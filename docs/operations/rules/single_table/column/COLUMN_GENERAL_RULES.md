# 📋 ПРАВИЛА РАБОТЫ С КОЛОНКОЙ

## 🎯 ОБЩИЕ ПРИНЦИПЫ

### 1. **ИСТОЧНИК ДАННЫХ**
- Все операции с колонками выполняются в контексте задачи миграции (`task_id`)
- Основные метаданные: `mcl.mssql_columns` и `mcl.postgres_columns`
- Дополнительные метаданные: `mcl.mssql_derived_types` и `mcl.postgres_derived_types`

### 2. **ПРЕДВАРИТЕЛЬНОЕ РАСПРЕДЕЛЕНИЕ КОЛОНОК**
**⚠️ КРИТИЧЕСКИ ВАЖНО:** Распределение колонок между базовыми таблицами и представлениями происходит на этапе формирования метаданных, а не во время выполнения миграции.

#### Типы распределения:
- **`target_type = 'both'`** - колонка присутствует в базовой таблице и представлении
- **`target_type = 'base_table'`** - колонка только в базовой таблице
- **`target_type = 'view'`** - колонка только в представлении

#### Позиционирование:
- **`base_table_position`** - позиция колонки в базовой таблице
- **`view_position`** - позиция колонки в представлении

#### Логика распределения:
1. **Обычные таблицы** (без вычисляемых колонок):
   - Все колонки имеют `target_type = 'both'`
   - `base_table_position = view_position`

2. **Таблицы с вычисляемыми колонками**:
   - Физические колонки: `target_type = 'both'`
   - Вычисляемые колонки: `target_type = 'view'`
   - Identity колонки: `target_type = 'view'`

### 3. **СТРУКТУРА КОЛОНКИ**
```sql
-- Основные поля колонки
column_name          -- Имя колонки
ordinal_position     -- Порядковый номер
data_type_id         -- Ссылка на тип данных
is_nullable          -- Разрешен ли NULL
is_identity          -- Автоинкремент
is_computed          -- Вычисляемая колонка
has_default_value    -- Признак наличия значения по умолчанию (вычисляемое поле)
```

### 4. **ОБЯЗАТЕЛЬНЫЕ ФИЛЬТРЫ**
Все SQL-запросы должны содержать:
```sql
WHERE task_id = <TASK_ID>  -- Фильтр по задаче миграции
```

## 🔧 ОСНОВНЫЕ ОПЕРАЦИИ

### 1. **ПОЛУЧЕНИЕ СТРУКТУРЫ КОЛОНКИ**
```python
def get_column_structure(column_id: int, task_id: int) -> Dict:
    """
    Получение полной структуры колонки
    
    Args:
        column_id: ID колонки в postgres_columns
        task_id: ID задачи миграции
    
    Returns:
        Dict с полной информацией о колонке
    """
    # Валидация принадлежности колонки к задаче
    if not validate_column_belongs_to_task(column_id, task_id):
        raise ValueError(f"Колонка {column_id} не принадлежит задаче {task_id}")
    
    # Получение основной информации
    cursor.execute('''
        SELECT 
            pc.column_name,
            pc.ordinal_position,
            pc.is_nullable,
            pc.is_identity,
            pc.is_computed,
            pdt.typname_with_params as data_type,
            pc.default_value,
            CASE 
                WHEN EXISTS(
                    SELECT 1 FROM mcl.mssql_default_constraints mdc 
                    JOIN mcl.mssql_columns mc ON mdc.column_id = mc.id
                    WHERE mc.id = pc.source_column_id
                ) THEN true 
                ELSE false 
            END as has_default_constraint
        FROM mcl.postgres_columns pc
        JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
        JOIN mcl.postgres_derived_types pdt ON pc.postgres_data_type_id = pdt.id
        WHERE pc.id = %s AND mc.task_id = %s
    ''', (column_id, task_id))
    
    return cursor.fetchone()
```

### 2. **ВАЛИДАЦИЯ ПРИНАДЛЕЖНОСТИ К ЗАДАЧЕ**
```python
def validate_column_belongs_to_task(column_id: int, task_id: int) -> bool:
    """
    Проверка принадлежности колонки к задаче миграции
    
    Args:
        column_id: ID колонки в postgres_columns
        task_id: ID задачи миграции
    
    Returns:
        bool: True если колонка принадлежит задаче
    """
    cursor.execute('''
        SELECT COUNT(*)
        FROM mcl.postgres_columns pc
        JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
        WHERE pc.id = %s AND mc.task_id = %s
    ''', (column_id, task_id))
    
    return cursor.fetchone()[0] > 0
```

### 3. **ГЕНЕРАЦИЯ DDL ДЛЯ КОЛОНКИ**
```python
def generate_column_ddl(column_id: int, task_id: int) -> str:
    """
    Генерация DDL для отдельной колонки
    
    Args:
        column_id: ID колонки
        task_id: ID задачи миграции
    
    Returns:
        str: DDL определение колонки
    """
    column_info = get_column_structure(column_id, task_id)
    
    # Базовое определение
    ddl_parts = [column_info['column_name'], column_info['data_type']]
    
    # NULL/NOT NULL
    if column_info['is_nullable']:
        ddl_parts.append('NULL')
    else:
        ddl_parts.append('NOT NULL')
    
    # Значение по умолчанию (из таблиц default_constraints)
    if column_info['has_default_constraint']:
        default_value = get_default_constraint_value(column_id, task_id)
        if default_value:
            ddl_parts.append(f'DEFAULT {default_value}')
    
    # Автоинкремент
    if column_info['is_identity']:
        ddl_parts.append('GENERATED ALWAYS AS IDENTITY')
    
    # Вычисляемая колонка
    if column_info['is_computed']:
        computed_expression = get_computed_column_expression(column_id, task_id)
        if computed_expression:
            ddl_parts.append(f'GENERATED ALWAYS AS ({computed_expression}) STORED')
    
    return ' '.join(ddl_parts)
```

## 🔍 СПЕЦИАЛЬНЫЕ СЛУЧАИ

### 1. **ИМЕНА КОЛОНОК С ОСОБЕННОСТЯМИ**
```python
def format_column_name(column_name: str) -> str:
    """
    Форматирование имени колонки для PostgreSQL
    
    Args:
        column_name: Исходное имя колонки
    
    Returns:
        str: Отформатированное имя
    """
    # Кавычки нужны если:
    # - Начинается с цифры
    # - Содержит дефис
    # - Смешанный регистр (не lowercase)
    if (column_name[0].isdigit() or 
        '-' in column_name or 
        column_name != column_name.lower()):
        return f'"{column_name}"'
    
    return column_name
```

### 2. **ТИПЫ ДАННЫХ**
```python
def get_column_data_type(column_id: int, task_id: int) -> str:
    """
    Получение типа данных колонки для PostgreSQL
    
    Args:
        column_id: ID колонки
        task_id: ID задачи миграции
    
    Returns:
        str: Тип данных PostgreSQL
    """
    cursor.execute('''
        SELECT pdt.typname_with_params
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_derived_types pdt ON pc.postgres_data_type_id = pdt.id
        JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
        WHERE pc.id = %s AND mc.task_id = %s
    ''', (column_id, task_id))
    
    result = cursor.fetchone()
    return result[0] if result else 'text'
```

## 📊 ЛОГИРОВАНИЕ И МОНИТОРИНГ

### 1. **ЛОГИРОВАНИЕ ОПЕРАЦИЙ С КОЛОНКАМИ**
```python
def log_column_operation(
    column_id: int, 
    task_id: int, 
    operation: str, 
    status: str, 
    details: str = None
):
    """
    Логирование операций с колонками
    
    Args:
        column_id: ID колонки
        task_id: ID задачи миграции
        operation: Тип операции (CREATE, ALTER, DROP, etc.)
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
            'COLUMN_OPERATION',
            %s,
            %s, 
            %s,
            NOW()
        )
    ''', (task_id, operation, status, details))
```

### 2. **МЕТРИКИ ПО КОЛОНКАМ**
```python
def get_column_metrics(task_id: int) -> Dict:
    """
    Получение метрик по колонкам для задачи
    
    Args:
        task_id: ID задачи миграции
    
    Returns:
        Dict: Статистика по колонкам
    """
    cursor.execute('''
        SELECT 
            COUNT(*) as total_columns,
            COUNT(CASE WHEN is_nullable THEN 1 END) as nullable_columns,
            COUNT(CASE WHEN is_identity THEN 1 END) as identity_columns,
            COUNT(CASE WHEN is_computed THEN 1 END) as computed_columns,
            COUNT(CASE WHEN has_default_constraint THEN 1 END) as default_columns
        FROM mcl.postgres_columns pc
        JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
        WHERE mc.task_id = %s
    ''', (task_id,))
    
    return cursor.fetchone()
```

## ⚠️ ОГРАНИЧЕНИЯ И ПРЕДУПРЕЖДЕНИЯ

### 1. **ОГРАНИЧЕНИЯ POSTGRESQL**
- Максимум 1600 колонок в таблице
- Имена колонок до 63 символов
- Ограничения по типам данных PostgreSQL

### 2. **ПРОВЕРКИ ПЕРЕД ОПЕРАЦИЯМИ**
```python
def validate_column_constraints(column_id: int, task_id: int) -> List[str]:
    """
    Проверка ограничений для колонки
    
    Args:
        column_id: ID колонки
        task_id: ID задачи миграции
    
    Returns:
        List[str]: Список предупреждений
    """
    warnings = []
    column_info = get_column_structure(column_id, task_id)
    
    # Проверка длины имени
    if len(column_info['column_name']) > 63:
        warnings.append(f"Имя колонки слишком длинное: {column_info['column_name']}")
    
    # Проверка типа данных
    if column_info['data_type'] == 'unknown':
        warnings.append(f"Неопределенный тип данных для колонки: {column_info['column_name']}")
    
    return warnings
```

## 🔄 ИНТЕГРАЦИЯ С ДРУГИМИ КОМПОНЕНТАМИ

### 1. **СВЯЗЬ С ТАБЛИЦАМИ**
- Колонки всегда принадлежат таблице
- Операции с колонками влияют на структуру таблицы
- Изменения в колонках требуют обновления DDL таблицы

### 2. **СВЯЗЬ СО ЗНАЧЕНИЯМИ ПО УМОЛЧАНИЮ**
- Признак `has_default_value` вычисляется по наличию записей в `default_constraints`
- Работа со значениями по умолчанию ведется через специализированные функции
- См. файл `DEFAULT_VALUE_RULES.md`

### 3. **СВЯЗЬ С ОГРАНИЧЕНИЯМИ**
- Колонки могут участвовать в PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK
- Изменения в колонках требуют проверки связанных ограничений
- См. соответствующие файлы правил для ограничений