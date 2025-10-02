# 🎯 УЛУЧШЕННОЕ ПРЕДЛОЖЕНИЕ ПО ОПРЕДЕЛЕНИЮ ЦЕЛЕВЫХ ФУНКЦИЙ С ВНЕШНИМИ КЛЮЧАМИ

## 🎯 НАЗНАЧЕНИЕ ДОКУМЕНТА

Данный документ содержит улучшенные предложения по определению целевых функций на этапе формирования метаданных с использованием внешних ключей для связи объектов с правилами маппинга функций.

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ

### **Найденные случаи использования функций:**
- **Значения по умолчанию:** 17 случаев (getdate())
- **Вычисляемые колонки:** 67 колонок (isnull(), len(), upper(), lower(), и др.)
- **Итого:** 84 случая использования функций

### **Проблема текущего подхода:**
- Неявная связь между объектами и правилами маппинга
- Дублирование правил в определениях
- Сложность управления и обновления правил
- Отсутствие трассируемости применения правил

---

## 🚀 УЛУЧШЕННОЕ РЕШЕНИЕ С ВНЕШНИМИ КЛЮЧАМИ

### **🏗️ АРХИТЕКТУРА С ВНЕШНИМИ КЛЮЧАМИ**

#### **1. Справочная таблица правил маппинга**

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

---

## 🔗 ПРЕИМУЩЕСТВА ВНЕШНИХ КЛЮЧЕЙ

### **✅ НОРМАЛИЗАЦИЯ ДАННЫХ:**
- Избежание дублирования правил маппинга
- Централизованное хранение правил
- Консистентность данных

### **✅ УПРАВЛЯЕМОСТЬ:**
- Изменение правила в одном месте
- Автоматическое обновление всех связанных объектов
- Возможность версионирования правил

### **✅ ТРАССИРУЕМОСТЬ:**
- Четкая связь объект → правило
- Легкость анализа использования правил
- Возможность аудита изменений

### **✅ ПРОИЗВОДИТЕЛЬНОСТЬ:**
- Быстрые JOIN запросы
- Эффективные индексы
- Оптимизированные отчеты

### **✅ ГИБКОСТЬ:**
- Легкость добавления новых правил
- Возможность кастомных правил
- Простота тестирования

---

## 📊 ПРИМЕРЫ СВЯЗЕЙ ЧЕРЕЗ ВНЕШНИЕ КЛЮЧИ

| Объект | Правило маппинга | Исходная функция | Целевая функция |
|--------|------------------|------------------|-----------------|
| **Default Constraint #1** | getdate → NOW | `getdate()` | `NOW()` |
| **Default Constraint #2** | getdate → NOW | `getdate()` | `NOW()` |
| **Computed Column #1** | isnull → COALESCE | `isnull(expr1, expr2)` | `COALESCE(expr1, expr2)` |
| **Computed Column #2** | len → LENGTH | `len(expression)` | `LENGTH(expression)` |
| **Computed Column #3** | isnull → COALESCE | `isnull(expr1, expr2)` | `COALESCE(expr1, expr2)` |

---

## 🔧 АЛГОРИТМ ОПРЕДЕЛЕНИЯ ЦЕЛЕВЫХ ФУНКЦИЙ С ВНЕШНИМИ КЛЮЧАМИ

### **Этап 1: Создание и заполнение правил маппинга**

```python
def create_function_mapping_rules() -> bool:
    """
    Создание и заполнение базовых правил маппинга функций
    """
    cursor.execute('''
        INSERT INTO mcl.function_mapping_rules 
        (source_function, target_function, mapping_pattern, replacement_pattern, mapping_type, complexity_level, description) 
        VALUES
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
        ('day', 'EXTRACT', 'day\\s*\\(\\s*([^)]+)\\s*\\)', 'EXTRACT(DAY FROM \\1)', 'regex', 1, 'Замена day(date) на EXTRACT(DAY FROM date)')
    ''')
    
    return True
```

### **Этап 2: Анализ и связывание с правилами**

```python
def analyze_and_link_functions_to_rules(task_id: int) -> Dict:
    """
    Анализ функций в определениях и связывание с правилами маппинга
    """
    results = {
        'default_constraints_processed': 0,
        'computed_columns_processed': 0,
        'rules_applied': {},
        'errors': []
    }
    
    # Обработка default constraints
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
    
    # Обработка computed columns
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
    
    return results

def find_and_apply_mapping_rule(definition: str, usage_type: str) -> int:
    """
    Поиск подходящего правила маппинга для определения
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
        ORDER BY complexity_level, source_function
    ''')
    
    rules = cursor.fetchall()
    
    for rule_id, source_func, pattern, replacement, mapping_type, complexity in rules:
        if source_func in definition.lower():
            return rule_id
    
    return None

def apply_rule_to_definition(definition: str, rule_id: int) -> str:
    """
    Применение правила маппинга к определению
    """
    cursor.execute('''
        SELECT mapping_pattern, replacement_pattern, mapping_type
        FROM mcl.function_mapping_rules
        WHERE id = %s
    ''', (rule_id,))
    
    pattern, replacement, mapping_type = cursor.fetchone()
    
    if mapping_type == 'direct':
        # Простая замена
        return definition.replace(pattern.split('\\')[0], replacement.split('\\')[0])
    elif mapping_type == 'regex':
        # Замена по регулярному выражению
        import re
        return re.sub(pattern, replacement, definition, flags=re.IGNORECASE)
    
    return definition
```

### **Этап 3: Валидация и отчеты**

```python
def validate_function_mappings_with_fk(task_id: int) -> Dict:
    """
    Валидация примененных маппингов функций с использованием внешних ключей
    """
    validation_results = {
        'total_objects': 0,
        'mapped_objects': 0,
        'unmapped_objects': 0,
        'rule_usage_statistics': {},
        'errors': []
    }
    
    # Статистика по default constraints
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(function_mapping_rule_id) as mapped,
            COUNT(CASE WHEN function_mapping_rule_id IS NULL AND definition IS NOT NULL THEN 1 END) as unmapped
        FROM mcl.postgres_default_constraints pdc
        JOIN mcl.postgres_tables pt ON pdc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
    ''', (task_id,))
    
    default_stats = cursor.fetchone()
    
    # Статистика по computed columns
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(computed_function_mapping_rule_id) as mapped,
            COUNT(CASE WHEN computed_function_mapping_rule_id IS NULL AND computed_definition IS NOT NULL THEN 1 END) as unmapped
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
    ''', (task_id,))
    
    computed_stats = cursor.fetchone()
    
    validation_results['total_objects'] = default_stats[0] + computed_stats[0]
    validation_results['mapped_objects'] = default_stats[1] + computed_stats[1]
    validation_results['unmapped_objects'] = default_stats[2] + computed_stats[2]
    
    # Статистика использования правил
    cursor.execute('''
        SELECT 
            fmr.source_function,
            fmr.target_function,
            COUNT(pdc.id) as default_constraints_count,
            COUNT(pc.id) as computed_columns_count,
            (COUNT(pdc.id) + COUNT(pc.id)) as total_usage
        FROM mcl.function_mapping_rules fmr
        LEFT JOIN mcl.postgres_default_constraints pdc ON fmr.id = pdc.function_mapping_rule_id
        LEFT JOIN mcl.postgres_columns pc ON fmr.id = pc.computed_function_mapping_rule_id
        GROUP BY fmr.id, fmr.source_function, fmr.target_function
        HAVING (COUNT(pdc.id) + COUNT(pc.id)) > 0
        ORDER BY total_usage DESC
    ''')
    
    rule_stats = cursor.fetchall()
    validation_results['rule_usage_statistics'] = rule_stats
    
    return validation_results
```

---

## 📊 ПРИМЕРЫ ЗАПРОСОВ С ВНЕШНИМИ КЛЮЧАМИ

### **🔍 Поиск всех объектов, использующих конкретное правило:**

```sql
-- Поиск всех объектов, использующих правило getdate → NOW
SELECT 
    'default_constraint' as object_type,
    pdc.constraint_name,
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
    pc.column_name as constraint_name,
    pt.object_name as table_name,
    fmr.source_function,
    fmr.target_function,
    pc.postgres_computed_definition
FROM mcl.postgres_columns pc
JOIN mcl.function_mapping_rules fmr ON pc.computed_function_mapping_rule_id = fmr.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
WHERE fmr.source_function = 'getdate';
```

### **📈 Статистика использования правил:**

```sql
-- Статистика использования правил маппинга
SELECT 
    fmr.source_function,
    fmr.target_function,
    fmr.complexity_level,
    COUNT(pdc.id) as default_constraints_count,
    COUNT(pc.id) as computed_columns_count,
    (COUNT(pdc.id) + COUNT(pc.id)) as total_usage
FROM mcl.function_mapping_rules fmr
LEFT JOIN mcl.postgres_default_constraints pdc ON fmr.id = pdc.function_mapping_rule_id
LEFT JOIN mcl.postgres_columns pc ON fmr.id = pc.computed_function_mapping_rule_id
WHERE fmr.is_active = TRUE
GROUP BY fmr.id, fmr.source_function, fmr.target_function, fmr.complexity_level
ORDER BY total_usage DESC;
```

### **🔄 Обновление правила для всех связанных объектов:**

```sql
-- Обновление целевой функции в правиле (автоматически влияет на все связанные объекты)
UPDATE mcl.function_mapping_rules
SET target_function = 'CURRENT_TIMESTAMP'
WHERE source_function = 'getdate';

-- Поиск всех объектов, которые будут затронуты
SELECT 
    'default_constraint' as object_type,
    pdc.constraint_name,
    pt.object_name,
    pdc.postgres_definition
FROM mcl.postgres_default_constraints pdc
JOIN mcl.postgres_tables pt ON pdc.table_id = pt.id
WHERE pdc.function_mapping_rule_id = (
    SELECT id FROM mcl.function_mapping_rules WHERE source_function = 'getdate'
);
```

### **📋 Отчет по статусу маппинга:**

```sql
-- Отчет по статусу маппинга функций для задачи
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
ORDER BY object_type, mapping_status;
```

---

## 🚀 ПЛАН ВНЕДРЕНИЯ УЛУЧШЕННОГО РЕШЕНИЯ

### **Этап 1: Создание структуры с внешними ключами**
1. Создание таблицы `function_mapping_rules`
2. Расширение `postgres_default_constraints` с внешним ключом
3. Расширение `postgres_columns` с внешним ключом
4. Создание индексов для производительности

### **Этап 2: Заполнение правил маппинга**
1. Вставка базовых правил маппинга
2. Тестирование правил на примерах
3. Добавление сложных правил

### **Этап 3: Применение маппинга с внешними ключами**
1. Анализ существующих определений
2. Связывание объектов с правилами через внешние ключи
3. Генерация PostgreSQL определений
4. Запись результатов в метаданные

### **Этап 4: Валидация и отчеты**
1. Проверка корректности связей
2. Генерация статистики использования правил
3. Выявление необработанных объектов
4. Корректировка правил при необходимости

---

## 🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

После внедрения улучшенного решения с внешними ключами:

1. **84 случая использования функций** будут связаны с правилами через внешние ключи
2. **Централизованное управление** правилами маппинга
3. **Автоматическое обновление** всех связанных объектов при изменении правил
4. **Полная трассируемость** применения правил
5. **Эффективные запросы** для анализа и отчетности
6. **Масштабируемость** для добавления новых правил

---

## 🏆 ЗАКЛЮЧЕНИЕ

**Внешние ключи на правила маппинга функций значительно улучшают архитектуру системы:**

- ✅ **Нормализация данных** - избежание дублирования правил
- ✅ **Управляемость** - централизованное управление правилами
- ✅ **Трассируемость** - четкая связь объектов с правилами
- ✅ **Производительность** - эффективные JOIN запросы
- ✅ **Гибкость** - легкость расширения и модификации

**Это решение обеспечивает профессиональный уровень архитектуры для системы миграции функций MS SQL Server в PostgreSQL.**