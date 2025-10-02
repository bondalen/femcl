# 🎯 ПРЕДЛОЖЕНИЕ ПО ВИДОВОЙ МИГРАЦИИ С ВЫЧИСЛЯЕМЫМИ ПОЛЯМИ

## 🎯 ЦЕЛЬ

Обеспечить работоспособность объектов базы данных при миграции с минимальной их модификацией через использование представлений, которые максимально близко повторяют структуру исходных таблиц.

## 📊 АНАЛИЗ ПОДХОДОВ

### **ПОДХОД 1: РАСШИРЕНИЕ ТАБЛИЦЫ `postgres_tables`**

#### Структура:
```sql
-- Расширенная таблица postgres_tables
CREATE TABLE mcl.postgres_tables (
    id INTEGER PRIMARY KEY,
    source_table_id INTEGER REFERENCES mcl.mssql_tables(id),
    object_name VARCHAR,           -- Имя базовой таблицы (с _bt)
    view_name VARCHAR,             -- Имя представления (близко к исходному)
    has_computed_columns BOOLEAN,  -- Есть ли вычисляемые поля
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Расширенная таблица postgres_columns
CREATE TABLE mcl.postgres_columns (
    id INTEGER PRIMARY KEY,
    table_id INTEGER REFERENCES mcl.postgres_tables(id),
    source_column_id INTEGER REFERENCES mcl.mssql_columns(id),
    column_name VARCHAR,
    ordinal_position INTEGER,
    is_computed BOOLEAN,           -- Вычисляемая ли колонка
    target_type VARCHAR,           -- 'base_table' или 'view'
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### Логика именования:
```python
def generate_table_names(source_table_name: str, has_computed_columns: bool) -> Dict[str, str]:
    """
    Генерация имен для базовой таблицы и представления
    """
    if has_computed_columns:
        base_table_name = f"{source_table_name}_bt"  # Базовая таблица
        view_name = source_table_name                 # Представление (как исходная таблица)
    else:
        base_table_name = source_table_name           # Таблица без вычисляемых полей
        view_name = source_table_name                 # Представление = таблица
    
    return {
        'base_table_name': base_table_name,
        'view_name': view_name
    }
```

#### Примеры:
```
Исходная таблица: "users"
- Базовая таблица: "users_bt" (содержит только физические колонки)
- Представление: "users" (содержит все колонки включая вычисляемые)

Исходная таблица: "orders" (без вычисляемых полей)
- Базовая таблица: "orders" 
- Представление: "orders" (одинаковые имена)
```

---

### **ПОДХОД 2: ИЕРАРХИЧЕСКАЯ СТРУКТУРА ОБЪЕКТОВ**

#### Структура:
```sql
-- Родительская таблица объектов
CREATE TABLE mcl.postgres_objects (
    id INTEGER PRIMARY KEY,
    source_table_id INTEGER REFERENCES mcl.mssql_tables(id),
    object_name VARCHAR,           -- Имя исходного объекта
    object_type VARCHAR,           -- 'table', 'view', 'function', etc.
    has_computed_columns BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Таблица целевых таблиц и представлений
CREATE TABLE mcl.postgres_table_views (
    id INTEGER PRIMARY KEY,
    parent_object_id INTEGER REFERENCES mcl.postgres_objects(id),
    base_table_name VARCHAR,       -- Имя базовой таблицы
    view_name VARCHAR,             -- Имя представления
    has_computed_columns BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Таблица базовых таблиц
CREATE TABLE mcl.postgres_base_tables (
    id INTEGER PRIMARY KEY,
    table_view_id INTEGER REFERENCES mcl.postgres_table_views(id),
    object_name VARCHAR,
    schema_name VARCHAR DEFAULT 'public',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Таблица представлений
CREATE TABLE mcl.postgres_views (
    id INTEGER PRIMARY KEY,
    table_view_id INTEGER REFERENCES mcl.postgres_table_views(id),
    base_table_id INTEGER REFERENCES mcl.postgres_base_tables(id),
    object_name VARCHAR,
    schema_name VARCHAR DEFAULT 'public',
    view_definition TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Модифицированная таблица колонок
CREATE TABLE mcl.postgres_columns (
    id INTEGER PRIMARY KEY,
    table_view_id INTEGER REFERENCES mcl.postgres_table_views(id),  -- Ссылка на обобщающую таблицу
    source_column_id INTEGER REFERENCES mcl.mssql_columns(id),
    column_name VARCHAR,
    ordinal_position INTEGER,
    is_computed BOOLEAN,
    target_type VARCHAR,           -- 'base_table' или 'view'
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### Схема связей:
```
mssql_tables (исходные)
    ↓
postgres_objects (родительские объекты)
    ↓
postgres_table_views (обобщающие таблица+представление)
    ↓
postgres_base_tables (физические таблицы)
postgres_views (представления)
    ↓
postgres_columns (колонки с ссылкой на table_view_id)
```

---

## 🔍 СРАВНИТЕЛЬНЫЙ АНАЛИЗ

| Критерий | Подход 1 | Подход 2 |
|----------|----------|----------|
| **Простота** | ✅ Простой | ❌ Сложный |
| **Гибкость** | ⚠️ Ограниченная | ✅ Высокая |
| **Масштабируемость** | ⚠️ Средняя | ✅ Высокая |
| **Производительность** | ✅ Быстрый | ⚠️ Медленнее |
| **Поддержка** | ✅ Легко | ❌ Сложно |
| **Нормализация** | ❌ Частичная | ✅ Полная |

---

## 🎯 РЕКОМЕНДУЕМЫЙ ПОДХОД

### **ПОДХОД 1: РАСШИРЕНИЕ ТАБЛИЦЫ `postgres_tables`**

#### Причины выбора:
1. **Простота реализации** - минимальные изменения в существующей структуре
2. **Обратная совместимость** - существующий код продолжит работать
3. **Производительность** - меньше JOIN'ов для получения информации
4. **Понятность** - логика именования проста и прозрачна

#### Структура реализации:
```sql
-- Модифицированная таблица postgres_tables
ALTER TABLE mcl.postgres_tables ADD COLUMN view_name VARCHAR;
ALTER TABLE mcl.postgres_tables ADD COLUMN has_computed_columns BOOLEAN DEFAULT FALSE;

-- Модифицированная таблица postgres_columns  
ALTER TABLE mcl.postgres_columns ADD COLUMN is_computed BOOLEAN DEFAULT FALSE;
ALTER TABLE mcl.postgres_columns ADD COLUMN target_type VARCHAR DEFAULT 'base_table';
```

#### Логика работы:
```python
def create_table_structure(table_id: int, task_id: int) -> bool:
    """
    Создание структуры таблицы с учетом вычисляемых полей
    """
    # Получаем информацию о таблице
    table_info = get_table_info(table_id, task_id)
    
    if table_info['has_computed_columns']:
        # Создаем базовую таблицу с суффиксом _bt
        create_base_table(table_info['object_name'] + '_bt', physical_columns)
        
        # Создаем представление с исходным именем
        create_view(table_info['view_name'], all_columns)
    else:
        # Создаем обычную таблицу
        create_table(table_info['object_name'], all_columns)
```

---

## 🔧 ПРАКТИЧЕСКАЯ РЕАЛИЗАЦИЯ

### **1. Обновление структуры метаданных:**

```sql
-- Добавление полей в postgres_tables
ALTER TABLE mcl.postgres_tables 
ADD COLUMN view_name VARCHAR,
ADD COLUMN has_computed_columns BOOLEAN DEFAULT FALSE,
ADD COLUMN base_table_name VARCHAR;

-- Добавление полей в postgres_columns
ALTER TABLE mcl.postgres_columns 
ADD COLUMN is_computed BOOLEAN DEFAULT FALSE,
ADD COLUMN target_type VARCHAR DEFAULT 'base_table';

-- Обновление существующих записей
UPDATE mcl.postgres_tables 
SET 
    base_table_name = CASE 
        WHEN has_computed_columns THEN object_name || '_bt'
        ELSE object_name 
    END,
    view_name = object_name;
```

### **2. Функции для работы с именованием:**

```sql
-- Функция генерации имен
CREATE OR REPLACE FUNCTION mcl.generate_table_names(
    p_source_name VARCHAR,
    p_has_computed BOOLEAN
) RETURNS TABLE (
    base_table_name VARCHAR,
    view_name VARCHAR
) AS $$
BEGIN
    IF p_has_computed THEN
        RETURN QUERY SELECT 
            p_source_name || '_bt' as base_table_name,
            p_source_name as view_name;
    ELSE
        RETURN QUERY SELECT 
            p_source_name as base_table_name,
            p_source_name as view_name;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

### **3. Представления для удобства:**

```sql
-- Представление для получения полной информации о таблицах
CREATE OR REPLACE VIEW mcl.v_postgres_tables_full AS
SELECT 
    pt.id,
    pt.source_table_id,
    pt.object_name,
    pt.base_table_name,
    pt.view_name,
    pt.has_computed_columns,
    mt.object_name as source_table_name,
    CASE 
        WHEN pt.has_computed_columns THEN 'table_view'
        ELSE 'table_only'
    END as object_type
FROM mcl.postgres_tables pt
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id;

-- Представление для колонок с информацией о типе
CREATE OR REPLACE VIEW mcl.v_postgres_columns_full AS
SELECT 
    pc.id,
    pc.table_id,
    pc.column_name,
    pc.ordinal_position,
    pc.is_computed,
    pc.target_type,
    pt.object_name as table_name,
    pt.base_table_name,
    pt.view_name,
    pt.has_computed_columns
FROM mcl.postgres_columns pc
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id;
```

### **4. Обновление функций миграции:**

```python
def create_table_structure(table_id: int, task_id: int) -> bool:
    """
    Обновленная функция создания структуры таблицы
    """
    # Получаем информацию о таблице
    cursor.execute('''
        SELECT 
            pt.object_name,
            pt.base_table_name,
            pt.view_name,
            pt.has_computed_columns
        FROM mcl.postgres_tables pt
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE pt.id = %s AND mt.task_id = %s
    ''', (table_id, task_id))
    
    table_info = cursor.fetchone()
    
    if table_info['has_computed_columns']:
        # Создаем базовую таблицу
        create_base_table(table_info['base_table_name'], physical_columns_only)
        
        # Создаем представление
        create_view(table_info['view_name'], all_columns_including_computed)
        
        log_migration_event(
            task_id, 'TABLE_VIEW_CREATED', 'SUCCESS',
            f"Created base table '{table_info['base_table_name']}' and view '{table_info['view_name']}'"
        )
    else:
        # Создаем обычную таблицу
        create_table(table_info['object_name'], all_columns)
        
        log_migration_event(
            task_id, 'TABLE_CREATED', 'SUCCESS',
            f"Created table '{table_info['object_name']}'"
        )
    
    return True
```

---

## 📋 ПЛАН ВНЕДРЕНИЯ

### **Этап 1: Подготовка структуры**
1. Добавить новые поля в `postgres_tables` и `postgres_columns`
2. Создать функции для работы с именованием
3. Создать представления для удобства

### **Этап 2: Анализ вычисляемых полей**
1. Определить, какие таблицы имеют вычисляемые поля
2. Обновить флаг `has_computed_columns` для таблиц
3. Обновить флаг `is_computed` для колонок

### **Этап 3: Генерация имен**
1. Сгенерировать `base_table_name` и `view_name` для всех таблиц
2. Проверить уникальность имен
3. Обновить метаданные

### **Этап 4: Обновление функций миграции**
1. Модифицировать `create_table_structure`
2. Создать функции для создания представлений
3. Обновить логику DDL генерации

### **Этап 5: Тестирование**
1. Протестировать создание таблиц с вычисляемыми полями
2. Протестировать создание представлений
3. Проверить совместимость с существующими объектами

---

## 🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### **Преимущества:**
1. **Совместимость** - существующие объекты найдут нужные колонки
2. **Гибкость** - поддержка любых вычисляемых полей
3. **Производительность** - физические таблицы без лишних вычислений
4. **Масштабируемость** - легко добавлять новые типы вычисляемых полей

### **Примеры использования:**
```sql
-- Приложение продолжит работать без изменений
SELECT * FROM users WHERE age > 18;  -- Обращается к представлению

-- Физическая таблица содержит только реальные данные
SELECT * FROM users_bt;  -- Только физические колонки

-- Представление содержит все колонки включая вычисляемые
SELECT * FROM users;     -- Все колонки включая computed
```

Этот подход обеспечит плавную миграцию с минимальными изменениями в существующих объектах базы данных.