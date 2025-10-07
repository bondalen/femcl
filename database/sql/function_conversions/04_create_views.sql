-- ============================================================================
-- FEMCL: Создание представлений для function_conversions
-- ============================================================================
-- Дата создания: 2025-10-07
-- Назначение: Удобные представления для работы с конвертациями функций
-- ============================================================================

-- ============================================================================
-- 1. v_function_conversions_typed - конвертации с типом объекта
-- ============================================================================

CREATE OR REPLACE VIEW mcl.v_function_conversions_typed AS
SELECT 
    fc.id,
    fc.source_definition,
    fc.target_definition,
    fc.mapping_rule_id,
    fc.mapping_status,
    fc.mapping_complexity,
    fc.mapping_notes,
    fc.manual_developer,
    fc.manual_started_at,
    fc.manual_completed_at,
    fc.created_at,
    fc.updated_at,
    
    -- Определение типа объекта
    CASE 
        WHEN cfc.column_id IS NOT NULL THEN 'column'
        WHEN dcfc.constraint_id IS NOT NULL THEN 'default_constraint'
        WHEN ccfc.constraint_id IS NOT NULL THEN 'check_constraint'
        WHEN ifc.index_id IS NOT NULL THEN 'index'
    END as object_type,
    
    -- ID объекта
    COALESCE(cfc.column_id, dcfc.constraint_id, ccfc.constraint_id, ifc.index_id) as object_id,
    
    -- Правило маппинга
    fmr.source_function,
    fmr.target_function,
    fmr.mapping_type,
    fmr.complexity_level as rule_complexity

FROM mcl.function_conversions fc

-- JOIN к правилам маппинга
LEFT JOIN mcl.function_mapping_rules fmr ON fc.mapping_rule_id = fmr.id

-- JOIN к дочерним таблицам для определения типа
LEFT JOIN mcl.column_function_conversions cfc ON fc.id = cfc.id
LEFT JOIN mcl.default_constraint_function_conversions dcfc ON fc.id = dcfc.id
LEFT JOIN mcl.check_constraint_function_conversions ccfc ON fc.id = ccfc.id
LEFT JOIN mcl.index_function_conversions ifc ON fc.id = ifc.id;

COMMENT ON VIEW mcl.v_function_conversions_typed IS 
'Представление конвертаций функций с типом объекта. Объединяет данные из function_conversions с информацией о типе через JOIN к дочерним таблицам.';

-- ============================================================================
-- 2. v_function_conversions_full - конвертации с полной информацией
-- ============================================================================

CREATE OR REPLACE VIEW mcl.v_function_conversions_full AS
SELECT 
    fc.id as conversion_id,
    fc.source_definition,
    fc.target_definition,
    fc.mapping_rule_id,
    fc.mapping_status,
    fc.mapping_complexity,
    fc.mapping_notes,
    fc.manual_developer,
    fc.manual_started_at,
    fc.manual_completed_at,
    
    -- Тип объекта
    CASE 
        WHEN cfc.column_id IS NOT NULL THEN 'column'
        WHEN dcfc.constraint_id IS NOT NULL THEN 'default_constraint'
        WHEN ccfc.constraint_id IS NOT NULL THEN 'check_constraint'
        WHEN ifc.index_id IS NOT NULL THEN 'index'
    END as object_type,
    
    COALESCE(cfc.column_id, dcfc.constraint_id, ccfc.constraint_id, ifc.index_id) as object_id,
    
    -- Полное имя объекта
    CASE 
        WHEN cfc.column_id IS NOT NULL THEN pt_c.object_name || '.' || pc.column_name
        WHEN dcfc.constraint_id IS NOT NULL THEN pdc.constraint_name
        WHEN ccfc.constraint_id IS NOT NULL THEN pcc.constraint_name
        WHEN ifc.index_id IS NOT NULL THEN pi.index_name || ' ON ' || pt_i.object_name
    END as object_full_name,
    
    -- task_id (только для колонок и индексов, у которых есть table_id)
    COALESCE(mt_c.task_id, mt_i.task_id) as task_id,
    
    -- Правило маппинга
    fmr.source_function,
    fmr.target_function,
    fmr.mapping_type,
    fmr.complexity_level as rule_complexity

FROM mcl.function_conversions fc
LEFT JOIN mcl.function_mapping_rules fmr ON fc.mapping_rule_id = fmr.id

-- Колонки
LEFT JOIN mcl.column_function_conversions cfc ON fc.id = cfc.id
LEFT JOIN mcl.postgres_columns pc ON cfc.column_id = pc.id
LEFT JOIN mcl.postgres_tables pt_c ON pc.table_id = pt_c.id
LEFT JOIN mcl.mssql_tables mt_c ON pt_c.source_table_id = mt_c.id

-- DEFAULT ограничения (нет table_id, только имя)
LEFT JOIN mcl.default_constraint_function_conversions dcfc ON fc.id = dcfc.id
LEFT JOIN mcl.postgres_default_constraints pdc ON dcfc.constraint_id = pdc.id

-- CHECK ограничения (нет table_id, только имя)
LEFT JOIN mcl.check_constraint_function_conversions ccfc ON fc.id = ccfc.id
LEFT JOIN mcl.postgres_check_constraints pcc ON ccfc.constraint_id = pcc.id

-- Индексы (есть table_id)
LEFT JOIN mcl.index_function_conversions ifc ON fc.id = ifc.id
LEFT JOIN mcl.postgres_indexes pi ON ifc.index_id = pi.id
LEFT JOIN mcl.postgres_tables pt_i ON pi.table_id = pt_i.id
LEFT JOIN mcl.mssql_tables mt_i ON pt_i.source_table_id = mt_i.id;

COMMENT ON VIEW mcl.v_function_conversions_full IS 
'Полное представление конвертаций функций с именами объектов, task_id (для колонок и индексов) и правилами маппинга.';

-- Вывод информации
DO $$ 
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✅ Представления созданы:';
    RAISE NOTICE '   • v_function_conversions_typed - с типом объекта';
    RAISE NOTICE '   • v_function_conversions_full - полная информация + имена';
END $$;
