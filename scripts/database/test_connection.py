#!/usr/bin/env python3
"""
FEMCL - Тестирование подключения к базе данных
Проверяет подключение к PostgreSQL и схему mcl
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Загрузка переменных окружения
load_dotenv()

console = Console()

def test_connection():
    """Тестирование подключения к базе данных"""
    try:
        # Параметры подключения
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        database = os.getenv('POSTGRES_DB', 'Fish_Eye')
        user = os.getenv('POSTGRES_USER', 'alex')
        password = os.getenv('POSTGRES_PASSWORD', '')
        
        console.print(f"[blue]Подключение к PostgreSQL...[/blue]")
        console.print(f"Host: {host}:{port}")
        console.print(f"Database: {database}")
        console.print(f"User: {user}")
        
        # Подключение к базе данных
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        console.print("[green]✅ Подключение успешно![/green]")
        
        # Проверка версии PostgreSQL
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            console.print(f"[blue]PostgreSQL версия:[/blue] {version}")
        
        # Проверка схем
        with conn.cursor() as cur:
            cur.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name;")
            schemas = cur.fetchall()
            
            table = Table(title="Доступные схемы")
            table.add_column("Схема", style="cyan")
            
            for schema in schemas:
                table.add_row(schema[0])
            
            console.print(table)
        
        # Проверка схемы mcl
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'mcl' 
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            
            console.print(f"[blue]Таблицы в схеме mcl:[/blue] {len(tables)}")
            
            if tables:
                table = Table(title="Таблицы схемы mcl")
                table.add_column("Таблица", style="green")
                
                for table_name in tables:
                    table.add_row(table_name[0])
                
                console.print(table)
        
        # Проверка статуса миграции
        with conn.cursor() as cur:
            cur.execute("""
                SELECT migration_status, count(*) 
                FROM mcl.mssql_tables 
                GROUP BY migration_status 
                ORDER BY migration_status;
            """)
            status = cur.fetchall()
            
            console.print("[blue]Статус миграции MS SQL таблиц:[/blue]")
            for status_name, count in status:
                console.print(f"  {status_name}: {count}")
        
        # Проверка проблем
        with conn.cursor() as cur:
            cur.execute("""
                SELECT severity_level, count(*) 
                FROM mcl.problems 
                GROUP BY severity_level 
                ORDER BY severity_level;
            """)
            problems = cur.fetchall()
            
            console.print("[blue]Проблемы миграции:[/blue]")
            for severity, count in problems:
                console.print(f"  {severity}: {count}")
        
        conn.close()
        console.print("[green]✅ Все проверки пройдены успешно![/green]")
        
    except psycopg2.Error as e:
        console.print(f"[red]❌ Ошибка подключения к базе данных:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Неожиданная ошибка:[/red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_connection()