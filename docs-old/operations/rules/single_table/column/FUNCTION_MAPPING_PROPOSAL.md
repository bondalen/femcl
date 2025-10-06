# 🎯 ПРЕДЛОЖЕНИЕ ПО ОПРЕДЕЛЕНИЮ ЦЕЛЕВЫХ ФУНКЦИЙ

## 🎯 НАЗНАЧЕНИЕ ДОКУМЕНТА

Данный документ содержит предложения по определению целевых функций на этапе формирования метаданных для обеспечения корректной миграции функций MS SQL Server в PostgreSQL.

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ

### **Найденные случаи использования функций:**
- **Значения по умолчанию:** 17 случаев (getdate())
- **Вычисляемые колонки:** 67 колонок (isnull(), len(), upper(), lower(), и др.)
- **Итого:** 84 случая использования функций

### **Текущая структура метаданных:**
- **`mcl.postgres_default_constraints.definition`** - содержит исходные определения с функциями MS SQL
- **`mcl.postgres_columns.computed_definition`** - содержит исходные определения вычисляемых колонок

---

## 🎯 ПРЕДЛОЖЕНИЯ ПО СТРУКТУРЕ ХРАНЕНИЯ ЦЕЛЕВЫХ ФУНКЦИЙ

### **ПОДХОД 1: РАСШИРЕНИЕ СУЩЕСТВУЮЩИХ ТАБЛИЦ**

#### **1.1 Расширение таблицы `postgres_default_constraints`**

```sql
-- Добавление полей для целевых функций
ALTER TABLE mcl.postgres_default_constraints 
ADD COLUMN postgres_definition TEXT,
ADD COLUMN function_mapping_status VARCHAR DEFAULT 'pending',
ADD COLUMN source_functions TEXT[], -- массив исходных функций
ADD COLUMN target_functions TEXT[], -- массив целевых функций
ADD COLUMN mapping_complexity VARCHAR DEFAULT 'simple'; -- simple, complex, custom
```

**Назначение полей:**
- **`postgres_definition`** - определение для PostgreSQL с замененными функциями
- **`function_mapping_status`** - статус маппинга функций (pending, mapped, error)
- **`source_functions`** - массив найденных исходных функций
- **`target_functions`** - массив соответствующих целевых функций
- **`mapping_complexity`** - сложность маппинга (simple/complex/custom)

#### **1.2 Расширение таблицы `postgres_columns`**

```sql
-- Добавление полей для целевых функций в вычисляемых колонках
ALTER TABLE mcl.postgres_columns 
ADD COLUMN postgres_computed_definition TEXT,
ADD COLUMN computed_function_mapping_status VARCHAR DEFAULT 'pending',
ADD COLUMN computed_source_functions TEXT[],
ADD COLUMN computed_target_functions TEXT[],
ADD COLUMN computed_mapping_complexity VARCHAR DEFAULT 'simple';
```

**Назначение полей:**
- **`postgres_computed_definition`** - определение вычисляемой колонки для PostgreSQL
- **`computed_function_mapping_status`** - статус маппинга функций в вычисляемых колонках
- **`computed_source_functions`** - массив исходных функций в вычисляемой колонке
- **`computed_target_functions`** - массив целевых функций
- **`computed_mapping_complexity`** - сложность маппинга

---

### **ПОДХОД 2: ОТДЕЛЬНАЯ ТАБЛИЦА МАППИНГА ФУНКЦИЙ**

#### **2.1 Создание таблицы маппинга функций**

```sql
-- Таблица для хранения маппинга функций
CREATE TABLE mcl.function_mappings (
    id SERIAL PRIMARY KEY,
    source_function_name VARCHAR NOT NULL,
    target_function_name VARCHAR NOT NULL,
    source_syntax TEXT,
    target_syntax TEXT,
    mapping_type VARCHAR NOT NULL, -- direct, complex, custom
    complexity_level INTEGER DEFAULT 1, -- 1=simple, 2=complex, 3=custom
    description TEXT,
    examples TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого поиска
CREATE INDEX idx_function_mappings_source ON mcl.function_mappings(source_function_name);
CREATE INDEX idx_function_mappings_type ON mcl.function_mappings(mapping_type);
```

#### **2.2 Создание таблицы использования функций**

```sql
-- Таблица для отслеживания использования функций
CREATE TABLE mcl.function_usage (
    id SERIAL PRIMARY KEY,
    function_mapping_id INTEGER REFERENCES mcl.function_mappings(id),
    usage_type VARCHAR NOT NULL, -- 'default_constraint', 'computed_column'
    table_id INTEGER,
    column_id INTEGER,
    constraint_id INTEGER,
    source_definition TEXT,
    target_definition TEXT,
    mapping_status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы
CREATE INDEX idx_function_usage_type ON mcl.function_usage(usage_type);
CREATE INDEX idx_function_usage_status ON mcl.function_usage(mapping_status);
```

---

### **ПОДХОД 3: ГИБРИДНЫЙ ПОДХОД (РЕКОМЕНДУЕМЫЙ)**

#### **3.1 Расширение существующих таблиц + справочник маппинга**

```sql
-- 1. Расширяем postgres_default_constraints
ALTER TABLE mcl.postgres_default_constraints 
ADD COLUMN postgres_definition TEXT,
ADD COLUMN function_mapping_status VARCHAR DEFAULT 'pending',
ADD COLUMN mapping_complexity VARCHAR DEFAULT 'simple',
ADD COLUMN function_mapping_notes TEXT;

-- 2. Расширяем postgres_columns
ALTER TABLE mcl.postgres_columns 
ADD COLUMN postgres_computed_definition TEXT,
ADD COLUMN computed_function_mapping_status VARCHAR DEFAULT 'pending',
ADD COLUMN computed_mapping_complexity VARCHAR DEFAULT 'simple',
ADD COLUMN computed_function_mapping_notes TEXT;

-- 3. Создаем справочник маппинга функций
CREATE TABLE mcl.function_mapping_rules (
    id SERIAL PRIMARY KEY,
    source_function VARCHAR NOT NULL,
    target_function VARCHAR NOT NULL,
    mapping_pattern TEXT NOT NULL, -- регулярное выражение для поиска
    replacement_pattern TEXT NOT NULL, -- шаблон замены
    mapping_type VARCHAR NOT NULL, -- direct, regex, custom
    complexity_level INTEGER DEFAULT 1,
    description TEXT,
    examples TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Создаем таблицу примененных маппингов
CREATE TABLE mcl.applied_function_mappings (
    id SERIAL PRIMARY KEY,
    mapping_rule_id INTEGER REFERENCES mcl.function_mapping_rules(id),
    usage_type VARCHAR NOT NULL, -- 'default_constraint', 'computed_column'
    object_id INTEGER NOT NULL, -- ID объекта (constraint_id или column_id)
    source_definition TEXT,
    target_definition TEXT,
    mapping_status VARCHAR DEFAULT 'pending', -- pending, applied, error
    error_message TEXT,
    applied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔧 АЛГОРИТМ ОПРЕДЕЛЕНИЯ ЦЕЛЕВЫХ ФУНКЦИЙ

### **Этап 1: Анализ и идентификация функций**

```python
def analyze_functions_in_definitions(task_id: int) -> Dict:
    """
    Анализ всех определений на наличие функций MS SQL Server
    """
    functions_found = {
        'default_constraints': {},
        'computed_columns': {}
    }
    
    # Анализ default constraints
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
        functions = extract_functions_from_definition(definition)
        if functions:
            functions_found['default_constraints'][constraint_id] = {
                'table_name': table_name,
                'definition': definition,
                'functions': functions
            }
    
    # Анализ computed columns
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
        functions = extract_functions_from_definition(definition)
        if functions:
            functions_found['computed_columns'][column_id] = {
                'table_name': table_name,
                'column_name': column_name,
                'definition': definition,
                'functions': functions
            }
    
    return functions_found

def extract_functions_from_definition(definition: str) -> List[str]:
    """
    Извлечение функций из определения
    """
    import re
    
    # Паттерны для поиска функций MS SQL Server
    function_patterns = [
        r'\bgetdate\s*\(',      # getdate()
        r'\bisnull\s*\(',       # isnull()
        r'\blen\s*\(',          # len()
        r'\bupper\s*\(',        # upper()
        r'\blower\s*\(',        # lower()
        r'\bsubstring\s*\(',    # substring()
        r'\bconvert\s*\(',      # convert()
        r'\bcast\s*\(',         # cast()
        r'\bdateadd\s*\(',      # dateadd()
        r'\bdatediff\s*\(',     # datediff()
        r'\byear\s*\(',         # year()
        r'\bmonth\s*\(',        # month()
        r'\bday\s*\(',          # day()
    ]
    
    found_functions = []
    for pattern in function_patterns:
        matches = re.findall(pattern, definition.lower())
        for match in matches:
            func_name = match.split('(')[0].strip()
            if func_name not in found_functions:
                found_functions.append(func_name)
    
    return found_functions
```

### **Этап 2: Применение правил маппинга**

```python
def apply_function_mapping_rules(task_id: int) -> bool:
    """
    Применение правил маппинга функций к определениям
    """
    # Загружаем правила маппинга
    cursor.execute('''
        SELECT 
            id,
            source_function,
            target_function,
            mapping_pattern,
            replacement_pattern,
            mapping_type,
            complexity_level
        FROM mcl.function_mapping_rules
        WHERE is_active = TRUE
        ORDER BY complexity_level, source_function
    ''')
    
    mapping_rules = cursor.fetchall()
    
    # Применяем к default constraints
    apply_mapping_to_default_constraints(task_id, mapping_rules)
    
    # Применяем к computed columns
    apply_mapping_to_computed_columns(task_id, mapping_rules)
    
    return True

def apply_mapping_to_default_constraints(task_id: int, mapping_rules: List) -> None:
    """
    Применение маппинга к default constraints
    """
    cursor.execute('''
        SELECT 
            pdc.id,
            pdc.definition
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_tables pt ON pdc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pdc.definition IS NOT NULL
    ''', (task_id,))
    
    for constraint_id, definition in cursor.fetchall():
        target_definition = definition
        mapping_complexity = 'simple'
        applied_rules = []
        
        for rule_id, source_func, target_func, pattern, replacement, mapping_type, complexity in mapping_rules:
            if source_func in definition.lower():
                if mapping_type == 'direct':
                    # Простая замена
                    target_definition = target_definition.replace(source_func, target_func)
                elif mapping_type == 'regex':
                    # Замена по регулярному выражению
                    import re
                    target_definition = re.sub(pattern, replacement, target_definition, flags=re.IGNORECASE)
                
                applied_rules.append(rule_id)
                if complexity > 1:
                    mapping_complexity = 'complex'
        
        # Обновляем запись
        cursor.execute('''
            UPDATE mcl.postgres_default_constraints 
            SET 
                postgres_definition = %s,
                function_mapping_status = 'mapped',
                mapping_complexity = %s
            WHERE id = %s
        ''', (target_definition, mapping_complexity, constraint_id))
        
        # Записываем примененные маппинги
        for rule_id in applied_rules:
            cursor.execute('''
                INSERT INTO mcl.applied_function_mappings 
                (mapping_rule_id, usage_type, object_id, source_definition, target_definition, mapping_status)
                VALUES (%s, 'default_constraint', %s, %s, %s, 'applied')
            ''', (rule_id, constraint_id, definition, target_definition))
```

### **Этап 3: Валидация и проверка**

```python
def validate_function_mappings(task_id: int) -> Dict:
    """
    Валидация примененных маппингов функций
    """
    validation_results = {
        'total_processed': 0,
        'successful_mappings': 0,
        'failed_mappings': 0,
        'errors': []
    }
    
    # Проверяем default constraints
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN function_mapping_status = 'mapped' THEN 1 END) as mapped,
            COUNT(CASE WHEN function_mapping_status = 'error' THEN 1 END) as errors
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_tables pt ON pdc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pdc.definition IS NOT NULL
    ''', (task_id,))
    
    default_stats = cursor.fetchone()
    
    # Проверяем computed columns
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN computed_function_mapping_status = 'mapped' THEN 1 END) as mapped,
            COUNT(CASE WHEN computed_function_mapping_status = 'error' THEN 1 END) as errors
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
            AND pc.computed_definition IS NOT NULL
    ''', (task_id,))
    
    computed_stats = cursor.fetchone()
    
    validation_results['total_processed'] = default_stats[0] + computed_stats[0]
    validation_results['successful_mappings'] = default_stats[1] + computed_stats[1]
    validation_results['failed_mappings'] = default_stats[2] + computed_stats[2]
    
    return validation_results
```

---

## 📋 ПРИМЕРЫ ПРАВИЛ МАППИНГА

### **Базовые правила маппинга**

```sql
-- Вставка базовых правил маппинга
INSERT INTO mcl.function_mapping_rules (source_function, target_function, mapping_pattern, replacement_pattern, mapping_type, complexity_level, description) VALUES
-- Простые замены
('getdate', 'NOW', 'getdate\\s*\\(\\s*\\)', 'NOW()', 'direct', 1, 'Замена getdate() на NOW()'),
('isnull', 'COALESCE', 'isnull\\s*\\(\\s*([^,]+)\\s*,\\s*([^)]+)\\s*\\)', 'COALESCE(\\1, \\2)', 'regex', 1, 'Замена isnull(expr1, expr2) на COALESCE(expr1, expr2)'),
('len', 'LENGTH', 'len\\s*\\(\\s*([^)]+)\\s*\\)', 'LENGTH(\\1)', 'regex', 1, 'Замена len() на LENGTH()'),
('upper', 'UPPER', 'upper\\s*\\(\\s*([^)]+)\\s*\\)', 'UPPER(\\1)', 'regex', 1, 'Замена upper() на UPPER()'),
('lower', 'LOWER', 'lower\\s*\\(\\s*([^)]+)\\s*\\)', 'LOWER(\\1)', 'regex', 1, 'Замена lower() на LOWER()'),

-- Сложные замены
('substring', 'SUBSTRING', 'substring\\s*\\(\\s*([^,]+)\\s*,\\s*([^,]+)\\s*,\\s*([^)]+)\\s*\\)', 'SUBSTRING(\\1 FROM \\2 FOR \\3)', 'regex', 2, 'Замена substring(str, start, length) на SUBSTRING(str FROM start FOR length)'),
('convert', 'CAST', 'convert\\s*\\(\\s*([^,]+)\\s*,\\s*([^)]+)\\s*\\)', 'CAST(\\2 AS \\1)', 'regex', 2, 'Замена convert(datatype, expression) на CAST(expression AS datatype)'),

-- Функции дат
('dateadd', 'DATE_ADD', 'dateadd\\s*\\(\\s*([^,]+)\\s*,\\s*([^,]+)\\s*,\\s*([^)]+)\\s*\\)', '\\3 + INTERVAL \\2 \\1', 'regex', 2, 'Замена dateadd(datepart, number, date) на date + INTERVAL number datepart'),
('datediff', 'DATE_PART', 'datediff\\s*\\(\\s*([^,]+)\\s*,\\s*([^,]+)\\s*,\\s*([^)]+)\\s*\\)', 'DATE_PART(\\1, \\3) - DATE_PART(\\1, \\2)', 'regex', 3, 'Замена datediff(datepart, startdate, enddate) на DATE_PART(datepart, enddate) - DATE_PART(datepart, startdate)'),
('year', 'EXTRACT', 'year\\s*\\(\\s*([^)]+)\\s*\\)', 'EXTRACT(YEAR FROM \\1)', 'regex', 1, 'Замена year(date) на EXTRACT(YEAR FROM date)'),
('month', 'EXTRACT', 'month\\s*\\(\\s*([^)]+)\\s*\\)', 'EXTRACT(MONTH FROM \\1)', 'regex', 1, 'Замена month(date) на EXTRACT(MONTH FROM date)'),
('day', 'EXTRACT', 'day\\s*\\(\\s*([^)]+)\\s*\\)', 'EXTRACT(DAY FROM \\1)', 'regex', 1, 'Замена day(date) на EXTRACT(DAY FROM date)');
```

---

## 🎯 РЕКОМЕНДУЕМЫЙ ПОДХОД

### **Гибридный подход (Подход 3)**

**Преимущества:**
1. ✅ **Централизованные правила** маппинга в справочной таблице
2. ✅ **Готовые определения** для PostgreSQL в существующих таблицах
3. ✅ **Отслеживание применения** маппингов
4. ✅ **Гибкость** в добавлении новых правил
5. ✅ **Валидация** и контроль качества

**Структура:**
- **`postgres_default_constraints.postgres_definition`** - готовые определения для PostgreSQL
- **`postgres_columns.postgres_computed_definition`** - готовые определения вычисляемых колонок
- **`function_mapping_rules`** - справочник правил маппинга
- **`applied_function_mappings`** - журнал примененных маппингов

---

## 🚀 ПЛАН ВНЕДРЕНИЯ

### **Этап 1: Создание структуры**
1. Добавление полей в существующие таблицы
2. Создание справочных таблиц
3. Создание индексов

### **Этап 2: Заполнение правил маппинга**
1. Вставка базовых правил маппинга
2. Тестирование правил на примерах
3. Добавление сложных правил

### **Этап 3: Применение маппинга**
1. Анализ существующих определений
2. Применение правил маппинга
3. Валидация результатов

### **Этап 4: Тестирование**
1. Проверка корректности маппинга
2. Тестирование на реальных данных
3. Корректировка правил при необходимости

---

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

После внедрения системы маппинга функций:

1. **84 случая использования функций** будут обработаны автоматически
2. **Готовые определения** для PostgreSQL будут доступны в метаданных
3. **Централизованное управление** правилами маппинга
4. **Возможность расширения** для новых типов функций
5. **Полная трассируемость** применения маппингов

Это обеспечит корректную миграцию всех функций MS SQL Server в PostgreSQL на этапе формирования метаданных.