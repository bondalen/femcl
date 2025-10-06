# 🗑️ ПЛАН УДАЛЕНИЯ MIGRATION_LOG ИЗ СХЕМЫ AGS

## 📋 Статус плана

**Дата создания:** 29 сентября 2025  
**Задача:** Удаление избыточной таблицы migration_log из схемы ags  
**Статус:** ✅ ПЛАН ГОТОВ К ВЫПОЛНЕНИЮ

## 🎯 Обоснование удаления

### ❌ Причины удаления ags.migration_log:

1. **Дублирование функциональности**
   - Схема mcl уже содержит все необходимые данные для отслеживания
   - Таблицы `mssql_tables` и `postgres_tables` имеют колонки `migration_status`

2. **Избыточность архитектуры**
   - Схема ags предназначена для целевых таблиц данных
   - Схема mcl предназначена для управления миграцией
   - Логирование должно быть в mcl, а не в ags

3. **Пустая таблица**
   - 0 записей в таблице
   - Не используется в текущей работе
   - Занимает место без пользы

4. **Архитектурная чистота**
   - Разделение ответственности: mcl для управления, ags для данных
   - Упрощение структуры базы данных
   - Улучшение производительности

## 🛠️ План удаления

### 📊 Текущее состояние ags.migration_log:

**Структура таблицы:**
```sql
CREATE TABLE ags.migration_log (
    id integer NOT NULL DEFAULT nextval('ags.migration_log_id_seq'::regclass),
    table_name character varying NOT NULL,
    migration_status character varying DEFAULT 'pending'::character varying,
    started_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    rows_migrated integer DEFAULT 0,
    error_message text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
```

**Данные:** 0 записей (пустая таблица)

### 🗑️ Шаги удаления:

#### 1. ✅ Создание резервной копии (опционально)
```sql
-- Создание резервной копии структуры
CREATE TABLE ags.migration_log_backup AS 
SELECT * FROM ags.migration_log;

-- Создание резервной копии последовательности
CREATE SEQUENCE ags.migration_log_id_seq_backup;
SELECT setval('ags.migration_log_id_seq_backup', nextval('ags.migration_log_id_seq'));
```

#### 2. ❌ Удаление таблицы
```sql
-- Удаление таблицы migration_log
DROP TABLE IF EXISTS ags.migration_log;
```

#### 3. ❌ Удаление последовательности
```sql
-- Удаление последовательности
DROP SEQUENCE IF EXISTS ags.migration_log_id_seq;
```

#### 4. ✅ Проверка зависимостей
```sql
-- Проверка, что нет зависимостей
SELECT 
    schemaname, 
    tablename, 
    attname, 
    atttypid::regtype
FROM pg_attribute a
JOIN pg_class c ON a.attrelid = c.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE n.nspname = 'ags' 
AND c.relname = 'migration_log';
```

#### 5. ✅ Проверка прав доступа
```sql
-- Проверка прав на схему ags
SELECT 
    schemaname, 
    tablename, 
    tableowner, 
    hasindexes, 
    hasrules, 
    hastriggers
FROM pg_tables 
WHERE schemaname = 'ags';
```

## 🚀 Альтернативное решение

### ✅ Использование схемы mcl для отслеживания:

**Вместо ags.migration_log использовать:**

#### 📊 Отслеживание через mssql_tables:
```sql
-- Статус миграции исходных таблиц
SELECT 
    object_name,
    migration_status,
    migration_date,
    error_message,
    row_count,
    table_size
FROM mcl.mssql_tables
WHERE migration_status != 'pending'
ORDER BY migration_date DESC;
```

#### 📊 Отслеживание через postgres_tables:
```sql
-- Статус миграции целевых таблиц
SELECT 
    object_name,
    migration_status,
    migration_date,
    error_message,
    row_count,
    data_integrity_percentage
FROM mcl.postgres_tables
WHERE migration_status != 'pending'
ORDER BY migration_date DESC;
```

#### 📊 Связанное отслеживание:
```sql
-- Полная картина миграции
SELECT 
    mt.object_name as source_table,
    pt.object_name as target_table,
    mt.migration_status as source_status,
    pt.migration_status as target_status,
    mt.migration_date as source_date,
    pt.migration_date as target_date,
    mt.error_message as source_error,
    pt.error_message as target_error
FROM mcl.mssql_tables mt
LEFT JOIN mcl.postgres_tables pt ON mt.id = pt.source_table_id
WHERE mt.migration_status != 'pending' OR pt.migration_status != 'pending'
ORDER BY COALESCE(mt.migration_date, pt.migration_date) DESC;
```

## 🎯 Преимущества после удаления

### ✅ Упрощение архитектуры:
- **Четкое разделение ответственности** - mcl для управления, ags для данных
- **Устранение дублирования** - один источник истины для отслеживания
- **Улучшение производительности** - меньше таблиц для обслуживания

### ✅ Улучшение мониторинга:
- **Богатые возможности** - больше метрик в mcl
- **Связанные данные** - исходные и целевые таблицы связаны
- **Детальная статистика** - размеры, длительность, ошибки

### ✅ Готовые запросы:
- **Прогресс миграции** - по задачам и статусам
- **Анализ ошибок** - детальные сообщения
- **Метрики производительности** - время, размеры, целостность

## 🚀 Рекомендации по выполнению

### 1. ✅ Подтвердить удаление
- **Схема mcl готова** для полного отслеживания
- **ags.migration_log избыточна** и не используется
- **Архитектура станет чище** после удаления

### 2. 🗑️ Выполнить удаление
- **Создать резервную копию** (если нужно)
- **Удалить таблицу** и последовательность
- **Проверить зависимости**

### 3. 🚀 Начать миграцию
- **Использовать mcl** для отслеживания
- **Мониторить прогресс** через готовые запросы
- **Анализировать результаты** в реальном времени

## 🎉 Заключение

**Удаление ags.migration_log рекомендуется!**

### ✅ Готовность: 100%
- **Схема mcl готова** для полного отслеживания
- **ags.migration_log избыточна** и не используется
- **Архитектура станет чище** после удаления

### 🚀 Следующие шаги:
1. **Подтвердить удаление** ags.migration_log
2. **Выполнить удаление** по плану
3. **Начать миграцию** с использованием mcl

**Рекомендация: Удалить ags.migration_log и использовать схему mcl для отслеживания!**

---
*План создан: 29 сентября 2025*  
*Автор: AI Assistant*  
*Статус: ГОТОВ К ВЫПОЛНЕНИЮ*