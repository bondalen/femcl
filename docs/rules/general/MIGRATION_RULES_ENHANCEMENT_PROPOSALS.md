# ПРЕДЛОЖЕНИЯ ПО ДОРАБОТКЕ ПРАВИЛ МИГРАЦИИ

## Обзор изменений

На основе анализа BPMN алгоритма и существующих правил предлагается создать двухуровневую систему правил миграции:

### Уровень 1: Общие правила миграции (НОВЫЙ)
- **Файл:** `general/COMPLETE_MIGRATION_RULES.md`
- **Назначение:** Управление процессом миграции всех 166 таблиц
- **Основа:** BPMN алгоритм с учётом зависимостей внешних ключей

### Уровень 2: Правила переноса отдельных таблиц (СУЩЕСТВУЮЩИЙ)
- **Папка:** `single_table/`
- **Назначение:** Детальные правила для переноса одной таблицы
- **Файлы:** 4 существующих файла правил

## Предлагаемые доработки

### 1. Создание модуля управления списком таблиц

#### Новый файл: `general/TABLE_LIST_MANAGEMENT_RULES.md`

**Функции:**
- Ведение списка незавершённых таблиц
- Отслеживание статуса каждой таблицы
- Логирование прогресса миграции
- Обработка ошибок и повторных попыток

**Python функции:**
```python
def initialize_table_list()
def update_table_status(table_name, status)
def get_incomplete_tables()
def mark_table_completed(table_name)
def get_migration_progress()
```

### 2. Создание модуля анализа зависимостей

#### Новый файл: `general/DEPENDENCY_ANALYSIS_RULES.md`

**Функции:**
- Анализ внешних ключей таблицы
- Проверка готовности ссылочных таблиц
- Выявление циклических зависимостей
- Определение порядка переноса таблиц

**Python функции:**
```python
def analyze_table_dependencies(table_name)
def check_referenced_tables_ready(table_name)
def detect_circular_dependencies()
def get_migration_order()
```

### 3. Создание модуля последовательного переноса данных

#### Новый файл: `general/SEQUENTIAL_DATA_MIGRATION_RULES.md`

**Функции:**
- Управление последовательностью переноса данных
- Обеспечение целостности данных при переносе
- Обработка зависимостей между записями
- Валидация перенесённых данных

**Python функции:**
```python
def migrate_table_data_sequentially(table_name)
def validate_data_integrity(table_name)
def handle_foreign_key_constraints(table_name)
def rollback_table_migration(table_name)
```

### 4. Доработка существующих правил

#### 4.1 Обновление `SINGLE_TABLE_MIGRATION_RULES.md`

**Добавить:**
- Интеграцию с общими правилами миграции
- Проверку готовности ссылочных таблиц
- Обработку ошибок зависимостей
- Логирование для общего процесса

**Новые этапы:**
```python
def check_dependencies_before_migration(table_name)
def create_table_structure_with_dependencies(table_name)
def migrate_data_with_integrity_checks(table_name)
def create_foreign_keys_after_data_migration(table_name)
```

#### 4.2 Обновление `TABLE_CREATION_RULES.md`

**Добавить:**
- Создание внешних ключей после переноса данных
- Проверку ссылочной целостности
- Обработку ошибок зависимостей

**Новые функции:**
```python
def create_foreign_keys_after_data_migration(table_name)
def validate_foreign_key_constraints(table_name)
def handle_dependency_errors(table_name, error)
```

#### 4.3 Обновление `DATA_MIGRATION_RULES.md`

**Добавить:**
- Проверку целостности данных перед переносом
- Валидацию ссылочных данных
- Обработку ошибок зависимостей

**Новые функции:**
```python
def validate_data_before_migration(table_name)
def check_referenced_data_exists(table_name)
def migrate_data_with_dependency_validation(table_name)
```

#### 4.4 Обновление `TABLE_READINESS_CHECK_RULES.md`

**Добавить:**
- Проверку готовности ссылочных таблиц
- Анализ зависимостей
- Валидацию целостности данных

**Новые функции:**
```python
def check_referenced_tables_ready(table_name)
def validate_dependency_chain(table_name)
def check_data_integrity_requirements(table_name)
```

### 5. Создание модуля мониторинга и логирования

#### Новый файл: `general/MIGRATION_MONITORING_RULES.md`

**Функции:**
- Мониторинг прогресса миграции
- Логирование всех операций
- Отслеживание ошибок и их обработка
- Генерация отчётов о миграции

**Python функции:**
```python
def log_migration_start(table_name)
def log_migration_progress(table_name, step, status)
def log_migration_error(table_name, error)
def generate_migration_report()
```

### 6. Создание модуля обработки ошибок

#### Новый файл: `general/ERROR_HANDLING_RULES.md`

**Функции:**
- Классификация ошибок миграции
- Стратегии восстановления
- Обработка критических ошибок
- Уведомления о проблемах

**Python функции:**
```python
def classify_migration_error(error)
def get_error_recovery_strategy(error)
def handle_critical_migration_error(table_name, error)
def notify_migration_issues()
```

## Структура новой системы правил

```
docs/rules/
├── general/                          # Общие правила миграции
│   ├── COMPLETE_MIGRATION_RULES.md  # Основной алгоритм (СОЗДАН)
│   ├── TABLE_LIST_MANAGEMENT_RULES.md
│   ├── DEPENDENCY_ANALYSIS_RULES.md
│   ├── SEQUENTIAL_DATA_MIGRATION_RULES.md
│   ├── MIGRATION_MONITORING_RULES.md
│   └── ERROR_HANDLING_RULES.md
└── single_table/                     # Правила для отдельных таблиц
    ├── SINGLE_TABLE_MIGRATION_RULES.md
    ├── TABLE_CREATION_RULES.md
    ├── TABLE_READINESS_CHECK_RULES.md
    └── DATA_MIGRATION_RULES.md
```

## Приоритеты реализации

### Фаза 1: Основная инфраструктура
1. ✅ Создание структуры папок
2. ✅ Создание основного файла общих правил
3. ✅ Перемещение существующих файлов
4. 🔄 Создание модуля управления списком таблиц
5. 🔄 Создание модуля анализа зависимостей

### Фаза 2: Интеграция и доработка
1. Обновление существующих правил
2. Создание модуля последовательного переноса данных
3. Создание модуля мониторинга
4. Создание модуля обработки ошибок

### Фаза 3: Тестирование и оптимизация
1. Тестирование на подмножестве таблиц
2. Оптимизация производительности
3. Полномасштабное тестирование
4. Документирование и обучение

## Преимущества новой структуры

### 1. Модульность
- Чёткое разделение ответственности
- Возможность независимой разработки модулей
- Лёгкость тестирования и отладки

### 2. Масштабируемость
- Поддержка миграции всех 166 таблиц
- Обработка сложных зависимостей
- Возможность добавления новых типов правил

### 3. Надёжность
- Обработка ошибок на всех уровнях
- Восстановление после сбоев
- Валидация на каждом этапе

### 4. Мониторинг
- Полная видимость процесса миграции
- Детальное логирование
- Возможность анализа производительности

## Следующие шаги

1. **Создание модуля управления списком таблиц**
2. **Создание модуля анализа зависимостей**
3. **Обновление существующих правил**
4. **Создание модуля последовательного переноса данных**
5. **Тестирование на подмножестве таблиц**
6. **Полномасштабная миграция всех 166 таблиц**