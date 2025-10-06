# 📋 Миграция отдельной таблицы

## 🎯 Назначение
Документ описывает процесс миграции отдельной таблицы в рамках этапа 1.2 "Создание объектов и перенос данных" системы FEMCL.

---

## 📖 Обзор

### Контекст
- **Этап:** 1.2 - Создание объектов и перенос данных
- **Задача миграции:** ID=2
- **Область:** Отдельные таблицы
- **Цель:** Создание объектов и перенос данных для одной таблицы

### Принципы
- **Последовательность:** Переход к следующей таблице только после полного завершения предыдущей
- **Полнота:** Каждая таблица мигрируется полностью (структура + данные)
- **Контроль:** Все операции отслеживаются в схеме mcl

---

## 🏗️ Архитектура

### Классы и компоненты

#### TableMigrator
Основной класс для миграции отдельной таблицы:
- **Файл:** `src/classes/table_migrator.py`
- **Назначение:** Оркестрация процесса миграции таблицы
- **Методы:**
  - `get_table_metadata()` - получение метаданных таблицы
  - `create_target_table()` - создание целевой таблицы
  - `create_indexes()` - создание индексов
  - `create_foreign_keys()` - создание внешних ключей
  - `create_constraints()` - создание ограничений
  - `create_triggers()` - создание триггеров
  - `migrate_table_data()` - перенос данных
  - `validate_migration()` - валидация миграции

#### TableModel (абстрактный)
Базовый класс для представления таблицы:
- **Файл:** `src/classes/table_model.py`
- **Назначение:** Абстрактная модель таблицы
- **Фабричный метод:** `create_table_model()` - создание правильного типа модели
- **Абстрактные методы:**
  - `generate_table_ddl()` - генерация DDL для таблицы
  - `generate_indexes_ddl()` - генерация DDL для индексов
  - `migrate_data()` - миграция данных

#### RegularTableModel
Модель обычной таблицы без вычисляемых колонок:
- **Файл:** `src/classes/regular_table_model.py`
- **Назначение:** Конкретная реализация для обычных таблиц
- **Особенности:** Прямая миграция без дополнительных объектов

#### BaseTableModel
Модель базовой таблицы с вычисляемыми колонками:
- **Файл:** `src/classes/base_table_model.py`
- **Назначение:** Конкретная реализация для таблиц с вычисляемыми колонками
- **Особенности:** Создание базовой таблицы + представления
- **Компоненты:**
  - `target_base_table_name` - имя базовой таблицы
  - `view_reference` - ссылка на ViewModel

#### ViewModel
Модель представления для вычисляемых колонок:
- **Файл:** `src/classes/view_model.py`
- **Назначение:** Управление представлением с вычисляемыми колонками
- **Компоненты:**
  - `view_name` - имя представления
  - `base_table_name` - имя базовой таблицы
  - `computed_columns` - список вычисляемых колонок
  - `base_table_model` - ссылка на базовую таблицу

#### ComputedColumnModel
Модель вычисляемой колонки:
- **Файл:** `src/classes/computed_column_model.py`
- **Назначение:** Представление отдельной вычисляемой колонки
- **Компоненты:**
  - `name` - имя колонки
  - `source_expression` - исходное выражение
  - `target_expression` - целевое выражение
  - `function_mapping` - состояние маппинга функции

#### FunctionMappingState
Состояние маппинга функции:
- **Файл:** `src/classes/function_mapping_state.py`
- **Назначение:** Управление состоянием и валидацией маппинга функций
- **Компоненты:**
  - `status` - статус маппинга
  - `complexity` - сложность выражения
  - `functions` - список найденных функций
  - `function_mapping_model` - модель маппинга (если есть)
  - `requires_manual_review` - требует ли ручной проверки

---

## 🔄 Процесс миграции

### 1. Инициализация
```python
# Создание мигратора таблицы
migrator = TableMigrator(table_name="accnt", verbose=True)

# Получение метаданных
metadata = migrator.get_table_metadata()
```

### 2. Определение типа таблицы
```python
# Проверка наличия вычисляемых колонок
has_computed_columns = migrator._check_has_computed_columns()

# Создание правильной модели через фабричный метод
table_model = TableModel.create_table_model(table_name, has_computed_columns)
```

### 3. Загрузка метаданных
```python
# Загрузка всех метаданных таблицы
success = table_model.load_metadata(config_loader)

# Для BaseTableModel дополнительно загружается ViewModel
if isinstance(table_model, BaseTableModel):
    table_model.view_reference.load_computed_columns(config_loader)
```

### 4. Создание объектов
```python
# Создание целевой таблицы
migrator.create_target_table()

# Создание индексов
migrator.create_indexes()

# Создание ограничений
migrator.create_constraints()

# Создание триггеров
migrator.create_triggers()
```

### 5. Перенос данных
```python
# Миграция данных таблицы
migrator.migrate_table_data()
```

### 6. Валидация
```python
# Валидация миграции
migrator.validate_migration()
```

---

## 📊 Метаданные

### Источники метаданных

#### MS SQL Server (исходная БД)
- **Таблицы:** `mcl.mssql_tables`
- **Колонки:** `mcl.mssql_columns`
- **Индексы:** `mcl.mssql_indexes`
- **Ограничения:** `mcl.mssql_*_constraints`

#### PostgreSQL (целевая БД)
- **Таблицы:** `mcl.postgres_tables`
- **Колонки:** `mcl.postgres_columns`
- **Индексы:** `mcl.postgres_indexes`
- **Ограничения:** `mcl.postgres_*_constraints`

#### Правила маппинга
- **Функции:** `mcl.function_mapping_rules`
- **Типы данных:** `mcl.mssql_derived_types`, `mcl.postgres_derived_types`

### Ключевые поля

#### mcl.postgres_tables
- `object_name` - имя целевой таблицы
- `base_table_name` - имя базовой таблицы (для таблиц с вычисляемыми колонками)
- `view_name` - имя представления (для таблиц с вычисляемыми колонками)
- `has_computed_columns` - флаг наличия вычисляемых колонок

#### mcl.postgres_columns
- `column_name` - имя целевой колонки
- `is_computed` - флаг вычисляемой колонки
- `target_type` - тип колонки ('both', 'view')
- `computed_definition` - исходное выражение
- `postgres_computed_definition` - целевое выражение

---

## 🎯 Вычисляемые колонки

### Принцип обработки
PostgreSQL не поддерживает вычисляемые колонки напрямую, поэтому используется подход с разделением на:
1. **Базовую таблицу** - содержит только физические колонки
2. **Представление** - содержит все колонки, включая вычисляемые

### Процесс создания
1. Создание базовой таблицы с физическими колонками
2. Создание представления с базовыми + вычисляемыми колонками
3. Маппинг функций в вычисляемых выражениях

### Маппинг функций
```python
# Анализ состояния функции
function_state = computed_col.analyze_function_state(config_loader)

# Применение маппинга
if function_state.function_mapping_model:
    success = computed_col.map_function()
```

---

## 🔧 Конфигурация

### config.yaml
```yaml
databases:
  mssql:
    host: "source-server"
    database: "Fish_Eye"
    # ... другие параметры
  
  postgres:
    host: "target-server"
    database: "fish_eye_mcl"
    # ... другие параметры

migration:
  task_id: 2
  verbose: true
```

### Использование
```python
from config.config_loader import ConfigLoader

config_loader = ConfigLoader()
mssql_config = config_loader.get_database_config('mssql')
postgres_config = config_loader.get_database_config('postgres')
```

---

## 📝 Примеры использования

### Миграция обычной таблицы
```python
# Создание мигратора
migrator = TableMigrator("accnt", verbose=True)

# Получение метаданных
metadata = migrator.get_table_metadata()
table_model = metadata['table_model']

# Проверка типа таблицы
if isinstance(table_model, RegularTableModel):
    print(f"Обычная таблица: {table_model.target_table_name}")
    
# Создание таблицы
migrator.create_target_table()

# Перенос данных
migrator.migrate_table_data()
```

### Миграция таблицы с вычисляемыми колонками
```python
# Создание мигратора
migrator = TableMigrator("rgTaxIdNumInd", verbose=True)

# Получение метаданных
metadata = migrator.get_table_metadata()
table_model = metadata['table_model']

# Проверка типа таблицы
if isinstance(table_model, BaseTableModel):
    print(f"Базовая таблица: {table_model.target_base_table_name}")
    print(f"Представление: {table_model.view_reference.view_name}")
    
    # Проверка вычисляемых колонок
    for col in table_model.view_reference.computed_columns:
        print(f"Вычисляемая колонка: {col.name}")
        print(f"Статус маппинга: {col.mapping_status}")
        
# Создание объектов
migrator.create_target_table()  # Создает и таблицу, и представление
```

---

## 🚨 Обработка ошибок

### Типичные ошибки
1. **Отсутствие исходной таблицы** - проверка `source_exists`
2. **Ошибки маппинга функций** - статус `manual_review_required`
3. **Ошибки создания объектов** - логирование в `mcl.migration_events`
4. **Ошибки переноса данных** - валидация количества строк

### Логирование
```python
# События миграции
mcl.migration_events

# Статусы миграции
mcl.migration_status

# Проблемы
mcl.problems
```

---

## 📈 Мониторинг и валидация

### Метрики миграции
- **Время выполнения** - `migration_duration`
- **Количество строк** - `source_row_count` vs фактическое
- **Статус миграции** - `migration_status`
- **Ошибки** - `errors` список

### Валидация
```python
# Валидация миграции
success = migrator.validate_migration()

# Проверка количества строк
source_count = table_model.source_row_count
target_count = get_target_row_count(table_model.target_table_name)

if source_count != target_count:
    print(f"❌ Несоответствие количества строк: {source_count} != {target_count}")
```

---

## 🔄 Следующие шаги

### После миграции таблицы
1. **Валидация** - проверка корректности миграции
2. **Логирование** - запись результатов в метаданные
3. **Переход к следующей таблице** - согласно алгоритму обхода
4. **Обновление прогресса** - в системе мониторинга

### Интеграция с алгоритмом обхода
```python
# Получение следующей таблицы
next_table = get_next_table_to_migrate()

# Миграция следующей таблицы
migrator = TableMigrator(next_table, verbose=True)
# ... процесс миграции
```

---

## 📚 Связанные документы

- [MIGRATION_STRATEGY.md](MIGRATION_STRATEGY.md) - общая стратегия миграции
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - схема метаданных
- [FUNCTION_MAPPING_RULES.md](../operations/rules/function_mapping/FUNCTION_MAPPING_RULES.md) - правила маппинга функций
- [class_diagram.puml](../diagrams/class_diagram.puml) - диаграмма классов

---

*Документ создан: 3 октября 2025*
*Последнее обновление: 3 октября 2025*
*Автор: AI Assistant*
*Статус: АКТИВНЫЙ*

