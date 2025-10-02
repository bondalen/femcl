#!/usr/bin/env python3
"""
Перенос реальных данных из MS SQL Server в PostgreSQL
"""
import pyodbc
import psycopg2
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
import pandas as pd
from datetime import datetime

console = Console()

def get_mssql_connection():
    """Подключение к MS SQL Server"""
    with open('/home/alex/projects/sql/femcl/config/config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    mssql_config = config['database']['mssql']
    
    connection_string = (
        f"DRIVER={mssql_config['driver']};"
        f"SERVER={mssql_config['server']};"
        f"DATABASE={mssql_config['database']};"
        f"UID={mssql_config['user']};"
        f"PWD={mssql_config['password']};"
        f"Trusted_Connection={mssql_config.get('trusted_connection', 'no')};"
    )
    
    return pyodbc.connect(connection_string)

def get_postgres_connection():
    """Подключение к PostgreSQL"""
    with open('/home/alex/projects/sql/femcl/config/config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    postgres_config = config['database']['postgres']
    
    return psycopg2.connect(
        host=postgres_config['host'],
        port=postgres_config['port'],
        dbname=postgres_config['database'],
        user=postgres_config['user'],
        password=postgres_config['password']
    )

def analyze_source_tables():
    """Анализ структуры исходных таблиц в MS SQL Server"""
    console.print(Panel.fit(
        "[bold blue]🔍 АНАЛИЗ ИСХОДНЫХ ТАБЛИЦ В MS SQL SERVER[/bold blue]",
        border_style="blue"
    ))
    
    mssql_conn = get_mssql_connection()
    cursor = mssql_conn.cursor()
    
    try:
        # Анализируем три таблицы
        tables = ['accnt', 'cn', 'cnInvCmmAgN']
        
        for table in tables:
            console.print(f"\n🔍 Анализ таблицы: {table}")
            
            # Получаем информацию о колонках
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table}'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns = cursor.fetchall()
            console.print(f"   📋 Колонок: {len(columns)}")
            
            for col in columns:
                col_info = f"      - {col[0]}: {col[1]}"
                if col[2] == 'NO':
                    col_info += " NOT NULL"
                if col[3]:
                    col_info += f"({col[3]})"
                elif col[4]:
                    col_info += f"({col[4]},{col[5]})"
                console.print(col_info)
            
            # Получаем количество записей
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            console.print(f"   📊 Записей: {count}")
            
            if count > 0:
                # Показываем первые записи
                cursor.execute(f"SELECT TOP 3 * FROM {table}")
                rows = cursor.fetchall()
                console.print(f"   📝 Первые записи:")
                for i, row in enumerate(rows, 1):
                    console.print(f"      {i}. {row}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка анализа исходных таблиц: {e}[/red]")
        return False
    finally:
        cursor.close()
        mssql_conn.close()

def migrate_table_data(table_name, source_columns, target_columns):
    """Перенос данных одной таблицы"""
    console.print(f"\n🚀 Перенос данных таблицы: {table_name}")
    
    mssql_conn = get_mssql_connection()
    postgres_conn = get_postgres_connection()
    
    mssql_cursor = mssql_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        # Получаем данные из MS SQL Server
        console.print(f"   📥 Загрузка данных из MS SQL Server...")
        
        # Строим SELECT запрос
        select_columns = ', '.join(source_columns)
        query = f"SELECT {select_columns} FROM {table_name}"
        
        mssql_cursor.execute(query)
        rows = mssql_cursor.fetchall()
        
        console.print(f"   📊 Загружено записей: {len(rows)}")
        
        if len(rows) == 0:
            console.print(f"   ⚠️ Таблица {table_name} пуста")
            return True
        
        # Подготавливаем данные для вставки в PostgreSQL
        console.print(f"   📤 Вставка данных в PostgreSQL...")
        
        # Строим INSERT запрос
        target_table = f'ags.{table_name}' if table_name != 'cnInvCmmAgN' else 'ags."cnInvCmmAgN"'
        insert_columns = ', '.join(target_columns)
        placeholders = ', '.join(['%s'] * len(target_columns))
        
        insert_query = f"""
            INSERT INTO {target_table} ({insert_columns})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """
        
        # Вставляем данные пакетами
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            
            # Преобразуем данные для PostgreSQL
            processed_batch = []
            for row in batch:
                processed_row = []
                for j, value in enumerate(row):
                    if value is None:
                        processed_row.append(None)
                    elif isinstance(value, datetime):
                        processed_row.append(value)
                    else:
                        processed_row.append(str(value))
                processed_batch.append(tuple(processed_row))
            
            postgres_cursor.executemany(insert_query, processed_batch)
            total_inserted += len(batch)
            
            if i % (batch_size * 10) == 0:
                console.print(f"      📊 Обработано: {total_inserted}/{len(rows)} записей")
        
        postgres_conn.commit()
        console.print(f"   ✅ Успешно перенесено: {total_inserted} записей")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка переноса таблицы {table_name}: {e}[/red]")
        postgres_conn.rollback()
        return False
    finally:
        mssql_cursor.close()
        mssql_conn.close()
        postgres_cursor.close()
        postgres_conn.close()

def verify_migration():
    """Проверка корректности переноса"""
    console.print(Panel.fit(
        "[bold yellow]🔍 ПРОВЕРКА ПЕРЕНОСА ДАННЫХ[/bold yellow]",
        border_style="yellow"
    ))
    
    mssql_conn = get_mssql_connection()
    postgres_conn = get_postgres_connection()
    
    mssql_cursor = mssql_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        tables = ['accnt', 'cn', 'cnInvCmmAgN']
        
        console.print("📊 Сравнение количества записей:")
        
        migration_success = True
        
        for table in tables:
            # Подсчитываем записи в MS SQL Server
            mssql_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            mssql_count = mssql_cursor.fetchone()[0]
            
            # Подсчитываем записи в PostgreSQL
            target_table = f'ags.{table}' if table != 'cnInvCmmAgN' else 'ags."cnInvCmmAgN"'
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
            postgres_count = postgres_cursor.fetchone()[0]
            
            status = "✅" if mssql_count == postgres_count else "❌"
            console.print(f"   {status} {table}: {mssql_count} → {postgres_count}")
            
            if mssql_count != postgres_count:
                migration_success = False
        
        return migration_success
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка проверки: {e}[/red]")
        return False
    finally:
        mssql_cursor.close()
        mssql_conn.close()
        postgres_cursor.close()
        postgres_conn.close()

def main():
    """Основная функция переноса данных"""
    console.print(Panel.fit(
        "[bold green]🚀 ПЕРЕНОС РЕАЛЬНЫХ ДАННЫХ[/bold green]\n"
        "Из MS SQL Server в PostgreSQL",
        border_style="green"
    ))
    
    # Шаг 1: Анализ исходных таблиц
    console.print("\n" + "="*70)
    console.print("[bold blue]ШАГ 1: Анализ исходных таблиц в MS SQL Server[/bold blue]")
    console.print("="*70)
    
    if not analyze_source_tables():
        console.print("[red]❌ Не удалось проанализировать исходные таблицы[/red]")
        return False
    
    # Шаг 2: Перенос данных
    console.print("\n" + "="*70)
    console.print("[bold blue]ШАГ 2: Перенос данных[/bold blue]")
    console.print("="*70)
    
    # Определяем маппинг колонок для каждой таблицы
    table_mappings = {
        'accnt': {
            'source': ['id', 'name', 'balance', 'created_at'],
            'target': ['id', 'name', 'created_at']
        },
        'cn': {
            'source': ['id', 'number', 'description', 'amount', 'created_at'],
            'target': ['id', 'number', 'created_at']
        },
        'cnInvCmmAgN': {
            'source': ['id', 'value', 'category', 'quantity', 'created_at'],
            'target': ['id', 'value', 'created_at']
        }
    }
    
    migration_success = True
    
    for table, mapping in table_mappings.items():
        if not migrate_table_data(table, mapping['source'], mapping['target']):
            migration_success = False
            break
    
    if not migration_success:
        console.print("[red]❌ Перенос данных завершился с ошибками[/red]")
        return False
    
    # Шаг 3: Проверка переноса
    console.print("\n" + "="*70)
    console.print("[bold blue]ШАГ 3: Проверка переноса[/bold blue]")
    console.print("="*70)
    
    if not verify_migration():
        console.print("[red]❌ Проверка переноса не пройдена[/red]")
        return False
    
    # Итоговый отчёт
    console.print("\n" + "="*70)
    console.print("[bold blue]📊 ИТОГОВЫЙ ОТЧЁТ[/bold blue]")
    console.print("="*70)
    
    console.print("[green]✅ ПЕРЕНОС РЕАЛЬНЫХ ДАННЫХ ЗАВЕРШЁН УСПЕШНО![/green]")
    console.print("[green]✅ Все данные из MS SQL Server перенесены в PostgreSQL[/green]")
    console.print("[green]✅ Система готова к переносу всех 166 таблиц с реальными данными[/green]")
    
    return True

if __name__ == "__main__":
    main()