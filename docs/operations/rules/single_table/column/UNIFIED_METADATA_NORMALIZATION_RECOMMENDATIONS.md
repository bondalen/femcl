# 🎯 ОБОБЩЕННЫЕ РЕКОМЕНДАЦИИ ПО НОРМАЛИЗАЦИИ МЕТАДАННЫХ

## 🔍 РЕЗУЛЬТАТЫ КОМПЛЕКСНОГО АНАЛИЗА ВСЕЙ СИСТЕМЫ МЕТАДАННЫХ

После анализа как исходных (MS SQL), так и целевых (PostgreSQL) таблиц метаданных выявлены системные проблемы с дублированными и избыточными связями, которые нарушают логическую модель данных в обеих частях системы.

## 📊 СРАВНИТЕЛЬНЫЙ АНАЛИЗ СТРУКТУР МЕТАДАННЫХ

### **Структуры таблиц MS SQL и PostgreSQL идентичны:**

| Объект | MS SQL Основная | MS SQL Колонки | PostgreSQL Основная | PostgreSQL Колонки | Статус |
|--------|-----------------|----------------|---------------------|-------------------|---------|
| **Check Constraints** | `mssql_check_constraints` | ❌ НЕТ | `postgres_check_constraints` | ❌ НЕТ | Одинаково |
| **Indexes** | `mssql_indexes` | ✅ `mssql_index_columns` | `postgres_indexes` | ✅ `postgres_index_columns` | Одинаково |
| **Unique Constraints** | `mssql_unique_constraints` | ✅ `mssql_unique_constraint_columns` | `postgres_unique_constraints` | ✅ `postgres_unique_constraint_columns` | Одинаково |
| **Foreign Keys** | `mssql_foreign_keys` | ✅ `mssql_foreign_key_columns` | `postgres_foreign_keys` | ✅ `postgres_foreign_key_columns` | Одинаково |
| **Primary Keys** | `mssql_primary_keys` | ✅ `mssql_primary_key_columns` | `postgres_primary_keys` | ✅ `postgres_primary_key_columns` | Одинаково |
| **Default Constraints** | `mssql_default_constraints` | ❌ НЕТ | `postgres_default_constraints` | ❌ НЕТ | Одинаково |
| **Identity Columns** | `mssql_identity_columns` | ❌ НЕТ | `postgres_sequences` | ❌ НЕТ | Разные названия |

## ❌ ПРОБЛЕМЫ В MS SQL ТАБЛИЦАХ

### **Дублированные связи (table_id + column_id):**
- **`mssql_default_constraints`** - 49 записей с дублированными связями
- **`mssql_identity_columns`** - 110 записей с дублированными связями

### **Таблицы с table_id (12 таблиц):**
- `mssql_check_constraints`, `mssql_columns`, `mssql_default_constraints`
- `mssql_foreign_keys`, `mssql_identity_columns`, `mssql_indexes`
- `mssql_primary_keys`, `mssql_triggers`, `mssql_unique_constraints`

### **Таблицы с column_id (7 таблиц):**
- `mssql_default_constraints`, `mssql_foreign_key_columns`
- `mssql_identity_columns`, `mssql_index_columns`
- `mssql_primary_key_columns`, `mssql_unique_constraint_columns`

## ❌ ПРОБЛЕМЫ В POSTGRESQL ТАБЛИЦАХ

### **Дублированные связи (table_id + column_id):**
- **`postgres_default_constraints`** - 49 записей с дублированными связями
- **`postgres_sequences`** - 110 записей с дублированными связями

### **Таблицы с table_id (9 таблиц):**
- `postgres_check_constraints`, `postgres_columns`, `postgres_default_constraints`
- `postgres_foreign_keys`, `postgres_indexes`, `postgres_primary_keys`
- `postgres_sequences`, `postgres_triggers`, `postgres_unique_constraints`

### **Критические несогласованности данных:**
- **`postgres_unique_constraints`**: 10 записей, но только 2 имеют колонки в `_columns` таблице
- **`mssql_unique_constraints`**: 10 записей, но только 2 имеют колонки в `_columns` таблице

## 🎯 ОБОБЩЕННЫЕ ПРИНЦИПЫ НОРМАЛИЗАЦИИ

### **Уровень принадлежности объектов:**

| Объект | Уровень принадлежности | Основная связь | Дополнительная связь | Действие |
|--------|----------------------|----------------|---------------------|----------|
| **Default Constraints** | Колонка | `column_id` | НЕТ (избыточна) | Убрать `table_id` |
| **Identity Columns/Sequences** | Колонка | `column_id` | НЕТ (избыточна) | Убрать `table_id` |
| **Check Constraints** | Колонка/Таблица | `column_id` | `table_id` (через column) | Создать `_columns` таблицу |
| **Index Columns** | Колонка | `column_id` | `table_id` (через column) | Убрать `table_id` |
| **Unique Constraint Columns** | Колонка | `column_id` | `table_id` (через column) | Убрать `table_id` |
| **Foreign Keys** | Таблица | `table_id` | НЕТ | Оставить `table_id` |
| **Primary Keys** | Таблица | `table_id` | НЕТ | Оставить `table_id` |
| **Triggers** | Таблица | `table_id` | НЕТ | Оставить `table_id` |

## 📋 ОБОБЩЕННЫЙ ПЛАН НОРМАЛИЗАЦИИ

### **🔥 КРИТИЧЕСКИЙ ПРИОРИТЕТ**

#### 1. **Исправить критические проблемы с данными (1 час)**
- **Проблема**: 8 из 10 unique constraints не имеют колонок в `_columns` таблицах
- **Область**: MS SQL + PostgreSQL
- **Действие**: Валидировать и исправить данные в обеих системах

```sql
-- MS SQL
SELECT uc.id, uc.constraint_name, uc.table_id
FROM mcl.mssql_unique_constraints uc
LEFT JOIN mcl.mssql_unique_constraint_columns ucc ON uc.id = ucc.unique_constraint_id
WHERE ucc.unique_constraint_id IS NULL;

-- PostgreSQL
SELECT uc.id, uc.constraint_name, uc.table_id
FROM mcl.postgres_unique_constraints uc
LEFT JOIN mcl.postgres_unique_constraint_columns ucc ON uc.id = ucc.unique_constraint_id
WHERE ucc.unique_constraint_id IS NULL;
```

#### 2. **Создать таблицы для колонок check constraints (1.5 часа)**
- **Проблема**: Отсутствует структура для множественных колонок
- **Область**: MS SQL + PostgreSQL
- **Действие**: Создать `mssql_check_constraint_columns` и `postgres_check_constraint_columns`

```sql
-- MS SQL
CREATE TABLE mcl.mssql_check_constraint_columns (
    id SERIAL PRIMARY KEY,
    check_constraint_id INTEGER NOT NULL,
    column_id INTEGER NOT NULL,
    source_check_constraint_column_id INTEGER,
    ordinal_position INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT mssql_check_constraint_columns_check_constraint_id_fkey 
        FOREIGN KEY (check_constraint_id) REFERENCES mcl.mssql_check_constraints(id),
    CONSTRAINT mssql_check_constraint_columns_column_id_fkey 
        FOREIGN KEY (column_id) REFERENCES mcl.mssql_columns(id)
);

-- PostgreSQL (аналогично)
CREATE TABLE mcl.postgres_check_constraint_columns (...);
```

### **⚡ ВЫСОКИЙ ПРИОРИТЕТ**

#### 3. **Убрать table_id из объектов уровня колонки (1 час)**
- **Таблицы**: `default_constraints`, `identity_columns`/`sequences`
- **Область**: MS SQL + PostgreSQL
- **Обоснование**: Дублирование данных (`table_id` всегда равен `column.table_id`)

```sql
-- MS SQL
ALTER TABLE mcl.mssql_default_constraints DROP COLUMN table_id;
ALTER TABLE mcl.mssql_identity_columns DROP COLUMN table_id;

-- PostgreSQL
ALTER TABLE mcl.postgres_default_constraints DROP COLUMN table_id;
ALTER TABLE mcl.postgres_sequences DROP COLUMN table_id;
```

#### 4. **Убрать table_id из объектов с _columns таблицами (1 час)**
- **Таблицы**: `indexes`, `unique_constraints`, `check_constraints`
- **Область**: MS SQL + PostgreSQL
- **Обоснование**: Избыточная связь при наличии отдельной таблицы колонок

```sql
-- MS SQL
ALTER TABLE mcl.mssql_indexes DROP COLUMN table_id;
ALTER TABLE mcl.mssql_unique_constraints DROP COLUMN table_id;
ALTER TABLE mcl.mssql_check_constraints DROP COLUMN table_id;

-- PostgreSQL
ALTER TABLE mcl.postgres_indexes DROP COLUMN table_id;
ALTER TABLE mcl.postgres_unique_constraints DROP COLUMN table_id;
ALTER TABLE mcl.postgres_check_constraints DROP COLUMN table_id;
```

### **📊 СРЕДНИЙ ПРИОРИТЕТ**

#### 5. **Создать представления для удобства (2 часа)**
- **Цель**: Упростить запросы для разработчиков
- **Область**: MS SQL + PostgreSQL

```sql
-- Представления для MS SQL
CREATE VIEW mcl.v_mssql_default_constraints_by_table AS
SELECT 
    pt.id as table_id,
    pt.object_name as table_name,
    pc.column_name,
    pdc.*
FROM mcl.mssql_default_constraints pdc
JOIN mcl.mssql_columns pc ON pdc.column_id = pc.id
JOIN mcl.mssql_tables pt ON pc.table_id = pt.id;

-- Аналогично для PostgreSQL и других объектов
```

#### 6. **Обновить код и правила (3 часа)**
- **Область**: MS SQL + PostgreSQL
- **Действие**: Обновить все функции миграции и правила проекта

### **✅ НИЗКИЙ ПРИОРИТЕТ**

#### 7. **Оставить table_id в объектах уровня таблицы**
- **Таблицы**: `foreign_keys`, `primary_keys`, `triggers`
- **Область**: MS SQL + PostgreSQL
- **Обоснование**: Логично для объектов, принадлежащих таблице

## 🎯 ОБОБЩЕННЫЕ РЕКОМЕНДАЦИИ ПО ПРИОРИТЕТАМ

| Приоритет | Действие | Область | Время | Обоснование |
|-----------|----------|---------|-------|-------------|
| **КРИТИЧЕСКИЙ** | Исправить критические проблемы с данными | MS SQL + PostgreSQL | 1 час | Несогласованность данных |
| **КРИТИЧЕСКИЙ** | Создать _columns таблицы для check constraints | MS SQL + PostgreSQL | 1.5 часа | Отсутствует структура |
| **ВЫСОКИЙ** | Убрать table_id из объектов уровня колонки | MS SQL + PostgreSQL | 1 час | Дублирование данных |
| **ВЫСОКИЙ** | Убрать table_id из объектов с _columns таблицами | MS SQL + PostgreSQL | 1 час | Избыточная связь |
| **СРЕДНИЙ** | Создать представления для удобства | MS SQL + PostgreSQL | 2 часа | Упрощение запросов |
| **СРЕДНИЙ** | Обновить код и правила | MS SQL + PostgreSQL | 3 часа | Интеграция изменений |
| **НИЗКИЙ** | Оставить table_id в объектах уровня таблицы | MS SQL + PostgreSQL | 0 часов | Логично |

## ⚠️ ВАЖНЫЕ ОСОБЕННОСТИ ОБОБЩЕННОГО ПОДХОДА

### **Синхронность изменений:**
- Все изменения должны выполняться **одновременно** в MS SQL и PostgreSQL
- Поддерживать **идентичность структур** для упрощения миграции
- Обеспечить **обратную совместимость** на время переходного периода

### **Проверка данных:**
- **Множественные колонки** реально используются (22 индекса, 26 FK, 20 PK)
- **Критические несогласованности** требуют немедленного исправления
- **Валидация данных** должна выполняться перед структурными изменениями

### **Представления как мост:**
- Создать **унифицированные представления** для обеих систем
- Обеспечить **прозрачность** для существующего кода
- Подготовить **постепенный переход** на новую архитектуру

## 🏆 ИТОГОВАЯ РЕКОМЕНДАЦИЯ

### **✅ ВЫПОЛНИТЬ ПОЛНУЮ НОРМАЛИЗАЦИЮ ДЛЯ ВСЕЙ СИСТЕМЫ МЕТАДАННЫХ**

**Обоснование:**
1. **🔍 Логическая корректность** - объекты связаны через правильные таблицы колонок
2. **📊 Синхронность структур** - идентичность MS SQL и PostgreSQL метаданных
3. **🏗️ Архитектурная чистота** - устранение дублирования и избыточных связей
4. **⚠️ Критические проблемы** - несогласованность данных требует исправления
5. **📈 Масштабируемость** - правильная основа для развития системы миграции

**Ключевые принципы:**
- **Единообразие** - одинаковые структуры для MS SQL и PostgreSQL
- **Синхронность** - одновременные изменения в обеих системах
- **Постепенность** - поэтапная реализация с минимальными рисками
- **Обратная совместимость** - поддержка существующего кода через представления

**Нормализация всей системы метаданных - это фундаментальная инвестиция в архитектурную чистоту, логическую корректность и долгосрочную стабильность системы миграции.**