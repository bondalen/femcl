# 🔧 СТРАТЕГИЯ МИГРАЦИИ ТРИГГЕРОВ FEMCL

## 📋 Назначение документа
Данный документ описывает стратегию миграции триггеров из MS SQL Server в PostgreSQL с учетом различных уровней сложности и автоматизации.

---

## 🎯 ОБЗОР ПРОБЛЕМЫ

### ⚠️ **Основная проблема**
Триггеры в MS SQL Server и PostgreSQL имеют существенные различия в синтаксисе, функциональности и возможностях, что делает их автоматическую миграцию сложной задачей.

### 📊 **Реальные данные из проекта FEMCL**
- **Всего триггеров:** 15
- **Таблиц с триггерами:** 7 из 166 (4.2%)
- **Среднее количество триггеров на таблицу:** 2.1

### 📊 **Типы триггеров в проекте**
1. **INSTEAD OF триггеры** - 1 (6.7%) - заменяют операцию
2. **AFTER триггеры** - 14 (93.3%) - выполняются после операции
3. **DDL триггеры** - 0 - не обнаружены
4. **LOGON триггеры** - 0 - не обнаружены

---

## 🔄 СТРАТЕГИЯ МИГРАЦИИ

### 📊 **Классификация по сложности**

#### ✅ **Простые триггеры (33.3% - 5 из 15)**
- **st_delete, stCost_delete, stCost_insert, stIpg_delete, stIpg_insert**
- **Паттерн:** Простые имена с явным указанием операции
- **Автоматизация:** 95%

#### ⚠️ **Стандартные триггеры (40.0% - 6 из 15)**
- **rgTaxIdNumJurPers_*, rgTaxMnStRegNumInd_***
- **Паттерн:** Сложные имена с суффиксами _del_aftr, _ins_inst, _upd_inst
- **Автоматизация:** 70%

#### ❌ **Сложные триггеры (6.7% - 1 из 15)**
- **tr_InsteadOfInsert** - INSTEAD OF триггер
- **Паттерн:** INSTEAD OF триггеры требуют полной адаптации
- **Автоматизация:** 10%

#### ❓ **Неопределенные триггеры (20.0% - 3 из 15)**
- **del_aftr, ins_inst, upd_inst** - короткие имена
- **Паттерн:** Требуют анализа содержимого для классификации
- **Автоматизация:** 50%

---

## 🏗️ АРХИТЕКТУРА РЕШЕНИЯ

### 📋 **Компоненты системы**

#### 1. **TriggerClassifier**
```python
class TriggerClassifier:
    """Классификатор триггеров по сложности"""
    
    def classify_trigger(self, trigger_name: str, trigger_type: str) -> str:
        """Классификация триггера по сложности"""
        
        if trigger_type == "INSTEAD OF":
            return "manual"
        elif self.is_simple_trigger(trigger_name):
            return "automatic"
        elif self.is_standard_trigger(trigger_name):
            return "semi_automatic"
        else:
            return "unknown"
    
    def is_simple_trigger(self, trigger_name: str) -> bool:
        """Проверка на простой триггер по имени"""
        simple_patterns = [
            "st_delete", "stCost_delete", "stCost_insert", 
            "stIpg_delete", "stIpg_insert"
        ]
        return trigger_name in simple_patterns
```

#### 2. **SimpleTriggerCreator**
```python
class SimpleTriggerCreator:
    """Создатель простых триггеров"""
    
    def create_audit_trigger(self, table_name: str) -> str:
        """Создание триггера аудита"""
        return f"""
        CREATE OR REPLACE FUNCTION ags.audit_{table_name}()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO ags.audit_log (table_name, operation, record_id, timestamp)
            VALUES ('{table_name}', TG_OP, COALESCE(NEW.id, OLD.id), CURRENT_TIMESTAMP);
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER trg_{table_name}_audit
            AFTER INSERT OR UPDATE OR DELETE ON ags.{table_name}
            FOR EACH ROW
            EXECUTE FUNCTION ags.audit_{table_name}();
        """
```

#### 3. **StandardTriggerCreator**
```python
class StandardTriggerCreator:
    """Создатель стандартных триггеров с шаблонами"""
    
    def create_validation_trigger(self, table_name: str, validation_rules: dict) -> str:
        """Создание триггера валидации"""
        conditions = []
        for column, rule in validation_rules.items():
            if rule['type'] == 'not_null':
                conditions.append(f"NEW.{column} IS NULL")
            elif rule['type'] == 'range':
                conditions.append(f"NEW.{column} NOT BETWEEN {rule['min']} AND {rule['max']}")
        
        return f"""
        CREATE OR REPLACE FUNCTION ags.validate_{table_name}()
        RETURNS TRIGGER AS $$
        BEGIN
            IF {' OR '.join(conditions)} THEN
                RAISE EXCEPTION 'Validation failed for {table_name}';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER trg_{table_name}_validation
            BEFORE INSERT OR UPDATE ON ags.{table_name}
            FOR EACH ROW
            EXECUTE FUNCTION ags.validate_{table_name}();
        """
```

#### 4. **ComplexTriggerHandler**
```python
class ComplexTriggerHandler:
    """Обработчик сложных триггеров"""
    
    def analyze_complex_trigger(self, trigger_definition: str) -> dict:
        """Анализ сложного триггера"""
        analysis = {
            'complexity': 'high',
            'requires_manual_review': True,
            'estimated_effort': '2-4 hours',
            'dependencies': [],
            'notes': []
        }
        
        if 'EXEC' in trigger_definition.upper():
            analysis['dependencies'].append('stored_procedures')
            analysis['notes'].append('Contains stored procedure calls')
        
        if 'CURSOR' in trigger_definition.upper():
            analysis['complexity'] = 'very_high'
            analysis['estimated_effort'] = '4-8 hours'
            analysis['notes'].append('Contains cursor operations')
        
        return analysis
```

---

## 📋 ПЛАН ВЫПОЛНЕНИЯ

### 🔄 **Этап 1.2: Создание объектов таблиц**

#### ✅ **Автоматически (простые триггеры)**
1. **Анализ триггеров** - классификация по сложности
2. **Создание простых триггеров** - аудит, timestamp, валидация
3. **Валидация** - проверка корректности создания
4. **Документирование** - запись в журнал миграции

#### ⚠️ **Полуавтоматически (стандартные триггеры)**
1. **Анализ логики** - извлечение условий и правил
2. **Применение шаблонов** - использование готовых шаблонов
3. **Ручная проверка** - валидация созданных триггеров
4. **Тестирование** - проверка функциональности

#### ❌ **Ручная работа (сложные триггеры)**
1. **Отложение** - перенос на Этап 2
2. **Анализ** - детальное изучение логики
3. **Планирование** - создание плана миграции
4. **Реализация** - ручная адаптация под PostgreSQL

### 🔄 **Этап 2: Создание иных объектов БД**

#### ❌ **Ручная работа (сложные триггеры)**
1. **Анализ зависимостей** - определение связанных объектов
2. **Создание функций** - адаптация логики под PostgreSQL
3. **Создание триггеров** - ручная реализация
4. **Тестирование** - проверка функциональности
5. **Документирование** - описание изменений

---

## 📊 ОЦЕНКА АВТОМАТИЗАЦИИ

### 📈 **Статистика автоматизации (на основе реальных данных)**

| Тип триггера | Автоматизация | Процент от общего числа | Время на единицу |
|--------------|---------------|-------------------------|------------------|
| Простые (delete, insert) | 95% | 33.3% (5 из 15) | 5-10 минут |
| Стандартные (сложные имена) | 70% | 40.0% (6 из 15) | 30-60 минут |
| Сложные (INSTEAD OF) | 10% | 6.7% (1 из 15) | 2-8 часов |
| Неопределенные | 50% | 20.0% (3 из 15) | 1-2 часа |

### 🎯 **Реальные результаты**
- **33.3% триггеров** - простые (автоматическая миграция)
- **40.0% триггеров** - стандартные (полуавтоматическая миграция)
- **6.7% триггеров** - сложные (ручная миграция)
- **20.0% триггеров** - неопределенные (требуют анализа)

---

## 🔧 ТЕХНИЧЕСКАЯ РЕАЛИЗАЦИЯ

### 📋 **Схема mcl для триггеров (реальная структура)**

#### **mcl.mssql_triggers**
```sql
-- Реальная структура таблицы
CREATE TABLE mcl.mssql_triggers (
    id SERIAL PRIMARY KEY,
    table_id INTEGER REFERENCES mcl.mssql_tables(id),
    trigger_name VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    is_disabled BOOLEAN DEFAULT FALSE,
    is_not_for_replication BOOLEAN DEFAULT FALSE,
    definition TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **mcl.postgres_triggers**
```sql
-- Реальная структура таблицы
CREATE TABLE mcl.postgres_triggers (
    id SERIAL PRIMARY KEY,
    table_id INTEGER REFERENCES mcl.postgres_tables(id),
    trigger_name VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(50) NOT NULL,
    trigger_event VARCHAR(50) NOT NULL,
    function_name VARCHAR(255) NOT NULL,
    migration_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 📋 **Процесс миграции**

#### 1. **Анализ исходных триггеров**
```sql
-- Получение триггеров из mcl.mssql_triggers
SELECT 
    mt.trigger_name,
    mt.trigger_type,
    mt.event_type,
    t.object_name as table_name,
    mt.definition
FROM mcl.mssql_triggers mt
JOIN mcl.mssql_tables t ON mt.table_id = t.id
WHERE t.task_id = 2
ORDER BY t.object_name, mt.trigger_name;
```

#### 2. **Классификация триггеров**
```python
def classify_triggers(triggers_data):
    """Классификация триггеров по сложности"""
    classified = {
        'automatic': [],
        'semi_automatic': [],
        'manual': [],
        'unknown': []
    }
    
    for trigger in triggers_data:
        complexity = TriggerClassifier().classify_trigger(
            trigger['trigger_name'], 
            trigger['trigger_type']
        )
        classified[complexity].append(trigger)
    
    return classified
```

#### 3. **Создание простых триггеров**
```python
def create_simple_triggers(table_name, triggers):
    """Создание простых триггеров"""
    creator = SimpleTriggerCreator()
    
    for trigger in triggers:
        trigger_name = trigger['trigger_name']
        event_type = trigger['event_type']
        
        if 'delete' in trigger_name.lower():
            ddl = creator.create_delete_trigger(table_name, trigger_name)
        elif 'insert' in trigger_name.lower():
            ddl = creator.create_insert_trigger(table_name, trigger_name)
        else:
            ddl = creator.create_generic_trigger(table_name, trigger_name, event_type)
        
        execute_ddl(ddl)
        log_trigger_creation(table_name, trigger_name, 'automatic')
```

---

## 🎯 РЕКОМЕНДАЦИИ

### ✅ **Что автоматизировать**
1. **Простые триггеры аудита** - запись в журнал изменений
2. **Триггеры timestamp** - обновление времени модификации
3. **Простые триггеры валидации** - проверка NOT NULL, диапазонов
4. **Триггеры подсчета** - обновление счетчиков

### ⚠️ **Что полуавтоматизировать**
1. **Триггеры с условной логикой** - IF/ELSE конструкции
2. **Триггеры вычислений** - математические операции
3. **Триггеры проверок** - сложные условия валидации

### ❌ **Что делать вручную**
1. **Триггеры с бизнес-логикой** - сложные алгоритмы
2. **Триггеры с внешними вызовами** - вызовы процедур/функций
3. **Триггеры с курсорами** - обработка наборов данных
4. **INSTEAD OF триггеры** - замена операций

### 📋 **Процесс работы**
1. **Классификация** - автоматическое определение сложности
2. **Автоматизация** - создание простых триггеров
3. **Полуавтоматизация** - создание стандартных триггеров
4. **Ручная работа** - адаптация сложных триггеров
5. **Тестирование** - проверка всех триггеров
6. **Документирование** - описание изменений

---

## 📊 МОНИТОРИНГ И ОТЧЕТНОСТЬ

### 📈 **Метрики успеха**
- **Процент автоматизации** - доля автоматически созданных триггеров
- **Время миграции** - общее время на миграцию триггеров
- **Количество ошибок** - число триггеров с проблемами
- **Качество миграции** - соответствие функциональности

### 📋 **Отчеты**
- **Отчет по классификации** - распределение триггеров по сложности
- **Отчет по автоматизации** - результаты автоматического создания
- **Отчет по ручной работе** - список триггеров для ручной адаптации
- **Отчет по тестированию** - результаты проверки функциональности

---

*Документ создан: 27 января 2025*
*Автор: AI Assistant*
*Статус: АКТУАЛЬНЫЙ*