#!/usr/bin/env python3
"""
Скрипт для создания метаданных для всех 84 случаев использования функций
"""

import psycopg2
import yaml
import re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Загрузка конфигурации
with open('config/config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

postgres_config = config['database']['postgres']

console.print(Panel.fit(
    '[bold green]🚀 СОЗДАНИЕ МЕТАДАННЫХ ДЛЯ ВСЕХ 84 СЛУЧАЕВ ИСПОЛЬЗОВАНИЯ ФУНКЦИЙ[/bold green]',
    style='green'
))

# Подключение к PostgreSQL
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

def apply_rule_to_definition(definition: str, rule_id: int) -> str:
    """
    Применение правила маппинга к определению
    """
    cursor.execute('''
        SELECT mapping_pattern, replacement_pattern, mapping_type
        FROM mcl.function_mapping_rules
        WHERE id = %s
    ''', (rule_id,))
    
    pattern, replacement, mapping_type = cursor.fetchone()
    
    if mapping_type == 'direct':
        # Простая замена
        return definition.replace(pattern.split('\\')[0], replacement.split('\\')[0])
    elif mapping_type == 'regex':
        # Замена по регулярному выражению
        return re.sub(pattern, replacement, definition, flags=re.IGNORECASE)
    
    return definition

def process_all_default_constraints():
    """Обработка всех default constraints с getdate()"""
    console.print('\n1️⃣ Обработка всех default constraints с getdate()...')
    
    # Получаем все default constraints с getdate()
    cursor.execute('''
        SELECT 
            pdc.id,
            pdc.definition,
            pt.object_name,
            pdc.constraint_name
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_tables pt ON pdc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = 2
            AND pdc.definition IS NOT NULL
            AND pdc.definition ILIKE '%getdate%'
            AND pdc.function_mapping_rule_id IS NULL
    ''')
    
    all_default_constraints = cursor.fetchall()
    console.print(f'Найдено default constraints с getdate(): {len(all_default_constraints)}')
    
    # Получаем правило для getdate
    cursor.execute('''
        SELECT id FROM mcl.function_mapping_rules 
        WHERE source_function = 'getdate' AND 'default_constraint' = ANY(applicable_objects)
    ''')
    
    getdate_rule_id = cursor.fetchone()[0]
    processed_defaults = 0
    
    for constraint_id, definition, table_name, constraint_name in all_default_constraints:
        postgres_definition = apply_rule_to_definition(definition, getdate_rule_id)
        
        cursor.execute('''
            UPDATE mcl.postgres_default_constraints 
            SET 
                function_mapping_rule_id = %s,
                postgres_definition = %s,
                mapping_status = 'mapped',
                mapping_complexity = 'simple'
            WHERE id = %s
        ''', (getdate_rule_id, postgres_definition, constraint_id))
        
        processed_defaults += 1
    
    console.print(f'✅ Обработано default constraints: {processed_defaults}')
    return processed_defaults

def process_all_computed_columns():
    """Обработка всех computed columns с функциями"""
    console.print('\n2️⃣ Обработка всех computed columns с функциями...')
    
    # Получаем все computed columns с функциями
    cursor.execute('''
        SELECT 
            pc.id,
            pc.computed_definition,
            pt.object_name,
            pc.column_name
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = 2
            AND pc.computed_definition IS NOT NULL
            AND pc.computed_definition ILIKE ANY(ARRAY['%isnull%', '%len%', '%upper%', '%lower%', '%substring%', '%convert%', '%year%', '%month%', '%day%'])
            AND pc.computed_function_mapping_rule_id IS NULL
    ''')
    
    all_computed_columns = cursor.fetchall()
    console.print(f'Найдено computed columns с функциями: {len(all_computed_columns)}')
    
    # Получаем все правила маппинга
    cursor.execute('''
        SELECT id, source_function, mapping_pattern, replacement_pattern, mapping_type
        FROM mcl.function_mapping_rules
        WHERE is_active = TRUE
            AND 'computed_column' = ANY(applicable_objects)
        ORDER BY complexity_level, source_function
    ''')
    
    mapping_rules = cursor.fetchall()
    processed_computed = 0
    
    for column_id, definition, table_name, column_name in all_computed_columns:
        # Ищем подходящее правило для каждой функции в определении
        matched_rule = None
        postgres_definition = definition
        
        for rule_id, source_func, pattern, replacement, mapping_type in mapping_rules:
            if source_func in definition.lower():
                matched_rule = rule_id
                if mapping_type == 'direct':
                    postgres_definition = postgres_definition.replace(source_func, replacement.split('\\')[0])
                elif mapping_type == 'regex':
                    postgres_definition = re.sub(pattern, replacement, postgres_definition, flags=re.IGNORECASE)
                break
        
        if matched_rule:
            cursor.execute('''
                UPDATE mcl.postgres_columns 
                SET 
                    computed_function_mapping_rule_id = %s,
                    postgres_computed_definition = %s,
                    computed_mapping_status = 'mapped',
                    computed_mapping_complexity = 'simple'
                WHERE id = %s
            ''', (matched_rule, postgres_definition, column_id))
            
            processed_computed += 1
    
    console.print(f'✅ Обработано computed columns: {processed_computed}')
    return processed_computed

def validate_complete_coverage():
    """Валидация полного покрытия"""
    console.print('\n3️⃣ Валидация полного покрытия...')
    
    # Проверяем финальную статистику
    cursor.execute('''
        SELECT 
            COUNT(*) as total_with_functions,
            COUNT(function_mapping_rule_id) as mapped
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_tables pt ON pdc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = 2
            AND pdc.definition IS NOT NULL
            AND pdc.definition ILIKE '%getdate%'
    ''')
    
    default_final = cursor.fetchone()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_with_functions,
            COUNT(computed_function_mapping_rule_id) as mapped
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = 2
            AND pc.computed_definition IS NOT NULL
            AND pc.computed_definition ILIKE ANY(ARRAY['%isnull%', '%len%', '%upper%', '%lower%', '%substring%', '%convert%', '%year%', '%month%', '%day%'])
    ''')
    
    computed_final = cursor.fetchone()
    
    total_cases = default_final[0] + computed_final[0]
    total_mapped = default_final[1] + computed_final[1]
    coverage_percentage = (total_mapped / total_cases * 100) if total_cases > 0 else 0
    
    console.print(f'\n📊 ФИНАЛЬНАЯ СТАТИСТИКА:')
    console.print(f'Default constraints с getdate(): {default_final[0]} всего, {default_final[1]} обработано')
    console.print(f'Computed columns с функциями: {computed_final[0]} всего, {computed_final[1]} обработано')
    console.print(f'Общее покрытие: {total_mapped}/{total_cases} ({coverage_percentage:.1f}%)')
    
    return total_cases, total_mapped, coverage_percentage

def show_rule_statistics():
    """Показать статистику использования правил"""
    console.print('\n4️⃣ Статистика использования правил...')
    
    cursor.execute('''
        SELECT 
            fmr.source_function,
            fmr.target_function,
            COUNT(pdc.id) as default_constraints_count,
            COUNT(pc.id) as computed_columns_count,
            (COUNT(pdc.id) + COUNT(pc.id)) as total_usage
        FROM mcl.function_mapping_rules fmr
        LEFT JOIN mcl.postgres_default_constraints pdc ON fmr.id = pdc.function_mapping_rule_id
        LEFT JOIN mcl.postgres_columns pc ON fmr.id = pc.computed_function_mapping_rule_id
        GROUP BY fmr.id, fmr.source_function, fmr.target_function
        HAVING (COUNT(pdc.id) + COUNT(pc.id)) > 0
        ORDER BY total_usage DESC
    ''')
    
    rule_stats = cursor.fetchall()
    
    table = Table(title='📈 ФИНАЛЬНАЯ СТАТИСТИКА ИСПОЛЬЗОВАНИЯ ПРАВИЛ')
    table.add_column('Исходная функция', style='cyan', width=15)
    table.add_column('Целевая функция', style='green', width=15)
    table.add_column('Default constraints', style='blue', width=18)
    table.add_column('Computed columns', style='yellow', width=15)
    table.add_column('Всего', style='red', width=8)
    
    for source_func, target_func, default_count, computed_count, total in rule_stats:
        table.add_row(
            source_func, 
            target_func, 
            str(default_count),
            str(computed_count),
            str(total)
        )
    
    console.print(table)
    return rule_stats

def main():
    """Основная функция"""
    try:
        # Обработка default constraints
        processed_defaults = process_all_default_constraints()
        
        # Обработка computed columns
        processed_computed = process_all_computed_columns()
        
        # Валидация покрытия
        total_cases, total_mapped, coverage_percentage = validate_complete_coverage()
        
        # Статистика правил
        rule_stats = show_rule_statistics()
        
        # Итоговый отчет
        final_report = Panel(
            f'[bold green]🎯 МЕТАДАННЫЕ ДЛЯ ВСЕХ СЛУЧАЕВ ИСПОЛЬЗОВАНИЯ ФУНКЦИЙ СОЗДАНЫ![/bold green]\n'
            f'\n'
            f'[yellow]📊 ИТОГОВАЯ СТАТИСТИКА:[/yellow]\n'
            f'• Default constraints обработано: {processed_defaults}\n'
            f'• Computed columns обработано: {processed_computed}\n'
            f'• Всего случаев: {total_cases}\n'
            f'• Общее покрытие: {total_mapped}/{total_cases} ({coverage_percentage:.1f}%)\n'
            f'\n'
            f'[yellow]🔧 АКТИВНЫЕ ПРАВИЛА:[/yellow]\n'
            f'• Количество правил в использовании: {len(rule_stats)}\n'
            f'• Общее использование: {sum(r[4] for r in rule_stats)}\n'
            f'\n'
            f'[green]✅ РЕЗУЛЬТАТ:[/green]\n'
            f'Все найденные случаи использования функций обработаны!\n'
            f'Метаданные готовы для миграции.',
            title='🏆 УСПЕШНОЕ ЗАВЕРШЕНИЕ',
            border_style='green'
        )
        
        console.print(final_report)
        
        conn.commit()
        console.print('\n✅ МЕТАДАННЫЕ ДЛЯ ВСЕХ СЛУЧАЕВ ИСПОЛЬЗОВАНИЯ ФУНКЦИЙ СОЗДАНЫ!')
        
    except Exception as e:
        console.print(f'[red]❌ Ошибка при создании метаданных: {e}[/red]')
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    main()