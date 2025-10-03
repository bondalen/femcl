#!/usr/bin/env python3
"""
FEMCL - Полный скрипт для миграции отдельных таблиц
Версия: 1.0
Автор: FEMCL Team
Дата: 2025-01-27

Описание:
    Полный скрипт для миграции отдельных таблиц со всеми элементами:
    - Колонки
    - Первичные ключи
    - Индексы
    - Внешние ключи
    - Уникальные ограничения
    - Check ограничения
    - Триггеры

Использование:
    python scripts/complete_migrate.py <table_name> [--force]
    
Примеры:
    python scripts/complete_migrate.py accnt
    python scripts/complete_migrate.py cn --force
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

class CompleteTableMigrator:
    """Полный класс для миграции отдельных таблиц со всеми элементами"""
    
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
    
    def get_indexes_metadata(self, table_name):
        """Получение метаданных индексов"""
        try:
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                # Получаем индексы через связь с исходными индексами
                query = f"""
                SELECT 
                    pi.index_name,
                    pi.index_type,
                    pi.is_unique,
                    pi.is_primary_key,
                    pi.postgres_definition,
                    pic.column_name,
                    pic.ordinal_position
                FROM mcl.postgres_indexes pi
                LEFT JOIN mcl.postgres_index_columns pic ON pi.id = pic.index_id
                WHERE pi.source_index_id IN (
                    SELECT mi.id FROM mcl.mssql_indexes mi
                    JOIN mcl.mssql_tables mt ON mi.table_id = mt.id
                    WHERE mt.object_name = '{table_name}'
                )
                ORDER BY pi.index_name, pic.ordinal_position
                """
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            rprint(f"[red]❌ Ошибка получения метаданных индексов: {e}[/red]")
            return []
    
    def get_foreign_keys_metadata(self, table_name):
        """Получение метаданных внешних ключей"""
        try:
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                query = f"""
                SELECT 
                    pfk.constraint_name,
                    pfk.delete_action,
                    pfk.update_action,
                    pt2.object_name as referenced_table,
                    pfkc.column_name,
                    pfkc.referenced_column_name,
                    pfkc.ordinal_position
                FROM mcl.postgres_foreign_keys pfk
                JOIN mcl.postgres_tables pt ON pfk.table_id = pt.id
                LEFT JOIN mcl.postgres_tables pt2 ON pfk.referenced_table_id = pt2.id
                LEFT JOIN mcl.postgres_foreign_key_columns pfkc ON pfk.id = pfkc.foreign_key_id
                WHERE pt.object_name = '{table_name}'
                ORDER BY pfk.constraint_name, pfkc.ordinal_position
                """
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            rprint(f"[red]❌ Ошибка получения метаданных внешних ключей: {e}[/red]")
            return []
    
    def get_unique_constraints_metadata(self, table_name):
        """Получение метаданных уникальных ограничений"""
        try:
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                query = f"""
                SELECT 
                    puc.constraint_name,
                    pucc.column_name,
                    pucc.ordinal_position
                FROM mcl.postgres_unique_constraints puc
                LEFT JOIN mcl.postgres_unique_constraint_columns pucc ON puc.id = pucc.constraint_id
                WHERE puc.source_unique_constraint_id IN (
                    SELECT muc.id FROM mcl.mssql_unique_constraints muc
                    JOIN mcl.mssql_tables mt ON muc.table_id = mt.id
                    WHERE mt.object_name = '{table_name}'
                )
                ORDER BY puc.constraint_name, pucc.ordinal_position
                """
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            rprint(f"[red]❌ Ошибка получения метаданных уникальных ограничений: {e}[/red]")
            return []
    
    def get_check_constraints_metadata(self, table_name):
        """Получение метаданных check ограничений"""
        try:
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                query = f"""
                SELECT 
                    pcc.constraint_name,
                    pcc.check_clause,
                    pccc.column_name
                FROM mcl.postgres_check_constraints pcc
                LEFT JOIN mcl.postgres_check_constraint_columns pccc ON pcc.id = pccc.constraint_id
                WHERE pcc.source_check_constraint_id IN (
                    SELECT mcc.id FROM mcl.mssql_check_constraints mcc
                    JOIN mcl.mssql_tables mt ON mcc.table_id = mt.id
                    WHERE mt.object_name = '{table_name}'
                )
                ORDER BY pcc.constraint_name
                """
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            rprint(f"[red]❌ Ошибка получения метаданных check ограничений: {e}[/red]")
            return []
    
    def get_triggers_metadata(self, table_name):
        """Получение метаданных триггеров"""
        try:
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                query = f"""
                SELECT 
                    ptr.trigger_name,
                    ptr.trigger_event,
                    ptr.trigger_timing,
                    ptr.trigger_definition
                FROM mcl.postgres_triggers ptr
                JOIN mcl.postgres_tables pt ON ptr.table_id = pt.id
                WHERE pt.object_name = '{table_name}'
                ORDER BY ptr.trigger_name
                """
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            rprint(f"[red]❌ Ошибка получения метаданных триггеров: {e}[/red]")
            return []
    
    def generate_complete_ddl(self, table_name, metadata):
        """Генерация полного DDL для создания таблицы"""
        try:
            ddl_parts = []
            pk_columns = []
            
            # 1. Колонки
            for col in metadata:
                col_name = col[0]  # pc.column_name
                col_type = col[3]  # postgres_type
                is_identity = col[2]  # is_identity
                
                # Формируем определение колонки
                col_def = f"    {col_name} {col_type}"
                
                if is_identity:
                    col_def += " GENERATED ALWAYS AS IDENTITY"
                    pk_columns.append(col_name)
                
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
    
    def create_indexes(self, table_name, indexes_metadata):
        """Создание индексов"""
        try:
            if not indexes_metadata:
                rprint(f"[yellow]⚠️ Нет индексов для таблицы {table_name}[/yellow]")
                return True
            
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                
                # Группируем индексы по имени
                indexes = {}
                for idx in indexes_metadata:
                    idx_name = idx[0]
                    if idx_name not in indexes:
                        indexes[idx_name] = {
                            'type': idx[1],
                            'unique': idx[2],
                            'primary': idx[3],
                            'definition': idx[4],
                            'columns': []
                        }
                    if idx[5]:  # column_name
                        indexes[idx_name]['columns'].append((idx[5], idx[6]))  # (column, position)
                
                for idx_name, idx_info in indexes.items():
                    if idx_info['primary']:
                        rprint(f"[blue]📇 Пропускаем первичный ключ {idx_name}[/blue]")
                        continue
                    
                    if idx_info['definition']:
                        # Используем готовое определение
                        cursor.execute(idx_info['definition'])
                        rprint(f"[green]✅ Создан индекс {idx_name} (из определения)[/green]")
                    else:
                        # Создаем индекс из колонок
                        columns = [col[0] for col in sorted(idx_info['columns'], key=lambda x: x[1])]
                        unique_str = "UNIQUE " if idx_info['unique'] else ""
                        idx_ddl = f"CREATE {unique_str}INDEX {idx_name} ON ags.{table_name} ({', '.join(columns)});"
                        cursor.execute(idx_ddl)
                        rprint(f"[green]✅ Создан индекс {idx_name}[/green]")
                
                conn.commit()
                return True
                
        except Exception as e:
            rprint(f"[red]❌ Ошибка создания индексов: {e}[/red]")
            return False
    
    def create_foreign_keys(self, table_name, fks_metadata):
        """Создание внешних ключей"""
        try:
            if not fks_metadata:
                rprint(f"[yellow]⚠️ Нет внешних ключей для таблицы {table_name}[/yellow]")
                return True
            
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                
                # Группируем внешние ключи по имени
                fks = {}
                for fk in fks_metadata:
                    fk_name = fk[0]
                    if fk_name not in fks:
                        fks[fk_name] = {
                            'delete_action': fk[1],
                            'update_action': fk[2],
                            'referenced_table': fk[3],
                            'columns': []
                        }
                    if fk[4]:  # column_name
                        fks[fk_name]['columns'].append((fk[4], fk[5], fk[6]))  # (column, ref_column, position)
                
                for fk_name, fk_info in fks.items():
                    if not fk_info['columns']:
                        continue
                    
                    # Формируем колонки
                    columns = [col[0] for col in sorted(fk_info['columns'], key=lambda x: x[2])]
                    ref_columns = [col[1] for col in sorted(fk_info['columns'], key=lambda x: x[2])]
                    
                    # Формируем действия
                    delete_action = f"ON DELETE {fk_info['delete_action']}" if fk_info['delete_action'] else ""
                    update_action = f"ON UPDATE {fk_info['update_action']}" if fk_info['update_action'] else ""
                    
                    fk_ddl = f"""
                    ALTER TABLE ags.{table_name} 
                    ADD CONSTRAINT {fk_name} 
                    FOREIGN KEY ({', '.join(columns)}) 
                    REFERENCES ags.{fk_info['referenced_table']} ({', '.join(ref_columns)})
                    {delete_action} {update_action};
                    """
                    
                    cursor.execute(fk_ddl)
                    rprint(f"[green]✅ Создан внешний ключ {fk_name}[/green]")
                
                conn.commit()
                return True
                
        except Exception as e:
            rprint(f"[red]❌ Ошибка создания внешних ключей: {e}[/red]")
            return False
    
    def create_unique_constraints(self, table_name, unique_constraints_metadata):
        """Создание уникальных ограничений"""
        try:
            if not unique_constraints_metadata:
                rprint(f"[yellow]⚠️ Нет уникальных ограничений для таблицы {table_name}[/yellow]")
                return True
            
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                
                # Группируем ограничения по имени
                constraints = {}
                for uc in unique_constraints_metadata:
                    uc_name = uc[0]
                    if uc_name not in constraints:
                        constraints[uc_name] = []
                    if uc[1]:  # column_name
                        constraints[uc_name].append((uc[1], uc[2]))  # (column, position)
                
                for uc_name, columns in constraints.items():
                    if not columns:
                        continue
                    
                    # Сортируем колонки по позиции
                    sorted_columns = [col[0] for col in sorted(columns, key=lambda x: x[1])]
                    
                    uc_ddl = f"ALTER TABLE ags.{table_name} ADD CONSTRAINT {uc_name} UNIQUE ({', '.join(sorted_columns)});"
                    cursor.execute(uc_ddl)
                    rprint(f"[green]✅ Создано уникальное ограничение {uc_name}[/green]")
                
                conn.commit()
                return True
                
        except Exception as e:
            rprint(f"[red]❌ Ошибка создания уникальных ограничений: {e}[/red]")
            return False
    
    def create_check_constraints(self, table_name, check_constraints_metadata):
        """Создание check ограничений"""
        try:
            if not check_constraints_metadata:
                rprint(f"[yellow]⚠️ Нет check ограничений для таблицы {table_name}[/yellow]")
                return True
            
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                
                for cc in check_constraints_metadata:
                    cc_name = cc[0]
                    cc_clause = cc[1]
                    
                    if not cc_clause:
                        continue
                    
                    cc_ddl = f"ALTER TABLE ags.{table_name} ADD CONSTRAINT {cc_name} CHECK ({cc_clause});"
                    cursor.execute(cc_ddl)
                    rprint(f"[green]✅ Создано check ограничение {cc_name}[/green]")
                
                conn.commit()
                return True
                
        except Exception as e:
            rprint(f"[red]❌ Ошибка создания check ограничений: {e}[/red]")
            return False
    
    def create_triggers(self, table_name, triggers_metadata):
        """Создание триггеров"""
        try:
            if not triggers_metadata:
                rprint(f"[yellow]⚠️ Нет триггеров для таблицы {table_name}[/yellow]")
                return True
            
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                
                for trigger in triggers_metadata:
                    trigger_name = trigger[0]
                    trigger_event = trigger[1]
                    trigger_timing = trigger[2]
                    trigger_definition = trigger[3]
                    
                    if not trigger_definition:
                        continue
                    
                    # Создаем триггер
                    cursor.execute(trigger_definition)
                    rprint(f"[green]✅ Создан триггер {trigger_name}[/green]")
                
                conn.commit()
                return True
                
        except Exception as e:
            rprint(f"[red]❌ Ошибка создания триггеров: {e}[/red]")
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
        """Основной метод полной миграции таблицы"""
        rprint(Panel(f"[bold blue]🚀 FEMCL - Полная миграция таблицы {table_name}[/bold blue]", expand=False))
        
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
            ddl = self.generate_complete_ddl(table_name, metadata)
            if not ddl:
                return False
            
            # 4. Создание таблицы
            if force and self.table_exists_pg(table_name):
                with self.get_pg_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"DROP TABLE IF EXISTS ags.{table_name} CASCADE;")
                    conn.commit()
                rprint(f"[yellow]⚠️ Таблица {table_name} удалена[/yellow]")
            
            with self.get_pg_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(ddl)
                conn.commit()
            rprint(f"[green]✅ Таблица {table_name} создана[/green]")
            
            # 5. Создание индексов
            indexes_metadata = self.get_indexes_metadata(table_name)
            self.create_indexes(table_name, indexes_metadata)
            
            # 6. Создание внешних ключей
            fks_metadata = self.get_foreign_keys_metadata(table_name)
            self.create_foreign_keys(table_name, fks_metadata)
            
            # 7. Создание уникальных ограничений
            unique_constraints_metadata = self.get_unique_constraints_metadata(table_name)
            self.create_unique_constraints(table_name, unique_constraints_metadata)
            
            # 8. Создание check ограничений
            check_constraints_metadata = self.get_check_constraints_metadata(table_name)
            self.create_check_constraints(table_name, check_constraints_metadata)
            
            # 9. Создание триггеров
            triggers_metadata = self.get_triggers_metadata(table_name)
            self.create_triggers(table_name, triggers_metadata)
            
            # 10. Перенос данных
            if not self.migrate_data(table_name, metadata):
                return False
            
            # 11. Валидация
            if not self.validate_migration(table_name):
                return False
            
            # 12. Обновление статуса
            self.update_status(table_name, "completed")
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            rprint(f"[green]✅ Таблица {table_name} полностью мигрирована за {duration}[/green]")
            return True
            
        except Exception as e:
            rprint(f"[red]❌ Ошибка миграции: {e}[/red]")
            self.update_status(table_name, "failed")
            return False
    
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

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='FEMCL - Полный скрипт для миграции отдельных таблиц')
    parser.add_argument('table_name', help='Имя таблицы для миграции')
    parser.add_argument('--force', action='store_true', help='Принудительное пересоздание таблицы')
    
    args = parser.parse_args()
    
    # Загрузка конфигурации
    config_loader = ConfigLoader()
    
    # Создание мигратора
    migrator = CompleteTableMigrator(config_loader)
    
    # Выполнение миграции
    success = migrator.migrate_table(
        table_name=args.table_name,
        force=args.force
    )
    
    if success:
        rprint("[bold green]✅ Полная миграция завершена успешно![/bold green]")
        sys.exit(0)
    else:
        rprint("[bold red]❌ Миграция завершена с ошибками![/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()