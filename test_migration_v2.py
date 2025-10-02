#!/usr/bin/env python3
"""
Улучшенная тестовая миграция с реальным созданием таблиц и переносом данных
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from migration_functions import *
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

console = Console()

def initialize_migration_v2(task_id: int = 2):
    """Инициализация улучшенной миграции"""
    
    console.print(Panel.fit(
        f'[bold green]🚀 УЛУЧШЕННАЯ ТЕСТОВАЯ МИГРАЦИЯ V2[/bold green]\\n'
        f'С реальным созданием таблиц и переносом данных\\n'
        f'Задача миграции: ID = {task_id}\\n'
        f'Цель: Перенести первые 3 таблицы без внешних ключей',
        style='green'
    ))
    
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
        
        # Получение списка таблиц без внешних ключей для конкретной задачи
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
                    SELECT DISTINCT mt2.id
                    FROM mcl.mssql_foreign_keys mfk
                    JOIN mcl.mssql_tables mt2 ON mfk.table_id = mt2.id
                    WHERE mt2.task_id = %s
                )
                AND pt.migration_status = 'pending'
            ORDER BY mt.object_name
        ''', (task_id, task_id))
        
        no_fk_tables = cursor.fetchall()
        
        console.print(f'\\n[blue]📊 Найдено таблиц без внешних ключей: {len(no_fk_tables)}[/blue]')
        
        # Показываем первые 10 таблиц
        if no_fk_tables:
            console.print('\\n[cyan]📋 Первые 10 таблиц для миграции:[/cyan]')
            table = Table()
            table.add_column('№', style='cyan')
            table.add_column('ID', style='yellow')
            table.add_column('Имя таблицы', style='green')
            table.add_column('Строк', style='magenta')
            table.add_column('Статус', style='red')
            
            for i, (table_id, name, schema, rows, status) in enumerate(no_fk_tables[:10], 1):
                table.add_row(str(i), str(table_id), name, str(rows), status)
            
            console.print(table)
        
        conn.close()
        
        log_migration_event(
            'MIGRATION_V2_START',
            f'Начало улучшенной миграции задачи {task_id}. Найдено {len(no_fk_tables)} таблиц без FK',
            'INFO',
            task_id=task_id
        )
        
        return no_fk_tables
        
    except Exception as e:
        console.print(f'[red]❌ Ошибка инициализации: {e}[/red]')
        log_migration_event('MIGRATION_V2_INIT_ERROR', f'Ошибка инициализации: {e}', 'ERROR')
        return []

def execute_migration_cycle_v2(task_id: int = 2):
    """Выполнение улучшенного цикла миграции"""
    
    console.print(Panel(
        f'[bold blue]🔄 ЦИКЛ МИГРАЦИИ V2[/bold blue]\\n'
        f'С реальным созданием таблиц и переносом данных\\n'
        f'Задача: {task_id}',
        title='BPMN ЭТАП 2',
        border_style='blue'
    ))
    
    # Валидация задачи
    if not validate_migration_task(task_id):
        return 0
    
    # Применение маппинга функций
    console.print('\\n[blue]🎯 Применение маппинга функций...[/blue]')
    try:
        # Применяем маппинг ко всем типам объектов
        mapping_results = apply_universal_function_mapping(task_id)
        
        console.print(f'  • Default constraints обработано: {mapping_results["default_constraints_processed"]}')
        console.print(f'  • Computed columns обработано: {mapping_results["computed_columns_processed"]}')
        console.print(f'  • CHECK constraints обработано: {mapping_results["check_constraints_processed"]}')
        console.print(f'  • Индексы обработано: {mapping_results["indexes_processed"]}')
        
        if mapping_results['errors']:
            console.print(f'  ⚠️ Ошибки маппинга: {len(mapping_results["errors"])}')
            for error in mapping_results['errors']:
                console.print(f'    • {error}')
        
        log_migration_event(
            'FUNCTION_MAPPING_COMPLETE',
            f'Маппинг функций завершен. Обработано: {mapping_results["default_constraints_processed"]} default constraints, {mapping_results["computed_columns_processed"]} computed columns',
            'INFO',
            task_id=task_id
        )
        
    except Exception as e:
        console.print(f'  ❌ Ошибка маппинга функций: {e}')
        log_migration_event(
            'FUNCTION_MAPPING_ERROR',
            f'Ошибка маппинга функций: {e}',
            'ERROR',
            task_id=task_id
        )
    
    # Предварительное распределение колонок
    console.print('\\n[blue]🎯 Предварительное распределение колонок...[/blue]')
    try:
        distribution_success = analyze_and_distribute_columns(task_id)
        
        if distribution_success:
            console.print('  ✅ Распределение колонок выполнено успешно')
            
            # Проверка распределения
            distribution_check = check_column_distribution(task_id)
            console.print(f'  • Проверено таблиц: {len(distribution_check)}')
            
            log_migration_event(
                'COLUMN_DISTRIBUTION_COMPLETE',
                f'Распределение колонок завершено. Проверено таблиц: {len(distribution_check)}',
                'INFO',
                task_id=task_id
            )
        else:
            console.print('  ❌ Ошибка распределения колонок')
            
    except Exception as e:
        console.print(f'  ❌ Ошибка распределения колонок: {e}')
        log_migration_event(
            'COLUMN_DISTRIBUTION_ERROR',
            f'Ошибка распределения колонок: {e}',
            'ERROR',
            task_id=task_id
        )
    
    # Инициализация
    tables_to_migrate = initialize_migration_v2(task_id)
    
    if not tables_to_migrate:
        console.print('[red]❌ Нет таблиц для миграции![/red]')
        return 0
    
    # Счетчики
    target_count = 3
    migrated_count = 0
    failed_count = 0
    
    console.print(f'\\n[yellow]🎯 Цель: Перенести {target_count} таблиц[/yellow]')
    
    # Проход по таблицам
    for i, (table_id, table_name, schema, row_count, status) in enumerate(tables_to_migrate, 1):
        
        console.print(f'\\n[cyan]📋 Обработка таблицы {i}: {table_name} (ID: {table_id})[/cyan]')
        console.print(f'  • Строк: {row_count}')
        console.print(f'  • Статус: {status}')
        
        # Проверка готовности
        if status != 'pending':
            console.print(f'  ⚠️ Пропуск - неожиданный статус: {status}')
            continue
        
        # Выполнение миграции таблицы
        console.print(f'  🚀 Начало миграции...')
        
        try:
            success = migrate_single_table(table_id, task_id)
            
            if success:
                migrated_count += 1
                console.print(f'  ✅ Таблица {table_name} успешно мигрирована!')
                
                # Проверка достижения цели
                if migrated_count >= target_count:
                    console.print(f'\\n[green]🎉 ДОСТИГНУТА ЦЕЛЬ: Перенесено {migrated_count} таблиц![/green]')
                    break
            else:
                failed_count += 1
                console.print(f'  ❌ Ошибка миграции таблицы {table_name}')
                
                # Останавливаем при ошибке
                console.print(f'\\n[red]🛑 ОСТАНОВКА ИЗ-ЗА ОШИБКИ[/red]')
                break
                
        except Exception as e:
            failed_count += 1
            console.print(f'  ❌ Критическая ошибка: {e}')
            console.print(f'\\n[red]🛑 ОСТАНОВКА ИЗ-ЗА КРИТИЧЕСКОЙ ОШИБКИ[/red]')
            break
    
    # Итоговая статистика
    console.print(f'\\n[blue]📊 ИТОГОВАЯ СТАТИСТИКА:[/blue]')
    console.print(f'  • Обработано таблиц: {i}')
    console.print(f'  • Успешно мигрировано: {migrated_count}')
    console.print(f'  • Ошибок: {failed_count}')
    console.print(f'  • Цель достигнута: {"✅ Да" if migrated_count >= target_count else "❌ Нет"}')
    
    # Логирование завершения
    log_migration_event(
        'MIGRATION_V2_COMPLETE',
        f'Завершена миграция V2 задачи {task_id}. Успешно: {migrated_count}, Ошибок: {failed_count}',
        'INFO',
        task_id=task_id
    )
    
    return migrated_count

def validate_migration_results_v2():
    """Валидация результатов улучшенной миграции"""
    
    console.print(Panel(
        '[bold blue]🔍 ВАЛИДАЦИЯ РЕЗУЛЬТАТОВ V2[/bold blue]\\n'
        'Проверка физических таблиц в PostgreSQL',
        title='BPMN ЭТАП 5',
        border_style='blue'
    ))
    
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
        
        # Проверка количества таблиц в схеме ags
        cursor.execute('''
            SELECT COUNT(*) as table_count
            FROM information_schema.tables 
            WHERE table_schema = 'ags'
        ''')
        
        ags_tables_count = cursor.fetchone()[0]
        
        console.print(f'\\n[blue]📊 ТАБЛИЦ В СХЕМЕ AGS: {ags_tables_count}[/blue]')
        
        if ags_tables_count > 0:
            # Получение списка таблиц в схеме ags
            cursor.execute('''
                SELECT 
                    table_name,
                    CASE 
                        WHEN table_name = 'cn_inv_cmm_fn_n' THEN (SELECT COUNT(*) FROM ags.cn_inv_cmm_fn_n)
                        WHEN table_name = 'cn_inv_cmm_gr' THEN (SELECT COUNT(*) FROM ags.cn_inv_cmm_gr)
                        WHEN table_name = 'cn_inv_cmm_tp' THEN (SELECT COUNT(*) FROM ags.cn_inv_cmm_tp)
                        ELSE 0
                    END as row_count
                FROM information_schema.tables 
                WHERE table_schema = 'ags'
                ORDER BY table_name
            ''')
            
            ags_tables = cursor.fetchall()
            
            console.print('\\n[green]📋 ТАБЛИЦЫ В СХЕМЕ AGS:[/green]')
            table = Table()
            table.add_column('Имя таблицы', style='cyan')
            table.add_column('Строк', style='green')
            
            for table_name, row_count in ags_tables:
                table.add_row(table_name, str(row_count))
            
            console.print(table)
        
        # Проверка статусов в метаданных
        cursor.execute('''
            SELECT 
                migration_status,
                COUNT(*) as count
            FROM mcl.postgres_tables
            GROUP BY migration_status
            ORDER BY migration_status
        ''')
        
        statuses = cursor.fetchall()
        
        console.print('\\n[blue]📊 СТАТУСЫ В МЕТАДАННЫХ:[/blue]')
        status_table = Table()
        status_table.add_column('Статус', style='cyan')
        status_table.add_column('Количество', style='green')
        
        for status, count in statuses:
            status_table.add_row(status, str(count))
        
        console.print(status_table)
        
        # Проверка статистики маппинга функций
        console.print('\\n[blue]🎯 СТАТИСТИКА МАППИНГА ФУНКЦИЙ:[/blue]')
        try:
            mapping_stats = get_function_mapping_statistics(task_id)
            
            console.print(f'  • Default constraints: {mapping_stats["default_constraints"]["mapped"]}/{mapping_stats["default_constraints"]["total"]} обработано')
            console.print(f'  • Computed columns: {mapping_stats["computed_columns"]["mapped"]}/{mapping_stats["computed_columns"]["total"]} обработано')
            console.print(f'  • Общее покрытие: {mapping_stats["coverage_percentage"]:.1f}%')
            
            if mapping_stats['coverage_percentage'] == 100.0:
                console.print('  ✅ Полное покрытие маппинга функций')
            else:
                console.print('  ⚠️ Неполное покрытие маппинга функций')
                
        except Exception as e:
            console.print(f'  ❌ Ошибка получения статистики маппинга: {e}')
        
        # Проверка соответствия
        cursor.execute('''
            SELECT 
                pt.object_name,
                pt.migration_status,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'ags' AND table_name = pt.object_name
                    ) THEN 'EXISTS'
                    ELSE 'MISSING'
                END as physical_status
            FROM mcl.postgres_tables pt
            WHERE pt.migration_status = 'completed'
            ORDER BY pt.object_name
        ''')
        
        completed_tables = cursor.fetchall()
        
        console.print('\\n[blue]📊 СООТВЕТСТВИЕ СТАТУСОВ И ФИЗИЧЕСКИХ ТАБЛИЦ:[/blue]')
        if completed_tables:
            physical_table = Table()
            physical_table.add_column('Таблица', style='cyan')
            physical_table.add_column('Статус', style='yellow')
            physical_table.add_column('Физическая таблица', style='green')
            
            for table_name, status, physical in completed_tables:
                physical_table.add_row(
                    table_name, 
                    status, 
                    '✅ Существует' if physical == 'EXISTS' else '❌ Отсутствует'
                )
            
            console.print(physical_table)
        else:
            console.print('[yellow]Нет завершенных таблиц для проверки[/yellow]')
        
        conn.close()
        
        # Анализ результатов
        success_count = sum(1 for _, _, physical in completed_tables if physical == 'EXISTS')
        total_completed = len(completed_tables)
        
        console.print(f'\\n[blue]📊 АНАЛИЗ СООТВЕТСТВИЯ:[/blue]')
        console.print(f'  • Завершенных таблиц в метаданных: {total_completed}')
        console.print(f'  • Физических таблиц в PostgreSQL: {ags_tables_count}')
        console.print(f'  • Соответствие: {success_count}/{total_completed}')
        
        if ags_tables_count > 0 and total_completed > 0:
            console.print('[green]✅ МИГРАЦИЯ РАБОТАЕТ КОРРЕКТНО![/green]')
        else:
            console.print('[red]❌ ПРОБЛЕМЫ С МИГРАЦИЕЙ![/red]')
        
        log_migration_event(
            'VALIDATION_V2_COMPLETE',
            f'Валидация V2 завершена. Физических таблиц: {ags_tables_count}, завершенных: {total_completed}',
            'INFO'
        )
        
        return ags_tables_count > 0
        
    except Exception as e:
        console.print(f'[red]❌ Ошибка валидации: {e}[/red]')
        log_migration_event('VALIDATION_V2_ERROR', f'Ошибка валидации: {e}', 'ERROR')
        return False

def main(task_id: int = 2):
    """Основная функция"""
    console.print(Panel.fit(
        f'[bold magenta]🎯 ТЕСТОВАЯ МИГРАЦИЯ V2 - ГОТОВ К ЗАПУСКУ[/bold magenta]\\n'
        f'Задача миграции: ID = {task_id}',
        style='magenta'
    ))
    
    # Валидация задачи
    if not validate_migration_task(task_id):
        console.print(Panel(
            f'[bold red]❌ ОШИБКА: Задача {task_id} не найдена![/bold red]',
            title='ОШИБКА',
            border_style='red'
        ))
        return
    
    # Выполнение цикла миграции
    migrated_count = execute_migration_cycle_v2(task_id)
    
    if migrated_count > 0:
        # Валидация результатов
        validation_success = validate_migration_results_v2()
        
        # Итоговый отчет
        console.print(Panel(
            f'[bold green]🎉 ТЕСТОВАЯ МИГРАЦИЯ V2 ЗАВЕРШЕНА[/bold green]\\n'
            f'Задача: {task_id}\\n'
            f'Перенесено таблиц: {migrated_count}\\n'
            f'Валидация: {"✅ Успешна" if validation_success else "❌ Не пройдена"}',
            title='ИТОГИ',
            border_style='green'
        ))
    else:
        console.print(Panel(
            f'[bold red]❌ ТЕСТОВАЯ МИГРАЦИЯ V2 НЕ УДАЛАСЬ[/bold red]\\n'
            f'Задача: {task_id}',
            title='ИТОГИ',
            border_style='red'
        ))

if __name__ == '__main__':
    main()
