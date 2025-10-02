# 📋 ПРЕДЛОЖЕНИЯ ПО КОРРЕКТИРОВКЕ ПРАВИЛ МИГРАЦИИ

## 🎯 **КРИТИЧЕСКИЕ КОРРЕКТИРОВКИ**

### 1. **ДОБАВЛЕНИЕ КОНТЕКСТА ЗАДАЧИ МИГРАЦИИ**

**Проблема:** В правилах не указано, что миграция выполняется в контексте конкретной задачи с определенным ID.

**Решение:** Добавить во все правила ссылку на `task_id` и обязательную фильтрацию по нему.

#### **1.1 Корректировка SINGLE_TABLE_MIGRATION_RULES.md**

**Добавить в начало документа:**

```markdown
## 🎯 КОНТЕКСТ ЗАДАЧИ МИГРАЦИИ

**⚠️ КРИТИЧЕСКИ ВАЖНО:** Все операции миграции выполняются в контексте конкретной задачи миграции.

### Параметры задачи:
- `task_id` - идентификатор задачи миграции (например, 2)
- `task_name` - название задачи миграции
- `task_description` - описание задачи
- `created_at` - дата создания задачи

### Обязательные фильтры:
Все SQL-запросы к метаданным должны включать фильтр:
```sql
WHERE task_id = <TASK_ID>
```

**Пример использования:**
```python
def get_migration_tables(task_id: int):
    """Получение списка таблиц для конкретной задачи"""
    cursor.execute('''
        SELECT mt.*, pt.migration_status
        FROM mcl.mssql_tables mt
        JOIN mcl.postgres_tables pt ON mt.id = pt.source_table_id
        WHERE mt.task_id = %s
        ORDER BY mt.object_name
    ''', (task_id,))
```

#### **1.2 Корректировка всех SQL-запросов**

**Заменить все запросы без task_id:**

```sql
-- БЫЛО:
SELECT * FROM mcl.mssql_tables WHERE schema_name = 'ags'

-- СТАЛО:
SELECT * FROM mcl.mssql_tables 
WHERE schema_name = 'ags' AND task_id = 2
```

#### **1.3 Обновление функций миграции**

**Добавить task_id во все функции:**

```python
def get_table_structure(table_id: int, task_id: int) -> Dict:
    """Получение структуры таблицы с проверкой task_id"""
    cursor.execute('''
        SELECT 
            mt.object_name,
            mt.schema_name,
            mt.row_count,
            pt.object_name as target_name,
            pt.schema_name as target_schema
        FROM mcl.mssql_tables mt
        JOIN mcl.postgres_tables pt ON mt.id = pt.source_table_id
        WHERE mt.id = %s AND mt.task_id = %s
    ''', (table_id, task_id))
```

### 2. **ДОБАВЛЕНИЕ ПРОВЕРКИ ЦЕЛОСТНОСТИ ЗАДАЧИ**

#### **2.1 Валидация существования задачи**

```python
def validate_migration_task(task_id: int) -> bool:
    """Проверка существования и валидности задачи миграции"""
    cursor.execute('''
        SELECT id, description, created_at, status
        FROM mcl.migration_tasks
        WHERE id = %s
    ''', (task_id,))
    
    task = cursor.fetchone()
    if not task:
        raise ValueError(f"Задача миграции с ID {task_id} не найдена")
    
    return True
```

#### **2.2 Проверка соответствия таблиц задаче**

```python
def validate_table_belongs_to_task(table_id: int, task_id: int) -> bool:
    """Проверка, что таблица принадлежит указанной задаче"""
    cursor.execute('''
        SELECT COUNT(*) FROM mcl.mssql_tables
        WHERE id = %s AND task_id = %s
    ''', (table_id, task_id))
    
    count = cursor.fetchone()[0]
    if count == 0:
        raise ValueError(f"Таблица {table_id} не принадлежит задаче {task_id}")
    
    return True
```

### 3. **ОБНОВЛЕНИЕ ЛОГИРОВАНИЯ**

#### **3.1 Добавление task_id в события**

```python
def log_migration_event(event_type: str, message: str, severity: str = 'INFO', 
                       table_name: str = None, task_id: int = None):
    """Логирование события миграции с указанием task_id"""
    cursor.execute('''
        INSERT INTO mcl.migration_events 
        (event_type, event_message, severity, table_name, task_id)
        VALUES (%s, %s, %s, %s, %s)
    ''', (event_type, message, severity, table_name, task_id))
```

#### **3.2 Обновление структуры таблицы migration_events**

```sql
ALTER TABLE mcl.migration_events 
ADD COLUMN task_id INTEGER REFERENCES mcl.migration_tasks(id);

CREATE INDEX idx_migration_events_task_id ON mcl.migration_events(task_id);
```

### 4. **КОРРЕКТИРОВКА BPMN АЛГОРИТМА**

#### **4.1 Обновление COMPLETE_MIGRATION_RULES.md**

**Добавить в инициализацию:**

```markdown
### 1. Инициализация задачи миграции

**Задача:** `Перенос таблиц. Начало`
- Получить task_id из параметров
- Валидировать существование задачи
- Создать список таблиц для конкретной задачи
- Инициализировать счётчики и логирование процесса с указанием task_id
```

#### **4.2 Обновление цикла проверки**

```markdown
### 2. Основной цикл проверки

**Проверка наличия таблиц в списке задачи:**
```python
def get_unmigrated_tables_for_task(task_id: int):
    """Получение незавершенных таблиц для конкретной задачи"""
    cursor.execute('''
        SELECT mt.*, pt.migration_status
        FROM mcl.mssql_tables mt
        JOIN mcl.postgres_tables pt ON mt.id = pt.source_table_id
        WHERE mt.task_id = %s 
            AND pt.migration_status IN ('pending', 'failed')
        ORDER BY mt.object_name
    ''', (task_id,))
```

### 5. **ОБНОВЛЕНИЕ ИНСТРУМЕНТОВ МИГРАЦИИ**

#### **5.1 Обновление migration_functions.py**

```python
def migrate_single_table(table_id: int, task_id: int) -> bool:
    """Полная миграция одной таблицы в контексте задачи"""
    
    # Валидация задачи и таблицы
    validate_migration_task(task_id)
    validate_table_belongs_to_task(table_id, task_id)
    
    # Логирование с task_id
    log_migration_event(
        'TABLE_MIGRATION_START',
        f'Начало миграции таблицы {table_id} в задаче {task_id}',
        'INFO',
        task_id=task_id
    )
    
    # Остальная логика миграции...
```

#### **5.2 Обновление test_migration_v2.py**

```python
def execute_migration_cycle_v2(task_id: int = 2):
    """Выполнение цикла миграции для конкретной задачи"""
    
    # Валидация задачи
    validate_migration_task(task_id)
    
    # Получение таблиц для задачи
    tables_to_migrate = get_unmigrated_tables_for_task(task_id)
    
    # Остальная логика...
```

### 6. **ДОПОЛНИТЕЛЬНЫЕ ПРЕДЛОЖЕНИЯ**

#### **6.1 Добавление статистики по задачам**

```sql
CREATE VIEW mcl.v_task_migration_stats AS
SELECT 
    mt.id as task_id,
    mt.description,
    COUNT(pt.id) as total_tables,
    COUNT(CASE WHEN pt.migration_status = 'completed' THEN 1 END) as completed_tables,
    COUNT(CASE WHEN pt.migration_status = 'pending' THEN 1 END) as pending_tables,
    COUNT(CASE WHEN pt.migration_status = 'failed' THEN 1 END) as failed_tables,
    ROUND(
        COUNT(CASE WHEN pt.migration_status = 'completed' THEN 1 END) * 100.0 / COUNT(pt.id), 
        2
    ) as completion_percentage
FROM mcl.migration_tasks mt
LEFT JOIN mcl.mssql_tables mst ON mt.id = mst.task_id
LEFT JOIN mcl.postgres_tables pt ON mst.id = pt.source_table_id
GROUP BY mt.id, mt.description;
```

#### **6.2 Добавление проверки зависимостей между задачами**

```python
def check_task_dependencies(task_id: int) -> List[int]:
    """Проверка зависимостей между задачами миграции"""
    cursor.execute('''
        SELECT dependent_task_id
        FROM mcl.task_dependencies
        WHERE task_id = %s
    ''', (task_id,))
    
    return [row[0] for row in cursor.fetchall()]
```

#### **6.3 Добавление возможности отката задачи**

```python
def rollback_migration_task(task_id: int) -> bool:
    """Откат миграции для конкретной задачи"""
    
    # Обновление статусов таблиц
    cursor.execute('''
        UPDATE mcl.postgres_tables
        SET migration_status = 'pending', updated_at = NOW()
        WHERE source_table_id IN (
            SELECT id FROM mcl.mssql_tables WHERE task_id = %s
        )
    ''', (task_id,))
    
    # Удаление физических таблиц (опционально)
    # Логирование отката
    
    return True
```

## 📋 **ПЛАН ВНЕДРЕНИЯ КОРРЕКТИРОВОК**

### Этап 1: Обновление структуры БД
1. Добавить колонку `task_id` в `migration_events`
2. Создать индексы для `task_id`
3. Создать представления статистики

### Этап 2: Обновление правил
1. Обновить `SINGLE_TABLE_MIGRATION_RULES.md`
2. Обновить `COMPLETE_MIGRATION_RULES.md`
3. Добавить новые правила валидации

### Этап 3: Обновление инструментов
1. Обновить `migration_functions.py`
2. Обновить `test_migration_v2.py`
3. Добавить новые функции валидации

### Этап 4: Тестирование
1. Протестировать с task_id = 2
2. Проверить логирование
3. Валидировать результаты

## 🎯 **ЗАКЛЮЧЕНИЕ**

Добавление контекста задачи миграции критически важно для:
- **Изоляции задач** - каждая задача работает только со своими таблицами
- **Параллельной работы** - можно запускать несколько задач одновременно
- **Отслеживания прогресса** - четкая статистика по каждой задаче
- **Отката изменений** - возможность откатить конкретную задачу
- **Аудита** - полное логирование действий по задачам

**Рекомендация:** Внедрить все корректировки перед началом полномасштабной миграции.

