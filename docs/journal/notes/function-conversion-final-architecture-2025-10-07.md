# Финальная архитектура конвертации функций (Вариант B уточненный)

**Дата:** 2025-10-07  
**Чат:** Функции в колонках  
**Версия:** FINAL (с уточнением по source/target_definition)  
**Статус:** Предложение без изменений

---

## ✅ УТОЧНЕНИЕ АРХИТЕКТУРЫ

### Распределение полей:

#### РОДИТЕЛЬСКАЯ таблица (function_conversions):
```
✅ ВСЕ общие поля для обработки:
  - source_definition          ← В РОДИТЕЛЬСКОЙ!
  - target_definition          ← В РОДИТЕЛЬСКОЙ!
  - mapping_rule_id
  - mapping_status
  - mapping_complexity
  - mapping_notes
  - manual_developer
  - manual_started_at
  - manual_completed_at
  - created_at, updated_at
```

#### ДОЧЕРНИЕ таблицы (минимальны):
```
✅ ТОЛЬКО связь + специфичные поля (если есть):
  - [type]_id (FK)              ← Связь с объектом
  - специфичные поля (опционально)
```

**Зачем дочерние:**
1. Типобезопасные FK к конкретным таблицам
2. Место для специфичных полей (если понадобятся)
3. Уникальность связи (один объект = одна конвертация)

---

## 📋 ФИНАЛЬНАЯ SQL СПЕЦИФИКАЦИЯ

### 1. Родительская таблица (ВСЯ логика обработки)

```sql
CREATE TABLE mcl.function_conversions (
    id                      SERIAL PRIMARY KEY,
    
    -- ОПРЕДЕЛЕНИЯ ФУНКЦИЙ (в родительской!)
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
    CONSTRAINT chk_mapping_status CHECK (mapping_status IN (
        'pending', 'automatic-mapped', 'manual-required',
        'manual-in-progress', 'manual-completed',
        'automatic-error', 'validation-failed', 'skipped'
    ))
);

-- Индексы на родительской
CREATE INDEX idx_fc_status ON mcl.function_conversions(mapping_status);
CREATE INDEX idx_fc_rule ON mcl.function_conversions(mapping_rule_id);
CREATE INDEX idx_fc_manual ON mcl.function_conversions(manual_developer) 
    WHERE manual_developer IS NOT NULL;
CREATE INDEX idx_fc_pending ON mcl.function_conversions(mapping_status) 
    WHERE mapping_status IN ('pending', 'manual-required', 'manual-in-progress');

COMMENT ON TABLE mcl.function_conversions IS 
'Родительская таблица конвертации функций. Содержит ВСЕ общие поля для обработки. Дочерние таблицы содержат только FK связи.';

COMMENT ON COLUMN mcl.function_conversions.source_definition IS 
'Исходное определение функции (MS SQL синтаксис). Берется из computed_definition, definition и т.д.';

COMMENT ON COLUMN mcl.function_conversions.target_definition IS 
'Преобразованное определение (PostgreSQL синтаксис). Заполняется автоматически или вручную.';
```

### 2. Дочерняя для колонок (МИНИМАЛЬНА - только связь)

```sql
CREATE TABLE mcl.column_function_conversions (
    -- СВЯЗЬ С ОБЪЕКТОМ
    column_id               INTEGER NOT NULL UNIQUE
                            REFERENCES mcl.postgres_columns(id) ON DELETE CASCADE,
    
    -- Специфичные поля (опционально, если понадобятся)
    is_persisted_source     BOOLEAN,            -- Из MS SQL (для информации)
    
    CONSTRAINT pk_column_conversion PRIMARY KEY (id)
    
) INHERITS (mcl.function_conversions);

-- Индекс для JOIN
CREATE UNIQUE INDEX idx_cfc_column ON mcl.column_function_conversions(column_id);

-- Индекс для поиска по статусу (оптимизация)
CREATE INDEX idx_cfc_status ON mcl.column_function_conversions(mapping_status);

COMMENT ON TABLE mcl.column_function_conversions IS 
'Конвертация функций в вычисляемых колонках. Содержит только FK связь с postgres_columns. Все поля обработки наследуются от function_conversions.';
```

### 3. Дочерняя для DEFAULT ограничений (МИНИМАЛЬНА)

```sql
CREATE TABLE mcl.default_constraint_function_conversions (
    -- СВЯЗЬ С ОБЪЕКТОМ
    constraint_id           INTEGER NOT NULL UNIQUE
                            REFERENCES mcl.postgres_default_constraints(id) ON DELETE CASCADE,
    
    -- Специфичные поля (пока нет, резерв)
    
    CONSTRAINT pk_default_conversion PRIMARY KEY (id)
    
) INHERITS (mcl.function_conversions);

CREATE UNIQUE INDEX idx_dcfc_constraint ON mcl.default_constraint_function_conversions(constraint_id);
CREATE INDEX idx_dcfc_status ON mcl.default_constraint_function_conversions(mapping_status);

COMMENT ON TABLE mcl.default_constraint_function_conversions IS 
'Конвертация функций в DEFAULT ограничениях. Минимальная структура - только FK связь.';
```

### 4. Дочерняя для CHECK ограничений (МИНИМАЛЬНА)

```sql
CREATE TABLE mcl.check_constraint_function_conversions (
    -- СВЯЗЬ С ОБЪЕКТОМ
    constraint_id           INTEGER NOT NULL UNIQUE
                            REFERENCES mcl.postgres_check_constraints(id) ON DELETE CASCADE,
    
    -- Специфичные поля (пока нет, резерв)
    
    CONSTRAINT pk_check_conversion PRIMARY KEY (id)
    
) INHERITS (mcl.function_conversions);

CREATE UNIQUE INDEX idx_ccfc_constraint ON mcl.check_constraint_function_conversions(constraint_id);
CREATE INDEX idx_ccfc_status ON mcl.check_constraint_function_conversions(mapping_status);

COMMENT ON TABLE mcl.check_constraint_function_conversions IS 
'Конвертация функций в CHECK ограничениях. Минимальная структура - только FK связь.';
```

### 5. Дочерняя для индексов (с возможными специфичными полями)

```sql
CREATE TABLE mcl.index_function_conversions (
    -- СВЯЗЬ С ОБЪЕКТОМ
    index_id                INTEGER NOT NULL UNIQUE
                            REFERENCES mcl.postgres_indexes(id) ON DELETE CASCADE,
    
    -- Специфичные поля для индексов (могут понадобиться)
    is_functional           BOOLEAN,            -- Функциональный индекс?
    filter_expression       TEXT,               -- WHERE clause (filtered index)
    
    CONSTRAINT pk_index_conversion PRIMARY KEY (id)
    
) INHERITS (mcl.function_conversions);

CREATE UNIQUE INDEX idx_ifc_index ON mcl.index_function_conversions(index_id);
CREATE INDEX idx_ifc_status ON mcl.index_function_conversions(mapping_status);

COMMENT ON TABLE mcl.index_function_conversions IS 
'Конвертация функций в индексах. Содержит специфичные поля для функциональных и filtered индексов.';
```

---

## ✅ ПРЕИМУЩЕСТВА УТОЧНЕННОЙ АРХИТЕКТУРЫ

### 1. Стандартная обработка ПРОСТА:

```sql
-- ВСЕ конвертации требующие ручной работы (из всех 4 типов)
SELECT id, source_definition, target_definition, mapping_status
FROM mcl.function_conversions
WHERE mapping_status = 'manual-required';

-- Обновление статуса - РАБОТАЕТ для всех типов
UPDATE mcl.function_conversions
SET mapping_status = 'manual-in-progress',
    manual_developer = 'AI-Assistant',
    manual_started_at = NOW()
WHERE id = 123;

-- Обновление результата - РАБОТАЕТ для всех типов
UPDATE mcl.function_conversions
SET target_definition = 'ags.fn_cn_num(cn_key)',
    mapping_status = 'manual-completed',
    manual_completed_at = NOW()
WHERE id = 123;
```

### 2. Типобезопасные FK в дочерних:

```sql
-- Каждая дочерняя таблица имеет реальный FK
column_function_conversions.column_id 
    → FK postgres_columns(id) ON DELETE CASCADE

-- Каскадное удаление работает!
DELETE FROM postgres_columns WHERE id = 9;
-- → Автоматически удалится запись из column_function_conversions
```

### 3. Дочерние минимальны (только связь):

```sql
-- Дочерняя таблица - ТОЛЬКО связь
CREATE TABLE column_function_conversions (
    column_id INTEGER FK,       ← ТОЛЬКО ЭТО
    -- + наследуемые поля
) INHERITS (function_conversions);

-- Если понадобится специфичное поле - добавим:
ALTER TABLE column_function_conversions
    ADD COLUMN is_persisted_source BOOLEAN;
```

---

## 🔧 СТАНДАРТИЗИРОВАННЫЙ API (упрощенный)

```python
class FunctionConverter:
    
    def create_conversion(
        self,
        object_type: str,      # 'column'|'default_constraint'|'check_constraint'|'index'
        object_id: int,
        source_definition: str
    ) -> int:
        """Создать конвертацию - СТАНДАРТНО"""
        
        table = {
            'column': 'column_function_conversions',
            'default_constraint': 'default_constraint_function_conversions',
            'check_constraint': 'check_constraint_function_conversions',
            'index': 'index_function_conversions'
        }[object_type]
        
        fk_field = {
            'column': 'column_id',
            'default_constraint': 'constraint_id',
            'check_constraint': 'constraint_id',
            'index': 'index_id'
        }[object_type]
        
        cursor.execute(f'''
            INSERT INTO mcl.{table} 
                ({fk_field}, source_definition, mapping_status)
            VALUES (%s, %s, 'pending')
            RETURNING id
        ''', [object_id, source_definition])
        
        return cursor.fetchone()[0]
    
    def process_all_pending(self) -> ProcessingReport:
        """
        Обработать ВСЕ pending конвертации
        
        РАБОТАЕТ С РОДИТЕЛЬСКОЙ ТАБЛИЦЕЙ - видит все типы!
        """
        cursor.execute('''
            SELECT id, source_definition
            FROM mcl.function_conversions
            WHERE mapping_status = 'pending'
        ''')
        
        for conv_id, source_def in cursor.fetchall():
            # Применить правила
            result = self._apply_rules(source_def)
            
            if result.success:
                # Обновление РОДИТЕЛЬСКОЙ - работает для всех
                cursor.execute('''
                    UPDATE mcl.function_conversions
                    SET target_definition = %s,
                        mapping_rule_id = %s,
                        mapping_status = 'automatic-mapped'
                    WHERE id = %s
                ''', [result.target, result.rule_id, conv_id])
            else:
                cursor.execute('''
                    UPDATE mcl.function_conversions
                    SET mapping_status = 'manual-required'
                    WHERE id = %s
                ''', [conv_id])
    
    def get_manual_list(self) -> List[dict]:
        """
        Список для ручной работы - ПРОСТОЙ ЗАПРОС
        """
        cursor.execute('''
            SELECT id, source_definition, target_definition, mapping_status
            FROM mcl.function_conversions
            WHERE mapping_status IN ('manual-required', 'manual-in-progress')
        ''')
        return cursor.fetchall()
    
    def start_manual(self, conversion_id: int, developer: str):
        """СТАНДАРТНОЕ обновление родительской"""
        cursor.execute('''
            UPDATE mcl.function_conversions
            SET mapping_status = 'manual-in-progress',
                manual_developer = %s,
                manual_started_at = NOW()
            WHERE id = %s
        ''', [developer, conversion_id])
    
    def complete_manual(self, conversion_id: int, target_def: str):
        """СТАНДАРТНОЕ обновление родительской"""
        cursor.execute('''
            UPDATE mcl.function_conversions
            SET target_definition = %s,
                mapping_status = 'manual-completed',
                manual_completed_at = NOW()
            WHERE id = %s
        ''', [target_def, conversion_id])
```

---

## 📋 УТОЧНЕННАЯ SQL СПЕЦИФИКАЦИЯ

### 1. Родительская таблица (ВСЕ поля обработки)

```sql
CREATE TABLE mcl.function_conversions (
    id                      SERIAL PRIMARY KEY,
    
    -- ОПРЕДЕЛЕНИЯ ФУНКЦИЙ (в родительской для стандартной обработки!)
    source_definition       TEXT NOT NULL,      -- Функция MS SQL
    target_definition       TEXT,               -- Функция PostgreSQL (NULL пока не преобразовано)
    
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
    CONSTRAINT chk_mapping_status CHECK (mapping_status IN (
        'pending',
        'automatic-mapped',
        'manual-required',
        'manual-in-progress',
        'manual-completed',
        'automatic-error',
        'validation-failed',
        'skipped'
    ))
);

-- Индексы
CREATE INDEX idx_fc_status ON mcl.function_conversions(mapping_status);
CREATE INDEX idx_fc_rule ON mcl.function_conversions(mapping_rule_id);
CREATE INDEX idx_fc_manual ON mcl.function_conversions(manual_developer) 
    WHERE manual_developer IS NOT NULL;
CREATE INDEX idx_fc_pending ON mcl.function_conversions(mapping_status) 
    WHERE mapping_status IN ('pending', 'manual-required', 'manual-in-progress');

-- Комментарии
COMMENT ON TABLE mcl.function_conversions IS 
'Родительская таблица конвертации функций. Содержит ВСЕ поля для обработки конвертаций (source_definition, target_definition, статусы и т.д.). Дочерние таблицы содержат только FK связи с объектами.';

COMMENT ON COLUMN mcl.function_conversions.source_definition IS 
'Исходное определение функции (MS SQL). В родительской таблице для стандартной обработки всех типов объектов.';

COMMENT ON COLUMN mcl.function_conversions.target_definition IS 
'Преобразованное определение (PostgreSQL). Заполняется автоматически (через правила) или вручную (AI в чате).';
```

### 2. Дочерняя для колонок (ТОЛЬКО связь)

```sql
CREATE TABLE mcl.column_function_conversions (
    -- СВЯЗЬ С ОБЪЕКТОМ (единственное обязательное поле)
    column_id               INTEGER NOT NULL UNIQUE
                            REFERENCES mcl.postgres_columns(id) ON DELETE CASCADE,
    
    -- Специфичные поля для колонок (опционально, резерв на будущее)
    -- is_persisted_source     BOOLEAN,  -- Если понадобится
    
    CONSTRAINT pk_column_conversion PRIMARY KEY (id)
    
) INHERITS (mcl.function_conversions);

-- Индекс для JOIN
CREATE UNIQUE INDEX idx_cfc_column ON mcl.column_function_conversions(column_id);

COMMENT ON TABLE mcl.column_function_conversions IS 
'Связь конвертаций с вычисляемыми колонками. Минимальная структура - только column_id (FK). Все поля обработки наследуются от function_conversions.';
```

### 3. Дочерняя для DEFAULT ограничений (ТОЛЬКО связь)

```sql
CREATE TABLE mcl.default_constraint_function_conversions (
    -- СВЯЗЬ С ОБЪЕКТОМ
    constraint_id           INTEGER NOT NULL UNIQUE
                            REFERENCES mcl.postgres_default_constraints(id) ON DELETE CASCADE,
    
    -- Специфичные поля (резерв)
    
    CONSTRAINT pk_default_conversion PRIMARY KEY (id)
    
) INHERITS (mcl.function_conversions);

CREATE UNIQUE INDEX idx_dcfc_constraint ON mcl.default_constraint_function_conversions(constraint_id);

COMMENT ON TABLE mcl.default_constraint_function_conversions IS 
'Связь конвертаций с DEFAULT ограничениями. Только constraint_id (FK).';
```

### 4. Дочерняя для CHECK ограничений (ТОЛЬКО связь)

```sql
CREATE TABLE mcl.check_constraint_function_conversions (
    -- СВЯЗЬ С ОБЪЕКТОМ
    constraint_id           INTEGER NOT NULL UNIQUE
                            REFERENCES mcl.postgres_check_constraints(id) ON DELETE CASCADE,
    
    -- Специфичные поля (резерв)
    
    CONSTRAINT pk_check_conversion PRIMARY KEY (id)
    
) INHERITS (mcl.function_conversions);

CREATE UNIQUE INDEX idx_ccfc_constraint ON mcl.check_constraint_function_conversions(constraint_id);

COMMENT ON TABLE mcl.check_constraint_function_conversions IS 
'Связь конвертаций с CHECK ограничениями. Только constraint_id (FK).';
```

### 5. Дочерняя для индексов (ТОЛЬКО связь + специфичные)

```sql
CREATE TABLE mcl.index_function_conversions (
    -- СВЯЗЬ С ОБЪЕКТОМ
    index_id                INTEGER NOT NULL UNIQUE
                            REFERENCES mcl.postgres_indexes(id) ON DELETE CASCADE,
    
    -- Специфичные поля для индексов (могут понадобиться)
    is_functional           BOOLEAN,            -- Функциональный индекс
    filter_expression       TEXT,               -- WHERE clause (filtered index)
    
    CONSTRAINT pk_index_conversion PRIMARY KEY (id)
    
) INHERITS (mcl.function_conversions);

CREATE UNIQUE INDEX idx_ifc_index ON mcl.index_function_conversions(index_id);

COMMENT ON TABLE mcl.index_function_conversions IS 
'Связь конвертаций с индексами. Содержит специфичные поля для функциональных и filtered индексов.';
```

---

## 🔄 ПРИМЕРЫ РАБОТЫ

### Стандартная обработка (работа с родительской):

```sql
-- Получить ВСЕ pending конвертации (все типы объектов)
SELECT id, source_definition, mapping_status
FROM mcl.function_conversions
WHERE mapping_status = 'pending';

-- Применить автоматическое преобразование
UPDATE mcl.function_conversions
SET target_definition = 'COALESCE(column_name, 0)',
    mapping_rule_id = 2,
    mapping_status = 'automatic-mapped',
    mapping_complexity = 'simple'
WHERE id = 123;

-- Получить все ручные разработки в процессе
SELECT 
    id,
    source_definition,
    target_definition,
    manual_developer,
    manual_started_at
FROM mcl.function_conversions
WHERE mapping_status = 'manual-in-progress';
```

### Работа с конкретным типом (JOIN с дочерней):

```sql
-- Получить вычисляемые колонки с их конвертациями (task_id=2)
SELECT 
    pt.object_name || '.' || pc.column_name as full_name,
    cfc.source_definition,
    cfc.target_definition,
    cfc.mapping_status,
    cfc.manual_developer
FROM mcl.column_function_conversions cfc
JOIN mcl.postgres_columns pc ON cfc.column_id = pc.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
WHERE mt.task_id = 2
  AND cfc.mapping_status = 'manual-required';
```

### Получение object_type (если нужно):

```sql
-- Представление с типом объекта
CREATE OR REPLACE VIEW mcl.v_function_conversions_typed AS
SELECT 
    fc.*,
    CASE 
        WHEN cfc.column_id IS NOT NULL THEN 'column'
        WHEN dcfc.constraint_id IS NOT NULL THEN 'default_constraint'
        WHEN ccfc.constraint_id IS NOT NULL THEN 'check_constraint'
        WHEN ifc.index_id IS NOT NULL THEN 'index'
    END as object_type,
    COALESCE(cfc.column_id, dcfc.constraint_id, ccfc.constraint_id, ifc.index_id) as object_id
FROM mcl.function_conversions fc
LEFT JOIN mcl.column_function_conversions cfc ON fc.id = cfc.id
LEFT JOIN mcl.default_constraint_function_conversions dcfc ON fc.id = dcfc.id
LEFT JOIN mcl.check_constraint_function_conversions ccfc ON fc.id = ccfc.id
LEFT JOIN mcl.index_function_conversions ifc ON fc.id = ifc.id;
```

---

## 📊 СТРУКТУРА ПОЛЕЙ (итоговая)

### Родительская (11 полей):
```
function_conversions:
  1. id                       ← PK
  2. source_definition        ← Исходная функция
  3. target_definition        ← Преобразованная функция
  4. mapping_rule_id          ← FK к правилам
  5. mapping_status           ← Статус обработки
  6. mapping_complexity       ← Уровень сложности
  7. mapping_notes            ← Заметки
  8. manual_developer         ← Кто разрабатывает
  9. manual_started_at        ← Начало ручной работы
 10. manual_completed_at      ← Завершение
 11. created_at, updated_at   ← Аудит
```

### Дочерние (минимум 1 поле):
```
column_function_conversions:
  - column_id                 ← FK (единственное обязательное)
  + наследуемые 11 полей
  
default_constraint_function_conversions:
  - constraint_id             ← FK (единственное обязательное)
  + наследуемые 11 полей
  
check_constraint_function_conversions:
  - constraint_id             ← FK (единственное обязательное)
  + наследуемые 11 полей
  
index_function_conversions:
  - index_id                  ← FK (единственное обязательное)
  - is_functional             ← Специфичное (опционально)
  - filter_expression         ← Специфичное (опционально)
  + наследуемые 11 полей
```

**Итого:** 
- Родительская: 11 полей
- Дочерние: 1 FK + опционально специфичные
- **Нет дублирования!**

---

## ✅ ПРЕИМУЩЕСТВА ФИНАЛЬНОЙ АРХИТЕКТУРЫ

1. **Стандартная обработка:**
   - ✅ Работа с `function_conversions` видит ВСЕ записи
   - ✅ `source_definition`, `target_definition` доступны сразу
   - ✅ UPDATE на родительской работает для всех типов

2. **Типобезопасность:**
   - ✅ Реальные FK в дочерних таблицах
   - ✅ Каскадное удаление
   - ✅ Уникальность связи

3. **Минимализм дочерних:**
   - ✅ Только FK связь
   - ✅ Специфичные поля добавляются по необходимости
   - ✅ Нет дублирования логики

4. **Расширяемость:**
   - ✅ Новые общие поля → только в родительской
   - ✅ Специфичные поля → в конкретной дочерней
   - ✅ Новые типы объектов → новая дочерняя таблица

---

## 🔄 МИГРАЦИЯ ДАННЫХ (уточненная)

```sql
-- 1. Создать родительскую таблицу
CREATE TABLE mcl.function_conversions (...);  -- 11 полей

-- 2. Создать дочерние таблицы
CREATE TABLE mcl.column_function_conversions (...) INHERITS (...);
CREATE TABLE mcl.default_constraint_function_conversions (...) INHERITS (...);
CREATE TABLE mcl.check_constraint_function_conversions (...) INHERITS (...);
CREATE TABLE mcl.index_function_conversions (...) INHERITS (...);

-- 3. Мигрировать данные: postgres_columns → column_function_conversions
INSERT INTO mcl.column_function_conversions 
    (column_id, source_definition, target_definition, 
     mapping_rule_id, mapping_status, mapping_complexity, mapping_notes,
     created_at, updated_at)
SELECT 
    pc.id as column_id,                                    -- FK
    pc.computed_definition as source_definition,           -- → родительское поле
    pc.postgres_computed_definition as target_definition,  -- → родительское поле
    pc.computed_function_mapping_rule_id as mapping_rule_id,
    CASE 
        WHEN pc.computed_mapping_status = 'mapped' THEN 'automatic-mapped'
        ELSE COALESCE(pc.computed_mapping_status, 'pending')
    END as mapping_status,
    COALESCE(pc.computed_mapping_complexity, 'simple') as mapping_complexity,
    pc.computed_mapping_notes as mapping_notes,
    COALESCE(pc.created_at, NOW()),
    COALESCE(pc.updated_at, NOW())
FROM mcl.postgres_columns pc
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
WHERE pc.is_computed = true AND mt.task_id = 2;

-- Результат: 67 записей в column_function_conversions
-- Автоматически появляются в родительской function_conversions!

-- 4. Мигрировать: postgres_default_constraints → default_constraint_function_conversions
INSERT INTO mcl.default_constraint_function_conversions 
    (constraint_id, source_definition, target_definition, 
     mapping_rule_id, mapping_status, mapping_complexity, mapping_notes,
     created_at, updated_at)
SELECT 
    pdc.id as constraint_id,
    pdc.definition as source_definition,
    pdc.postgres_definition as target_definition,
    pdc.function_mapping_rule_id,
    CASE 
        WHEN pdc.mapping_status = 'mapped' THEN 'automatic-mapped'
        ELSE COALESCE(pdc.mapping_status, 'pending')
    END,
    COALESCE(pdc.mapping_complexity, 'simple'),
    pdc.mapping_notes,
    COALESCE(pdc.created_at, NOW()),
    COALESCE(pdc.updated_at, NOW())
FROM mcl.postgres_default_constraints pdc
WHERE pdc.definition IS NOT NULL AND pdc.definition != '';

-- 5. Аналогично для CHECK и indexes
```

---

## 📊 СРАВНЕНИЕ: БЫЛО → СТАЛО

### БЫЛО (дублирование):

```
postgres_columns:
  - computed_definition
  - postgres_computed_definition
  - computed_function_mapping_rule_id
  - computed_mapping_status
  - computed_mapping_complexity
  - computed_mapping_notes
  
postgres_default_constraints:
  - definition
  - postgres_definition
  - function_mapping_rule_id
  - mapping_status
  - mapping_complexity
  - mapping_notes

(+ аналогично еще 2 таблицы)

ИТОГО: 24 поля (6 × 4 таблицы)
```

### СТАЛО (нормализация):

```
function_conversions (родитель):
  - source_definition          ← Общее
  - target_definition          ← Общее
  - mapping_rule_id            ← Общее
  - mapping_status             ← Общее
  - mapping_complexity         ← Общее
  - mapping_notes              ← Общее
  - manual_developer           ← Общее
  - manual_started_at          ← Общее
  - manual_completed_at        ← Общее
  - created_at, updated_at     ← Общее
  
column_function_conversions:
  - column_id                  ← Специфичное (FK)
  
default_constraint_function_conversions:
  - constraint_id              ← Специфичное (FK)
  
check_constraint_function_conversions:
  - constraint_id              ← Специфичное (FK)
  
index_function_conversions:
  - index_id                   ← Специфичное (FK)
  - is_functional              ← Специфичное (опционально)
  - filter_expression          ← Специфичное (опционально)

ИТОГО: 11 общих + 4 FK + 2 специфичных = 17 полей
```

**Экономия:** 24 → 17 полей (30% меньше)

---

## 🎯 ПРОЦЕСС РАБОТЫ (примеры)

### Автоматическая обработка:

```python
# Обработать ВСЕ типы объектов одной командой
converter = FunctionConverter(manager)

# Применить правила ко ВСЕМ pending (работает с родительской!)
cursor.execute('''
    SELECT id, source_definition
    FROM mcl.function_conversions
    WHERE mapping_status = 'pending'
''')

for conv_id, source_def in cursor.fetchall():
    result = converter.apply_rules(source_def)
    
    if result.success:
        cursor.execute('''
            UPDATE mcl.function_conversions
            SET target_definition = %s,
                mapping_rule_id = %s,
                mapping_status = 'automatic-mapped'
            WHERE id = %s
        ''', [result.target, result.rule_id, conv_id])
```

### Ручная разработка:

```python
# Получить список (из родительской - видит все типы!)
cursor.execute('''
    SELECT id, source_definition
    FROM mcl.function_conversions
    WHERE mapping_status = 'manual-required'
    LIMIT 10
''')

# Начать работу
converter.start_manual(conversion_id=123, developer='AI-Assistant')

# ... разработка PostgreSQL кода в чате ...

# Завершить
converter.complete_manual(
    conversion_id=123,
    target_def='ags.fn_cn_num(cn_key)'
)
```

### Запрос с типом объекта:

```sql
-- С использованием представления
SELECT 
    id,
    object_type,
    object_id,
    source_definition,
    target_definition,
    mapping_status
FROM mcl.v_function_conversions_typed
WHERE mapping_status = 'manual-in-progress';
```

---

## ✅ ИТОГОВАЯ СТРУКТУРА

```
Уровень 1: function_mapping_rules
            ↓ (18 правил маппинга)
            
Уровень 2: function_conversions (РОДИТЕЛЬ)
            ├── source_definition, target_definition  ← Вся логика обработки
            ├── mapping_status, complexity, notes
            └── manual_developer, started_at, completed_at
            
Уровень 3: Дочерние (ТОЛЬКО связи)
            ├── column_function_conversions (column_id FK)
            ├── default_constraint_function_conversions (constraint_id FK)
            ├── check_constraint_function_conversions (constraint_id FK)
            └── index_function_conversions (index_id FK + специфичные)
            
Уровень 4: Объекты
            ├── postgres_columns
            ├── postgres_default_constraints
            ├── postgres_check_constraints
            └── postgres_indexes
```

---

**Документ создан:** 2025-10-07  
**Версия:** FINAL (source/target в родительской, дочерние минимальны)  
**Статус:** Уточненное предложение готово, изменений не внесено  
**Следующий шаг:** Начать Фазу 1 - Документирование

