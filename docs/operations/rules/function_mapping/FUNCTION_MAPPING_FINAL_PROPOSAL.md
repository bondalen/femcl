# 🎯 ФИНАЛЬНОЕ ПРЕДЛОЖЕНИЕ ПО СИСТЕМЕ МАППИНГА ФУНКЦИЙ

## 🎯 НАЗНАЧЕНИЕ ДОКУМЕНТА

Данный документ содержит финальное предложение по системе маппинга функций MS SQL Server в PostgreSQL на основе анализа тестовой миграции и выявленных проблем.

---

## 📊 РЕЗУЛЬТАТЫ ТЕСТОВОЙ МИГРАЦИИ

### ✅ **УСПЕШНО ВЫПОЛНЕНО:**
- **Структура таблиц:** 166 таблиц созданы в схеме `ags`
- **Перенос данных:** 385,841 строк успешно перенесены
- **Независимые таблицы:** 69 таблиц перенесены на 100%
- **Таблицы с зависимостями:** 20 таблиц перенесены на 100%

### 🚨 **ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ:**

#### **1. Критическая проблема с маппингом функций:**
- **Таблиц с вычисляемыми полями:** 32
- **Представления созданы:** 2 из 32 (6.3%)
- **Ошибки в определениях:** 30 из 32 (93.7%)

#### **2. Типы ошибок в `postgres_computed_definition`:**
```
❌ Ошибка: столбец "cn_key" не существует
❌ Ошибка: ошибка синтаксиса (примерное положение: " ")
❌ Ошибка: ошибка синтаксиса (примерное положение: "[")
❌ Ошибка: ошибка синтаксиса (примерное положение: "CAST( AS )")
```

#### **3. Причины ошибок:**
- **Незамаппированные функции MS SQL:** `[column]`, `CAST( AS )`, `case when`
- **Некорректный синтаксис PostgreSQL:** использование MS SQL синтаксиса
- **Отсутствие валидации:** определения не проверяются на корректность

---

## 🚀 ФИНАЛЬНОЕ РЕШЕНИЕ: УНИВЕРСАЛЬНАЯ СИСТЕМА МАППИНГА

### **🏗️ АРХИТЕКТУРА РЕШЕНИЯ**

#### **1. Справочная таблица правил маппинга**

```sql
-- Создание справочной таблицы правил маппинга функций
CREATE TABLE mcl.function_mapping_rules (
    id SERIAL PRIMARY KEY,
    source_function VARCHAR NOT NULL,
    target_function VARCHAR NOT NULL,
    mapping_pattern TEXT NOT NULL, -- регулярное выражение для поиска
    replacement_pattern TEXT NOT NULL, -- строка замены
    mapping_type VARCHAR NOT NULL, -- direct, regex, custom
    complexity_level INTEGER DEFAULT 1, -- 1=simple, 2=complex, 3=custom
    applicable_objects TEXT[], -- 'default_constraint', 'computed_column', 'check_constraint', 'index'
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

#### **2. Расширение таблицы postgres_columns**

```sql
-- Расширение таблицы postgres_columns для отслеживания маппинга
ALTER TABLE mcl.postgres_columns
ADD COLUMN computed_function_mapping_rule_id INTEGER,
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

#### **3. Расширение таблицы postgres_default_constraints**

```sql
-- Расширение таблицы postgres_default_constraints для отслеживания маппинга
ALTER TABLE mcl.postgres_default_constraints
ADD COLUMN function_mapping_rule_id INTEGER,
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

---

## 🔧 АЛГОРИТМ МАППИНГА ФУНКЦИЙ

### **Этап 1: Создание базовых правил маппинга**

```python
def create_basic_function_mapping_rules() -> bool:
    """
    Создание базовых правил маппинга функций на основе выявленных проблем
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

### **Этап 2: Анализ и маппинг вычисляемых полей**

```python
def analyze_and_map_computed_columns(task_id: int) -> Dict:
    """
    Анализ вычисляемых полей и применение правил маппинга
    """
    results = {
        'total_computed_columns': 0,
        'mapped_columns': 0,
        'unmapped_columns': 0,
        'errors': []
    }
    
    # Получаем все вычисляемые колонки
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
            AND pc.is_computed = true
            AND pc.computed_definition IS NOT NULL
    ''', (task_id,))
    
    computed_columns = cursor.fetchall()
    results['total_computed_columns'] = len(computed_columns)
    
    for column_id, definition, table_name, column_name in computed_columns:
        try:
            # Применяем правила маппинга
            mapped_definition = apply_function_mapping_rules(definition)
            
            if mapped_definition != definition:
                # Найдены функции для маппинга
                rule_id = find_applied_rule_id(definition, mapped_definition)
                
                cursor.execute('''
                    UPDATE mcl.postgres_columns 
                    SET 
                        computed_function_mapping_rule_id = %s,
                        computed_mapping_status = 'mapped',
                        computed_mapping_complexity = (
                            SELECT CASE 
                                WHEN complexity_level = 1 THEN 'simple'
                                WHEN complexity_level = 2 THEN 'complex'
                                ELSE 'custom'
                            END
                            FROM mcl.function_mapping_rules 
                            WHERE id = %s
                        ),
                        postgres_computed_definition = %s
                    WHERE id = %s
                ''', (rule_id, rule_id, mapped_definition, column_id))
                
                results['mapped_columns'] += 1
            else:
                # Функции не найдены или уже корректны
                cursor.execute('''
                    UPDATE mcl.postgres_columns 
                    SET 
                        computed_mapping_status = 'no_functions_found',
                        postgres_computed_definition = %s
                    WHERE id = %s
                ''', (definition, column_id))
                
                results['unmapped_columns'] += 1
                
        except Exception as e:
            # Ошибка при маппинге
            cursor.execute('''
                UPDATE mcl.postgres_columns 
                SET 
                    computed_mapping_status = 'error',
                    computed_mapping_notes = %s
                WHERE id = %s
            ''', (str(e), column_id))
            
            results['errors'].append({
                'column_id': column_id,
                'table_name': table_name,
                'column_name': column_name,
                'error': str(e)
            })
    
    return results

def apply_function_mapping_rules(definition: str) -> str:
    """
    Применение правил маппинга функций к определению
    """
    cursor.execute('''
        SELECT 
            mapping_pattern,
            replacement_pattern,
            mapping_type
        FROM mcl.function_mapping_rules
        WHERE is_active = TRUE
            AND 'computed_column' = ANY(applicable_objects)
        ORDER BY complexity_level, source_function
    ''')
    
    rules = cursor.fetchall()
    result = definition
    
    for pattern, replacement, mapping_type in rules:
        if mapping_type == 'direct':
            # Простая замена
            result = result.replace(pattern.split('\\')[0], replacement.split('\\')[0])
        elif mapping_type == 'regex':
            # Замена по регулярному выражению
            import re
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result
```

### **Этап 3: Валидация и создание представлений**

```python
def validate_and_create_views(task_id: int) -> Dict:
    """
    Валидация маппированных определений и создание представлений
    """
    results = {
        'views_created': 0,
        'validation_errors': 0,
        'creation_errors': 0,
        'errors': []
    }
    
    # Получаем таблицы с вычисляемыми полями
    cursor.execute('''
        SELECT 
            pt.object_name as view_name,
            pt.base_table_name,
            COUNT(pc.id) as computed_columns_count
        FROM mcl.postgres_tables pt
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        LEFT JOIN mcl.postgres_columns pc ON pt.id = pc.table_id AND pc.is_computed = true
        WHERE mt.task_id = 2 
            AND pt.has_computed_columns = true
        GROUP BY pt.object_name, pt.base_table_name
        ORDER BY pt.object_name
    ''')
    
    tables_with_computed = cursor.fetchall()
    
    for view_name, base_table_name, computed_count in tables_with_computed:
        try:
            # Проверяем, что все вычисляемые поля замаппированы
            cursor.execute('''
                SELECT COUNT(*) as unmapped_count
                FROM mcl.postgres_columns pc
                JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
                JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
                WHERE mt.task_id = 2
                    AND pt.object_name = %s
                    AND pc.is_computed = true
                    AND pc.computed_mapping_status = 'error'
            ''', (view_name,))
            
            unmapped_count = cursor.fetchone()[0]
            
            if unmapped_count > 0:
                results['validation_errors'] += 1
                results['errors'].append({
                    'view_name': view_name,
                    'error': f'Есть {unmapped_count} необработанных вычисляемых полей'
                })
                continue
            
            # Создаем представление
            create_view_sql = build_view_definition(view_name, base_table_name)
            
            cursor.execute(create_view_sql)
            results['views_created'] += 1
            
        except Exception as e:
            results['creation_errors'] += 1
            results['errors'].append({
                'view_name': view_name,
                'error': str(e)
            })
    
    return results

def build_view_definition(view_name: str, base_table_name: str) -> str:
    """
    Построение определения представления
    """
    # Получаем все колонки для представления
    cursor.execute('''
        SELECT 
            pc.column_name,
            pc.is_computed,
            pc.postgres_computed_definition,
            pc.ordinal_position
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        WHERE pt.object_name = %s
        AND (pc.target_type = 'both' OR pc.target_type = 'view')
        ORDER BY pc.ordinal_position
    ''', (view_name,))
    
    columns = cursor.fetchall()
    
    select_parts = []
    for col_name, is_computed, computed_def, position in columns:
        if is_computed and computed_def:
            # Вычисляемая колонка
            select_parts.append(f'    {computed_def} AS "{col_name}"')
        else:
            # Обычная колонка
            select_parts.append(f'    "{col_name}"')
    
    select_clause = ',\\n'.join(select_parts)
    
    return f'''CREATE OR REPLACE VIEW ags."{view_name}" AS
SELECT
{select_clause}
FROM ags."{base_table_name}";'''
```

---

## 📊 ПРИМЕРЫ ЗАПРОСОВ ДЛЯ АНАЛИЗА МАППИНГА

### **🔍 Анализ статуса маппинга вычисляемых полей:**

```sql
-- Анализ статуса маппинга вычисляемых полей
SELECT 
    computed_mapping_status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM mcl.postgres_columns pc
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
WHERE mt.task_id = 2
    AND pc.is_computed = true
GROUP BY computed_mapping_status
ORDER BY count DESC;
```

### **📈 Статистика использования правил маппинга:**

```sql
-- Статистика использования правил маппинга
SELECT 
    fmr.source_function,
    fmr.target_function,
    fmr.complexity_level,
    COUNT(pc.id) as computed_columns_count,
    COUNT(pdc.id) as default_constraints_count,
    (COUNT(pc.id) + COUNT(pdc.id)) as total_usage
FROM mcl.function_mapping_rules fmr
LEFT JOIN mcl.postgres_columns pc ON fmr.id = pc.computed_function_mapping_rule_id
LEFT JOIN mcl.postgres_default_constraints pdc ON fmr.id = pdc.function_mapping_rule_id
WHERE fmr.is_active = TRUE
GROUP BY fmr.id, fmr.source_function, fmr.target_function, fmr.complexity_level
ORDER BY total_usage DESC;
```

### **🚨 Поиск проблемных вычисляемых полей:**

```sql
-- Поиск вычисляемых полей с ошибками маппинга
SELECT 
    pt.object_name as table_name,
    pc.column_name,
    pc.computed_definition,
    pc.computed_mapping_status,
    pc.computed_mapping_notes
FROM mcl.postgres_columns pc
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
WHERE mt.task_id = 2
    AND pc.is_computed = true
    AND pc.computed_mapping_status = 'error'
ORDER BY pt.object_name, pc.column_name;
```

---

## 🚀 ПЛАН ВНЕДРЕНИЯ

### **Этап 1: Создание структуры (1-2 дня)**
1. Создание таблицы `function_mapping_rules`
2. Расширение `postgres_columns` с внешним ключом
3. Расширение `postgres_default_constraints` с внешним ключом
4. Создание индексов

### **Этап 2: Заполнение правил маппинга (1 день)**
1. Вставка базовых правил маппинга
2. Тестирование правил на примерах
3. Добавление сложных правил

### **Этап 3: Применение маппинга (2-3 дня)**
1. Анализ всех вычисляемых полей
2. Применение правил маппинга
3. Валидация результатов
4. Исправление ошибок

### **Этап 4: Создание представлений (1 день)**
1. Построение определений представлений
2. Создание представлений
3. Валидация представлений

### **Этап 5: Тестирование (1 день)**
1. Проверка корректности маппинга
2. Тестирование на реальных данных
3. Корректировка правил при необходимости

---

## 🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

После внедрения системы маппинга функций:

1. **32 таблицы с вычисляемыми полями** будут обработаны
2. **32 представления** будут созданы успешно
3. **100% покрытие** маппинга функций
4. **Централизованное управление** правилами маппинга
5. **Возможность расширения** для новых типов функций
6. **Полная трассируемость** применения маппингов

---

## 🏆 ЗАКЛЮЧЕНИЕ

**Система маппинга функций решает ключевую проблему миграции:**

- ✅ **Устранение ошибок** в определениях вычисляемых полей
- ✅ **Автоматическое создание** корректных представлений
- ✅ **Централизованное управление** правилами маппинга
- ✅ **Масштабируемость** для новых типов функций
- ✅ **Полная трассируемость** процесса маппинга

**Это обеспечит успешное завершение миграции с созданием всех необходимых представлений для вычисляемых полей.**
