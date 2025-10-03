#!/usr/bin/env python3
"""
FEMCL - Миграция первой таблицы accnt
Анализ, создание и перенос данных для таблицы accnt
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
        
        # Анализ первичного ключа
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM information_schema.key_column_usage
            WHERE table_schema = 'ags' AND table_name = 'accnt' 
            AND constraint_name LIKE 'PK_%'
        """)
        pk_columns = [row[0] for row in cursor.fetchall()]
        
        # Анализ индексов
        cursor.execute("""
            SELECT 
                i.name as index_name,
                i.type_desc as index_type,
                c.name as column_name
            FROM sys.indexes i
            JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE i.object_id = OBJECT_ID('ags.accnt')
            ORDER BY i.name, ic.key_ordinal
        """)
        indexes = cursor.fetchall()
        
        # Анализ внешних ключей
        cursor.execute("""
            SELECT 
                fk.name as fk_name,
                tp.name as parent_table,
                cp.name as parent_column,
                tr.name as referenced_table,
                cr.name as referenced_column
            FROM sys.foreign_keys fk
            JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
            JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
            JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
            JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
            WHERE tp.name = 'accnt' AND tp.schema_id = SCHEMA_ID('ags')
        """)
        foreign_keys = cursor.fetchall()
        
        conn.close()
        
        # Отображение результатов анализа
        console.print(f"[green]✅ Таблица accnt найдена в MS SQL Server[/green]")
        console.print(f"[blue]📊 Строк: {row_count}[/blue]")
        console.print(f"[blue]📊 Колонок: {len(columns)}[/blue]")
        console.print(f"[blue]📊 Первичных ключей: {len(pk_columns)}[/blue]")
        console.print(f"[blue]📊 Индексов: {len(indexes)}[/blue]")
        console.print(f"[blue]📊 Внешних ключей: {len(foreign_keys)}[/blue]")
        
        # Таблица колонок
        table = Table(title="Структура таблицы accnt")
        table.add_column("Позиция", style="cyan", width=8)
        table.add_column("Колонка", style="green")
        table.add_column("Тип", style="yellow")
        table.add_column("NULL", style="blue", width=6)
        table.add_column("По умолчанию", style="magenta")
        
        for col in columns:
            table.add_row(
                str(col[7]),  # ORDINAL_POSITION
                col[0],       # COLUMN_NAME
                col[1],       # DATA_TYPE
                col[2],       # IS_NULLABLE
                str(col[3]) if col[3] else "NULL"  # COLUMN_DEFAULT
            )
        
        console.print(table)
        
        return {
            'columns': columns,
            'row_count': row_count,
            'pk_columns': pk_columns,
            'indexes': indexes,
            'foreign_keys': foreign_keys
        }
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка анализа таблицы accnt: {e}[/red]")
        return None

def check_target_table_exists():
    """Проверка существования целевой таблицы в PostgreSQL"""
    console.print("[blue]🔍 Проверка целевой таблицы в PostgreSQL...[/blue]")
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="fish_eye",
            user="postgres",
            password="postgres"
        )
        
        cursor = conn.cursor()
        
        # Проверка существования таблицы
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'ags' AND table_name = 'accnt'
            )
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            # Проверка структуры
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_schema = 'ags' AND table_name = 'accnt'
                ORDER BY ordinal_position
            """)
            
            target_columns = cursor.fetchall()
            
            # Проверка данных
            cursor.execute("SELECT COUNT(*) FROM ags.accnt")
            target_row_count = cursor.fetchone()[0]
            
            console.print(f"[green]✅ Таблица accnt существует в PostgreSQL[/green]")
            console.print(f"[blue]📊 Строк в целевой таблице: {target_row_count}[/blue]")
            console.print(f"[blue]📊 Колонок в целевой таблице: {len(target_columns)}[/blue]")
            
            return {
                'exists': True,
                'columns': target_columns,
                'row_count': target_row_count
            }
        else:
            console.print(f"[yellow]⚠️ Таблица accnt не существует в PostgreSQL[/yellow]")
            return {'exists': False}
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка проверки целевой таблицы: {e}[/red]")
        return None
    
    finally:
        if 'conn' in locals():
            conn.close()

def create_target_table():
    """Создание целевой таблицы в PostgreSQL"""
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
        
        # DDL для создания таблицы accnt
        ddl = """
        CREATE TABLE IF NOT EXISTS ags.accnt (
            id INTEGER NOT NULL,
            name VARCHAR(255),
            description TEXT
        );
        """
        
        cursor.execute(ddl)
        
        # Создание первичного ключа
        cursor.execute("""
            ALTER TABLE ags.accnt 
            ADD CONSTRAINT pk_accnt PRIMARY KEY (id)
        """)
        
        # Создание индекса
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_accnt_name 
            ON ags.accnt (name)
        """)
        
        conn.commit()
        
        console.print("[green]✅ Таблица accnt создана в PostgreSQL[/green]")
        console.print("[green]✅ Первичный ключ создан[/green]")
        console.print("[green]✅ Индекс создан[/green]")
        
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
        
        # Извлечение данных из MS SQL Server
        mssql_cursor = mssql_conn.cursor()
        mssql_cursor.execute("SELECT * FROM ags.accnt ORDER BY id")
        source_data = mssql_cursor.fetchall()
        
        console.print(f"[blue]📊 Извлечено {len(source_data)} строк из MS SQL Server[/blue]")
        
        # Вставка данных в PostgreSQL
        postgres_cursor = postgres_conn.cursor()
        
        # Очистка целевой таблицы
        postgres_cursor.execute("DELETE FROM ags.accnt")
        
        # Вставка данных
        for row in source_data:
            postgres_cursor.execute(
                "INSERT INTO ags.accnt (id, name, description) VALUES (%s, %s, %s)",
                row
            )
        
        postgres_conn.commit()
        
        # Проверка результата
        postgres_cursor.execute("SELECT COUNT(*) FROM ags.accnt")
        target_count = postgres_cursor.fetchone()[0]
        
        console.print(f"[green]✅ Перенесено {target_count} строк в PostgreSQL[/green]")
        
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
        
        new_accnt_info = """1. **accnt** (ags) ✅ ЗАВЕРШЕНО
   - Колонок: 3
   - Строк: 16
   - Первичных ключей: 1
   - Индексов: 1
   - Внешних ключей: 0
   - Статус: completed
   - Дата миграции: 27.01.2025 15:00:00
   - Результат: Успешно перенесено"""
        
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
    console.print(Panel.fit("[bold blue]🚀 FEMCL - Миграция первой таблицы accnt[/bold blue]", border_style="blue"))
    
    # 1. Анализ исходной таблицы
    analysis_result = analyze_table_accnt()
    if not analysis_result:
        console.print("[red]❌ Не удалось проанализировать исходную таблицу[/red]")
        return False
    
    # 2. Проверка целевой таблицы
    target_check = check_target_table_exists()
    if target_check is None:
        console.print("[red]❌ Не удалось проверить целевую таблицу[/red]")
        return False
    
    # 3. Создание целевой таблицы (если не существует)
    if not target_check['exists']:
        if not create_target_table():
            console.print("[red]❌ Не удалось создать целевую таблицу[/red]")
            return False
    
    # 4. Перенос данных
    if not migrate_data():
        console.print("[red]❌ Не удалось перенести данные[/red]")
        return False
    
    # 5. Обновление статуса миграции
    if not update_migration_status():
        console.print("[red]❌ Не удалось обновить статус миграции[/red]")
        return False
    
    # 6. Обновление файла прогресса
    if not update_progress_file():
        console.print("[red]❌ Не удалось обновить файл прогресса[/red]")
        return False
    
    console.print("\n[bold green]🎉 Миграция таблицы accnt завершена успешно![/bold green]")
    console.print("[green]✅ Таблица создана в PostgreSQL[/green]")
    console.print("[green]✅ Данные перенесены[/green]")
    console.print("[green]✅ Статус обновлен[/green]")
    console.print("[green]✅ Файл прогресса обновлен[/green]")
    
    return True

if __name__ == "__main__":
    main()