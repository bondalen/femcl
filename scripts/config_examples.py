#!/usr/bin/env python3
"""
Примеры использования конфигурации системы миграции FEMCL
"""
import psycopg2
import pyodbc
from config_loader import get_config
from rich.console import Console

console = Console()

def example_database_connections():
    """Пример использования конфигурации для подключения к базам данных"""
    config = get_config()
    
    console.print("[blue]🔌 Примеры подключения к базам данных[/blue]")
    
    try:
        # Подключение к MS SQL Server
        mssql_config = config.get_database_config('mssql')
        mssql_conn_str = config.get_connection_string('mssql')
        
        console.print(f"[green]✅ Строка подключения MS SQL:[/green]")
        console.print(f"  {mssql_conn_str}")
        
        # Подключение к PostgreSQL
        postgres_config = config.get_database_config('postgres')
        postgres_conn_str = config.get_connection_string('postgres')
        
        console.print(f"[green]✅ Строка подключения PostgreSQL:[/green]")
        console.print(f"  {postgres_conn_str}")
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка получения конфигурации: {e}[/red]")

def example_migration_settings():
    """Пример использования настроек миграции"""
    config = get_config()
    
    console.print("[blue]🎯 Примеры настроек миграции[/blue]")
    
    try:
        migration_config = config.get_migration_config()
        
        console.print(f"  Целевая схема: {migration_config.get('target_schema')}")
        console.print(f"  Размер пакета: {migration_config.get('batch_size')}")
        console.print(f"  Максимум попыток: {migration_config.get('max_retries')}")
        console.print(f"  Таймаут: {migration_config.get('timeout')} сек")
        console.print(f"  Порог больших таблиц: {migration_config.get('large_table_threshold')} строк")
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка получения настроек миграции: {e}[/red]")

def example_readiness_check():
    """Пример использования настроек проверки готовности"""
    config = get_config()
    
    console.print("[blue]🔍 Примеры настроек проверки готовности[/blue]")
    
    try:
        readiness_config = config.get_readiness_check()
        
        console.print(f"  Минимальный процент готовности: {readiness_config.get('min_readiness_percentage')}%")
        console.print(f"  Проверка родительских объектов: {readiness_config.get('check_parent_objects')}")
        console.print(f"  Проверка дочерних таблиц: {readiness_config.get('check_child_tables')}")
        console.print(f"  Проверка колонок: {readiness_config.get('check_columns')}")
        console.print(f"  Проверка индексов: {readiness_config.get('check_indexes')}")
        console.print(f"  Проверка ограничений: {readiness_config.get('check_constraints')}")
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка получения настроек проверки готовности: {e}[/red]")

def example_data_migration():
    """Пример использования настроек переноса данных"""
    config = get_config()
    
    console.print("[blue]📦 Примеры настроек переноса данных[/blue]")
    
    try:
        data_config = config.get_data_migration_config()
        
        console.print(f"  Стратегия переноса: {data_config.get('transfer_strategy')}")
        console.print(f"  Размер пакета: {data_config.get('batch_size')}")
        console.print(f"  Параллельные воркеры: {data_config.get('parallel_workers')}")
        console.print(f"  Обработка identity колонок: {data_config.get('handle_identity_columns')}")
        console.print(f"  Проверка целостности: {data_config.get('check_data_integrity')}")
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка получения настроек переноса данных: {e}[/red]")

def example_security_settings():
    """Пример использования настроек безопасности"""
    config = get_config()
    
    console.print("[blue]🔒 Примеры настроек безопасности[/blue]")
    
    try:
        security_config = config.get_security_config()
        
        console.print(f"  Шифрование паролей: {security_config.get('encrypt_passwords')}")
        console.print(f"  SSL соединения: {security_config.get('use_ssl_connections')}")
        console.print(f"  Проверка прав доступа: {security_config.get('check_user_permissions')}")
        console.print(f"  Логирование событий безопасности: {security_config.get('log_security_events')}")
        console.print(f"  Резервное копирование: {security_config.get('backup_critical_data')}")
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка получения настроек безопасности: {e}[/red]")

def example_development_settings():
    """Пример использования настроек разработки"""
    config = get_config()
    
    console.print("[blue]🔧 Примеры настроек разработки[/blue]")
    
    try:
        dev_config = config.get_development_config()
        
        console.print(f"  Режим отладки: {dev_config.get('debug_mode')}")
        console.print(f"  Подробное логирование: {dev_config.get('verbose_logging')}")
        console.print(f"  Тестовый режим: {dev_config.get('dry_run')}")
        console.print(f"  Запуск тестов: {dev_config.get('run_tests')}")
        console.print(f"  Размер тестовых данных: {dev_config.get('test_data_size')}")
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка получения настроек разработки: {e}[/red]")

def main():
    """Основная функция с примерами"""
    console.print("[bold blue]📋 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ КОНФИГУРАЦИИ FEMCL[/bold blue]")
    
    # Проверяем валидность конфигурации
    config = get_config()
    if not config.validate_config():
        console.print("[red]❌ Конфигурация невалидна, примеры не могут быть выполнены[/red]")
        return
    
    # Выводим примеры
    example_database_connections()
    console.print()
    
    example_migration_settings()
    console.print()
    
    example_readiness_check()
    console.print()
    
    example_data_migration()
    console.print()
    
    example_security_settings()
    console.print()
    
    example_development_settings()
    
    console.print("\n[green]✅ Все примеры выполнены успешно![/green]")

if __name__ == "__main__":
    main()