# 🎯 УТОЧНЕННОЕ ПРЕДЛОЖЕНИЕ ПО ВИДОВОЙ МИГРАЦИИ

## 🚨 ВЫЯВЛЕННАЯ ПРОБЛЕМА

### **Критический недостаток Подхода 1:**
- Распределение полей между базовыми таблицами и представлениями происходит **на этапе выполнения миграции**
- В метаданных схемы `mcl` это распределение **НЕ отражено заранее**
- Риск ошибок при определении, какие поля физические, а какие вычисляемые

## 🎯 УЛУЧШЕННЫЕ ПОДХОДЫ

### **ПОДХОД 1-УЛУЧШЕННЫЙ: РАСШИРЕНИЕ С ПРЕДВАРИТЕЛЬНЫМ РАСПРЕДЕЛЕНИЕМ**

#### Структура:
```sql
-- Расширенная таблица postgres_tables
CREATE TABLE mcl.postgres_tables (
    id INTEGER PRIMARY KEY,
    source_table_id INTEGER REFERENCES mcl.mssql_tables(id),
    object_name VARCHAR,           -- Исходное имя
    base_table_name VARCHAR,       -- Имя базовой таблицы (определено заранее)
    view_name VARCHAR,             -- Имя представления (определено заранее)
    has_computed_columns BOOLEAN,  -- Определено заранее на этапе анализа
    base_table_created BOOLEAN DEFAULT FALSE,
    view_created BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Расширенная таблица postgres_columns с ПРЕДВАРИТЕЛЬНЫМ распределением
CREATE TABLE mcl.postgres_columns (
    id INTEGER PRIMARY KEY,
    table_id INTEGER REFERENCES mcl.postgres_tables(id),
    source_column_id INTEGER REFERENCES mcl.mssql_columns(id),
    column_name VARCHAR,
    ordinal_position INTEGER,
    is_computed BOOLEAN,           -- Определено заранее
    target_type VARCHAR,           -- 'base_table' или 'view' - ОПРЕДЕЛЕНО ЗАРАНЕЕ
    base_table_position INTEGER,   -- Позиция в базовой таблице
    view_position INTEGER,         -- Позиция в представлении
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### Алгоритм предварительного распределения:
```python
def analyze_and_distribute_columns(task_id: int) -> bool:
    """
    Анализ и предварительное распределение колонок на этапе формирования метаданных
    """
    # 1. Получаем все таблицы задачи
    cursor.execute('''
        SELECT pt.id, pt.source_table_id, mt.object_name
        FROM mcl.postgres_tables pt
        JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
        WHERE mt.task_id = %s
    ''', (task_id,))
    
    tables = cursor.fetchall()
    
    for table_id, source_table_id, table_name in tables:
        # 2. Анализируем колонки таблицы
        cursor.execute('''
            SELECT 
                pc.id,
                pc.source_column_id,
                mc.column_name,
                mc.ordinal_position,
                mc.is_computed,
                mc.is_identity,
                mc.is_nullable
            FROM mcl.postgres_columns pc
            JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
            WHERE pc.table_id = %s
            ORDER BY mc.ordinal_position
        ''', (table_id,))
        
        columns = cursor.fetchall()
        
        # 3. Определяем, есть ли вычисляемые поля
        has_computed = any(col[4] for col in columns)  # is_computed
        
        # 4. Генерируем имена объектов
        if has_computed:
            base_table_name = f"{table_name}_bt"
            view_name = table_name
        else:
            base_table_name = table_name
            view_name = table_name
        
        # 5. Обновляем информацию о таблице
        cursor.execute('''
            UPDATE mcl.postgres_tables 
            SET 
                base_table_name = %s,
                view_name = %s,
                has_computed_columns = %s
            WHERE id = %s
        ''', (base_table_name, view_name, has_computed, table_id))
        
        # 6. Распределяем колонки
        base_position = 1
        view_position = 1
        
        for col_id, source_col_id, col_name, ordinal_pos, is_computed, is_identity, is_nullable in columns:
            if has_computed:
                if is_computed or is_identity:
                    # Вычисляемая колонка - только в представлении
                    target_type = 'view'
                    base_position = None
                else:
                    # Физическая колонка - в базовой таблице и представлении
                    target_type = 'both'
            else:
                # Обычная таблица - все колонки в обоих местах
                target_type = 'both'
                base_position = view_position
            
            # 7. Обновляем информацию о колонке
            cursor.execute('''
                UPDATE mcl.postgres_columns 
                SET 
                    is_computed = %s,
                    target_type = %s,
                    base_table_position = %s,
                    view_position = %s
                WHERE id = %s
            ''', (is_computed, target_type, base_position, view_position, col_id))
            
            # 8. Обновляем счетчики позиций
            if target_type in ['both', 'base_table']:
                base_position += 1
            if target_type in ['both', 'view']:
                view_position += 1
    
    conn.commit()
    return True
```

---

### **ПОДХОД 2-УЛУЧШЕННЫЙ: ИЕРАРХИЧЕСКАЯ СТРУКТУРА С ДЕТАЛЬНЫМ РАСПРЕДЕЛЕНИЕМ**

#### Структура:
```sql
-- Родительская таблица объектов
CREATE TABLE mcl.postgres_objects (
    id INTEGER PRIMARY KEY,
    source_table_id INTEGER REFERENCES mcl.mssql_tables(id),
    object_name VARCHAR,
    object_type VARCHAR,           -- 'table', 'table_view', 'view'
    has_computed_columns BOOLEAN,
    analysis_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Таблица целевых таблиц и представлений
CREATE TABLE mcl.postgres_table_views (
    id INTEGER PRIMARY KEY,
    parent_object_id INTEGER REFERENCES mcl.postgres_objects(id),
    base_table_name VARCHAR,
    view_name VARCHAR,
    has_computed_columns BOOLEAN,
    distribution_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Таблица базовых таблиц
CREATE TABLE mcl.postgres_base_tables (
    id INTEGER PRIMARY KEY,
    table_view_id INTEGER REFERENCES mcl.postgres_table_views(id),
    object_name VARCHAR,
    schema_name VARCHAR DEFAULT 'public',
    column_count INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Таблица представлений
CREATE TABLE mcl.postgres_views (
    id INTEGER PRIMARY KEY,
    table_view_id INTEGER REFERENCES mcl.postgres_table_views(id),
    base_table_id INTEGER REFERENCES mcl.postgres_base_tables(id),
    object_name VARCHAR,
    schema_name VARCHAR DEFAULT 'public',
    view_definition TEXT,
    column_count INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- ДЕТАЛЬНАЯ таблица колонок с полным распределением
CREATE TABLE mcl.postgres_columns (
    id INTEGER PRIMARY KEY,
    table_view_id INTEGER REFERENCES mcl.postgres_table_views(id),
    source_column_id INTEGER REFERENCES mcl.mssql_columns(id),
    column_name VARCHAR,
    source_ordinal_position INTEGER,
    is_computed BOOLEAN,
    
    -- Распределение по объектам
    in_base_table BOOLEAN,
    in_view BOOLEAN,
    
    -- Позиции в каждом объекте
    base_table_position INTEGER,
    view_position INTEGER,
    
    -- Дополнительная информация
    column_definition_base TEXT,    -- DDL для базовой таблицы
    column_definition_view TEXT,    -- DDL для представления
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### Алгоритм детального распределения:
```python
def detailed_column_distribution(task_id: int) -> bool:
    """
    Детальное распределение колонок на этапе формирования метаданных
    """
    # 1. Создаем записи в postgres_objects
    cursor.execute('''
        INSERT INTO mcl.postgres_objects (source_table_id, object_name, object_type, has_computed_columns)
        SELECT 
            mt.id,
            mt.object_name,
            CASE 
                WHEN EXISTS(SELECT 1 FROM mcl.mssql_columns mc WHERE mc.table_id = mt.id AND mc.is_computed = true)
                THEN 'table_view'
                ELSE 'table'
            END as object_type,
            EXISTS(SELECT 1 FROM mcl.mssql_columns mc WHERE mc.table_id = mt.id AND mc.is_computed = true) as has_computed
        FROM mcl.mssql_tables mt
        WHERE mt.task_id = %s
    ''', (task_id,))
    
    # 2. Создаем записи в postgres_table_views
    cursor.execute('''
        INSERT INTO mcl.postgres_table_views (parent_object_id, base_table_name, view_name, has_computed_columns)
        SELECT 
            po.id,
            CASE 
                WHEN po.has_computed_columns THEN po.object_name || '_bt'
                ELSE po.object_name
            END as base_table_name,
            po.object_name as view_name,
            po.has_computed_columns
        FROM mcl.postgres_objects po
    ''')
    
    # 3. Создаем записи в postgres_base_tables и postgres_views
    cursor.execute('''
        INSERT INTO mcl.postgres_base_tables (table_view_id, object_name)
        SELECT 
            ptv.id,
            ptv.base_table_name
        FROM mcl.postgres_table_views ptv
        WHERE ptv.has_computed_columns = true
    ''')
    
    cursor.execute('''
        INSERT INTO mcl.postgres_views (table_view_id, base_table_id, object_name)
        SELECT 
            ptv.id,
            pbt.id,
            ptv.view_name
        FROM mcl.postgres_table_views ptv
        LEFT JOIN mcl.postgres_base_tables pbt ON ptv.id = pbt.table_view_id
        WHERE ptv.has_computed_columns = true
    ''')
    
    # 4. Детальное распределение колонок
    cursor.execute('''
        SELECT 
            ptv.id as table_view_id,
            ptv.has_computed_columns,
            mc.id as source_column_id,
            mc.column_name,
            mc.ordinal_position,
            mc.is_computed,
            mc.is_identity,
            mc.is_nullable,
            mc.default_value
        FROM mcl.postgres_table_views ptv
        JOIN mcl.postgres_objects po ON ptv.parent_object_id = po.id
        JOIN mcl.mssql_tables mt ON po.source_table_id = mt.id
        JOIN mcl.mssql_columns mc ON mt.id = mc.table_id
        WHERE mt.task_id = %s
        ORDER BY ptv.id, mc.ordinal_position
    ''', (task_id,))
    
    columns = cursor.fetchall()
    
    base_positions = {}
    view_positions = {}
    
    for (table_view_id, has_computed, source_col_id, col_name, ordinal_pos, 
         is_computed, is_identity, is_nullable, default_value) in columns:
        
        # Инициализируем счетчики позиций
        if table_view_id not in base_positions:
            base_positions[table_view_id] = 1
        if table_view_id not in view_positions:
            view_positions[table_view_id] = 1
        
        # Определяем распределение колонки
        if has_computed:
            if is_computed or is_identity:
                # Вычисляемая колонка - только в представлении
                in_base_table = False
                in_view = True
                base_position = None
                view_position = view_positions[table_view_id]
            else:
                # Физическая колонка - в обоих объектах
                in_base_table = True
                in_view = True
                base_position = base_positions[table_view_id]
                view_position = view_positions[table_view_id]
        else:
            # Обычная таблица - все колонки в обоих местах
            in_base_table = True
            in_view = True
            base_position = base_positions[table_view_id]
            view_position = view_positions[table_view_id]
        
        # Генерируем DDL для колонки
        column_def_base = generate_column_ddl(col_name, ordinal_pos, is_nullable, default_value, False)
        column_def_view = generate_column_ddl(col_name, ordinal_pos, is_nullable, default_value, is_computed)
        
        # 5. Создаем запись о колонке
        cursor.execute('''
            INSERT INTO mcl.postgres_columns (
                table_view_id, source_column_id, column_name, source_ordinal_position,
                is_computed, in_base_table, in_view, base_table_position, view_position,
                column_definition_base, column_definition_view
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        ''', (table_view_id, source_col_id, col_name, ordinal_pos, is_computed,
              in_base_table, in_view, base_position, view_position,
              column_def_base, column_def_view))
        
        # Обновляем счетчики позиций
        if in_base_table:
            base_positions[table_view_id] += 1
        if in_view:
            view_positions[table_view_id] += 1
    
    # 6. Обновляем счетчики колонок
    cursor.execute('''
        UPDATE mcl.postgres_base_tables 
        SET column_count = (
            SELECT COUNT(*) 
            FROM mcl.postgres_columns 
            WHERE table_view_id = postgres_base_tables.table_view_id 
                AND in_base_table = true
        )
    ''')
    
    cursor.execute('''
        UPDATE mcl.postgres_views 
        SET column_count = (
            SELECT COUNT(*) 
            FROM mcl.postgres_columns 
            WHERE table_view_id = postgres_views.table_view_id 
                AND in_view = true
        )
    ''')
    
    # 7. Отмечаем завершение анализа
    cursor.execute('''
        UPDATE mcl.postgres_objects 
        SET analysis_completed = true
        WHERE source_table_id IN (
            SELECT id FROM mcl.mssql_tables WHERE task_id = %s
        )
    ''', (task_id,))
    
    cursor.execute('''
        UPDATE mcl.postgres_table_views 
        SET distribution_completed = true
        WHERE parent_object_id IN (
            SELECT id FROM mcl.postgres_objects 
            WHERE source_table_id IN (
                SELECT id FROM mcl.mssql_tables WHERE task_id = %s
            )
        )
    ''', (task_id,))
    
    conn.commit()
    return True
```

---

## 🔍 СРАВНЕНИЕ УЛУЧШЕННЫХ ПОДХОДОВ

| Критерий | Подход 1-Улучшенный | Подход 2-Улучшенный |
|----------|---------------------|---------------------|
| **Предварительное распределение** | ✅ Есть | ✅ Есть |
| **Детализация распределения** | ⚠️ Базовая | ✅ Полная |
| **Простота реализации** | ✅ Простой | ❌ Сложный |
| **Гибкость** | ⚠️ Ограниченная | ✅ Высокая |
| **Производительность** | ✅ Высокая | ⚠️ Средняя |
| **Отслеживание позиций** | ✅ Есть | ✅ Есть |
| **DDL готовность** | ⚠️ Частичная | ✅ Полная |

---

## 🎯 РЕКОМЕНДАЦИЯ

### **ПОДХОД 1-УЛУЧШЕННЫЙ** - оптимальный баланс простоты и функциональности

#### **Ключевые улучшения:**
1. **Предварительное распределение** колонок на этапе формирования метаданных
2. **Явное указание** `target_type` для каждой колонки
3. **Позиционирование** колонок в каждом объекте
4. **Исключение ошибок** при выполнении миграции

#### **Алгоритм работы:**
1. **Этап анализа** - определение вычисляемых полей и распределение
2. **Этап создания** - использование готовых метаданных для DDL
3. **Этап проверки** - валидация созданных объектов

#### **Преимущества:**
- Все решения приняты заранее в метаданных
- Нет риска ошибок при выполнении миграции
- Простота реализации и поддержки
- Полная прозрачность распределения колонок

---

## 📋 ПЛАН ВНЕДРЕНИЯ УЛУЧШЕННОГО ПОДХОДА

### **Этап 1: Расширение структуры метаданных**
```sql
-- Добавление полей в postgres_tables
ALTER TABLE mcl.postgres_tables 
ADD COLUMN base_table_name VARCHAR,
ADD COLUMN view_name VARCHAR,
ADD COLUMN has_computed_columns BOOLEAN DEFAULT FALSE,
ADD COLUMN base_table_created BOOLEAN DEFAULT FALSE,
ADD COLUMN view_created BOOLEAN DEFAULT FALSE;

-- Добавление полей в postgres_columns
ALTER TABLE mcl.postgres_columns 
ADD COLUMN is_computed BOOLEAN DEFAULT FALSE,
ADD COLUMN target_type VARCHAR DEFAULT 'base_table',
ADD COLUMN base_table_position INTEGER,
ADD COLUMN view_position INTEGER;
```

### **Этап 2: Создание функций анализа**
```python
def analyze_and_distribute_columns(task_id: int) -> bool:
    # Реализация предварительного распределения
    pass

def generate_table_names(table_name: str, has_computed: bool) -> Dict[str, str]:
    # Генерация имен объектов
    pass
```

### **Этап 3: Обновление функций миграции**
```python
def create_table_structure(table_id: int, task_id: int) -> bool:
    # Использование готовых метаданных
    pass
```

### **Этап 4: Тестирование**
- Проверка корректности распределения колонок
- Валидация созданных объектов
- Тестирование производительности

---

## 🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### **Устранение недостатков:**
1. ✅ Распределение колонок происходит на этапе формирования метаданных
2. ✅ Все решения зафиксированы в схеме `mcl`
3. ✅ Исключены ошибки при выполнении миграции
4. ✅ Полная прозрачность и контролируемость процесса

### **Дополнительные преимущества:**
1. ✅ Возможность предварительной валидации распределения
2. ✅ Легкость отладки и исправления ошибок
3. ✅ Возможность детального мониторинга процесса
4. ✅ Подготовленность DDL для всех объектов

Этот уточненный подход полностью решает выявленную проблему и обеспечивает надежную миграцию с предварительным планированием всех аспектов.