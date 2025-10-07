-- ============================================================================
-- FEMCL: Создание родительской таблицы function_conversions
-- ============================================================================
-- Дата создания: 2025-10-07
-- Назначение: Центральная таблица для отслеживания конвертации функций
--             MS SQL → PostgreSQL
-- Принцип: metadataFirst - все функции преобразуются на стадии 02.01
-- ============================================================================

-- Проверка существования
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'mcl' AND table_name = 'function_conversions'
    ) THEN
        RAISE NOTICE 'Таблица mcl.function_conversions уже существует. Пропускаем создание.';
    ELSE
        RAISE NOTICE 'Создаем таблицу mcl.function_conversions...';
    END IF;
END $$;

-- Создание родительской таблицы
CREATE TABLE IF NOT EXISTS mcl.function_conversions (
    -- Идентификация
    id                      SERIAL PRIMARY KEY,
    
    -- ОПРЕДЕЛЕНИЯ ФУНКЦИЙ (в родительской для стандартной обработки!)
    source_definition       TEXT NOT NULL,      -- Исходная функция (MS SQL)
    target_definition       TEXT,               -- Преобразованная (PostgreSQL)
    
    -- МАППИНГ
    mapping_rule_id         INTEGER REFERENCES mcl.function_mapping_rules(id),
    mapping_status          VARCHAR(30) NOT NULL DEFAULT 'pending',
    mapping_complexity      VARCHAR(20) DEFAULT 'simple',
    mapping_notes           TEXT,
    
    -- РУЧНАЯ РАЗРАБОТКА
    manual_developer        VARCHAR(100),
    manual_started_at       TIMESTAMP,
    manual_completed_at     TIMESTAMP,
    
    -- АУДИТ
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- ОГРАНИЧЕНИЯ
    CONSTRAINT chk_fc_mapping_status CHECK (mapping_status IN (
        'pending',
        'automatic-mapped',
        'manual-required',
        'manual-in-progress',
        'manual-completed',
        'automatic-error',
        'validation-failed',
        'skipped'
    )),
    
    CONSTRAINT chk_fc_complexity CHECK (mapping_complexity IN (
        'simple', 'medium', 'complex', 'custom'
    ))
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_fc_status 
    ON mcl.function_conversions(mapping_status);

CREATE INDEX IF NOT EXISTS idx_fc_rule 
    ON mcl.function_conversions(mapping_rule_id);

CREATE INDEX IF NOT EXISTS idx_fc_manual 
    ON mcl.function_conversions(manual_developer) 
    WHERE manual_developer IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_fc_pending 
    ON mcl.function_conversions(mapping_status) 
    WHERE mapping_status IN ('pending', 'manual-required', 'manual-in-progress');

CREATE INDEX IF NOT EXISTS idx_fc_ready 
    ON mcl.function_conversions(mapping_status) 
    WHERE mapping_status IN ('automatic-mapped', 'manual-completed');

-- Комментарии к таблице
COMMENT ON TABLE mcl.function_conversions IS 
'Родительская таблица конвертации функций MS SQL → PostgreSQL. Содержит ВСЕ общие поля для обработки конвертаций (source_definition, target_definition, статусы, ручная разработка). Дочерние таблицы содержат только FK связи с объектами. Принцип: metadataFirst - все функции определяются на стадии 02.01, а НЕ на лету.';

-- Комментарии к полям
COMMENT ON COLUMN mcl.function_conversions.id IS 
'Уникальный идентификатор конвертации';

COMMENT ON COLUMN mcl.function_conversions.source_definition IS 
'Исходное определение функции (MS SQL синтаксис). В родительской таблице для стандартной обработки всех типов объектов. Берется из computed_definition, definition и т.д.';

COMMENT ON COLUMN mcl.function_conversions.target_definition IS 
'Преобразованное определение (PostgreSQL синтаксис). Заполняется автоматически (через правила из function_mapping_rules) или вручную (AI в чате как код).';

COMMENT ON COLUMN mcl.function_conversions.mapping_rule_id IS 
'Ссылка на правило маппинга из function_mapping_rules (для автоматических конвертаций)';

COMMENT ON COLUMN mcl.function_conversions.mapping_status IS 
'Статус конвертации: pending → automatic-mapped OR (manual-required → manual-in-progress → manual-completed)';

COMMENT ON COLUMN mcl.function_conversions.mapping_complexity IS 
'Уровень сложности: simple (базовые функции), medium (составные), complex (вложенные), custom (кастомные [ags])';

COMMENT ON COLUMN mcl.function_conversions.mapping_notes IS 
'Заметки о преобразовании: какое решение выбрано, почему, особенности реализации';

COMMENT ON COLUMN mcl.function_conversions.manual_developer IS 
'Кто разрабатывает функцию вручную (AI-Assistant или имя пользователя)';

COMMENT ON COLUMN mcl.function_conversions.manual_started_at IS 
'Время начала ручной разработки (устанавливается при start_manual)';

COMMENT ON COLUMN mcl.function_conversions.manual_completed_at IS 
'Время завершения ручной разработки (устанавливается при complete_manual)';

-- Вывод информации
DO $$ 
BEGIN
    RAISE NOTICE '✅ Родительская таблица mcl.function_conversions создана';
    RAISE NOTICE '   • 11 полей (source_definition, target_definition, mapping_*, manual_*)';
    RAISE NOTICE '   • 5 индексов для оптимизации';
    RAISE NOTICE '   • 8 статусов конвертации';
END $$;
