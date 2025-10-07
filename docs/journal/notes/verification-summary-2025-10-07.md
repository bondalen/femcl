# Итоговая сводка: Сличение проекта с БД PostgreSQL

**Дата:** 2025-10-07  
**Чат:** Функции в колонках  
**Task ID:** 2  
**Режим:** 🔧 РАЗРАБОТКА

---

## ✅ ПОДТВЕРЖДЕНО: Метаданные существуют

### Связь через source_table_id и source_column_id

**postgres_tables:**
- ✅ **166 записей** (связь: source_table_id → mssql_tables.id)
- ✅ Все связаны с task_id=2 через исходные таблицы
- ⚠️ Статус: 2 completed (account, cn), 164 pending

**postgres_columns:**
- ✅ **1,001 запись** (связь: source_column_id → mssql_columns.id)
- ✅ **67 вычисляемых колонок** (is_computed=true)
- ⚠️ Все вычисляемые колонки: статус "pending"

---

## 🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Функции не преобразованы!

### Что обнаружено:

Все 67 вычисляемых колонок в `postgres_columns.computed_definition` содержат:
- **Исходный синтаксис MS SQL** (не преобразован!)
- Квадратные скобки `[table].[column]`
- Функции MS SQL: `CONVERT`, `ISNULL`
- Кастомные функции: `[ags].[fnCnNum]`

### Примеры:

| Таблица | Колонка | Source (mssql) | Target (postgres) | Статус |
|---------|---------|----------------|-------------------|--------|
| cn | cn_number | `([ags].[fnCnNum]([cn_key]))` | `([ags].[fnCnNum]([cn_key]))` | ❌ НЕ ПРЕОБРАЗОВАНО |
| cnInvCmmGr | cnicg_nm_cs | `((CONVERT([nvarchar](10),[cnicgDate],(23))+' ')+[cnicgName])` | `((CONVERT([nvarchar](10),[cnicgDate],(23))+' ')+[cnicgName])` | ❌ НЕ ПРЕОБРАЗОВАНО |

### Что должно быть:

```sql
-- MS SQL (source):
([ags].[fnCnNum]([cn_key]))

-- PostgreSQL (target, правильно):
ags.fn_cn_num(cn_key)

-- Но сейчас (неправильно):
([ags].[fnCnNum]([cn_key]))  ← Просто скопировано!
```

---

## 📊 Статистика использования функций

### В 67 вычисляемых колонках:

| Функция/Конструкция | Частота | Правила маппинга |
|---------------------|---------|------------------|
| ISNULL | 154× | ✅ Правило #2 (isnull → COALESCE) |
| CONVERT | 16× | ✅ Правило #7 (но форматы требуют доработки) |
| **[ags].fn**** | **15×** | ❌ **НЕТ ПРАВИЛ** |
| CASE WHEN | 14× | ✅ Стандартный SQL |
| CONCAT | 9× | ✅ Правило #16 |

---

## 🔧 Правила маппинга функций

### Существует: 18 активных правил

**Уровень 1 (простые):** 14 правил
- getdate → NOW, isnull → COALESCE, len → LENGTH, year/month/day → EXTRACT и др.

**Уровень 2 (средние):** 3 правила
- substring → SUBSTRING, convert → CAST, dateadd → DATE_ADD

**Уровень 3 (сложные):** 1 правило
- datediff → DATE_PART

### Недостает:

❌ **15 кастомных функций схемы [ags]:**
- fnCnNum, fnCnName, fnCstAgPnCstName, fnCstAgPnOgName и др.
- Требуют анализа определений и создания эквивалентов

---

## 🏗️ Архитектура связей

### Наследование:
```
postgres_objects (task_id хранится здесь, но = NULL)
    ↑ INHERITS
postgres_tables (source_table_id)
    ↓ связь
mssql_tables (task_id = 2)
```

### Проблема task_id:
- ⚠️ В `postgres_objects.task_id = NULL` для всех 166 записей
- ✅ Связь работает через `source_table_id`
- ⚠️ Прямой фильтр `WHERE task_id = 2` не работает

---

## ✅ Что работает корректно:

1. ✅ **Инфраструктура:**
   - ConnectionManager с connections.json
   - Таблица function_mapping_rules (18 правил)
   - Классы: ComputedColumnModel, FunctionMappingModel

2. ✅ **Метаданные MS SQL:**
   - 166 таблиц, 1,001 колонка, 67 вычисляемых колонок
   - Все корректно загружены

3. ✅ **Метаданные PostgreSQL:**
   - 166 postgres_tables, 1,001 postgres_columns
   - Связи через source_table_id/source_column_id работают

---

## ❌ Что требует действий:

1. **КРИТИЧНО:** Преобразовать функции в postgres_columns
   - 67 колонок со статусом "pending"
   - Применить правила маппинга из function_mapping_rules
   - Обновить computed_definition с MS SQL синтаксиса на PostgreSQL

2. **ВАЖНО:** Кастомные функции [ags]
   - Извлечь определения из MS SQL
   - Создать эквиваленты в PostgreSQL или SQL-выражения
   - Добавить правила в function_mapping_rules

3. **ЖЕЛАТЕЛЬНО:** Заполнить task_id в postgres_objects
   - Для корректной работы прямых фильтров
   - UPDATE postgres_objects SET task_id = (SELECT mt.task_id FROM...)

---

## 🎯 Следующие шаги

### Приоритет 1: Кастомные функции
1. Получить определения всех функций [ags].fn* из MS SQL
2. Проанализировать их логику
3. Создать PostgreSQL эквиваленты
4. Добавить правила маппинга

### Приоритет 2: Применить маппинг
1. Использовать существующие 18 правил
2. Преобразовать computed_definition в postgres_columns
3. Обновить статус с "pending" на "mapped"

### Приоритет 3: Валидация
1. Проверить синтаксис преобразованных определений
2. Протестировать на примерах
3. Документировать проблемы

---

**Статус:** Проверка завершена, изменений в БД не внесено  
**Автор:** Система FEMCL  
**Следующий шаг:** Анализ кастомных функций [ags]

