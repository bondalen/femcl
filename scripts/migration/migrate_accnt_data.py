#!/usr/bin/env python3
"""
FEMCL - Миграция данных таблицы accnt
Полный цикл миграции данных из MS SQL Server в PostgreSQL
"""
import os
import sys
import pandas as pd
import pyodbc
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
import json
from datetime import datetime

load_dotenv()
console = Console()

class AccntDataMigrator:
    def __init__(self):
        # MS SQL Server настройки
        self.mssql_server = os.getenv('MSSQL_SERVER', 'localhost')
        self.mssql_port = os.getenv('MSSQL_PORT', '1433')
        self.mssql_db = os.getenv('MSSQL_DB', 'FishEye')
        self.mssql_user = os.getenv('MSSQL_USER', 'sa')
        self.mssql_password = os.getenv('MSSQL_PASSWORD', 'kolob_OK1')
        
        # PostgreSQL настройки
        self.pg_host = os.getenv('POSTGRES_HOST', 'localhost')
        self.pg_port = os.getenv('POSTGRES_PORT', '5432')
        self.pg_db = os.getenv('POSTGRES_DB', 'fish_eye')
        self.pg_user = os.getenv('POSTGRES_USER', 'postgres')
        self.pg_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        
        self.mssql_conn = None
        self.pg_conn = None
        
    def connect_mssql(self):
        """Подключение к MS SQL Server"""
        try:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.mssql_server},{self.mssql_port};"
                f"DATABASE={self.mssql_db};"
                f"UID={self.mssql_user};"
                f"PWD={self.mssql_password};"
                "TrustServerCertificate=yes;"
            )
            
            console.print(f"[blue]Подключение к MS SQL Server...[/blue]")
            self.mssql_conn = pyodbc.connect(conn_str)
            console.print("[green]✅ Подключение к MS SQL Server успешно![/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка подключения к MS SQL Server:[/red] {e}")
            return False
    
    def connect_postgres(self):
        """Подключение к PostgreSQL"""
        try:
            conn_str = f"host={self.pg_host} port={self.pg_port} dbname={self.pg_db} user={self.pg_user} password={self.pg_password}"
            
            console.print(f"[blue]Подключение к PostgreSQL...[/blue]")
            self.pg_conn = psycopg2.connect(conn_str)
            console.print("[green]✅ Подключение к PostgreSQL успешно![/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка подключения к PostgreSQL:[/red] {e}")
            return False
    
    def extract_data_from_mssql(self):
        """Извлечение данных из MS SQL Server"""
        try:
            console.print("[blue]Извлечение данных из MS SQL Server...[/blue]")
            
            query = "SELECT * FROM ags.accnt ORDER BY account_key"
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Извлечение данных из MS SQL", total=None)
                
                df = pd.read_sql(query, self.mssql_conn)
                
            console.print(f"[green]✅ Извлечено {len(df)} строк из MS SQL Server[/green]")
            
            # Отображение информации о данных
            if len(df) > 0:
                console.print(f"[blue]Структура данных:[/blue]")
                console.print(f"Колонки: {list(df.columns)}")
                console.print(f"Типы данных: {df.dtypes.to_dict()}")
                
                # Отображение первых строк
                table = Table(title="Первые 5 строк из MS SQL")
                table.add_column("account_key", style="cyan")
                table.add_column("account_num", style="yellow")
                table.add_column("account_name", style="green")
                
                for index, row in df.head().iterrows():
                    table.add_row(str(row['account_key']), str(row['account_num']), str(row['account_name']))
                
                console.print(table)
            
            return df
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка извлечения данных из MS SQL:[/red] {e}")
            return None
    
    def load_data_to_postgres(self, df):
        """Загрузка данных в PostgreSQL"""
        try:
            console.print("[blue]Загрузка данных в PostgreSQL...[/blue]")
            
            # Очистка таблицы
            with self.pg_conn.cursor() as cur:
                cur.execute("DELETE FROM ags.accnt")
                self.pg_conn.commit()
                console.print("[blue]Таблица ags.accnt очищена[/blue]")
            
            # Загрузка данных
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Загрузка данных в PostgreSQL", total=len(df))
                
                with self.pg_conn.cursor() as cur:
                    for index, row in df.iterrows():
                        # Подготовка данных
                        values = []
                        for col in df.columns:
                            value = row[col]
                            if pd.isna(value):
                                values.append(None)
                            else:
                                values.append(value)
                        
                        # SQL запрос для вставки с OVERRIDING SYSTEM VALUE для identity колонки
                        columns = ', '.join(df.columns)
                        placeholders = ', '.join(['%s'] * len(df.columns))
                        sql = f"INSERT INTO ags.accnt ({columns}) OVERRIDING SYSTEM VALUE VALUES ({placeholders})"
                        
                        cur.execute(sql, values)
                        progress.advance(task)
                
                self.pg_conn.commit()
            
            console.print(f"[green]✅ Загружено {len(df)} строк в PostgreSQL[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка загрузки данных в PostgreSQL:[/red] {e}")
            return False
    
    def verify_migration(self):
        """Проверка результатов миграции"""
        try:
            console.print("[blue]Проверка результатов миграции...[/blue]")
            
            with self.pg_conn.cursor() as cur:
                # Подсчет строк
                cur.execute("SELECT COUNT(*) FROM ags.accnt")
                row_count = cur.fetchone()[0]
                
                console.print(f"[blue]Количество строк в ags.accnt: {row_count}[/blue]")
                
                if row_count > 0:
                    # Получение первых 5 строк
                    cur.execute("SELECT * FROM ags.accnt ORDER BY account_key LIMIT 5")
                    sample_data = cur.fetchall()
                    
                    console.print(f"[blue]Пример данных из PostgreSQL:[/blue]")
                    
                    table = Table(title="Первые 5 строк из PostgreSQL")
                    table.add_column("account_key", style="cyan")
                    table.add_column("account_num", style="yellow")
                    table.add_column("account_name", style="green")
                    
                    for row in sample_data:
                        table.add_row(str(row[0]), str(row[1]), str(row[2]))
                    
                    console.print(table)
                
                return True
                
        except Exception as e:
            console.print(f"[red]❌ Ошибка проверки миграции:[/red] {e}")
            return False
    
    def close_connections(self):
        """Закрытие соединений"""
        if self.mssql_conn:
            self.mssql_conn.close()
            console.print("[blue]Соединение с MS SQL Server закрыто[/blue]")
        
        if self.pg_conn:
            self.pg_conn.close()
            console.print("[blue]Соединение с PostgreSQL закрыто[/blue]")

def main():
    """Основная функция миграции"""
    console.print("[bold blue]FEMCL - Миграция данных таблицы accnt[/bold blue]")
    console.print("[bold]Полный цикл: MS SQL Server → PostgreSQL[/bold]")
    
    migrator = AccntDataMigrator()
    
    try:
        # Подключение к базам данных
        if not migrator.connect_mssql():
            console.print("[red]Не удалось подключиться к MS SQL Server[/red]")
            return False
        
        if not migrator.connect_postgres():
            console.print("[red]Не удалось подключиться к PostgreSQL[/red]")
            return False
        
        # Извлечение данных из MS SQL
        df = migrator.extract_data_from_mssql()
        if df is None:
            console.print("[red]Не удалось извлечь данные из MS SQL Server[/red]")
            return False
        
        # Загрузка данных в PostgreSQL
        if not migrator.load_data_to_postgres(df):
            console.print("[red]Не удалось загрузить данные в PostgreSQL[/red]")
            return False
        
        # Проверка результатов
        if not migrator.verify_migration():
            console.print("[red]Ошибка при проверке результатов миграции[/red]")
            return False
        
        console.print("[green]✅ Миграция данных таблицы accnt завершена успешно![/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка при миграции:[/red] {e}")
        return False
    
    finally:
        migrator.close_connections()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)