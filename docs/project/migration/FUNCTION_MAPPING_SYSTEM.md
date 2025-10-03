# 🔧 СИСТЕМА МАППИНГА ФУНКЦИЙ FEMCL

## Обзор системы
Система маппинга функций обеспечивает автоматическое преобразование MS SQL Server функций в их PostgreSQL аналоги на этапе формирования метаданных.

## Ключевые компоненты

### 1. Таблица правил маппинга (`mcl.function_mapping_rules`)
- **Источник:** Исходная MS SQL Server функция (например, `getdate`, `isnull`)
- **Целевая функция:** PostgreSQL эквивалент (например, `NOW`, `COALESCE`)
- **Тип маппинга:** `direct` (прямая замена) или `regex` (регулярное выражение)
- **Применимые объекты:** `default_constraint`, `computed_column`, `check_constraint`, `index`

### 2. Интеграция с метаданными
- **`postgres_default_constraints`**: поле `function_mapping_rule_id` (FK), `postgres_definition`
- **`postgres_columns`**: поле `computed_function_mapping_rule_id` (FK), `postgres_computed_definition`
- **`postgres_check_constraints`**: поле `function_mapping_rule_id` (FK), `postgres_definition`
- **`postgres_indexes`**: поле `function_mapping_rule_id` (FK), `postgres_definition`

## Этапы применения маппинга

### Этап 1: Анализ и идентификация
1. **Сканирование метаданных** на наличие функций в определениях
2. **Классификация объектов** по типам (default constraints, computed columns, etc.)
3. **Идентификация функций** в тексте определений

### Этап 2: Применение правил
1. **Сопоставление функций** с правилами маппинга
2. **Преобразование определений** согласно правилам
3. **Обновление метаданных** с PostgreSQL определениями

### Этап 3: Валидация
1. **Проверка покрытия** всех найденных функций
2. **Валидация синтаксиса** PostgreSQL определений
3. **Статистика применения** правил маппинга

## Интеграция в алгоритм миграции

### Модификация этапа "Создание структуры таблицы"
```python
def create_table_structure_with_mapping(table_id: int, task_id: int) -> bool:
    # 1. Получение структуры с PostgreSQL определениями
    structure = get_table_structure_with_postgres_definitions(table_id, task_id)
    
    # 2. Генерация DDL с использованием postgres_definition
    ddl = generate_postgres_ddl_with_mapped_functions(structure)
    
    # 3. Создание таблицы в PostgreSQL
    return execute_postgres_ddl(ddl)
```

### Модификация этапа "Перенос данных"
```python
def migrate_table_data_with_mapping(table_id: int, task_id: int) -> bool:
    # 1. Получение структуры с маппингом
    structure = get_table_structure_with_postgres_definitions(table_id, task_id)
    
    # 2. Извлечение данных с учетом маппинга
    data = extract_data_with_function_mapping(structure)
    
    # 3. Загрузка в PostgreSQL
    return load_data_to_postgres(data)
```

## Статистика маппинга (для задачи ID=2)
- **Default constraints с getdate()**: 17 случаев → `NOW()`
- **Computed columns с isnull()**: 22 случая → `COALESCE()`
- **Computed columns с convert()**: 15 случаев → `CAST()`
- **Computed columns с year()**: 3 случая → `EXTRACT()`
- **Computed columns с month()**: 2 случая → `EXTRACT()`
- **Общее покрытие**: 59 случаев (100%)

## Функции системы маппинга

### Основные функции
- `apply_function_mapping(definition: str, rule_id: int) -> str`
- `map_default_constraints_functions(task_id: int) -> int`
- `map_computed_columns_functions(task_id: int) -> int`
- `map_check_constraints_functions(task_id: int) -> int`
- `map_indexes_functions(task_id: int) -> int`

### Вспомогательные функции
- `get_function_mapping_statistics(task_id: int) -> Dict`
- `validate_function_mapping_coverage(task_id: int) -> bool`
- `generate_mapping_report(task_id: int) -> str`

## 🎯 ПРИНЦИП НЕБЛОКИРУЮЩЕЙ МИГРАЦИИ ДЛЯ НЕЗАМАППИРОВАННЫХ ФУНКЦИЙ

**Незамаппированные вычисляемые поля НЕ БЛОКИРУЮТ полную миграцию**, поскольку:
1. **Базовые таблицы всегда создаются** (с физическими колонками)
2. **Представления создаются частично** или дорабатываются позже
3. **Структура метаданных позволяет** пост-миграционную доработку

## Трехуровневая обработка незамаппированных функций

### Уровень 1: Автоматический маппинг (80% случаев)
- Стандартные правила: `getdate→NOW`, `isnull→COALESCE`, `len→LENGTH`
- Высокая уверенность (>80%) → применяем маппинг

### Уровень 2: Полуавтоматический маппинг (15% случаев)
- Средняя уверенность (50-80%) → маппинг + валидация
- Если валидация не прошла → помечаем для ручного обзора

### Уровень 3: Ручная обработка (5% случаев)
- Низкая уверенность (<50%) → помечаем для ручной доработки
- Создаем записи в `computed_columns_mapping_issues`

## Обработка ошибок маппинга

### Типы ошибок
1. **Неизвестная функция** - функция не найдена в правилах маппинга
2. **Ошибка синтаксиса** - некорректное PostgreSQL определение
3. **Конфликт правил** - несколько правил для одной функции
4. **Незамаппированные функции** - функции требующие ручной доработки

### Стратегии восстановления
1. **Добавление нового правила** - расширение `function_mapping_rules`
2. **Ручная корректировка** - исправление определений в метаданных
3. **Создание проблемных записей** - отслеживание в `computed_columns_mapping_issues`
4. **Создание частичных представлений** - только с замаппированными полями
5. **Пост-миграционная доработка** - возможность доработки после основной миграции

## Ссылки на детали

### 🔄 Алгоритм миграции
- **[MIGRATION_ALGORITHM.md](../overview/MIGRATION_ALGORITHM.md)** - Интеграция в алгоритм миграции

### 🏗️ Архитектура системы
- **[MODULE_ARCHITECTURE.md](../architecture/MODULE_ARCHITECTURE.md)** - Архитектура модулей

### 📋 Операционные правила
- **[../../operations/rules/function_mapping/](../../operations/rules/function_mapping/)** - Правила маппинга функций

### 🚨 Обработка ошибок
- **[ERROR_HANDLING.md](../development/ERROR_HANDLING.md)** - Обработка ошибок маппинга

### 🏗️ Техническая реализация
- **[TECHNICAL_IMPLEMENTATION.md](../development/TECHNICAL_IMPLEMENTATION.md)** - Детали технической реализации (планируется)