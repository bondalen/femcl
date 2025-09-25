#!/usr/bin/env python3
"""
FEMCL - Проверка статуса миграции
Мониторинг прогресса миграции и выявление проблем
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

# Загрузка переменных окружения
load_dotenv()

console = Console()

def check_migration_status():
    """Проверка статуса миграции"""
    try:
        # Параметры подключения
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        database = os.getenv('POSTGRES_DB', 'Fish_Eye')
        user = os.getenv('POSTGRES_USER', 'alex')
        password = os.getenv('POSTGRES_PASSWORD', '')
        
        # Подключение к базе данных
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        console.print(Panel.fit("[bold blue]FEMCL - Статус миграции[/bold blue]", border_style="blue"))
        
        # Общая статистика
        with conn.cursor() as cur:
            # Количество задач миграции
            cur.execute("SELECT COUNT(*) FROM mcl.migration_tasks;")
            tasks_count = cur.fetchone()[0]
            
            # Количество MS SQL таблиц
            cur.execute("SELECT COUNT(*) FROM mcl.mssql_tables;")
            mssql_count = cur.fetchone()[0]
            
            # Количество PostgreSQL таблиц
            cur.execute("SELECT COUNT(*) FROM mcl.postgres_tables;")
            postgres_count = cur.fetchone()[0]
            
            # Количество проблем
            cur.execute("SELECT COUNT(*) FROM mcl.problems;")
            problems_count = cur.fetchone()[0]
            
            console.print(f"[blue]Задач миграции:[/blue] {tasks_count}")
            console.print(f"[blue]MS SQL таблиц:[/blue] {mssql_count}")
            console.print(f"[blue]PostgreSQL таблиц:[/blue] {postgres_count}")
            console.print(f"[blue]Проблем:[/blue] {problems_count}")
        
        # Статус миграции MS SQL таблиц
        with conn.cursor() as cur:
            cur.execute("""
                SELECT migration_status, count(*) 
                FROM mcl.mssql_tables 
                GROUP BY migration_status 
                ORDER BY migration_status;
            """)
            mssql_status = cur.fetchall()
            
            table = Table(title="Статус миграции MS SQL таблиц")
            table.add_column("Статус", style="cyan")
            table.add_column("Количество", style="green")
            
            for status, count in mssql_status:
                table.add_row(status, str(count))
            
            console.print(table)
        
        # Статус миграции PostgreSQL таблиц
        with conn.cursor() as cur:
            cur.execute("""
                SELECT migration_status, count(*) 
                FROM mcl.postgres_tables 
                GROUP BY migration_status 
                ORDER BY migration_status;
            """)
            postgres_status = cur.fetchall()
            
            table = Table(title="Статус миграции PostgreSQL таблиц")
            table.add_column("Статус", style="cyan")
            table.add_column("Количество", style="green")
            
            for status, count in postgres_status:
                table.add_row(status, str(count))
            
            console.print(table)
        
        # Проблемы по уровням серьезности
        with conn.cursor() as cur:
            cur.execute("""
                SELECT severity_level, count(*) 
                FROM mcl.problems 
                GROUP BY severity_level 
                ORDER BY 
                    CASE severity_level 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                    END;
            """)
            problems = cur.fetchall()
            
            table = Table(title="Проблемы по уровням серьезности")
            table.add_column("Уровень", style="cyan")
            table.add_column("Количество", style="red")
            
            for severity, count in problems:
                color = "red" if severity == "high" else "yellow" if severity == "medium" else "green"
                table.add_row(severity, str(count), style=color)
            
            console.print(table)
        
        # Детали проблем
        with conn.cursor() as cur:
            cur.execute("""
                SELECT problem_name, problem_category, severity_level 
                FROM mcl.problems 
                ORDER BY 
                    CASE severity_level 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                    END,
                    problem_name;
            """)
            problem_details = cur.fetchall()
            
            table = Table(title="Детали проблем")
            table.add_column("Проблема", style="cyan")
            table.add_column("Категория", style="blue")
            table.add_column("Уровень", style="red")
            
            for name, category, severity in problem_details:
                color = "red" if severity == "high" else "yellow" if severity == "medium" else "green"
                table.add_row(name, category, severity, style=color)
            
            console.print(table)
        
        # Прогресс миграции
        total_mssql = mssql_count
        migrated_count = postgres_count
        
        if total_mssql > 0:
            progress_percent = (migrated_count / total_mssql) * 100
            console.print(f"[blue]Прогресс миграции:[/blue] {migrated_count}/{total_mssql} ({progress_percent:.1f}%)")
        
        # Рекомендации
        console.print(Panel.fit("[bold yellow]Рекомендации:[/bold yellow]", border_style="yellow"))
        
        if problems_count > 0:
            console.print("1. Решить выявленные проблемы перед началом миграции")
        
        if mssql_count > postgres_count:
            console.print("2. Запустить процесс миграции таблиц")
        
        if total_mssql > 0 and migrated_count == 0:
            console.print("3. Начать миграцию с простых таблиц")
        
        conn.close()
        console.print("[green]✅ Проверка статуса завершена![/green]")
        
    except psycopg2.Error as e:
        console.print(f"[red]❌ Ошибка подключения к базе данных:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Неожиданная ошибка:[/red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_migration_status()