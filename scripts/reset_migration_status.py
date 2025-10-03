#!/usr/bin/env python3
"""
FEMCL - Сброс статуса миграции для задачи ID=2
Сбрасывает статус всех таблиц на 'pending' для повторной миграции
"""
import psycopg2
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

console = Console()

def reset_migration_status(task_id=2):
    """Сброс статуса миграции для всех таблиц задачи"""
    
    try:
        # Подключение к PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="fish_eye",
            user="postgres",
            password="postgres"
        )
        
        console.print(Panel.fit("[bold blue]🔄 FEMCL - Сброс статуса миграции[/bold blue]", border_style="blue"))
        console.print(f"[blue]Задача миграции: ID={task_id}[/blue]")
        
        with conn.cursor() as cur:
            # Получение текущей статистики
            cur.execute("""
                SELECT 
                    migration_status,
                    COUNT(*) as count
                FROM mcl.mssql_tables 
                WHERE task_id = %s
                GROUP BY migration_status
                ORDER BY migration_status
            """, (task_id,))
            
            current_status = cur.fetchall()
            
            console.print("\n[blue]📊 Текущий статус таблиц:[/blue]")
            status_table = Table(title="Статус до сброса")
            status_table.add_column("Статус", style="cyan")
            status_table.add_column("Количество", style="green")
            
            for status, count in current_status:
                status_table.add_row(status, str(count))
            
            console.print(status_table)
            
            # Сброс статуса всех таблиц на 'pending'
            cur.execute("""
                UPDATE mcl.mssql_tables 
                SET 
                    migration_status = 'pending',
                    migration_date = NULL,
                    error_message = NULL
                WHERE task_id = %s
            """, (task_id,))
            
            affected_rows = cur.rowcount
            
            # Сброс статуса в postgres_tables
            cur.execute("""
                UPDATE mcl.postgres_tables 
                SET 
                    migration_status = 'pending',
                    migration_date = NULL,
                    error_message = NULL
                WHERE source_table_id IN (
                    SELECT id FROM mcl.mssql_tables WHERE task_id = %s
                )
            """, (task_id,))
            
            postgres_affected = cur.rowcount
            
            # Подтверждение изменений
            conn.commit()
            
            # Получение новой статистики
            cur.execute("""
                SELECT 
                    migration_status,
                    COUNT(*) as count
                FROM mcl.mssql_tables 
                WHERE task_id = %s
                GROUP BY migration_status
                ORDER BY migration_status
            """, (task_id,))
            
            new_status = cur.fetchall()
            
            console.print("\n[green]✅ Сброс статуса выполнен успешно![/green]")
            console.print(f"[green]📊 Обновлено MS SQL таблиц: {affected_rows}[/green]")
            console.print(f"[green]📊 Обновлено PostgreSQL таблиц: {postgres_affected}[/green]")
            
            console.print("\n[blue]📊 Новый статус таблиц:[/blue]")
            new_status_table = Table(title="Статус после сброса")
            new_status_table.add_column("Статус", style="cyan")
            new_status_table.add_column("Количество", style="green")
            
            for status, count in new_status:
                new_status_table.add_row(status, str(count))
            
            console.print(new_status_table)
            
            # Проверка, что все таблицы в статусе 'pending'
            pending_count = sum(count for status, count in new_status if status == 'pending')
            total_count = sum(count for status, count in new_status)
            
            if pending_count == total_count:
                console.print(f"\n[green]✅ Все {total_count} таблиц сброшены на статус 'pending'[/green]")
                console.print("[green]🚀 Готово к выполнению миграции![/green]")
                return True
            else:
                console.print(f"\n[yellow]⚠️ Не все таблицы сброшены: {pending_count}/{total_count}[/yellow]")
                return False
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка сброса статуса: {e}[/red]")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Основная функция"""
    success = reset_migration_status(task_id=2)
    
    if success:
        console.print("\n[bold green]🎉 Сброс статуса миграции завершен успешно![/bold green]")
        console.print("[blue]📋 Все таблицы задачи ID=2 готовы к миграции[/blue]")
    else:
        console.print("\n[bold red]❌ Ошибка при сбросе статуса миграции[/bold red]")
        console.print("[yellow]⚠️ Требуется ручная проверка[/yellow]")

if __name__ == "__main__":
    main()