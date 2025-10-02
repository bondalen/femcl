#!/usr/bin/env python3
"""
Скрипт для маппинга функций в CHECK constraints
"""

import psycopg2
from rich.console import Console

console = Console()

def map_check_constraints_functions(task_id: int):
    """Маппинг функций в CHECK constraints для задачи"""
    
    # Подключение к базе данных
    conn = psycopg2.connect(
        dbname='fish_eye',
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432'
    )
    cursor = conn.cursor()
    
    try:
        # Получаем все CHECK constraints с функциями
        cursor.execute('''
            SELECT 
                pcc.id,
                pcc.definition,
                pt.object_name,
                pcc.constraint_name
            FROM mcl.postgres_check_constraints pcc
            JOIN mcl.postgres_check_constraint_columns pccc ON pcc.id = pccc.check_constraint_id
            JOIN mcl.postgres_columns pc ON pccc.column_id = pc.id
            JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
            JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
            WHERE mt.task_id = %s
                AND pcc.definition IS NOT NULL
                AND pcc.function_mapping_rule_id IS NULL
        ''', (task_id,))
        
        check_constraints = cursor.fetchall()
        
        console.print(f'🔍 Найдено CHECK constraints с функциями: {len(check_constraints)}')
        
        processed_count = 0
        
        for constraint_id, definition, table_name, constraint_name in check_constraints:
            console.print(f'  📋 Обработка: {constraint_name} в таблице {table_name}')
            console.print(f'     Определение: {definition[:100]}...')
            
            # Простой маппинг функций (можно расширить)
            postgres_definition = definition
            
            # Маппинг основных функций
            if 'getdate()' in postgres_definition:
                postgres_definition = postgres_definition.replace('getdate()', 'CURRENT_TIMESTAMP')
            
            if 'isnull(' in postgres_definition:
                postgres_definition = postgres_definition.replace('isnull(', 'COALESCE(')
            
            if 'len(' in postgres_definition:
                postgres_definition = postgres_definition.replace('len(', 'LENGTH(')
            
            if 'upper(' in postgres_definition:
                postgres_definition = postgres_definition.replace('upper(', 'UPPER(')
            
            if 'lower(' in postgres_definition:
                postgres_definition = postgres_definition.replace('lower(', 'LOWER(')
            
            # Обновляем запись
            cursor.execute('''
                UPDATE mcl.postgres_check_constraints 
                SET 
                    postgres_definition = %s,
                    mapping_status = 'mapped',
                    mapping_complexity = 'simple',
                    mapping_notes = 'Автоматический маппинг основных функций'
                WHERE id = %s
            ''', (postgres_definition, constraint_id))
            
            processed_count += 1
            
            if postgres_definition != definition:
                console.print(f'     ✅ Маппинг применен')
            else:
                console.print(f'     ℹ️  Маппинг не требовался')
        
        # Подтверждаем изменения
        conn.commit()
        
        console.print(f'\\n✅ Маппинг завершен успешно!')
        console.print(f'📊 Обработано CHECK constraints: {processed_count}')
        
        return processed_count
        
    except Exception as e:
        console.print(f'❌ Ошибка: {e}')
        conn.rollback()
        return 0
        
    finally:
        conn.close()

if __name__ == '__main__':
    console.print('🚀 Запуск маппинга функций для CHECK CONSTRAINTS...')
    result = map_check_constraints_functions(2)
    console.print(f'\\n🎯 Результат: обработано {result} CHECK constraints')