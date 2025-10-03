# ПРАВИЛА УПРАВЛЕНИЯ СПИСКОМ ТАБЛИЦ

## Описание
Данный модуль обеспечивает управление списком таблиц для миграции, отслеживание их статуса и логирование прогресса миграции всех 166 таблиц.

## Основные функции

### 1. Инициализация списка таблиц
- Создание начального списка всех таблиц для миграции
- Установка начального статуса для каждой таблицы
- Инициализация счётчиков и метрик

### 2. Управление статусами таблиц
- Отслеживание текущего статуса каждой таблицы
- Обновление статуса при изменении состояния
- Логирование всех изменений статуса

### 3. Мониторинг прогресса
- Подсчёт количества обработанных таблиц
- Вычисление процента завершения
- Генерация отчётов о прогрессе

### 4. Обработка ошибок
- Логирование ошибок для каждой таблицы
- Ведение истории попыток миграции
- Управление повторными попытками

## Статусы таблиц

### Основные статусы
- **`pending`** - Таблица ожидает миграции
- **`in_progress`** - Таблица в процессе миграции
- **`completed`** - Таблица успешно мигрирована
- **`failed`** - Ошибка при миграции таблицы
- **`skipped`** - Таблица пропущена (зависимости не готовы)
- **`blocked`** - Таблица заблокирована (критические ошибки)

### Детальные статусы
- **`pending_dependency_check`** - Ожидает проверки зависимостей
- **`pending_structure_creation`** - Ожидает создания структуры
- **`pending_data_migration`** - Ожидает переноса данных
- **`pending_foreign_keys`** - Ожидает создания внешних ключей
- **`pending_validation`** - Ожидает валидации

## Python API

### Основные функции

#### `initialize_table_list()`
```python
def initialize_table_list():
    """
    Инициализация списка таблиц для миграции
    
    Returns:
        dict: Словарь с информацией о таблицах и их статусах
    """
```

#### `get_incomplete_tables()`
```python
def get_incomplete_tables():
    """
    Получение списка незавершённых таблиц
    
    Returns:
        list: Список таблиц, которые ещё не завершены
    """
```

#### `update_table_status(table_name, status, details=None)`
```python
def update_table_status(table_name, status, details=None):
    """
    Обновление статуса таблицы
    
    Args:
        table_name (str): Имя таблицы
        status (str): Новый статус
        details (dict): Дополнительные детали
    
    Returns:
        bool: True если обновление успешно
    """
```

#### `mark_table_completed(table_name, metrics=None)`
```python
def mark_table_completed(table_name, metrics=None):
    """
    Отметка таблицы как завершённой
    
    Args:
        table_name (str): Имя таблицы
        metrics (dict): Метрики миграции
    
    Returns:
        bool: True если операция успешна
    """
```

#### `get_migration_progress()`
```python
def get_migration_progress():
    """
    Получение информации о прогрессе миграции
    
    Returns:
        dict: Статистика прогресса миграции
    """
```

### Дополнительные функции

#### `get_table_status(table_name)`
```python
def get_table_status(table_name):
    """
    Получение текущего статуса таблицы
    
    Args:
        table_name (str): Имя таблицы
    
    Returns:
        str: Текущий статус таблицы
    """
```

#### `get_failed_tables()`
```python
def get_failed_tables():
    """
    Получение списка таблиц с ошибками
    
    Returns:
        list: Список таблиц со статусом 'failed'
    """
```

#### `get_blocked_tables()`
```python
def get_blocked_tables():
    """
    Получение списка заблокированных таблиц
    
    Returns:
        list: Список таблиц со статусом 'blocked'
    """
```

#### `retry_failed_table(table_name)`
```python
def retry_failed_table(table_name):
    """
    Повторная попытка миграции таблицы
    
    Args:
        table_name (str): Имя таблицы
    
    Returns:
        bool: True если попытка инициирована
    """
```

#### `get_migration_statistics()`
```python
def get_migration_statistics():
    """
    Получение детальной статистики миграции
    
    Returns:
        dict: Подробная статистика по всем таблицам
    """
```

## Структура данных

### Таблица миграции
```sql
CREATE TABLE mcl.migration_status (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL UNIQUE,
    current_status VARCHAR(50) NOT NULL,
    previous_status VARCHAR(50),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    attempt_count INTEGER DEFAULT 0,
    last_error TEXT,
    error_details JSONB,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Индексы
```sql
CREATE INDEX idx_migration_status_table_name ON mcl.migration_status(table_name);
CREATE INDEX idx_migration_status_current_status ON mcl.migration_status(current_status);
CREATE INDEX idx_migration_status_updated_at ON mcl.migration_status(updated_at);
```

## Логирование

### Уровни логирования
- **INFO** - Общий прогресс миграции
- **WARNING** - Предупреждения о потенциальных проблемах
- **ERROR** - Ошибки миграции таблиц
- **DEBUG** - Детальная информация для отладки

### Формат логов
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "table_name": "accnt",
    "status": "completed",
    "message": "Table migration completed successfully",
    "metrics": {
        "duration_seconds": 45.2,
        "records_migrated": 1250,
        "structure_elements": 8
    }
}
```

## Метрики и мониторинг

### Основные метрики
- **Время миграции** - Общее время переноса таблицы
- **Количество записей** - Количество перенесённых записей
- **Элементы структуры** - Количество созданных элементов
- **Размер данных** - Объём перенесённых данных

### Статистика прогресса
- **Общий прогресс** - Процент завершённых таблиц
- **Прогресс по статусам** - Распределение по статусам
- **Скорость миграции** - Таблиц в час
- **Ошибки** - Количество и типы ошибок

## Интеграция с другими модулями

### С модулем анализа зависимостей
- Передача информации о готовности ссылочных таблиц
- Обновление статуса на основе анализа зависимостей

### С модулем переноса данных
- Передача статуса начала/завершения переноса
- Получение метрик производительности

### С модулем мониторинга
- Предоставление данных для дашборда
- Генерация уведомлений о критических событиях

## Обработка ошибок

### Типы ошибок
1. **Структурные ошибки** - Проблемы создания структуры
2. **Ошибки данных** - Проблемы переноса данных
3. **Ошибки зависимостей** - Проблемы с внешними ключами
4. **Ошибки производительности** - Медленный перенос

### Стратегии восстановления
1. **Автоматический повтор** - Для временных ошибок
2. **Отложенный повтор** - Для ошибок зависимостей
3. **Ручное вмешательство** - Для критических ошибок
4. **Пропуск таблицы** - Для некритических проблем

## Примеры использования

### Инициализация миграции
```python
# Инициализация списка таблиц
table_list = initialize_table_list()
print(f"Инициализировано {len(table_list)} таблиц")

# Получение незавершённых таблиц
incomplete = get_incomplete_tables()
print(f"Незавершённых таблиц: {len(incomplete)}")
```

### Мониторинг прогресса
```python
# Получение прогресса
progress = get_migration_progress()
print(f"Прогресс: {progress['percentage']:.1f}%")
print(f"Завершено: {progress['completed']}/{progress['total']}")

# Получение статистики
stats = get_migration_statistics()
print(f"Ошибок: {stats['failed_count']}")
print(f"В процессе: {stats['in_progress_count']}")
```

### Обработка ошибок
```python
# Получение таблиц с ошибками
failed_tables = get_failed_tables()
for table in failed_tables:
    status = get_table_status(table)
    print(f"Таблица {table}: {status}")

# Повторная попытка
for table in failed_tables:
    if retry_failed_table(table):
        print(f"Повторная попытка для {table} инициирована")
```

## Следующие шаги

1. **Реализация Python функций**
2. **Создание тестового скрипта**
3. **Интеграция с существующими правилами**
4. **Тестирование на подмножестве таблиц**
5. **Интеграция с модулем анализа зависимостей**