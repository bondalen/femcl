-- Создание представления для упрощения работы с индексами
-- Дата: 2025-10-02
-- Проект: FEMCL

-- Удаляем представление если существует
DROP VIEW IF EXISTS mcl.v_postgres_indexes_by_table;

-- Создаем представление для связи таблиц и индексов
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
    pi.migration_date,
    pi.error_message,
    pi.fill_factor,
    pi.is_concurrent,
    pi.name_conflict_resolved,
    pi.name_conflict_reason,
    pi.alternative_name,
    pi.postgres_definition,
    pi.source_index_id,
    pi.created_at,
    pi.updated_at
FROM mcl.postgres_tables pt
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
JOIN mcl.mssql_columns mc ON mt.id = mc.table_id
JOIN mcl.mssql_index_columns mic ON mc.id = mic.column_id
JOIN mcl.mssql_indexes mi ON mic.index_id = mi.id
JOIN mcl.postgres_indexes pi ON mi.id = pi.source_index_id
GROUP BY 
    pt.id, pt.object_name, 
    pi.id, pi.index_name, pi.original_index_name, pi.index_type,
    pi.is_unique, pi.is_primary_key, pi.migration_status, pi.migration_date,
    pi.error_message, pi.fill_factor, pi.is_concurrent, pi.name_conflict_resolved,
    pi.name_conflict_reason, pi.alternative_name, pi.postgres_definition,
    pi.source_index_id, pi.created_at, pi.updated_at
ORDER BY pt.object_name, pi.index_name;

-- Создаем индекс для производительности
CREATE INDEX IF NOT EXISTS idx_postgres_tables_object_name 
ON mcl.postgres_tables(object_name);

-- Комментарии
COMMENT ON VIEW mcl.v_postgres_indexes_by_table IS 
'Представление для упрощения работы с индексами таблиц. Связывает postgres_indexes с postgres_tables через исходные метаданные MS SQL.';

COMMENT ON COLUMN mcl.v_postgres_indexes_by_table.table_name IS 'Имя таблицы';
COMMENT ON COLUMN mcl.v_postgres_indexes_by_table.table_id IS 'ID таблицы в postgres_tables';
COMMENT ON COLUMN mcl.v_postgres_indexes_by_table.index_id IS 'ID индекса в postgres_indexes';
COMMENT ON COLUMN mcl.v_postgres_indexes_by_table.index_name IS 'Имя индекса в PostgreSQL';
COMMENT ON COLUMN mcl.v_postgres_indexes_by_table.source_index_id IS 'ID исходного индекса в MS SQL';