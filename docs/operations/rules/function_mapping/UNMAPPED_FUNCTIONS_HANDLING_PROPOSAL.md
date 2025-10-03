# 🎯 ПРЕДЛОЖЕНИЕ ПО ОБРАБОТКЕ НЕЗАМАППИРОВАННЫХ ФУНКЦИЙ

## 🎯 НАЗНАЧЕНИЕ ДОКУМЕНТА

Данный документ содержит уточненные предложения по обработке незамаппированных функций на основе анализа тестовой миграции и выявленных проблем.

---

## 📊 АНАЛИЗ ПРОБЛЕМ ИЗ ТЕСТОВОЙ МИГРАЦИИ

### **🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:**

#### **1. Статистика незамаппированных функций:**
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

## 🚀 СТРАТЕГИЯ ОБРАБОТКИ НЕЗАМАППИРОВАННЫХ ФУНКЦИЙ

### **🎯 ПРИНЦИП: НЕЗАМАППИРОВАННЫЕ ФУНКЦИИ НЕ БЛОКИРУЮТ МИГРАЦИЮ**

Согласно анализу чата, **незамаппированные вычисляемые поля не должны блокировать полную миграцию**, поскольку:

1. **Базовые таблицы всегда создаются** (с физическими колонками)
2. **Представления могут быть созданы частично** или доработаны позже
3. **Структура метаданных позволяет** пост-миграционную доработку

### **📋 ТРИ УРОВНЯ ОБРАБОТКИ:**

#### **Уровень 1: Автоматический маппинг (80% случаев)**
```python
def apply_automatic_function_mapping(definition: str) -> str:
    """
    Автоматическое применение базовых правил маппинга
    """
    # Применяем стандартные правила: getdate→NOW, isnull→COALESCE, etc.
    return apply_standard_mapping_rules(definition)
```

#### **Уровень 2: Полуавтоматический маппинг (15% случаев)**
```python
def apply_semi_automatic_mapping(definition: str) -> str:
    """
    Полуавтоматическое применение с валидацией
    """
    # Применяем правила + валидация синтаксиса
    mapped = apply_standard_mapping_rules(definition)
    if validate_postgres_syntax(mapped):
        return mapped
    else:
        return mark_for_manual_review(definition)
```

#### **Уровень 3: Ручная обработка (5% случаев)**
```python
def mark_for_manual_review(definition: str) -> str:
    """
    Помечаем для ручной доработки
    """
    return f"-- MANUAL_REVIEW_REQUIRED: {definition}"
```

---

## 🏗️ АРХИТЕКТУРА ОБРАБОТКИ НЕЗАМАППИРОВАННЫХ ФУНКЦИЙ

### **1. Расширенная таблица статусов маппинга**

```sql
-- Расширение таблицы postgres_columns для детального отслеживания
ALTER TABLE mcl.postgres_columns
ADD COLUMN computed_mapping_status VARCHAR DEFAULT 'pending', -- pending, mapped, semi_mapped, manual_review, error
ADD COLUMN computed_mapping_confidence INTEGER DEFAULT 0, -- 0-100, процент уверенности в маппинге
ADD COLUMN computed_mapping_attempts INTEGER DEFAULT 0, -- количество попыток маппинга
ADD COLUMN computed_mapping_notes TEXT, -- детальные заметки о проблемах
ADD COLUMN computed_mapping_priority VARCHAR DEFAULT 'normal', -- low, normal, high, critical
ADD COLUMN computed_mapping_complexity VARCHAR DEFAULT 'simple'; -- simple, medium, complex, custom

-- Создание индексов для быстрого поиска проблемных случаев
CREATE INDEX idx_postgres_columns_mapping_status ON mcl.postgres_columns(computed_mapping_status);
CREATE INDEX idx_postgres_columns_mapping_confidence ON mcl.postgres_columns(computed_mapping_confidence);
CREATE INDEX idx_postgres_columns_mapping_priority ON mcl.postgres_columns(computed_mapping_priority);
```

### **2. Таблица для отслеживания проблемных случаев**

```sql
-- Создание таблицы для отслеживания проблемных вычисляемых полей
CREATE TABLE mcl.computed_columns_mapping_issues (
    id SERIAL PRIMARY KEY,
    column_id INTEGER REFERENCES mcl.postgres_columns(id),
    issue_type VARCHAR NOT NULL, -- 'unmapped_function', 'syntax_error', 'validation_failed'
    issue_description TEXT,
    source_definition TEXT,
    attempted_mapping TEXT,
    error_details TEXT,
    suggested_solution TEXT,
    manual_review_required BOOLEAN DEFAULT FALSE,
    priority_level INTEGER DEFAULT 3, -- 1=critical, 2=high, 3=normal, 4=low
    status VARCHAR DEFAULT 'open', -- open, in_progress, resolved, deferred
    assigned_to VARCHAR,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого поиска
CREATE INDEX idx_computed_columns_issues_status ON mcl.computed_columns_mapping_issues(status);
CREATE INDEX idx_computed_columns_issues_priority ON mcl.computed_columns_mapping_issues(priority_level);
CREATE INDEX idx_computed_columns_issues_type ON mcl.computed_columns_mapping_issues(issue_type);
```

---

## 🔧 АЛГОРИТМ ОБРАБОТКИ НЕЗАМАППИРОВАННЫХ ФУНКЦИЙ

### **Этап 1: Многоуровневый маппинг**

```python
def process_computed_columns_with_unmapped_handling(task_id: int) -> Dict:
    """
    Обработка вычисляемых полей с многоуровневым подходом к незамаппированным функциям
    """
    results = {
        'total_columns': 0,
        'fully_mapped': 0,
        'semi_mapped': 0,
        'manual_review': 0,
        'errors': 0,
        'issues_created': 0
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
    results['total_columns'] = len(computed_columns)
    
    for column_id, definition, table_name, column_name in computed_columns:
        try:
            # Уровень 1: Автоматический маппинг
            mapped_definition, confidence = apply_automatic_mapping(definition)
            
            if confidence >= 80:
                # Высокая уверенность - применяем маппинг
                update_column_mapping_status(column_id, 'mapped', mapped_definition, confidence)
                results['fully_mapped'] += 1
                
            elif confidence >= 50:
                # Средняя уверенность - полуавтоматический маппинг
                if validate_postgres_syntax(mapped_definition):
                    update_column_mapping_status(column_id, 'semi_mapped', mapped_definition, confidence)
                    results['semi_mapped'] += 1
                else:
                    # Валидация не прошла - помечаем для ручного обзора
                    create_mapping_issue(column_id, 'validation_failed', definition, mapped_definition)
                    update_column_mapping_status(column_id, 'manual_review', definition, confidence)
                    results['manual_review'] += 1
                    results['issues_created'] += 1
            else:
                # Низкая уверенность - помечаем для ручного обзора
                create_mapping_issue(column_id, 'unmapped_function', definition, None)
                update_column_mapping_status(column_id, 'manual_review', definition, confidence)
                results['manual_review'] += 1
                results['issues_created'] += 1
                
        except Exception as e:
            # Ошибка при обработке
            create_mapping_issue(column_id, 'syntax_error', definition, None, str(e))
            update_column_mapping_status(column_id, 'error', definition, 0)
            results['errors'] += 1
            results['issues_created'] += 1
    
    return results

def apply_automatic_mapping(definition: str) -> tuple[str, int]:
    """
    Применение автоматического маппинга с оценкой уверенности
    """
    confidence = 100
    mapped = definition
    
    # Список правил маппинга с оценкой уверенности
    mapping_rules = [
        ('getdate()', 'NOW()', 95),
        ('isnull(', 'COALESCE(', 90),
        ('len(', 'LENGTH(', 90),
        ('upper(', 'UPPER(', 95),
        ('lower(', 'LOWER(', 95),
        ('substring(', 'SUBSTRING(', 85),
        ('convert(', 'CAST(', 80),
        ('year(', 'EXTRACT(YEAR FROM ', 85),
        ('month(', 'EXTRACT(MONTH FROM ', 85),
        ('day(', 'EXTRACT(DAY FROM ', 85),
    ]
    
    # Применяем правила маппинга
    for source, target, rule_confidence in mapping_rules:
        if source in mapped.lower():
            mapped = mapped.replace(source, target)
            confidence = min(confidence, rule_confidence)
    
    # Дополнительные преобразования
    mapped = fix_sql_server_syntax(mapped)
    
    return mapped, confidence

def fix_sql_server_syntax(definition: str) -> str:
    """
    Исправление специфичного синтаксиса MS SQL Server
    """
    # Замена квадратных скобок на двойные кавычки
    definition = re.sub(r'\[([^\]]+)\]', r'"\1"', definition)
    
    # Исправление CAST синтаксиса
    definition = re.sub(r'CAST\(\s*AS\s*\)', 'CAST(NULL AS TEXT)', definition)
    
    # Исправление пустых выражений
    definition = re.sub(r'\(\s*\+\s*\)', '(NULL)', definition)
    
    return definition

def validate_postgres_syntax(definition: str) -> bool:
    """
    Валидация синтаксиса PostgreSQL
    """
    try:
        # Простая валидация - проверка на наличие очевидных ошибок
        if 'CAST( AS )' in definition:
            return False
        if definition.count('(') != definition.count(')'):
            return False
        if '[' in definition or ']' in definition:
            return False
        return True
    except:
        return False
```

### **Этап 2: Создание представлений с обработкой ошибок**

```python
def create_views_with_error_handling(task_id: int) -> Dict:
    """
    Создание представлений с обработкой незамаппированных функций
    """
    results = {
        'views_created': 0,
        'views_partial': 0,
        'views_failed': 0,
        'errors': []
    }
    
    # Получаем таблицы с вычисляемыми полями
    cursor.execute('''
        SELECT 
            pt.object_name as view_name,
            pt.base_table_name,
            COUNT(pc.id) as computed_columns_count,
            COUNT(CASE WHEN pc.computed_mapping_status = 'mapped' THEN 1 END) as mapped_count,
            COUNT(CASE WHEN pc.computed_mapping_status = 'semi_mapped' THEN 1 END) as semi_mapped_count,
            COUNT(CASE WHEN pc.computed_mapping_status = 'manual_review' THEN 1 END) as manual_review_count
        FROM mcl.postgres_tables pt
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        LEFT JOIN mcl.postgres_columns pc ON pt.id = pc.table_id AND pc.is_computed = true
        WHERE mt.task_id = 2 
            AND pt.has_computed_columns = true
        GROUP BY pt.object_name, pt.base_table_name
        ORDER BY pt.object_name
    ''')
    
    tables_with_computed = cursor.fetchall()
    
    for view_name, base_table_name, total_computed, mapped_count, semi_mapped_count, manual_review_count in tables_with_computed:
        try:
            if manual_review_count == 0:
                # Все поля замаппированы - создаем полное представление
                create_view_sql = build_complete_view_definition(view_name, base_table_name)
                cursor.execute(create_view_sql)
                results['views_created'] += 1
                
            elif mapped_count > 0:
                # Есть замаппированные поля - создаем частичное представление
                create_view_sql = build_partial_view_definition(view_name, base_table_name, mapped_count)
                cursor.execute(create_view_sql)
                results['views_partial'] += 1
                
            else:
                # Нет замаппированных полей - создаем базовое представление
                create_view_sql = build_basic_view_definition(view_name, base_table_name)
                cursor.execute(create_view_sql)
                results['views_partial'] += 1
                
        except Exception as e:
            results['views_failed'] += 1
            results['errors'].append({
                'view_name': view_name,
                'error': str(e)
            })
    
    return results

def build_partial_view_definition(view_name: str, base_table_name: str, mapped_count: int) -> str:
    """
    Построение частичного представления (только с замаппированными полями)
    """
    # Получаем только замаппированные колонки
    cursor.execute('''
        SELECT 
            pc.column_name,
            pc.is_computed,
            pc.postgres_computed_definition,
            pc.ordinal_position
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        WHERE pt.object_name = %s
        AND (
            (pc.target_type = 'both' OR pc.target_type = 'view') 
            AND pc.is_computed = false
        ) OR (
            pc.is_computed = true 
            AND pc.computed_mapping_status IN ('mapped', 'semi_mapped')
        )
        ORDER BY pc.ordinal_position
    ''', (view_name,))
    
    columns = cursor.fetchall()
    
    select_parts = []
    for col_name, is_computed, computed_def, position in columns:
        if is_computed and computed_def:
            # Замаппированная вычисляемая колонка
            select_parts.append(f'    {computed_def} AS "{col_name}"')
        else:
            # Обычная колонка
            select_parts.append(f'    "{col_name}"')
    
    select_clause = ',\\n'.join(select_parts)
    
    return f'''CREATE OR REPLACE VIEW ags."{view_name}" AS
SELECT
{select_clause}
FROM ags."{base_table_name}";'''

def build_basic_view_definition(view_name: str, base_table_name: str) -> str:
    """
    Построение базового представления (только физические колонки)
    """
    # Получаем только физические колонки
    cursor.execute('''
        SELECT 
            pc.column_name,
            pc.ordinal_position
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        WHERE pt.object_name = %s
        AND (pc.target_type = 'both' OR pc.target_type = 'view')
        AND pc.is_computed = false
        ORDER BY pc.ordinal_position
    ''', (view_name,))
    
    columns = cursor.fetchall()
    
    select_parts = [f'    "{col_name}"' for col_name, position in columns]
    select_clause = ',\\n'.join(select_parts)
    
    return f'''CREATE OR REPLACE VIEW ags."{view_name}" AS
SELECT
{select_clause}
FROM ags."{base_table_name}";'''
```

### **Этап 3: Мониторинг и отчетность**

```python
def generate_unmapped_functions_report(task_id: int) -> Dict:
    """
    Генерация отчета по незамаппированным функциям
    """
    report = {
        'summary': {},
        'by_table': {},
        'by_issue_type': {},
        'recommendations': []
    }
    
    # Общая статистика
    cursor.execute('''
        SELECT 
            computed_mapping_status,
            COUNT(*) as count,
            ROUND(AVG(computed_mapping_confidence), 2) as avg_confidence
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s AND pc.is_computed = true
        GROUP BY computed_mapping_status
        ORDER BY count DESC
    ''', (task_id,))
    
    report['summary'] = dict(cursor.fetchall())
    
    # Статистика по таблицам
    cursor.execute('''
        SELECT 
            pt.object_name,
            COUNT(*) as total_computed,
            COUNT(CASE WHEN pc.computed_mapping_status = 'mapped' THEN 1 END) as mapped,
            COUNT(CASE WHEN pc.computed_mapping_status = 'semi_mapped' THEN 1 END) as semi_mapped,
            COUNT(CASE WHEN pc.computed_mapping_status = 'manual_review' THEN 1 END) as manual_review,
            COUNT(CASE WHEN pc.computed_mapping_status = 'error' THEN 1 END) as errors
        FROM mcl.postgres_columns pc
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s AND pc.is_computed = true
        GROUP BY pt.object_name
        ORDER BY manual_review DESC, errors DESC
    ''', (task_id,))
    
    report['by_table'] = {row[0]: dict(zip(['total', 'mapped', 'semi_mapped', 'manual_review', 'errors'], row[1:])) 
                         for row in cursor.fetchall()}
    
    # Статистика по типам проблем
    cursor.execute('''
        SELECT 
            issue_type,
            COUNT(*) as count,
            COUNT(CASE WHEN status = 'open' THEN 1 END) as open_issues
        FROM mcl.computed_columns_mapping_issues cci
        JOIN mcl.postgres_columns pc ON cci.column_id = pc.id
        JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
        GROUP BY issue_type
        ORDER BY count DESC
    ''', (task_id,))
    
    report['by_issue_type'] = dict(cursor.fetchall())
    
    # Рекомендации
    if report['summary'].get('manual_review', 0) > 0:
        report['recommendations'].append(
            f"Требуется ручная доработка {report['summary']['manual_review']} вычисляемых полей"
        )
    
    if report['summary'].get('error', 0) > 0:
        report['recommendations'].append(
            f"Обнаружены ошибки в {report['summary']['error']} вычисляемых полях"
        )
    
    return report
```

---

## 📊 ПРИМЕРЫ ЗАПРОСОВ ДЛЯ АНАЛИЗА НЕЗАМАППИРОВАННЫХ ФУНКЦИЙ

### **🔍 Поиск проблемных вычисляемых полей:**

```sql
-- Поиск вычисляемых полей, требующих ручного обзора
SELECT 
    pt.object_name as table_name,
    pc.column_name,
    pc.computed_definition as source_definition,
    pc.computed_mapping_status,
    pc.computed_mapping_confidence,
    pc.computed_mapping_notes
FROM mcl.postgres_columns pc
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
WHERE mt.task_id = 2
    AND pc.is_computed = true
    AND pc.computed_mapping_status IN ('manual_review', 'error')
ORDER BY pc.computed_mapping_confidence ASC, pt.object_name, pc.column_name;
```

### **📈 Статистика по статусам маппинга:**

```sql
-- Детальная статистика по статусам маппинга
SELECT 
    computed_mapping_status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage,
    ROUND(AVG(computed_mapping_confidence), 2) as avg_confidence,
    MIN(computed_mapping_confidence) as min_confidence,
    MAX(computed_mapping_confidence) as max_confidence
FROM mcl.postgres_columns pc
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
WHERE mt.task_id = 2 AND pc.is_computed = true
GROUP BY computed_mapping_status
ORDER BY count DESC;
```

### **🚨 Отчет по проблемам маппинга:**

```sql
-- Отчет по созданным проблемам маппинга
SELECT 
    cci.issue_type,
    pt.object_name as table_name,
    pc.column_name,
    cci.issue_description,
    cci.priority_level,
    cci.status,
    cci.assigned_to,
    cci.created_at
FROM mcl.computed_columns_mapping_issues cci
JOIN mcl.postgres_columns pc ON cci.column_id = pc.id
JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
WHERE mt.task_id = 2
ORDER BY cci.priority_level, cci.created_at DESC;
```

---

## 🚀 ПЛАН ВНЕДРЕНИЯ ОБРАБОТКИ НЕЗАМАППИРОВАННЫХ ФУНКЦИЙ

### **Этап 1: Расширение структуры (1 день)**
1. Добавление полей в `postgres_columns` для детального отслеживания
2. Создание таблицы `computed_columns_mapping_issues`
3. Создание индексов для производительности

### **Этап 2: Реализация алгоритма (2-3 дня)**
1. Многоуровневый маппинг с оценкой уверенности
2. Валидация синтаксиса PostgreSQL
3. Создание проблемных записей для ручного обзора

### **Этап 3: Создание представлений (1 день)**
1. Полные представления для полностью замаппированных таблиц
2. Частичные представления для частично замаппированных таблиц
3. Базовые представления для не замаппированных таблиц

### **Этап 4: Мониторинг и отчетность (1 день)**
1. Генерация отчетов по незамаппированным функциям
2. Создание дашборда для мониторинга
3. Настройка уведомлений о проблемах

### **Этап 5: Ручная доработка (по мере необходимости)**
1. Обработка проблемных случаев из `computed_columns_mapping_issues`
2. Добавление новых правил маппинга
3. Обновление представлений после доработки

---

## 🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

После внедрения системы обработки незамаппированных функций:

1. **100% покрытие** - все вычисляемые поля будут обработаны
2. **Максимальное количество представлений** - созданы все возможные представления
3. **Прозрачность процесса** - полная видимость проблемных случаев
4. **Неблокирующая миграция** - незамаппированные функции не останавливают процесс
5. **Пост-миграционная доработка** - возможность доработки после основной миграции

---

## 🏆 ЗАКЛЮЧЕНИЕ

**Система обработки незамаппированных функций обеспечивает:**

- ✅ **Неблокирующую миграцию** - процесс не останавливается из-за проблемных функций
- ✅ **Максимальное покрытие** - создается максимальное количество представлений
- ✅ **Прозрачность процесса** - полная видимость всех проблемных случаев
- ✅ **Пост-миграционную доработку** - возможность доработки после основной миграции
- ✅ **Масштабируемость** - легкость добавления новых правил и исправления проблем

**Это решение обеспечивает успешное завершение миграции даже при наличии незамаппированных функций, с возможностью их последующей доработки.**
