# 📋 ПРАВИЛА ПРОВЕРКИ ГОТОВНОСТИ ТАБЛИЦЫ К СОЗДАНИЮ В ЦЕЛЕВОЙ БД

## 🎯 Назначение документа
Данный документ определяет порядок и правила проверки готовности таблицы к созданию в целевой базе данных PostgreSQL в рамках проекта миграции FEMCL.

---

## 🏗️ ИЕРАРХИЯ ОБЪЕКТОВ В СХЕМЕ MCL

### 📊 **Родительские таблицы (уровень 1)**
- `mssql_objects` - исходные объекты MS SQL
- `postgres_objects` - целевые объекты PostgreSQL

### 📊 **Дочерние таблицы (уровень 2)**
- `mssql_tables` - исходные таблицы MS SQL
- `postgres_tables` - целевые таблицы PostgreSQL

### 📊 **Связанные таблицы (уровень 3)**
- `mssql_columns` / `postgres_columns` - колонки
- `mssql_indexes` / `postgres_indexes` - индексы
- `mssql_primary_keys` / `postgres_primary_keys` - первичные ключи
- `mssql_foreign_keys` / `postgres_foreign_keys` - внешние ключи
- `mssql_unique_constraints` / `postgres_unique_constraints` - уникальные ограничения
- `mssql_check_constraints` / `postgres_check_constraints` - проверочные ограничения
- `mssql_default_constraints` / `postgres_default_constraints` - ограничения по умолчанию
- `mssql_triggers` / `postgres_triggers` - триггеры
- `mssql_identity_columns` / `postgres_sequences` - identity колонки/последовательности
- `problems_tb_slt_mp` - проблемы и их решения

---

## 📋 ПОРЯДОК ПРОВЕРКИ ГОТОВНОСТИ

### 🔍 **ЭТАП 1: Проверка родительских объектов**

#### 1.1 Проверка исходного объекта (mssql_objects)
```sql
SELECT id, object_name, object_type, schema_name, migration_status, 
       object_description, create_date, modify_date
FROM mcl.mssql_objects 
WHERE object_name = '<table_name>' OR id = <table_id>;
```

**Критерии готовности:**
- ✅ Запись должна существовать
- ✅ `object_type` должен быть 'BASE TABLE'
- ✅ `schema_name` должен быть определен
- ✅ `migration_status` может быть 'pending' или 'ready'

#### 1.2 Проверка целевого объекта (postgres_objects)
```sql
SELECT id, object_name, object_type, schema_name, migration_status,
       create_date, modify_date
FROM mcl.postgres_objects 
WHERE object_name = '<table_name>' OR id = <target_table_id>;
```

**Критерии готовности:**
- ✅ Запись должна существовать
- ✅ `object_type` должен быть 'BASE TABLE'
- ✅ `schema_name` должен быть определен
- ✅ `migration_status` должен быть 'ready' для создания

### 🔍 **ЭТАП 2: Проверка дочерних таблиц**

#### 2.1 Проверка исходной таблицы (mssql_tables)
```sql
SELECT id, object_name, primary_key_count, foreign_key_count, 
       index_count, column_count, row_count, table_size
FROM mcl.mssql_tables 
WHERE id = <table_id>;
```

**Критерии готовности:**
- ✅ Запись должна существовать
- ✅ `object_name` должен соответствовать исходному объекту
- ✅ Все счетчики должны быть заполнены (≥ 0)

#### 2.2 Проверка целевой таблицы (postgres_tables)
```sql
SELECT id, source_table_id, object_name, has_primary_key, 
       has_foreign_keys, has_indexes, has_triggers, column_count,
       row_count, table_size, data_integrity_percentage, migration_status
FROM mcl.postgres_tables 
WHERE id = <target_table_id>;
```

**Критерии готовности:**
- ✅ Запись должна существовать
- ✅ `source_table_id` должен ссылаться на исходную таблицу
- ✅ `has_primary_key`, `has_foreign_keys`, `has_indexes`, `has_triggers` должны быть определены
- ✅ `column_count`, `row_count`, `table_size` должны быть заполнены
- ✅ `data_integrity_percentage` должен быть 100.0
- ✅ `migration_status` должен быть 'ready'

### 🔍 **ЭТАП 3: Проверка связанных объектов**

#### 3.1 Проверка колонок
```sql
-- Исходные колонки
SELECT COUNT(*) as source_columns FROM mcl.mssql_columns WHERE table_id = <table_id>;

-- Целевые колонки
SELECT COUNT(*) as target_columns FROM mcl.postgres_columns WHERE table_id = <target_table_id>;
```

**Критерии готовности:**
- ✅ Количество исходных и целевых колонок должно совпадать
- ✅ Все целевые колонки должны иметь `type_mapping_quality = 'excellent'`
- ✅ Все целевые колонки должны иметь `data_type_migration_status = 'ready'`

#### 3.2 Проверка индексов
```sql
-- Исходные индексы
SELECT COUNT(*) as source_indexes FROM mcl.mssql_indexes WHERE table_id = <table_id>;

-- Целевые индексы
SELECT COUNT(*) as target_indexes FROM mcl.postgres_indexes WHERE table_id = <target_table_id>;
```

**Критерии готовности:**
- ✅ Количество исходных и целевых индексов должно совпадать
- ✅ Первичный ключ должен быть создан в целевых индексах
- ✅ Все целевые индексы должны иметь корректные имена

#### 3.3 Проверка первичных ключей
```sql
-- Исходные первичные ключи
SELECT COUNT(*) as source_pk FROM mcl.mssql_primary_keys WHERE table_id = <table_id>;

-- Целевые первичные ключи
SELECT COUNT(*) as target_pk FROM mcl.postgres_primary_keys WHERE table_id = <target_table_id>;
```

**Критерии готовности:**
- ✅ Количество исходных и целевых первичных ключей должно совпадать
- ✅ Целевой первичный ключ должен иметь корректное имя

#### 3.4 Проверка внешних ключей
```sql
-- Исходные внешние ключи
SELECT COUNT(*) as source_fk FROM mcl.mssql_foreign_keys WHERE table_id = <table_id>;

-- Целевые внешние ключи
SELECT COUNT(*) as target_fk FROM mcl.postgres_foreign_keys WHERE table_id = <target_table_id>;
```

**Критерии готовности:**
- ✅ Количество исходных и целевых внешних ключей должно совпадать
- ✅ Если внешних ключей нет (0), то это нормально

#### 3.5 Проверка других ограничений
```sql
-- Уникальные ограничения
SELECT COUNT(*) as source_unique FROM mcl.mssql_unique_constraints WHERE table_id = <table_id>;
SELECT COUNT(*) as target_unique FROM mcl.postgres_unique_constraints WHERE table_id = <target_table_id>;

-- Проверочные ограничения
SELECT COUNT(*) as source_check FROM mcl.mssql_check_constraints WHERE table_id = <table_id>;
SELECT COUNT(*) as target_check FROM mcl.postgres_check_constraints WHERE table_id = <target_table_id>;

-- Ограничения по умолчанию
SELECT COUNT(*) as source_default FROM mcl.mssql_default_constraints WHERE table_id = <table_id>;
SELECT COUNT(*) as target_default FROM mcl.postgres_default_constraints WHERE table_id = <target_table_id>;
```

**Критерии готовности:**
- ✅ Количество исходных и целевых ограничений должно совпадать

#### 3.6 Проверка триггеров
```sql
-- Исходные триггеры
SELECT COUNT(*) as source_triggers FROM mcl.mssql_triggers WHERE table_id = <table_id>;

-- Целевые триггеры
SELECT COUNT(*) as target_triggers FROM mcl.postgres_triggers WHERE table_id = <target_table_id>;
```

**Критерии готовности:**
- ✅ Количество исходных и целевых триггеров должно совпадать

#### 3.7 Проверка identity колонок/последовательностей
```sql
-- Исходные identity колонки
SELECT COUNT(*) as source_identity FROM mcl.mssql_identity_columns WHERE table_id = <table_id>;

-- Целевые последовательности
SELECT COUNT(*) as target_sequences FROM mcl.postgres_sequences WHERE table_id = <target_table_id>;
```

**Критерии готовности:**
- ✅ Количество исходных identity колонок и целевых последовательностей должно совпадать

#### 3.8 Проверка проблем
```sql
-- Проблемы и их решения
SELECT COUNT(*) as problems FROM mcl.problems_tb_slt_mp WHERE table_id = <table_id>;
```

**Критерии готовности:**
- ✅ Проблем не должно быть (COUNT = 0) или все проблемы должны быть решены

---

## 📊 КРИТЕРИИ ОЦЕНКИ ГОТОВНОСТИ

### ✅ **100% ГОТОВА**
- Все родительские объекты присутствуют
- Все дочерние таблицы готовы
- Все связанные объекты созданы
- Метаданные заполнены
- Статус миграции 'ready'
- Нет нерешенных проблем

### ⚠️ **95-99% ГОТОВА**
- Родительские объекты присутствуют
- Дочерние таблицы готовы
- Связанные объекты созданы
- Метаданные частично заполнены
- Статус миграции 'pending' или 'ready'
- Нет критических проблем

### ❌ **<95% ГОТОВА**
- Отсутствуют родительские объекты
- Отсутствуют дочерние таблицы
- Отсутствуют связанные объекты
- Метаданные не заполнены
- Статус миграции 'pending'
- Есть нерешенные проблемы

---

## 🚀 АЛГОРИТМ ПРОВЕРКИ

### 1. **Инициализация**
- Определить ID исходной таблицы
- Определить ID целевой таблицы
- Проверить существование записей

### 2. **Проверка иерархии**
- Проверить родительские объекты
- Проверить дочерние таблицы
- Проверить связи между объектами

### 3. **Проверка связанных объектов**
- Проверить колонки
- Проверить индексы
- Проверить ограничения
- Проверить триггеры
- Проверить identity/последовательности

### 4. **Проверка метаданных**
- Проверить заполненность метаданных
- Проверить статус миграции
- Проверить качество маппинга

### 5. **Проверка проблем**
- Проверить наличие проблем
- Проверить статус решений

### 6. **Формирование отчета**
- Подсчитать процент готовности
- Определить критические проблемы
- Сформировать рекомендации

---

## 📋 ШАБЛОН ПРОВЕРКИ

```sql
-- Шаблон для проверки готовности таблицы
WITH readiness_check AS (
    -- Проверка родительских объектов
    SELECT 'parent_objects' as check_type, 
           CASE WHEN EXISTS(SELECT 1 FROM mcl.mssql_objects WHERE id = <table_id>) 
                AND EXISTS(SELECT 1 FROM mcl.postgres_objects WHERE id = <target_table_id>)
                THEN 1 ELSE 0 END as is_ready,
           2 as weight
    
    UNION ALL
    
    -- Проверка дочерних таблиц
    SELECT 'child_tables' as check_type,
           CASE WHEN EXISTS(SELECT 1 FROM mcl.mssql_tables WHERE id = <table_id>)
                AND EXISTS(SELECT 1 FROM mcl.postgres_tables WHERE id = <target_table_id>)
                THEN 1 ELSE 0 END as is_ready,
           3 as weight
    
    UNION ALL
    
    -- Проверка колонок
    SELECT 'columns' as check_type,
           CASE WHEN (SELECT COUNT(*) FROM mcl.mssql_columns WHERE table_id = <table_id>) = 
                     (SELECT COUNT(*) FROM mcl.postgres_columns WHERE table_id = <target_table_id>)
                THEN 1 ELSE 0 END as is_ready,
           2 as weight
    
    UNION ALL
    
    -- Проверка индексов
    SELECT 'indexes' as check_type,
           CASE WHEN (SELECT COUNT(*) FROM mcl.mssql_indexes WHERE table_id = <table_id>) = 
                     (SELECT COUNT(*) FROM mcl.postgres_indexes WHERE table_id = <target_table_id>)
                THEN 1 ELSE 0 END as is_ready,
           2 as weight
    
    UNION ALL
    
    -- Проверка метаданных
    SELECT 'metadata' as check_type,
           CASE WHEN (SELECT has_primary_key FROM mcl.postgres_tables WHERE id = <target_table_id>) IS NOT NULL
                THEN 1 ELSE 0 END as is_ready,
           1 as weight
)
SELECT 
    check_type,
    is_ready,
    weight,
    ROUND(SUM(is_ready * weight) * 100.0 / SUM(weight), 2) as readiness_percentage
FROM readiness_check
GROUP BY check_type, is_ready, weight;
```

---

## 📞 ПОДДЕРЖКА

При возникновении вопросов по применению правил:
1. Обратитесь к примерам в отчетах проекта
2. Проверьте соответствие иерархии объектов
3. Убедитесь в корректности связей между таблицами

---

*Документ создан: $(date)*
*Версия: 1.0*
*Статус: АКТУАЛЬНЫЙ*



