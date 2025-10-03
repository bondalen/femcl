# 📚 СТРУКТУРА ПРОЕКТНОЙ ДОКУМЕНТАЦИИ FEMCL

## 🎯 Иерархия документов

```
docs/project/
├── overview/                    # Обзор проекта
│   ├── README.md               # Главная страница проекта
│   ├── PROJECT_CONCEPT.md      # Основной замысел проекта
│   ├── MIGRATION_ALGORITHM.md  # Детальный алгоритм миграции
│   ├── ARCHITECTURE.md         # Архитектура системы
│   ├── PROJECT_JOURNAL.md      # Дневник проекта
│   ├── CHANGELOG.md            # Журнал изменений
│   └── DOCUMENTATION_STRUCTURE.md # Этот документ
│
├── architecture/               # Архитектура системы
│   ├── MODULE_ARCHITECTURE.md  # Архитектура модулей
│   ├── SYSTEM_DESIGN.md        # Дизайн системы (планируется)
│   └── INTEGRATION_PATTERNS.md # Паттерны интеграции (планируется)
│
├── migration/                  # Миграция данных
│   ├── DATABASE_SCHEMA.md      # Схема базы данных
│   ├── MIGRATION_STRATEGY.md   # Стратегия миграции
│   ├── TRIGGER_MIGRATION_STRATEGY.md # Стратегия миграции триггеров
│   └── FUNCTION_MAPPING_SYSTEM.md # Система маппинга функций
│
└── development/                # Разработка
    ├── ERROR_HANDLING.md       # Обработка ошибок
    ├── CRITERIA_SUCCESS.md     # Критерии успеха
    ├── TECHNICAL_IMPLEMENTATION.md # Техническая реализация (планируется)
    └── TESTING_STRATEGY.md     # Стратегия тестирования (планируется)
```

## 🔗 Система ссылок

### 📊 **overview/** - Обзор проекта

#### **PROJECT_CONCEPT.md** (Основной замысел)
- **Ссылается на:**
  - `MIGRATION_ALGORITHM.md` - детальный алгоритм выполнения
  - `MODULE_ARCHITECTURE.md` - архитектура системы
  - `FUNCTION_MAPPING_SYSTEM.md` - система маппинга функций
  - `MIGRATION_STRATEGY.md` - стратегия миграции

#### **MIGRATION_ALGORITHM.md** (Алгоритм миграции)
- **Ссылается на:**
  - `MODULE_ARCHITECTURE.md` - архитектура модулей
  - `FUNCTION_MAPPING_SYSTEM.md` - система маппинга функций
  - `ERROR_HANDLING.md` - обработка ошибок

#### **ARCHITECTURE.md** (Архитектура системы)
- **Ссылается на:**
  - `MODULE_ARCHITECTURE.md` - детальная архитектура модулей
  - `FUNCTION_MAPPING_SYSTEM.md` - система маппинга функций

### 🏗️ **architecture/** - Архитектура системы

#### **MODULE_ARCHITECTURE.md** (Архитектура модулей)
- **Ссылается на:**
  - `MIGRATION_ALGORITHM.md` - алгоритм миграции
  - `TECHNICAL_IMPLEMENTATION.md` - техническая реализация
  - `../../operations/rules/single_table/` - правила миграции таблиц

### 🔄 **migration/** - Миграция данных

#### **MIGRATION_STRATEGY.md** (Стратегия миграции)
- **Ссылается на:**
  - `MIGRATION_ALGORITHM.md` - алгоритм выполнения
  - `MODULE_ARCHITECTURE.md` - архитектура модулей
  - `TRIGGER_MIGRATION_STRATEGY.md` - стратегия миграции триггеров
  - `FUNCTION_MAPPING_SYSTEM.md` - система маппинга функций

#### **FUNCTION_MAPPING_SYSTEM.md** (Система маппинга функций)
- **Ссылается на:**
  - `../../operations/rules/function_mapping/` - правила маппинга
  - `TECHNICAL_IMPLEMENTATION.md` - техническая реализация

### 🚀 **development/** - Разработка

#### **ERROR_HANDLING.md** (Обработка ошибок)
- **Ссылается на:**
  - `MIGRATION_ALGORITHM.md` - алгоритм миграции
  - `../../operations/procedures/ERROR_RECOVERY.md` - процедуры восстановления

#### **CRITERIA_SUCCESS.md** (Критерии успеха)
- **Ссылается на:**
  - `MIGRATION_ALGORITHM.md` - алгоритм миграции
  - `../../operations/progress/README.md` - мониторинг прогресса

## 🎯 Принципы организации

### 1. **Иерархическая структура**
- **overview/** - общие концепции и замысел
- **architecture/** - архитектурные решения
- **migration/** - специфика миграции данных
- **development/** - детали разработки

### 2. **Система ссылок**
- Каждый документ ссылается на связанные документы
- Ссылки организованы по уровням детализации
- Перекрестные ссылки между разделами

### 3. **Разделение ответственности**
- **Концепция** → **Архитектура** → **Реализация**
- **Общее** → **Специфичное**
- **Планирование** → **Выполнение** → **Контроль**

### 4. **Навигация**
- Главная страница проекта: `overview/README.md`
- Быстрый доступ к ключевым документам
- Поиск по ключевым словам

## 📋 План реализации

### Этап 1: Создание новых документов
1. ✅ `MIGRATION_ALGORITHM.md` - алгоритм миграции
2. ✅ `MODULE_ARCHITECTURE.md` - архитектура модулей
3. ✅ `FUNCTION_MAPPING_SYSTEM.md` - система маппинга функций
4. ✅ `ERROR_HANDLING.md` - обработка ошибок
5. ✅ `CRITERIA_SUCCESS.md` - критерии успеха

### Этап 2: Обновление существующих документов
1. ✅ `PROJECT_CONCEPT.md` - добавление ссылок
2. ✅ `ARCHITECTURE.md` - добавление ссылок
3. ✅ `MIGRATION_STRATEGY.md` - добавление ссылок

### Этап 3: Создание системы ссылок
1. ✅ `DOCUMENTATION_STRUCTURE.md` - этот документ
2. ✅ Обновление `README.md` файлов
3. ✅ Добавление перекрестных ссылок

### Этап 4: Очистка
1. 🔄 Удаление `COMPLETE_MIGRATION_RULES.md`
2. 🔄 Проверка всех ссылок
3. 🔄 Валидация структуры

## 🎯 Результат

После реализации:
- ✅ Проектные решения вынесены из операционных правил
- ✅ Создана иерархическая структура документации
- ✅ Настроена система ссылок между документами
- ✅ Упрощена навигация по проекту
- ✅ Разделены концепция, архитектура и реализация
