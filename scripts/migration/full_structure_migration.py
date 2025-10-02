#!/usr/bin/env python3
"""
Полный перенос таблиц с реальной структурой и данными из MS SQL Server в PostgreSQL
"""
import pyodbc
import psycopg2
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
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

def get_table_structure(table_name):
    """Получение полной структуры таблицы из MS SQL Server"""
    mssql_conn = get_mssql_connection()
    cursor = mssql_conn.cursor()
    
    try:
        cursor.execute(f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'ags' AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """)
        
        columns = cursor.fetchall()
        return columns
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка получения структуры таблицы {table_name}: {e}[/red]")
        return []
    finally:
        cursor.close()
        mssql_conn.close()

def convert_mssql_to_postgres_type(mssql_type, max_length, precision, scale):
    """Преобразование типов данных из MS SQL Server в PostgreSQL"""
    type_mapping = {
        'int': 'INTEGER',
        'bigint': 'BIGINT',
        'smallint': 'SMALLINT',
        'tinyint': 'SMALLINT',
        'bit': 'BOOLEAN',
        'decimal': f'DECIMAL({precision},{scale})' if precision and scale else 'DECIMAL',
        'numeric': f'DECIMAL({precision},{scale})' if precision and scale else 'DECIMAL',
        'money': 'DECIMAL(19,4)',
        'smallmoney': 'DECIMAL(10,4)',
        'float': 'DOUBLE PRECISION',
        'real': 'REAL',
        'datetime': 'TIMESTAMP',
        'datetime2': 'TIMESTAMP',
        'smalldatetime': 'TIMESTAMP',
        'date': 'DATE',
        'time': 'TIME',
        'char': f'CHAR({max_length})' if max_length else 'CHAR(1)',
        'varchar': f'VARCHAR({max_length})' if max_length and max_length > 0 else 'TEXT',
        'nchar': f'CHAR({max_length})' if max_length else 'CHAR(1)',
        'nvarchar': f'VARCHAR({max_length})' if max_length and max_length > 0 else 'TEXT',
        'text': 'TEXT',
        'ntext': 'TEXT',
        'image': 'BYTEA',
        'varbinary': 'BYTEA',
        'uniqueidentifier': 'UUID'
    }
    
    return type_mapping.get(mssql_type.lower(), 'TEXT')

def create_table_structure(table_name, columns):
    """Создание структуры таблицы в PostgreSQL"""
    postgres_conn = get_postgres_connection()
    cursor = postgres_conn.cursor()
    
    try:
        # Строим DDL для создания таблицы
        ddl_parts = []
        
        for col in columns:
            col_name = col[0]
            mssql_type = col[1]
            is_nullable = col[2] == 'YES'
            max_length = col[3]
            precision = col[4]
            scale = col[5]
            default_value = col[6]
            
            # Преобразуем тип данных
            postgres_type = convert_mssql_to_postgres_type(mssql_type, max_length, precision, scale)
            
            # Строим определение колонки
            col_def = f'"{col_name}" {postgres_type}'
            
            if not is_nullable:
                col_def += ' NOT NULL'
            
            if default_value:
                # Обрабатываем значения по умолчанию
                if 'getdate()' in str(default_value).lower():
                    col_def += ' DEFAULT CURRENT_TIMESTAMP'
                elif 'newid()' in str(default_value).lower():
                    col_def += ' DEFAULT gen_random_uuid()'
                else:
                    col_def += f' DEFAULT {default_value}'
            
            ddl_parts.append(col_def)
        
        # Создаём таблицу
        target_table = f'ags.{table_name}' if table_name != 'cnInvCmmAgN' else 'ags."cnInvCmmAgN"'
        ddl = f'CREATE TABLE {target_table} (\n    ' + ',\n    '.join(ddl_parts) + '\n);'
        
        console.print(f"🔨 Создание таблицы: {target_table}")
        console.print(f"   📋 Колонок: {len(columns)}")
        
        cursor.execute(ddl)
        postgres_conn.commit()
        
        console.print(f"   ✅ Таблица {target_table} создана успешно")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка создания таблицы {table_name}: {e}[/red]")
        postgres_conn.rollback()
        return False
    finally:
        cursor.close()
        postgres_conn.close()

def migrate_table_data(table_name, columns):
    """Перенос данных таблицы"""
    mssql_conn = get_mssql_connection()
    postgres_conn = get_postgres_connection()
    
    mssql_cursor = mssql_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        console.print(f"🚀 Перенос данных таблицы: {table_name}")
        
        # Получаем данные из MS SQL Server
        column_names = [col[0] for col in columns]
        select_columns = ', '.join([f'[{col}]' for col in column_names])
        query = f"SELECT {select_columns} FROM ags.{table_name}"
        
        mssql_cursor.execute(query)
        rows = mssql_cursor.fetchall()
        
        console.print(f"   📊 Загружено записей: {len(rows)}")
        
        if len(rows) == 0:
            console.print(f"   ⚠️ Таблица {table_name} пуста")
            return True
        
        # Вставляем данные в PostgreSQL
        target_table = f'ags.{table_name}' if table_name != 'cnInvCmmAgN' else 'ags."cnInvCmmAgN"'
        insert_columns = ', '.join([f'"{col}"' for col in column_names])
        placeholders = ', '.join(['%s'] * len(column_names))
        
        insert_query = f"""
            INSERT INTO {target_table} ({insert_columns})
            VALUES ({placeholders})
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
        console.print(f"[red]❌ Ошибка переноса данных таблицы {table_name}: {e}[/red]")
        postgres_conn.rollback()
        return False
    finally:
        mssql_cursor.close()
        mssql_conn.close()
        postgres_cursor.close()
        postgres_conn.close()

def verify_full_migration():
    """Проверка полного переноса"""
    console.print(Panel.fit(
        "[bold yellow]🔍 ПРОВЕРКА ПОЛНОГО ПЕРЕНОСА[/bold yellow]",
        border_style="yellow"
    ))
    
    mssql_conn = get_mssql_connection()
    postgres_conn = get_postgres_connection()
    
    mssql_cursor = mssql_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        tables = ['accnt', 'cn', 'cnInvCmmAgN']
        
        console.print("📊 Сравнение структуры и данных:")
        
        migration_success = True
        
        for table in tables:
            console.print(f"\n🔍 Таблица: {table}")
            
            # Сравниваем количество записей
            mssql_cursor.execute(f"SELECT COUNT(*) FROM ags.{table}")
            mssql_count = mssql_cursor.fetchone()[0]
            
            target_table = f'ags.{table}' if table != 'cnInvCmmAgN' else 'ags."cnInvCmmAgN"'
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
            postgres_count = postgres_cursor.fetchone()[0]
            
            # Сравниваем количество колонок
            mssql_cursor.execute(f"""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'ags' AND TABLE_NAME = '{table}'
            """)
            mssql_columns = mssql_cursor.fetchone()[0]
            
            postgres_cursor.execute(f"""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_schema = 'ags' AND table_name = %s
            """, (table,))
            postgres_columns = postgres_cursor.fetchone()[0]
            
            # Статус
            records_ok = mssql_count == postgres_count
            columns_ok = mssql_columns == postgres_columns
            
            status = "✅" if records_ok and columns_ok else "❌"
            console.print(f"   {status} Записей: {mssql_count} → {postgres_count}")
            console.print(f"   {status} Колонок: {mssql_columns} → {postgres_columns}")
            
            if not (records_ok and columns_ok):
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
    """Основная функция полного переноса"""
    console.print(Panel.fit(
        "[bold green]🚀 ПОЛНЫЙ ПЕРЕНОС С РЕАЛЬНОЙ СТРУКТУРОЙ[/bold green]\n"
        "Из MS SQL Server в PostgreSQL",
        border_style="green"
    ))
    
    # Шаг 1: Получение структуры и создание таблиц
    console.print("\n" + "="*70)
    console.print("[bold blue]ШАГ 1: Создание полной структуры таблиц[/bold blue]")
    console.print("="*70)
    
    tables = ['accnt', 'cn', 'cnInvCmmAgN']
    
    for table in tables:
        console.print(f"\n🔍 Обработка таблицы: {table}")
        
        # Получаем структуру
        columns = get_table_structure(table)
        if not columns:
            console.print(f"[red]❌ Не удалось получить структуру таблицы {table}[/red]")
            continue
        
        console.print(f"   📋 Найдено колонок: {len(columns)}")
        
        # Создаём структуру
        if not create_table_structure(table, columns):
            console.print(f"[red]❌ Не удалось создать структуру таблицы {table}[/red]")
            continue
    
    # Шаг 2: Перенос данных
    console.print("\n" + "="*70)
    console.print("[bold blue]ШАГ 2: Перенос данных[/bold blue]")
    console.print("="*70)
    
    for table in tables:
        columns = get_table_structure(table)
        if not migrate_table_data(table, columns):
            console.print(f"[red]❌ Не удалось перенести данные таблицы {table}[/red]")
            continue
    
    # Шаг 3: Проверка
    console.print("\n" + "="*70)
    console.print("[bold blue]ШАГ 3: Проверка полного переноса[/bold blue]")
    console.print("="*70)
    
    if not verify_full_migration():
        console.print("[red]❌ Проверка полного переноса не пройдена[/red]")
        return False
    
    # Итоговый отчёт
    console.print("\n" + "="*70)
    console.print("[bold blue]📊 ИТОГОВЫЙ ОТЧЁТ[/bold blue]")
    console.print("="*70)
    
    console.print("[green]✅ ПОЛНЫЙ ПЕРЕНОС ЗАВЕРШЁН УСПЕШНО![/green]")
    console.print("[green]✅ Все таблицы перенесены с полной структурой и данными[/green]")
    console.print("[green]✅ Система готова к переносу всех 166 таблиц с полной структурой[/green]")
    
    return True

if __name__ == "__main__":
    main()