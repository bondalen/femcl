# 📋 ПРАВИЛА СОЗДАНИЯ ТАБЛИЦЫ В ЦЕЛЕВОЙ БД

## 🎯 Цель
Определить порядок и правила создания таблицы в целевой базе данных PostgreSQL (схема `ags`) на основе метаданных, хранящихся в схеме `mcl`.

## 🏗️ Иерархия объектов в схеме MCL

### **Исходные объекты (MS SQL Server):**
```
mssql_objects (родительская таблица)
├── mssql_tables (таблицы)
├── mssql_columns (колонки)
├── mssql_indexes (индексы)
├── mssql_primary_keys (первичные ключи)
├── mssql_foreign_keys (внешние ключи)
└── mssql_constraints (ограничения)
```

### **Целевые объекты (PostgreSQL):**
```
postgres_objects (родительская таблица)
├── postgres_tables (таблицы)
├── postgres_columns (колонки)
├── postgres_indexes (индексы)
├── postgres_primary_keys (первичные ключи)
├── postgres_foreign_keys (внешние ключи)
└── postgres_constraints (ограничения)
```

## 📊 ПРОЦЕСС СОЗДАНИЯ ТАБЛИЦЫ

### **Этап 1: Проверка готовности таблицы**

#### **1.1 Проверка существования исходной таблицы**
```sql
-- Проверяем наличие таблицы в mssql_tables
SELECT id, object_name, object_type, schema_name
FROM mcl.mssql_tables 
WHERE id = [TABLE_ID];
```

#### **1.2 Проверка существования целевой таблицы**
```sql
-- Проверяем наличие целевой таблицы в postgres_tables
SELECT id, object_name, object_type, schema_name
FROM mcl.postgres_tables 
WHERE id = [TARGET_TABLE_ID];
```

#### **1.3 Проверка колонок исходной таблицы**
```sql
-- Получаем информацию о колонках исходной таблицы
SELECT 
    mc.column_name,
    mc.ordinal_position,
    mc.is_identity,
    mc.default_value
FROM mcl.mssql_tables mt
JOIN mcl.mssql_columns mc ON mt.id = mc.table_id
WHERE mt.id = [TABLE_ID]
ORDER BY mc.ordinal_position;
```

#### **1.4 Проверка колонок целевой таблицы**
```sql
-- Получаем информацию о колонках целевой таблицы
SELECT 
    pc.column_name,
    pc.ordinal_position,
    pdt.typname_with_params as postgres_type,
    pc.is_identity,
    pc.default_value
FROM mcl.postgres_tables pt
JOIN mcl.postgres_columns pc ON pt.id = pc.table_id
JOIN mcl.postgres_derived_types pdt ON pc.postgres_data_type_id = pdt.id
WHERE pt.id = [TARGET_TABLE_ID]
ORDER BY pc.ordinal_position;
```

### **Этап 2: Генерация DDL для создания таблицы**

#### **2.1 Структура DDL для таблицы**
```sql
CREATE TABLE ags.[table_name] (
    [column_definitions]
    [constraints]
);
```

#### **2.2 Определение колонок**
- **IDENTITY колонки:** `GENERATED ALWAYS AS IDENTITY`
- **NOT NULL колонки:** `NOT NULL`
- **DEFAULT значения:** `DEFAULT [value]`
- **Типы данных:** Используются из `postgres_derived_types.typname_with_params`

#### **2.3 Первичные ключи**
- **IDENTITY колонки:** Автоматически становятся PRIMARY KEY
- **Составные ключи:** `PRIMARY KEY (col1, col2, ...)`

### **Этап 3: Создание таблицы в PostgreSQL**

#### **3.1 Выполнение DDL**
```sql
-- Пример создания таблицы accnt
CREATE TABLE ags.accnt (
    account_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_num INTEGER NOT NULL,
    account_name VARCHAR(255) NOT NULL
);
```

#### **3.2 Проверка создания таблицы**
```sql
-- Проверяем структуру созданной таблицы
SELECT 
    table_schema,
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'ags' AND table_name = '[table_name]'
ORDER BY ordinal_position;
```

#### **3.3 Проверка индексов**
```sql
-- Проверяем созданные индексы
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'ags' AND tablename = '[table_name]';
```

## 🔍 ПРОВЕРКИ КАЧЕСТВА

### **Обязательные проверки:**
1. ✅ **Таблица создана** в правильной схеме (`ags`)
2. ✅ **Все колонки созданы** согласно метаданным
3. ✅ **Типы данных соответствуют** целевым типам
4. ✅ **Первичные ключи созданы** корректно
5. ✅ **IDENTITY колонки работают** правильно
6. ✅ **NOT NULL ограничения** применены

### **Дополнительные проверки:**
1. 🔍 **Индексы созданы** (если есть)
2. 🔍 **Ограничения применены** (если есть)
3. 🔍 **Комментарии добавлены** (если есть)

## 📝 ШАБЛОН DDL ДЛЯ ТАБЛИЦЫ

```sql
-- Создание таблицы [table_name] в схеме ags
CREATE TABLE ags.[table_name] (
    [column_name] [data_type] [constraints],
    [column_name] [data_type] [constraints],
    [column_name] [data_type] [constraints],
    PRIMARY KEY ([primary_key_columns])
);

-- Создание индексов (если необходимо)
CREATE INDEX [index_name] ON ags.[table_name] ([column_name]);

-- Создание ограничений (если необходимо)
ALTER TABLE ags.[table_name] 
ADD CONSTRAINT [constraint_name] [constraint_definition];
```

## 🚨 ВАЖНЫЕ МОМЕНТЫ

### **Идентификаторы:**
- **IDENTITY колонки:** Всегда `GENERATED ALWAYS AS IDENTITY`
- **Первичные ключи:** Автоматически создаются для IDENTITY колонок
- **Составные ключи:** Явно указываются в DDL

### **Типы данных:**
- **Используются типы** из `postgres_derived_types.typname_with_params`
- **Параметры типов** (длина, точность) учитываются
- **NULL/NOT NULL** определяется из метаданных

### **Схема:**
- **Все таблицы создаются** в схеме `ags`
- **Схема должна существовать** перед созданием таблиц
- **Права доступа** настроены для пользователя `postgres`

## 📊 ЛОГИРОВАНИЕ И ОТЧЕТНОСТЬ

### **Обязательные записи:**
1. 📝 **Время создания** таблицы
2. 📝 **Количество колонок** создано
3. 📝 **Количество индексов** создано
4. 📝 **Ошибки** (если есть)
5. 📝 **Предупреждения** (если есть)

### **Формат отчета:**
```markdown
## 📋 ОТЧЕТ О СОЗДАНИИ ТАБЛИЦЫ [table_name]

### ✅ Результат: УСПЕШНО
- **Время создания:** [timestamp]
- **Схема:** ags
- **Колонок:** [count]
- **Индексов:** [count]
- **Ошибок:** 0

### 📊 Структура таблицы:
| Колонка | Тип | Ограничения |
|---------|-----|-------------|
| [col1] | [type1] | [constraints1] |
| [col2] | [type2] | [constraints2] |
```

## 🎯 СЛЕДУЮЩИЕ ШАГИ

После успешного создания таблицы:
1. **Обновить статус** в `postgres_tables.status = 'created'`
2. **Записать время создания** в `postgres_tables.created_at`
3. **Подготовить следующую таблицу** к созданию
4. **Проверить зависимости** для таблиц с внешними ключами

---

**Дата создания:** [current_date]  
**Версия:** 1.0  
**Автор:** FEMCL Migration System
