# 🎯 ПРАВИЛА РАБОТЫ СО ЗНАЧЕНИЯМИ ПО УМОЛЧАНИЮ

## 🎯 ОСНОВНЫЕ ПРИНЦИПЫ

### 1. **ЕДИНСТВЕННЫЙ ИСТОЧНИК ИСТИНЫ**
- **Основные метаданные**: `mcl.mssql_default_constraints` и `mcl.postgres_default_constraints`
- **Признак наличия**: Вычисляемое поле `has_default_value` в таблицах колонок
- **Удаление дублирования**: Поле `default_value` в таблицах колонок **НЕ ИСПОЛЬЗУЕТСЯ**

### 2. **СТРУКТУРА МЕТАДАННЫХ**
```sql
-- Исходные ограничения DEFAULT (НОРМАЛИЗОВАННАЯ МОДЕЛЬ)
mcl.mssql_default_constraints (
    id,
    column_id,          -- Ссылка на mssql_columns (ЕДИНСТВЕННАЯ связь)
    constraint_name,    -- Имя ограничения
    definition,         -- Определение значения (например, (getdate()))
    is_system_named,    -- Системное имя
    created_at,
    updated_at
)

-- Целевые ограничения DEFAULT (НОРМАЛИЗОВАННАЯ МОДЕЛЬ)
mcl.postgres_default_constraints (
    id,
    column_id,          -- Ссылка на postgres_columns (ЕДИНСТВЕННАЯ связь)
    source_default_constraint_id, -- Ссылка на mssql_default_constraints
    constraint_name,    -- Целевое имя ограничения
    original_constraint_name,     -- Оригинальное имя
    definition,         -- Исходное определение
    postgres_definition,-- PostgreSQL определение (после маппинга функций)
    function_mapping_rule_id,     -- FK на function_mapping_rules
    mapping_status,     -- Статус маппинга функций
    mapping_complexity, -- Сложность маппинга
    migration_status,   -- Статус миграции
    migration_date,     -- Дата миграции
    error_message,      -- Сообщение об ошибке
    created_at,
    updated_at
)

-- Представление для удобства запросов по таблицам (НОРМАЛИЗОВАННАЯ ВЕРСИЯ)
CREATE VIEW mcl.v_postgres_default_constraints_by_table AS
SELECT 
    pt.id as table_id,
    pt.object_name as table_name,
    pt.schema_name,
    pc.id as column_id,
    pc.column_name,
    pdc.id as constraint_id,
    pdc.constraint_name,
    pdc.definition,
    pdc.postgres_definition,
    pdc.migration_status,
    pdc.function_mapping_rule_id
FROM mcl.postgres_default_constraints pdc
JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id;

-- Представление для удобства запросов по таблицам
CREATE VIEW mcl.v_default_constraints_by_table AS
SELECT 
    pt.id as table_id,
    pt.object_name as table_name,
    pt.schema_name,
    pc.id as column_id,
    pc.column_name,
    pdc.id as constraint_id,
    pdc.constraint_name,
    pdc.definition,
    pdc.postgres_definition,
    pdc.migration_status,
    pdc.function_mapping_rule_id
FROM mcl.postgres_default_constraints pdc
JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id;
```

### 3. **ПРИНЦИПЫ НОРМАЛИЗОВАННОЙ МОДЕЛИ**
- **Единственная связь**: `column_id → postgres_columns.id`
- **Логическая корректность**: Default constraint принадлежит колонке, а не таблице
- **Представление для удобства**: `v_default_constraints_by_table` для запросов по таблицам
- **Оптимизация**: Индекс на `column_id` для быстрых запросов

### 4. **ОБЯЗАТЕЛЬНЫЕ ФИЛЬТРЫ**
Все SQL-запросы должны содержать:
```sql
WHERE task_id = <TASK_ID>  -- Фильтр по задаче миграции
```

### 5. **ЗАПРОСЫ С ИСПОЛЬЗОВАНИЕМ ПРЕДСТАВЛЕНИЯ**
```python
def get_table_default_constraints_via_view(table_name: str, task_id: int) -> List[Dict]:
    """
    Получение всех значений по умолчанию для таблицы через представление
    
    Args:
        table_name: Имя таблицы
        task_id: ID задачи миграции
    
    Returns:
        List[Dict]: Список значений по умолчанию
    """
    cursor.execute('''
        SELECT 
            table_id,
            table_name,
            column_name,
            constraint_id,
            constraint_name,
            definition,
            postgres_definition,
            migration_status
        FROM mcl.v_default_constraints_by_table vdc
        JOIN mcl.mssql_tables mt ON vdc.table_name = mt.object_name
        WHERE mt.task_id = %s AND vdc.table_name = %s
        ORDER BY column_name
    ''', (task_id, table_name))
    
    return [
        {
            'table_id': row[0],
            'table_name': row[1],
            'column_name': row[2],
            'constraint_id': row[3],
            'constraint_name': row[4],
            'definition': row[5],
            'postgres_definition': row[6],
            'migration_status': row[7]
        }
        for row in cursor.fetchall()
    ]
```

## 🔧 ОСНОВНЫЕ ОПЕРАЦИИ

### 1. **ПОЛУЧЕНИЕ ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ**
```python
def get_default_constraint_value(column_id: int, task_id: int) -> str:
    """
    Получение значения по умолчанию для колонки
    
    Args:
        column_id: ID колонки в postgres_columns
        task_id: ID задачи миграции
    
    Returns:
        str: Определение значения по умолчанию или None
    """
    cursor.execute('''
        SELECT pdc.definition
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
        JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
        WHERE pc.id = %s AND mc.task_id = %s
        ORDER BY pdc.id
        LIMIT 1
    ''', (column_id, task_id))
    
    result = cursor.fetchone()
    return result[0] if result else None
```

### 2. **ПРОВЕРКА НАЛИЧИЯ ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ**
```python
def has_default_constraint(column_id: int, task_id: int) -> bool:
    """
    Проверка наличия значения по умолчанию для колонки
    
    Args:
        column_id: ID колонки в postgres_columns
        task_id: ID задачи миграции
    
    Returns:
        bool: True если есть значение по умолчанию
    """
    cursor.execute('''
        SELECT COUNT(*)
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
        JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
        WHERE pc.id = %s AND mc.task_id = %s
    ''', (column_id, task_id))
    
    return cursor.fetchone()[0] > 0
```

### 3. **ПОЛУЧЕНИЕ ВСЕХ ЗНАЧЕНИЙ ПО УМОЛЧАНИЮ ДЛЯ ТАБЛИЦЫ**
```python
def get_table_default_constraints(table_id: int, task_id: int) -> List[Dict]:
    """
    Получение всех значений по умолчанию для таблицы
    
    Args:
        table_id: ID таблицы в postgres_tables
        task_id: ID задачи миграции
    
    Returns:
        List[Dict]: Список значений по умолчанию
    """
    cursor.execute('''
        SELECT 
            pc.column_name,
            pdc.constraint_name,
            pdc.definition,
            pdc.migration_status,
            pdc.error_message
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
        JOIN mcl.mssql_tables mt ON pc.source_table_id = mt.id
        WHERE mt.id = %s AND mt.task_id = %s
        ORDER BY pc.ordinal_position
    ''', (table_id, task_id))
    
    return [
        {
            'column_name': row[0],
            'constraint_name': row[1],
            'definition': row[2],
            'migration_status': row[3],
            'error_message': row[4]
        }
        for row in cursor.fetchall()
    ]
```

## 🔄 ПРЕОБРАЗОВАНИЕ ФУНКЦИЙ

### 1. **МАППИНГ ФУНКЦИЙ MS SQL → POSTGRESQL**
```python
def get_function_mappings() -> Dict[str, str]:
    """
    Получение маппинга функций MS SQL Server → PostgreSQL
    
    Returns:
        Dict[str, str]: Словарь маппинга функций
    """
    return {
        'getdate()': 'CURRENT_TIMESTAMP',
        'getutcdate()': 'CURRENT_TIMESTAMP AT TIME ZONE \'UTC\'',
        'newid()': 'gen_random_uuid()',
        'newsequentialid()': 'gen_random_uuid()',
        'isnull(expr1, expr2)': 'COALESCE(expr1, expr2)',
        'len(string)': 'length(string)',
        'substring(string, start, length)': 'substring(string FROM start FOR length)',
        'charindex(substring, string)': 'position(substring IN string)',
        'patindex(pattern, string)': 'position(substring(string FROM pattern) IN string)',
        'dateadd(part, number, date)': 'date + interval \'number part\'',
        'datediff(part, startdate, enddate)': 'EXTRACT(part FROM enddate - startdate)',
        'datename(part, date)': 'to_char(date, \'part\')',
        'datepart(part, date)': 'EXTRACT(part FROM date)',
        'convert(data_type, expression)': 'expression::data_type',
        'cast(expression AS data_type)': 'expression::data_type'
    }
```

### 2. **ПРЕОБРАЗОВАНИЕ ОПРЕДЕЛЕНИЯ ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ**
```python
def transform_default_definition(definition: str) -> str:
    """
    Преобразование определения значения по умолчанию из MS SQL в PostgreSQL
    
    Args:
        definition: Исходное определение (например, "(getdate())")
    
    Returns:
        str: Преобразованное определение для PostgreSQL
    """
    if not definition:
        return None
    
    # Убираем внешние скобки
    definition = definition.strip()
    if definition.startswith('(') and definition.endswith(')'):
        definition = definition[1:-1]
    
    # Получаем маппинг функций
    function_mappings = get_function_mappings()
    
    # Применяем маппинг
    transformed = definition
    for mssql_func, postgres_func in function_mappings.items():
        # Простое замещение (можно улучшить с помощью regex)
        transformed = transformed.replace(mssql_func, postgres_func)
    
    # Дополнительные преобразования
    transformed = transform_sql_syntax(transformed)
    
    return f"({transformed})" if transformed else None

def transform_sql_syntax(sql_expr: str) -> str:
    """
    Дополнительные преобразования синтаксиса SQL
    
    Args:
        sql_expr: SQL выражение
    
    Returns:
        str: Преобразованное выражение
    """
    import re
    
    # Преобразование dateadd
    # dateadd(day, 1, getdate()) → getdate() + interval '1 day'
    dateadd_pattern = r"dateadd\s*\(\s*(\w+)\s*,\s*(\d+)\s*,\s*([^)]+)\s*\)"
    def replace_dateadd(match):
        part = match.group(1)
        number = match.group(2)
        date_expr = match.group(3)
        
        # Маппинг частей даты
        part_mapping = {
            'year': 'year',
            'month': 'month', 
            'day': 'day',
            'hour': 'hour',
            'minute': 'minute',
            'second': 'second'
        }
        
        postgres_part = part_mapping.get(part.lower(), part)
        return f"{date_expr} + interval '{number} {postgres_part}'"
    
    sql_expr = re.sub(dateadd_pattern, replace_dateadd, sql_expr, flags=re.IGNORECASE)
    
    return sql_expr
```

## 📊 СОЗДАНИЕ И ОБНОВЛЕНИЕ ЗНАЧЕНИЙ ПО УМОЛЧАНИЮ

### 1. **СОЗДАНИЕ ЗАПИСИ О ЗНАЧЕНИИ ПО УМОЛЧАНИЮ**
```python
def create_default_constraint(
    column_id: int, 
    task_id: int, 
    definition: str,
    constraint_name: str = None
) -> int:
    """
    Создание записи о значении по умолчанию
    
    Args:
        column_id: ID колонки в postgres_columns
        task_id: ID задачи миграции
        definition: Определение значения по умолчанию
        constraint_name: Имя ограничения (опционально)
    
    Returns:
        int: ID созданной записи
    """
    # Получаем информацию о колонке
    cursor.execute('''
        SELECT pc.table_id, pc.source_column_id
        FROM mcl.postgres_columns pc
        JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
        WHERE pc.id = %s AND mc.task_id = %s
    ''', (column_id, task_id))
    
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"Колонка {column_id} не найдена для задачи {task_id}")
    
    table_id, source_column_id = result
    
    # Получаем исходное ограничение
    cursor.execute('''
        SELECT id, constraint_name
        FROM mcl.mssql_default_constraints
        WHERE column_id = %s
        ORDER BY id
        LIMIT 1
    ''', (source_column_id,))
    
    source_constraint = cursor.fetchone()
    source_constraint_id = source_constraint[0] if source_constraint else None
    original_name = source_constraint[1] if source_constraint else None
    
    # Генерируем имя ограничения
    if not constraint_name:
        constraint_name = generate_postgres_constraint_name(column_id, task_id)
    
    # Преобразуем определение
    transformed_definition = transform_default_definition(definition)
    
    # Создаем запись
    cursor.execute('''
        INSERT INTO mcl.postgres_default_constraints (
            table_id,
            column_id,
            source_default_constraint_id,
            constraint_name,
            original_constraint_name,
            definition,
            migration_status,
            created_at,
            updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, 'PENDING', NOW(), NOW()
        )
        RETURNING id
    ''', (table_id, column_id, source_constraint_id, constraint_name, 
          original_name, transformed_definition))
    
    return cursor.fetchone()[0]
```

### 2. **ГЕНЕРАЦИЯ ИМЕНИ ОГРАНИЧЕНИЯ**
```python
def generate_postgres_constraint_name(column_id: int, task_id: int) -> str:
    """
    Генерация имени ограничения для PostgreSQL
    
    Args:
        column_id: ID колонки
        task_id: ID задачи миграции
    
    Returns:
        str: Имя ограничения
    """
    # Получаем информацию о таблице и колонке
    cursor.execute('''
        SELECT 
            pt.object_name,
            pc.column_name
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
        WHERE pc.id = %s AND mc.task_id = %s
    ''', (column_id, task_id))
    
    result = cursor.fetchone()
    if not result:
        return f"df_default_{column_id}"
    
    table_name, column_name = result
    
    # Генерируем имя в стиле PostgreSQL
    constraint_name = f"df_{table_name}_{column_name}"
    
    # Ограничиваем длину и приводим к lowercase
    constraint_name = constraint_name.lower()[:63]
    
    # Заменяем недопустимые символы
    import re
    constraint_name = re.sub(r'[^a-z0-9_]', '_', constraint_name)
    
    return constraint_name
```

## 🔍 ВАЛИДАЦИЯ И ПРОВЕРКИ

### 1. **ВАЛИДАЦИЯ ОПРЕДЕЛЕНИЯ ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ**
```python
def validate_default_definition(definition: str) -> Dict[str, Any]:
    """
    Валидация определения значения по умолчанию
    
    Args:
        definition: Определение для проверки
    
    Returns:
        Dict: Результат валидации
    """
    result = {
        'is_valid': True,
        'warnings': [],
        'errors': [],
        'transformed_definition': None
    }
    
    if not definition:
        result['errors'].append("Определение не может быть пустым")
        result['is_valid'] = False
        return result
    
    try:
        # Пытаемся преобразовать
        transformed = transform_default_definition(definition)
        result['transformed_definition'] = transformed
        
        # Проверяем на наличие неподдерживаемых функций
        unsupported_functions = check_unsupported_functions(definition)
        if unsupported_functions:
            result['warnings'].extend([
                f"Неподдерживаемая функция: {func}" 
                for func in unsupported_functions
            ])
        
        # Проверяем синтаксис PostgreSQL
        if not validate_postgres_syntax(transformed):
            result['errors'].append("Некорректный синтаксис PostgreSQL")
            result['is_valid'] = False
            
    except Exception as e:
        result['errors'].append(f"Ошибка преобразования: {str(e)}")
        result['is_valid'] = False
    
    return result

def check_unsupported_functions(definition: str) -> List[str]:
    """
    Проверка на неподдерживаемые функции
    
    Args:
        definition: Определение для проверки
    
    Returns:
        List[str]: Список неподдерживаемых функций
    """
    unsupported = []
    
    # Список неподдерживаемых функций
    unsupported_patterns = [
        r'\buser_name\b',
        r'\bsystem_user\b',
        r'\bhost_name\b',
        r'\bapp_name\b',
        r'\b@@version\b',
        r'\b@@servername\b'
    ]
    
    import re
    for pattern in unsupported_patterns:
        if re.search(pattern, definition, re.IGNORECASE):
            match = re.search(pattern, definition, re.IGNORECASE)
            unsupported.append(match.group(0))
    
    return unsupported

def validate_postgres_syntax(definition: str) -> bool:
    """
    Базовая валидация синтаксиса PostgreSQL
    
    Args:
        definition: Определение для проверки
    
    Returns:
        bool: True если синтаксис корректный
    """
    # Убираем внешние скобки для проверки
    expr = definition.strip()
    if expr.startswith('(') and expr.endswith(')'):
        expr = expr[1:-1]
    
    # Простые проверки
    if not expr:
        return False
    
    # Проверяем на наличие незакрытых скобок
    if expr.count('(') != expr.count(')'):
        return False
    
    # Проверяем на наличие кавычек
    if expr.count("'") % 2 != 0:
        return False
    
    return True
```

## 📈 ЛОГИРОВАНИЕ И МОНИТОРИНГ

### 1. **ЛОГИРОВАНИЕ ОПЕРАЦИЙ СО ЗНАЧЕНИЯМИ ПО УМОЛЧАНИЮ**
```python
def log_default_constraint_operation(
    constraint_id: int,
    task_id: int,
    operation: str,
    status: str,
    details: str = None
):
    """
    Логирование операций со значениями по умолчанию
    
    Args:
        constraint_id: ID ограничения
        task_id: ID задачи миграции
        operation: Тип операции (CREATE, UPDATE, DELETE, MIGRATE)
        status: Статус операции (SUCCESS, ERROR, WARNING)
        details: Дополнительные детали
    """
    cursor.execute('''
        INSERT INTO mcl.migration_events (
            task_id,
            event_type,
            event_subtype,
            status,
            message,
            created_at
        ) VALUES (
            %s,
            'DEFAULT_CONSTRAINT_OPERATION',
            %s,
            %s,
            %s,
            NOW()
        )
    ''', (task_id, operation, status, details))
```

### 2. **МЕТРИКИ ПО ЗНАЧЕНИЯМ ПО УМОЛЧАНИЮ**
```python
def get_default_constraint_metrics(task_id: int) -> Dict:
    """
    Получение метрик по значениям по умолчанию для задачи
    
    Args:
        task_id: ID задачи миграции
    
    Returns:
        Dict: Статистика по значениям по умолчанию
    """
    cursor.execute('''
        SELECT 
            COUNT(*) as total_constraints,
            COUNT(CASE WHEN migration_status = 'SUCCESS' THEN 1 END) as migrated,
            COUNT(CASE WHEN migration_status = 'ERROR' THEN 1 END) as failed,
            COUNT(CASE WHEN migration_status = 'PENDING' THEN 1 END) as pending,
            COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as with_errors
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
        JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
        WHERE mc.task_id = %s
    ''', (task_id,))
    
    result = cursor.fetchone()
    return {
        'total_constraints': result[0],
        'migrated': result[1],
        'failed': result[2],
        'pending': result[3],
        'with_errors': result[4]
    }
```

## ⚠️ ОГРАНИЧЕНИЯ И ПРЕДУПРЕЖДЕНИЯ

### 1. **ОГРАНИЧЕНИЯ POSTGRESQL**
- Значения по умолчанию должны быть константами или функциями без параметров
- Некоторые функции MS SQL Server не имеют прямых аналогов в PostgreSQL
- Ограничения на длину определений

### 2. **РЕКОМЕНДАЦИИ**
- Всегда проверяйте преобразованные определения перед применением
- Логируйте все операции для отладки
- Используйте тестирование на небольших наборах данных
- Подготавливайте fallback-решения для неподдерживаемых функций

### 3. **ИНТЕГРАЦИЯ С ДРУГИМИ КОМПОНЕНТАМИ**
- Значения по умолчанию влияют на DDL таблиц
- При изменении значений по умолчанию требуется обновление DDL
- См. файл `COLUMN_GENERAL_RULES.md` для интеграции с колонками

---

## 🎯 ИНТЕГРАЦИЯ С СИСТЕМОЙ МАППИНГА ФУНКЦИЙ

**⚠️ КРИТИЧЕСКИ ВАЖНО:** Система маппинга функций интегрирована в работу со значениями по умолчанию для автоматического преобразования MS SQL Server функций в PostgreSQL эквиваленты.

### Расширенная структура метаданных:
```sql
-- Целевые ограничения DEFAULT с интеграцией маппинга
mcl.postgres_default_constraints (
    id,
    table_id,                    -- Ссылка на postgres_tables
    column_id,                   -- Ссылка на postgres_columns
    source_default_constraint_id, -- Ссылка на mssql_default_constraints
    constraint_name,             -- Целевое имя ограничения
    original_constraint_name,    -- Оригинальное имя
    definition,                  -- Исходное определение (например, (getdate()))
    postgres_definition,         -- PostgreSQL определение (например, (NOW()))
    function_mapping_rule_id,    -- FK на mcl.function_mapping_rules
    mapping_status,              -- 'pending', 'mapped', 'error'
    mapping_complexity,          -- 'simple', 'complex', 'manual'
    migration_status,            -- Статус миграции
    migration_date,              -- Дата миграции
    error_message,               -- Сообщение об ошибке
    created_at,
    updated_at
)
```

### Автоматическое применение маппинга:
```python
def get_default_constraint_with_mapping(column_id: int, task_id: int) -> Dict:
    """
    Получение значения по умолчанию с применением маппинга функций
    
    Args:
        column_id: ID колонки в postgres_columns
        task_id: ID задачи миграции
    
    Returns:
        Dict: Определение с примененным маппингом
    """
    cursor.execute('''
        SELECT 
            pdc.definition as original_definition,
            pdc.postgres_definition,
            fmr.source_function,
            fmr.target_function,
            pdc.mapping_status,
            pdc.mapping_complexity
        FROM mcl.postgres_default_constraints pdc
        LEFT JOIN mcl.function_mapping_rules fmr ON pdc.function_mapping_rule_id = fmr.id
        JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
        JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
        WHERE pc.id = %s AND mc.task_id = %s
        ORDER BY pdc.id
        LIMIT 1
    ''', (column_id, task_id))
    
    result = cursor.fetchone()
    if not result:
        return None
    
    return {
        'original_definition': result[0],
        'postgres_definition': result[1],
        'source_function': result[2],
        'target_function': result[3],
        'mapping_status': result[4],
        'mapping_complexity': result[5],
        'use_definition': result[1] or result[0]  # Используем postgres_definition если есть
    }
```

### Генерация DDL с маппингом:
```python
def generate_default_constraint_ddl_with_mapping(constraint_id: int) -> str:
    """
    Генерация DDL для default constraint с использованием postgres_definition
    
    Args:
        constraint_id: ID ограничения в postgres_default_constraints
    
    Returns:
        str: DDL команда для создания ограничения
    """
    cursor.execute('''
        SELECT 
            pdc.constraint_name,
            pdc.postgres_definition,
            pc.column_name,
            pt.object_name
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
        JOIN mcl.postgres_tables pt ON pdc.table_id = pt.id
        WHERE pdc.id = %s
    ''', (constraint_id,))
    
    result = cursor.fetchone()
    if not result:
        return None
    
    constraint_name, postgres_definition, column_name, table_name = result
    
    # Используем postgres_definition (уже содержит преобразованные функции)
    definition = postgres_definition or "NULL"
    
    return f"ALTER TABLE ags.{table_name} ALTER COLUMN {column_name} SET DEFAULT {definition};"
```

### Статистика маппинга для default constraints:
```python
def get_default_constraint_mapping_statistics(task_id: int) -> Dict:
    """
    Получение статистики маппинга функций для default constraints
    
    Args:
        task_id: ID задачи миграции
    
    Returns:
        Dict: Статистика маппинга
    """
    cursor.execute('''
        SELECT 
            COUNT(*) as total_constraints,
            COUNT(postgres_definition) as with_postgres_definition,
            COUNT(function_mapping_rule_id) as with_mapping_rule,
            COUNT(CASE WHEN mapping_status = 'mapped' THEN 1 END) as mapped,
            COUNT(CASE WHEN mapping_status = 'error' THEN 1 END) as mapping_errors
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
        JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
        WHERE mc.task_id = %s
    ''', (task_id,))
    
    result = cursor.fetchone()
    return {
        'total_constraints': result[0],
        'with_postgres_definition': result[1],
        'with_mapping_rule': result[2],
        'mapped': result[3],
        'mapping_errors': result[4],
        'coverage_percentage': (result[3] / result[0] * 100) if result[0] > 0 else 0
    }
```

### Примеры маппинга для default constraints:
- **`getdate()` → `NOW()`**: 17 случаев в задаче ID=2
- **`getutcdate()` → `CURRENT_TIMESTAMP AT TIME ZONE 'UTC'`**
- **`newid()` → `gen_random_uuid()`**
- **`newsequentialid()` → `gen_random_uuid()`**

### Интеграция с процессами миграции:
1. **На этапе формирования метаданных**: Автоматическое применение правил маппинга
2. **При генерации DDL**: Использование `postgres_definition` вместо `definition`
3. **При валидации**: Проверка корректности преобразованных определений
4. **При логировании**: Отслеживание применения правил маппинга

---

## 🔄 **ИЗМЕНЕНИЯ ПОСЛЕ НОРМАЛИЗАЦИИ МЕТАДАННЫХ**

### **✅ Ключевые изменения:**

1. **Удален `table_id`** из `mcl.postgres_default_constraints`
2. **Создано представление** `v_postgres_default_constraints_by_table`
3. **Все запросы обновлены** для работы с новой архитектурой
4. **Поддержка множественных колонок** через `_columns` таблицы

### **📋 Примеры правильных запросов:**

```sql
-- ✅ ПРАВИЛЬНО: Связь через column_id
SELECT 
    pdc.id,
    pdc.definition,
    pt.object_name,
    pc.column_name
FROM mcl.postgres_default_constraints pdc
JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id

-- ✅ ПРАВИЛЬНО: Использование представления
SELECT * FROM mcl.v_postgres_default_constraints_by_table
WHERE table_name = 'accnt'
```

### **📚 Связанные документы:**
- `NORMALIZED_QUERY_EXAMPLES.md` - Примеры правильных запросов
- `NORMALIZATION_COMPLETION_REPORT.md` - Отчет о нормализации
- `MULTIPLE_COLUMNS_VERIFICATION_REPORT.md` - Проверка множественных колонок

### Функции системы маппинга для default constraints:
- `map_default_constraints_functions(task_id: int) -> int`
- `apply_function_mapping_to_default_constraint(constraint_id: int) -> bool`
- `validate_default_constraint_mapping(constraint_id: int) -> bool`