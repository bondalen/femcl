#!/usr/bin/env python3
"""
Перенос данных таблицы cn из MS SQL Server в PostgreSQL
"""
import psycopg2
import pyodbc
from rich.console import Console

console = Console()

def transfer_data():
    """Перенос данных из MS SQL Server в PostgreSQL"""
    console.print("[blue]📦 Перенос данных таблицы cn[/blue]")
    
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
    
    pg_cursor = pg_conn.cursor()
    mssql_cursor = mssql_conn.cursor()
    
    try:
        # Очищаем таблицу в PostgreSQL
        console.print("[yellow]⚠️ Очистка таблицы в PostgreSQL...[/yellow]")
        pg_cursor.execute("TRUNCATE TABLE ags.cn")
        pg_conn.commit()
        
        # Получаем данные из MS SQL Server
        console.print("[blue]📥 Извлечение данных из MS SQL Server...[/blue]")
        mssql_cursor.execute("SELECT * FROM ags.cn ORDER BY cn_key")
        
        # Проверяем, есть ли данные
        first_row = mssql_cursor.fetchone()
        if not first_row:
            console.print("[red]❌ Нет данных в MS SQL Server[/red]")
            return False
        
        # Возвращаем курсор к началу
        mssql_cursor.execute("SELECT * FROM ags.cn ORDER BY cn_key")
        
        # Получаем информацию о колонках
        mssql_cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'ags' AND TABLE_NAME = 'cn'
        ORDER BY ORDINAL_POSITION
        """)
        column_names = [row[0] for row in mssql_cursor.fetchall()]
        
        # Создаем SQL для вставки
        placeholders = ",".join(["%s"] * len(column_names))
        columns_str = ",".join(column_names)
        insert_sql = f"INSERT INTO ags.cn ({columns_str}) VALUES ({placeholders})"
        
        console.print(f"[blue]📝 SQL для вставки: {insert_sql}[/blue]")
        
        # Переносим данные порциями
        batch_size = 500
        total_inserted = 0
        
        while True:
            rows = mssql_cursor.fetchmany(batch_size)
            if not rows:
                break
            
            # Конвертируем данные
            converted_rows = []
            for row in rows:
                converted_row = []
                for value in row:
                    if value is None:
                        converted_row.append(None)
                    elif isinstance(value, str):
                        # Экранируем кавычки
                        converted_row.append(value.replace("'", "''"))
                    else:
                        converted_row.append(value)
                converted_rows.append(tuple(converted_row))
            
            # Вставляем данные
            pg_cursor.executemany(insert_sql, converted_rows)
            total_inserted += len(converted_rows)
            
            console.print(f"[blue]📊 Перенесено строк: {total_inserted}[/blue]")
        
        pg_conn.commit()
        console.print(f"[green]✅ Данные успешно перенесены: {total_inserted} строк[/green]")
        
        # Проверяем результат
        pg_cursor.execute("SELECT COUNT(*) FROM ags.cn")
        final_count = pg_cursor.fetchone()[0]
        console.print(f"[blue]📊 Итоговое количество строк в PostgreSQL: {final_count}[/blue]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка переноса данных: {e}[/red]")
        pg_conn.rollback()
        return False
    
    finally:
        pg_conn.close()
        mssql_conn.close()

if __name__ == "__main__":
    success = transfer_data()
    if success:
        console.print("[green]🎉 Перенос данных завершен успешно![/green]")
    else:
        console.print("[red]❌ Ошибка переноса данных[/red]")