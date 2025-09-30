#!/usr/bin/env python3
"""
FEMCL - Извлечение данных из MS SQL Server
Скрипт для извлечения данных из MS SQL Server и подготовки к миграции
"""
import os
import sys
import pyodbc
import pandas as pd
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import json
from datetime import datetime

load_dotenv()
console = Console()

class MSSQLExtractor:
    def __init__(self):
        self.server = os.getenv('MSSQL_SERVER', 'localhost')
        self.port = os.getenv('MSSQL_PORT', '1433')
        self.database = os.getenv('MSSQL_DB', 'Fish_Eye')
        self.user = os.getenv('MSSQL_USER', 'sa')
        self.password = os.getenv('MSSQL_PASSWORD', 'kolob_OK1')
        self.connection = None
        
    def connect(self):
        """Подключение к MS SQL Server"""
        try:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.server},{self.port};"
                f"DATABASE={self.database};"
                f"UID={self.user};"
                f"PWD={self.password};"
                "TrustServerCertificate=yes;"
            )
            
            console.print(f"[blue]Подключение к MS SQL Server...[/blue]")
            console.print(f"Server: {self.server}:{self.port}")
            console.print(f"Database: {self.database}")
            console.print(f"User: {self.user}")
            
            self.connection = pyodbc.connect(conn_str)
            console.print("[green]✅ Подключение успешно![/green]")
            return True
            
        except pyodbc.Error as e:
            console.print(f"[red]❌ Ошибка подключения к MS SQL Server:[/red] {e}")
            return False
        except Exception as e:
            console.print(f"[red]❌ Неожиданная ошибка:[/red] {e}")
            return False
    
    def extract_table_data(self, table_name, schema='ags'):
        """Извлечение данных из указанной таблицы"""
        try:
            query = f"SELECT * FROM [{schema}].[{table_name}]"
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Извлечение данных из {schema}.{table_name}", total=None)
                
                df = pd.read_sql(query, self.connection)
                
            console.print(f"[green]✅ Извлечено {len(df)} строк из {schema}.{table_name}[/green]")
            return df
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка извлечения данных из {schema}.{table_name}:[/red] {e}")
            return None
    
    def get_table_info(self, table_name, schema='ags'):
        """Получение информации о структуре таблицы"""
        try:
            query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = '{schema}' 
            AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
            """
            
            df = pd.read_sql(query, self.connection)
            return df
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка получения информации о таблице {schema}.{table_name}:[/red] {e}")
            return None
    
    def save_data_to_csv(self, df, table_name, output_dir='data'):
        """Сохранение данных в CSV файл"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            filename = f"{output_dir}/{table_name}_data.csv"
            df.to_csv(filename, index=False, encoding='utf-8')
            console.print(f"[green]✅ Данные сохранены в {filename}[/green]")
            return filename
        except Exception as e:
            console.print(f"[red]❌ Ошибка сохранения данных:[/red] {e}")
            return None
    
    def save_metadata(self, table_name, table_info, output_dir='data'):
        """Сохранение метаданных таблицы"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            metadata = {
                'table_name': table_name,
                'extraction_time': datetime.now().isoformat(),
                'columns': table_info.to_dict('records')
            }
            
            filename = f"{output_dir}/{table_name}_metadata.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            console.print(f"[green]✅ Метаданные сохранены в {filename}[/green]")
            return filename
        except Exception as e:
            console.print(f"[red]❌ Ошибка сохранения метаданных:[/red] {e}")
            return None
    
    def close(self):
        """Закрытие соединения"""
        if self.connection:
            self.connection.close()
            console.print("[blue]Соединение с MS SQL Server закрыто[/blue]")

def main():
    """Основная функция"""
    console.print("[bold blue]FEMCL - Извлечение данных из MS SQL Server[/bold blue]")
    
    # Создание экстрактора
    extractor = MSSQLExtractor()
    
    # Попытка подключения
    if not extractor.connect():
        console.print("[red]Не удалось подключиться к MS SQL Server. Завершение работы.[/red]")
        return False
    
    try:
        # Извлечение данных таблицы accnt
        table_name = 'accnt'
        schema = 'ags'
        
        console.print(f"\n[bold]Извлечение данных таблицы {schema}.{table_name}[/bold]")
        
        # Получение информации о структуре
        table_info = extractor.get_table_info(table_name, schema)
        if table_info is not None:
            console.print(f"[green]✅ Получена информация о структуре таблицы[/green]")
            
            # Отображение структуры
            table = Table(title=f"Структура таблицы {schema}.{table_name}")
            table.add_column("Колонка", style="cyan")
            table.add_column("Тип данных", style="green")
            table.add_column("Длина", style="yellow")
            table.add_column("Nullable", style="magenta")
            
            for _, row in table_info.iterrows():
                table.add_row(
                    row['COLUMN_NAME'],
                    row['DATA_TYPE'],
                    str(row['CHARACTER_MAXIMUM_LENGTH']) if row['CHARACTER_MAXIMUM_LENGTH'] else '',
                    row['IS_NULLABLE']
                )
            
            console.print(table)
            
            # Сохранение метаданных
            extractor.save_metadata(table_name, table_info)
        
        # Извлечение данных
        data = extractor.extract_table_data(table_name, schema)
        if data is not None:
            console.print(f"[green]✅ Извлечено {len(data)} строк данных[/green]")
            
            # Отображение первых строк
            if len(data) > 0:
                console.print(f"\n[bold]Первые 5 строк данных:[/bold]")
                console.print(data.head().to_string())
            
            # Сохранение данных
            extractor.save_data_to_csv(data, table_name)
        
        console.print("[green]✅ Извлечение данных завершено успешно![/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка при извлечении данных:[/red] {e}")
        return False
    
    finally:
        extractor.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)