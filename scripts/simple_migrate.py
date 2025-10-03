#!/usr/bin/env python3
"""
FEMCL - Простой скрипт для миграции отдельных таблиц
Версия: 1.0
Автор: FEMCL Team
Дата: 2025-01-27

Описание:
    Простой и надежный скрипт для миграции отдельных таблиц
    с использованием метаданных системы FEMCL.

Использование:
    python scripts/simple_migrate.py <table_name> [--force]
    
Примеры:
    python scripts/simple_migrate.py accnt
    python scripts/simple_migrate.py cn --force
"""

import os
import sys
import argparse
import pyodbc
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config_loader import ConfigLoader

load_dotenv()
console = Console()

class SimpleTableMigrator:
    """Простой класс для миграции отдельных таблиц"""
    
    def __init__(self, config_loader):
        self.config_loader = config_loader
        self.mssql_config = config_loader.get_database_config('mssql')
        self.pg_config = config_loader.get_database_config('postgres')
        
    def get_mssql_connection(self):
        """Получение подключения к MS SQL Server"""
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.mssql_config['server']},{self.mssql_config['port']};"
            f"DATABASE={self.mssql_config['database']};"
            f"UID={self.mssql_config['user']};"
            f"PWD={self.mssql_config['password']}"
        )
        return pyodbc.connect(conn_str)
    
    def get_pg_connection(self):
        """Получение подключения к PostgreSQL"""
        conn_str = (
            f"host={self.pg_config['host']} port={self.pg_config['port']} "
            f"dbname={self.pg_config['database']} user={self.pg_config['user']} "
            f"password={self.pg_config['password']}"
        )
        return psycopg2.connect(conn_str)
    
    def check_table_exists_mssql(self, table_name):
        """Проверка существования таблицы в MS SQL Server"""
        try:
            with self.get_mssql_connection() as conn:
                cursor = conn.cursor()
                query = f"""
                SELECT COUNT(*) 
                FROM {self.mssql_config['database']}.information_schema.tables 
                WHERE table_schema = 'ags' AND table_name = '{table_name}'
                """
                cursor.execute(query)
                return cursor.fetchone()[0] > 0
        except Exception as e:
            rprint(f"[red]❌ Ошибка проверки таблицы в MS SQL: {e}[/red]")
            return False
    
    def get_table_metadata(self, table_name):
        """Получение метаданных таблицы из системы FEMCL"""
        try:
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                query = f"""
                SELECT 
                    pc.column_name,
                    pc.ordinal_position,
                    pc.is_identity,
                    pdt.typname_with_params as postgres_type,
                    mc.column_name as source_column_name
                FROM mcl.postgres_tables pt
                JOIN mcl.postgres_columns pc ON pt.id = pc.table_id
                JOIN mcl.postgres_derived_types pdt ON pc.postgres_data_type_id = pdt.id
                LEFT JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
                WHERE pt.object_name = '{table_name}'
                ORDER BY pc.ordinal_position
                """
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            rprint(f"[red]❌ Ошибка получения метаданных: {e}[/red]")
            return None
    
    def generate_ddl(self, table_name, metadata):
        """Генерация DDL для создания таблицы"""
        try:
            ddl_parts = []
            pk_columns = []
            
            for col in metadata:
                col_name = col[0]  # pc.column_name
                col_type = col[3]  # postgres_type
                is_identity = col[2]  # is_identity
                default_value = None  # default_value не доступен
                
                # Формируем определение колонки
                col_def = f"    {col_name} {col_type}"
                
                if is_identity:
                    col_def += " GENERATED ALWAYS AS IDENTITY"
                    pk_columns.append(col_name)
                
                if default_value:
                    col_def += f" DEFAULT {default_value}"
                
                ddl_parts.append(col_def)
            
            # Создаем DDL
            ddl = f"CREATE TABLE ags.{table_name} (\n" + ",\n".join(ddl_parts) + "\n);"
            
            # Добавляем первичный ключ если есть identity колонки
            if pk_columns:
                pk_ddl = f"ALTER TABLE ags.{table_name} ADD CONSTRAINT pk_{table_name} PRIMARY KEY ({', '.join(pk_columns)});"
                ddl += "\n" + pk_ddl
            
            return ddl
            
        except Exception as e:
            rprint(f"[red]❌ Ошибка генерации DDL: {e}[/red]")
            return None
    
    def table_exists_pg(self, table_name):
        """Проверка существования таблицы в PostgreSQL"""
        try:
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                query = f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'ags' AND table_name = '{table_name}'
                )
                """
                cursor.execute(query)
                return cursor.fetchone()[0]
        except Exception as e:
            rprint(f"[red]❌ Ошибка проверки таблицы в PostgreSQL: {e}[/red]")
            return False
    
    def create_table(self, table_name, ddl, force=False):
        """Создание таблицы в PostgreSQL"""
        try:
            if self.table_exists_pg(table_name):
                if force:
                    # Удаляем существующую таблицу
                    with self.get_pg_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(f"DROP TABLE IF EXISTS ags.{table_name} CASCADE;")
                        conn.commit()
                    rprint(f"[yellow]⚠️ Таблица {table_name} удалена[/yellow]")
                else:
                    rprint(f"[yellow]⚠️ Таблица {table_name} уже существует[/yellow]")
                    return True
            
            # Создаем таблицу
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(ddl)
                conn.commit()
            
            rprint(f"[green]✅ Таблица {table_name} создана[/green]")
            return True
            
        except Exception as e:
            rprint(f"[red]❌ Ошибка создания таблицы: {e}[/red]")
            return False
    
    def migrate_data(self, table_name, metadata):
        """Перенос данных из MS SQL в PostgreSQL"""
        try:
            # Получаем имена колонок для SELECT и INSERT
            source_columns = [col[4] for col in metadata if col[4]]  # source_column_name
            target_columns = [col[0] for col in metadata]  # column_name
            
            if not source_columns:
                rprint(f"[red]❌ Не найдены исходные имена колонок для таблицы {table_name}[/red]")
                return False
            
            # Формируем запросы
            select_query = f"SELECT {', '.join(source_columns)} FROM ags.{table_name}"
            insert_query = f"INSERT INTO ags.{table_name} ({', '.join(target_columns)}) OVERRIDING SYSTEM VALUE VALUES ({', '.join(['%s'] * len(target_columns))})"
            
            rprint(f"[blue]📦 Перенос данных из MS SQL в PostgreSQL...[/blue]")
            
            with self.get_mssql_connection() as mssql_conn:
                mssql_cursor = mssql_conn.cursor()
                mssql_cursor.execute(select_query)
                
                with self.get_pg_connection() as pg_conn:
                    pg_cursor = pg_conn.cursor()
                    
                    # Отключаем триггеры для быстрой вставки
                    pg_cursor.execute(f"ALTER TABLE ags.{table_name} DISABLE TRIGGER ALL;")
                    
                    row_count = 0
                    for row in mssql_cursor.fetchall():
                        pg_cursor.execute(insert_query, row)
                        row_count += 1
                        
                        if row_count % 1000 == 0:
                            rprint(f"[blue]📊 Перенесено {row_count} строк...[/blue]")
                    
                    pg_conn.commit()
                    pg_cursor.execute(f"ALTER TABLE ags.{table_name} ENABLE TRIGGER ALL;")
                    pg_conn.commit()
                    
                    rprint(f"[green]✅ Перенесено {row_count} строк[/green]")
            
            return True
            
        except Exception as e:
            rprint(f"[red]❌ Ошибка переноса данных: {e}[/red]")
            return False
    
    def validate_migration(self, table_name):
        """Валидация миграции"""
        try:
            # Сравниваем количество строк
            with self.get_mssql_connection() as mssql_conn:
                mssql_cursor = mssql_conn.cursor()
                mssql_cursor.execute(f"SELECT COUNT(*) FROM ags.{table_name}")
                mssql_count = mssql_cursor.fetchone()[0]
            
            with self.get_pg_connection() as pg_conn:
                pg_cursor = pg_conn.cursor()
                pg_cursor.execute(f"SELECT COUNT(*) FROM ags.{table_name}")
                pg_count = pg_cursor.fetchone()[0]
            
            if mssql_count != pg_count:
                rprint(f"[red]❌ Несоответствие количества строк: MS SQL={mssql_count}, PG={pg_count}[/red]")
                return False
            
            rprint(f"[green]✅ Количество строк совпадает: {pg_count}[/green]")
            return True
            
        except Exception as e:
            rprint(f"[red]❌ Ошибка валидации: {e}[/red]")
            return False
    
    def update_status(self, table_name, status):
        """Обновление статуса миграции"""
        try:
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                
                # Обновляем статус в mcl.migration_status
                cursor.execute(f"""
                    UPDATE mcl.migration_status 
                    SET current_status = '{status}', updated_at = NOW()
                    WHERE table_name = '{table_name}'
                """)
                
                # Обновляем статус в mcl.postgres_tables
                cursor.execute(f"""
                    UPDATE mcl.postgres_tables 
                    SET migration_status = '{status}', updated_at = NOW()
                    WHERE object_name = '{table_name}'
                """)
                
                conn.commit()
                rprint(f"[green]✅ Статус таблицы {table_name} обновлен на '{status}'[/green]")
                return True
                
        except Exception as e:
            rprint(f"[red]❌ Ошибка обновления статуса: {e}[/red]")
            return False
    
    def migrate_table(self, table_name, force=False):
        """Основной метод миграции таблицы"""
        rprint(Panel(f"[bold blue]🚀 FEMCL - Миграция таблицы {table_name}[/bold blue]", expand=False))
        
        start_time = datetime.now()
        
        try:
            # 1. Проверка существования таблицы в MS SQL
            if not self.check_table_exists_mssql(table_name):
                rprint(f"[red]❌ Таблица {table_name} не найдена в MS SQL Server[/red]")
                return False
            
            # 2. Получение метаданных
            metadata = self.get_table_metadata(table_name)
            if not metadata:
                rprint(f"[red]❌ Метаданные для таблицы {table_name} не найдены[/red]")
                return False
            
            rprint(f"[green]✅ Получено {len(metadata)} колонок из метаданных[/green]")
            
            # 3. Генерация DDL
            ddl = self.generate_ddl(table_name, metadata)
            if not ddl:
                return False
            
            # 4. Создание таблицы
            if not self.create_table(table_name, ddl, force):
                return False
            
            # 5. Перенос данных
            if not self.migrate_data(table_name, metadata):
                return False
            
            # 6. Валидация
            if not self.validate_migration(table_name):
                return False
            
            # 7. Обновление статуса
            self.update_status(table_name, "completed")
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            rprint(f"[green]✅ Таблица {table_name} успешно мигрирована за {duration}[/green]")
            return True
            
        except Exception as e:
            rprint(f"[red]❌ Ошибка миграции: {e}[/red]")
            self.update_status(table_name, "failed")
            return False

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='FEMCL - Простой скрипт для миграции отдельных таблиц')
    parser.add_argument('table_name', help='Имя таблицы для миграции')
    parser.add_argument('--force', action='store_true', help='Принудительное пересоздание таблицы')
    
    args = parser.parse_args()
    
    # Загрузка конфигурации
    config_loader = ConfigLoader()
    
    # Создание мигратора
    migrator = SimpleTableMigrator(config_loader)
    
    # Выполнение миграции
    success = migrator.migrate_table(
        table_name=args.table_name,
        force=args.force
    )
    
    if success:
        rprint("[bold green]✅ Миграция завершена успешно![/bold green]")
        sys.exit(0)
    else:
        rprint("[bold red]❌ Миграция завершена с ошибками![/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()