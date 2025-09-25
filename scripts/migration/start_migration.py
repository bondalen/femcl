#!/usr/bin/env python3
"""
FEMCL - Запуск процесса миграции
Автоматизированный запуск миграции согласно диаграмме процесса
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
import time

# Загрузка переменных окружения
load_dotenv()

console = Console()

def start_migration():
    """Запуск процесса миграции"""
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
        
        console.print(Panel.fit("[bold blue]FEMCL - Запуск миграции[/bold blue]", border_style="blue"))
        
        # Проверка готовности к миграции
        with conn.cursor() as cur:
            # Проверка задач миграции
            cur.execute("SELECT COUNT(*) FROM mcl.migration_tasks;")
            tasks_count = cur.fetchone()[0]
            
            if tasks_count == 0:
                console.print("[red]❌ Нет задач миграции! Создайте задачу перед запуском.[/red]")
                return
            
            # Проверка MS SQL таблиц
            cur.execute("SELECT COUNT(*) FROM mcl.mssql_tables;")
            mssql_count = cur.fetchone()[0]
            
            if mssql_count == 0:
                console.print("[red]❌ Нет MS SQL таблиц для миграции![/red]")
                return
            
            # Проверка проблем
            cur.execute("SELECT COUNT(*) FROM mcl.problems WHERE severity_level = 'high';")
            high_problems = cur.fetchone()[0]
            
            if high_problems > 0:
                console.print(f"[yellow]⚠️ Обнаружено {high_problems} критических проблем. Рекомендуется решить их перед миграцией.[/yellow]")
                
                # Показать критические проблемы
                cur.execute("""
                    SELECT problem_name, problem_category 
                    FROM mcl.problems 
                    WHERE severity_level = 'high' 
                    ORDER BY problem_name;
                """)
                problems = cur.fetchall()
                
                table = Table(title="Критические проблемы")
                table.add_column("Проблема", style="red")
                table.add_column("Категория", style="yellow")
                
                for name, category in problems:
                    table.add_row(name, category)
                
                console.print(table)
                
                # Запрос подтверждения
                response = input("Продолжить миграцию несмотря на критические проблемы? (y/N): ")
                if response.lower() != 'y':
                    console.print("[yellow]Миграция отменена.[/yellow]")
                    return
        
        # Получение списка таблиц для миграции
        with conn.cursor() as cur:
            cur.execute("""
                SELECT object_name, schema_name, table_size, row_count 
                FROM mcl.mssql_tables 
                WHERE migration_status = 'pending' 
                ORDER BY table_size DESC, row_count DESC;
            """)
            tables_to_migrate = cur.fetchall()
        
        console.print(f"[blue]Найдено таблиц для миграции:[/blue] {len(tables_to_migrate)}")
        
        # Показать топ-10 таблиц по размеру
        if tables_to_migrate:
            table = Table(title="Топ-10 таблиц по размеру")
            table.add_column("Таблица", style="cyan")
            table.add_column("Схема", style="blue")
            table.add_column("Размер (MB)", style="green")
            table.add_column("Строк", style="yellow")
            
            for name, schema, size, rows in tables_to_migrate[:10]:
                size_mb = size / (1024 * 1024) if size else 0
                table.add_row(name, schema, f"{size_mb:.2f}", str(rows))
            
            console.print(table)
        
        # Запрос подтверждения
        response = input(f"Начать миграцию {len(tables_to_migrate)} таблиц? (y/N): ")
        if response.lower() != 'y':
            console.print("[yellow]Миграция отменена.[/yellow]")
            return
        
        # Запуск миграции
        console.print("[green]🚀 Запуск миграции...[/green]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            
            task = progress.add_task("Миграция таблиц...", total=len(tables_to_migrate))
            
            migrated_count = 0
            failed_count = 0
            
            for table_name, schema_name, table_size, row_count in tables_to_migrate:
                try:
                    # Обновление статуса на "in_progress"
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE mcl.mssql_tables 
                            SET migration_status = 'in_progress', 
                                migration_date = NOW() 
                            WHERE object_name = %s AND schema_name = %s;
                        """, (table_name, schema_name))
                        conn.commit()
                    
                    # Симуляция миграции (заменить на реальную логику)
                    time.sleep(0.1)  # Имитация времени миграции
                    
                    # Обновление статуса на "completed"
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE mcl.mssql_tables 
                            SET migration_status = 'completed' 
                            WHERE object_name = %s AND schema_name = %s;
                        """, (table_name, schema_name))
                        conn.commit()
                    
                    migrated_count += 1
                    progress.update(task, advance=1, description=f"Мигрирована: {table_name}")
                    
                except Exception as e:
                    # Обновление статуса на "failed"
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE mcl.mssql_tables 
                            SET migration_status = 'failed', 
                                error_message = %s 
                            WHERE object_name = %s AND schema_name = %s;
                        """, (str(e), table_name, schema_name))
                        conn.commit()
                    
                    failed_count += 1
                    progress.update(task, advance=1, description=f"Ошибка: {table_name}")
        
        # Итоговая статистика
        console.print(Panel.fit("[bold green]Миграция завершена![/bold green]", border_style="green"))
        console.print(f"[green]✅ Успешно мигрировано:[/green] {migrated_count}")
        console.print(f"[red]❌ Ошибок:[/red] {failed_count}")
        
        # Обновление статистики
        with conn.cursor() as cur:
            cur.execute("""
                SELECT migration_status, count(*) 
                FROM mcl.mssql_tables 
                GROUP BY migration_status 
                ORDER BY migration_status;
            """)
            final_status = cur.fetchall()
            
            table = Table(title="Итоговый статус миграции")
            table.add_column("Статус", style="cyan")
            table.add_column("Количество", style="green")
            
            for status, count in final_status:
                table.add_row(status, str(count))
            
            console.print(table)
        
        conn.close()
        
    except psycopg2.Error as e:
        console.print(f"[red]❌ Ошибка подключения к базе данных:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Неожиданная ошибка:[/red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_migration()