#!/usr/bin/env python3
"""
FEMCL - Универсальный скрипт для миграции отдельных таблиц
Версия: 1.0
Автор: FEMCL Team
Дата: 2025-01-27

Описание:
    Универсальный скрипт для миграции отдельных таблиц из MS SQL Server в PostgreSQL
    с использованием метаданных системы FEMCL.

Использование:
    python scripts/migrate_single_table.py <table_name> [--force] [--validate-only]
    
Примеры:
    python scripts/migrate_single_table.py accnt
    python scripts/migrate_single_table.py cn --force
    python scripts/migrate_single_table.py users --validate-only
"""

import os
import sys
import argparse
import pyodbc
import psycopg2
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config_loader import ConfigLoader

load_dotenv()
console = Console()

class UniversalTableMigrator:
    """
    Универсальный класс для миграции отдельных таблиц
    """
    
    def __init__(self, config):
        self.config = config
        self.mssql_conn_str = self._get_mssql_conn_str()
        self.pg_conn_str = self._get_pg_conn_str()
        self.migration_log = []
        
    def _get_mssql_conn_str(self):
        """Получение строки подключения к MS SQL Server"""
        db_config = self.config.get_database_config('mssql')
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={db_config['server']},{db_config['port']};"
            f"DATABASE={db_config['database']};"
            f"UID={db_config['user']};"
            f"PWD={db_config['password']}"
        )
    
    def _get_pg_conn_str(self):
        """Получение строки подключения к PostgreSQL"""
        db_config = self.config.get_database_config('postgres')
        return (
            f"host={db_config['host']} port={db_config['port']} "
            f"dbname={db_config['database']} user={db_config['user']} "
            f"password={db_config['password']}"
        )
    
    def _execute_pg_query(self, query, params=None, fetch_one=False, commit=False):
        """Выполнение запроса к PostgreSQL"""
        with psycopg2.connect(self.pg_conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                if fetch_one:
                    return cursor.fetchone()
                return cursor.fetchall()
    
    def _execute_mssql_query(self, query, params=None, fetch_one=False):
        """Выполнение запроса к MS SQL Server"""
        with pyodbc.connect(self.mssql_conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch_one:
                    return cursor.fetchone()
                return cursor.fetchall()
    
    def log_action(self, action, status, details=""):
        """Логирование действий"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'action': action,
            'status': status,
            'details': details
        }
        self.migration_log.append(log_entry)
        rprint(f"[{timestamp}] {action}: {status} - {details}")
    
    def check_table_readiness(self, table_name):
        """Проверка готовности таблицы к миграции"""
        try:
            # Проверяем существование таблицы в MS SQL
            db_config = self.config.get_database_config('mssql')
            query = f"""
            SELECT COUNT(*) 
            FROM {db_config['database']}.information_schema.tables 
            WHERE table_schema = 'ags' AND table_name = '{table_name}'
            """
            exists = self._execute_mssql_query(query, fetch_one=True)[0]
            
            if not exists:
                self.log_action("Проверка готовности", "FAILED", f"Таблица {table_name} не найдена в MS SQL Server")
                return False
            
            # Проверяем метаданные в PostgreSQL
            metadata_query = f"""
            SELECT 
                pt.object_name,
                pt.migration_status,
                pt.base_table_created,
                pt.has_computed_columns
            FROM mcl.postgres_tables pt
            WHERE pt.object_name = '{table_name}'
            """
            metadata = self._execute_pg_query(metadata_query, fetch_one=True)
            
            if not metadata:
                self.log_action("Проверка готовности", "FAILED", f"Метаданные для таблицы {table_name} не найдены")
                return False
            
            self.log_action("Проверка готовности", "SUCCESS", f"Таблица {table_name} готова к миграции")
            return True
            
        except Exception as e:
            self.log_action("Проверка готовности", "ERROR", str(e))
            return False
    
    def get_table_metadata(self, table_name):
        """Получение метаданных таблицы из системы FEMCL"""
        try:
            query = f"""
            SELECT 
                pc.column_name,
                pc.ordinal_position,
                pc.is_identity,
                pc.default_value,
                pdt.typname_with_params as postgres_type,
                mc.column_name as source_column_name
            FROM mcl.postgres_tables pt
            JOIN mcl.postgres_columns pc ON pt.id = pc.table_id
            JOIN mcl.postgres_derived_types pdt ON pc.postgres_data_type_id = pdt.id
            LEFT JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
            WHERE pt.object_name = '{table_name}'
            ORDER BY pc.ordinal_position
            """
            
            metadata = self._execute_pg_query(query)
            
            if not metadata:
                self.log_action("Получение метаданных", "FAILED", f"Метаданные для таблицы {table_name} не найдены")
                return None
            
            self.log_action("Получение метаданных", "SUCCESS", f"Получено {len(metadata)} колонок")
            return metadata
            
        except Exception as e:
            self.log_action("Получение метаданных", "ERROR", str(e))
            return None
    
    def generate_table_ddl(self, table_name, metadata):
        """Генерация DDL для создания таблицы"""
        try:
            ddl_parts = []
            pk_columns = []
            
            for col in metadata:
                col_name = col[0]  # pc.column_name
                col_type = col[4]  # postgres_type
                is_identity = col[2]  # is_identity
                default_value = col[3]  # default_value
                
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
            
            self.log_action("Генерация DDL", "SUCCESS", f"DDL для таблицы {table_name} сгенерирован")
            return ddl
            
        except Exception as e:
            self.log_action("Генерация DDL", "ERROR", str(e))
            return None
    
    def create_target_table(self, table_name, ddl, force=False):
        """Создание целевой таблицы в PostgreSQL"""
        try:
            # Проверяем существование таблицы
            exists_query = f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'ags' AND table_name = '{table_name}'
            )
            """
            table_exists = self._execute_pg_query(exists_query, fetch_one=True)[0]
            
            if table_exists:
                if force:
                    # Удаляем существующую таблицу
                    drop_query = f"DROP TABLE IF EXISTS ags.{table_name} CASCADE;"
                    self._execute_pg_query(drop_query, commit=True)
                    self.log_action("Удаление таблицы", "SUCCESS", f"Таблица {table_name} удалена")
                else:
                    self.log_action("Создание таблицы", "SKIPPED", f"Таблица {table_name} уже существует")
                    return True
            
            # Создаем таблицу
            self._execute_pg_query(ddl, commit=True)
            self.log_action("Создание таблицы", "SUCCESS", f"Таблица {table_name} создана")
            return True
            
        except Exception as e:
            self.log_action("Создание таблицы", "ERROR", str(e))
            return False
    
    def migrate_data(self, table_name, metadata):
        """Перенос данных из MS SQL в PostgreSQL"""
        try:
            # Получаем имена колонок для SELECT и INSERT
            source_columns = [col[5] for col in metadata if col[5]]  # source_column_name
            target_columns = [col[0] for col in metadata]  # column_name
            
            if not source_columns:
                self.log_action("Перенос данных", "FAILED", "Не найдены исходные имена колонок")
                return False
            
            # Формируем запросы
            select_query = f"SELECT {', '.join(source_columns)} FROM ags.{table_name}"
            insert_query = f"INSERT INTO ags.{table_name} ({', '.join(target_columns)}) VALUES ({', '.join(['%s'] * len(target_columns))})"
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task("Перенос данных...", total=None)
                
                with pyodbc.connect(self.mssql_conn_str) as mssql_conn:
                    mssql_cursor = mssql_conn.cursor()
                    mssql_cursor.execute(select_query)
                    
                    with psycopg2.connect(self.pg_conn_str) as pg_conn:
                        pg_cursor = pg_conn.cursor()
                        
                        # Отключаем триггеры для быстрой вставки
                        pg_cursor.execute(f"ALTER TABLE ags.{table_name} DISABLE TRIGGER ALL;")
                        
                        row_count = 0
                        for row in mssql_cursor.fetchall():
                            pg_cursor.execute(insert_query, row)
                            row_count += 1
                            
                            if row_count % 1000 == 0:
                                progress.update(task, description=f"Перенесено {row_count} строк...")
                        
                        pg_conn.commit()
                        pg_cursor.execute(f"ALTER TABLE ags.{table_name} ENABLE TRIGGER ALL;")
                        pg_conn.commit()
                        
                        progress.update(task, description=f"Перенесено {row_count} строк")
            
            self.log_action("Перенос данных", "SUCCESS", f"Перенесено {row_count} строк")
            return True
            
        except Exception as e:
            self.log_action("Перенос данных", "ERROR", str(e))
            return False
    
    def validate_migration(self, table_name):
        """Валидация миграции"""
        try:
            # Сравниваем количество строк
            mssql_count_query = f"SELECT COUNT(*) FROM ags.{table_name}"
            mssql_count = self._execute_mssql_query(mssql_count_query, fetch_one=True)[0]
            
            pg_count_query = f"SELECT COUNT(*) FROM ags.{table_name}"
            pg_count = self._execute_pg_query(pg_count_query, fetch_one=True)[0]
            
            if mssql_count != pg_count:
                self.log_action("Валидация", "FAILED", f"Несоответствие количества строк: MS SQL={mssql_count}, PG={pg_count}")
                return False
            
            self.log_action("Валидация", "SUCCESS", f"Количество строк совпадает: {pg_count}")
            return True
            
        except Exception as e:
            self.log_action("Валидация", "ERROR", str(e))
            return False
    
    def update_migration_status(self, table_name, status):
        """Обновление статуса миграции"""
        try:
            # Обновляем статус в mcl.migration_status
            update_query = f"""
            UPDATE mcl.migration_status 
            SET current_status = '{status}', updated_at = NOW()
            WHERE table_name = '{table_name}'
            """
            self._execute_pg_query(update_query, commit=True)
            
            # Обновляем статус в mcl.postgres_tables
            update_pt_query = f"""
            UPDATE mcl.postgres_tables 
            SET migration_status = '{status}', updated_at = NOW()
            WHERE object_name = '{table_name}'
            """
            self._execute_pg_query(update_pt_query, commit=True)
            
            self.log_action("Обновление статуса", "SUCCESS", f"Статус таблицы {table_name} обновлен на '{status}'")
            return True
            
        except Exception as e:
            self.log_action("Обновление статуса", "ERROR", str(e))
            return False
    
    def migrate_table(self, table_name, force=False, validate_only=False):
        """Основной метод миграции таблицы"""
        rprint(Panel(f"[bold blue]🚀 FEMCL - Миграция таблицы {table_name}[/bold blue]", expand=False))
        
        start_time = datetime.now()
        
        try:
            # 1. Проверка готовности
            if not self.check_table_readiness(table_name):
                return False
            
            if validate_only:
                self.log_action("Валидация", "INFO", "Режим только валидации")
                return self.validate_migration(table_name)
            
            # 2. Получение метаданных
            metadata = self.get_table_metadata(table_name)
            if not metadata:
                return False
            
            # 3. Генерация DDL
            ddl = self.generate_table_ddl(table_name, metadata)
            if not ddl:
                return False
            
            # 4. Создание таблицы
            if not self.create_target_table(table_name, ddl, force):
                return False
            
            # 5. Перенос данных
            if not self.migrate_data(table_name, metadata):
                return False
            
            # 6. Валидация
            if not self.validate_migration(table_name):
                return False
            
            # 7. Обновление статуса
            self.update_migration_status(table_name, "completed")
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.log_action("Миграция", "SUCCESS", f"Таблица {table_name} успешно мигрирована за {duration}")
            return True
            
        except Exception as e:
            self.log_action("Миграция", "ERROR", str(e))
            self.update_migration_status(table_name, "failed")
            return False
    
    def print_summary(self):
        """Вывод сводки миграции"""
        rprint("\n" + "="*60)
        rprint("[bold blue]📊 СВОДКА МИГРАЦИИ[/bold blue]")
        rprint("="*60)
        
        for log_entry in self.migration_log:
            status_color = {
                "SUCCESS": "green",
                "FAILED": "red", 
                "ERROR": "red",
                "SKIPPED": "yellow",
                "INFO": "blue"
            }.get(log_entry['status'], "white")
            
            rprint(f"[{status_color}]{log_entry['timestamp']} {log_entry['action']}: {log_entry['status']}[/{status_color}]")
            if log_entry['details']:
                rprint(f"    {log_entry['details']}")

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='FEMCL - Универсальный скрипт для миграции отдельных таблиц')
    parser.add_argument('table_name', help='Имя таблицы для миграции')
    parser.add_argument('--force', action='store_true', help='Принудительное пересоздание таблицы')
    parser.add_argument('--validate-only', action='store_true', help='Только валидация без миграции')
    
    args = parser.parse_args()
    
    # Загрузка конфигурации
    config_loader = ConfigLoader()
    config = config_loader.load_config()
    
    # Создание мигратора
    migrator = UniversalTableMigrator(config_loader)
    
    # Выполнение миграции
    success = migrator.migrate_table(
        table_name=args.table_name,
        force=args.force,
        validate_only=args.validate_only
    )
    
    # Вывод сводки
    migrator.print_summary()
    
    if success:
        rprint("[bold green]✅ Миграция завершена успешно![/bold green]")
        sys.exit(0)
    else:
        rprint("[bold red]❌ Миграция завершена с ошибками![/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()