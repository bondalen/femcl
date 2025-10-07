-- ============================================================================
-- FEMCL: Создание дочерних таблиц для конвертации функций
-- ============================================================================
-- Дата создания: 2025-10-07
-- Назначение: 4 дочерние таблицы через INHERITS от function_conversions
--             Каждая содержит ТОЛЬКО FK связь с объектом
-- ============================================================================

-- ============================================================================
-- 1. column_function_conversions - для вычисляемых колонок
-- ============================================================================

CREATE TABLE IF NOT EXISTS mcl.column_function_conversions (
    -- СВЯЗЬ С ОБЪЕКТОМ (единственное обязательное поле)
    column_id               INTEGER NOT NULL UNIQUE
                            REFERENCES mcl.postgres_columns(id) ON DELETE CASCADE,
    
    -- Специфичные поля для колонок (опционально, резерв на будущее)
    -- is_persisted_source     BOOLEAN,  -- Если понадобится
    
    CONSTRAINT pk_column_conversion PRIMARY KEY (id)
    
) INHERITS (mcl.function_conversions);

-- Индексы
CREATE UNIQUE INDEX IF NOT EXISTS idx_cfc_column 
    ON mcl.column_function_conversions(column_id);

CREATE INDEX IF NOT EXISTS idx_cfc_status 
    ON mcl.column_function_conversions(mapping_status);

-- Комментарии
COMMENT ON TABLE mcl.column_function_conversions IS 
'Конвертация функций в вычисляемых колонках. Минимальная структура - только column_id (FK). Все поля обработки (source_definition, target_definition, mapping_*, manual_*) наследуются от function_conversions.';

COMMENT ON COLUMN mcl.column_function_conversions.column_id IS 
'FK к postgres_columns.id. Каскадное удаление при удалении колонки.';


-- ============================================================================
-- 2. default_constraint_function_conversions - для DEFAULT ограничений
-- ============================================================================

CREATE TABLE IF NOT EXISTS mcl.default_constraint_function_conversions (
    -- СВЯЗЬ С ОБЪЕКТОМ
    constraint_id           INTEGER NOT NULL UNIQUE
                            REFERENCES mcl.postgres_default_constraints(id) ON DELETE CASCADE,
    
    -- Специфичные поля (резерв на будущее)
    
    CONSTRAINT pk_default_conversion PRIMARY KEY (id)
    
) INHERITS (mcl.function_conversions);

-- Индексы
CREATE UNIQUE INDEX IF NOT EXISTS idx_dcfc_constraint 
    ON mcl.default_constraint_function_conversions(constraint_id);

CREATE INDEX IF NOT EXISTS idx_dcfc_status 
    ON mcl.default_constraint_function_conversions(mapping_status);

-- Комментарии
COMMENT ON TABLE mcl.default_constraint_function_conversions IS 
'Конвертация функций в DEFAULT ограничениях. Минимальная структура - только constraint_id (FK).';

COMMENT ON COLUMN mcl.default_constraint_function_conversions.constraint_id IS 
'FK к postgres_default_constraints.id. Каскадное удаление.';


-- ============================================================================
-- 3. check_constraint_function_conversions - для CHECK ограничений
-- ============================================================================

CREATE TABLE IF NOT EXISTS mcl.check_constraint_function_conversions (
    -- СВЯЗЬ С ОБЪЕКТОМ
    constraint_id           INTEGER NOT NULL UNIQUE
                            REFERENCES mcl.postgres_check_constraints(id) ON DELETE CASCADE,
    
    -- Специфичные поля (резерв на будущее)
    
    CONSTRAINT pk_check_conversion PRIMARY KEY (id)
    
) INHERITS (mcl.function_conversions);

-- Индексы
CREATE UNIQUE INDEX IF NOT EXISTS idx_ccfc_constraint 
    ON mcl.check_constraint_function_conversions(constraint_id);

CREATE INDEX IF NOT EXISTS idx_ccfc_status 
    ON mcl.check_constraint_function_conversions(mapping_status);

-- Комментарии
COMMENT ON TABLE mcl.check_constraint_function_conversions IS 
'Конвертация функций в CHECK ограничениях. Минимальная структура - только constraint_id (FK).';

COMMENT ON COLUMN mcl.check_constraint_function_conversions.constraint_id IS 
'FK к postgres_check_constraints.id. Каскадное удаление.';


-- ============================================================================
-- 4. index_function_conversions - для функциональных индексов
-- ============================================================================

CREATE TABLE IF NOT EXISTS mcl.index_function_conversions (
    -- СВЯЗЬ С ОБЪЕКТОМ
    index_id                INTEGER NOT NULL UNIQUE
                            REFERENCES mcl.postgres_indexes(id) ON DELETE CASCADE,
    
    -- Специфичные поля для индексов
    is_functional           BOOLEAN,            -- Функциональный индекс?
    filter_expression       TEXT,               -- WHERE clause (filtered index)
    
    CONSTRAINT pk_index_conversion PRIMARY KEY (id)
    
) INHERITS (mcl.function_conversions);

-- Индексы
CREATE UNIQUE INDEX IF NOT EXISTS idx_ifc_index 
    ON mcl.index_function_conversions(index_id);

CREATE INDEX IF NOT EXISTS idx_ifc_status 
    ON mcl.index_function_conversions(mapping_status);

-- Комментарии
COMMENT ON TABLE mcl.index_function_conversions IS 
'Конвертация функций в индексах. Содержит специфичные поля для функциональных и filtered индексов.';

COMMENT ON COLUMN mcl.index_function_conversions.index_id IS 
'FK к postgres_indexes.id. Каскадное удаление.';

COMMENT ON COLUMN mcl.index_function_conversions.is_functional IS 
'Флаг функционального индекса (индекс по выражению, а не по колонке)';

COMMENT ON COLUMN mcl.index_function_conversions.filter_expression IS 
'WHERE clause для filtered/partial индексов (PostgreSQL специфика)';

-- Итоговый вывод
DO $$ 
BEGIN
    RAISE NOTICE '✅ Все 4 дочерние таблицы созданы:';
    RAISE NOTICE '   • column_function_conversions (column_id FK)';
    RAISE NOTICE '   • default_constraint_function_conversions (constraint_id FK)';
    RAISE NOTICE '   • check_constraint_function_conversions (constraint_id FK)';
    RAISE NOTICE '   • index_function_conversions (index_id FK + специфичные поля)';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Наследование: Все 4 таблицы INHERITS FROM function_conversions';
END $$;
