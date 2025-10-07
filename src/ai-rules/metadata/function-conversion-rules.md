# Правила конвертации функций для AI-ассистента

**Версия:** 1.0.0  
**Дата создания:** 2025-10-07  
**Применяется:** Стадия 02.01 (Формирование метаданных)  
**Режим:** 🔧 РАЗРАБОТКА  

---

## 📋 ПРИНЦИП "НЕ ОПРЕДЕЛЯТЬ НА ЛЕТУ"

### Критическое правило:

> **ВСЕ имена и свойства объектов целевой БД определяются на стадии 02.01 
> (формирование метаданных), а НЕ на лету при создании объектов (02.02)**

### Что это значит:

**✅ ПРАВИЛЬНО (стадия 02.01 - метаданные):**
```python
# На стадии формирования метаданных:
UPDATE mcl.function_conversions
SET target_definition = 'ags.fn_cn_num(cn_key)',
    mapping_status = 'manual-completed'
WHERE id = 123;

# Позже на стадии 02.02 - просто ЧИТАЕМ:
SELECT target_definition FROM mcl.function_conversions WHERE id = 123;
# → 'ags.fn_cn_num(cn_key)' УЖЕ готово
```

**❌ НЕПРАВИЛЬНО (на лету при создании):**
```python
# На стадии 02.02 - НЕЛЬЗЯ определять функцию:
# НЕЛЬЗЯ: if has_computed_column: create_postgres_function(...)
# ВСЕ функции УЖЕ должны быть определены на стадии 02.01
```

### Обоснование:

- **Предсказуемость:** Все функции известны заранее
- **Валидация:** Можно проверить корректность до создания в БД
- **Отладка:** Легче найти и исправить ошибки в метаданных
- **Повторяемость:** Гарантия идентичных результатов
- **Прозрачность:** Весь код доступен для review

---

## 🗄️ АРХИТЕКТУРА ХРАНЕНИЯ

### Таблицы конвертации (наследование):

```
function_conversions (РОДИТЕЛЬ)
├── source_definition        ← Исходная функция (MS SQL)
├── target_definition        ← Преобразованная (PostgreSQL)
├── mapping_rule_id          ← FK к правилам
├── mapping_status           ← Статус обработки
├── mapping_complexity       ← Уровень сложности
├── mapping_notes            ← Заметки
├── manual_developer         ← Кто разрабатывает вручную
├── manual_started_at        ← Начало ручной работы
├── manual_completed_at      ← Завершение
└── created_at, updated_at

НАСЛЕДНИКИ (ТОЛЬКО FK связь):
├── column_function_conversions (column_id FK)
├── default_constraint_function_conversions (constraint_id FK)
├── check_constraint_function_conversions (constraint_id FK)
└── index_function_conversions (index_id FK + специфичные)
```

### Связи:

```
function_mapping_rules (18 правил)
        ↓ FK
function_conversions (родитель - ВСЯ логика обработки)
        ↓ INHERITS
column_function_conversions → postgres_columns (вычисляемые колонки)
default_constraint_function_conversions → postgres_default_constraints
check_constraint_function_conversions → postgres_check_constraints
index_function_conversions → postgres_indexes
```

**Преимущество:** source_definition и target_definition в РОДИТЕЛЬСКОЙ таблице
→ Стандартная обработка для ВСЕХ типов объектов одинакова!

---

## 🔄 ПРОЦЕСС КОНВЕРТАЦИИ

### Два режима работы:

#### 1. Автоматическая конвертация (02.01.01)

**Когда:** Простые функции с правилами в `function_mapping_rules`

**Процесс:**
```python
from metadata.classes import FunctionConverter

converter = FunctionConverter(connection_manager)

# Обработать все pending
report = converter.convert_all_automatic(task_id=2)

# Результат:
#   automatic-mapped: 42 функции
#   manual-required: 25 функций
#   automatic-error: 0
```

**Что делает:**
- Загружает правила из `function_mapping_rules`
- Применяет к `source_definition`
- Записывает результат в `target_definition` (родительская таблица!)
- Устанавливает `mapping_status = 'automatic-mapped'`
- Связывает с `mapping_rule_id`

**НЕ требует участия AI** - работает автоматически

---

#### 2. Ручная разработка функций (02.01.02 + 02.01.03)

**Когда:** 
- Кастомные функции `[ags].*` (13 функций)
- Сложные конструкции без правил (12 функций)
- Ошибки автоматической конвертации

**Процесс (ДЕТАЛЬНО):**

##### Шаг 1: Получить список функций для ручной работы

```python
# После автоматической конвертации (02.01.01)
converter.identify_manual_functions(task_id=2)
# → Устанавливает mapping_status = 'manual-required'

# Получить список (работа с РОДИТЕЛЬСКОЙ таблицей)
cursor.execute('''
    SELECT 
        fc.id,
        fc.source_definition,
        fc.mapping_notes
    FROM mcl.function_conversions fc
    WHERE fc.mapping_status = 'manual-required'
    ORDER BY fc.id
''')

manual_list = cursor.fetchall()
print(f"Функций для ручной разработки: {len(manual_list)}")
```

##### Шаг 2: Начать работу над функцией

```python
# Выбрать функцию
conversion_id = manual_list[0][0]
source_def = manual_list[0][1]

print(f"Работаю над функцией #{conversion_id}")
print(f"Исходная: {source_def}")

# ОБЯЗАТЕЛЬНО: Пометить начало работы
converter.start_manual(
    conversion_id=conversion_id,
    developer='AI-Assistant'
)

# Статус меняется:
# manual-required → manual-in-progress
# + manual_developer = 'AI-Assistant'
# + manual_started_at = NOW()
```

##### Шаг 3: Анализ исходной функции

```python
# Пример: ([ags].[fnCnNum]([cn_key]))

# Шаг 3.1: Получить определение функции из MS SQL
ms_conn = connection_manager.get_mssql_connection()
cursor_ms = ms_conn.cursor()

cursor_ms.execute('''
    SELECT sm.definition
    FROM sys.sql_modules sm
    JOIN sys.objects o ON sm.object_id = o.object_id
    WHERE o.schema_id = SCHEMA_ID('ags')
      AND o.name = 'fnCnNum'
      AND o.type IN ('FN', 'IF', 'TF')
''')

func_definition = cursor_ms.fetchone()
if func_definition:
    print("Определение MS SQL функции:")
    print(func_definition[0])

# Шаг 3.2: Анализ логики
# - Что делает функция?
# - Какие параметры?
# - Какой результат?
# - Есть ли зависимости от других функций/таблиц?
```

##### Шаг 4: Разработка PostgreSQL решения

**Вариант A: Создать PostgreSQL функцию**
```sql
CREATE OR REPLACE FUNCTION ags.fn_cn_num(p_cn_key INTEGER)
RETURNS VARCHAR(20) AS $$
BEGIN
    RETURN (SELECT cn_num FROM ags.cn WHERE cn_key = p_cn_key);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Целевое выражение для колонки:
target_expression = 'ags.fn_cn_num(cn_key)'
```

**Вариант B: Inline SQL (подзапрос)**
```sql
-- Без создания функции, прямой подзапрос:
target_expression = '(SELECT cn_num FROM ags.cn c WHERE c.cn_key = cn.cn_key)'
```

**Выбор варианта:**
- Вариант A: если функция используется многократно
- Вариант B: если функция простая и используется 1-2 раза

##### Шаг 5: Тестирование синтаксиса

```python
# Проверить синтаксис PostgreSQL
test_sql = f'''
    SELECT {target_expression}
    FROM ags.cn
    LIMIT 1
'''

try:
    cursor.execute(test_sql)
    result = cursor.fetchone()
    print(f"✅ Синтаксис корректен, результат: {result}")
except Exception as e:
    print(f"❌ Ошибка синтаксиса: {e}")
    # Исправить и повторить тест
```

##### Шаг 6: Сохранение результата

```python
# Обновить function_conversions (РОДИТЕЛЬСКАЯ таблица)
cursor.execute('''
    UPDATE mcl.function_conversions
    SET target_definition = %s,
        mapping_notes = %s,
        updated_at = NOW()
    WHERE id = %s
''', [
    target_expression,
    'Ручная разработка: создана PostgreSQL функция ags.fn_cn_num',
    conversion_id
])

print("✅ Результат сохранен в function_conversions.target_definition")
```

##### Шаг 7: Завершение работы

```python
# ОБЯЗАТЕЛЬНО: Пометить завершение
converter.complete_manual(
    conversion_id=conversion_id,
    target_definition=target_expression  # Для валидации
)

# Статус меняется:
# manual-in-progress → manual-completed
# + manual_completed_at = NOW()

print("✅ Функция готова к использованию на стадии 02.02")
```

---

## 📋 ПРАВИЛА ДЛЯ AI-АССИСТЕНТА

### Правило 1: ВСЕГДА начинать с start_manual()

**ОБЯЗАТЕЛЬНО** перед началом работы:
```python
converter.start_manual(conversion_id, developer='AI-Assistant')
```

**Зачем:**
- Защита от одновременной автоматической обработки
- Отслеживание кто и когда начал работу
- Прозрачность процесса
- Возможность продолжить работу после прерывания

### Правило 2: Работать как с обычным кодом

**Процесс разработки функции = процесс разработки обычного кода:**

1. **Анализ требований:** Что делает исходная функция?
2. **Проектирование:** Как реализовать в PostgreSQL?
3. **Разработка:** Написать PostgreSQL код
4. **Тестирование:** Проверить синтаксис и логику
5. **Документирование:** Описать решение в mapping_notes
6. **Коммит:** Сохранить в target_definition

### Правило 3: ВСЕГДА тестировать синтаксис

Перед сохранением результата:
```python
# Обязательный тест синтаксиса
test_sql = f"SELECT {target_expression} FROM ... LIMIT 1"
cursor.execute(test_sql)
```

**Если ошибка:**
- Исправить код
- Повторить тест
- Сохранить только ВАЛИДНЫЙ PostgreSQL код

### Правило 4: ВСЕГДА завершать с complete_manual()

**ОБЯЗАТЕЛЬНО** после завершения работы:
```python
converter.complete_manual(conversion_id, target_definition)
```

**Что делает:**
- Валидирует наличие target_definition
- Проверяет синтаксис PostgreSQL (опционально)
- Устанавливает статус: manual-completed
- Фиксирует время завершения: manual_completed_at = NOW()

### Правило 5: НЕ трогать чужие функции в работе

**Проверка перед началом:**
```python
cursor.execute('''
    SELECT manual_developer, manual_started_at
    FROM mcl.function_conversions
    WHERE id = %s AND mapping_status = 'manual-in-progress'
''', [conversion_id])

result = cursor.fetchone()
if result and result[0] != 'AI-Assistant':
    print(f"⚠️ Функция уже в работе у {result[0]} с {result[1]}")
    # НЕ начинать работу
```

### Правило 6: Документировать решение

**В mapping_notes описать:**
- Какое решение выбрано (функция / inline SQL)
- Почему именно так
- Особенности реализации
- Проблемы и их решения

**Пример:**
```python
mapping_notes = '''
Ручная разработка: создана PostgreSQL функция ags.fn_cn_num
Решение: Вариант A (функция вместо inline SQL)
Причина: Функция используется в 2 колонках
Реализация: Простой SELECT из ags.cn
Протестировано: синтаксис корректен
'''
```

---

## ✅ ВАЛИДАЦИЯ ПЕРЕД СТАДИЕЙ 02.02

### Критично перед переходом к 02.02:

**Проверка готовности всех функций (02.01.04):**

```python
from metadata.classes import MetadataTransformer

transformer = MetadataTransformer(connection_manager)
report = transformer.validate_all_functions(task_id=2)

# Проверки:
assert report.pending_count == 0, "Есть необработанные функции"
assert report.manual_in_progress_count == 0, "Есть незавершенные ручные разработки"
assert report.error_count == 0, "Есть ошибки конвертации"
assert report.ready_count == report.total_count, "Не все функции готовы"

print("✅ Все функции преобразованы, готовы к стадии 02.02")
```

**Критерии готовности:**
1. ✅ Все функции: `mapping_status IN ('automatic-mapped', 'manual-completed', 'skipped')`
2. ✅ `target_definition IS NOT NULL` для всех (кроме skipped)
3. ✅ Нет записей в статусе `manual-in-progress`
4. ✅ Синтаксис PostgreSQL валиден
5. ✅ Все связи `function_conversion_id` корректны

**Если не готово:**
- ❌ ОСТАНОВИТЬ переход к стадии 02.02
- 📊 Показать отчет: какие функции не готовы
- 🔧 Завершить ручные разработки
- ✅ Повторить валидацию

---

## 🚀 РЕЖИМ ЭКСПЛУАТАЦИИ vs РАЗРАБОТКА

### 🔧 РЕЖИМ РАЗРАБОТКИ (текущий)

**На стадии 02.01:**
- ✅ AI разрабатывает функции (automatic + manual)
- ✅ AI работает с `function_conversions.target_definition`
- ✅ AI использует `start_manual()` / `complete_manual()`
- ✅ AI тестирует и документирует

**На стадии 02.02:**
- ✅ AI ЧИТАЕТ готовые функции из `target_definition`
- ✅ AI ПРИМЕНЯЕТ функции при создании объектов
- ❌ AI НЕ создает функции на лету

### 🚀 РЕЖИМ ЭКСПЛУАТАЦИИ

**Предусловие:**
- ВСЕ функции УЖЕ преобразованы на стадии 02.01
- `function_conversions` заполнена (automatic + manual)
- Статусы: automatic-mapped OR manual-completed

**Действия AI:**
- ✅ Только ЧТЕНИЕ из `target_definition`
- ✅ Применение готовых метаданных
- ❌ НЕ разрабатывать функции
- ❌ НЕ изменять `function_conversions`

**Проверка:**
```python
# В режиме эксплуатации это ДОЛЖНО быть True:
cursor.execute('''
    SELECT COUNT(*) = 0 as all_ready
    FROM mcl.function_conversions
    WHERE mapping_status NOT IN ('automatic-mapped', 'manual-completed', 'skipped')
''')
assert cursor.fetchone()[0], "Не все функции готовы!"
```

---

## 📊 ПРИМЕРЫ РАБОТЫ

### Пример 1: Автоматическая конвертация

```python
# Функция: ISNULL([column], 0)
# Есть правило: isnull → COALESCE

converter = FunctionConverter(manager)
result = converter.convert_automatic(conversion_id=45)

# Результат:
# source_definition: ISNULL([iuplpM01], 0)
# target_definition: COALESCE(iuplp_m01, 0)
# mapping_status: automatic-mapped
# mapping_rule_id: 2
```

### Пример 2: Ручная разработка кастомной функции

```python
# Функция: ([ags].[fnCnNum]([cn_key]))
# Нет правила → manual-required

# Шаг 1: Начало
converter.start_manual(conversion_id=9, developer='AI-Assistant')

# Шаг 2: Анализ исходной функции в MS SQL
cursor_ms.execute("SELECT definition FROM sys.sql_modules WHERE object_id = OBJECT_ID('ags.fnCnNum')")
# Результат: Функция возвращает cn_num по cn_key

# Шаг 3: Разработка PostgreSQL функции
postgres_function = '''
CREATE OR REPLACE FUNCTION ags.fn_cn_num(p_cn_key INTEGER)
RETURNS VARCHAR(20) AS $$
BEGIN
    RETURN (SELECT cn_num FROM ags.cn WHERE cn_key = p_cn_key);
END;
$$ LANGUAGE plpgsql IMMUTABLE;
'''

# Создать функцию в БД
cursor.execute(postgres_function)

# Шаг 4: Целевое выражение для колонки
target_expression = 'ags.fn_cn_num(cn_key)'

# Шаг 5: Тестирование
test_sql = f"SELECT {target_expression} FROM ags.cn LIMIT 1"
cursor.execute(test_sql)
result = cursor.fetchone()
print(f"✅ Тест пройден: {result}")

# Шаг 6: Завершение
converter.complete_manual(
    conversion_id=9,
    target_definition='ags.fn_cn_num(cn_key)'
)

# Результат в БД:
# target_definition: ags.fn_cn_num(cn_key)
# mapping_status: manual-completed
# manual_completed_at: 2025-10-07 12:30:00
```

### Пример 3: Сложная конструкция CASE WHEN

```python
# Функция: CASE WHEN [col] IS NULL THEN 'X' ELSE [col] END
# Правила есть, но сложная → manual-required

converter.start_manual(conversion_id=15, developer='AI-Assistant')

# Анализ: Замена NULL на строку 'X'
# Решение: Использовать COALESCE + NULLIF
target_expression = "COALESCE(NULLIF(col_name, ''), 'X')"

# Тест
cursor.execute(f"SELECT {target_expression} FROM test_table LIMIT 1")

# Завершение
converter.complete_manual(conversion_id=15, target_definition=target_expression)
```

---

## 🔍 ДИАГНОСТИКА И МОНИТОРИНГ

### Получить статистику:

```sql
SELECT 
    mapping_status,
    COUNT(*) as count
FROM mcl.function_conversions
GROUP BY mapping_status
ORDER BY count DESC;
```

### Найти незавершенные ручные разработки:

```sql
SELECT 
    fc.id,
    fc.source_definition,
    fc.manual_developer,
    fc.manual_started_at,
    NOW() - fc.manual_started_at as duration
FROM mcl.function_conversions fc
WHERE fc.mapping_status = 'manual-in-progress'
ORDER BY fc.manual_started_at;
```

### Найти функции требующие внимания:

```sql
SELECT 
    fc.id,
    fc.source_definition,
    fc.mapping_status,
    fc.mapping_notes
FROM mcl.function_conversions fc
WHERE fc.mapping_status IN ('manual-required', 'automatic-error', 'validation-failed')
ORDER BY fc.id;
```

### Проверить готовность для task_id:

```sql
-- Через представление v_function_conversions_full
SELECT 
    task_id,
    mapping_status,
    COUNT(*) as count
FROM mcl.v_function_conversions_full
WHERE task_id = 2
GROUP BY task_id, mapping_status;
```

---

## 🎯 ЧЕКЛИСТ РАЗРАБОТКИ ФУНКЦИИ

**Для каждой функции в ручной разработке:**

- [ ] 1. Получить conversion_id из списка manual-required
- [ ] 2. Вызвать converter.start_manual(conversion_id, 'AI-Assistant')
- [ ] 3. Проверить статус → manual-in-progress
- [ ] 4. Получить определение из MS SQL (если нужно)
- [ ] 5. Проанализировать логику исходной функции
- [ ] 6. Разработать PostgreSQL решение (функция ИЛИ inline SQL)
- [ ] 7. Протестировать синтаксис: SELECT {target} FROM ... LIMIT 1
- [ ] 8. Сохранить в target_definition через UPDATE
- [ ] 9. Документировать решение в mapping_notes
- [ ] 10. Вызвать converter.complete_manual(conversion_id, target_definition)
- [ ] 11. Проверить статус → manual-completed
- [ ] 12. Перейти к следующей функции

---

## 📚 СПРАВОЧНАЯ ИНФОРМАЦИЯ

### Таблицы БД:

```
mcl.function_conversions (РОДИТЕЛЬ)
├── Запросы видят ВСЕ записи из дочерних
├── UPDATE работает для всех типов
└── source_definition, target_definition здесь

mcl.column_function_conversions (column_id FK)
mcl.default_constraint_function_conversions (constraint_id FK)
mcl.check_constraint_function_conversions (constraint_id FK)
mcl.index_function_conversions (index_id FK)
```

### Классы Python:

```python
FunctionConverter (src/code/metadata/classes/function_converter.py)
├── convert_automatic() - автоматическая обработка
├── identify_manual_functions() - поиск функций для ручной работы
├── start_manual() - начать ручную работу
├── complete_manual() - завершить ручную работу
└── _apply_rules() - применение правил маппинга

MetadataTransformer (src/code/metadata/classes/transformer.py)
├── transform_all() - полная трансформация метаданных
├── transform_functions() - только функции
└── validate_all_functions() - валидация готовности
```

### Статусы конвертации:

| Статус | Описание | Следующее действие |
|--------|----------|-------------------|
| pending | Ожидает обработки | Автоматическая конвертация |
| automatic-mapped | Автоматически преобразовано | Готово к 02.02 |
| manual-required | Требует ручной работы | start_manual() |
| manual-in-progress | Ручная разработка идет | Завершить разработку |
| manual-completed | Ручная разработка завершена | Готово к 02.02 |
| automatic-error | Ошибка автоматики | Ручная обработка |
| validation-failed | Ошибка валидации | Исправить и повторить |
| skipped | Пропущено | Готово к 02.02 |

---

## ⚠️ ВАЖНЫЕ ОГРАНИЧЕНИЯ

### 1. НЕ изменять target_definition на стадии 02.02

```python
# ❌ НЕПРАВИЛЬНО на стадии 02.02:
if computed_column:
    target_def = convert_function(source_def)  # НЕТ!
    
# ✅ ПРАВИЛЬНО на стадии 02.02:
target_def = get_from_metadata(conversion_id)  # Просто читаем
```

### 2. НЕ трогать функции других разработчиков

```python
# Проверить перед началом работы
cursor.execute('''
    SELECT manual_developer
    FROM mcl.function_conversions
    WHERE id = %s AND mapping_status = 'manual-in-progress'
''', [conversion_id])

result = cursor.fetchone()
if result and result[0] != 'AI-Assistant':
    # НЕ начинать - уже в работе у другого
    print(f"⚠️ В работе у {result[0]}")
    return
```

### 3. ВСЕГДА валидировать перед переходом к 02.02

```python
# Перед началом стадии 02.02
report = transformer.validate_all_functions(task_id=2)

if not report.is_ready:
    print("❌ НЕ готово к стадии 02.02")
    print(f"Незавершенных: {report.manual_in_progress_count}")
    print(f"Ошибок: {report.error_count}")
    # ОСТАНОВИТЬ процесс
    return False
```

---

## 📖 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

**Документация:**
- Принцип metadataFirst: `docs/project/project-docs.json` → `architecture.principles.metadataFirst`
- Стадия 02.01: `docs/project/project-docs.json` → `architecture.stages.rootStages[1].substages[0]`
- Таблицы БД: `docs/project/project-docs.json` → `database.controlSchema.functionConversion`

**Примеры:**
- `docs/journal/notes/function-conversion-final-architecture-2025-10-07.md`

---

**Документ создан:** 2025-10-07  
**Применяется на стадии:** 02.01 (Формирование метаданных)  
**Обязателен для:** AI-ассистент в режиме РАЗРАБОТКА  
**Ссылки:** .cursorrules, project-docs.json
