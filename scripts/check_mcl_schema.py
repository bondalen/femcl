#!/usr/bin/env python3
"""
Проверка схемы mcl в PostgreSQL

ОБНОВЛЕНО: Использует ConnectionManager и ConnectionDiagnostics
"""
import sys
from pathlib import Path

# Добавляем путь к модулям проекта
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "code"))

from infrastructure.classes import ConnectionManager, ConnectionDiagnostics
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def check_mcl_schema_detailed(manager: ConnectionManager):
    """Детальная проверка схемы mcl"""
    console.print("[blue]📋 Проверка схемы mcl в PostgreSQL...[/blue]")
    
    try:
        conn = manager.get_postgres_connection()
        cursor = conn.cursor()
        
        # Получаем список таблиц в схеме mcl
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'mcl' 
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        console.print(f"\n[cyan]📊 Таблицы в схеме mcl: {len(tables)}[/cyan]")
        
        # Ожидаемые ключевые таблицы
        key_tables = [
            'migration_tasks',
            'mssql_tables', 'postgres_tables',
            'mssql_columns', 'postgres_columns',
            'mssql_indexes', 'postgres_indexes',
            'mssql_foreign_keys', 'postgres_foreign_keys',
            'function_mapping_rules'
        ]
        
        existing_tables = [table[0] for table in tables]
        
        # Проверка ключевых таблиц
        console.print("\n[yellow]🔑 Ключевые таблицы:[/yellow]")
        table_status = Table()
        table_status.add_column("Таблица", style="cyan")
        table_status.add_column("Статус", style="green")
        table_status.add_column("Записей", style="yellow")
        
        for key_table in key_tables:
            if key_table in existing_tables:
                # Получаем количество записей
                cursor.execute(f"SELECT COUNT(*) FROM mcl.{key_table}")
                count = cursor.fetchone()[0]
                table_status.add_row(key_table, "✅ Есть", str(count))
            else:
                table_status.add_row(key_table, "❌ Нет", "-")
        
        console.print(table_status)
        
        cursor.close()
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка: {e}[/red]")
        return False


def main():
    """Основная функция проверки"""
    console.print(Panel.fit(
        "[bold cyan]🔍 ПРОВЕРКА СХЕМЫ MCL[/bold cyan]",
        border_style="cyan"
    ))
    
    try:
        # Инициализация ConnectionManager (task_id=2 по умолчанию)
        manager = ConnectionManager()
        
        # Информация о профиле
        info = manager.get_connection_info()
        console.print(f"\n[green]✅ Профиль: {info['profile_name']} (task_id={info['task_id']})[/green]")
        
        # Инициализация ConnectionDiagnostics
        diagnostics = ConnectionDiagnostics(manager)
        
        # Быстрая проверка схемы
        mcl_info = diagnostics.check_mcl_schema_postgres()
        
        if mcl_info['exists']:
            console.print(f"[green]✅ Схема mcl существует[/green]")
            console.print(f"[yellow]📊 Таблиц в схеме: {mcl_info['tables_count']}[/yellow]")
            
            # Детальная проверка
            check_mcl_schema_detailed(manager)
            
            # Проверка таблиц метаданных
            console.print("\n[cyan]🔍 Проверка таблиц метаданных...[/cyan]")
            tables_check = diagnostics.check_mcl_tables()
            
            if tables_check['status'] == 'success':
                console.print("[green]✅ Проверка таблиц метаданных завершена[/green]")
        else:
            console.print("[red]❌ Схема mcl не найдена![/red]")
            console.print("[yellow]💡 Возможно, нужно восстановить схему из бэкапа[/yellow]")
            return False
        
        return True
        
    except ValueError as e:
        console.print(f"[red]❌ Ошибка: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Неожиданная ошибка: {e}[/red]")
        return False
    finally:
        if 'manager' in locals():
            manager.close_all_connections()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

    check_mcl_schema()