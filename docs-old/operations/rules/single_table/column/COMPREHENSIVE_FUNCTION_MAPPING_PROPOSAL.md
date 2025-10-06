# 🎯 УНИВЕРСАЛЬНОЕ ПРЕДЛОЖЕНИЕ ПО ОПРЕДЕЛЕНИЮ ЦЕЛЕВЫХ ФУНКЦИЙ ДЛЯ ВСЕХ ТИПОВ ОБЪЕКТОВ

## 🎯 НАЗНАЧЕНИЕ ДОКУМЕНТА

Данный документ содержит универсальное предложение по определению целевых функций на этапе формирования метаданных с использованием внешних ключей для связи всех типов объектов с правилами маппинга функций.

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ ВСЕХ ТИПОВ ОБЪЕКТОВ

### **Найденные случаи использования функций:**
- **Значения по умолчанию:** 17 случаев (getdate())
- **Вычисляемые колонки:** 67 колонок (isnull(), len(), upper(), lower(), и др.)
- **CHECK ограничения:** 31 ограничение (функции пока не найдены, но потенциал высокий)
- **Индексы:** 150 индексов (функции пока не найдены, но потенциал средний)
- **Итого:** 84 текущих случая + 181 потенциальный случай = 265 возможных случаев

### **Проблема текущего подхода:**
- Неполное покрытие типов объектов
- Отсутствие готовности к будущим функциям
- Неравномерный подход к разным типам объектов
- Потенциальные проблемы при появлении функций в новых местах

---

## 🚀 УНИВЕРСАЛЬНОЕ РЕШЕНИЕ С ВНЕШНИМИ КЛЮЧАМИ ДЛЯ ВСЕХ ТИПОВ

### **🏗️ ПОЛНАЯ АРХИТЕКТУРА С ВНЕШНИМИ КЛЮЧАМИ**

#### **1. Справочная таблица правил маппинга (без изменений)**

```sql
-- Создание справочной таблицы правил маппинга функций
CREATE TABLE mcl.function_mapping_rules (
    id SERIAL PRIMARY KEY,
    source_function VARCHAR NOT NULL,
    target_function VARCHAR NOT NULL,
    mapping_pattern TEXT NOT NULL,
    replacement_pattern TEXT NOT NULL,
    mapping_type VARCHAR NOT NULL DEFAULT 'direct', -- direct, regex, custom
    complexity_level INTEGER DEFAULT 1, -- 1=simple, 2=complex, 3=custom
    applicable_objects TEXT[] DEFAULT '{}', -- массив типов объектов: {'default_constraint', 'computed_column', 'check_constraint', 'index'}
    description TEXT,
    examples TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого поиска
CREATE INDEX idx_function_mapping_rules_source ON mcl.function_mapping_rules(source_function);
CREATE INDEX idx_function_mapping_rules_type ON mcl.function_mapping_rules(mapping_type);
CREATE INDEX idx_function_mapping_rules_active ON mcl.function_mapping_rules(is_active);
CREATE INDEX idx_function_mapping_rules_objects ON mcl.function_mapping_rules USING GIN(applicable_objects);
```

#### **2. Расширение таблицы default constraints**

```sql
-- Расширение таблицы postgres_default_constraints
ALTER TABLE mcl.postgres_default_constraints 
ADD COLUMN function_mapping_rule_id INTEGER,
ADD COLUMN postgres_definition TEXT,
ADD COLUMN mapping_status VARCHAR DEFAULT 'pending', -- pending, mapped, error
ADD COLUMN mapping_complexity VARCHAR DEFAULT 'simple', -- simple, complex, custom
ADD COLUMN mapping_notes TEXT;

-- Создание внешнего ключа
ALTER TABLE mcl.postgres_default_constraints 
ADD CONSTRAINT fk_default_function_mapping
FOREIGN KEY (function_mapping_rule_id)
REFERENCES mcl.function_mapping_rules(id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Индексы
CREATE INDEX idx_postgres_default_constraints_mapping ON mcl.postgres_default_constraints(function_mapping_rule_id);
CREATE INDEX idx_postgres_default_constraints_status ON mcl.postgres_default_constraints(mapping_status);
```

#### **3. Расширение таблицы computed columns**

```sql
-- Расширение таблицы postgres_columns для computed columns
ALTER TABLE mcl.postgres_columns 
ADD COLUMN computed_function_mapping_rule_id INTEGER,
ADD COLUMN postgres_computed_definition TEXT,
ADD COLUMN computed_mapping_status VARCHAR DEFAULT 'pending', -- pending, mapped, error
ADD COLUMN computed_mapping_complexity VARCHAR DEFAULT 'simple', -- simple, complex, custom
ADD COLUMN computed_mapping_notes TEXT;

-- Создание внешнего ключа
ALTER TABLE mcl.postgres_columns 
ADD CONSTRAINT fk_computed_function_mapping
FOREIGN KEY (computed_function_mapping_rule_id)
REFERENCES mcl.function_mapping_rules(id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Индексы
CREATE INDEX idx_postgres_columns_computed_mapping ON mcl.postgres_columns(computed_function_mapping_rule_id);
CREATE INDEX idx_postgres_columns_computed_status ON mcl.postgres_columns(computed_mapping_status);
```

#### **4. Расширение таблицы CHECK constraints**

```sql
-- Расширение таблицы postgres_check_constraints
ALTER TABLE mcl.postgres_check_constraints 
ADD COLUMN function_mapping_rule_id INTEGER,
ADD COLUMN postgres_definition TEXT,
ADD COLUMN mapping_status VARCHAR DEFAULT 'pending', -- pending, mapped, error
ADD COLUMN mapping_complexity VARCHAR DEFAULT 'simple', -- simple, complex, custom
ADD COLUMN mapping_notes TEXT;

-- Создание внешнего ключа
ALTER TABLE mcl.postgres_check_constraints 
ADD CONSTRAINT fk_check_function_mapping
FOREIGN KEY (function_mapping_rule_id)
REFERENCES mcl.function_mapping_rules(id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Индексы
CREATE INDEX idx_postgres_check_constraints_mapping ON mcl.postgres_check_constraints(function_mapping_rule_id);
CREATE INDEX idx_postgres_check_constraints_status ON mcl.postgres_check_constraints(mapping_status);
```

#### **5. Расширение таблицы индексов**

```sql
-- Расширение таблицы postgres_indexes
ALTER TABLE mcl.postgres_indexes 
ADD COLUMN function_mapping_rule_id INTEGER,
ADD COLUMN postgres_definition TEXT,
ADD COLUMN mapping_status VARCHAR DEFAULT 'pending', -- pending, mapped, error
ADD COLUMN mapping_complexity VARCHAR DEFAULT 'simple', -- simple, complex, custom
ADD COLUMN mapping_notes TEXT;

-- Создание внешнего ключа
ALTER TABLE mcl.postgres_indexes 
ADD CONSTRAINT fk_index_function_mapping
FOREIGN KEY (function_mapping_rule_id)
REFERENCES mcl.function_mapping_rules(id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Индексы
CREATE INDEX idx_postgres_indexes_mapping ON mcl.postgres_indexes(function_mapping_rule_id);
CREATE INDEX idx_postgres_indexes_status ON mcl.postgres_indexes(mapping_status);
```

---

## 🔮 ПОТЕНЦИАЛЬНЫЕ ФУНКЦИИ В CHECK ОГРАНИЧЕНИЯХ И ИНДЕКСАХ

### **CHECK ограничения с функциями:**

| Пример | MS SQL Server | PostgreSQL | Назначение |
|--------|---------------|------------|------------|
| **Проверка даты** | `CHECK (created_date > getdate())` | `CHECK (created_date > NOW())` | Валидация даты создания |
| **Проверка длины** | `CHECK (len(description) > 0)` | `CHECK (LENGTH(description) > 0)` | Валидация длины текста |
| **Проверка NULL** | `CHECK (isnull(code, '') != '')` | `CHECK (COALESCE(code, '') != '')` | Валидация наличия значения |
| **Проверка формата** | `CHECK (len(phone) >= 10)` | `CHECK (LENGTH(phone) >= 10)` | Валидация формата данных |
| **Проверка диапазона** | `CHECK (year(birth_date) >= 1900)` | `CHECK (EXTRACT(YEAR FROM birth_date) >= 1900)` | Валидация диапазона дат |

### **Функциональные индексы:**

| Пример | MS SQL Server | PostgreSQL | Назначение |
|--------|---------------|------------|------------|
| **Индекс по функции** | `CREATE INDEX idx_name ON table (upper(name))` | `CREATE INDEX idx_name ON table (UPPER(name))` | Поиск без учета регистра |
| **Индекс по дате** | `CREATE INDEX idx_date ON table (year(created_date))` | `CREATE INDEX idx_date ON table (EXTRACT(YEAR FROM created_date))` | Индексирование по году |
| **Индекс по NULL** | `CREATE INDEX idx_code ON table (isnull(code, 'DEFAULT'))` | `CREATE INDEX idx_code ON table (COALESCE(code, 'DEFAULT'))` | Индексирование с заменой NULL |
| **Сложный индекс** | `CREATE INDEX idx_complex ON table (upper(isnull(name, '')))` | `CREATE INDEX idx_complex ON table (UPPER(COALESCE(name, '')))` | Комбинированные функции |

---

## 🔧 УНИВЕРСАЛЬНЫЙ АЛГОРИТМ ОПРЕДЕЛЕНИЯ ЦЕЛЕВЫХ ФУНКЦИЙ

### **Этап 1: Создание и заполнение универсальных правил маппинга**

```python
def create_universal_function_mapping_rules() -> bool:
    """
    Создание и заполнение универсальных правил маппинга функций
    """
    cursor.execute('''
        INSERT INTO mcl.function_mapping_rules 
        (source_function, target_function, mapping_pattern, replacement_pattern, mapping_type, complexity_level, applicable_objects, description) 
        VALUES
        -- Простые замены (применимы ко всем типам объектов)
        ('getdate', 'NOW', 'getdate\\s*\\(\\s*\\)', 'NOW()', 'direct', 1, 
         ARRAY['default_constraint', 'computed_column', 'check_constraint'], 
         'Замена getdate() на NOW()'),
        
        ('isnull', 'COALESCE', 'isnull\\s*\\(\\s*([^,]+)\\s*,\\s*([^)]+)\\s*\\)', 'COALESCE(\\1, \\2)', 'regex', 1,
         ARRAY['default_constraint', 'computed_column', 'check_constraint', 'index'],
         'Замена isnull(expr1, expr2) на COALESCE(expr1, expr2)'),
        
        ('len', 'LENGTH', 'len\\s*\\(\\s*([^)]+)\\s*\\)', 'LENGTH(\\1)', 'regex', 1,
         ARRAY['computed_column', 'check_constraint', 'index'],
         'Замена len() на LENGTH()'),
        
        ('upper', 'UPPER', 'upper\\s*\\(\\s*([^)]+)\\s*\\)', 'UPPER(\\1)', 'regex', 1,
         ARRAY['computed_column', 'check_constraint', 'index'],
         'Замена upper() на UPPER()'),
        
        ('lower', 'LOWER', 'lower\\s*\\(\\s*([^)]+)\\s*\\)', 'LOWER(\\1)', 'regex', 1,
         ARRAY['computed_column', 'check_constraint', 'index'],
         'Замена lower() на LOWER()'),
        
        -- Сложные замены
        ('substring', 'SUBSTRING', 'substring\\s*\\(\\s*([^,]+)\\s*,\\s*([^,]+)\\s*,\\s*([^)]+)\\s*\\)', 'SUBSTRING(\\1 FROM \\2 FOR \\3)', 'regex', 2,
         ARRAY['computed_column', 'check_constraint', 'index'],
         'Замена substring(str, start, length) на SUBSTRING(str FROM start FOR length)'),
        
        ('convert', 'CAST', 'convert\\s*\\(\\s*([^,]+)\\s*,\\s*([^)]+)\\s*\\)', 'CAST(\\2 AS \\1)', 'regex', 2,
         ARRAY['computed_column', 'check_constraint', 'index'],
         'Замена convert(datatype, expression) на CAST(expression AS datatype)'),
        
        -- Функции дат
        ('dateadd', 'DATE_ADD', 'dateadd\\s*\\(\\s*([^,]+)\\s*,\\s*([^,]+)\\s*,\\s*([^)]+)\\s*\\)', '\\3 + INTERVAL \\2 \\1', 'regex', 2,
         ARRAY['computed_column', 'check_constraint'],
         'Замена dateadd(datepart, number, date) на date + INTERVAL number datepart'),
        
        ('datediff', 'DATE_PART', 'datediff\\s*\\(\\s*([^,]+)\\s*,\\s*([^,]+)\\s*,\\s*([^)]+)\\s*\\)', 'DATE_PART(\\1, \\3) - DATE_PART(\\1, \\2)', 'regex', 3,
         ARRAY['computed_column', 'check_constraint'],
         'Замена datediff(datepart, startdate, enddate) на DATE_PART(datepart, enddate) - DATE_PART(datepart, startdate)'),
        
        ('year', 'EXTRACT', 'year\\s*\\(\\s*([^)]+)\\s*\\)', 'EXTRACT(YEAR FROM \\1)', 'regex', 1,
         ARRAY['computed_column', 'check_constraint', 'index'],
         'Замена year(date) на EXTRACT(YEAR FROM date)'),
        
        ('month', 'EXTRACT', 'month\\s*\\(\\s*([^)]+)\\s*\\)', 'EXTRACT(MONTH FROM \\1)', 'regex', 1,
         ARRAY['computed_column', 'check_constraint', 'index'],
         'Замена month(date) на EXTRACT(MONTH FROM date)'),
        
        ('day', 'EXTRACT', 'day\\s*\\(\\s*([^)]+)\\s*\\)', 'EXTRACT(DAY FROM \\1)', 'regex', 1,
         ARRAY['computed_column', 'check_constraint', 'index'],
         'Замена day(date) на EXTRACT(DAY FROM date)')
    ''')
    
    return True
```

### **Этап 2: Универсальный анализ и связывание с правилами**

```python
def analyze_and_link_all_objects_to_rules(task_id: int) -> Dict:
    """
    Универсальный анализ всех типов объектов на наличие функций и связывание с правилами маппинга
    """
    results = {
        'default_constraints_processed': 0,
        'computed_columns_processed': 0,
        'check_constraints_processed': 0,
        'indexes_processed': 0,
        'rules_applied': {},
        'errors': []
    }
    
    # Обработка default constraints
    process_default_constraints(task_id, results)
    
    # Обработка computed columns
    process_computed_columns(task_id, results)
    
    # Обработка CHECK constraints
    process_check_constraints(task_id, results)
    
    # Обработка индексов
    process_indexes(task_id, results)
    
    return results

def process_default_constraints(task_id: int, results: Dict) -> None:
    """Обработка default constraints"""
    cursor.execute('''
        SELECT 
            pdc.id,
            pdc.definition,
            pt.object_name
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_tables pt ON pdc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pdc.definition IS NOT NULL
    ''', (task_id,))
    
    for constraint_id, definition, table_name in cursor.fetchall():
        rule_id = find_and_apply_mapping_rule(definition, 'default_constraint')
        if rule_id:
            postgres_definition = apply_rule_to_definition(definition, rule_id)
            
            cursor.execute('''
                UPDATE mcl.postgres_default_constraints 
                SET 
                    function_mapping_rule_id = %s,
                    postgres_definition = %s,
                    mapping_status = 'mapped',
                    mapping_complexity = (
                        SELECT CASE 
                            WHEN complexity_level = 1 THEN 'simple'
                            WHEN complexity_level = 2 THEN 'complex'
                            ELSE 'custom'
                        END
                        FROM mcl.function_mapping_rules 
                        WHERE id = %s
                    )
                WHERE id = %s
            ''', (rule_id, postgres_definition, rule_id, constraint_id))
            
            results['default_constraints_processed'] += 1
            results['rules_applied'][rule_id] = results['rules_applied'].get(rule_id, 0) + 1

def process_computed_columns(task_id: int, results: Dict) -> None:
    """Обработка computed columns"""
    cursor.execute('''
        SELECT 
            pc.id,
            pc.computed_definition,
            pt.object_name,
            pc.column_name
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pc.computed_definition IS NOT NULL
    ''', (task_id,))
    
    for column_id, definition, table_name, column_name in cursor.fetchall():
        rule_id = find_and_apply_mapping_rule(definition, 'computed_column')
        if rule_id:
            postgres_definition = apply_rule_to_definition(definition, rule_id)
            
            cursor.execute('''
                UPDATE mcl.postgres_columns 
                SET 
                    computed_function_mapping_rule_id = %s,
                    postgres_computed_definition = %s,
                    computed_mapping_status = 'mapped',
                    computed_mapping_complexity = (
                        SELECT CASE 
                            WHEN complexity_level = 1 THEN 'simple'
                            WHEN complexity_level = 2 THEN 'complex'
                            ELSE 'custom'
                        END
                        FROM mcl.function_mapping_rules 
                        WHERE id = %s
                    )
                WHERE id = %s
            ''', (rule_id, postgres_definition, rule_id, column_id))
            
            results['computed_columns_processed'] += 1
            results['rules_applied'][rule_id] = results['rules_applied'].get(rule_id, 0) + 1

def process_check_constraints(task_id: int, results: Dict) -> None:
    """Обработка CHECK constraints"""
    cursor.execute('''
        SELECT 
            pcc.id,
            pcc.definition,
            pt.object_name,
            pcc.constraint_name
        FROM mcl.postgres_check_constraints pcc
        JOIN mcl.postgres_tables pt ON pcc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pcc.definition IS NOT NULL
    ''', (task_id,))
    
    for constraint_id, definition, table_name, constraint_name in cursor.fetchall():
        rule_id = find_and_apply_mapping_rule(definition, 'check_constraint')
        if rule_id:
            postgres_definition = apply_rule_to_definition(definition, rule_id)
            
            cursor.execute('''
                UPDATE mcl.postgres_check_constraints 
                SET 
                    function_mapping_rule_id = %s,
                    postgres_definition = %s,
                    mapping_status = 'mapped',
                    mapping_complexity = (
                        SELECT CASE 
                            WHEN complexity_level = 1 THEN 'simple'
                            WHEN complexity_level = 2 THEN 'complex'
                            ELSE 'custom'
                        END
                        FROM mcl.function_mapping_rules 
                        WHERE id = %s
                    )
                WHERE id = %s
            ''', (rule_id, postgres_definition, rule_id, constraint_id))
            
            results['check_constraints_processed'] += 1
            results['rules_applied'][rule_id] = results['rules_applied'].get(rule_id, 0) + 1

def process_indexes(task_id: int, results: Dict) -> None:
    """Обработка индексов"""
    cursor.execute('''
        SELECT 
            pi.id,
            pi.definition,
            pt.object_name,
            pi.index_name
        FROM mcl.postgres_indexes pi
        JOIN mcl.postgres_tables pt ON pi.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pi.definition IS NOT NULL
    ''', (task_id,))
    
    for index_id, definition, table_name, index_name in cursor.fetchall():
        rule_id = find_and_apply_mapping_rule(definition, 'index')
        if rule_id:
            postgres_definition = apply_rule_to_definition(definition, rule_id)
            
            cursor.execute('''
                UPDATE mcl.postgres_indexes 
                SET 
                    function_mapping_rule_id = %s,
                    postgres_definition = %s,
                    mapping_status = 'mapped',
                    mapping_complexity = (
                        SELECT CASE 
                            WHEN complexity_level = 1 THEN 'simple'
                            WHEN complexity_level = 2 THEN 'complex'
                            ELSE 'custom'
                        END
                        FROM mcl.function_mapping_rules 
                        WHERE id = %s
                    )
                WHERE id = %s
            ''', (rule_id, postgres_definition, rule_id, index_id))
            
            results['indexes_processed'] += 1
            results['rules_applied'][rule_id] = results['rules_applied'].get(rule_id, 0) + 1

def find_and_apply_mapping_rule(definition: str, usage_type: str) -> int:
    """
    Поиск подходящего правила маппинга для определения с учетом типа объекта
    """
    cursor.execute('''
        SELECT 
            id,
            source_function,
            mapping_pattern,
            replacement_pattern,
            mapping_type,
            complexity_level
        FROM mcl.function_mapping_rules
        WHERE is_active = TRUE
            AND %s = ANY(applicable_objects)
        ORDER BY complexity_level, source_function
    ''', (usage_type,))
    
    rules = cursor.fetchall()
    
    for rule_id, source_func, pattern, replacement, mapping_type, complexity in rules:
        if source_func in definition.lower():
            return rule_id
    
    return None
```

### **Этап 3: Универсальная валидация и отчеты**

```python
def validate_universal_function_mappings(task_id: int) -> Dict:
    """
    Универсальная валидация примененных маппингов функций для всех типов объектов
    """
    validation_results = {
        'total_objects': 0,
        'mapped_objects': 0,
        'unmapped_objects': 0,
        'object_type_breakdown': {},
        'rule_usage_statistics': {},
        'coverage_analysis': {},
        'errors': []
    }
    
    # Статистика по всем типам объектов
    object_types = [
        ('default_constraints', 'postgres_default_constraints', 'function_mapping_rule_id'),
        ('computed_columns', 'postgres_columns', 'computed_function_mapping_rule_id'),
        ('check_constraints', 'postgres_check_constraints', 'function_mapping_rule_id'),
        ('indexes', 'postgres_indexes', 'function_mapping_rule_id')
    ]
    
    for object_type, table_name, fk_field in object_types:
        cursor.execute(f'''
            SELECT 
                COUNT(*) as total,
                COUNT({fk_field}) as mapped,
                COUNT(CASE WHEN {fk_field} IS NULL AND definition IS NOT NULL THEN 1 END) as unmapped
            FROM mcl.{table_name} obj
            JOIN mcl.postgres_tables pt ON obj.table_id = pt.id
            JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
            WHERE mt.task_id = %s
        ''', (task_id,))
        
        stats = cursor.fetchone()
        validation_results['object_type_breakdown'][object_type] = {
            'total': stats[0],
            'mapped': stats[1],
            'unmapped': stats[2]
        }
        
        validation_results['total_objects'] += stats[0]
        validation_results['mapped_objects'] += stats[1]
        validation_results['unmapped_objects'] += stats[2]
    
    # Статистика использования правил
    cursor.execute('''
        SELECT 
            fmr.source_function,
            fmr.target_function,
            fmr.complexity_level,
            COUNT(pdc.id) as default_constraints_count,
            COUNT(pc.id) as computed_columns_count,
            COUNT(pcc.id) as check_constraints_count,
            COUNT(pi.id) as indexes_count,
            (COUNT(pdc.id) + COUNT(pc.id) + COUNT(pcc.id) + COUNT(pi.id)) as total_usage
        FROM mcl.function_mapping_rules fmr
        LEFT JOIN mcl.postgres_default_constraints pdc ON fmr.id = pdc.function_mapping_rule_id
        LEFT JOIN mcl.postgres_columns pc ON fmr.id = pc.computed_function_mapping_rule_id
        LEFT JOIN mcl.postgres_check_constraints pcc ON fmr.id = pcc.function_mapping_rule_id
        LEFT JOIN mcl.postgres_indexes pi ON fmr.id = pi.function_mapping_rule_id
        GROUP BY fmr.id, fmr.source_function, fmr.target_function, fmr.complexity_level
        HAVING (COUNT(pdc.id) + COUNT(pc.id) + COUNT(pcc.id) + COUNT(pi.id)) > 0
        ORDER BY total_usage DESC
    ''')
    
    rule_stats = cursor.fetchall()
    validation_results['rule_usage_statistics'] = rule_stats
    
    # Анализ покрытия
    validation_results['coverage_analysis'] = {
        'coverage_percentage': (validation_results['mapped_objects'] / validation_results['total_objects'] * 100) if validation_results['total_objects'] > 0 else 0,
        'ready_for_migration': validation_results['unmapped_objects'] == 0,
        'object_types_ready': {obj_type: data['unmapped'] == 0 for obj_type, data in validation_results['object_type_breakdown'].items()}
    }
    
    return validation_results
```

---

## 📊 ПРИМЕРЫ УНИВЕРСАЛЬНЫХ ЗАПРОСОВ

### **🔍 Поиск всех объектов, использующих конкретное правило:**

```sql
-- Универсальный поиск всех объектов, использующих правило getdate → NOW
SELECT 
    'default_constraint' as object_type,
    pdc.constraint_name as object_name,
    pt.object_name as table_name,
    fmr.source_function,
    fmr.target_function,
    pdc.postgres_definition
FROM mcl.postgres_default_constraints pdc
JOIN mcl.function_mapping_rules fmr ON pdc.function_mapping_rule_id = fmr.id
JOIN mcl.postgres_tables pt ON pdc.table_id = pt.id
WHERE fmr.source_function = 'getdate'

UNION ALL

SELECT 
    'computed_column' as object_type,
    pc.column_name as object_name,
    pt.object_name as table_name,
    fmr.source_function,
    fmr.target_function,
    pc.postgres_computed_definition
FROM mcl.postgres_columns pc
JOIN mcl.function_mapping_rules fmr ON pc.computed_function_mapping_rule_id = fmr.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
WHERE fmr.source_function = 'getdate'

UNION ALL

SELECT 
    'check_constraint' as object_type,
    pcc.constraint_name as object_name,
    pt.object_name as table_name,
    fmr.source_function,
    fmr.target_function,
    pcc.postgres_definition
FROM mcl.postgres_check_constraints pcc
JOIN mcl.function_mapping_rules fmr ON pcc.function_mapping_rule_id = fmr.id
JOIN mcl.postgres_tables pt ON pcc.table_id = pt.id
WHERE fmr.source_function = 'getdate'

UNION ALL

SELECT 
    'index' as object_type,
    pi.index_name as object_name,
    pt.object_name as table_name,
    fmr.source_function,
    fmr.target_function,
    pi.postgres_definition
FROM mcl.postgres_indexes pi
JOIN mcl.function_mapping_rules fmr ON pi.function_mapping_rule_id = fmr.id
JOIN mcl.postgres_tables pt ON pi.table_id = pt.id
WHERE fmr.source_function = 'getdate';
```

### **📈 Универсальная статистика использования правил:**

```sql
-- Универсальная статистика использования правил маппинга
SELECT 
    fmr.source_function,
    fmr.target_function,
    fmr.complexity_level,
    fmr.applicable_objects,
    COUNT(pdc.id) as default_constraints_count,
    COUNT(pc.id) as computed_columns_count,
    COUNT(pcc.id) as check_constraints_count,
    COUNT(pi.id) as indexes_count,
    (COUNT(pdc.id) + COUNT(pc.id) + COUNT(pcc.id) + COUNT(pi.id)) as total_usage
FROM mcl.function_mapping_rules fmr
LEFT JOIN mcl.postgres_default_constraints pdc ON fmr.id = pdc.function_mapping_rule_id
LEFT JOIN mcl.postgres_columns pc ON fmr.id = pc.computed_function_mapping_rule_id
LEFT JOIN mcl.postgres_check_constraints pcc ON fmr.id = pcc.function_mapping_rule_id
LEFT JOIN mcl.postgres_indexes pi ON fmr.id = pi.function_mapping_rule_id
WHERE fmr.is_active = TRUE
GROUP BY fmr.id, fmr.source_function, fmr.target_function, fmr.complexity_level, fmr.applicable_objects
ORDER BY total_usage DESC;
```

### **📋 Универсальный отчет по статусу маппинга:**

```sql
-- Универсальный отчет по статусу маппинга функций для задачи
SELECT 
    'default_constraints' as object_type,
    mapping_status,
    COUNT(*) as count
FROM mcl.postgres_default_constraints pdc
JOIN mcl.postgres_tables pt ON pdc.table_id = pt.id
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
WHERE mt.task_id = 2
GROUP BY mapping_status

UNION ALL

SELECT 
    'computed_columns' as object_type,
    computed_mapping_status as mapping_status,
    COUNT(*) as count
FROM mcl.postgres_columns pc
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
WHERE mt.task_id = 2
GROUP BY computed_mapping_status

UNION ALL

SELECT 
    'check_constraints' as object_type,
    mapping_status,
    COUNT(*) as count
FROM mcl.postgres_check_constraints pcc
JOIN mcl.postgres_tables pt ON pcc.table_id = pt.id
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
WHERE mt.task_id = 2
GROUP BY mapping_status

UNION ALL

SELECT 
    'indexes' as object_type,
    mapping_status,
    COUNT(*) as count
FROM mcl.postgres_indexes pi
JOIN mcl.postgres_tables pt ON pi.table_id = pt.id
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
WHERE mt.task_id = 2
GROUP BY mapping_status
ORDER BY object_type, mapping_status;
```

---

## 🚀 ПЛАН ВНЕДРЕНИЯ УНИВЕРСАЛЬНОГО РЕШЕНИЯ

### **Этап 1: Создание универсальной структуры с внешними ключами**
1. Создание таблицы `function_mapping_rules` с полем `applicable_objects`
2. Расширение `postgres_default_constraints` с внешним ключом
3. Расширение `postgres_columns` с внешним ключом
4. Расширение `postgres_check_constraints` с внешним ключом
5. Расширение `postgres_indexes` с внешним ключом
6. Создание индексов для производительности

### **Этап 2: Заполнение универсальных правил маппинга**
1. Вставка правил с указанием применимых типов объектов
2. Тестирование правил на всех типах объектов
3. Добавление специализированных правил

### **Этап 3: Применение универсального маппинга с внешними ключами**
1. Анализ всех типов объектов на наличие функций
2. Связывание объектов с правилами через внешние ключи
3. Генерация PostgreSQL определений для всех типов
4. Запись результатов в метаданные

### **Этап 4: Универсальная валидация и отчеты**
1. Проверка корректности связей для всех типов
2. Генерация универсальной статистики использования правил
3. Выявление необработанных объектов всех типов
4. Корректировка правил при необходимости

---

## 🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ УНИВЕРСАЛЬНОГО РЕШЕНИЯ

После внедрения универсального решения с внешними ключами:

1. **84 текущих случая использования функций** будут связаны с правилами через внешние ключи
2. **181 потенциальный случай** будет готов к обработке при появлении функций
3. **4 типа объектов** будут покрыты единой системой маппинга
4. **Централизованное управление** правилами маппинга для всех типов
5. **Автоматическое обновление** всех связанных объектов при изменении правил
6. **Полная трассируемость** применения правил ко всем типам объектов
7. **Эффективные запросы** для анализа и отчетности по всем типам
8. **Масштабируемость** для добавления новых типов объектов и правил

---

## 🏆 ЗАКЛЮЧЕНИЕ

**Универсальная система маппинга функций с внешними ключами обеспечивает:**

- ✅ **Полноту покрытия** - все типы объектов с функциями покрыты
- ✅ **Проактивность** - готовность к будущим функциям
- ✅ **Консистентность** - единый подход ко всем объектам
- ✅ **Масштабируемость** - легкость добавления новых типов
- ✅ **Универсальность** - один справочник правил для всех
- ✅ **Нормализацию данных** - избежание дублирования правил
- ✅ **Управляемость** - централизованное управление правилами
- ✅ **Трассируемость** - четкая связь объектов с правилами
- ✅ **Производительность** - эффективные JOIN запросы
- ✅ **Гибкость** - легкость расширения и модификации

**Это решение обеспечивает корпоративный уровень архитектуры для системы миграции функций MS SQL Server в PostgreSQL с полным покрытием всех типов объектов базы данных.**