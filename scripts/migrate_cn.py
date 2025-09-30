#!/usr/bin/env python3
"""
Миграция таблицы cn из MS SQL Server в PostgreSQL
"""
import psycopg2
import pyodbc
import pandas as pd
from rich.console import Console

console = Console()

def connect_databases():
    """Подключение к базам данных"""
    console.print("[blue]🔌 Подключение к базам данных...[/blue]")
    
    # PostgreSQL
    pg_conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="fish_eye",
        user="postgres",
        password="postgres"
    )
    
    # MS SQL Server
    mssql_conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=FishEye;"
        "UID=sa;"
        "PWD=kolob_OK1;"
        "TrustServerCertificate=yes;"
    )
    
    console.print("[green]✅ Подключения установлены[/green]")
    return pg_conn, mssql_conn

def check_table_readiness(pg_conn, mssql_conn):
    """Проверка готовности таблицы cn к миграции"""
    console.print("[blue]🔍 ЭТАП 1: Проверка готовности таблицы cn[/blue]")
    
    pg_cursor = pg_conn.cursor()
    mssql_cursor = mssql_conn.cursor()
    
    # Проверим количество строк в MS SQL Server
    mssql_cursor.execute("SELECT COUNT(*) FROM ags.cn")
    row_count_mssql = mssql_cursor.fetchone()[0]
    console.print(f"📊 Строк в MS SQL Server: {row_count_mssql}")
    
    # Проверим, существует ли таблица в PostgreSQL
    try:
        pg_cursor.execute("SELECT COUNT(*) FROM ags.cn")
        row_count_pg = pg_cursor.fetchone()[0]
        console.print(f"📊 Строк в PostgreSQL: {row_count_pg}")
        table_exists = True
    except:
        console.print("📊 Таблица cn не существует в PostgreSQL")
        row_count_pg = 0
        table_exists = False
    
    # Получим структуру таблицы из MS SQL Server
    console.print("[blue]📋 Получение структуры таблицы cn из MS SQL Server[/blue]")
    
    mssql_cursor.execute("""
    SELECT 
        COLUMN_NAME,
        DATA_TYPE,
        IS_NULLABLE,
        CHARACTER_MAXIMUM_LENGTH,
        NUMERIC_PRECISION,
        NUMERIC_SCALE,
        COLUMN_DEFAULT
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'ags' AND TABLE_NAME = 'cn'
    ORDER BY ORDINAL_POSITION
    """)
    
    columns_info = mssql_cursor.fetchall()
    console.print(f"📊 Найдено колонок: {len(columns_info)}")
    
    for i, col in enumerate(columns_info):
        col_name, data_type, nullable, max_length, precision, scale, default = col
        console.print(f"  {i+1}. {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
        
        if max_length:
            console.print(f"     Максимальная длина: {max_length}")
        if precision:
            console.print(f"     Точность: {precision}, Масштаб: {scale}")
        if default:
            console.print(f"     По умолчанию: {default}")
    
    # Оценка готовности
    readiness_score = 0
    
    if row_count_mssql > 0:
        readiness_score += 25
        console.print("[green]✅ Данные в MS SQL Server найдены[/green]")
    
    if len(columns_info) > 0:
        readiness_score += 25
        console.print("[green]✅ Структура таблицы получена[/green]")
    
    if not table_exists:
        readiness_score += 25
        console.print("[green]✅ Таблица не существует в PostgreSQL (готова к созданию)[/green]")
    else:
        console.print("[yellow]⚠️ Таблица уже существует в PostgreSQL[/yellow]")
    
    if row_count_mssql == 2329:  # Ожидаемое количество строк
        readiness_score += 25
        console.print("[green]✅ Количество строк соответствует ожидаемому[/green]")
    
    console.print(f"[blue]📊 Оценка готовности: {readiness_score}%[/blue]")
    
    return readiness_score >= 75, columns_info, row_count_mssql

def create_table_structure(columns_info):
    """Создание структуры таблицы в PostgreSQL"""
    console.print("[blue]🔧 ЭТАП 2: Создание структуры таблицы cn в PostgreSQL[/blue]")
    
    # Создаем новое соединение
    pg_conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="fish_eye",
        user="postgres",
        password="postgres"
    )
    pg_cursor = pg_conn.cursor()
    
    # Генерируем DDL для создания таблицы
    ddl_parts = ["CREATE TABLE ags.cn ("]
    
    for col in columns_info:
        col_name, data_type, nullable, max_length, precision, scale, default = col
        
        # Преобразуем типы данных MS SQL -> PostgreSQL
        if data_type == "int":
            pg_type = "INTEGER"
        elif data_type == "varchar":
            pg_type = f"VARCHAR({max_length})" if max_length and max_length > 0 else "VARCHAR"
        elif data_type == "nvarchar":
            # Для nvarchar с max_length = -1 (MAX) используем TEXT
            if max_length == -1:
                pg_type = "TEXT"
            else:
                pg_type = f"VARCHAR({max_length})" if max_length and max_length > 0 else "VARCHAR"
        elif data_type == "datetime":
            pg_type = "TIMESTAMP"
        elif data_type == "bit":
            pg_type = "BOOLEAN"
        elif data_type == "decimal":
            pg_type = f"DECIMAL({precision},{scale})" if precision else "DECIMAL"
        else:
            pg_type = data_type.upper()
        
        # Добавляем ограничения
        constraints = []
        if nullable == "NO":
            constraints.append("NOT NULL")
        
        if default:
            constraints.append(f"DEFAULT {default}")
        
        constraint_str = " ".join(constraints)
        ddl_parts.append(f"    {col_name} {pg_type} {constraint_str},")
    
    # Убираем последнюю запятую и закрываем скобку
    ddl_parts[-1] = ddl_parts[-1].rstrip(",")
    ddl_parts.append(");")
    
    ddl = "\n".join(ddl_parts)
    console.print("[blue]📝 Сгенерированный DDL:[/blue]")
    console.print(ddl)
    
    try:
        # Удаляем таблицу если существует
        pg_cursor.execute("DROP TABLE IF EXISTS ags.cn CASCADE;")
        pg_conn.commit()
        console.print("[yellow]⚠️ Существующая таблица удалена[/yellow]")
        
        # Создаем таблицу
        pg_cursor.execute(ddl)
        pg_conn.commit()
        console.print("[green]✅ Таблица cn создана в PostgreSQL[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка создания таблицы: {e}[/red]")
        try:
            pg_conn.rollback()
        except:
            pass
        return False
    finally:
        pg_conn.close()

def migrate_data(pg_conn, mssql_conn, row_count):
    """Перенос данных из MS SQL Server в PostgreSQL"""
    console.print("[blue]📦 ЭТАП 3: Перенос данных из MS SQL Server в PostgreSQL[/blue]")
    
    pg_cursor = pg_conn.cursor()
    mssql_cursor = mssql_conn.cursor()
    
    try:
        # Получаем информацию о колонках для правильной вставки
        mssql_cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'ags' AND TABLE_NAME = 'cn'
        ORDER BY ORDINAL_POSITION
        """)
        column_names = [row[0] for row in mssql_cursor.fetchall()]
        
        # Создаем плейсхолдеры для INSERT
        placeholders = ",".join(["%s"] * len(column_names))
        columns_str = ",".join(column_names)
        
        insert_sql = f"INSERT INTO ags.cn ({columns_str}) VALUES ({placeholders})"
        
        console.print(f"[blue]📝 SQL для вставки: {insert_sql}[/blue]")
        
        # Получаем все данные из MS SQL Server
        console.print("[blue]📥 Извлечение данных из MS SQL Server...[/blue]")
        mssql_cursor.execute("SELECT * FROM ags.cn ORDER BY 1")
        
        # Переносим данные порциями
        batch_size = 1000
        total_inserted = 0
        
        while True:
            rows = mssql_cursor.fetchmany(batch_size)
            if not rows:
                break
                
            # Конвертируем данные для PostgreSQL
            converted_rows = []
            for row in rows:
                converted_row = []
                for value in row:
                    if value is None:
                        converted_row.append(None)
                    elif isinstance(value, str):
                        # Экранируем специальные символы
                        converted_row.append(value.replace("'", "''"))
                    else:
                        converted_row.append(value)
                converted_rows.append(tuple(converted_row))
            
            # Вставляем данные
            pg_cursor.executemany(insert_sql, converted_rows)
            total_inserted += len(converted_rows)
            
            console.print(f"[blue]📊 Перенесено строк: {total_inserted}/{row_count}[/blue]")
        
        pg_conn.commit()
        console.print(f"[green]✅ Данные успешно перенесены: {total_inserted} строк[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка переноса данных: {e}[/red]")
        pg_conn.rollback()
        return False

def verify_migration(pg_conn, expected_count):
    """Проверка результатов миграции"""
    console.print("[blue]🔍 ЭТАП 4: Проверка результатов миграции[/blue]")
    
    pg_cursor = pg_conn.cursor()
    
    try:
        # Проверяем количество строк
        pg_cursor.execute("SELECT COUNT(*) FROM ags.cn")
        actual_count = pg_cursor.fetchone()[0]
        
        console.print(f"📊 Ожидаемое количество строк: {expected_count}")
        console.print(f"📊 Фактическое количество строк: {actual_count}")
        
        if actual_count == expected_count:
            console.print("[green]✅ Количество строк совпадает[/green]")
        else:
            console.print(f"[red]❌ Несоответствие количества строк: {actual_count} != {expected_count}[/red]")
            return False
        
        # Проверяем первые несколько строк
        pg_cursor.execute("SELECT * FROM ags.cn ORDER BY 1 LIMIT 5")
        sample_rows = pg_cursor.fetchall()
        
        console.print("[blue]📋 Примеры данных:[/blue]")
        for i, row in enumerate(sample_rows, 1):
            console.print(f"  {i}. {row}")
        
        console.print("[green]✅ Миграция таблицы cn завершена успешно![/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка проверки результатов: {e}[/red]")
        return False

def main():
    """Основная функция миграции"""
    console.print("[bold blue]🚀 НАЧАЛО МИГРАЦИИ ТАБЛИЦЫ CN[/bold blue]")
    
    try:
        # Подключение к базам данных
        pg_conn, mssql_conn = connect_databases()
        
        # Этап 1: Проверка готовности
        is_ready, columns_info, row_count = check_table_readiness(pg_conn, mssql_conn)
        
        if not is_ready:
            console.print("[red]❌ Таблица не готова к миграции[/red]")
            return False
        
        # Этап 2: Создание структуры
        if not create_table_structure(columns_info):
            console.print("[red]❌ Ошибка создания структуры таблицы[/red]")
            return False
        
        # Этап 3: Перенос данных
        if not migrate_data(pg_conn, mssql_conn, row_count):
            console.print("[red]❌ Ошибка переноса данных[/red]")
            return False
        
        # Этап 4: Проверка результатов
        if not verify_migration(pg_conn, row_count):
            console.print("[red]❌ Ошибка проверки результатов[/red]")
            return False
        
        console.print("[bold green]🎉 МИГРАЦИЯ ТАБЛИЦЫ CN ЗАВЕРШЕНА УСПЕШНО![/bold green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Критическая ошибка: {e}[/red]")
        return False
    
    finally:
        # Закрываем соединения
        try:
            pg_conn.close()
            mssql_conn.close()
            console.print("[blue]🔌 Соединения закрыты[/blue]")
        except:
            pass

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)