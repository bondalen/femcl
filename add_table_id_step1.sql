-- Шаг 1: Добавление колонок table_id
-- Дата: 2025-10-02
-- Проект: FEMCL

-- Добавляем колонку table_id в mssql_indexes
ALTER TABLE mcl.mssql_indexes 
ADD COLUMN table_id INTEGER;

-- Добавляем колонку table_id в postgres_indexes  
ALTER TABLE mcl.postgres_indexes 
ADD COLUMN table_id INTEGER;

-- Проверяем добавление
SELECT 'mssql_indexes' as table_name, column_name 
FROM information_schema.columns 
WHERE table_schema = 'mcl' AND table_name = 'mssql_indexes' AND column_name = 'table_id'
UNION ALL
SELECT 'postgres_indexes' as table_name, column_name 
FROM information_schema.columns 
WHERE table_schema = 'mcl' AND table_name = 'postgres_indexes' AND column_name = 'table_id';