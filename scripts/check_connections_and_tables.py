#!/usr/bin/env python3
"""
FEMCL - Проверка подключений к базам данных и исходных таблиц

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


def check_source_tables(manager: ConnectionManager):
    """Проверка исходных таблиц в MS SQL Server"""
    console.print("[blue]🔍 Проверка исходных таблиц в MS SQL Server...[/blue]")
    
    try:
        conn = manager.get_mssql_connection()
        cursor = conn.cursor()
        
        # Получение списка таблиц в схеме ags
        cursor.execute("""
            SELECT 
                TABLE_NAME,
                TABLE_TYPE,
                (SELECT COUNT(*) FROM information_schema.columns 
                 WHERE table_schema = 'ags' AND table_name = t.TABLE_NAME) as COLUMN_COUNT
            FROM information_schema.tables t
            WHERE table_schema = 'ags' AND table_type = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        tables = cursor.fetchall()
        
        # Создание таблицы для отображения
        table = Table(title="📊 Исходные таблицы в схеме ags")
        table.add_column("Таблица", style="cyan")
        table.add_column("Тип", style="green")
        table.add_column("Колонок", style="yellow")
        
        for table_name, table_type, column_count in tables:
            table.add_row(table_name, table_type, str(column_count))
        
        console.print(table)
        console.print(f"[blue]📊 Всего таблиц в схеме ags: {len(tables)}[/blue]")
        
        cursor.close()
        
        return {
            'status': 'success',
            'tables_count': len(tables),
            'tables': tables
        }
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка проверки исходных таблиц: {e}[/red]")
        return {
            'status': 'error',
            'error': str(e)
        }


def main():
    """Основная функция проверки"""
    console.print(Panel.fit(
        "[bold blue]🔍 FEMCL - Проверка подключений и исходных таблиц[/bold blue]",
        border_style="blue"
    ))
    
    try:
        # Инициализация ConnectionManager (task_id=2 по умолчанию)
        console.print("\n[cyan]📡 Инициализация ConnectionManager...[/cyan]")
        manager = ConnectionManager()
        
        # Информация о профиле
        info = manager.get_connection_info()
        console.print(f"[green]✅ Профиль загружен: {info['profile_name']} (task_id={info['task_id']})[/green]")
        
        # Инициализация ConnectionDiagnostics
        diagnostics = ConnectionDiagnostics(manager)
        
        # Проверка подключений
        console.print("\n[bold blue]🔌 ПРОВЕРКА ПОДКЛЮЧЕНИЙ[/bold blue]")
        
        # Тестирование подключений
        test_results = diagnostics.test_all_connections()
        
        mssql_status = test_results['mssql']['status']
        postgres_status = test_results['postgres']['status']
        
        if mssql_status == 'success':
            console.print(f"[green]✅ MS SQL Server: подключение успешно[/green]")
            console.print(f"  {info['source']['host']}:{info['source']['port']}/{info['source']['database']}")
        else:
            console.print(f"[red]❌ MS SQL Server: ошибка подключения[/red]")
            console.print(f"  {test_results['mssql']['error']}")
        
        if postgres_status == 'success':
            console.print(f"[green]✅ PostgreSQL: подключение успешно[/green]")
            console.print(f"  {info['target']['host']}:{info['target']['port']}/{info['target']['database']}")
        else:
            console.print(f"[red]❌ PostgreSQL: ошибка подключения[/red]")
            console.print(f"  {test_results['postgres']['error']}")
        
        # Проверка исходных таблиц
        console.print("\n[bold blue]📊 ПРОВЕРКА ИСХОДНЫХ ТАБЛИЦ[/bold blue]")
        source_tables_result = check_source_tables(manager)
        
        # Проверка метаданных миграции
        console.print("\n[bold blue]📋 ПРОВЕРКА МЕТАДАННЫХ МИГРАЦИИ[/bold blue]")
        metadata_result = diagnostics.check_migration_metadata()
        
        if metadata_result['status'] == 'success':
            console.print(f"[blue]📊 Задач миграции: {metadata_result['tasks_count']}[/blue]")
            console.print(f"[blue]📊 MS SQL таблиц в метаданных: {metadata_result['mssql_tables_count']}[/blue]")
            console.print(f"[blue]📊 PostgreSQL таблиц в метаданных: {metadata_result['postgres_tables_count']}[/blue]")
            console.print(f"[blue]📊 Проблем: {metadata_result['problems_count']}[/blue]")
            
            # Статус миграции
            if metadata_result.get('migration_status'):
                status_table = Table(title="📊 Статус миграции")
                status_table.add_column("Статус", style="cyan")
                status_table.add_column("Количество", style="green")
                
                for status, count in metadata_result['migration_status'].items():
                    status_table.add_row(status, str(count))
                
                console.print(status_table)
        
        # Итоговая оценка
        console.print("\n[bold blue]📈 ИТОГОВАЯ ОЦЕНКА[/bold blue]")
        
        all_success = (
            mssql_status == 'success' and
            postgres_status == 'success' and
            source_tables_result['status'] == 'success' and
            metadata_result['status'] == 'success'
        )
        
        if all_success:
            console.print("[green]✅ Все проверки пройдены успешно![/green]")
            console.print("[green]🚀 Система готова к миграции![/green]")
            return True
        else:
            console.print("[red]❌ Обнаружены проблемы![/red]")
            console.print("[yellow]⚠️ Требуется устранение ошибок перед началом миграции[/yellow]")
            return False
            
    except ValueError as e:
        console.print(f"[red]❌ Ошибка инициализации: {e}[/red]")
        console.print("[yellow]💡 Проверьте connections.json и убедитесь, что профиль для task_id=2 существует[/yellow]")
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
