# 📋 ПРИМЕРЫ ПРАВИЛЬНЫХ ЗАПРОСОВ ДЛЯ НОРМАЛИЗОВАННОЙ МЕТАДАННЫХ

## 📊 **СТАТУС ДОКУМЕНТА**

**Дата создания:** 1 октября 2025 г.  
**Задача:** Примеры правильных запросов для работы с нормализованной метаданными  
**Статус:** ✅ **ДОКУМЕНТ СОЗДАН**

---

## 🎯 **ОБЗОР ИЗМЕНЕНИЙ**

После нормализации метаданных **удалены избыточные `table_id`** из объектов уровня колонки и объектов с `_columns` таблицами. Теперь все запросы должны использовать **правильные связи через `_columns` таблицы**.

---

## 🔧 **ПРАВИЛЬНЫЕ ЗАПРОСЫ**

### **1. DEFAULT CONSTRAINTS**

#### **❌ НЕПРАВИЛЬНО (старый способ):**
```sql
-- Прямая связь через table_id (удален)
SELECT pdc.*, pt.object_name
FROM mcl.postgres_default_constraints pdc
JOIN mcl.postgres_tables pt ON pdc.table_id = pt.id
```

#### **✅ ПРАВИЛЬНО (новый способ):**
```sql
-- Связь через column_id
SELECT 
    pdc.id,
    pdc.definition,
    pdc.postgres_definition,
    pt.object_name as table_name,
    pc.column_name
FROM mcl.postgres_default_constraints pdc
JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
```

### **2. CHECK CONSTRAINTS**

#### **❌ НЕПРАВИЛЬНО (старый способ):**
```sql
-- Прямая связь через table_id (удален)
SELECT pcc.*, pt.object_name
FROM mcl.postgres_check_constraints pcc
JOIN mcl.postgres_tables pt ON pcc.table_id = pt.id
```

#### **✅ ПРАВИЛЬНО (новый способ):**
```sql
-- Связь через _columns таблицу (поддерживает множественные колонки)
SELECT 
    pcc.id,
    pcc.constraint_name,
    pcc.definition,
    pcc.postgres_definition,
    pt.object_name as table_name,
    COUNT(pccc.column_id) as column_count,
    STRING_AGG(pc.column_name, ', ') as columns
FROM mcl.postgres_check_constraints pcc
JOIN mcl.postgres_check_constraint_columns pccc ON pcc.id = pccc.check_constraint_id
JOIN mcl.postgres_columns pc ON pccc.column_id = pc.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
GROUP BY pcc.id, pcc.constraint_name, pcc.definition, pcc.postgres_definition, pt.object_name
```

### **3. INDEXES**

#### **❌ НЕПРАВИЛЬНО (старый способ):**
```sql
-- Прямая связь через table_id (удален)
SELECT pi.*, pt.object_name
FROM mcl.postgres_indexes pi
JOIN mcl.postgres_tables pt ON pi.table_id = pt.id
```

#### **✅ ПРАВИЛЬНО (новый способ):**
```sql
-- Связь через _columns таблицу (поддерживает множественные колонки)
SELECT 
    pi.id,
    pi.index_name,
    pi.postgres_definition,
    pt.object_name as table_name,
    COUNT(pic.column_id) as column_count,
    STRING_AGG(pc.column_name, ', ') as columns
FROM mcl.postgres_indexes pi
JOIN mcl.postgres_index_columns pic ON pi.id = pic.index_id
JOIN mcl.postgres_columns pc ON pic.column_id = pc.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
GROUP BY pi.id, pi.index_name, pi.postgres_definition, pt.object_name
```

### **4. FOREIGN KEYS**

#### **❌ НЕПРАВИЛЬНО (старый способ):**
```sql
-- Прямая связь через table_id (удален)
SELECT pfk.*, pt.object_name
FROM mcl.postgres_foreign_keys pfk
JOIN mcl.postgres_tables pt ON pfk.table_id = pt.id
```

#### **✅ ПРАВИЛЬНО (новый способ):**
```sql
-- Связь через _columns таблицу (поддерживает множественные колонки)
SELECT 
    pfk.id,
    pfk.constraint_name,
    pt.object_name as table_name,
    COUNT(pfkc.column_id) as column_count,
    STRING_AGG(pc.column_name, ', ') as columns
FROM mcl.postgres_foreign_keys pfk
JOIN mcl.postgres_foreign_key_columns pfkc ON pfk.id = pfkc.foreign_key_id
JOIN mcl.postgres_columns pc ON pfkc.column_id = pc.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
GROUP BY pfk.id, pfk.constraint_name, pt.object_name
```

### **5. UNIQUE CONSTRAINTS**

#### **❌ НЕПРАВИЛЬНО (старый способ):**
```sql
-- Прямая связь через table_id (удален)
SELECT puc.*, pt.object_name
FROM mcl.postgres_unique_constraints puc
JOIN mcl.postgres_tables pt ON puc.table_id = pt.id
```

#### **✅ ПРАВИЛЬНО (новый способ):**
```sql
-- Связь через _columns таблицу (поддерживает множественные колонки)
SELECT 
    puc.id,
    puc.constraint_name,
    pt.object_name as table_name,
    COUNT(pucc.column_id) as column_count,
    STRING_AGG(pc.column_name, ', ') as columns
FROM mcl.postgres_unique_constraints puc
JOIN mcl.postgres_unique_constraint_columns pucc ON puc.id = pucc.unique_constraint_id
JOIN mcl.postgres_columns pc ON pucc.column_id = pc.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
GROUP BY puc.id, puc.constraint_name, pt.object_name
```

---

## 🎯 **ЗАПРОСЫ С ФИЛЬТРАЦИЕЙ ПО ЗАДАЧЕ**

### **1. Все объекты для конкретной задачи:**

```sql
-- Default constraints для задачи
SELECT 
    pdc.id,
    pdc.definition,
    pt.object_name,
    pc.column_name
FROM mcl.postgres_default_constraints pdc
JOIN mcl.postgres_columns pc ON pdc.column_id = pc.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
WHERE mt.task_id = 2
    AND pdc.definition IS NOT NULL
    AND pdc.function_mapping_rule_id IS NULL
```

```sql
-- Check constraints для задачи
SELECT 
    pcc.id,
    pcc.constraint_name,
    pcc.definition,
    pt.object_name
FROM mcl.postgres_check_constraints pcc
JOIN mcl.postgres_check_constraint_columns pccc ON pcc.id = pccc.check_constraint_id
JOIN mcl.postgres_columns pc ON pccc.column_id = pc.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
WHERE mt.task_id = 2
    AND pcc.definition IS NOT NULL
    AND pcc.function_mapping_rule_id IS NULL
```

### **2. Таблицы БЕЗ foreign keys для задачи:**

```sql
-- Таблицы без внешних ключей
SELECT 
    mt.id,
    mt.object_name,
    mt.schema_name,
    mt.row_count,
    pt.migration_status
FROM mcl.mssql_tables mt
JOIN mcl.postgres_tables pt ON mt.id = pt.source_table_id
WHERE mt.task_id = 2
    AND mt.schema_name = 'ags'
    AND mt.id NOT IN (
        SELECT DISTINCT mt2.id
        FROM mcl.mssql_foreign_keys mfk
        JOIN mcl.mssql_tables mt2 ON mfk.table_id = mt2.id
        WHERE mt2.task_id = 2
    )
    AND pt.migration_status = 'pending'
ORDER BY mt.object_name
```

---

## 📊 **ИСПОЛЬЗОВАНИЕ ПРЕДСТАВЛЕНИЙ**

### **1. Представления для удобства:**

```sql
-- Все default constraints по таблицам
SELECT * FROM mcl.v_postgres_default_constraints_by_table
WHERE table_name = 'accnt'

-- Все check constraints по таблицам  
SELECT * FROM mcl.v_postgres_check_constraints_by_table
WHERE table_name = 'accnt'

-- Все indexes по таблицам
SELECT * FROM mcl.v_postgres_indexes_by_table
WHERE table_name = 'accnt'
```

### **2. Статистика по множественным колонкам:**

```sql
-- Статистика по количеству колонок в объектах
SELECT 
    'CHECK CONSTRAINTS' as object_type,
    COUNT(*) as total_objects,
    AVG(column_count) as avg_columns,
    MAX(column_count) as max_columns
FROM (
    SELECT pcc.id, COUNT(pccc.column_id) as column_count
    FROM mcl.postgres_check_constraints pcc
    JOIN mcl.postgres_check_constraint_columns pccc ON pcc.id = pccc.check_constraint_id
    GROUP BY pcc.id
) check_stats
```

---

## 🚨 **ВАЖНЫЕ ПРИНЦИПЫ**

### **1. Всегда используйте _columns таблицы для объектов с множественными колонками:**
- ✅ **CHECK CONSTRAINTS** → `postgres_check_constraint_columns`
- ✅ **INDEXES** → `postgres_index_columns`
- ✅ **FOREIGN KEYS** → `postgres_foreign_key_columns`
- ✅ **UNIQUE CONSTRAINTS** → `postgres_unique_constraint_columns`

### **2. Для объектов уровня колонки используйте column_id:**
- ✅ **DEFAULT CONSTRAINTS** → `pdc.column_id`
- ✅ **IDENTITY COLUMNS/SEQUENCES** → `column_id`

### **3. Для объектов уровня таблицы table_id остается:**
- ✅ **FOREIGN KEYS** → `pfk.table_id` (основная таблица)
- ✅ **PRIMARY KEYS** → `ppk.table_id`
- ✅ **TRIGGERS** → `ptr.table_id`

---

## 🎯 **ПРОВЕРКА КОРРЕКТНОСТИ**

### **1. Тестирование запросов:**
```sql
-- Проверка, что запрос возвращает данные
EXPLAIN (ANALYZE, BUFFERS) 
SELECT COUNT(*) FROM mcl.postgres_check_constraints pcc
JOIN mcl.postgres_check_constraint_columns pccc ON pcc.id = pccc.check_constraint_id
JOIN mcl.postgres_columns pc ON pccc.column_id = pc.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id;
```

### **2. Валидация множественных колонок:**
```sql
-- Проверка объектов с множественными колонками
SELECT 
    object_type,
    COUNT(*) as multi_column_objects
FROM (
    SELECT 'CHECK CONSTRAINTS' as object_type, pcc.id
    FROM mcl.postgres_check_constraints pcc
    JOIN mcl.postgres_check_constraint_columns pccc ON pcc.id = pccc.check_constraint_id
    GROUP BY pcc.id
    HAVING COUNT(pccc.column_id) > 1
    
    UNION ALL
    
    SELECT 'INDEXES' as object_type, pi.id
    FROM mcl.postgres_indexes pi
    JOIN mcl.postgres_index_columns pic ON pi.id = pic.index_id
    GROUP BY pi.id
    HAVING COUNT(pic.column_id) > 1
) multi_objects
GROUP BY object_type;
```

---

## 🏆 **ЗАКЛЮЧЕНИЕ**

**Все запросы теперь соответствуют нормализованной архитектуре и корректно обрабатывают множественные колонки!**

**Ключевые преимущества:**
- ✅ **Полная поддержка множественных колонок**
- ✅ **Соответствие принципам нормализации**
- ✅ **Улучшенная производительность**
- ✅ **Логическая корректность связей**