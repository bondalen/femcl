#!/usr/bin/env python3
"""
FEMCL - Загрузка данных в PostgreSQL
Скрипт для загрузки данных из CSV файлов в PostgreSQL
"""
import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import json
from datetime import datetime

load_dotenv()
console = Console()

class PostgreSQLLoader:
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = os.getenv('POSTGRES_PORT', '5432')
        self.database = os.getenv('POSTGRES_DB', 'fish_eye')
        self.user = os.getenv('POSTGRES_USER', 'postgres')
        self.password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        self.connection = None
        
    def connect(self):
        """Подключение к PostgreSQL"""
        try:
            conn_str = f"host={self.host} port={self.port} dbname={self.database} user={self.user} password={self.password}"
            
            console.print(f"[blue]Подключение к PostgreSQL...[/blue]")
            console.print(f"Host: {self.host}:{self.port}")
            console.print(f"Database: {self.database}")
            console.print(f"User: {self.user}")
            
            self.connection = psycopg2.connect(conn_str)
            console.print("[green]✅ Подключение успешно![/green]")
            return True
            
        except psycopg2.Error as e:
            console.print(f"[red]❌ Ошибка подключения к PostgreSQL:[/red] {e}")
            return False
        except Exception as e:
            console.print(f"[red]❌ Неожиданная ошибка:[/red] {e}")
            return False
    
    def load_csv_data(self, csv_file, table_name, schema='ags'):
        """Загрузка данных из CSV файла в таблицу PostgreSQL"""
        try:
            # Чтение CSV файла
            console.print(f"[blue]Чтение данных из {csv_file}...[/blue]")
            df = pd.read_csv(csv_file)
            console.print(f"[green]✅ Прочитано {len(df)} строк из CSV[/green]")
            
            # Проверка существования таблицы
            if not self.table_exists(table_name, schema):
                console.print(f"[red]❌ Таблица {schema}.{table_name} не существует![/red]")
                return False
            
            # Очистка таблицы перед загрузкой
            console.print(f"[blue]Очистка таблицы {schema}.{table_name}...[/blue]")
            with self.connection.cursor() as cur:
                cur.execute(f"DELETE FROM {schema}.{table_name}")
                self.connection.commit()
            
            # Загрузка данных
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Загрузка данных в {schema}.{table_name}", total=len(df))
                
                with self.connection.cursor() as cur:
                    for index, row in df.iterrows():
                        # Подготовка данных для вставки
                        values = []
                        placeholders = []
                        
                        for col in df.columns:
                            value = row[col]
                            if pd.isna(value):
                                values.append(None)
                            else:
                                values.append(value)
                            placeholders.append('%s')
                        
                        # SQL запрос для вставки
                        columns = ', '.join(df.columns)
                        placeholders_str = ', '.join(placeholders)
                        sql = f"INSERT INTO {schema}.{table_name} ({columns}) VALUES ({placeholders_str})"
                        
                        cur.execute(sql, values)
                        progress.advance(task)
                
                self.connection.commit()
            
            console.print(f"[green]✅ Загружено {len(df)} строк в {schema}.{table_name}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка загрузки данных:[/red] {e}")
            return False
    
    def table_exists(self, table_name, schema='ags'):
        """Проверка существования таблицы"""
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = %s
                    )
                """, (schema, table_name))
                return cur.fetchone()[0]
        except Exception as e:
            console.print(f"[red]❌ Ошибка проверки существования таблицы:[/red] {e}")
            return False
    
    def get_table_info(self, table_name, schema='ags'):
        """Получение информации о структуре таблицы"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale,
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema, table_name))
                
                columns = cur.fetchall()
                return columns
                
        except Exception as e:
            console.print(f"[red]❌ Ошибка получения информации о таблице:[/red] {e}")
            return None
    
    def verify_data(self, table_name, schema='ags'):
        """Проверка загруженных данных"""
        try:
            with self.connection.cursor() as cur:
                # Подсчет строк
                cur.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
                row_count = cur.fetchone()[0]
                
                console.print(f"[blue]Количество строк в {schema}.{table_name}: {row_count}[/blue]")
                
                if row_count > 0:
                    # Получение первых 5 строк
                    cur.execute(f"SELECT * FROM {schema}.{table_name} ORDER BY account_key LIMIT 5")
                    sample_data = cur.fetchall()
                    
                    console.print(f"[blue]Пример данных из {schema}.{table_name}:[/blue]")
                    
                    table = Table(title=f"Первые 5 строк из {schema}.{table_name}")
                    table.add_column("account_key", style="cyan")
                    table.add_column("account_num", style="yellow")
                    table.add_column("account_name", style="green")
                    
                    for row in sample_data:
                        table.add_row(str(row[0]), str(row[1]), str(row[2]))
                    
                    console.print(table)
                
                return True
                
        except Exception as e:
            console.print(f"[red]❌ Ошибка проверки данных:[/red] {e}")
            return False
    
    def close(self):
        """Закрытие соединения"""
        if self.connection:
            self.connection.close()
            console.print("[blue]Соединение с PostgreSQL закрыто[/blue]")

def main():
    """Основная функция"""
    console.print("[bold blue]FEMCL - Загрузка данных в PostgreSQL[/bold blue]")
    
    # Создание загрузчика
    loader = PostgreSQLLoader()
    
    # Попытка подключения
    if not loader.connect():
        console.print("[red]Не удалось подключиться к PostgreSQL. Завершение работы.[/red]")
        return False
    
    try:
        # Загрузка данных таблицы accnt
        table_name = 'accnt'
        schema = 'ags'
        csv_file = 'data/accnt_data.csv'
        
        console.print(f"\n[bold]Загрузка данных таблицы {schema}.{table_name}[/bold]")
        
        # Проверка существования CSV файла
        if not os.path.exists(csv_file):
            console.print(f"[red]❌ CSV файл {csv_file} не найден![/red]")
            return False
        
        # Проверка существования таблицы
        if not loader.table_exists(table_name, schema):
            console.print(f"[red]❌ Таблица {schema}.{table_name} не существует![/red]")
            return False
        
        # Получение информации о структуре таблицы
        table_info = loader.get_table_info(table_name, schema)
        if table_info:
            console.print(f"[green]✅ Получена информация о структуре таблицы[/green]")
            
            # Отображение структуры
            table = Table(title=f"Структура таблицы {schema}.{table_name}")
            table.add_column("Колонка", style="cyan")
            table.add_column("Тип данных", style="green")
            table.add_column("Длина", style="yellow")
            table.add_column("Nullable", style="magenta")
            
            for col in table_info:
                length = col['character_maximum_length'] if col['character_maximum_length'] else f"{col['numeric_precision']},{col['numeric_scale']}" if col['numeric_precision'] else "N/A"
                table.add_row(
                    col['column_name'],
                    col['data_type'],
                    str(length),
                    col['is_nullable']
                )
            
            console.print(table)
        
        # Загрузка данных
        if loader.load_csv_data(csv_file, table_name, schema):
            console.print(f"[green]✅ Данные успешно загружены в {schema}.{table_name}[/green]")
            
            # Проверка загруженных данных
            loader.verify_data(table_name, schema)
        
        console.print("[green]✅ Загрузка данных завершена успешно![/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка при загрузке данных:[/red] {e}")
        return False
    
    finally:
        loader.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)