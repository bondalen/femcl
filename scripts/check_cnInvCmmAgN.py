#!/usr/bin/env python3
"""
Проверка и миграция таблицы cnInvCmmAgN
"""
import os
import sys
import pandas as pd
import pyodbc
import psycopg2
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()

def check_table_exists():
    """Проверка существования таблицы в обеих БД"""
    console.print("[blue]🔍 Проверка существования таблицы cnInvCmmAgN[/blue]")
    
    # PostgreSQL
    pg_conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        dbname=os.getenv('POSTGRES_DB', 'fish_eye'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres')
    )
    
    # MS SQL Server
    mssql_conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('MSSQL_SERVER', 'localhost')},{os.getenv('MSSQL_PORT', '1433')};"
        f"DATABASE={os.getenv('MSSQL_DB', 'FishEye')};"
        f"UID={os.getenv('MSSQL_USER', 'sa')};"
        f"PWD={os.getenv('MSSQL_PASSWORD', 'kolob_OK1')};"
        "TrustServerCertificate=yes;"
    )
    
    pg_cursor = pg_conn.cursor()
    mssql_cursor = mssql_conn.cursor()
    
    try:
        # Проверяем в MS SQL Server
        mssql_cursor.execute("SELECT COUNT(*) FROM ags.cnInvCmmAgN")
        mssql_count = mssql_cursor.fetchone()[0]
        console.print(f"📊 Строк в MS SQL Server: {mssql_count}")
        
        # Проверяем в PostgreSQL
        pg_cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'ags' AND table_name = 'cnInvCmmAgN')")
        table_exists = pg_cursor.fetchone()[0]
        
        if table_exists:
            pg_cursor.execute("SELECT COUNT(*) FROM ags.cnInvCmmAgN")
            pg_count = pg_cursor.fetchone()[0]
            console.print(f"📊 Строк в PostgreSQL: {pg_count}")
            
            if pg_count == mssql_count:
                console.print("[green]✅ Количество строк совпадает![/green]")
                return True
            else:
                console.print(f"[red]❌ Несоответствие: {pg_count} != {mssql_count}[/red]")
                return False
        else:
            console.print("[yellow]⚠️ Таблица не существует в PostgreSQL[/yellow]")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Ошибка проверки: {e}[/red]")
        return False
    
    finally:
        pg_conn.close()
        mssql_conn.close()

def migrate_table_data():
    """Перенос данных таблицы cnInvCmmAgN"""
    console.print("[blue]🚀 Начало переноса данных таблицы cnInvCmmAgN[/blue]")
    
    # Подключение к MS SQL Server
    mssql_conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('MSSQL_SERVER', 'localhost')},{os.getenv('MSSQL_PORT', '1433')};"
        f"DATABASE={os.getenv('MSSQL_DB', 'FishEye')};"
        f"UID={os.getenv('MSSQL_USER', 'sa')};"
        f"PWD={os.getenv('MSSQL_PASSWORD', 'kolob_OK1')};"
        "TrustServerCertificate=yes;"
    )
    
    # Подключение к PostgreSQL
    pg_conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        dbname=os.getenv('POSTGRES_DB', 'fish_eye'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres')
    )
    
    try:
        # 1. Извлечение данных из MS SQL Server
        console.print("[blue]📥 Извлечение данных из MS SQL Server[/blue]")
        query = "SELECT * FROM ags.cnInvCmmAgN ORDER BY cicanKey"
        df = pd.read_sql(query, mssql_conn)
        console.print(f"Извлечено {len(df)} строк из MS SQL Server")
        
        if len(df) == 0:
            console.print("[yellow]⚠️ Таблица пуста в MS SQL Server[/yellow]")
            return True
        
        # 2. Очистка целевой таблицы
        console.print("[blue]🧹 Очистка целевой таблицы[/blue]")
        with pg_conn.cursor() as cur:
            cur.execute("DELETE FROM ags.cnInvCmmAgN")
            pg_conn.commit()
        
        # 3. Загрузка данных в PostgreSQL
        console.print("[blue]📤 Загрузка данных в PostgreSQL[/blue]")
        with pg_conn.cursor() as cur:
            for index, row in df.iterrows():
                values = []
                for col in df.columns:
                    value = row[col]
                    if pd.isna(value):
                        values.append(None)
                    else:
                        values.append(value)
                
                columns = ', '.join(df.columns)
                placeholders = ', '.join(['%s'] * len(df.columns))
                sql = f"INSERT INTO ags.cnInvCmmAgN ({columns}) OVERRIDING SYSTEM VALUE VALUES ({placeholders})"
                cur.execute(sql, values)
            
            pg_conn.commit()
        
        # 4. Проверка результатов
        console.print("[blue]✅ Проверка результатов переноса[/blue]")
        with pg_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM ags.cnInvCmmAgN")
            row_count = cur.fetchone()[0]
            console.print(f"Загружено {row_count} строк в PostgreSQL")
            
            if row_count == len(df):
                console.print("[green]🎉 Перенос данных завершен успешно![/green]")
                return True
            else:
                console.print(f"[red]❌ Ошибка переноса: {row_count} != {len(df)}[/red]")
                return False
                
    except Exception as e:
        console.print(f"[red]❌ Ошибка переноса: {e}[/red]")
        return False
    
    finally:
        mssql_conn.close()
        pg_conn.close()

def main():
    """Основная функция"""
    console.print("[bold blue]🔍 ПРОВЕРКА И МИГРАЦИЯ ТАБЛИЦЫ cnInvCmmAgN[/bold blue]")
    
    # Проверяем существование таблицы
    if check_table_exists():
        console.print("[green]✅ Таблица уже существует и данные совпадают[/green]")
        return True
    
    # Если таблица не существует или данные не совпадают, выполняем миграцию
    console.print("[blue]🚀 Начинаем миграцию данных[/blue]")
    success = migrate_table_data()
    
    if success:
        console.print("[green]🎉 Миграция таблицы cnInvCmmAgN завершена успешно![/green]")
    else:
        console.print("[red]❌ Ошибка миграции таблицы cnInvCmmAgN[/red]")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)









