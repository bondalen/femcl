# 📋 ОТЧЕТ ОБ ОБНОВЛЕНИИ ПРАВИЛ МИГРАЦИИ ОТДЕЛЬНОЙ ТАБЛИЦЫ

## 🎯 **Цель обновления**
Интеграция метаданных схемы `mcl` для автоматического определения параметров миграции и свойств всех элементов таблицы.

## 📊 **Основные изменения**

### ✅ **1. Добавлен новый этап проверки подключений к базам данных**

#### **ЭТАП 0: ПРОВЕРКА ПОДКЛЮЧЕНИЙ К БАЗАМ ДАННЫХ**
- Загрузка конфигурации из файла `config.yaml`
- Проверка подключения к MS SQL Server
- Проверка подключения к PostgreSQL
- Валидация доступности схем `mcl` и `ags`

**Python функции:**
```python
def load_config(config_path="/home/alex/projects/sql/femcl/config/config.yaml"):
    """Загрузка конфигурации из файла"""
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def check_mssql_connection():
    """Проверка подключения к MS SQL Server"""
    # Проверка подключения с использованием параметров из config.yaml
    # Валидация доступности схемы mcl
    # Проверка количества таблиц в схеме mcl

def check_postgres_connection():
    """Проверка подключения к PostgreSQL"""
    # Проверка подключения с использованием параметров из config.yaml
    # Валидация доступности схем mcl и ags
    # Проверка количества таблиц в схемах

def check_database_connections():
    """Комплексная проверка подключений к базам данных"""
    # Выполнение всех проверок подключений
    # Возврат результата проверки
```

### ✅ **2. Добавлен новый этап определения целевой таблицы**

#### **ЭТАП 1: ОПРЕДЕЛЕНИЕ ИМЕНИ ЦЕЛЕВОЙ ТАБЛИЦЫ**
- Поиск исходной таблицы в `mcl.mssql_tables`
- Получение `source_table_id`
- Поиск целевой таблицы по `source_table_id` в `mcl.postgres_tables`
- Извлечение имени целевой таблицы

**SQL запросы:**
```sql
-- Поиск исходной таблицы
SELECT id, object_name, schema_name, object_type, row_count, column_count
FROM mcl.mssql_tables 
WHERE object_name = '<table_name>';

-- Получение ID исходной таблицы
SELECT id as source_table_id
FROM mcl.mssql_tables 
WHERE object_name = '<table_name>';

-- Поиск целевой таблицы по ID исходной таблицы
SELECT id, source_table_id, object_name, schema_name, object_type, migration_status
FROM mcl.postgres_tables 
WHERE source_table_id = <source_table_id>;

-- Получение имени целевой таблицы
SELECT object_name as target_table_name
FROM mcl.postgres_tables 
WHERE source_table_id = <source_table_id>;
```

### ✅ **3. Переименованы существующие этапы**

| Старый номер | Новый номер | Название |
|--------------|-------------|----------|
| ЭТАП 0 | ЭТАП 0 | ПРОВЕРКА ПОДКЛЮЧЕНИЙ К БАЗАМ ДАННЫХ (НОВЫЙ) |
| ЭТАП 1 | ЭТАП 1 | ОПРЕДЕЛЕНИЕ ИМЕНИ ЦЕЛЕВОЙ ТАБЛИЦЫ (НОВЫЙ) |
| ЭТАП 1 | ЭТАП 2 | ПОДГОТОВКА К МИГРАЦИИ |
| ЭТАП 2 | ЭТАП 3 | ПРОВЕРКА ГОТОВНОСТИ ТАБЛИЦЫ |
| ЭТАП 3 | ЭТАП 4 | СОЗДАНИЕ СТРУКТУРЫ ТАБЛИЦЫ |
| ЭТАП 4 | ЭТАП 5 | ПЕРЕНОС ДАННЫХ |

### ✅ **4. Добавлена функция валидации параметров из метаданных**

```python
def validate_migration_parameters_from_metadata(table_name):
    """Валидация параметров миграции из метаданных"""
    
    # 1. Поиск исходной таблицы
    source_query = """
    SELECT id, object_name, schema_name, row_count, column_count
    FROM mcl.mssql_tables 
    WHERE object_name = %s
    """
    source_table = execute_query(source_query, (table_name,))
    
    if not source_table:
        raise ValueError(f"Исходная таблица {table_name} не найдена в mssql_tables")
    
    source_table_id = source_table[0]['id']
    
    # 2. Поиск целевой таблицы
    target_query = """
    SELECT id, object_name, schema_name, migration_status
    FROM mcl.postgres_tables 
    WHERE source_table_id = %s
    """
    target_table = execute_query(target_query, (source_table_id,))
    
    if not target_table:
        raise ValueError(f"Целевая таблица для {table_name} не найдена в postgres_tables")
    
    return {
        'source_table_id': source_table_id,
        'target_table_id': target_table[0]['id'],
        'source_table_name': table_name,
        'target_table_name': target_table[0]['object_name'],
        'source_schema': source_table[0]['schema_name'],
        'target_schema': target_table[0]['schema_name'],
        'migration_status': target_table[0]['migration_status']
    }
```

### ✅ **5. Обновлена функция миграции**

```python
def migrate_single_table(table_name):
    """Управление миграцией отдельной таблицы с использованием метаданных"""
    
    # ЭТАП 1: Определение параметров из метаданных
    params = validate_migration_parameters_from_metadata(table_name)
    
    # ЭТАП 2: Проверка готовности
    readiness_result = check_table_readiness(params['source_table_id'], params['target_table_id'])
    
    # ЭТАП 3: Создание структуры
    creation_result = create_table_structure(params['target_table_id'], params['target_table_name'])
    
    # ЭТАП 4: Перенос данных
    migration_result = migrate_table_data(
        params['source_schema'], params['source_table_name'], 
        params['target_schema'], params['target_table_name']
    )
    
    # ЭТАП 5: Проверка результатов
    verification_result = verify_migration_results(params['target_table_name'])
```

### ✅ **6. Добавлены функции определения свойств всех элементов таблицы**

#### **5.1 Определение колонок с прямыми ссылками**
```python
def resolve_columns_metadata_correct(table_info):
    """Определение колонок с использованием прямых ссылок source_column_id"""
    
    query = """
    SELECT 
        -- Исходные свойства
        mc.id as source_column_id,
        mc.column_name as source_column_name,
        mc.ordinal_position as source_ordinal_position,
        mc.default_value as source_default_value,
        mc.is_identity as source_is_identity,
        mc.identity_seed as source_identity_seed,
        mc.identity_increment as source_identity_increment,
        mc.is_computed as source_is_computed,
        mc.computed_definition as source_computed_definition,
        mc.is_persisted as source_is_persisted,
        mc.column_description as source_description,
        
        -- Целевые свойства
        pc.id as target_column_id,
        pc.column_name as target_column_name,
        pc.ordinal_position as target_ordinal_position,
        pc.default_value as target_default_value,
        pc.is_identity as target_is_identity,
        pc.identity_seed as target_identity_seed,
        pc.identity_increment as target_identity_increment,
        pc.is_computed as target_is_computed,
        pc.computed_definition as target_computed_definition,
        pc.column_description as target_description,
        
        -- Типы данных
        pdt.typname_with_params as target_data_type,
        pdt.typname as base_type,
        
        -- Статус миграции
        pc.type_mapping_quality,
        pc.data_type_migration_status,
        pc.data_type_migration_notes,
        
        -- Прямая связь
        pc.source_column_id as direct_source_reference
        
    FROM mcl.postgres_columns pc
    JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
    JOIN mcl.postgres_derived_types pdt ON pc.postgres_data_type_id = pdt.id
    WHERE pc.table_id = %s
    ORDER BY pc.ordinal_position
    """
    
    return execute_query(query, (table_info['target_table_id'],))
```

#### **5.2 Определение первичных ключей**
```python
def resolve_primary_keys_metadata_correct(table_info):
    """Определение первичных ключей с использованием прямых ссылок"""
    
    # Основная информация о первичном ключе
    pk_query = """
    SELECT 
        -- Исходные свойства
        mpk.id as source_primary_key_id,
        mpk.constraint_name as source_constraint_name,
        mpk.is_clustered as source_is_clustered,
        mpk.pk_type as source_pk_type,
        mpk.pk_ordinal_position as source_ordinal_position,
        
        -- Целевые свойства
        ppk.id as target_primary_key_id,
        ppk.constraint_name as target_constraint_name,
        ppk.is_clustered as target_is_clustered,
        ppk.created_at as target_created_at,
        ppk.updated_at as target_updated_at,
        
        -- Прямая связь
        ppk.source_primary_key_id as direct_source_reference
        
    FROM mcl.postgres_primary_keys ppk
    JOIN mcl.mssql_primary_keys mpk ON ppk.source_primary_key_id = mpk.id
    WHERE ppk.table_id = %s
    """
    
    # Колонки первичного ключа
    pk_columns_query = """
    SELECT 
        ppkc.column_name as target_column_name,
        ppkc.ordinal_position,
        ppkc.is_descending as target_is_descending,
        ppkc.created_at,
        ppkc.updated_at
        
    FROM mcl.postgres_primary_key_columns ppkc
    JOIN mcl.postgres_primary_keys ppk ON ppkc.primary_key_id = ppk.id
    WHERE ppk.table_id = %s
    ORDER BY ppkc.ordinal_position
    """
    
    return {
        'primary_key': execute_query(pk_query, (table_info['target_table_id'],)),
        'columns': execute_query(pk_columns_query, (table_info['target_table_id'],))
    }
```

#### **5.3 Определение внешних ключей**
```python
def resolve_foreign_keys_metadata_correct(table_info):
    """Определение внешних ключей с использованием прямых ссылок"""
    
    query = """
    SELECT 
        -- Исходные свойства
        mfk.id as source_foreign_key_id,
        mfk.constraint_name as source_constraint_name,
        mfk.referenced_table_name as source_referenced_table,
        mfk.delete_action as source_delete_action,
        mfk.update_action as source_update_action,
        mfk.is_disabled as source_is_disabled,
        mfk.is_not_trusted as source_is_not_trusted,
        
        -- Целевые свойства
        pfk.id as target_foreign_key_id,
        pfk.constraint_name as target_constraint_name,
        pfk.original_constraint_name,
        pfk.delete_action as target_delete_action,
        pfk.update_action as target_update_action,
        pfk.migration_status,
        pfk.migration_date,
        pfk.error_message,
        
        -- Прямая связь
        pfk.source_foreign_key_id as direct_source_reference,
        pfk.referenced_table_id,
        pfk.created_at,
        pfk.updated_at
        
    FROM mcl.postgres_foreign_keys pfk
    JOIN mcl.mssql_foreign_keys mfk ON pfk.source_foreign_key_id = mfk.id
    WHERE pfk.table_id = %s
    ORDER BY pfk.constraint_name
    """
    
    # Колонки внешнего ключа
    fk_columns_query = """
    SELECT 
        pfkc.column_name as target_column_name,
        pfkc.referenced_column_name as target_referenced_column,
        pfkc.ordinal_position,
        pfkc.created_at,
        pfkc.updated_at
        
    FROM mcl.postgres_foreign_key_columns pfkc
    JOIN mcl.postgres_foreign_keys pfk ON pfkc.foreign_key_id = pfk.id
    WHERE pfk.table_id = %s
    ORDER BY pfk.constraint_name, pfkc.ordinal_position
    """
    
    return {
        'foreign_keys': execute_query(query, (table_info['target_table_id'],)),
        'columns': execute_query(fk_columns_query, (table_info['target_table_id'],))
    }
```

#### **5.4 Определение индексов**
```python
def resolve_indexes_metadata_correct(table_info):
    """Определение индексов с использованием прямых ссылок"""
    
    query = """
    SELECT 
        -- Исходные свойства
        mi.id as source_index_id,
        mi.index_name as source_index_name,
        mi.index_type as source_index_type,
        mi.is_unique as source_is_unique,
        mi.is_primary_key as source_is_primary_key,
        mi.is_disabled as source_is_disabled,
        mi.fill_factor as source_fill_factor,
        mi.is_padded as source_is_padded,
        mi.allow_row_locks as source_allow_row_locks,
        mi.allow_page_locks as source_allow_page_locks,
        
        -- Целевые свойства
        pi.id as target_index_id,
        pi.index_name as target_index_name,
        pi.original_index_name,
        pi.index_type as target_index_type,
        pi.is_unique as target_is_unique,
        pi.is_primary_key as target_is_primary_key,
        pi.fill_factor as target_fill_factor,
        pi.is_concurrent as target_is_concurrent,
        
        -- Конфликты имен
        pi.name_conflict_resolved,
        pi.name_conflict_reason,
        pi.alternative_name,
        
        -- Статус миграции
        pi.migration_status,
        pi.migration_date,
        pi.error_message,
        
        -- Прямая связь
        pi.source_index_id as direct_source_reference,
        pi.created_at,
        pi.updated_at
        
    FROM mcl.postgres_indexes pi
    JOIN mcl.mssql_indexes mi ON pi.source_index_id = mi.id
    WHERE pi.table_id = %s
    ORDER BY pi.index_name
    """
    
    # Колонки индекса
    index_columns_query = """
    SELECT 
        pic.column_name as target_column_name,
        pic.ordinal_position,
        pic.is_descending as target_is_descending,
        pic.key_ordinal as target_key_ordinal,
        pic.created_at,
        pic.updated_at
        
    FROM mcl.postgres_index_columns pic
    JOIN mcl.postgres_indexes pi ON pic.index_id = pi.id
    WHERE pi.table_id = %s
    ORDER BY pi.index_name, pic.ordinal_position
    """
    
    return {
        'indexes': execute_query(query, (table_info['target_table_id'],)),
        'columns': execute_query(index_columns_query, (table_info['target_table_id'],))
    }
```

#### **5.5 Общая функция определения всех элементов**
```python
def resolve_complete_table_metadata_correct(table_name):
    """Полное определение всех элементов таблицы с использованием прямых ссылок"""
    
    # 1. Получение базовых параметров таблицы
    table_info = validate_migration_parameters_from_metadata(table_name)
    
    # 2. Определение всех элементов таблицы через прямые ссылки
    elements = {
        'columns': resolve_columns_metadata_correct(table_info),
        'primary_keys': resolve_primary_keys_metadata_correct(table_info),
        'foreign_keys': resolve_foreign_keys_metadata_correct(table_info),
        'indexes': resolve_indexes_metadata_correct(table_info)
    }
    
    return {
        'table': table_info,
        'elements': elements,
        'migration_status': 'ready_for_migration'
    }
```

## 🎉 **Преимущества обновленных правил**

### ✅ **Автоматизация**
- Автоматическое определение имени целевой таблицы
- Исключение ручного ввода параметров
- Использование метаданных для валидации

### ✅ **Надежность**
- Проверка существования таблиц в метаданных
- Валидация параметров перед миграцией
- Обработка ошибок на каждом этапе

### ✅ **Гибкость**
- Поддержка различных схем исходных и целевых таблиц
- Адаптация к изменениям в метаданных
- Легкое расширение для новых типов объектов

### ✅ **Производительность**
- Оптимизированные запросы к метаданным
- Минимальное количество обращений к БД
- Эффективное использование индексов

### ✅ **Прямые связи**
- Использование `source_*_id` полей для точного сопоставления
- Исключение ошибок при сопоставлении по позициям
- Надежная связь между исходными и целевыми объектами

## 📋 **Классификация целевых объектов**

| Категория | Количество | Примеры | Способ получения свойств |
|-----------|------------|---------|-------------------------|
| **Прямые ссылки** | 14 | tables, columns, indexes | `source_*_id` |
| **Косвенные ссылки** | 4 | *_columns таблицы | Через родительские объекты |
| **Независимые** | 2 | base_types, objects | Собственные свойства |

## 🚀 **Результат обновления**

Правила миграции отдельной таблицы теперь полностью интегрированы с метаданными схемы `mcl` и обеспечивают:

1. **Автоматическое определение параметров** из метаданных
2. **Прямые ссылки** между исходными и целевыми объектами
3. **Полное определение свойств** всех элементов таблицы
4. **Надежную валидацию** параметров миграции
5. **Оптимизированные запросы** к метаданным

---

*Отчет создан: 2025-01-27*  
*Версия: 1.0*  
*Статус: ЗАВЕРШЕН*  
*Тип: ОТЧЕТ ОБ ОБНОВЛЕНИИ ПРАВИЛ*