# Анализ функций в вычисляемых колонках

**Дата:** 2025-10-07  
**Чат:** Функции в колонках  
**Task ID:** 2  
**Режим:** 🔧 РАЗРАБОТКА

---

## 📊 Сводка по базе данных

### Подключение
- **Профиль:** Test Migration Task 2
- **PostgreSQL:** localhost:5432/fish_eye
- **MS SQL Server:** localhost:1433/FishEye

### Структура схемы MCL
- **Таблиц в схеме mcl:** 77
- **✅ function_mapping_rules:** СУЩЕСТВУЕТ

---

## 📈 Статистика метаданных (task_id=2)

### MS SQL Server (источник)
| Показатель | Количество |
|-----------|-----------|
| Таблиц | 166 |
| Колонок | 1,001 |
| Вычисляемых колонок | **67** |
| Таблиц с вычисляемыми колонками | **32** |

### PostgreSQL (целевая БД)
| Показатель | Количество |
|-----------|-----------|
| Записей postgres_tables (через source_table_id) | **166** |
| Записей postgres_columns (через source_table_id) | **1,001** |
| Вычисляемых колонок в postgres_columns | **67** |

**✅ Метаданные созданы через source_table_id**
**⚠️ Преобразование функций: НЕ выполнено (target_def = source_def)**

---

## 🔧 Правила маппинга функций

### Таблица function_mapping_rules

**Структура:**
- `id` (integer, NOT NULL) - PK
- `source_function` (varchar, NOT NULL) - Функция MS SQL
- `target_function` (varchar, NOT NULL) - Функция PostgreSQL
- `mapping_pattern` (text, NOT NULL) - Паттерн для поиска
- `replacement_pattern` (text, NOT NULL) - Паттерн замены
- `mapping_type` (varchar, NOT NULL) - Тип маппинга (direct/regex)
- `complexity_level` (integer) - Уровень сложности (1-3)
- `applicable_objects` (ARRAY) - Применимые объекты
- `description` (text) - Описание
- `examples` (ARRAY) - Примеры
- `is_active` (boolean) - Активность правила
- `created_at`, `updated_at` (timestamp)

**Статистика:**
- Всего правил: **18**
- Активных правил: **18**
- Неактивных правил: **0**

### Существующие правила (по сложности)

#### Уровень 1 (простые):
1. `getdate` → `NOW` (direct)
2. `isnull` → `COALESCE` (regex)
3. `len` → `LENGTH` (regex)
4. `upper` → `UPPER` (regex)
5. `lower` → `LOWER` (regex)
6. `year` → `EXTRACT` (regex)
7. `month` → `EXTRACT` (regex)
8. `day` → `EXTRACT` (regex)
9. `brackets` → `quotes` (regex)
10. `rtrim` → `RTRIM` (regex)
11. `ltrim` → `LTRIM` (regex)
12. `concat` → `CONCAT` (regex)
13. `left` → `LEFT` (regex)
14. `datepart` → `EXTRACT` (regex)

#### Уровень 2 (средние):
15. `substring` → `SUBSTRING` (regex)
16. `convert` → `CAST` (regex)
17. `dateadd` → `DATE_ADD` (regex)

#### Уровень 3 (сложные):
18. `datediff` → `DATE_PART` (regex)

---

## 🔍 Анализ использования функций

### Частота использования в вычисляемых колонках (67 колонок):

| Функция | Частота | Покрытие правилами |
|---------|---------|-------------------|
| `ISNULL` | 154 | ✅ Правило #2 |
| `CONVERT` | 16 | ✅ Правило #7 (уровень 2) |
| `Custom [ags]` | 15 | ❌ НЕТ ПРАВИЛ |
| `CASE WHEN` | 14 | ✅ Стандартный SQL |
| `CONCAT` | 9 | ✅ Правило #16 |
| `LEFT` | 3 | ✅ Правило #17 |
| `RTRIM` | 2 | ✅ Правило #14 |
| `LTRIM` | 2 | ✅ Правило #15 |

---

## 🚨 Проблемные зоны

### 1. Кастомные функции схемы [ags]

**Найдено:** 15 использований

**Примеры:**
- `[ags].[fnCnNum]([cn_key])` - формирование номера контракта
- `[ags].[fnCnName]([cn_key])` - формирование имени контракта
- `[ags].[fnCstAgPnCstName]([cstapKey])` - получение имени клиента
- `[ags].[fnCstAgPnCstName255]([cstapKey])` - имя клиента (255 символов)
- `[ags].[fnCstAgPnOgName]([cstapKey])` - получение имени организации

**Проблема:** Для этих функций нужно:
1. Получить определение функций из MS SQL
2. Создать эквивалентные функции в PostgreSQL
3. Либо заменить их выражениями/подзапросами

### 2. Сложные CASE WHEN конструкции

**Найдено:** 14 использований

**Примеры:**
```sql
CASE WHEN [ciaName] IS NULL THEN 'NullИлиПусто' 
     ELSE CASE WHEN [ciaName]='' THEN 'NullИлиПусто' 
          ELSE [ciaName] END 
END
```

**Проблема:** Требуют анализа логики для корректного переноса

### 3. Функция CONVERT с форматами

**Найдено:** 16 использований

**Примеры:**
```sql
CONVERT([nvarchar](10), [cnicgDate], (23))
CONVERT([date], '01.01.1900', (0))
```

**Проблема:** Форматы CONVERT (23, 0 и др.) требуют специальной обработки

---

## 📝 Примеры вычисляемых колонок

### Простые (покрыты правилами):

```sql
-- Таблица: cn
-- Колонка: cn_number
-- Определение: ([ags].[fnCnNum]([cn_key]))
-- Проблема: Кастомная функция
```

### Средней сложности:

```sql
-- Таблица: cnInvCmmGr
-- Колонка: cnicgNmCs
-- Определение: ((CONVERT([nvarchar](10),[cnicgDate],(23))+' ')+[cnicgName])
-- Проблема: CONVERT с форматом + конкатенация
```

### Сложные:

```sql
-- Таблица: cnInvAccnt
-- Колонка: ciaNameNull
-- Определение: (case when [ciaName] IS NULL then 'NullИлиПусто' 
--                else case when [ciaName]='' then 'NullИлиПусто' 
--                else [ciaName] end end)
-- Проблема: Вложенный CASE WHEN
```

---

## ✅ Соответствие файлов проекта и БД

### Что совпадает:

1. ✅ **Структура таблиц mcl**
   - `mssql_columns` с полями `is_computed`, `computed_definition`
   - `postgres_columns` с аналогичными полями
   - `function_mapping_rules` с полной структурой

2. ✅ **Классы в коде**
   - `ComputedColumnModel` соответствует структуре колонок
   - `FunctionMappingModel` соответствует структуре правил
   - `FunctionMappingState` для анализа состояния

3. ✅ **Метаданные MS SQL**
   - 166 таблиц
   - 1,001 колонка
   - 67 вычисляемых колонок
   - Все данные корректно загружены

### Что требует внимания:

1. ⚠️ **Метаданные скопированы БЕЗ преобразования функций**
   - postgres_tables: 166 записей (связь через source_table_id)
   - postgres_columns: 1,001 запись (связь через source_column_id)
   - Вычисляемые колонки: 67 (все со статусом "pending")
   - **Проблема:** target_def = source_def (не преобразовано!)
   - **Пример:** `([ags].[fnCnNum]([cn_key]))` скопировано как есть

2. ⚠️ **task_id не заполнен в postgres_objects**
   - postgres_tables наследует от postgres_objects
   - task_id в родительской таблице = NULL
   - Связь работает только через source_table_id

3. ⚠️ **Статус миграции таблиц**
   - pending: 164 таблицы
   - completed: 2 таблицы (account, cn)

4. ❌ **Недостаточно правил маппинга**
   - 15 использований кастомных функций [ags] без правил
   - Форматы CONVERT требуют специальных правил

---

## 🎯 Выводы и рекомендации

### Текущая ситуация:
- ✅ Инфраструктура готова (таблицы, классы, ConnectionManager)
- ✅ 18 правил маппинга базовых функций созданы
- ✅ Метаданные загружены (166 postgres_tables, 1,001 postgres_columns)
- ⚠️ **Функции НЕ преобразованы** (target_def = source_def)
- ⚠️ Миграция начата: 2 таблицы completed, 164 pending
- ❌ Кастомные функции [ags] требуют особого внимания

### Следующие шаги:

1. **Анализ кастомных функций [ags]:**
   - Извлечь определения всех функций из MS SQL
   - Проанализировать их логику
   - Создать эквиваленты в PostgreSQL или SQL-выражения

2. **Расширение правил маппинга:**
   - Добавить правила для форматов CONVERT
   - Создать правила для сложных CASE WHEN
   - Добавить правила для кастомных функций

3. **Начало миграции:**
   - Протестировать миграцию простых таблиц
   - Проверить работу существующих правил
   - Мигрировать таблицы с вычисляемыми колонками

4. **Валидация:**
   - Проверить корректность преобразований
   - Сравнить результаты с исходными данными
   - Документировать проблемы и решения

---

## 🔍 КОРРЕКТИРОВКА ПОСЛЕ ДЕТАЛЬНОЙ ПРОВЕРКИ

### Исправление первоначальной оценки:

**БЫЛО (неверно):**
- postgres_tables: 0 записей
- postgres_columns: 0 записей  
- Миграция не начата

**СТАЛО (правильно):**
- ✅ postgres_tables: **166 записей** (связь через source_table_id)
- ✅ postgres_columns: **1,001 запись** (связь через source_column_id)
- ✅ Вычисляемые колонки: **67 записей** в postgres_columns
- ⚠️ Миграция **начата**: 2 completed, 164 pending

### Ключевое открытие:

**Метаданные созданы, но функции НЕ преобразованы!**

Все 67 вычисляемых колонок в postgres_columns имеют:
- `computed_definition` (target) = исходное определение из MS SQL
- Статус: "pending"
- **Преобразование функций еще не выполнено**

**Примеры:**
```sql
-- Source (mssql_columns):
([ags].[fnCnNum]([cn_key]))

-- Target (postgres_columns):
([ags].[fnCnNum]([cn_key]))  ← НЕ ПРЕОБРАЗОВАНО!

-- Должно быть:
ags.fn_cn_num(cn_key)  ← PostgreSQL синтаксис
```

### Архитектурная особенность:

**Наследование через postgres_objects:**
- postgres_tables INHERITS FROM postgres_objects
- task_id хранится в родительской таблице
- В postgres_objects.task_id = NULL для всех записей
- Связь работает через source_table_id → mssql_tables.task_id

---

**Документ создан:** 2025-10-07  
**Документ обновлен:** 2025-10-07 (после корректировки)  
**Автор:** Система FEMCL  
**Статус:** Анализ завершен, изменений в БД не внесено

