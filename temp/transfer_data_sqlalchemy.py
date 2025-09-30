#!/usr/bin/env python3
"""
Перенос данных таблицы cn с использованием SQLAlchemy
"""
import psycopg2
import pyodbc
import pandas as pd
from sqlalchemy import create_engine
from rich.console import Console

console = Console()

def transfer_data_sqlalchemy():
    """Перенос данных с использованием SQLAlchemy"""
    console.print("[blue]📦 Перенос данных таблицы cn (SQLAlchemy)[/blue]")
    
    # MS SQL Server
    mssql_conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=FishEye;"
        "UID=sa;"
        "PWD=kolob_OK1;"
        "TrustServerCertificate=yes;"
    )
    
    # PostgreSQL engine
    pg_engine = create_engine('postgresql://postgres:postgres@localhost:5432/fish_eye')
    
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
        console.print(df.head(3).to_string())
        
        # Очищаем таблицу в PostgreSQL
        console.print("[yellow]⚠️ Очистка таблицы в PostgreSQL...[/yellow]")
        with pg_engine.connect() as conn:
            conn.execute("TRUNCATE TABLE ags.cn")
            conn.commit()
        
        # Записываем данные в PostgreSQL
        console.print("[blue]📤 Запись данных в PostgreSQL...[/blue]")
        
        # Используем to_sql с SQLAlchemy engine
        df.to_sql('cn', pg_engine, schema='ags', if_exists='append', index=False, method='multi')
        
        # Проверяем результат
        with pg_engine.connect() as conn:
            result = conn.execute("SELECT COUNT(*) FROM ags.cn")
            final_count = result.fetchone()[0]
        
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

if __name__ == "__main__":
    success = transfer_data_sqlalchemy()
    if success:
        console.print("[green]🎉 Перенос данных завершен успешно![/green]")
    else:
        console.print("[red]❌ Ошибка переноса данных[/red]")