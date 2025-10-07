#!/usr/bin/env python3
"""
Тестовый скрипт для проверки ConnectionManager и ConnectionDiagnostics

Использование:
    python3 test_connection_manager.py
"""

import sys
from pathlib import Path

# Добавляем путь к модулям проекта
sys.path.insert(0, str(Path(__file__).parent / "src" / "code"))

from infrastructure.classes import ConnectionManager, ConnectionDiagnostics

try:
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False
    print("Rich не установлен. Используется простой вывод.")


def print_section(title: str):
    """Вывод заголовка секции."""
    if RICH_AVAILABLE:
        console.print(f"\n[bold cyan]{title}[/bold cyan]")
    else:
        print(f"\n{'='*60}")
        print(title)
        print('='*60)


def test_connection_manager():
    """Тест ConnectionManager."""
    print_section("🔌 ТЕСТ 1: Инициализация ConnectionManager")
    
    try:
        # Инициализация с task_id=2 по умолчанию
        manager = ConnectionManager()
        
        if RICH_AVAILABLE:
            console.print("[green]✅ ConnectionManager инициализирован успешно[/green]")
        else:
            print("✅ ConnectionManager инициализирован успешно")
        
        # Информация о профиле
        info = manager.get_connection_info()
        
        if RICH_AVAILABLE:
            console.print(f"  Task ID: [yellow]{info['task_id']}[/yellow]")
            console.print(f"  Профиль: [yellow]{info['profile_name']}[/yellow]")
            console.print(f"  Описание: {info['description']}")
        else:
            print(f"  Task ID: {info['task_id']}")
            print(f"  Профиль: {info['profile_name']}")
            print(f"  Описание: {info['description']}")
        
        return manager
        
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Ошибка: {e}[/red]")
        else:
            print(f"❌ Ошибка: {e}")
        return None


def test_postgres_connection(manager: ConnectionManager):
    """Тест подключения к PostgreSQL."""
    print_section("🐘 ТЕСТ 2: Подключение к PostgreSQL")
    
    try:
        conn = manager.get_postgres_connection()
        
        if RICH_AVAILABLE:
            console.print("[green]✅ Подключение к PostgreSQL успешно[/green]")
        else:
            print("✅ Подключение к PostgreSQL успешно")
        
        # Проверка версии
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        
        if RICH_AVAILABLE:
            console.print(f"  Версия: [cyan]{version[:50]}...[/cyan]")
        else:
            print(f"  Версия: {version[:50]}...")
        
        return True
        
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Ошибка подключения: {e}[/red]")
        else:
            print(f"❌ Ошибка подключения: {e}")
        return False


def test_mssql_connection(manager: ConnectionManager):
    """Тест подключения к MS SQL Server."""
    print_section("🗄️  ТЕСТ 3: Подключение к MS SQL Server")
    
    try:
        conn = manager.get_mssql_connection()
        
        if RICH_AVAILABLE:
            console.print("[green]✅ Подключение к MS SQL Server успешно[/green]")
        else:
            print("✅ Подключение к MS SQL Server успешно")
        
        # Проверка версии
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        cursor.close()
        
        if RICH_AVAILABLE:
            console.print(f"  Версия: [cyan]{version[:50]}...[/cyan]")
        else:
            print(f"  Версия: {version[:50]}...")
        
        return True
        
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Ошибка подключения: {e}[/red]")
        else:
            print(f"❌ Ошибка подключения: {e}")
        return False


def test_diagnostics(manager: ConnectionManager):
    """Тест ConnectionDiagnostics."""
    print_section("🔍 ТЕСТ 4: ConnectionDiagnostics")
    
    try:
        diagnostics = ConnectionDiagnostics(manager)
        
        if RICH_AVAILABLE:
            console.print("[green]✅ ConnectionDiagnostics инициализирован[/green]")
        else:
            print("✅ ConnectionDiagnostics инициализирован")
        
        # Тест подключений
        if RICH_AVAILABLE:
            console.print("\n[cyan]Тестирование подключений...[/cyan]")
        else:
            print("\nТестирование подключений...")
        
        test_results = diagnostics.test_all_connections()
        
        pg_status = test_results['postgres']['status']
        ms_status = test_results['mssql']['status']
        
        if RICH_AVAILABLE:
            pg_icon = "✅" if pg_status == 'success' else "❌"
            ms_icon = "✅" if ms_status == 'success' else "❌"
            console.print(f"  {pg_icon} PostgreSQL: {pg_status}")
            console.print(f"  {ms_icon} MS SQL Server: {ms_status}")
        else:
            print(f"  PostgreSQL: {pg_status}")
            print(f"  MS SQL Server: {ms_status}")
        
        # Проверка схемы mcl
        if RICH_AVAILABLE:
            console.print("\n[cyan]Проверка схемы mcl...[/cyan]")
        else:
            print("\nПроверка схемы mcl...")
        
        mcl_exists = diagnostics.check_schema_exists('mcl', 'postgres')
        
        if mcl_exists:
            if RICH_AVAILABLE:
                console.print("[green]  ✅ Схема mcl существует[/green]")
            else:
                print("  ✅ Схема mcl существует")
            
            tables_count = diagnostics.get_schema_tables_count('mcl', 'postgres')
            if RICH_AVAILABLE:
                console.print(f"  Таблиц в схеме: [yellow]{tables_count}[/yellow]")
            else:
                print(f"  Таблиц в схеме: {tables_count}")
        else:
            if RICH_AVAILABLE:
                console.print("[yellow]  ⚠️  Схема mcl не найдена[/yellow]")
            else:
                print("  ⚠️  Схема mcl не найдена")
        
        return diagnostics
        
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Ошибка: {e}[/red]")
        else:
            print(f"❌ Ошибка: {e}")
        return None


def test_full_report(diagnostics: ConnectionDiagnostics):
    """Тест полного диагностического отчета."""
    print_section("📊 ТЕСТ 5: Полный диагностический отчет")
    
    try:
        if RICH_AVAILABLE:
            console.print("[cyan]Генерация полного отчета...[/cyan]\n")
        else:
            print("Генерация полного отчета...\n")
        
        diagnostics.print_diagnostic_report()
        
        if RICH_AVAILABLE:
            console.print("\n[green]✅ Отчет сгенерирован успешно[/green]")
        else:
            print("\n✅ Отчет сгенерирован успешно")
        
        return True
        
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Ошибка генерации отчета: {e}[/red]")
        else:
            print(f"❌ Ошибка генерации отчета: {e}")
        return False


def test_context_manager():
    """Тест использования ConnectionManager как context manager."""
    print_section("🔄 ТЕСТ 6: Context Manager")
    
    try:
        with ConnectionManager() as manager:
            if RICH_AVAILABLE:
                console.print("[green]✅ ConnectionManager открыт как context manager[/green]")
            else:
                print("✅ ConnectionManager открыт как context manager")
            
            info = manager.get_connection_info()
            if RICH_AVAILABLE:
                console.print(f"  Task ID: [yellow]{info['task_id']}[/yellow]")
            else:
                print(f"  Task ID: {info['task_id']}")
        
        if RICH_AVAILABLE:
            console.print("[green]✅ Подключения автоматически закрыты[/green]")
        else:
            print("✅ Подключения автоматически закрыты")
        
        return True
        
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Ошибка: {e}[/red]")
        else:
            print(f"❌ Ошибка: {e}")
        return False


def main():
    """Основная функция тестирования."""
    if RICH_AVAILABLE:
        console.print(Panel.fit(
            "[bold green]🧪 ТЕСТИРОВАНИЕ CONNECTION MANAGER[/bold green]\n"
            "Проверка работы ConnectionManager и ConnectionDiagnostics",
            border_style="green"
        ))
    else:
        print("\n" + "="*60)
        print("🧪 ТЕСТИРОВАНИЕ CONNECTION MANAGER")
        print("="*60)
    
    # Тест 1: Инициализация
    manager = test_connection_manager()
    if not manager:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось инициализировать ConnectionManager")
        return False
    
    # Тест 2: PostgreSQL
    pg_ok = test_postgres_connection(manager)
    
    # Тест 3: MS SQL Server
    ms_ok = test_mssql_connection(manager)
    
    # Тест 4: Diagnostics
    diagnostics = test_diagnostics(manager)
    
    # Тест 5: Полный отчет
    if diagnostics:
        test_full_report(diagnostics)
    
    # Тест 6: Context Manager
    test_context_manager()
    
    # Закрываем подключения
    manager.close_all_connections()
    
    # Итоговый отчет
    print_section("📋 ИТОГИ ТЕСТИРОВАНИЯ")
    
    tests_passed = sum([
        manager is not None,
        pg_ok,
        ms_ok,
        diagnostics is not None
    ])
    
    if RICH_AVAILABLE:
        console.print(f"\n[bold]Пройдено тестов: {tests_passed}/4[/bold]")
        
        if tests_passed == 4:
            console.print(Panel.fit(
                "[bold green]✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО![/bold green]\n"
                "ConnectionManager и ConnectionDiagnostics работают корректно.",
                border_style="green"
            ))
        else:
            console.print(Panel.fit(
                f"[bold yellow]⚠️  ПРОЙДЕНО {tests_passed}/4 ТЕСТОВ[/bold yellow]\n"
                "Проверьте ошибки выше.",
                border_style="yellow"
            ))
    else:
        print(f"\nПройдено тестов: {tests_passed}/4")
        if tests_passed == 4:
            print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print(f"\n⚠️  ПРОЙДЕНО {tests_passed}/4 ТЕСТОВ")
    
    return tests_passed == 4


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

