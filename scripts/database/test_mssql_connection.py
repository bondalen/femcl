#!/usr/bin/env python3
"""
FEMCL - Тестирование подключения к MS SQL Server
Проверяет доступ к исходной базе данных и таблице accnt
"""

import os
import sys
import pyodbc
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Загрузка переменных окружения
load_dotenv()

console = Console()

def test_mssql_connection():
    """Тестирование подключения к MS SQL Server"""
    try:
        # Параметры подключения к MS SQL Server
        # Эти параметры должны быть настроены в .env файле
        server = os.getenv('MSSQL_SERVER', 'localhost')
        database = os.getenv('MSSQL_DB', 'FishEye')
        username = os.getenv('MSSQL_USER', 'sa')
        password = os.getenv('MSSQL_PASSWORD', '')
        driver = os.getenv('MSSQL_DRIVER', '{ODBC Driver 17 for SQL Server}')
        
        console.print(f"[blue]Подключение к MS SQL Server...[/blue]")
        console.print(f"Server: {server}")
        console.print(f"Database: {database}")
        console.print(f"Username: {username}")
        console.print(f"Driver: {driver}")
        
        # Строка подключения
        connection_string = f"""
            DRIVER={driver};
            SERVER={server};
            DATABASE={database};
            UID={username};
            PWD={password};
            TrustServerCertificate=yes;
        """
        
        # Подключение к MS SQL Server
        conn = pyodbc.connect(connection_string)
        
        console.print("[green]✅ Подключение к MS SQL Server успешно![/green]")
        
        # Проверка версии SQL Server
        with conn.cursor() as cur:
            cur.execute("SELECT @@VERSION")
            version = cur.fetchone()[0]
            console.print(f"[blue]SQL Server версия:[/blue] {version[:100]}...")
        
        # Проверка схем
        with conn.cursor() as cur:
            cur.execute("""
                SELECT SCHEMA_NAME 
                FROM INFORMATION_SCHEMA.SCHEMATA 
                ORDER BY SCHEMA_NAME
            """)
            schemas = cur.fetchall()
            
            table = Table(title="Доступные схемы в MS SQL")
            table.add_column("Схема", style="cyan")
            
            for schema in schemas:
                table.add_row(schema[0])
            
            console.print(table)
        
        # Проверка таблицы accnt
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    TABLE_NAME,
                    TABLE_SCHEMA,
                    TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'accnt'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)
            tables = cur.fetchall()
            
            if tables:
                console.print("[green]✅ Таблица accnt найдена в MS SQL Server![/green]")
                
                table = Table(title="Таблица accnt в MS SQL")
                table.add_column("Схема", style="green")
                table.add_column("Таблица", style="green")
                table.add_column("Тип", style="green")
                
                for schema, table_name, table_type in tables:
                    table.add_row(schema, table_name, table_type)
                
                console.print(table)
            else:
                console.print("[red]❌ Таблица accnt не найдена в MS SQL Server![/red]")
                return False
        
        # Проверка структуры таблицы accnt
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'accnt'
                ORDER BY ORDINAL_POSITION
            """)
            columns = cur.fetchall()
            
            console.print("[blue]Структура таблицы accnt в MS SQL:[/blue]")
            
            table = Table(title="Колонки таблицы accnt")
            table.add_column("Колонка", style="cyan")
            table.add_column("Тип", style="yellow")
            table.add_column("Длина", style="blue")
            table.add_column("Nullable", style="green")
            
            for col in columns:
                length = col[2] if col[2] else f"{col[3]},{col[4]}" if col[3] else "N/A"
                table.add_row(col[0], col[1], str(length), col[5])
            
            console.print(table)
        
        # Проверка данных в таблице accnt
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM accnt")
            row_count = cur.fetchone()[0]
            console.print(f"[blue]Количество строк в таблице accnt:[/blue] {row_count}")
            
            if row_count > 0:
                cur.execute("SELECT TOP 5 * FROM accnt ORDER BY account_key")
                sample_data = cur.fetchall()
                
                console.print("[blue]Пример данных из таблицы accnt:[/blue]")
                
                table = Table(title="Пример данных")
                table.add_column("account_key", style="cyan")
                table.add_column("account_num", style="yellow")
                table.add_column("account_name", style="green")
                
                for row in sample_data:
                    table.add_row(str(row[0]), str(row[1]), str(row[2]))
                
                console.print(table)
        
        conn.close()
        console.print("[green]✅ Все проверки MS SQL Server пройдены успешно![/green]")
        return True
        
    except pyodbc.Error as e:
        console.print(f"[red]❌ Ошибка подключения к MS SQL Server:[/red] {e}")
        return False
    except Exception as e:
        console.print(f"[red]❌ Неожиданная ошибка:[/red] {e}")
        return False

if __name__ == "__main__":
    success = test_mssql_connection()
    sys.exit(0 if success else 1)