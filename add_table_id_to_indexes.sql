-- Добавление table_id в таблицы индексов
-- Дата: 2025-10-02
-- Проект: FEMCL

BEGIN;

-- 1. Добавляем колонку table_id в mssql_indexes
ALTER TABLE mcl.mssql_indexes 
ADD COLUMN table_id INTEGER;

-- 2. Добавляем колонку table_id в postgres_indexes  
ALTER TABLE mcl.postgres_indexes 
ADD COLUMN table_id INTEGER;

-- 3. Заполняем table_id в mssql_indexes на основе связей
UPDATE mcl.mssql_indexes 
SET table_id = (
    SELECT DISTINCT mt.id 
    FROM mcl.mssql_tables mt
    JOIN mcl.mssql_columns mc ON mt.id = mc.table_id
    JOIN mcl.mssql_index_columns mic ON mc.id = mic.column_id
    WHERE mic.index_id = mssql_indexes.id
    LIMIT 1
)
WHERE table_id IS NULL;

-- 4. Заполняем table_id в postgres_indexes на основе связей через source_index_id
UPDATE mcl.postgres_indexes 
SET table_id = (
    SELECT DISTINCT pt.id 
    FROM mcl.postgres_tables pt
    JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
    JOIN mcl.mssql_columns mc ON mt.id = mc.table_id
    JOIN mcl.mssql_index_columns mic ON mc.id = mic.column_id
    JOIN mcl.mssql_indexes mi ON mic.index_id = mi.id
    WHERE mi.id = postgres_indexes.source_index_id
    LIMIT 1
)
WHERE table_id IS NULL;

-- 5. Создаем внешние ключи
ALTER TABLE mcl.mssql_indexes 
ADD CONSTRAINT fk_mssql_indexes_table_id 
FOREIGN KEY (table_id) REFERENCES mcl.mssql_tables(id) ON DELETE CASCADE;

ALTER TABLE mcl.postgres_indexes 
ADD CONSTRAINT fk_postgres_indexes_table_id 
FOREIGN KEY (table_id) REFERENCES mcl.postgres_tables(id) ON DELETE CASCADE;

-- 6. Создаем индексы для производительности
CREATE INDEX idx_mssql_indexes_table_id ON mcl.mssql_indexes(table_id);
CREATE INDEX idx_postgres_indexes_table_id ON mcl.postgres_indexes(table_id);

-- 7. Проверяем корректность заполнения
SELECT 
    'mssql_indexes' as table_name,
    COUNT(*) as total_records,
    COUNT(table_id) as with_table_id,
    COUNT(*) - COUNT(table_id) as without_table_id
FROM mcl.mssql_indexes
UNION ALL
SELECT 
    'postgres_indexes' as table_name,
    COUNT(*) as total_records,
    COUNT(table_id) as with_table_id,
    COUNT(*) - COUNT(table_id) as without_table_id
FROM mcl.postgres_indexes;

-- 8. Проверяем соответствие связей для таблицы accnt
SELECT 
    'Проверка связей для accnt' as check_name,
    mi.id as mssql_index_id,
    mi.index_name as mssql_index_name,
    mi.table_id as mssql_table_id,
    pi.id as postgres_index_id,
    pi.index_name as postgres_index_name,
    pi.table_id as postgres_table_id,
    pi.source_index_id,
    CASE 
        WHEN mi.id = pi.source_index_id THEN '✅ Соответствует'
        ELSE '❌ Не соответствует'
    END as source_match,
    CASE 
        WHEN mi.table_id = pi.table_id THEN '✅ Таблица совпадает'
        ELSE '❌ Таблица не совпадает'
    END as table_match
FROM mcl.mssql_indexes mi
JOIN mcl.postgres_indexes pi ON mi.id = pi.source_index_id
JOIN mcl.mssql_tables mt ON mi.table_id = mt.id
WHERE mt.object_name = 'accnt';

COMMIT;

-- Комментарии
COMMENT ON COLUMN mcl.mssql_indexes.table_id IS 'Прямая связь с таблицей в mssql_tables';
COMMENT ON COLUMN mcl.postgres_indexes.table_id IS 'Прямая связь с таблицей в postgres_tables';