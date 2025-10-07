# Предложение по очистке устаревших FK к function_mapping_rules

**Дата:** 2025-10-07  
**Чат:** Функции в колонках  
**Вопрос:** Нужны ли прямые связи от объектов к function_mapping_rules?  
**Статус:** Анализ без изменений

---

## 🔍 ТЕКУЩАЯ СИТУАЦИЯ

### Прямые FK (старые):

```
postgres_columns.computed_function_mapping_rule_id 
  → function_mapping_rules.id

postgres_default_constraints.function_mapping_rule_id 
  → function_mapping_rules.id

postgres_check_constraints.function_mapping_rule_id 
  → function_mapping_rules.id

postgres_indexes.function_mapping_rule_id 
  → function_mapping_rules.id
```

### Новая система (через conversions):

```
postgres_columns
  ↓ (через column_function_conversions.column_id)
postgres_column_function_conversions
  ↓ (наследует от родителя)
postgres_function_conversions.mapping_rule_id
  → function_mapping_rules.id
```

**Результат:** ДУБЛИРОВАНИЕ информации!

---

## 📊 АНАЛИЗ ДУБЛИРОВАНИЯ

### 1. postgres_columns:

```
Всего вычисляемых колонок: 67
Старое поле заполнено: 42
Новое поле заполнено: 42
Совпадают: 42
Расхождений: 0
```

**Вывод:** Данные ДУБЛИРУЮТСЯ для 42 колонок (automatic-mapped)

### 2. postgres_default_constraints:

```
Всего: 49
Старое поле заполнено: 17
Новое поле заполнено: 17
Совпадают: 17
Расхождений: 0
```

**Вывод:** Данные ДУБЛИРУЮТСЯ для 17 ограничений

### 3. postgres_check_constraints:

```
Всего: 31
Старое поле заполнено: 0
Новое поле заполнено: 0
```

**Вывод:** Поля пустые в обоих местах

---

## 💡 РЕКОМЕНДАЦИЯ: УДАЛИТЬ устаревшие FK

### Обоснование:

#### 1. Дублирование информации

**Было (старая система):**
```sql
-- Прямая связь
postgres_columns.computed_function_mapping_rule_id → function_mapping_rules.id
```

**Стало (новая система):**
```sql
-- Через conversions
postgres_columns → column_function_conversions.mapping_rule_id → function_mapping_rules.id
```

**Проблема:** Одна и та же информация в двух местах!

#### 2. Избыточные поля

**В каждой из 4 таблиц:**
```
postgres_columns:
  - computed_function_mapping_rule_id     ← ИЗБЫТОЧНО
  - computed_mapping_status               ← ИЗБЫТОЧНО
  - computed_mapping_complexity           ← ИЗБЫТОЧНО
  - computed_mapping_notes                ← ИЗБЫТОЧНО
  - postgres_computed_definition          ← Можно оставить для быстрого доступа

postgres_default_constraints:
  - function_mapping_rule_id              ← ИЗБЫТОЧНО
  - mapping_status                        ← ИЗБЫТОЧНО
  - mapping_complexity                    ← ИЗБЫТОЧНО
  - mapping_notes                         ← ИЗБЫТОЧНО
  - postgres_definition                   ← Можно оставить для быстрого доступа

(аналогично для CHECK и INDEX)
```

#### 3. Поддержка двух систем сложна

**Проблемы:**
- При обновлении нужно обновлять в двух местах
- Возможна несогласованность данных
- Сложнее код (WHERE писать?)

#### 4. Новая система полнее

**Старая система:**
- Только mapping_rule_id
- Нет отслеживания ручной разработки
- Нет истории конвертации

**Новая система:**
- mapping_rule_id
- mapping_status (8 статусов)
- manual_developer, manual_started_at, manual_completed_at
- source_definition, target_definition
- Полная история

---

## 📋 ПЛАН ОЧИСТКИ

### Вариант A: Удалить ВСЕ устаревшие поля (рекомендуется)

**Удалить из postgres_columns:**
```sql
ALTER TABLE mcl.postgres_columns
    DROP COLUMN computed_function_mapping_rule_id,
    DROP COLUMN computed_mapping_status,
    DROP COLUMN computed_mapping_complexity,
    DROP COLUMN computed_mapping_notes;
    
-- postgres_computed_definition ОСТАВИТЬ для быстрого доступа
```

**Удалить из postgres_default_constraints:**
```sql
ALTER TABLE mcl.postgres_default_constraints
    DROP COLUMN function_mapping_rule_id,
    DROP COLUMN mapping_status,
    DROP COLUMN mapping_complexity,
    DROP COLUMN mapping_notes;
    
-- postgres_definition ОСТАВИТЬ для быстрого доступа
```

**Удалить из postgres_check_constraints:**
```sql
ALTER TABLE mcl.postgres_check_constraints
    DROP COLUMN function_mapping_rule_id,
    DROP COLUMN mapping_status,
    DROP COLUMN mapping_complexity,
    DROP COLUMN mapping_notes;
    
-- postgres_definition ОСТАВИТЬ для быстрого доступа
```

**Удалить из postgres_indexes:**
```sql
ALTER TABLE mcl.postgres_indexes
    DROP COLUMN function_mapping_rule_id,
    DROP COLUMN mapping_status,
    DROP COLUMN mapping_complexity,
    DROP COLUMN mapping_notes;
    
-- postgres_definition ОСТАВИТЬ для быстрого доступа
```

**Результат:**
- Удалено 16 полей (4 × 4 таблицы)
- Оставлено 4 поля postgres_definition для быстрого доступа
- Вся информация о конвертации в postgres_function_conversions

---

### Вариант B: Оставить только postgres_definition

**Удалить метаданные о маппинге, оставить результат:**

```sql
-- Из каждой таблицы удалить:
DROP COLUMN *_function_mapping_rule_id,
DROP COLUMN *_mapping_status,
DROP COLUMN *_mapping_complexity,
DROP COLUMN *_mapping_notes;

-- ОСТАВИТЬ:
postgres_columns.postgres_computed_definition
postgres_default_constraints.postgres_definition
postgres_check_constraints.postgres_definition
postgres_indexes.postgres_definition
```

**Преимущества:**
- ✅ Быстрый доступ к результату без JOIN
- ✅ Вся метаданные конвертации в postgres_function_conversions
- ✅ Нет дублирования метаданных

**Обоснование:** `postgres_definition` - это РЕЗУЛЬТАТ, а метаданные ПРОЦЕССА в conversions

---

### Вариант C: Оставить как есть (НЕ рекомендуется)

**Обоснование:**
- ⚠️ Совместимость со старым кодом
- ⚠️ Нет необходимости JOIN для простых запросов

**Недостатки:**
- ❌ Дублирование данных
- ❌ Поддержка двух систем
- ❌ Возможна рассинхронизация

---

## ✅ РЕКОМЕНДАЦИЯ: Вариант B

**Удалить метаданные маппинга, оставить результат**

### Что удалить (4 поля из каждой таблицы):

```
postgres_columns:
  ❌ computed_function_mapping_rule_id
  ❌ computed_mapping_status
  ❌ computed_mapping_complexity
  ❌ computed_mapping_notes
  ✅ postgres_computed_definition  ← ОСТАВИТЬ!

postgres_default_constraints:
  ❌ function_mapping_rule_id
  ❌ mapping_status
  ❌ mapping_complexity
  ❌ mapping_notes
  ✅ postgres_definition  ← ОСТАВИТЬ!

postgres_check_constraints:
  ❌ function_mapping_rule_id
  ❌ mapping_status
  ❌ mapping_complexity
  ❌ mapping_notes
  ✅ postgres_definition  ← ОСТАВИТЬ!

postgres_indexes:
  ❌ function_mapping_rule_id
  ❌ mapping_status
  ❌ mapping_complexity
  ❌ mapping_notes
  ✅ postgres_definition  ← ОСТАВИТЬ!
```

### Зачем оставить postgres_definition?

**Причины:**
1. **Производительность:** Не нужен JOIN для получения результата
2. **Удобство:** Прямой доступ к преобразованной функции
3. **Использование:** При создании объектов (стадия 02.02) читаем отсюда
4. **Не дублирует процесс:** Это РЕЗУЛЬТАТ, а не метаданные процесса

**Пример использования:**
```python
# На стадии 02.02 - создание объекта
cursor.execute('''
    SELECT postgres_computed_definition
    FROM postgres_columns
    WHERE id = 123
''')
# Быстро, без JOIN!

# Если нужны метаданные процесса:
cursor.execute('''
    SELECT fc.mapping_status, fc.manual_developer, fc.created_at
    FROM postgres_column_function_conversions cfc
    JOIN postgres_function_conversions fc ON cfc.id = fc.id
    WHERE cfc.column_id = 123
''')
```

---

## 📋 SQL СКРИПТ ОЧИСТКИ

```sql
-- ============================================================================
-- Удаление устаревших полей маппинга из таблиц объектов
-- ============================================================================
-- Дата: 2025-10-07
-- Назначение: Очистка дублирующих полей после создания postgres_function_conversions
-- Оставляем: postgres_definition для быстрого доступа к результату
-- ============================================================================

-- 1. postgres_columns
ALTER TABLE mcl.postgres_columns
    DROP COLUMN IF EXISTS computed_function_mapping_rule_id,
    DROP COLUMN IF EXISTS computed_mapping_status,
    DROP COLUMN IF EXISTS computed_mapping_complexity,
    DROP COLUMN IF EXISTS computed_mapping_notes;
-- postgres_computed_definition ОСТАВЛЯЕМ!

-- 2. postgres_default_constraints
ALTER TABLE mcl.postgres_default_constraints
    DROP COLUMN IF EXISTS function_mapping_rule_id,
    DROP COLUMN IF EXISTS mapping_status,
    DROP COLUMN IF EXISTS mapping_complexity,
    DROP COLUMN IF EXISTS mapping_notes;
-- postgres_definition ОСТАВЛЯЕМ!

-- 3. postgres_check_constraints
ALTER TABLE mcl.postgres_check_constraints
    DROP COLUMN IF EXISTS function_mapping_rule_id,
    DROP COLUMN IF EXISTS mapping_status,
    DROP COLUMN IF EXISTS mapping_complexity,
    DROP COLUMN IF EXISTS mapping_notes;
-- postgres_definition ОСТАВЛЯЕМ!

-- 4. postgres_indexes
ALTER TABLE mcl.postgres_indexes
    DROP COLUMN IF EXISTS function_mapping_rule_id,
    DROP COLUMN IF EXISTS mapping_status,
    DROP COLUMN IF EXISTS mapping_complexity,
    DROP COLUMN IF EXISTS mapping_notes;
-- postgres_definition ОСТАВЛЯЕМ!

-- Итоговый отчет
DO $$ 
BEGIN
    RAISE NOTICE '✅ Удалено 16 устаревших полей (4 поля × 4 таблицы)';
    RAISE NOTICE '✅ Оставлено 4 поля postgres_definition для быстрого доступа';
    RAISE NOTICE '';
    RAISE NOTICE 'Метаданные процесса конвертации → postgres_function_conversions';
    RAISE NOTICE 'Результат конвертации → postgres_*_definition (в таблицах объектов)';
END $$;
```

---

## 📊 ИТОГОВАЯ АРХИТЕКТУРА

### БЫЛО (дублирование):

```
postgres_columns:
  - computed_definition (source)
  - postgres_computed_definition (result)
  - computed_function_mapping_rule_id (metadata)  ← ДУБЛИРУЕТ
  - computed_mapping_status (metadata)            ← ДУБЛИРУЕТ
  - computed_mapping_complexity (metadata)        ← ДУБЛИРУЕТ
  - computed_mapping_notes (metadata)             ← ДУБЛИРУЕТ

column_function_conversions:
  - source_definition (= computed_definition)
  - target_definition (= postgres_computed_definition)
  - mapping_rule_id (= computed_function_mapping_rule_id)  ← ДУБЛЬ!
  - mapping_status (= computed_mapping_status)             ← ДУБЛЬ!
  - mapping_complexity (= computed_mapping_complexity)     ← ДУБЛЬ!
  - mapping_notes (= computed_mapping_notes)               ← ДУБЛЬ!
```

### СТАЛО (после очистки):

```
postgres_columns:
  - computed_definition (source) ← ИСХОДНИК
  - postgres_computed_definition (result) ← РЕЗУЛЬТАТ (быстрый доступ)

column_function_conversions:
  - source_definition ← ПРОЦЕСС
  - target_definition ← ПРОЦЕСС
  - mapping_rule_id ← ПРОЦЕСС
  - mapping_status ← ПРОЦЕСС
  - mapping_complexity ← ПРОЦЕСС
  - mapping_notes ← ПРОЦЕСС
  - manual_* ← ПРОЦЕСС
```

**Разделение ответственности:**
- **Объекты (postgres_columns):** Исходник + Результат
- **Conversions:** Процесс конвертации + Метаданные

---

## ✅ ПРЕИМУЩЕСТВА ОЧИСТКИ

### 1. Нет дублирования
- Метаданные процесса ТОЛЬКО в postgres_function_conversions
- Результат ТОЛЬКО в postgres_definition

### 2. Единственный источник истины
- mapping_rule_id → postgres_function_conversions
- mapping_status → postgres_function_conversions
- manual_developer → postgres_function_conversions

### 3. Проще поддержка
- Обновление статуса → одно место
- Нет риска рассинхронизации
- Понятно где искать информацию

### 4. Чище структура БД
- Меньше полей
- Понятное разделение ответственности
- Нормализация

---

## 🎯 РЕКОМЕНДУЕМЫЕ ДЕЙСТВИЯ

### Шаг 1: Создать скрипт очистки

**Файл:** `database/sql/function_conversions/08_cleanup_legacy_fields.sql`

**Содержание:** DROP COLUMN для 16 устаревших полей

### Шаг 2: Синхронизировать target_definition

**Перед удалением - убедиться что данные синхронизированы:**

```sql
-- Проверить что данные совпадают
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN pc.postgres_computed_definition = cfc.target_definition THEN 1 END) as match
FROM postgres_columns pc
JOIN postgres_column_function_conversions cfc ON pc.id = cfc.column_id
WHERE pc.is_computed = true;

-- Если не совпадают - синхронизировать
UPDATE postgres_columns pc
SET postgres_computed_definition = cfc.target_definition
FROM postgres_column_function_conversions cfc
WHERE pc.id = cfc.column_id 
  AND pc.is_computed = true
  AND (pc.postgres_computed_definition IS NULL 
       OR pc.postgres_computed_definition != cfc.target_definition);
```

### Шаг 3: Удалить устаревшие поля

**Выполнить скрипт:** `08_cleanup_legacy_fields.sql`

### Шаг 4: Проверить работоспособность

**Проверки:**
- ✅ Данные сохранены в postgres_definition
- ✅ Метаданные доступны через JOIN к conversions
- ✅ Представления работают

---

## 📊 СРАВНЕНИЕ: ДО И ПОСЛЕ

### До очистки:

**postgres_columns (вычисляемые колонки):**
```
Всего полей: ~20
Из них связанных с функциями: 10
  - is_computed
  - computed_definition (source)
  - postgres_computed_definition (result)
  - computed_function_mapping_rule_id (metadata) ← УДАЛИТЬ
  - computed_mapping_status (metadata) ← УДАЛИТЬ
  - computed_mapping_complexity (metadata) ← УДАЛИТЬ
  - computed_mapping_notes (metadata) ← УДАЛИТЬ
  - data_type_migration_status
  - data_type_migration_notes
  - type_mapping_quality
```

### После очистки:

**postgres_columns (вычисляемые колонки):**
```
Полей связанных с функциями: 6 (было 10)
  - is_computed
  - computed_definition (source) ✅
  - postgres_computed_definition (result) ✅
  - data_type_migration_status
  - data_type_migration_notes
  - type_mapping_quality
```

**Экономия:** 4 поля × 4 таблицы = **16 полей меньше!**

---

## 🔄 ИСПОЛЬЗОВАНИЕ ПОСЛЕ ОЧИСТКИ

### Быстрый доступ к результату (стадия 02.02):

```python
# Прямой доступ - БЕЗ JOIN
cursor.execute('''
    SELECT postgres_computed_definition
    FROM postgres_columns
    WHERE id = 123 AND is_computed = true
''')
result = cursor.fetchone()[0]
# → 'ags.fn_cn_num(cn_key)' быстро!
```

### Доступ к метаданным процесса (если нужно):

```python
# С JOIN - когда нужна информация о процессе
cursor.execute('''
    SELECT 
        pc.postgres_computed_definition,
        fc.mapping_status,
        fc.mapping_complexity,
        fc.manual_developer,
        fc.manual_started_at,
        fmr.source_function,
        fmr.target_function
    FROM postgres_columns pc
    JOIN postgres_column_function_conversions cfc ON pc.id = cfc.column_id
    JOIN postgres_function_conversions fc ON cfc.id = fc.id
    LEFT JOIN function_mapping_rules fmr ON fc.mapping_rule_id = fmr.id
    WHERE pc.id = 123
''')
```

---

## ⚠️ ВНИМАНИЕ: Проверить код перед удалением

**Перед удалением полей проверить:**

1. **Нет ли использования в Python коде:**
```bash
grep -r "computed_function_mapping_rule_id" src/
grep -r "computed_mapping_status" src/
grep -r "function_mapping_rule_id" src/
grep -r "mapping_status" src/
```

2. **Нет ли использования в SQL скриптах:**
```bash
grep -r "computed_function_mapping_rule_id" database/
grep -r "function_mapping_rule_id" scripts/
```

3. **Обновить найденный код** перед удалением полей

---

## 🎯 ИТОГОВАЯ РЕКОМЕНДАЦИЯ

### ✅ УДАЛИТЬ 16 устаревших полей

**Что удалить:**
- `*_function_mapping_rule_id` (4 поля)
- `*_mapping_status` (4 поля)
- `*_mapping_complexity` (4 поля)
- `*_mapping_notes` (4 поля)

**Что оставить:**
- `postgres_computed_definition` ← Результат для колонок
- `postgres_definition` ← Результат для constraints/indexes
- `computed_definition` ← Исходник для колонок
- `definition` ← Исходник для constraints

**Распределение:**
- **Процесс конвертации** → `postgres_function_conversions` + дочерние
- **Результат конвертации** → `postgres_*_definition` в таблицах объектов
- **Исходные данные** → `*_definition` / `computed_definition`

---

**Документ создан:** 2025-10-07  
**Статус:** Предложение готово, удаление не выполнено  
**Рекомендация:** Вариант B - удалить метаданные, оставить результат

