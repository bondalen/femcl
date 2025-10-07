-- ============================================================================
-- FEMCL: Удаление устаревших полей маппинга из таблиц объектов
-- ============================================================================
-- Дата создания: 2025-10-07
-- Назначение: Очистка дублирующих полей после создания postgres_function_conversions
-- Принцип: Метаданные процесса → conversions, результат → postgres_definition
-- ============================================================================

-- ============================================================================
-- Шаг 0: Удалить зависимые представления
-- ============================================================================

DO $$ 
BEGIN
    RAISE NOTICE '📊 Удаление зависимых представлений...';
    
    DROP VIEW IF EXISTS mcl.v_default_constraints_by_table CASCADE;
    DROP VIEW IF EXISTS mcl.v_postgres_default_constraints_by_table CASCADE;
    
    RAISE NOTICE '  ✅ Представления удалены';
    RAISE NOTICE '  ℹ️  Будут пересозданы без устаревших полей после очистки';
END $$;

-- ============================================================================
-- Шаг 1: Синхронизация target_definition перед удалением
-- ============================================================================

DO $$ 
DECLARE
    v_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '🔄 Синхронизация target_definition...';
    
    -- Синхронизация колонок
    UPDATE mcl.postgres_columns pc
    SET postgres_computed_definition = cfc.target_definition
    FROM mcl.postgres_column_function_conversions cfc
    WHERE pc.id = cfc.column_id 
      AND pc.is_computed = true
      AND cfc.target_definition IS NOT NULL
      AND (pc.postgres_computed_definition IS NULL 
           OR pc.postgres_computed_definition != cfc.target_definition);
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    IF v_count > 0 THEN
        RAISE NOTICE '  ✅ Синхронизировано колонок: %', v_count;
    ELSE
        RAISE NOTICE '  ✅ Колонки уже синхронизированы';
    END IF;
    
    -- Синхронизация DEFAULT constraints
    UPDATE mcl.postgres_default_constraints pdc
    SET postgres_definition = dcfc.target_definition
    FROM mcl.postgres_default_constraint_function_conversions dcfc
    WHERE pdc.id = dcfc.constraint_id
      AND dcfc.target_definition IS NOT NULL
      AND (pdc.postgres_definition IS NULL 
           OR pdc.postgres_definition != dcfc.target_definition);
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    IF v_count > 0 THEN
        RAISE NOTICE '  ✅ Синхронизировано DEFAULT: %', v_count;
    ELSE
        RAISE NOTICE '  ✅ DEFAULT уже синхронизированы';
    END IF;
    
    -- Синхронизация CHECK constraints
    UPDATE mcl.postgres_check_constraints pcc
    SET postgres_definition = ccfc.target_definition
    FROM mcl.postgres_check_constraint_function_conversions ccfc
    WHERE pcc.id = ccfc.constraint_id
      AND ccfc.target_definition IS NOT NULL
      AND (pcc.postgres_definition IS NULL 
           OR pcc.postgres_definition != ccfc.target_definition);
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    IF v_count > 0 THEN
        RAISE NOTICE '  ✅ Синхронизировано CHECK: %', v_count;
    ELSE
        RAISE NOTICE '  ✅ CHECK уже синхронизированы';
    END IF;
END $$;

-- ============================================================================
-- Шаг 2: Удаление устаревших полей из postgres_columns
-- ============================================================================

DO $$ 
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '📊 Удаление устаревших полей из postgres_columns...';
    
    ALTER TABLE mcl.postgres_columns
        DROP COLUMN IF EXISTS computed_function_mapping_rule_id CASCADE,
        DROP COLUMN IF EXISTS computed_mapping_status CASCADE,
        DROP COLUMN IF EXISTS computed_mapping_complexity CASCADE,
        DROP COLUMN IF EXISTS computed_mapping_notes CASCADE;
    
    RAISE NOTICE '  ✅ Удалено 4 поля';
    RAISE NOTICE '  ✅ Оставлено: postgres_computed_definition (результат)';
END $$;

-- ============================================================================
-- Шаг 3: Удаление устаревших полей из postgres_default_constraints
-- ============================================================================

DO $$ 
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '📊 Удаление устаревших полей из postgres_default_constraints...';
    
    ALTER TABLE mcl.postgres_default_constraints
        DROP COLUMN IF EXISTS function_mapping_rule_id CASCADE,
        DROP COLUMN IF EXISTS mapping_status CASCADE,
        DROP COLUMN IF EXISTS mapping_complexity CASCADE,
        DROP COLUMN IF EXISTS mapping_notes CASCADE;
    
    RAISE NOTICE '  ✅ Удалено 4 поля';
    RAISE NOTICE '  ✅ Оставлено: postgres_definition (результат)';
END $$;

-- ============================================================================
-- Шаг 4: Удаление устаревших полей из postgres_check_constraints
-- ============================================================================

DO $$ 
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '📊 Удаление устаревших полей из postgres_check_constraints...';
    
    ALTER TABLE mcl.postgres_check_constraints
        DROP COLUMN IF EXISTS function_mapping_rule_id CASCADE,
        DROP COLUMN IF EXISTS mapping_status CASCADE,
        DROP COLUMN IF EXISTS mapping_complexity CASCADE,
        DROP COLUMN IF EXISTS mapping_notes CASCADE;
    
    RAISE NOTICE '  ✅ Удалено 4 поля';
    RAISE NOTICE '  ✅ Оставлено: postgres_definition (результат)';
END $$;

-- ============================================================================
-- Шаг 5: Удаление устаревших полей из postgres_indexes
-- ============================================================================

DO $$ 
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '📊 Удаление устаревших полей из postgres_indexes...';
    
    ALTER TABLE mcl.postgres_indexes
        DROP COLUMN IF EXISTS function_mapping_rule_id CASCADE,
        DROP COLUMN IF EXISTS mapping_status CASCADE,
        DROP COLUMN IF EXISTS mapping_complexity CASCADE,
        DROP COLUMN IF EXISTS mapping_notes CASCADE;
    
    RAISE NOTICE '  ✅ Удалено 4 поля';
    RAISE NOTICE '  ✅ Оставлено: postgres_definition (результат)';
END $$;

-- ============================================================================
-- Итоговый отчет
-- ============================================================================

DO $$ 
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════';
    RAISE NOTICE '✅ ОЧИСТКА ЗАВЕРШЕНА УСПЕШНО';
    RAISE NOTICE '═══════════════════════════════════════════════════════';
    RAISE NOTICE '';
    RAISE NOTICE 'Удалено полей: 16 (4 поля × 4 таблицы)';
    RAISE NOTICE 'Удалено представлений: 2 (зависимые от устаревших полей)';
    RAISE NOTICE 'Оставлено полей: 4 (postgres_definition в каждой таблице)';
    RAISE NOTICE '';
    RAISE NOTICE 'Разделение ответственности:';
    RAISE NOTICE '  • Объекты → Исходник + Результат';
    RAISE NOTICE '  • Conversions → Процесс + Метаданные + История';
    RAISE NOTICE '';
    RAISE NOTICE '✅ Нет дублирования данных';
    RAISE NOTICE '✅ Единственный источник истины';
    RAISE NOTICE '═══════════════════════════════════════════════════════';
END $$;
