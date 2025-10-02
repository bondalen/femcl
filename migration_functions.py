import psycopg2
from typing import Dict, Optional, Tuple, List
from rich.console import Console

console = Console()

def apply_universal_function_mapping(task_id: int) -> Dict:
    """
    Универсальное применение маппинга функций ко всем типам объектов
    """
    # Подключение к базе данных
    conn = psycopg2.connect(
        dbname='fish_eye',
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432'
    )
    cursor = conn.cursor()
    
    results = {
        'default_constraints_processed': 0,
        'computed_columns_processed': 0,
        'check_constraints_processed': 0,
        'indexes_processed': 0,
        'rules_applied': {},
        'errors': []
    }
    
    try:
        # Обработка default constraints
        process_default_constraints_mapping(task_id, results)
        
        # Обработка computed columns
        process_computed_columns_mapping(task_id, results)
        
        # Обработка CHECK constraints
        process_check_constraints_mapping(task_id, results)
        
        # Обработка индексов
        process_indexes_mapping(task_id, results)
        
    except Exception as e:
        results['errors'].append(f"Ошибка при применении маппинга: {str(e)}")
    
    return results

def process_default_constraints_mapping(task_id: int, results: Dict) -> None:
    """Обработка default constraints"""
    cursor.execute('''
        SELECT 
            pdc.id,
            pdc.definition,
            pt.object_name
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pdc.definition IS NOT NULL
            AND pdc.function_mapping_rule_id IS NULL
    ''', (task_id,))
    
    for constraint_id, definition, table_name in cursor.fetchall():
        rule_id = find_and_apply_mapping_rule(definition, 'default_constraint')
        if rule_id:
            postgres_definition = apply_rule_to_definition(definition, rule_id)
            
            cursor.execute('''
                UPDATE mcl.postgres_default_constraints 
                SET 
                    function_mapping_rule_id = %s,
                    postgres_definition = %s,
                    mapping_status = 'mapped',
                    mapping_complexity = (
                        SELECT CASE 
                            WHEN complexity_level = 1 THEN 'simple'
                            WHEN complexity_level = 2 THEN 'complex'
                            ELSE 'custom'
                        END
                        FROM mcl.function_mapping_rules 
                        WHERE id = %s
                    )
                WHERE id = %s
            ''', (rule_id, postgres_definition, rule_id, constraint_id))
            
            results['default_constraints_processed'] += 1
            results['rules_applied'][rule_id] = results['rules_applied'].get(rule_id, 0) + 1

def process_computed_columns_mapping(task_id: int, results: Dict) -> None:
    """Обработка computed columns"""
    cursor.execute('''
        SELECT 
            pc.id,
            pc.computed_definition,
            pt.object_name,
            pc.column_name
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pc.computed_definition IS NOT NULL
            AND pc.computed_function_mapping_rule_id IS NULL
    ''', (task_id,))
    
    for column_id, definition, table_name, column_name in cursor.fetchall():
        rule_id = find_and_apply_mapping_rule(definition, 'computed_column')
        if rule_id:
            postgres_definition = apply_rule_to_definition(definition, rule_id)
            
            cursor.execute('''
                UPDATE mcl.postgres_columns 
                SET 
                    computed_function_mapping_rule_id = %s,
                    postgres_computed_definition = %s,
                    computed_mapping_status = 'mapped',
                    computed_mapping_complexity = (
                        SELECT CASE 
                            WHEN complexity_level = 1 THEN 'simple'
                            WHEN complexity_level = 2 THEN 'complex'
                            ELSE 'custom'
                        END
                        FROM mcl.function_mapping_rules 
                        WHERE id = %s
                    )
                WHERE id = %s
            ''', (rule_id, postgres_definition, rule_id, column_id))
            
            results['computed_columns_processed'] += 1
            results['rules_applied'][rule_id] = results['rules_applied'].get(rule_id, 0) + 1

def process_check_constraints_mapping(task_id: int, results: Dict) -> None:
    """Обработка CHECK constraints"""
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
    
    for constraint_id, definition, table_name, constraint_name in cursor.fetchall():
        rule_id = find_and_apply_mapping_rule(definition, 'check_constraint')
        if rule_id:
            postgres_definition = apply_rule_to_definition(definition, rule_id)
            
            cursor.execute('''
                UPDATE mcl.postgres_check_constraints 
                SET 
                    function_mapping_rule_id = %s,
                    postgres_definition = %s,
                    mapping_status = 'mapped',
                    mapping_complexity = (
                        SELECT CASE 
                            WHEN complexity_level = 1 THEN 'simple'
                            WHEN complexity_level = 2 THEN 'complex'
                            ELSE 'custom'
                        END
                        FROM mcl.function_mapping_rules 
                        WHERE id = %s
                    )
                WHERE id = %s
            ''', (rule_id, postgres_definition, rule_id, constraint_id))
            
            results['check_constraints_processed'] += 1
            results['rules_applied'][rule_id] = results['rules_applied'].get(rule_id, 0) + 1

def process_indexes_mapping(task_id: int, results: Dict) -> None:
    """Обработка индексов"""
    cursor.execute('''
        SELECT 
            pi.id,
            pi.postgres_definition,
            pt.object_name,
            pi.index_name
        FROM mcl.postgres_indexes pi
        JOIN mcl.postgres_index_columns pic ON pi.id = pic.index_id
        JOIN mcl.postgres_columns pc ON pic.column_id = pc.id
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pi.postgres_definition IS NOT NULL
            AND pi.function_mapping_rule_id IS NULL
    ''', (task_id,))
    
    for index_id, definition, table_name, index_name in cursor.fetchall():
        rule_id = find_and_apply_mapping_rule(definition, 'index')
        if rule_id:
            postgres_definition = apply_rule_to_definition(definition, rule_id)
            
            cursor.execute('''
                UPDATE mcl.postgres_indexes 
                SET 
                    function_mapping_rule_id = %s,
                    postgres_definition = %s,
                    mapping_status = 'mapped',
                    mapping_complexity = (
                        SELECT CASE 
                            WHEN complexity_level = 1 THEN 'simple'
                            WHEN complexity_level = 2 THEN 'complex'
                            ELSE 'custom'
                        END
                        FROM mcl.function_mapping_rules 
                        WHERE id = %s
                    )
                WHERE id = %s
            ''', (rule_id, postgres_definition, rule_id, index_id))
            
            results['indexes_processed'] += 1
            results['rules_applied'][rule_id] = results['rules_applied'].get(rule_id, 0) + 1

def find_and_apply_mapping_rule(definition: str, usage_type: str) -> int:
    """
    Поиск подходящего правила маппинга для определения с учетом типа объекта
    """
    cursor.execute('''
        SELECT 
            id,
            source_function,
            mapping_pattern,
            replacement_pattern,
            mapping_type,
            complexity_level
        FROM mcl.function_mapping_rules
        WHERE is_active = TRUE
            AND %s = ANY(applicable_objects)
        ORDER BY complexity_level, source_function
    ''', (usage_type,))
    
    rules = cursor.fetchall()
    
    for rule_id, source_func, pattern, replacement, mapping_type, complexity in rules:
        if source_func in definition.lower():
            return rule_id
    
    return None

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
        import re
        return re.sub(pattern, replacement, definition, flags=re.IGNORECASE)
    
    return definition

# ============================================================================
# ФУНКЦИИ СИСТЕМЫ МАППИНГА ФУНКЦИЙ
# ============================================================================

def apply_function_mapping(definition: str, rule_id: int) -> str:
    """
    Применение конкретного правила маппинга к определению функции
    
    Args:
        definition: Исходное определение функции
        rule_id: ID правила маппинга
    
    Returns:
        str: Преобразованное определение
    """
    if not definition or not rule_id:
        return definition
    
    cursor.execute('''
        SELECT mapping_pattern, replacement_pattern, mapping_type
        FROM mcl.function_mapping_rules
        WHERE id = %s
    ''', (rule_id,))
    
    result = cursor.fetchone()
    if not result:
        return definition
    
    pattern, replacement, mapping_type = result
    
    if mapping_type == 'direct':
        # Простая замена
        return definition.replace(pattern, replacement)
    elif mapping_type == 'regex':
        # Замена по регулярному выражению
        import re
        return re.sub(pattern, replacement, definition, flags=re.IGNORECASE)
    
    return definition

def map_default_constraints_functions(task_id: int) -> int:
    """
    Применение маппинга функций к default constraints для задачи
    
    Args:
        task_id: ID задачи миграции
    
    Returns:
        int: Количество обработанных default constraints
    """
    processed_count = 0
    
    # Получаем все default constraints с функциями
    cursor.execute('''
        SELECT 
            pdc.id,
            pdc.definition,
            pt.object_name,
            pdc.constraint_name
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pdc.definition IS NOT NULL
            AND pdc.definition ILIKE '%getdate%'
            AND pdc.function_mapping_rule_id IS NULL
    ''', (task_id,))
    
    default_constraints = cursor.fetchall()
    
    # Получаем правило для getdate
    cursor.execute('''
        SELECT id FROM mcl.function_mapping_rules
        WHERE source_function = 'getdate' AND 'default_constraint' = ANY(applicable_objects)
    ''')
    
    getdate_rule = cursor.fetchone()
    if not getdate_rule:
        return 0
    
    getdate_rule_id = getdate_rule[0]
    
    for constraint_id, definition, table_name, constraint_name in default_constraints:
        postgres_definition = apply_function_mapping(definition, getdate_rule_id)
        
        cursor.execute('''
            UPDATE mcl.postgres_default_constraints
            SET
                function_mapping_rule_id = %s,
                postgres_definition = %s,
                mapping_status = 'mapped',
                mapping_complexity = 'simple'
            WHERE id = %s
        ''', (getdate_rule_id, postgres_definition, constraint_id))
        
        processed_count += 1
    
    return processed_count

def map_computed_columns_functions(task_id: int) -> int:
    """
    Применение маппинга функций к computed columns для задачи
    
    Args:
        task_id: ID задачи миграции
    
    Returns:
        int: Количество обработанных computed columns
    """
    processed_count = 0
    
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
        WHERE mt.task_id = %s
            AND pc.computed_definition IS NOT NULL
            AND pc.computed_definition ILIKE ANY(ARRAY['%isnull%', '%len%', '%upper%', '%lower%', '%substring%', '%convert%', '%year%', '%month%', '%day%'])
            AND pc.computed_function_mapping_rule_id IS NULL
    ''', (task_id,))
    
    computed_columns = cursor.fetchall()
    
    # Получаем все правила маппинга
    cursor.execute('''
        SELECT id, source_function, mapping_pattern, replacement_pattern, mapping_type
        FROM mcl.function_mapping_rules
        WHERE is_active = TRUE
            AND 'computed_column' = ANY(applicable_objects)
        ORDER BY complexity_level, source_function
    ''', (task_id,))
    
    mapping_rules = cursor.fetchall()
    
    for column_id, definition, table_name, column_name in computed_columns:
        # Ищем подходящее правило для каждой функции в определении
        matched_rule = None
        postgres_definition = definition
        
        for rule_id, source_func, pattern, replacement, mapping_type in mapping_rules:
            # Проверяем, содержится ли исходная функция в определении
            if re.search(r'\b' + re.escape(source_func) + r'\b', definition, re.IGNORECASE):
                matched_rule = rule_id
                postgres_definition = apply_function_mapping(postgres_definition, rule_id)
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
            
            processed_count += 1
    
    return processed_count

def map_check_constraints_functions(task_id: int) -> int:
    """
    Применение маппинга функций к CHECK constraints для задачи
    
    Args:
        task_id: ID задачи миграции
    
    Returns:
        int: Количество обработанных CHECK constraints
    """
    processed_count = 0
    
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
    
    # Получаем все правила маппинга для CHECK constraints
    cursor.execute('''
        SELECT id, source_function, mapping_pattern, replacement_pattern, mapping_type
        FROM mcl.function_mapping_rules
        WHERE is_active = TRUE
            AND 'check_constraint' = ANY(applicable_objects)
        ORDER BY complexity_level, source_function
    ''')
    
    mapping_rules = cursor.fetchall()
    
    for constraint_id, definition, table_name, constraint_name in check_constraints:
        # Ищем подходящее правило для каждой функции в определении
        matched_rule = None
        postgres_definition = definition
        
        for rule_id, source_func, pattern, replacement, mapping_type in mapping_rules:
            # Проверяем, содержится ли исходная функция в определении
            if re.search(r'\b' + re.escape(source_func) + r'\b', definition, re.IGNORECASE):
                matched_rule = rule_id
                postgres_definition = apply_function_mapping(postgres_definition, rule_id)
                break
        
        if matched_rule:
            cursor.execute('''
                UPDATE mcl.postgres_check_constraints
                SET
                    function_mapping_rule_id = %s,
                    postgres_definition = %s,
                    mapping_status = 'mapped',
                    mapping_complexity = 'simple'
                WHERE id = %s
            ''', (matched_rule, postgres_definition, constraint_id))
            
            processed_count += 1
    
    return processed_count

def map_indexes_functions(task_id: int) -> int:
    """
    Применение маппинга функций к индексам для задачи
    
    Args:
        task_id: ID задачи миграции
    
    Returns:
        int: Количество обработанных индексов
    """
    processed_count = 0
    
    # Получаем все индексы с функциями
    cursor.execute('''
        SELECT 
            pi.id,
            pi.postgres_definition,
            pt.object_name,
            pi.index_name
        FROM mcl.postgres_indexes pi
        JOIN mcl.postgres_index_columns pic ON pi.id = pic.index_id
        JOIN mcl.postgres_columns pc ON pic.column_id = pc.id
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pi.postgres_definition IS NOT NULL
            AND pi.function_mapping_rule_id IS NULL
    ''', (task_id,))
    
    indexes = cursor.fetchall()
    
    # Получаем все правила маппинга для индексов
    cursor.execute('''
        SELECT id, source_function, mapping_pattern, replacement_pattern, mapping_type
        FROM mcl.function_mapping_rules
        WHERE is_active = TRUE
            AND 'index' = ANY(applicable_objects)
        ORDER BY complexity_level, source_function
    ''')
    
    mapping_rules = cursor.fetchall()
    
    for index_id, definition, table_name, index_name in indexes:
        # Ищем подходящее правило для каждой функции в определении
        matched_rule = None
        postgres_definition = definition
        
        for rule_id, source_func, pattern, replacement, mapping_type in mapping_rules:
            # Проверяем, содержится ли исходная функция в определении
            if re.search(r'\b' + re.escape(source_func) + r'\b', definition, re.IGNORECASE):
                matched_rule = rule_id
                postgres_definition = apply_function_mapping(postgres_definition, rule_id)
                break
        
        if matched_rule:
            cursor.execute('''
                UPDATE mcl.postgres_indexes
                SET
                    function_mapping_rule_id = %s,
                    postgres_definition = %s,
                    mapping_status = 'mapped',
                    mapping_complexity = 'simple'
                WHERE id = %s
            ''', (matched_rule, postgres_definition, index_id))
            
            processed_count += 1
    
    return processed_count

def get_function_mapping_statistics(task_id: int) -> Dict:
    """
    Получение статистики применения маппинга функций для задачи
    
    Args:
        task_id: ID задачи миграции
    
    Returns:
        Dict: Статистика маппинга
    """
    cursor.execute('''
        SELECT 
            COUNT(*) as total_with_functions,
            COUNT(function_mapping_rule_id) as mapped
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pdc.definition IS NOT NULL
            AND pdc.definition ILIKE '%getdate%'
    ''', (task_id,))
    
    default_stats = cursor.fetchone()
    
    cursor.execute('''
        SELECT
            COUNT(*) as total_with_functions,
            COUNT(computed_function_mapping_rule_id) as mapped
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pc.computed_definition IS NOT NULL
            AND pc.computed_definition ILIKE ANY(ARRAY['%isnull%', '%len%', '%upper%', '%lower%', '%substring%', '%convert%', '%year%', '%month%', '%day%'])
    ''', (task_id,))
    
    computed_stats = cursor.fetchone()
    
    total_cases = default_stats[0] + computed_stats[0]
    total_mapped = default_stats[1] + computed_stats[1]
    coverage_percentage = (total_mapped / total_cases * 100) if total_cases > 0 else 0
    
    return {
        'default_constraints': {
            'total': default_stats[0],
            'mapped': default_stats[1]
        },
        'computed_columns': {
            'total': computed_stats[0],
            'mapped': computed_stats[1]
        },
        'total_cases': total_cases,
        'total_mapped': total_mapped,
        'coverage_percentage': coverage_percentage
    }

def validate_function_mapping_coverage(task_id: int) -> bool:
    """
    Валидация полного покрытия маппинга функций для задачи
    
    Args:
        task_id: ID задачи миграции
    
    Returns:
        bool: True если покрытие полное (100%)
    """
    stats = get_function_mapping_statistics(task_id)
    return stats['coverage_percentage'] == 100.0

# ... existing code ...