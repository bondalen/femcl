#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 ПОЛНОМАСШТАБНАЯ МИГРАЦИЯ V2
Система миграции с поддержкой задач и контекста
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from migration_functions import *
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, TaskID
from datetime import datetime
import time

console = Console()

def display_task_statistics(task_id: int):
    """Отображение статистики по задаче"""
    try:
        stats = get_task_statistics(task_id)
        
        if not stats:
            console.print(f'[red]❌ Статистика для задачи {task_id} не найдена[/red]')
            return
        
        console.print(Panel(
            f'[bold blue]📊 СТАТИСТИКА ЗАДАЧИ {task_id}[/bold blue]\\n'
            f'\\n'
            f'[cyan]Описание:[/cyan] {stats["description"]}\\n'
            f'[cyan]Создана:[/cyan] {stats["created_at"]}\\n'
            f'\\n'
            f'[green]Всего таблиц:[/green] {stats["total_tables"]}\\n'
            f'[green]Завершено:[/green] {stats["completed_tables"]}\\n'
            f'[yellow]Ожидает:[/yellow] {stats["pending_tables"]}\\n'
            f'[red]Ошибок:[/red] {stats["failed_tables"]}\\n'
            f'\\n'
            f'[bold blue]Прогресс:[/bold blue] {stats["completion_percentage"]}%',
            title='СТАТИСТИКА ЗАДАЧИ',
            border_style='blue'
        ))
        
    except Exception as e:
        console.print(f'[red]❌ Ошибка отображения статистики: {e}[/red]')

def execute_full_migration_cycle(task_id: int, max_iterations: int = 10) -> int:
    """Выполнение полного цикла миграции для задачи"""
    
    console.print(Panel(
        f'[bold green]🚀 ПОЛНОМАСШТАБНАЯ МИГРАЦИЯ V2[/bold green]\\n'
        f'Задача: {task_id}\\n'
        f'Максимум итераций: {max_iterations}',
        title='НАЧАЛО МИГРАЦИИ',
        border_style='green'
    ))
    
    # Валидация задачи
    if not validate_migration_task(task_id):
        return 0
    
    # Отображение начальной статистики
    display_task_statistics(task_id)
    
    total_migrated = 0
    iteration = 0
    
    with Progress() as progress:
        task = progress.add_task("[green]Миграция таблиц...", total=100)
        
        while iteration < max_iterations:
            iteration += 1
            
            console.print(f'\\n[bold blue]🔄 ИТЕРАЦИЯ {iteration}[/bold blue]')
            
            # Получение таблиц без внешних ключей для текущей итерации
            tables_to_migrate = get_unmigrated_tables_for_task(task_id)
            
            if not tables_to_migrate:
                console.print(f'[green]✅ Все таблицы задачи {task_id} мигрированы![/green]')
                break
            
            console.print(f'📊 Найдено таблиц для миграции: {len(tables_to_migrate)}')
            
            iteration_migrated = 0
            iteration_failed = 0
            
            # Миграция таблиц в текущей итерации
            for i, (table_id, table_name, schema, rows, status) in enumerate(tables_to_migrate, 1):
                console.print(f'\\n📋 [{i}/{len(tables_to_migrate)}] Миграция: {table_name} (строк: {rows})')
                
                try:
                    success = migrate_single_table(table_id, task_id)
                    
                    if success:
                        iteration_migrated += 1
                        total_migrated += 1
                        progress.update(task, advance=1)
                    else:
                        iteration_failed += 1
                        
                except Exception as e:
                    console.print(f'[red]❌ Критическая ошибка миграции {table_name}: {e}[/red]')
                    iteration_failed += 1
            
            # Статистика итерации
            console.print(f'\\n[blue]📊 Результаты итерации {iteration}:[/blue]')
            console.print(f'  • Мигрировано: {iteration_migrated}')
            console.print(f'  • Ошибок: {iteration_failed}')
            console.print(f'  • Всего мигрировано: {total_migrated}')
            
            # Логирование результатов итерации
            log_migration_event(
                'MIGRATION_ITERATION_COMPLETE',
                f'Итерация {iteration} завершена. Мигрировано: {iteration_migrated}, Ошибок: {iteration_failed}',
                'INFO',
                task_id=task_id
            )
            
            # Если в итерации не было миграций, значит остались только таблицы с зависимостями
            if iteration_migrated == 0:
                console.print(f'[yellow]⚠️ В итерации {iteration} не было миграций. Возможно, остались таблицы с зависимостями.[/yellow]')
                
                # Попробуем мигрировать таблицы с зависимостями
                remaining_tables = get_remaining_tables_with_dependencies(task_id)
                if remaining_tables:
                    console.print(f'📊 Найдено таблиц с зависимостями: {len(remaining_tables)}')
                    console.print('[blue]Попытка миграции таблиц с зависимостями...[/blue]')
                    
                    for table_id, table_name, schema, rows, status in remaining_tables[:5]:  # Ограничиваем 5 таблицами
                        console.print(f'🔄 Попытка миграции с зависимостями: {table_name}')
                        try:
                            success = migrate_single_table(table_id, task_id)
                            if success:
                                total_migrated += 1
                                progress.update(task, advance=1)
                        except Exception as e:
                            console.print(f'[red]❌ Ошибка миграции {table_name}: {e}[/red]')
                else:
                    console.print(f'[green]✅ Все таблицы задачи {task_id} успешно мигрированы![/green]')
                    break
            
            # Небольшая пауза между итерациями
            time.sleep(1)
    
    # Финальная статистика
    console.print(f'\\n[bold green]🎉 МИГРАЦИЯ ЗАВЕРШЕНА![/bold green]')
    console.print(f'[blue]Всего мигрировано таблиц: {total_migrated}[/blue]')
    console.print(f'[blue]Выполнено итераций: {iteration}[/blue]')
    
    # Отображение финальной статистики
    display_task_statistics(task_id)
    
    # Логирование завершения
    log_migration_event(
        'FULL_MIGRATION_COMPLETE',
        f'Полномасштабная миграция задачи {task_id} завершена. Мигрировано: {total_migrated}, Итераций: {iteration}',
        'INFO',
        task_id=task_id
    )
    
    return total_migrated

def get_remaining_tables_with_dependencies(task_id: int) -> list:
    """Получение оставшихся таблиц с зависимостями"""
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
        
        # Получение таблиц с зависимостями, которые еще не мигрированы
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
                AND pt.migration_status = 'pending'
                AND mt.id IN (
                    SELECT DISTINCT table_id 
                    FROM mcl.mssql_foreign_keys
                )
            ORDER BY mt.object_name
        ''', (task_id,))
        
        tables = cursor.fetchall()
        conn.close()
        
        return tables
        
    except Exception as e:
        console.print(f'[red]❌ Ошибка получения таблиц с зависимостями: {e}[/red]')
        return []

def main():
    """Основная функция"""
    console.print(Panel.fit(
        '[bold magenta]🎯 ПОЛНОМАСШТАБНАЯ МИГРАЦИЯ V2[/bold magenta]\\n'
        'Система готова к миграции всех таблиц задачи',
        style='magenta'
    ))
    
    # Параметры по умолчанию
    task_id = 2
    max_iterations = 10
    
    # Валидация задачи
    if not validate_migration_task(task_id):
        console.print(Panel(
            f'[bold red]❌ ОШИБКА: Задача {task_id} не найдена![/bold red]',
            title='ОШИБКА',
            border_style='red'
        ))
        return
    
    # Подтверждение запуска
    console.print(Panel(
        f'[bold yellow]⚠️ ВНИМАНИЕ: Запуск полномасштабной миграции[/bold yellow]\\n'
        f'Задача: {task_id}\\n'
        f'Максимум итераций: {max_iterations}\\n'
        f'\\n'
        f'Это может занять значительное время!',
        title='ПОДТВЕРЖДЕНИЕ',
        border_style='yellow'
    ))
    
    # Выполнение миграции
    migrated_count = execute_full_migration_cycle(task_id, max_iterations)
    
    if migrated_count > 0:
        console.print(Panel(
            f'[bold green]🎉 ПОЛНОМАСШТАБНАЯ МИГРАЦИЯ ЗАВЕРШЕНА![/bold green]\\n'
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

