# SQL скрипты для системы конвертации функций

**Дата создания:** 2025-10-07  
**Чат:** Функции в колонках  
**Принцип:** metadataFirst  

---

## 📋 Описание

Скрипты для создания нормализованной системы конвертации функций MS SQL → PostgreSQL через наследование таблиц.

**Архитектура:**
```
function_conversions (родитель - 11 полей)
├── column_function_conversions (column_id FK)
├── default_constraint_function_conversions (constraint_id FK)
├── check_constraint_function_conversions (constraint_id FK)
└── index_function_conversions (index_id FK + специфичные)
```

---

## 📁 Файлы

### 00_run_all.sql
Мастер-скрипт, выполняет все скрипты в правильном порядке.

**Использование:**
```bash
psql -U postgres -d fish_eye -f 00_run_all.sql
```

### 01_create_parent_table.sql
Создание родительской таблицы `function_conversions`.

**Содержит:**
- 11 полей (source_definition, target_definition, mapping_*, manual_*)
- 5 индексов для оптимизации
- 8 статусов конвертации
- Полные комментарии

### 02_create_child_tables.sql
Создание 4 дочерних таблиц через INHERITS.

**Таблицы:**
- column_function_conversions
- default_constraint_function_conversions
- check_constraint_function_conversions
- index_function_conversions

**Каждая содержит:** ТОЛЬКО FK связь + наследуемые 11 полей

### 03_migrate_existing_data.sql
Миграция существующих данных из текущих полей.

**Источники:**
- postgres_columns (67 вычисляемых колонок)
- postgres_default_constraints (~49 ограничений)
- postgres_check_constraints (~31 ограничение)
- postgres_indexes (если есть данные)

### 04_create_views.sql
Создание представлений для удобного доступа.

**Представления:**
- v_function_conversions_typed - с типом объекта
- v_function_conversions_full - полная информация + имена объектов

---

## 🚀 Быстрый старт

```bash
cd /home/alex/projects/sql/femcl/database/sql/function_conversions
psql -U postgres -d fish_eye -f 00_run_all.sql
```

---

## ✅ Результат выполнения

После выполнения будет создано:
- 5 таблиц (1 родитель + 4 наследника)
- 2 представления
- Мигрированы существующие данные (~67 колонок)

---

**Автор:** Система FEMCL  
**Документация:** docs/project/project-docs.json → database.controlSchema.functionConversion
