# 🏗️ Предложения по улучшению архитектуры индексов

**Дата:** 2025-10-02  
**Проект:** FEMCL  
**Проблема:** Индексы не связаны напрямую с таблицами в метаданных  

## 🔍 Анализ текущей проблемы

### Текущая архитектура:
```
mcl.postgres_indexes (НЕТ прямой связи с таблицами)
    ↓ (через source_index_id)
mcl.mssql_indexes 
    ↓ (через mssql_index_columns)
mcl.mssql_columns 
    ↓ (через table_id)
mcl.mssql_tables
```

### Проблемы:
1. **Сложные запросы** - для получения индексов таблицы нужен многоуровневый JOIN
2. **Низкая производительность** - каждый запрос проходит через 4-5 таблиц
3. **Сложность поддержки** - трудно понять связи между объектами
4. **Отсутствие прямых связей** - нет FK между postgres_indexes и postgres_tables

## 💡 Предложения по улучшению

### Вариант 1: Добавить прямую связь (Рекомендуемый)

#### 1.1 Добавить колонку table_id в postgres_indexes
```sql
-- Добавляем колонку для прямой связи с таблицей
ALTER TABLE mcl.postgres_indexes 
ADD COLUMN table_id INTEGER;

-- Создаем внешний ключ
ALTER TABLE mcl.postgres_indexes 
ADD CONSTRAINT fk_postgres_indexes_table_id 
FOREIGN KEY (table_id) REFERENCES mcl.postgres_tables(id) ON DELETE CASCADE;

-- Создаем индекс для производительности
CREATE INDEX idx_postgres_indexes_table_id ON mcl.postgres_indexes(table_id);
```

#### 1.2 Заполнить данные
```sql
-- Заполняем table_id на основе существующих связей
UPDATE mcl.postgres_indexes 
SET table_id = (
    SELECT pt.id 
    FROM mcl.postgres_tables pt
    JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
    JOIN mcl.mssql_columns mc ON mt.id = mc.table_id
    JOIN mcl.mssql_index_columns mic ON mc.id = mic.column_id
    JOIN mcl.mssql_indexes mi ON mic.index_id = mi.id
    WHERE mi.id = postgres_indexes.source_index_id
    LIMIT 1
)
WHERE table_id IS NULL;
```

#### 1.3 Преимущества:
- ✅ **Прямые запросы** - `SELECT * FROM postgres_indexes WHERE table_id = ?`
- ✅ **Высокая производительность** - один JOIN вместо четырех
- ✅ **Простота понимания** - очевидная связь таблица → индексы
- ✅ **Обратная совместимость** - source_index_id остается

### Вариант 2: Создать представление (View)

#### 2.1 Создать представление для упрощения запросов
```sql
CREATE VIEW mcl.v_postgres_indexes_by_table AS
SELECT 
    pt.object_name as table_name,
    pt.id as table_id,
    pi.id as index_id,
    pi.index_name,
    pi.original_index_name,
    pi.index_type,
    pi.is_unique,
    pi.is_primary_key,
    pi.migration_status,
    pi.source_index_id
FROM mcl.postgres_tables pt
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
JOIN mcl.mssql_columns mc ON mt.id = mc.table_id
JOIN mcl.mssql_index_columns mic ON mc.id = mic.column_id
JOIN mcl.mssql_indexes mi ON mic.index_id = mi.id
JOIN mcl.postgres_indexes pi ON mi.id = pi.source_index_id
GROUP BY pt.id, pt.object_name, pi.id, pi.index_name, pi.original_index_name, 
         pi.index_type, pi.is_unique, pi.is_primary_key, pi.migration_status, pi.source_index_id;
```

#### 2.2 Преимущества:
- ✅ **Без изменения схемы** - не нужно менять существующие таблицы
- ✅ **Упрощенные запросы** - `SELECT * FROM v_postgres_indexes_by_table WHERE table_name = 'accnt'`
- ✅ **Автоматическое обновление** - всегда актуальные данные

#### 2.3 Недостатки:
- ❌ **Производительность** - все равно сложные JOIN под капотом
- ❌ **Ограничения** - нельзя создавать индексы на представления

### Вариант 3: Нормализация через промежуточную таблицу

#### 3.1 Создать таблицу связей
```sql
CREATE TABLE mcl.postgres_table_indexes (
    id SERIAL PRIMARY KEY,
    table_id INTEGER NOT NULL,
    index_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_table_indexes_table FOREIGN KEY (table_id) REFERENCES mcl.postgres_tables(id),
    CONSTRAINT fk_table_indexes_index FOREIGN KEY (index_id) REFERENCES mcl.postgres_indexes(id),
    CONSTRAINT uk_table_indexes UNIQUE (table_id, index_id)
);
```

#### 3.2 Преимущества:
- ✅ **Гибкость** - можно добавлять дополнительные атрибуты связи
- ✅ **Масштабируемость** - легко добавлять новые типы связей
- ✅ **Нормализация** - правильная реляционная структура

## 🎯 Рекомендация

### Рекомендуемый подход: **Вариант 1 + Вариант 2**

1. **Краткосрочно** - создать представление для упрощения текущих запросов
2. **Долгосрочно** - добавить колонку table_id для прямой связи

### План реализации:

#### Этап 1: Создание представления (1-2 часа)
```sql
-- Создаем представление для упрощения запросов
CREATE VIEW mcl.v_postgres_indexes_by_table AS
SELECT 
    pt.object_name as table_name,
    pt.id as table_id,
    pi.id as index_id,
    pi.index_name,
    pi.index_type,
    pi.is_unique,
    pi.is_primary_key,
    pi.migration_status
FROM mcl.postgres_tables pt
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
JOIN mcl.mssql_columns mc ON mt.id = mc.table_id
JOIN mcl.mssql_index_columns mic ON mc.id = mic.column_id
JOIN mcl.mssql_indexes mi ON mic.index_id = mi.id
JOIN mcl.postgres_indexes pi ON mi.id = pi.source_index_id
GROUP BY pt.id, pt.object_name, pi.id, pi.index_name, pi.index_type, 
         pi.is_unique, pi.is_primary_key, pi.migration_status;
```

#### Этап 2: Обновление кода (2-3 часа)
- Обновить `TableModel.load_indexes()` для использования представления
- Упростить запросы в `TableMigrator.create_indexes()`
- Добавить кэширование для производительности

#### Этап 3: Добавление прямой связи (4-6 часов)
- Добавить колонку `table_id` в `postgres_indexes`
- Заполнить данные на основе существующих связей
- Создать индексы и ограничения
- Обновить код для использования прямой связи

## 📊 Ожидаемые результаты

### Производительность:
- **Текущий запрос:** 4-5 JOIN, ~50ms
- **С представлением:** 1 запрос, ~10ms
- **С прямой связью:** 1 JOIN, ~5ms

### Упрощение кода:
```python
# Текущий код (сложный)
cursor.execute("""
    SELECT pi.* FROM mcl.postgres_indexes pi
    WHERE pi.source_index_id IN (
        SELECT mi.id FROM mcl.mssql_indexes mi
        JOIN mcl.mssql_index_columns mic ON mi.id = mic.index_id
        JOIN mcl.mssql_columns mc ON mic.column_id = mc.id
        JOIN mcl.mssql_tables mt ON mc.table_id = mt.id
        WHERE mt.object_name = %s
    )
""", (table_name,))

# После улучшения (простой)
cursor.execute("""
    SELECT * FROM mcl.v_postgres_indexes_by_table 
    WHERE table_name = %s
""", (table_name,))
```

## 🚀 Следующие шаги

1. **Создать представление** для немедленного улучшения
2. **Обновить код** для использования представления
3. **Протестировать** на таблице accnt
4. **Планировать миграцию** для добавления прямой связи
5. **Документировать** изменения в архитектуре

Это решение значительно упростит работу с индексами и повысит производительность системы! 🎯