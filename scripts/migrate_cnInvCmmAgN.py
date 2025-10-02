#!/usr/bin/env python3
"""
Миграция данных таблицы cnInvCmmAgN из MS SQL Server в PostgreSQL
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

def migrate_cnInvCmmAgN():
    """Перенос данных таблицы cnInvCmmAgN"""
    console.print("[bold blue]🚀 МИГРАЦИЯ ТАБЛИЦЫ cnInvCmmAgN[/bold blue]")
    
    # Подключение к MS SQL Server
    console.print("[blue]📥 Подключение к MS SQL Server[/blue]")
    mssql_conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('MSSQL_SERVER', 'localhost')},{os.getenv('MSSQL_PORT', '1433')};"
        f"DATABASE={os.getenv('MSSQL_DB', 'FishEye')};"
        f"UID={os.getenv('MSSQL_USER', 'sa')};"
        f"PWD={os.getenv('MSSQL_PASSWORD', 'kolob_OK1')};"
        "TrustServerCertificate=yes;"
    )
    
    # Подключение к PostgreSQL
    console.print("[blue]📤 Подключение к PostgreSQL[/blue]")
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
        query = "SELECT cicanKey, cicanName FROM ags.cnInvCmmAgN ORDER BY cicanKey"
        df = pd.read_sql(query, mssql_conn)
        console.print(f"Извлечено {len(df)} строк из MS SQL Server")
        
        if len(df) == 0:
            console.print("[yellow]⚠️ Таблица пуста в MS SQL Server[/yellow]")
            return True
        
        # Показываем данные
        console.print("[blue]📋 Данные из MS SQL Server:[/blue]")
        for index, row in df.iterrows():
            console.print(f"  {row['cicanKey']}: {row['cicanName']}")
        
        # 2. Очистка целевой таблицы
        console.print("[blue]🧹 Очистка целевой таблицы[/blue]")
        with pg_conn.cursor() as cur:
            cur.execute("DELETE FROM ags.cninvcmmagn")
            pg_conn.commit()
        
        # 3. Загрузка данных в PostgreSQL
        console.print("[blue]📤 Загрузка данных в PostgreSQL[/blue]")
        with pg_conn.cursor() as cur:
            for index, row in df.iterrows():
                # Используем OVERRIDING SYSTEM VALUE для identity колонки
                sql = """
                INSERT INTO ags.cninvcmmagn (cican_key, cican_name) 
                OVERRIDING SYSTEM VALUE 
                VALUES (%s, %s)
                """
                cur.execute(sql, (row['cicanKey'], row['cicanName']))
            
            pg_conn.commit()
        
        # 4. Проверка результатов
        console.print("[blue]✅ Проверка результатов переноса[/blue]")
        with pg_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM ags.cninvcmmagn")
            row_count = cur.fetchone()[0]
            console.print(f"Загружено {row_count} строк в PostgreSQL")
            
            # Показываем загруженные данные
            cur.execute("SELECT cican_key, cican_name FROM ags.cninvcmmagn ORDER BY cican_key")
            rows = cur.fetchall()
            console.print("[blue]📋 Данные в PostgreSQL:[/blue]")
            for row in rows:
                console.print(f"  {row[0]}: {row[1]}")
            
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

if __name__ == "__main__":
    success = migrate_cnInvCmmAgN()
    sys.exit(0 if success else 1)









