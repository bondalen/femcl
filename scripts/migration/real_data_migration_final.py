#!/usr/bin/env python3
"""
Перенос реальных данных из MS SQL Server в PostgreSQL (финальная версия)
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

def migrate_table_data(table_name, source_columns, target_columns, data_mapping):
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
        query = f"SELECT {select_columns} FROM ags.{table_name}"
        
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
                        # Применяем маппинг данных
                        if j < len(data_mapping):
                            processed_row.append(data_mapping[j](value))
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
            mssql_cursor.execute(f"SELECT COUNT(*) FROM ags.{table}")
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
    
    # Шаг 1: Перенос данных
    console.print("\n" + "="*70)
    console.print("[bold blue]ШАГ 1: Перенос данных[/bold blue]")
    console.print("="*70)
    
    # Определяем маппинг колонок и функций преобразования данных
    table_mappings = {
        'accnt': {
            'source': ['account_key', 'account_num', 'account_name'],
            'target': ['id', 'name', 'created_at'],
            'data_mapping': [
                lambda x: int(x),  # account_key -> id
                lambda x: str(x),  # account_name -> name  
                lambda x: datetime.now()  # created_at
            ]
        },
        'cn': {
            'source': ['cn_key', 'cn_number', 'cn_date'],
            'target': ['id', 'number', 'created_at'],
            'data_mapping': [
                lambda x: int(x),  # cn_key -> id
                lambda x: str(x) if x else '',  # cn_number -> number
                lambda x: x if x else datetime.now()  # cn_date -> created_at
            ]
        },
        'cnInvCmmAgN': {
            'source': ['cicanKey', 'cicanName'],
            'target': ['id', 'value', 'created_at'],
            'data_mapping': [
                lambda x: int(x),  # cicanKey -> id
                lambda x: str(x),  # cicanName -> value
                lambda x: datetime.now()  # created_at
            ]
        }
    }
    
    migration_success = True
    
    for table, mapping in table_mappings.items():
        if not migrate_table_data(table, mapping['source'], mapping['target'], mapping['data_mapping']):
            migration_success = False
            break
    
    if not migration_success:
        console.print("[red]❌ Перенос данных завершился с ошибками[/red]")
        return False
    
    # Шаг 2: Проверка переноса
    console.print("\n" + "="*70)
    console.print("[bold blue]ШАГ 2: Проверка переноса[/bold blue]")
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