# 🔄 СТРАТЕГИЯ МИГРАЦИИ FEMCL

## 📋 Назначение документа
Данный документ описывает детальную стратегию миграции базы данных Fish_Eye из MS SQL Server в PostgreSQL в соответствии с основным замыслом проекта.

---

## 🎯 ОБЗОР СТРАТЕГИИ

### 📊 Концепция
Стратегия основана на **двухэтапном подходе** с четким разделением ответственности:

```
Этап 1: Формирование таблиц и перенос данных
├── 1.1: Формирование метаданных целевой схемы
└── 1.2: Создание объектов и перенос данных

Этап 2: Создание иных объектов БД
├── Индексы
├── Ограничения
├── Триггеры
├── Представления
└── Функции и процедуры
```

**Подробное описание:** [MIGRATION_ALGORITHM.md](../overview/MIGRATION_ALGORITHM.md)

---

## 📋 ЭТАП 1: ФОРМИРОВАНИЕ ТАБЛИЦ И ПЕРЕНОС ДАННЫХ

### 🔧 **Этап 1.1: Формирование метаданных целевой схемы**

#### 🎯 Цель
Создание полных метаданных всех таблиц целевой схемы PostgreSQL на основе исходной схемы MS SQL Server.

#### 📊 Процесс выполнения

##### 1. **Анализ исходной схемы**
```sql
-- Анализ таблиц MS SQL Server
SELECT 
    TABLE_NAME,
    TABLE_TYPE,
    TABLE_SCHEMA
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'ags'
ORDER BY TABLE_NAME;
```

##### 2. **Анализ колонок**
```sql
-- Анализ колонок MS SQL Server
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    CHARACTER_MAXIMUM_LENGTH,
    NUMERIC_PRECISION,
    NUMERIC_SCALE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ags'
ORDER BY TABLE_NAME, ORDINAL_POSITION;
```

##### 3. **Разрешение коллизий между СУБД**
- **Маппинг типов данных:** MS SQL → PostgreSQL
- **Обработка специфичных функций:** CONVERT, CAST, ISNULL
- **Разрешение различий в синтаксисе:** TOP → LIMIT, IDENTITY → SERIAL

##### 4. **Создание метаданных в схеме mcl**
```sql
-- Создание метаданных таблиц
INSERT INTO mcl.tables (table_name, source_schema, target_schema, status)
SELECT 
    TABLE_NAME,
    'ags' as source_schema,
    'ags' as target_schema,
    'pending' as status
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'ags';

-- Создание метаданных колонок
INSERT INTO mcl.columns (table_name, column_name, source_type, target_type, is_nullable, default_value)
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE as source_type,
    CASE 
        WHEN DATA_TYPE = 'varchar' THEN 'VARCHAR'
        WHEN DATA_TYPE = 'int' THEN 'INTEGER'
        WHEN DATA_TYPE = 'datetime' THEN 'TIMESTAMP'
        -- ... другие маппинги
    END as target_type,
    IS_NULLABLE = 'YES' as is_nullable,
    COLUMN_DEFAULT as default_value
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ags';
```

#### ✅ Критерии завершения
- [ ] Все таблицы проанализированы
- [ ] Метаданные созданы в схеме mcl
- [ ] Коллизии между СУБД разрешены
- [ ] Валидация метаданных пройдена

---

### 🔄 **Этап 1.2: Создание объектов и перенос данных**

#### 🎯 Цель
Создание физических таблиц в PostgreSQL и перенос данных с учетом связанности таблиц. **Включает создание всех объектов таблиц (индексы, ограничения, триггеры) совместно с таблицами.**

#### 📊 Алгоритм выполнения

##### 1. **Анализ зависимостей**
```sql
-- Анализ внешних ключей MS SQL Server
SELECT 
    fk.TABLE_NAME as child_table,
    fk.COLUMN_NAME as child_column,
    pk.TABLE_NAME as parent_table,
    pk.COLUMN_NAME as parent_column
FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fk 
    ON rc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk 
    ON rc.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME
WHERE fk.TABLE_SCHEMA = 'ags';
```

##### 2. **Определение порядка миграции**
- **Таблицы без внешних ключей** - мигрируются первыми
- **Таблицы с внешними ключами** - мигрируются после родительских таблиц
- **Циклические зависимости** - разрешаются специальными алгоритмами

##### 3. **Последовательная миграция таблиц**
```python
def migrate_table_sequence():
    """Последовательная миграция таблиц с учетом зависимостей"""
    
    # Получение списка таблиц в правильном порядке
    tables = get_migration_order()
    
    for table in tables:
        try:
            # Создание структуры таблицы
            create_table_structure(table)
            
            # Создание индексов таблицы
            create_table_indexes(table)
            
            # Создание ограничений таблицы
            create_table_constraints(table)
            
            # Создание триггеров таблицы (простые и стандартные)
            create_table_triggers(table)
            
            # Перенос данных
            migrate_table_data(table)
            
            # Валидация переноса
            validate_migration(table)
            
            # Обновление статуса
            update_migration_status(table, 'completed')
            
        except Exception as e:
            # Обработка ошибок
            log_error(table, e)
            update_migration_status(table, 'failed')
            raise
```

##### 4. **Создание структуры таблицы**
```sql
-- Создание таблицы в PostgreSQL
CREATE TABLE ags.table_name (
    column1 INTEGER NOT NULL,
    column2 VARCHAR(255),
    column3 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (column1)
);
```

##### 5. **Перенос данных**
```python
def migrate_table_data(table_name):
    """Перенос данных из MS SQL Server в PostgreSQL"""
    
    # Получение данных из MS SQL Server
    source_data = get_source_data(table_name)
    
    # Преобразование данных
    transformed_data = transform_data(source_data)
    
    # Вставка в PostgreSQL
    insert_target_data(table_name, transformed_data)
    
    # Проверка количества записей
    validate_record_count(table_name)
```

##### 6. **Валидация переноса**
```sql
-- Проверка количества записей
SELECT 
    (SELECT COUNT(*) FROM mssql.ags.table_name) as source_count,
    (SELECT COUNT(*) FROM postgres.ags.table_name) as target_count;

-- Проверка целостности данных
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT primary_key) as unique_records
FROM postgres.ags.table_name;
```

#### ✅ Критерии завершения
- [ ] Все 166 таблиц созданы в PostgreSQL
- [ ] Все индексы таблиц созданы
- [ ] Все ограничения таблиц созданы
- [ ] Простые и стандартные триггеры таблиц созданы
- [ ] Сложные триггеры отложены на Этап 2
- [ ] Все данные перенесены
- [ ] Валидация пройдена для всех таблиц
- [ ] Статус миграции обновлен

---

## 📋 ЭТАП 2: СОЗДАНИЕ ИНЫХ ОБЪЕКТОВ БД

### 🎯 Цель
Создание всех объектов базы данных, **не являющихся элементами таблиц**, которые ссылаются на таблицы, созданные на этапе 1.

### 📊 Последовательность создания

#### 1. **Пользовательские типы**
```sql
-- Создание пользовательских типов
CREATE TYPE ags.status_type AS ENUM ('active', 'inactive', 'pending');
CREATE TYPE ags.priority_type AS ENUM ('low', 'medium', 'high', 'critical');
```

#### 2. **Последовательности**
```sql
-- Создание последовательностей для генерации значений
CREATE SEQUENCE ags.seq_order_number START 1000;
CREATE SEQUENCE ags.seq_invoice_number START 1;
```

#### 3. **Функции (табличные и скалярные)**
```sql
-- Создание скалярных функций
CREATE OR REPLACE FUNCTION ags.calculate_total(amount DECIMAL)
RETURNS DECIMAL AS $$
BEGIN
    RETURN amount * 1.2; -- НДС 20%
END;
$$ LANGUAGE plpgsql;

-- Создание табличных функций
CREATE OR REPLACE FUNCTION ags.get_user_orders(user_id INTEGER)
RETURNS TABLE(order_id INTEGER, order_date DATE, total_amount DECIMAL) AS $$
BEGIN
    RETURN QUERY
    SELECT o.id, o.order_date, o.total_amount
    FROM ags.orders o
    WHERE o.user_id = user_id;
END;
$$ LANGUAGE plpgsql;
```

#### 4. **Хранимые процедуры**
```sql
-- Создание хранимых процедур
CREATE OR REPLACE PROCEDURE ags.process_order(
    IN p_user_id INTEGER,
    IN p_order_data JSON,
    OUT p_order_id INTEGER
) AS $$
BEGIN
    -- Логика обработки заказа
    INSERT INTO ags.orders (user_id, order_data, created_at)
    VALUES (p_user_id, p_order_data, CURRENT_TIMESTAMP)
    RETURNING id INTO p_order_id;
    
    -- Дополнительная обработка
    PERFORM ags.update_user_statistics(p_user_id);
END;
$$ LANGUAGE plpgsql;
```

#### 5. **Представления**
```sql
-- Создание представлений для упрощения доступа
CREATE VIEW ags.user_orders_summary AS
SELECT 
    u.id as user_id,
    u.name as user_name,
    COUNT(o.id) as total_orders,
    SUM(o.total_amount) as total_spent
FROM ags.users u
LEFT JOIN ags.orders o ON u.id = o.user_id
GROUP BY u.id, u.name;
```

#### 6. **Правила и операторы**
```sql
-- Создание правил для автоматизации
CREATE RULE ags.orders_audit_rule AS
    ON INSERT TO ags.orders
    DO ALSO
    INSERT INTO ags.audit_log (table_name, operation, record_id, timestamp)
    VALUES ('orders', 'INSERT', NEW.id, CURRENT_TIMESTAMP);

-- Создание операторов
CREATE OPERATOR ags.@> (LEFTARG = JSONB, RIGHTARG = JSONB)
    FUNCTION jsonb_contains;
```

#### 7. **Агрегаты**
```sql
-- Создание агрегатных функций
CREATE OR REPLACE FUNCTION ags.median_final(state DECIMAL[])
RETURNS DECIMAL AS $$
BEGIN
    -- Логика вычисления медианы
    RETURN state[array_length(state, 1) / 2];
END;
$$ LANGUAGE plpgsql;

CREATE AGGREGATE ags.median(DECIMAL) (
    SFUNC = array_append,
    STYPE = DECIMAL[],
    FINALFUNC = ags.median_final
);
```

---

## 🔄 УПРАВЛЕНИЕ ПРОЦЕССОМ МИГРАЦИИ

### 📊 Мониторинг прогресса
- **Отслеживание статуса** каждой таблицы
- **Логирование операций** в схеме mcl
- **Уведомления об ошибках** и проблемах
- **Отчеты о прогрессе** в реальном времени

### 🚨 Обработка ошибок
- **Автоматический откат** при критических ошибках
- **Ручное вмешательство** для сложных случаев
- **Повторные попытки** для временных сбоев
- **Документирование проблем** и решений

### 🔧 Оптимизация производительности
- **Параллельная обработка** независимых таблиц
- **Батчевая вставка** данных
- **Оптимизация запросов** для больших объемов
- **Мониторинг ресурсов** системы

---

## 📊 КРИТЕРИИ УСПЕХА

### ✅ **Этап 1.1 - Метаданные**
- [ ] 166 таблиц проанализированы
- [ ] Метаданные созданы в схеме mcl
- [ ] Коллизии между СУБД разрешены
- [ ] Валидация метаданных пройдена

### ✅ **Этап 1.2 - Таблицы и данные**
- [ ] Все 166 таблиц созданы в PostgreSQL
- [ ] Все индексы таблиц созданы
- [ ] Все ограничения таблиц созданы
- [ ] Простые и стандартные триггеры таблиц созданы
- [ ] Сложные триггеры отложены на Этап 2
- [ ] Все данные перенесены без потерь
- [ ] Валидация целостности данных пройдена
- [ ] Производительность соответствует требованиям

### ✅ **Этап 2 - Иные объекты**
- [ ] Все пользовательские типы созданы
- [ ] Все последовательности созданы
- [ ] Все функции (табличные и скалярные) созданы
- [ ] Все хранимые процедуры созданы
- [ ] Все представления созданы
- [ ] Все правила и операторы созданы
- [ ] Все агрегаты созданы
- [ ] Сложные триггеры адаптированы и созданы

---

## 🎯 ПЛАНЫ РАЗВИТИЯ

### 🔄 **Краткосрочные (1-2 недели)**
- Завершить этап 1.2 - миграция всех 166 таблиц
- Реализовать автоматическое создание простых триггеров
- Оптимизировать производительность переноса данных
- Улучшить систему мониторинга

### 🚀 **Среднесрочные (1-2 месяца)**
- Реализовать этап 2 - создание иных объектов БД
- Адаптировать сложные триггеры вручную
- Создать автоматизированную систему тестирования
- Добавить веб-интерфейс для управления

### 🌟 **Долгосрочные (3-6 месяцев)**
- Поддержка других СУБД
- Система автоматического восстановления
- Интеграция с системами мониторинга

## 🔗 Связанные документы

### 🔄 Алгоритм миграции
- **[MIGRATION_ALGORITHM.md](../overview/MIGRATION_ALGORITHM.md)** - Детальный алгоритм выполнения

### 🏗️ Архитектура системы
- **[MODULE_ARCHITECTURE.md](../architecture/MODULE_ARCHITECTURE.md)** - Архитектура модулей

### 🔧 Система маппинга функций
- **[FUNCTION_MAPPING_SYSTEM.md](./FUNCTION_MAPPING_SYSTEM.md)** - Система маппинга функций MS SQL → PostgreSQL

### 🚨 Обработка ошибок
- **[ERROR_HANDLING.md](../development/ERROR_HANDLING.md)** - Обработка ошибок и восстановление

### 📊 Критерии успеха
- **[CRITERIA_SUCCESS.md](../development/CRITERIA_SUCCESS.md)** - Критерии успеха миграции

---

*Документ создан: 27 января 2025*
*Автор: AI Assistant*
*Статус: АКТУАЛЬНЫЙ*