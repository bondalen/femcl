#!/usr/bin/env python3
"""
Проверка доступных таблиц в MS SQL Server
"""
import pyodbc
import yaml
from rich.console import Console
from rich.table import Table

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

def check_available_tables():
    """Проверка доступных таблиц"""
    console.print("🔍 ПРОВЕРКА ДОСТУПНЫХ ТАБЛИЦ В MS SQL SERVER")
    console.print("="*60)
    
    conn = get_mssql_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем список всех таблиц
        cursor.execute("""
            SELECT 
                TABLE_SCHEMA,
                TABLE_NAME,
                TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """)
        
        tables = cursor.fetchall()
        console.print(f"📊 Найдено таблиц: {len(tables)}")
        
        # Группируем по схемам
        schemas = {}
        for table in tables:
            schema = table[0]
            if schema not in schemas:
                schemas[schema] = []
            schemas[schema].append(table[1])
        
        # Показываем таблицы по схемам
        for schema, table_list in schemas.items():
            console.print(f"\n📋 Схема: {schema} ({len(table_list)} таблиц)")
            for table in table_list[:10]:  # Показываем первые 10
                console.print(f"   - {table}")
            if len(table_list) > 10:
                console.print(f"   ... и ещё {len(table_list) - 10} таблиц")
        
        # Ищем таблицы, похожие на наши целевые
        target_tables = ['accnt', 'cn', 'cnInvCmmAgN']
        console.print(f"\n🎯 ПОИСК ЦЕЛЕВЫХ ТАБЛИЦ:")
        
        for target in target_tables:
            found = False
            for table in tables:
                if target.lower() in table[1].lower():
                    console.print(f"   ✅ Найдена похожая: {table[0]}.{table[1]}")
                    found = True
                    break
            if not found:
                console.print(f"   ❌ Не найдена: {target}")
        
        return tables
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка: {e}[/red]")
        return []
    finally:
        cursor.close()
        conn.close()

def analyze_specific_table(schema, table_name):
    """Анализ конкретной таблицы"""
    console.print(f"\n🔍 Анализ таблицы: {schema}.{table_name}")
    
    conn = get_mssql_connection()
    cursor = conn.cursor()
    
    try:
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
            WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table_name}'
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
        cursor.execute(f"SELECT COUNT(*) FROM [{schema}].[{table_name}]")
        count = cursor.fetchone()[0]
        console.print(f"   📊 Записей: {count}")
        
        if count > 0:
            # Показываем первые записи
            cursor.execute(f"SELECT TOP 3 * FROM [{schema}].[{table_name}]")
            rows = cursor.fetchall()
            console.print(f"   📝 Первые записи:")
            for i, row in enumerate(rows, 1):
                console.print(f"      {i}. {row}")
        
        return True
        
    except Exception as e:
        console.print(f"   ❌ Ошибка: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Основная функция"""
    # Проверяем доступные таблицы
    tables = check_available_tables()
    
    if tables:
        # Анализируем первые несколько таблиц
        console.print(f"\n🔍 АНАЛИЗ ПЕРВЫХ ТАБЛИЦ:")
        for i, table in enumerate(tables[:5]):
            analyze_specific_table(table[0], table[1])
            if i >= 4:  # Ограничиваем 5 таблицами
                break

if __name__ == "__main__":
    main()