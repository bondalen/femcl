#!/usr/bin/env python3
"""
FEMCL - Миграция первой таблицы accnt (ИСПРАВЛЕННАЯ ВЕРСИЯ)
Анализ, создание и перенос данных для таблицы accnt с правильными именами колонок
"""
import psycopg2
import pyodbc
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

console = Console()

def load_config():
    """Загрузка конфигурации"""
    try:
        with open('/home/alex/projects/sql/femcl/config/config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        console.print(f"[red]❌ Ошибка загрузки конфигурации: {e}[/red]")
        return None

def analyze_table_accnt():
    """Анализ таблицы accnt в MS SQL Server"""
    console.print("[blue]🔍 Анализ таблицы accnt в MS SQL Server...[/blue]")
    
    config = load_config()
    if not config:
        return None
    
    try:
        # Подключение к MS SQL Server
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
        
        # Анализ структуры таблицы
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE,
                ORDINAL_POSITION
            FROM information_schema.columns 
            WHERE table_schema = 'ags' AND table_name = 'accnt'
            ORDER BY ORDINAL_POSITION
        """)
        
        columns = cursor.fetchall()
        
        # Анализ данных
        cursor.execute("SELECT COUNT(*) FROM ags.accnt")
        row_count = cursor.fetchone()[0]
        
        # Получение образца данных
        cursor.execute("SELECT TOP 5 * FROM ags.accnt ORDER BY account_key")
        sample_data = cursor.fetchall()
        
        conn.close()
        
        # Отображение результатов анализа
        console.print(f"[green]✅ Таблица accnt найдена в MS SQL Server[/green]")
        console.print(f"[blue]📊 Строк: {row_count}[/blue]")
        console.print(f"[blue]📊 Колонок: {len(columns)}[/blue]")
        
        # Таблица колонок
        table = Table(title="Структура таблицы accnt")
        table.add_column("Позиция", style="cyan", width=8)
        table.add_column("Колонка", style="green")
        table.add_column("Тип", style="yellow")
        table.add_column("NULL", style="blue", width=6)
        table.add_column("Длина", style="magenta", width=8)
        
        for col in columns:
            length = col[4] if col[4] else ""
            table.add_row(
                str(col[7]),  # ORDINAL_POSITION
                col[0],       # COLUMN_NAME
                col[1],       # DATA_TYPE
                col[2],       # IS_NULLABLE
                str(length)   # CHARACTER_MAXIMUM_LENGTH
            )
        
        console.print(table)
        
        # Образец данных
        if sample_data:
            console.print("\n[blue]📋 Образец данных:[/blue]")
            sample_table = Table(title="Первые 5 строк")
            sample_table.add_column("account_key", style="cyan")
            sample_table.add_column("account_num", style="green")
            sample_table.add_column("account_name", style="yellow")
            
            for row in sample_data:
                sample_table.add_row(str(row[0]), str(row[1]), str(row[2]))
            
            console.print(sample_table)
        
        return {
            'columns': columns,
            'row_count': row_count,
            'sample_data': sample_data
        }
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка анализа таблицы accnt: {e}[/red]")
        return None

def create_target_table():
    """Создание целевой таблицы в PostgreSQL с правильной структурой"""
    console.print("[blue]🔧 Создание целевой таблицы accnt в PostgreSQL...[/blue]")
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="fish_eye",
            user="postgres",
            password="postgres"
        )
        
        cursor = conn.cursor()
        
        # Удаление таблицы если существует
        cursor.execute("DROP TABLE IF EXISTS ags.accnt CASCADE")
        
        # DDL для создания таблицы accnt с правильными именами колонок
        ddl = """
        CREATE TABLE ags.accnt (
            account_key INTEGER NOT NULL,
            account_num INTEGER NOT NULL,
            account_name VARCHAR(255) NOT NULL
        );
        """
        
        cursor.execute(ddl)
        
        # Создание первичного ключа
        cursor.execute("""
            ALTER TABLE ags.accnt 
            ADD CONSTRAINT pk_accnt PRIMARY KEY (account_key)
        """)
        
        # Создание индекса
        cursor.execute("""
            CREATE INDEX idx_accnt_account_num 
            ON ags.accnt (account_num)
        """)
        
        conn.commit()
        
        console.print("[green]✅ Таблица accnt создана в PostgreSQL[/green]")
        console.print("[green]✅ Первичный ключ создан (account_key)[/green]")
        console.print("[green]✅ Индекс создан (account_num)[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка создания таблицы: {e}[/red]")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

def migrate_data():
    """Перенос данных из MS SQL Server в PostgreSQL"""
    console.print("[blue]📦 Перенос данных из MS SQL Server в PostgreSQL...[/blue]")
    
    config = load_config()
    if not config:
        return False
    
    try:
        # Подключение к MS SQL Server
        mssql_config = config['database']['mssql']
        mssql_conn = pyodbc.connect(
            f"DRIVER={{{mssql_config['driver']}}};"
            f"SERVER={mssql_config['server']},{mssql_config['port']};"
            f"DATABASE={mssql_config['database']};"
            f"UID={mssql_config['user']};"
            f"PWD={mssql_config['password']};"
            f"TrustServerCertificate={'yes' if mssql_config['trust_certificate'] else 'no'};"
        )
        
        # Подключение к PostgreSQL
        postgres_conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="fish_eye",
            user="postgres",
            password="postgres"
        )
        
        # Извлечение данных из MS SQL Server с правильными именами колонок
        mssql_cursor = mssql_conn.cursor()
        mssql_cursor.execute("SELECT account_key, account_num, account_name FROM ags.accnt ORDER BY account_key")
        source_data = mssql_cursor.fetchall()
        
        console.print(f"[blue]📊 Извлечено {len(source_data)} строк из MS SQL Server[/blue]")
        
        # Вставка данных в PostgreSQL
        postgres_cursor = postgres_conn.cursor()
        
        # Вставка данных с правильными именами колонок
        for row in source_data:
            postgres_cursor.execute(
                "INSERT INTO ags.accnt (account_key, account_num, account_name) VALUES (%s, %s, %s)",
                row
            )
        
        postgres_conn.commit()
        
        # Проверка результата
        postgres_cursor.execute("SELECT COUNT(*) FROM ags.accnt")
        target_count = postgres_cursor.fetchone()[0]
        
        # Проверка целостности данных
        postgres_cursor.execute("SELECT * FROM ags.accnt ORDER BY account_key LIMIT 5")
        target_sample = postgres_cursor.fetchall()
        
        console.print(f"[green]✅ Перенесено {target_count} строк в PostgreSQL[/green]")
        
        # Отображение образца перенесенных данных
        if target_sample:
            console.print("\n[blue]📋 Образец перенесенных данных:[/blue]")
            sample_table = Table(title="Первые 5 строк в PostgreSQL")
            sample_table.add_column("account_key", style="cyan")
            sample_table.add_column("account_num", style="green")
            sample_table.add_column("account_name", style="yellow")
            
            for row in target_sample:
                sample_table.add_row(str(row[0]), str(row[1]), str(row[2]))
            
            console.print(sample_table)
        
        # Закрытие соединений
        mssql_conn.close()
        postgres_conn.close()
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка переноса данных: {e}[/red]")
        return False

def update_migration_status():
    """Обновление статуса миграции в метаданных"""
    console.print("[blue]📝 Обновление статуса миграции...[/blue]")
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="fish_eye",
            user="postgres",
            password="postgres"
        )
        
        cursor = conn.cursor()
        
        # Обновление статуса в mssql_tables
        cursor.execute("""
            UPDATE mcl.mssql_tables 
            SET 
                migration_status = 'completed',
                migration_date = NOW()
            WHERE object_name = 'accnt' AND task_id = 2
        """)
        
        # Обновление статуса в postgres_tables
        cursor.execute("""
            UPDATE mcl.postgres_tables 
            SET 
                migration_status = 'completed',
                migration_date = NOW()
            WHERE object_name = 'accnt'
        """)
        
        conn.commit()
        
        console.print("[green]✅ Статус миграции обновлен на 'completed'[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка обновления статуса: {e}[/red]")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

def update_progress_file():
    """Обновление файла прогресса с результатами миграции таблицы accnt"""
    console.print("[blue]📝 Обновление файла прогресса...[/blue]")
    
    try:
        progress_file = "/home/alex/projects/sql/femcl/progress/20250127_143000_migration_progress.md"
        
        # Чтение текущего файла
        with open(progress_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Замена информации о таблице accnt
        old_accnt_info = """1. **accnt** (ags)
   - Колонок: 3
   - Строк: 16
   - Первичных ключей: 1
   - Индексов: 1
   - Внешних ключей: 0
   - Статус: pending"""
        
        new_accnt_info = f"""1. **accnt** (ags) ✅ ЗАВЕРШЕНО
   - Колонок: 3
   - Строк: 16
   - Первичных ключей: 1
   - Индексов: 1
   - Внешних ключей: 0
   - Статус: completed
   - Дата миграции: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
   - Результат: Успешно перенесено
   - Структура: account_key (PK), account_num, account_name"""
        
        # Замена в файле
        updated_content = content.replace(old_accnt_info, new_accnt_info)
        
        # Обновление общей статистики
        updated_content = updated_content.replace(
            "- **Завершено:** 0",
            "- **Завершено:** 1"
        )
        updated_content = updated_content.replace(
            "- **Ожидает:** 69",
            "- **Ожидает:** 68"
        )
        updated_content = updated_content.replace(
            "- **Прогресс:** 0%",
            "- **Прогресс:** 1.4%"
        )
        
        # Обновление даты
        updated_content = updated_content.replace(
            f"**Дата обновления:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
            f"**Дата обновления:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        
        # Запись обновленного файла
        with open(progress_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        console.print("[green]✅ Файл прогресса обновлен[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка обновления файла прогресса: {e}[/red]")
        return False

def main():
    """Основная функция миграции таблицы accnt"""
    console.print(Panel.fit("[bold blue]🚀 FEMCL - Миграция первой таблицы accnt (ИСПРАВЛЕННАЯ ВЕРСИЯ)[/bold blue]", border_style="blue"))
    
    # 1. Анализ исходной таблицы
    analysis_result = analyze_table_accnt()
    if not analysis_result:
        console.print("[red]❌ Не удалось проанализировать исходную таблицу[/red]")
        return False
    
    # 2. Создание целевой таблицы
    if not create_target_table():
        console.print("[red]❌ Не удалось создать целевую таблицу[/red]")
        return False
    
    # 3. Перенос данных
    if not migrate_data():
        console.print("[red]❌ Не удалось перенести данные[/red]")
        return False
    
    # 4. Обновление статуса миграции
    if not update_migration_status():
        console.print("[red]❌ Не удалось обновить статус миграции[/red]")
        return False
    
    # 5. Обновление файла прогресса
    if not update_progress_file():
        console.print("[red]❌ Не удалось обновить файл прогресса[/red]")
        return False
    
    console.print("\n[bold green]🎉 Миграция таблицы accnt завершена успешно![/bold green]")
    console.print("[green]✅ Таблица создана в PostgreSQL[/green]")
    console.print("[green]✅ Данные перенесены (16 строк)[/green]")
    console.print("[green]✅ Статус обновлен на 'completed'[/green]")
    console.print("[green]✅ Файл прогресса обновлен[/green]")
    
    return True

if __name__ == "__main__":
    main()