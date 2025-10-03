# 🔄 ПРЕДЛОЖЕНИЕ ПО РЕСТРУКТУРИЗАЦИИ МЕТАДАННЫХ

## 🎯 ПРОБЛЕМА

### Текущее состояние:
- **Дублирование данных**: Информация о значениях по умолчанию хранится в двух местах:
  - `mcl.mssql_columns.default_value` и `mcl.postgres_columns.default_value` (49 записей)
  - `mcl.mssql_default_constraints` и `mcl.postgres_default_constraints` (5 записей)
- **Неконсистентность**: 44 записи имеют `default_value` в колонках, но не имеют соответствующих записей в `default_constraints`
- **Сложность поддержки**: Два источника истины создают риск рассинхронизации данных

## 🔧 ПРЕДЛАГАЕМОЕ РЕШЕНИЕ

### 1. **УДАЛЕНИЕ ДУБЛИРОВАНИЯ**

#### A. Изменения в таблицах колонок:
```sql
-- УДАЛИТЬ поля default_value из таблиц колонок
ALTER TABLE mcl.mssql_columns DROP COLUMN default_value;
ALTER TABLE mcl.postgres_columns DROP COLUMN default_value;

-- ДОБАВИТЬ вычисляемое поле has_default_value
ALTER TABLE mcl.mssql_columns 
ADD COLUMN has_default_value BOOLEAN GENERATED ALWAYS AS (
    EXISTS (
        SELECT 1 FROM mcl.mssql_default_constraints mdc 
        WHERE mdc.column_id = mssql_columns.id
    )
) STORED;

ALTER TABLE mcl.postgres_columns 
ADD COLUMN has_default_value BOOLEAN GENERATED ALWAYS AS (
    EXISTS (
        SELECT 1 FROM mcl.postgres_default_constraints pdc 
        WHERE pdc.column_id = postgres_columns.id
    )
) STORED;
```

#### B. Дополнение таблиц default_constraints:
```sql
-- СОЗДАТЬ недостающие записи в mssql_default_constraints
INSERT INTO mcl.mssql_default_constraints (
    table_id, 
    column_id, 
    constraint_name, 
    definition,
    is_system_named,
    created_at,
    updated_at
)
SELECT 
    mc.table_id,
    mc.id as column_id,
    CASE 
        WHEN mc.default_value IS NOT NULL AND mc.default_value != '' 
        THEN 'DF_' || mt.object_name || '_' || mc.column_name
        ELSE NULL
    END as constraint_name,
    mc.default_value as definition,
    true as is_system_named,
    NOW() as created_at,
    NOW() as updated_at
FROM mcl.mssql_columns mc
JOIN mcl.mssql_tables mt ON mc.table_id = mt.id
WHERE mc.default_value IS NOT NULL 
    AND mc.default_value != ''
    AND NOT EXISTS (
        SELECT 1 FROM mcl.mssql_default_constraints mdc 
        WHERE mdc.column_id = mc.id
    );

-- СОЗДАТЬ соответствующие записи в postgres_default_constraints
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
)
SELECT 
    pt.id as table_id,
    pc.id as column_id,
    mdc.id as source_default_constraint_id,
    LOWER('df_' || pt.object_name || '_' || pc.column_name) as constraint_name,
    mdc.constraint_name as original_constraint_name,
    mdc.definition as definition,  -- Будет преобразовано позже
    'PENDING' as migration_status,
    NOW() as created_at,
    NOW() as updated_at
FROM mcl.mssql_default_constraints mdc
JOIN mcl.mssql_columns mc ON mdc.column_id = mc.id
JOIN mcl.postgres_columns pc ON mc.id = pc.source_column_id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
WHERE NOT EXISTS (
    SELECT 1 FROM mcl.postgres_default_constraints pdc 
    WHERE pdc.source_default_constraint_id = mdc.id
);
```

### 2. **ОБНОВЛЕНИЕ ИНДЕКСОВ И ОГРАНИЧЕНИЙ**

```sql
-- ДОБАВИТЬ индексы для улучшения производительности
CREATE INDEX idx_mssql_default_constraints_column_id 
ON mcl.mssql_default_constraints(column_id);

CREATE INDEX idx_postgres_default_constraints_column_id 
ON mcl.postgres_default_constraints(column_id);

CREATE INDEX idx_postgres_default_constraints_source_id 
ON mcl.postgres_default_constraints(source_default_constraint_id);

-- ДОБАВИТЬ ограничения уникальности
ALTER TABLE mcl.mssql_default_constraints 
ADD CONSTRAINT uk_mssql_default_constraints_column_id 
UNIQUE (column_id);

ALTER TABLE mcl.postgres_default_constraints 
ADD CONSTRAINT uk_postgres_default_constraints_column_id 
UNIQUE (column_id);
```

### 3. **ОБНОВЛЕНИЕ ФУНКЦИЙ МИГРАЦИИ**

#### A. Функция получения структуры таблицы:
```python
def get_table_structure(table_id: int, task_id: int = 2) -> Dict:
    """
    Обновленная функция получения структуры таблицы
    """
    # ... существующий код ...
    
    # Получение колонок таблицы (БЕЗ default_value из columns)
    cursor.execute('''
        SELECT 
            pc.column_name,
            pc.ordinal_position,
            mdt.is_nullable,
            pc.postgres_data_type_id,
            COALESCE(pdt.typname_with_params, 'text') as data_type,
            pc.has_default_value  -- Вычисляемое поле
        FROM mcl.postgres_tables pt
        JOIN mcl.postgres_columns pc ON pt.id = pc.table_id
        JOIN mcl.postgres_derived_types pdt ON pc.postgres_data_type_id = pdt.id
        JOIN mcl.mssql_derived_types mdt ON pdt.source_derived_type_id = mdt.id
        WHERE pt.id = %s
        ORDER BY pc.ordinal_position
    ''', (table_id,))
    
    columns = cursor.fetchall()
    
    # Получение значений по умолчанию из default_constraints
    default_values = {}
    cursor.execute('''
        SELECT 
            pc.column_name,
            pdc.definition
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
        JOIN mcl.mssql_tables mt ON pc.source_table_id = mt.id
        WHERE mt.id = %s AND mt.task_id = %s
    ''', (table_id, task_id))
    
    for column_name, definition in cursor.fetchall():
        default_values[column_name] = definition
    
    return {
        'columns': columns,
        'default_values': default_values,
        # ... остальные поля ...
    }
```

#### B. Функция создания структуры таблицы:
```python
def create_table_structure(table_id: int, task_id: int = 2) -> bool:
    """
    Обновленная функция создания структуры таблицы
    """
    structure = get_table_structure(table_id, task_id)
    
    column_definitions = []
    
    for column in structure['columns']:
        column_name, ordinal_position, is_nullable, data_type_id, data_type, has_default = column
        
        # Форматирование имени колонки
        formatted_name = format_column_name(column_name)
        
        # Базовое определение
        ddl_parts = [formatted_name, data_type]
        
        # NULL/NOT NULL
        nullable = 'NULL' if is_nullable else 'NOT NULL'
        ddl_parts.append(nullable)
        
        # Значение по умолчанию (из default_constraints)
        if has_default and column_name in structure['default_values']:
            default_value = structure['default_values'][column_name]
            if default_value:
                # Преобразуем определение для PostgreSQL
                transformed_default = transform_default_definition(default_value)
                if transformed_default:
                    ddl_parts.append(f'DEFAULT {transformed_default}')
        
        column_definitions.append('    ' + ' '.join(ddl_parts))
    
    # ... остальной код ...
```

### 4. **МИГРАЦИОННЫЙ СКРИПТ**

```sql
-- Скрипт для выполнения реструктуризации
BEGIN;

-- 1. Создаем недостающие записи в default_constraints
INSERT INTO mcl.mssql_default_constraints (table_id, column_id, constraint_name, definition, is_system_named, created_at, updated_at)
SELECT 
    mc.table_id,
    mc.id,
    'DF_' || mt.object_name || '_' || mc.column_name,
    mc.default_value,
    true,
    NOW(),
    NOW()
FROM mcl.mssql_columns mc
JOIN mcl.mssql_tables mt ON mc.table_id = mt.id
WHERE mc.default_value IS NOT NULL 
    AND mc.default_value != ''
    AND NOT EXISTS (
        SELECT 1 FROM mcl.mssql_default_constraints mdc 
        WHERE mdc.column_id = mc.id
    );

-- 2. Создаем соответствующие записи в postgres_default_constraints
INSERT INTO mcl.postgres_default_constraints (table_id, column_id, source_default_constraint_id, constraint_name, original_constraint_name, definition, migration_status, created_at, updated_at)
SELECT 
    pt.id,
    pc.id,
    mdc.id,
    LOWER('df_' || pt.object_name || '_' || pc.column_name),
    mdc.constraint_name,
    mdc.definition,
    'PENDING',
    NOW(),
    NOW()
FROM mcl.mssql_default_constraints mdc
JOIN mcl.mssql_columns mc ON mdc.column_id = mc.id
JOIN mcl.postgres_columns pc ON mc.id = pc.source_column_id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
WHERE NOT EXISTS (
    SELECT 1 FROM mcl.postgres_default_constraints pdc 
    WHERE pdc.source_default_constraint_id = mdc.id
);

-- 3. Добавляем вычисляемые поля
ALTER TABLE mcl.mssql_columns 
ADD COLUMN has_default_value BOOLEAN GENERATED ALWAYS AS (
    EXISTS (
        SELECT 1 FROM mcl.mssql_default_constraints mdc 
        WHERE mdc.column_id = mssql_columns.id
    )
) STORED;

ALTER TABLE mcl.postgres_columns 
ADD COLUMN has_default_value BOOLEAN GENERATED ALWAYS AS (
    EXISTS (
        SELECT 1 FROM mcl.postgres_default_constraints pdc 
        WHERE pdc.column_id = postgres_columns.id
    )
) STORED;

-- 4. Добавляем индексы
CREATE INDEX idx_mssql_default_constraints_column_id 
ON mcl.mssql_default_constraints(column_id);

CREATE INDEX idx_postgres_default_constraints_column_id 
ON mcl.postgres_default_constraints(column_id);

CREATE INDEX idx_postgres_default_constraints_source_id 
ON mcl.postgres_default_constraints(source_default_constraint_id);

-- 5. Добавляем ограничения уникальности
ALTER TABLE mcl.mssql_default_constraints 
ADD CONSTRAINT uk_mssql_default_constraints_column_id 
UNIQUE (column_id);

ALTER TABLE mcl.postgres_default_constraints 
ADD CONSTRAINT uk_postgres_default_constraints_column_id 
UNIQUE (column_id);

-- 6. Удаляем дублирующие поля (ВНИМАНИЕ: Только после проверки!)
-- ALTER TABLE mcl.mssql_columns DROP COLUMN default_value;
-- ALTER TABLE mcl.postgres_columns DROP COLUMN default_value;

COMMIT;
```

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### До реструктуризации:
- `mssql_default_constraints`: 5 записей
- `postgres_default_constraints`: 5 записей  
- `mssql_columns.default_value`: 49 записей
- `postgres_columns.default_value`: 49 записей
- **Неконсистентность**: 44 записи

### После реструктуризации:
- `mssql_default_constraints`: 49 записей
- `postgres_default_constraints`: 49 записей
- `mssql_columns.has_default_value`: 49 записей (вычисляемое)
- `postgres_columns.has_default_value`: 49 записей (вычисляемое)
- **Полная консистентность**: 0 несоответствий

## ⚠️ РИСКИ И МЕРЫ ПРЕДОСТОРОЖНОСТИ

### 1. **РИСКИ:**
- Потеря данных при удалении полей `default_value`
- Нарушение работы существующих функций
- Проблемы с производительностью при добавлении вычисляемых полей

### 2. **МЕРЫ ПРЕДОСТОРОЖНОСТИ:**
- Выполнять изменения в транзакции
- Создать резервную копию перед изменениями
- Тестировать на копии базы данных
- Поэтапное внедрение с проверками

### 3. **ПЛАН ВНЕДРЕНИЯ:**
1. **Этап 1**: Создание недостающих записей в `default_constraints`
2. **Этап 2**: Добавление вычисляемых полей `has_default_value`
3. **Этап 3**: Обновление функций миграции
4. **Этап 4**: Тестирование на копии данных
5. **Этап 5**: Удаление дублирующих полей `default_value`

## 🔍 ПРОВЕРКИ ПОСЛЕ РЕСТРУКТУРИЗАЦИИ

```sql
-- Проверка консистентности
SELECT 
    'mssql_columns с has_default_value' as source,
    COUNT(*) as count
FROM mcl.mssql_columns 
WHERE has_default_value = true

UNION ALL

SELECT 
    'mssql_default_constraints' as source,
    COUNT(*) as count
FROM mcl.mssql_default_constraints

UNION ALL

SELECT 
    'postgres_columns с has_default_value' as source,
    COUNT(*) as count
FROM mcl.postgres_columns 
WHERE has_default_value = true

UNION ALL

SELECT 
    'postgres_default_constraints' as source,
    COUNT(*) as count
FROM mcl.postgres_default_constraints;

-- Должны получить 4 одинаковых числа
```

## 💡 ДОПОЛНИТЕЛЬНЫЕ УЛУЧШЕНИЯ

### 1. **ФУНКЦИИ ДЛЯ РАБОТЫ С МЕТАДАННЫМИ:**
```sql
-- Функция для получения значения по умолчанию колонки
CREATE OR REPLACE FUNCTION mcl.get_column_default_value(
    p_column_id INTEGER
) RETURNS TEXT AS $$
DECLARE
    v_definition TEXT;
BEGIN
    SELECT definition INTO v_definition
    FROM mcl.mssql_default_constraints
    WHERE column_id = p_column_id;
    
    RETURN v_definition;
END;
$$ LANGUAGE plpgsql;

-- Функция для получения PostgreSQL значения по умолчанию
CREATE OR REPLACE FUNCTION mcl.get_postgres_default_value(
    p_column_id INTEGER
) RETURNS TEXT AS $$
DECLARE
    v_definition TEXT;
BEGIN
    SELECT definition INTO v_definition
    FROM mcl.postgres_default_constraints
    WHERE column_id = p_column_id;
    
    RETURN v_definition;
END;
$$ LANGUAGE plpgsql;
```

### 2. **ВИДЫ ДЛЯ УДОБСТВА РАБОТЫ:**
```sql
-- Вид для получения полной информации о колонках со значениями по умолчанию
CREATE OR REPLACE VIEW mcl.v_columns_with_defaults AS
SELECT 
    mc.id as mssql_column_id,
    pc.id as postgres_column_id,
    mc.column_name,
    pc.column_name as postgres_column_name,
    mc.default_value as mssql_default_value,
    pdc.definition as postgres_default_value,
    mdc.constraint_name as mssql_constraint_name,
    pdc.constraint_name as postgres_constraint_name,
    mc.has_default_value,
    pc.has_default_value as postgres_has_default_value
FROM mcl.mssql_columns mc
LEFT JOIN mcl.postgres_columns pc ON mc.id = pc.source_column_id
LEFT JOIN mcl.mssql_default_constraints mdc ON mc.id = mdc.column_id
LEFT JOIN mcl.postgres_default_constraints pdc ON pc.id = pdc.column_id
WHERE mc.has_default_value = true;
```

## 🎯 ЗАКЛЮЧЕНИЕ

Предлагаемая реструктуризация решает проблему дублирования данных и обеспечивает:

1. **Единственный источник истины** для значений по умолчанию
2. **Автоматическую синхронизацию** через вычисляемые поля
3. **Упрощение логики** работы с метаданными
4. **Повышение надежности** системы миграции

Рекомендуется выполнить реструктуризацию поэтапно с тщательным тестированием на каждом этапе.