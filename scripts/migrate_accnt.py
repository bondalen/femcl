#!/usr/bin/env python3
"""
Миграция таблицы accnt с использованием обновленных правил
"""
import os
import sys
import yaml
import pyodbc
import psycopg2
import pandas as pd
from rich.console import Console

# Загрузка конфигурации
def load_config(config_path="/home/alex/projects/sql/femcl/config/config.yaml"):
    """Загрузка конфигурации из файла"""
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

config = load_config()
console = Console()

# Функции проверки подключений
def check_mssql_connection():
    """Проверка подключения к MS SQL Server"""
    try:
        mssql_config = config['database']['mssql']
        
        connection_string = (
            f"DRIVER={{{mssql_config['driver']}}};"
            f"SERVER={mssql_config['server']},{mssql_config['port']};"
            f"DATABASE={mssql_config['database']};"
            f"UID={mssql_config['user']};"
            f"PWD={mssql_config['password']};"
            f"TrustServerCertificate={'yes' if mssql_config['trust_certificate'] else 'no'};"
            f"Connection Timeout={mssql_config['connection_timeout']};"
            f"Command Timeout={mssql_config['command_timeout']};"
        )
        
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Проверка доступности базы данных
        cursor.execute("SELECT DB_NAME() as current_database")
        result = cursor.fetchone()
        current_db = result[0]
        
        # Проверка схемы mcl
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables 
            WHERE table_schema = 'mcl'
        """)
        result = cursor.fetchone()
        mcl_tables_count = result[0]
        
        conn.close()
        
        console.print(f"✅ MS SQL Server: {mssql_config['server']}:{mssql_config['port']}")
        console.print(f"📊 База данных: {current_db}")
        console.print(f"📊 Таблиц в схеме mcl: {mcl_tables_count}")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Ошибка подключения к MS SQL Server: {e}")
        return False

def check_postgres_connection():
    """Проверка подключения к PostgreSQL"""
    try:
        postgres_config = config['database']['postgres']
        
        conn = psycopg2.connect(
            host=postgres_config['host'],
            port=postgres_config['port'],
            dbname=postgres_config['database'],
            user=postgres_config['user'],
            password=postgres_config['password'],
            connect_timeout=postgres_config['connection_timeout'],
            sslmode=postgres_config['ssl_mode']
        )
        
        cursor = conn.cursor()
        
        # Проверка доступности базы данных
        cursor.execute("SELECT current_database()")
        result = cursor.fetchone()
        current_db = result[0]
        
        # Проверка схемы mcl
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables 
            WHERE table_schema = 'mcl'
        """)
        result = cursor.fetchone()
        mcl_tables_count = result[0]
        
        # Проверка схемы ags
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables 
            WHERE table_schema = 'ags'
        """)
        result = cursor.fetchone()
        ags_tables_count = result[0]
        
        conn.close()
        
        console.print(f"✅ PostgreSQL: {postgres_config['host']}:{postgres_config['port']}")
        console.print(f"📊 База данных: {current_db}")
        console.print(f"📊 Таблиц в схеме mcl: {mcl_tables_count}")
        console.print(f"📊 Таблиц в схеме ags: {ags_tables_count}")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return False

def check_database_connections():
    """Комплексная проверка подключений к базам данных"""
    
    console.print("[bold blue]🔍 ПРОВЕРКА ПОДКЛЮЧЕНИЙ К БАЗАМ ДАННЫХ[/bold blue]")
    
    # Проверка MS SQL Server
    console.print("\n[blue]Проверка MS SQL Server...[/blue]")
    mssql_ok = check_mssql_connection()
    
    # Проверка PostgreSQL
    console.print("\n[blue]Проверка PostgreSQL...[/blue]")
    postgres_ok = check_postgres_connection()
    
    # Итоговая проверка
    if mssql_ok and postgres_ok:
        console.print("\n[green]✅ Все подключения к базам данных успешны![/green]")
        return True
    else:
        console.print("\n[red]❌ Ошибки в подключениях к базам данных![/red]")
        return False

def validate_migration_parameters_from_metadata(table_name):
    """Валидация параметров миграции из метаданных"""
    
    # Подключение к PostgreSQL для получения метаданных
    postgres_config = config['database']['postgres']
    conn = psycopg2.connect(
        host=postgres_config['host'],
        port=postgres_config['port'],
        dbname=postgres_config['database'],
        user=postgres_config['user'],
        password=postgres_config['password'],
        connect_timeout=postgres_config['connection_timeout'],
        sslmode=postgres_config['ssl_mode']
    )
    
    try:
        cursor = conn.cursor()
        
        # 1. Поиск исходной таблицы
        source_query = """
        SELECT id, object_name, schema_name, row_count, column_count
        FROM mcl.mssql_tables 
        WHERE object_name = %s
        """
        cursor.execute(source_query, (table_name,))
        source_table = cursor.fetchone()
        
        if not source_table:
            raise ValueError(f"Исходная таблица {table_name} не найдена в mssql_tables")
        
        source_table_id = source_table[0]
        
        # 2. Поиск целевой таблицы
        target_query = """
        SELECT id, object_name, schema_name, migration_status
        FROM mcl.postgres_tables 
        WHERE source_table_id = %s
        """
        cursor.execute(target_query, (source_table_id,))
        target_table = cursor.fetchone()
        
        if not target_table:
            raise ValueError(f"Целевая таблица для {table_name} не найдена в postgres_tables")
        
        # 3. Валидация параметров
        if source_table_id <= 0:
            raise ValueError("SOURCE_TABLE_ID должен быть положительным числом")
        
        if target_table[0] <= 0:
            raise ValueError("TARGET_TABLE_ID должен быть положительным числом")
        
        if not target_table[1]:
            raise ValueError("TARGET_TABLE_NAME не определен в метаданных")
        
        return {
            'source_table_id': source_table_id,
            'target_table_id': target_table[0],
            'source_table_name': table_name,
            'target_table_name': target_table[1],
            'source_schema': source_table[2],
            'target_schema': target_table[2],
            'migration_status': target_table[3]
        }
        
    finally:
        conn.close()

def migrate_single_table(table_name):
    """Управление миграцией отдельной таблицы с использованием метаданных"""
    
    console.print(f"[bold blue]🚀 МИГРАЦИЯ ТАБЛИЦЫ {table_name}[/bold blue]")
    
    try:
        # ЭТАП 0: Проверка подключений к базам данных
        console.print("[blue]Этап 0: Проверка подключений к базам данных[/blue]")
        if not check_database_connections():
            console.print("[red]❌ Критическая ошибка: Невозможно подключиться к базам данных![/red]")
            return False
        
        # ЭТАП 1: Определение параметров из метаданных
        console.print("[blue]Этап 1: Определение параметров миграции из метаданных[/blue]")
        params = validate_migration_parameters_from_metadata(table_name)
        
        console.print(f"📊 Исходная таблица: {params['source_table_name']} (ID: {params['source_table_id']})")
        console.print(f"📊 Целевая таблица: {params['target_table_name']} (ID: {params['target_table_id']})")
        console.print(f"📊 Схемы: {params['source_schema']} → {params['target_schema']}")
        console.print(f"📊 Статус миграции: {params['migration_status']}")
        
        # ЭТАП 2: Создание структуры таблицы
        console.print("[blue]Этап 2: Создание структуры таблицы[/blue]")
        
        # Получение структуры таблицы из метаданных
        postgres_config = config['database']['postgres']
        conn = psycopg2.connect(
            host=postgres_config['host'],
            port=postgres_config['port'],
            dbname=postgres_config['database'],
            user=postgres_config['user'],
            password=postgres_config['password'],
            connect_timeout=postgres_config['connection_timeout'],
            sslmode=postgres_config['ssl_mode']
        )
        
        cursor = conn.cursor()
        
        # Получение колонок таблицы
        columns_query = """
        SELECT 
            pc.column_name,
            pdt.typname_with_params as postgres_type,
            pc.is_nullable,
            pc.is_identity,
            pc.default_value
        FROM mcl.postgres_tables pt
        JOIN mcl.postgres_columns pc ON pt.id = pc.table_id
        JOIN mcl.postgres_derived_types pdt ON pc.postgres_data_type_id = pdt.id
        WHERE pt.id = %s
        ORDER BY pc.ordinal_position
        """
        cursor.execute(columns_query, (params['target_table_id'],))
        columns = cursor.fetchall()
        
        # Генерация DDL
        ddl_parts = []
        for col in columns:
            col_name, col_type, is_nullable, is_identity, default_value = col
            
            col_def = f"{col_name} {col_type}"
            
            if is_identity:
                col_def += " GENERATED ALWAYS AS IDENTITY"
            
            if not is_nullable and not is_identity:
                col_def += " NOT NULL"
            
            if default_value and not is_identity:
                col_def += f" DEFAULT {default_value}"
            
            ddl_parts.append(col_def)
        
        # Создание таблицы
        create_table_sql = f"""
        CREATE TABLE {params['target_schema']}.{params['target_table_name']} (
            {', '.join(ddl_parts)}
        )
        """
        
        console.print(f"📝 Создание таблицы: {params['target_schema']}.{params['target_table_name']}")
        cursor.execute(create_table_sql)
        conn.commit()
        
        # ЭТАП 3: Перенос данных
        console.print("[blue]Этап 3: Перенос данных[/blue]")
        
        # Подключение к MS SQL Server
        mssql_config = config['database']['mssql']
        mssql_conn = pyodbc.connect(
            f"DRIVER={{{mssql_config['driver']}}};"
            f"SERVER={mssql_config['server']},{mssql_config['port']};"
            f"DATABASE={mssql_config['database']};"
            f"UID={mssql_config['user']};"
            f"PWD={mssql_config['password']};"
            "TrustServerCertificate=yes;"
        )
        
        # Извлечение данных
        source_query = f"SELECT * FROM {params['source_schema']}.{params['source_table_name']}"
        df = pd.read_sql(source_query, mssql_conn)
        
        console.print(f"📊 Извлечено {len(df)} строк из {params['source_schema']}.{params['source_table_name']}")
        
        # Загрузка данных в PostgreSQL
        if len(df) > 0:
            # Подготовка данных для вставки
            columns_list = list(df.columns)
            placeholders = ', '.join(['%s'] * len(columns_list))
            columns_str = ', '.join(columns_list)
            
            # Вставка данных с OVERRIDING SYSTEM VALUE для identity колонок
            insert_sql = f"""
            INSERT INTO {params['target_schema']}.{params['target_table_name']} ({columns_str}) 
            OVERRIDING SYSTEM VALUE 
            VALUES ({placeholders})
            """
            
            # Выполнение вставки
            cursor.executemany(insert_sql, df.values.tolist())
            conn.commit()
            
            console.print(f"✅ Загружено {len(df)} строк в {params['target_schema']}.{params['target_table_name']}")
        else:
            console.print("⚠️ Таблица пуста, создана только структура")
        
        # ЭТАП 4: Проверка результатов
        console.print("[blue]Этап 4: Проверка результатов[/blue]")
        
        # Проверка количества строк
        cursor.execute(f"SELECT COUNT(*) FROM {params['target_schema']}.{params['target_table_name']}")
        result = cursor.fetchone()
        target_count = result[0]
        
        console.print(f"📊 Строк в целевой таблице: {target_count}")
        
        if target_count == len(df):
            console.print(f"[green]✅ Миграция таблицы {table_name} завершена успешно![/green]")
            return True
        else:
            console.print(f"[red]❌ Ошибка: количество строк не совпадает![/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Критическая ошибка при миграции:[/red] {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
        if 'mssql_conn' in locals():
            mssql_conn.close()

if __name__ == "__main__":
    # Параметры миграции - только имя таблицы
    TABLE_NAME = "accnt"  # Имя таблицы для миграции
    
    success = migrate_single_table(TABLE_NAME)
    sys.exit(0 if success else 1)








