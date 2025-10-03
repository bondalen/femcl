# Архитектура проекта FEMCL

**Дата:** 27 января 2025  
**Статус:** Частично реализована  
**Основной замысел:** [PROJECT_CONCEPT.md](./PROJECT_CONCEPT.md)

## 🎯 Концепция архитектуры

### 📊 Двухэтапный подход
Архитектура системы построена на основе двухэтапного подхода к миграции:

1. **Этап 1:** Формирование таблиц и перенос данных
2. **Этап 2:** Создание иных объектов БД

Подробное описание концепции см. в [PROJECT_CONCEPT.md](./PROJECT_CONCEPT.md)

## 🏗️ Структура проекта

```
/home/alex/projects/sql/femcl/
├── src/
│   ├── classes/           # Классы системы
│   │   ├── table_migrator.py    # Основной класс миграции
│   │   ├── table_model.py        # Модель таблицы
│   │   └── column_model.py       # Модель колонки
│   └── scripts/           # Скрипты миграции
│       └── migrate_table.py      # Скрипт миграции таблицы
├── config/
│   ├── config.yaml       # Конфигурация
│   └── config_loader.py  # Загрузчик конфигурации
└── docs/
    └── reports/          # Отчеты и документация
```

**Подробное описание:** [MODULE_ARCHITECTURE.md](../architecture/MODULE_ARCHITECTURE.md)

## 🔧 Ключевые классы

### TableModel
- **Назначение:** Модель переносимой таблицы (Этап 1.1 - формирование метаданных)
- **Статус:** ✅ Реализован
- **Методы:**
  - ✅ `load_columns()` - загружает колонки из `mcl`
  - ❌ `load_indexes()` - НЕ реализован (Этап 1.2)
  - ❌ `load_foreign_keys()` - НЕ реализован (Этап 1.2)
  - ❌ `load_constraints()` - НЕ реализован (Этап 1.2)
  - ❌ `load_triggers()` - НЕ реализован (Этап 1.2)

### TableMigrator
- **Назначение:** Выполнение миграции таблицы (Этап 1.2 - создание объектов и перенос данных)
- **Статус:** ✅ Частично реализован
- **Методы:**
  - ✅ `create_target_table()` - создает таблицу
  - ✅ `migrate_table_data()` - переносит данные
  - ❌ `create_indexes()` - НЕ реализован (Этап 1.2)
  - ❌ `create_constraints()` - НЕ реализован (Этап 1.2)
  - ❌ `create_triggers()` - НЕ реализован (Этап 1.2)

### ColumnModel
- **Назначение:** Модель колонки таблицы
- **Статус:** ✅ Реализован
- **Свойства:**
  - `name` - целевое имя (PostgreSQL)
  - `source_name` - исходное имя (MS SQL)
  - `data_type` - тип данных
  - `is_identity` - является ли identity колонкой

## 📊 Метаданные в PostgreSQL

### Таблицы метаданных:
- `mcl.postgres_tables` - таблицы
- `mcl.postgres_columns` - колонки
- `mcl.postgres_indexes` - индексы
- `mcl.postgres_foreign_keys` - внешние ключи
- `mcl.postgres_unique_constraints` - уникальные ограничения
- `mcl.postgres_check_constraints` - проверочные ограничения
- `mcl.postgres_triggers` - триггеры

### Связи:
- `mcl.mssql_tables` ↔ `mcl.postgres_tables` (через `source_table_id`)
- `mcl.mssql_columns` ↔ `mcl.postgres_columns` (через `source_column_id`)
- `mcl.mssql_indexes` ↔ `mcl.postgres_indexes` (через `source_index_id`)

## 🎯 Текущий статус миграции

### Таблица `accnt`:
- ✅ Колонки: 3 шт. перенесены
- ✅ Данные: 16 строк перенесены
- ❌ Индексы: 3 шт. НЕ перенесены
- ❌ Ограничения: НЕ перенесены
- ❌ Триггеры: НЕ перенесены

### Таблица `cn`:
- ✅ Метаданные загружены
- ✅ Преобразование имен (CamelCase → snake_case)
- ❌ Миграция не выполнена

## 🔧 Требуемые доработки

1. **Реализовать загрузку индексов в TableModel**
2. **Реализовать создание индексов в TableMigrator**
3. **Реализовать загрузку и создание ограничений**
4. **Реализовать загрузку и создание триггеров**
5. **Протестировать полную миграцию**

## 📝 Конфигурация

### config.yaml:
```yaml
migration:
  logging:
    level: INFO
  databases:
    mssql:
      host: localhost
      port: 1433
      database: fish_eye_mcl
      user: sa
      password: password
    postgres:
      host: localhost
      port: 5432
      database: femcl
      user: postgres
      password: password
```

## 🚀 Использование

### Миграция таблицы:
```bash
python3 src/scripts/migrate_table.py <table_name> [--force] [--verbose]
```

### Пример:
```bash
python3 src/scripts/migrate_table.py accnt --force --verbose
```

## 🔗 Связанные документы

### 🏗️ Архитектура системы
- **[MODULE_ARCHITECTURE.md](../architecture/MODULE_ARCHITECTURE.md)** - Детальная архитектура модулей
- **[SYSTEM_DESIGN.md](../architecture/SYSTEM_DESIGN.md)** - Дизайн системы (планируется)

### 🔧 Система маппинга функций
- **[FUNCTION_MAPPING_SYSTEM.md](../migration/FUNCTION_MAPPING_SYSTEM.md)** - Система маппинга функций MS SQL → PostgreSQL

### 🚨 Обработка ошибок
- **[ERROR_HANDLING.md](../development/ERROR_HANDLING.md)** - Обработка ошибок и восстановление

### 📊 Критерии успеха
- **[CRITERIA_SUCCESS.md](../development/CRITERIA_SUCCESS.md)** - Критерии успеха миграции



