#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔗 ТЕСТОВАЯ МИГРАЦИЯ С ВНЕШНИМИ КЛЮЧАМИ
Перенос таблиц до достижения 2 таблиц с внешними ключами
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from migration_functions import *
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from datetime import datetime

console = Console()

def get_tables_without_fk(task_id: int) -> list:
    """Получение таблиц без внешних ключей"""
    try:
        config = load_config()
        postgres_config = config['database']['postgres']
        
        conn = psycopg2.connect(
            host=postgres_config['host'],
            port=postgres_config['port'],
            dbname=postgres_config['database'],
            user=postgres_config['user'],
            password=postgres_config['password'],
            connect_timeout=postgres_config['connection_timeout'],
            sslmode=postgres_config['ssl_mode']
        )
        
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                mt.id,
                mt.object_name,
                mt.schema_name,
                mt.row_count,
                pt.migration_status
            FROM mcl.mssql_tables mt
            JOIN mcl.postgres_tables pt ON mt.id = pt.source_table_id
            WHERE mt.task_id = %s
                AND mt.schema_name = 'ags'
                AND mt.id NOT IN (
                    SELECT DISTINCT table_id 
                    FROM mcl.mssql_foreign_keys
                )
                AND pt.migration_status = 'pending'
            ORDER BY mt.object_name
        ''', (task_id,))
        
        tables = cursor.fetchall()
        conn.close()
        
        return tables
        
    except Exception as e:
        console.print(f'[red]❌ Ошибка получения таблиц без FK: {e}[/red]')
        return []

def get_tables_with_fk(task_id: int) -> list:
    """Получение таблиц с внешними ключами"""
    try:
        config = load_config()
        postgres_config = config['database']['postgres']
        
        conn = psycopg2.connect(
            host=postgres_config['host'],
            port=postgres_config['port'],
            dbname=postgres_config['database'],
            user=postgres_config['user'],
            password=postgres_config['password'],
            connect_timeout=postgres_config['connection_timeout'],
            sslmode=postgres_config['ssl_mode']
        )
        
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                mt.id,
                mt.object_name,
                mt.schema_name,
                mt.row_count,
                pt.migration_status,
                COUNT(mfk.id) as fk_count
            FROM mcl.mssql_tables mt
            JOIN mcl.postgres_tables pt ON mt.id = pt.source_table_id
            LEFT JOIN mcl.mssql_foreign_keys mfk ON mt.id = mfk.table_id
            WHERE mt.task_id = %s
                AND mt.schema_name = 'ags'
                AND pt.migration_status = 'pending'
            GROUP BY mt.id, mt.object_name, mt.schema_name, mt.row_count, pt.migration_status
            HAVING COUNT(mfk.id) > 0
            ORDER BY mt.object_name
        ''', (task_id,))
        
        tables = cursor.fetchall()
        conn.close()
        
        return tables
        
    except Exception as e:
        console.print(f'[red]❌ Ошибка получения таблиц с FK: {e}[/red]')
        return []

def check_fk_dependencies(table_id: int, task_id: int) -> bool:
    """Проверка готовности зависимостей для таблицы с внешними ключами"""
    try:
        config = load_config()
        postgres_config = config['database']['postgres']
        
        conn = psycopg2.connect(
            host=postgres_config['host'],
            port=postgres_config['port'],
            dbname=postgres_config['database'],
            user=postgres_config['user'],
            password=postgres_config['password'],
            connect_timeout=postgres_config['connection_timeout'],
            sslmode=postgres_config['ssl_mode']
        )
        
        cursor = conn.cursor()
        
        # Получение внешних ключей таблицы
        cursor.execute('''
            SELECT 
                mfk.referenced_table_id,
                mt.object_name as referenced_table_name
            FROM mcl.mssql_foreign_keys mfk
            JOIN mcl.mssql_tables mt ON mfk.referenced_table_id = mt.id
            WHERE mfk.table_id = %s
        ''', (table_id,))
        
        fk_dependencies = cursor.fetchall()
        
        if not fk_dependencies:
            conn.close()
            return True  # Нет зависимостей
        
        # Проверка статуса зависимых таблиц
        all_ready = True
        for ref_table_id, ref_table_name in fk_dependencies:
            cursor.execute('''
                SELECT migration_status
                FROM mcl.postgres_tables
                WHERE source_table_id = %s
            ''', (ref_table_id,))
            
            result = cursor.fetchone()
            if not result or result[0] != 'completed':
                console.print(f'    ⏳ Ожидает: {ref_table_name}')
                all_ready = False
            else:
                console.print(f'    ✅ Готова: {ref_table_name}')
        
        conn.close()
        return all_ready
        
    except Exception as e:
        console.print(f'[red]❌ Ошибка проверки зависимостей: {e}[/red]')
        return False

def execute_test_migration_with_fk(task_id: int = 2):
    """Выполнение тестовой миграции до 2 таблиц с внешними ключами"""
    
    console.print(Panel(
        f'[bold blue]🔗 ТЕСТОВАЯ МИГРАЦИЯ С ВНЕШНИМИ КЛЮЧАМИ[/bold blue]\\n'
        f'Задача: {task_id}\\n'
        f'Цель: Перенести таблицы до достижения 2 таблиц с FK',
        title='ТЕСТ С FK',
        border_style='blue'
    ))
    
    # Валидация задачи
    if not validate_migration_task(task_id):
        return 0
    
    total_migrated = 0
    fk_tables_migrated = 0
    target_fk_tables = 2
    
    # Этап 1: Миграция таблиц без внешних ключей
    console.print(f'\\n[bold cyan]📋 ЭТАП 1: Миграция таблиц без внешних ключей[/bold cyan]')
    
    tables_without_fk = get_tables_without_fk(task_id)
    console.print(f'📊 Найдено таблиц без FK: {len(tables_without_fk)}')
    
    if tables_without_fk:
        console.print(f'📋 Первые 10 таблиц без FK:')
        table = Table()
        table.add_column('№', width=3)
        table.add_column('ID', width=6)
        table.add_column('Таблица', width=25)
        table.add_column('Строк', width=8)
        table.add_column('Статус', width=12)
        
        for i, (table_id, name, schema, rows, status) in enumerate(tables_without_fk[:10], 1):
            table.add_row(str(i), str(table_id), name, str(rows), status)
        
        console.print(table)
    
    # Миграция всех таблиц без FK
    for i, (table_id, table_name, schema, rows, status) in enumerate(tables_without_fk, 1):
        console.print(f'\\n📋 [{i}/{len(tables_without_fk)}] Миграция: {table_name} (строк: {rows})')
        
        try:
            success = migrate_single_table(table_id, task_id)
            
            if success:
                total_migrated += 1
                console.print(f'  ✅ Таблица {table_name} успешно мигрирована!')
            else:
                console.print(f'  ❌ Ошибка миграции {table_name}')
                
        except Exception as e:
            console.print(f'  ❌ Критическая ошибка миграции {table_name}: {e}')
    
    console.print(f'\\n[green]✅ Этап 1 завершен. Мигрировано таблиц без FK: {total_migrated}[/green]')
    
    # Этап 2: Миграция таблиц с внешними ключами
    console.print(f'\\n[bold cyan]🔗 ЭТАП 2: Миграция таблиц с внешними ключами[/bold cyan]')
    
    tables_with_fk = get_tables_with_fk(task_id)
    console.print(f'📊 Найдено таблиц с FK: {len(tables_with_fk)}')
    
    if tables_with_fk:
        console.print(f'📋 Первые 10 таблиц с FK:')
        table = Table()
        table.add_column('№', width=3)
        table.add_column('ID', width=6)
        table.add_column('Таблица', width=25)
        table.add_column('Строк', width=8)
        table.add_column('FK', width=4)
        table.add_column('Статус', width=12)
        
        for i, (table_id, name, schema, rows, status, fk_count) in enumerate(tables_with_fk[:10], 1):
            table.add_row(str(i), str(table_id), name, str(rows), str(fk_count), status)
        
        console.print(table)
    
    # Попытка миграции таблиц с FK до достижения цели
    for i, (table_id, table_name, schema, rows, status, fk_count) in enumerate(tables_with_fk, 1):
        if fk_tables_migrated >= target_fk_tables:
            console.print(f'\\n[green]🎯 ДОСТИГНУТА ЦЕЛЬ: Перенесено {target_fk_tables} таблиц с FK![/green]')
            break
        
        console.print(f'\\n📋 [{i}/{len(tables_with_fk)}] Проверка: {table_name} (FK: {fk_count})')
        
        # Проверка зависимостей
        console.print(f'  🔍 Проверка зависимостей...')
        dependencies_ready = check_fk_dependencies(table_id, task_id)
        
        if dependencies_ready:
            console.print(f'  ✅ Зависимости готовы, начинаем миграцию...')
            
            try:
                success = migrate_single_table(table_id, task_id)
                
                if success:
                    total_migrated += 1
                    fk_tables_migrated += 1
                    console.print(f'  ✅ Таблица с FK {table_name} успешно мигрирована!')
                    console.print(f'  📊 Таблиц с FK мигрировано: {fk_tables_migrated}/{target_fk_tables}')
                else:
                    console.print(f'  ❌ Ошибка миграции {table_name}')
                    
            except Exception as e:
                console.print(f'  ❌ Критическая ошибка миграции {table_name}: {e}')
        else:
            console.print(f'  ⏳ Зависимости не готовы, пропускаем {table_name}')
    
    # Итоговая статистика
    console.print(f'\\n[bold green]🎉 ТЕСТОВАЯ МИГРАЦИЯ С FK ЗАВЕРШЕНА![/bold green]')
    console.print(f'📊 ИТОГОВАЯ СТАТИСТИКА:')
    console.print(f'  • Всего мигрировано таблиц: {total_migrated}')
    console.print(f'  • Таблиц без FK: {total_migrated - fk_tables_migrated}')
    console.print(f'  • Таблиц с FK: {fk_tables_migrated}')
    console.print(f'  • Цель достигнута: {"✅ Да" if fk_tables_migrated >= target_fk_tables else "❌ Нет"}')
    
    # Логирование завершения
    log_migration_event(
        'TEST_MIGRATION_WITH_FK_COMPLETE',
        f'Тестовая миграция с FK завершена. Всего: {total_migrated}, с FK: {fk_tables_migrated}',
        'INFO',
        task_id=task_id
    )
    
    return total_migrated

def main():
    """Основная функция"""
    console.print(Panel.fit(
        '[bold magenta]🔗 ТЕСТОВАЯ МИГРАЦИЯ С ВНЕШНИМИ КЛЮЧАМИ[/bold magenta]\\n'
        'Перенос до достижения 2 таблиц с FK',
        style='magenta'
    ))
    
    # Параметры
    task_id = 2
    
    # Валидация задачи
    if not validate_migration_task(task_id):
        console.print(Panel(
            f'[bold red]❌ ОШИБКА: Задача {task_id} не найдена![/bold red]',
            title='ОШИБКА',
            border_style='red'
        ))
        return
    
    # Выполнение тестовой миграции
    migrated_count = execute_test_migration_with_fk(task_id)
    
    if migrated_count > 0:
        console.print(Panel(
            f'[bold green]🎉 ТЕСТОВАЯ МИГРАЦИЯ С FK ЗАВЕРШЕНА![/bold green]\\n'
            f'Задача: {task_id}\\n'
            f'Мигрировано таблиц: {migrated_count}',
            title='ИТОГИ',
            border_style='green'
        ))
    else:
        console.print(Panel(
            f'[bold red]❌ МИГРАЦИЯ НЕ ВЫПОЛНЕНА[/bold red]\\n'
            f'Задача: {task_id}',
            title='ИТОГИ',
            border_style='red'
        ))

if __name__ == '__main__':
    main()

