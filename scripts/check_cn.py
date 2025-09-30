#!/usr/bin/env python3
"""
Проверка результатов миграции таблицы cn
"""
import psycopg2
import pyodbc
from rich.console import Console

console = Console()

def check_migration():
    """Проверка результатов миграции"""
    console.print("[blue]🔍 Проверка результатов миграции таблицы cn[/blue]")
    
    # PostgreSQL
    pg_conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="fish_eye",
        user="postgres",
        password="postgres"
    )
    
    # MS SQL Server
    mssql_conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=FishEye;"
        "UID=sa;"
        "PWD=kolob_OK1;"
        "TrustServerCertificate=yes;"
    )
    
    pg_cursor = pg_conn.cursor()
    mssql_cursor = mssql_conn.cursor()
    
    try:
        # Проверяем количество строк в MS SQL Server
        mssql_cursor.execute("SELECT COUNT(*) FROM ags.cn")
        mssql_count = mssql_cursor.fetchone()[0]
        console.print(f"📊 Строк в MS SQL Server: {mssql_count}")
        
        # Проверяем количество строк в PostgreSQL
        pg_cursor.execute("SELECT COUNT(*) FROM ags.cn")
        pg_count = pg_cursor.fetchone()[0]
        console.print(f"📊 Строк в PostgreSQL: {pg_count}")
        
        if pg_count == mssql_count:
            console.print("[green]✅ Количество строк совпадает![/green]")
        else:
            console.print(f"[red]❌ Несоответствие: {pg_count} != {mssql_count}[/red]")
        
        # Проверяем структуру таблицы
        console.print("[blue]📋 Структура таблицы в PostgreSQL:[/blue]")
        pg_cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_schema = 'ags' AND table_name = 'cn'
        ORDER BY ordinal_position
        """)
        
        columns = pg_cursor.fetchall()
        for col in columns:
            console.print(f"  {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        # Показываем первые несколько строк
        console.print("[blue]📋 Первые 5 строк данных:[/blue]")
        pg_cursor.execute("SELECT * FROM ags.cn ORDER BY cn_key LIMIT 5")
        rows = pg_cursor.fetchall()
        
        for i, row in enumerate(rows, 1):
            console.print(f"  {i}. {row}")
        
        if pg_count > 0:
            console.print("[green]🎉 Миграция таблицы cn завершена успешно![/green]")
        else:
            console.print("[red]❌ Таблица cn пуста в PostgreSQL[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Ошибка проверки: {e}[/red]")
    
    finally:
        pg_conn.close()
        mssql_conn.close()

if __name__ == "__main__":
    check_migration()