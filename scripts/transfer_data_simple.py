#!/usr/bin/env python3
"""
Простой перенос данных таблицы cn
"""
import psycopg2
import pyodbc
import pandas as pd
from rich.console import Console

console = Console()

def transfer_data_simple():
    """Простой перенос данных"""
    console.print("[blue]📦 Простой перенос данных таблицы cn[/blue]")
    
    # MS SQL Server
    mssql_conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=FishEye;"
        "UID=sa;"
        "PWD=kolob_OK1;"
        "TrustServerCertificate=yes;"
    )
    
    # PostgreSQL
    pg_conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="fish_eye",
        user="postgres",
        password="postgres"
    )
    
    try:
        # Читаем данные из MS SQL Server
        console.print("[blue]📥 Чтение данных из MS SQL Server...[/blue]")
        df = pd.read_sql("SELECT * FROM ags.cn ORDER BY cn_key", mssql_conn)
        console.print(f"📊 Загружено строк: {len(df)}")
        
        if len(df) == 0:
            console.print("[red]❌ Нет данных в MS SQL Server[/red]")
            return False
        
        # Показываем первые несколько строк
        console.print("[blue]📋 Первые 3 строки данных:[/blue]")
        for i in range(min(3, len(df))):
            row = df.iloc[i]
            console.print(f"  {i+1}. cn_key={row['cn_key']}, cn_number={row['cn_number']}")
        
        # Очищаем таблицу в PostgreSQL
        console.print("[yellow]⚠️ Очистка таблицы в PostgreSQL...[/yellow]")
        pg_cursor = pg_conn.cursor()
        pg_cursor.execute("TRUNCATE TABLE ags.cn")
        pg_conn.commit()
        
        # Записываем данные построчно
        console.print("[blue]📤 Запись данных в PostgreSQL...[/blue]")
        
        insert_sql = """
        INSERT INTO ags.cn (cn_key, cn_number, cn_date, cn_note, cnMark, cnTimeOfEntry, cnName) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        total_inserted = 0
        for index, row in df.iterrows():
            try:
                # Конвертируем данные
                values = (
                    int(row['cn_key']) if pd.notna(row['cn_key']) else None,
                    str(row['cn_number']) if pd.notna(row['cn_number']) else None,
                    row['cn_date'] if pd.notna(row['cn_date']) else None,
                    str(row['cn_note']) if pd.notna(row['cn_note']) else None,
                    int(row['cnMark']) if pd.notna(row['cnMark']) else None,
                    row['cnTimeOfEntry'] if pd.notna(row['cnTimeOfEntry']) else None,
                    str(row['cnName']) if pd.notna(row['cnName']) else None
                )
                
                pg_cursor.execute(insert_sql, values)
                total_inserted += 1
                
                if total_inserted % 100 == 0:
                    console.print(f"[blue]📊 Перенесено строк: {total_inserted}[/blue]")
                    
            except Exception as e:
                console.print(f"[red]❌ Ошибка в строке {index}: {e}[/red]")
                continue
        
        pg_conn.commit()
        console.print(f"[green]✅ Данные успешно перенесены: {total_inserted} строк[/green]")
        
        # Проверяем результат
        pg_cursor.execute("SELECT COUNT(*) FROM ags.cn")
        final_count = pg_cursor.fetchone()[0]
        console.print(f"[blue]📊 Итоговое количество строк в PostgreSQL: {final_count}[/blue]")
        
        if final_count == len(df):
            console.print("[green]✅ Все данные успешно перенесены![/green]")
            return True
        else:
            console.print(f"[red]❌ Несоответствие: {final_count} != {len(df)}[/red]")
            return False
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка переноса данных: {e}[/red]")
        return False
    
    finally:
        mssql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    success = transfer_data_simple()
    if success:
        console.print("[green]🎉 Перенос данных завершен успешно![/green]")
    else:
        console.print("[red]❌ Ошибка переноса данных[/red]")