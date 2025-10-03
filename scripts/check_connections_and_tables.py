#!/usr/bin/env python3
"""
FEMCL - Проверка подключений к базам данных и исходных таблиц
Использует конфигурацию из config.yaml
"""
import yaml
import pyodbc
import psycopg2
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def load_config():
    """Загрузка конфигурации из config.yaml"""
    try:
        with open('/home/alex/projects/sql/femcl/config/config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        console.print("[green]✅ Конфигурация загружена успешно[/green]")
        return config
    except Exception as e:
        console.print(f"[red]❌ Ошибка загрузки конфигурации: {e}[/red]")
        return None

def check_mssql_connection(config):
    """Проверка подключения к MS SQL Server"""
    console.print("[blue]🔍 Проверка подключения к MS SQL Server...[/blue]")
    
    try:
        mssql_config = config['database']['mssql']
        
        connection_string = (
            f"DRIVER={{{mssql_config['driver']}}};"
            f"SERVER={mssql_config['server']},{mssql_config['port']};"
            f"DATABASE={mssql_config['database']};"
            f"UID={mssql_config['user']};"
            f"PWD={mssql_config['password']};"
            f"TrustServerCertificate={'yes' if mssql_config['trust_certificate'] else 'no'};"
            f"Connection Timeout={mssql_config['connection_timeout']};"
            f"Command Timeout={mssql_config['command_timeout']};"
        )
        
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Проверка доступности базы данных
        cursor.execute("SELECT DB_NAME() as current_database")
        result = cursor.fetchone()
        current_db = result[0]
        
        # Проверка схемы ags
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables 
            WHERE table_schema = 'ags'
        """)
        result = cursor.fetchone()
        ags_tables_count = result[0]
        
        # Проверка схемы mcl
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables 
            WHERE table_schema = 'mcl'
        """)
        result = cursor.fetchone()
        mcl_tables_count = result[0]
        
        conn.close()
        
        console.print(f"[green]✅ MS SQL Server: {mssql_config['server']}:{mssql_config['port']}[/green]")
        console.print(f"[green]✅ База данных: {current_db}[/green]")
        console.print(f"[green]✅ Таблиц в схеме ags: {ags_tables_count}[/green]")
        console.print(f"[green]✅ Таблиц в схеме mcl: {mcl_tables_count}[/green]")
        
        return {
            'status': 'success',
            'server': f"{mssql_config['server']}:{mssql_config['port']}",
            'database': current_db,
            'ags_tables': ags_tables_count,
            'mcl_tables': mcl_tables_count
        }
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка подключения к MS SQL Server: {e}[/red]")
        return {
            'status': 'error',
            'error': str(e)
        }

def check_postgres_connection(config):
    """Проверка подключения к PostgreSQL"""
    console.print("[blue]🔍 Проверка подключения к PostgreSQL...[/blue]")
    
    try:
        postgres_config = config['database']['postgres']
        
        conn = psycopg2.connect(
            host=postgres_config['host'],
            port=postgres_config['port'],
            dbname=postgres_config['database'],
            user=postgres_config['user'],
            password=postgres_config['password'],
            connect_timeout=postgres_config['connection_timeout'],
            sslmode=postgres_config['ssl_mode']
        )
        
        cursor = conn.cursor()
        
        # Проверка доступности базы данных
        cursor.execute("SELECT current_database()")
        result = cursor.fetchone()
        current_db = result[0]
        
        # Проверка схемы mcl
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables 
            WHERE table_schema = 'mcl'
        """)
        result = cursor.fetchone()
        mcl_tables_count = result[0]
        
        # Проверка схемы ags
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables 
            WHERE table_schema = 'ags'
        """)
        result = cursor.fetchone()
        ags_tables_count = result[0]
        
        conn.close()
        
        console.print(f"[green]✅ PostgreSQL: {postgres_config['host']}:{postgres_config['port']}[/green]")
        console.print(f"[green]✅ База данных: {current_db}[/green]")
        console.print(f"[green]✅ Таблиц в схеме mcl: {mcl_tables_count}[/green]")
        console.print(f"[green]✅ Таблиц в схеме ags: {ags_tables_count}[/green]")
        
        return {
            'status': 'success',
            'server': f"{postgres_config['host']}:{postgres_config['port']}",
            'database': current_db,
            'mcl_tables': mcl_tables_count,
            'ags_tables': ags_tables_count
        }
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка подключения к PostgreSQL: {e}[/red]")
        return {
            'status': 'error',
            'error': str(e)
        }

def check_source_tables(config):
    """Проверка исходных таблиц в MS SQL Server"""
    console.print("[blue]🔍 Проверка исходных таблиц в MS SQL Server...[/blue]")
    
    try:
        mssql_config = config['database']['mssql']
        
        connection_string = (
            f"DRIVER={{{mssql_config['driver']}}};"
            f"SERVER={mssql_config['server']},{mssql_config['port']};"
            f"DATABASE={mssql_config['database']};"
            f"UID={mssql_config['user']};"
            f"PWD={mssql_config['password']};"
            f"TrustServerCertificate={'yes' if mssql_config['trust_certificate'] else 'no'};"
        )
        
        conn = pyodbc.connect(connection_string)
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
        
        conn.close()
        
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

def check_migration_metadata(config):
    """Проверка метаданных миграции в PostgreSQL"""
    console.print("[blue]🔍 Проверка метаданных миграции в PostgreSQL...[/blue]")
    
    try:
        postgres_config = config['database']['postgres']
        
        conn = psycopg2.connect(
            host=postgres_config['host'],
            port=postgres_config['port'],
            dbname=postgres_config['database'],
            user=postgres_config['user'],
            password=postgres_config['password']
        )
        
        cursor = conn.cursor()
        
        # Проверка задач миграции
        cursor.execute("SELECT COUNT(*) FROM mcl.migration_tasks")
        tasks_count = cursor.fetchone()[0]
        
        # Проверка MS SQL таблиц в метаданных
        cursor.execute("SELECT COUNT(*) FROM mcl.mssql_tables")
        mssql_tables_count = cursor.fetchone()[0]
        
        # Проверка PostgreSQL таблиц в метаданных
        cursor.execute("SELECT COUNT(*) FROM mcl.postgres_tables")
        postgres_tables_count = cursor.fetchone()[0]
        
        # Проверка проблем
        cursor.execute("SELECT COUNT(*) FROM mcl.problems")
        problems_count = cursor.fetchone()[0]
        
        # Статус миграции
        cursor.execute("""
            SELECT migration_status, COUNT(*) 
            FROM mcl.mssql_tables 
            GROUP BY migration_status 
            ORDER BY migration_status
        """)
        migration_status = cursor.fetchall()
        
        # Создание таблицы статуса
        status_table = Table(title="📊 Статус миграции")
        status_table.add_column("Статус", style="cyan")
        status_table.add_column("Количество", style="green")
        
        for status, count in migration_status:
            status_table.add_row(status, str(count))
        
        console.print(status_table)
        
        console.print(f"[blue]📊 Задач миграции: {tasks_count}[/blue]")
        console.print(f"[blue]📊 MS SQL таблиц в метаданных: {mssql_tables_count}[/blue]")
        console.print(f"[blue]📊 PostgreSQL таблиц в метаданных: {postgres_tables_count}[/blue]")
        console.print(f"[blue]📊 Проблем: {problems_count}[/blue]")
        
        conn.close()
        
        return {
            'status': 'success',
            'tasks_count': tasks_count,
            'mssql_tables_count': mssql_tables_count,
            'postgres_tables_count': postgres_tables_count,
            'problems_count': problems_count,
            'migration_status': migration_status
        }
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка проверки метаданных: {e}[/red]")
        return {
            'status': 'error',
            'error': str(e)
        }

def main():
    """Основная функция проверки"""
    console.print(Panel.fit("[bold blue]🔍 FEMCL - Проверка подключений и исходных таблиц[/bold blue]", border_style="blue"))
    
    # Загрузка конфигурации
    config = load_config()
    if not config:
        return False
    
    # Проверка подключений
    console.print("\n[bold blue]🔌 ПРОВЕРКА ПОДКЛЮЧЕНИЙ[/bold blue]")
    
    mssql_result = check_mssql_connection(config)
    postgres_result = check_postgres_connection(config)
    
    # Проверка исходных таблиц
    console.print("\n[bold blue]📊 ПРОВЕРКА ИСХОДНЫХ ТАБЛИЦ[/bold blue]")
    source_tables_result = check_source_tables(config)
    
    # Проверка метаданных миграции
    console.print("\n[bold blue]📋 ПРОВЕРКА МЕТАДАННЫХ МИГРАЦИИ[/bold blue]")
    metadata_result = check_migration_metadata(config)
    
    # Итоговая оценка
    console.print("\n[bold blue]📈 ИТОГОВАЯ ОЦЕНКА[/bold blue]")
    
    all_success = (
        mssql_result['status'] == 'success' and
        postgres_result['status'] == 'success' and
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

if __name__ == "__main__":
    main()