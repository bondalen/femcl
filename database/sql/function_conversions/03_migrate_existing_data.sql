-- ============================================================================
-- FEMCL: Миграция существующих данных в function_conversions
-- ============================================================================
-- Дата создания: 2025-10-07
-- Назначение: Перенос данных из существующих полей в новую структуру
-- ============================================================================

-- ============================================================================
-- 1. Миграция вычисляемых колонок (postgres_columns)
-- ============================================================================

DO $$ 
DECLARE
    v_count INTEGER;
BEGIN
    RAISE NOTICE '📊 Миграция данных из postgres_columns...';
    
    INSERT INTO mcl.column_function_conversions 
        (column_id, source_definition, target_definition, 
         mapping_rule_id, mapping_status, mapping_complexity, mapping_notes,
         created_at, updated_at)
    SELECT 
        pc.id as column_id,
        pc.computed_definition as source_definition,
        pc.postgres_computed_definition as target_definition,
        pc.computed_function_mapping_rule_id as mapping_rule_id,
        CASE 
            WHEN pc.computed_mapping_status = 'mapped' THEN 'automatic-mapped'
            ELSE COALESCE(pc.computed_mapping_status, 'pending')
        END as mapping_status,
        COALESCE(pc.computed_mapping_complexity, 'simple') as mapping_complexity,
        pc.computed_mapping_notes as mapping_notes,
        COALESCE(pc.created_at, NOW()) as created_at,
        COALESCE(pc.updated_at, NOW()) as updated_at
    FROM mcl.postgres_columns pc
    JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
    JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
    WHERE pc.is_computed = true 
      AND mt.task_id = 2
      AND pc.computed_definition IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 FROM mcl.column_function_conversions cfc 
          WHERE cfc.column_id = pc.id
      );
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RAISE NOTICE '  ✅ Вычисляемых колонок перенесено: %', v_count;
END $$;

-- ============================================================================
-- 2. Миграция DEFAULT ограничений
-- ============================================================================

DO $$ 
DECLARE
    v_count INTEGER;
BEGIN
    RAISE NOTICE '📊 Миграция данных из postgres_default_constraints...';
    
    INSERT INTO mcl.default_constraint_function_conversions 
        (constraint_id, source_definition, target_definition,
         mapping_rule_id, mapping_status, mapping_complexity, mapping_notes,
         created_at, updated_at)
    SELECT 
        pdc.id as constraint_id,
        pdc.definition as source_definition,
        pdc.postgres_definition as target_definition,
        pdc.function_mapping_rule_id as mapping_rule_id,
        CASE 
            WHEN pdc.mapping_status = 'mapped' THEN 'automatic-mapped'
            ELSE COALESCE(pdc.mapping_status, 'pending')
        END as mapping_status,
        COALESCE(pdc.mapping_complexity, 'simple') as mapping_complexity,
        pdc.mapping_notes as mapping_notes,
        COALESCE(pdc.created_at, NOW()) as created_at,
        COALESCE(pdc.updated_at, NOW()) as updated_at
    FROM mcl.postgres_default_constraints pdc
    WHERE pdc.definition IS NOT NULL 
      AND pdc.definition != ''
      AND NOT EXISTS (
          SELECT 1 FROM mcl.default_constraint_function_conversions dcfc 
          WHERE dcfc.constraint_id = pdc.id
      );
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RAISE NOTICE '  ✅ DEFAULT ограничений перенесено: %', v_count;
END $$;

-- ============================================================================
-- 3. Миграция CHECK ограничений
-- ============================================================================

DO $$ 
DECLARE
    v_count INTEGER;
BEGIN
    RAISE NOTICE '📊 Миграция данных из postgres_check_constraints...';
    
    INSERT INTO mcl.check_constraint_function_conversions 
        (constraint_id, source_definition, target_definition,
         mapping_rule_id, mapping_status, mapping_complexity, mapping_notes,
         created_at, updated_at)
    SELECT 
        pcc.id as constraint_id,
        pcc.definition as source_definition,
        pcc.postgres_definition as target_definition,
        pcc.function_mapping_rule_id as mapping_rule_id,
        CASE 
            WHEN pcc.mapping_status = 'mapped' THEN 'automatic-mapped'
            ELSE COALESCE(pcc.mapping_status, 'pending')
        END as mapping_status,
        COALESCE(pcc.mapping_complexity, 'simple') as mapping_complexity,
        pcc.mapping_notes as mapping_notes,
        COALESCE(pcc.created_at, NOW()) as created_at,
        COALESCE(pcc.updated_at, NOW()) as updated_at
    FROM mcl.postgres_check_constraints pcc
    WHERE pcc.definition IS NOT NULL 
      AND pcc.definition != ''
      AND NOT EXISTS (
          SELECT 1 FROM mcl.check_constraint_function_conversions ccfc 
          WHERE ccfc.constraint_id = pcc.id
      );
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RAISE NOTICE '  ✅ CHECK ограничений перенесено: %', v_count;
END $$;

-- ============================================================================
-- Итоговая статистика
-- ============================================================================

DO $$ 
DECLARE
    v_total INTEGER;
    v_columns INTEGER;
    v_defaults INTEGER;
    v_checks INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total FROM mcl.function_conversions;
    SELECT COUNT(*) INTO v_columns FROM mcl.column_function_conversions;
    SELECT COUNT(*) INTO v_defaults FROM mcl.default_constraint_function_conversions;
    SELECT COUNT(*) INTO v_checks FROM mcl.check_constraint_function_conversions;
    
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════';
    RAISE NOTICE '📊 ИТОГОВАЯ СТАТИСТИКА МИГРАЦИИ';
    RAISE NOTICE '═══════════════════════════════════════════════════════';
    RAISE NOTICE 'Всего конвертаций (родительская): %', v_total;
    RAISE NOTICE '';
    RAISE NOTICE 'По типам объектов:';
    RAISE NOTICE '  • Вычисляемые колонки:   %', v_columns;
    RAISE NOTICE '  • DEFAULT ограничения:   %', v_defaults;
    RAISE NOTICE '  • CHECK ограничения:     %', v_checks;
    RAISE NOTICE '';
    RAISE NOTICE '✅ Миграция данных завершена успешно!';
    RAISE NOTICE '═══════════════════════════════════════════════════════';
END $$;
