# Правила работы с подключениями к базам данных FEMCL

**Версия:** 1.0.0  
**Дата создания:** 2025-10-07  
**Последнее обновление:** 2025-10-07  
**Применяется:** Режим разработки + Режим эксплуатации  
**Автор:** Александр

---

## 📋 Содержание

1. [Принципы](#принципы)
2. [Архитектура](#архитектура)
3. [Использование ConnectionManager](#использование-connectionmanager)
4. [Правила для AI-ассистента](#правила-для-ai-ассистента)
5. [Рефакторинг существующего кода](#рефакторинг-существующего-кода)
6. [Диагностика подключений](#диагностика-подключений)
7. [Структура connections.json](#структура-connectionsjson)
8. [Режимы работы](#режимы-работы)
9. [Безопасность](#безопасность)
10. [Обработка ошибок](#обработка-ошибок)
11. [FAQ](#часто-задаваемые-вопросы)

---

## Принципы

### 🎯 Единая система подключений

- **Все подключения** (в любом режиме) используют `connections.json`
- **По умолчанию:** task_id=2 (основная тестовая задача)
- **Инструмент:** `ConnectionManager` + `ConnectionProfileLoader`

### 📁 Разделение конфигурации

| Файл | Назначение | Используется для |
|------|------------|------------------|
| `src/code/infrastructure/config/connections.json` | Профили подключений к БД | **ВСЕ подключения** (разработка + эксплуатация) |
| `src/code/infrastructure/config/config.yaml` | Общие настройки миграции | Параметры процесса (batch_size, timeout, log_level) |

**Важно:** `config.yaml` НЕ содержит параметров подключения к БД!

---

## Архитектура

### Схема работы

```
connections.json (task_id=2 по умолчанию)
    ↓
ConnectionProfileLoader (загрузка профиля)
    ↓
ConnectionManager (управление подключениями)
    ↓
Ваш код миграции
```

### Классы и их роли

| Класс | Расположение | Роль |
|-------|-------------|------|
| `ConnectionProfileLoader` | `src/code/infrastructure/classes/` | Загрузка профилей из connections.json |
| `ConnectionManager` | `src/code/infrastructure/classes/` | Управление подключениями к БД |
| `ConnectionDiagnostics` | `src/code/infrastructure/classes/` | Диагностика состояния БД |

---

## Использование ConnectionManager

### Базовое использование

```python
from src.code.infrastructure.classes import ConnectionManager

# По умолчанию task_id=2
manager = ConnectionManager()

# Получение подключений
pg_conn = manager.get_postgres_connection()
ms_conn = manager.get_mssql_connection()

# Информация о профиле
info = manager.get_connection_info()
print(f"Task ID: {info['task_id']}")
print(f"Profile: {info['profile_name']}")

# Закрытие подключений
manager.close_all_connections()
```

### Работа с разными задачами

```python
# Явное указание task_id
manager = ConnectionManager(task_id=1)

# Переключение между задачами
manager.switch_task(2)
print(f"Текущий task_id: {manager.task_id}")
```

### Использование в скриптах

```python
#!/usr/bin/env python3
"""Пример скрипта миграции"""

from src.code.infrastructure.classes import ConnectionManager

def main():
    # Инициализация (task_id=2 по умолчанию)
    manager = ConnectionManager()
    
    try:
        # Получение подключений
        pg_conn = manager.get_postgres_connection()
        ms_conn = manager.get_mssql_connection()
        
        # Ваша логика миграции
        cursor = pg_conn.cursor()
        cursor.execute("SELECT version()")
        print(cursor.fetchone())
        
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        manager.close_all_connections()

if __name__ == '__main__':
    main()
```

---

## Правила для AI-ассистента

### ✅ РАЗРЕШЕНО

```python
# 1. Использование ConnectionManager (по умолчанию)
manager = ConnectionManager()
conn = manager.get_postgres_connection()

# 2. Явное указание task_id
manager = ConnectionManager(task_id=1)

# 3. Переключение задач
manager.switch_task(2)

# 4. Получение информации о профиле
info = manager.get_connection_info()
```

### ❌ ЗАПРЕЩЕНО

```python
# 1. Прямое подключение к PostgreSQL
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='fish_eye',
    user='postgres',
    password='postgres'
)  # ❌ НЕТ!

# 2. Прямое подключение к MS SQL Server
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=FishEye;"
    "UID=sa;"
    "PWD=password;"
)  # ❌ НЕТ!

# 3. Жестко закодированные параметры
host = 'localhost'
port = 5432
dbname = 'fish_eye'
conn = psycopg2.connect(host=host, port=port, dbname=dbname)  # ❌ НЕТ!

# 4. Чтение config.yaml для подключений
with open('config.yaml') as f:
    config = yaml.safe_load(f)
conn = psycopg2.connect(**config['database']['postgres'])  # ❌ НЕТ!
```

### Обязательные требования

1. **ВСЕГДА** используй `ConnectionManager` для подключений к БД
2. **task_id=2** по умолчанию (если не указано иное)
3. **НЕ используй** прямые вызовы `psycopg2.connect()` или `pyodbc.connect()`
4. **НЕ используй** жестко закодированные параметры подключения
5. **НЕ читай** config.yaml для получения параметров подключения

---

## Рефакторинг существующего кода

### Шаги рефакторинга

1. **Найти** все прямые вызовы `psycopg2.connect()` / `pyodbc.connect()`
2. **Удалить** жестко закодированные параметры подключения
3. **Добавить** импорт `ConnectionManager`
4. **Заменить** подключения на `manager.get_*_connection()`
5. **Проверить** что используется task_id=2 по умолчанию
6. **Тестировать** измененный код

### Пример рефакторинга №1

**До (НЕПРАВИЛЬНО):**
```python
def check_database():
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        dbname='fish_eye',
        user='postgres',
        password='postgres'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mcl.mssql_tables")
    count = cursor.fetchone()[0]
    conn.close()
    return count
```

**После (ПРАВИЛЬНО):**
```python
from src.code.infrastructure.classes import ConnectionManager

def check_database():
    manager = ConnectionManager()  # task_id=2 по умолчанию
    conn = manager.get_postgres_connection()
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM mcl.mssql_tables")
        count = cursor.fetchone()[0]
        return count
    finally:
        manager.close_all_connections()
```

### Пример рефакторинга №2

**До (НЕПРАВИЛЬНО):**
```python
def migrate_table(table_name):
    # Подключение к MS SQL
    ms_conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=FishEye;"
        "UID=sa;PWD=password;"
    )
    
    # Подключение к PostgreSQL
    pg_conn = psycopg2.connect(
        host='localhost',
        dbname='fish_eye',
        user='postgres',
        password='postgres'
    )
    
    # Миграция...
    ms_conn.close()
    pg_conn.close()
```

**После (ПРАВИЛЬНО):**
```python
from src.code.infrastructure.classes import ConnectionManager

def migrate_table(table_name, task_id=2):
    manager = ConnectionManager(task_id=task_id)
    
    try:
        ms_conn = manager.get_mssql_connection()
        pg_conn = manager.get_postgres_connection()
        
        # Миграция таблицы...
        
    finally:
        manager.close_all_connections()
```

---

## Диагностика подключений

### Использование ConnectionDiagnostics

```python
from src.code.infrastructure.classes import (
    ConnectionManager,
    ConnectionDiagnostics
)

# Инициализация
manager = ConnectionManager()
diagnostics = ConnectionDiagnostics(manager)

# Проверка здоровья PostgreSQL
pg_report = diagnostics.check_postgres_health()
if pg_report['status'] == 'healthy':
    print("✅ PostgreSQL доступен")
    print(f"Версия: {pg_report['version']}")

# Проверка здоровья MS SQL Server
ms_report = diagnostics.check_mssql_health()

# Полный отчет о состоянии
full_report = diagnostics.generate_health_report()

# Красивый вывод отчета
diagnostics.print_diagnostic_report()
```

### Проверка схемы mcl

```python
# Проверка существования схемы
if diagnostics.check_schema_exists('mcl', 'postgres'):
    print("✅ Схема mcl существует")
    
    # Получение информации о схеме
    schema_info = diagnostics.get_schema_info('mcl', 'postgres')
    print(f"Таблиц в схеме: {schema_info['tables_count']}")

# Проверка таблиц метаданных
metadata_check = diagnostics.check_migration_metadata()
print(f"MS SQL таблиц: {metadata_check['mssql_tables_count']}")
print(f"PostgreSQL таблиц: {metadata_check['postgres_tables_count']}")
```

---

## Структура connections.json

### Формат профиля

```json
{
  "metadata": {
    "version": "1.0.0",
    "created": "2025-10-07",
    "description": "Профили подключений для миграции БД"
  },
  "profiles": [
    {
      "profile_id": "test_task_2",
      "name": "Test Migration Task 2",
      "task_id": 2,
      "description": "Основная тестовая задача миграции",
      "source": {
        "type": "mssql",
        "host": "localhost",
        "port": 1433,
        "database": "FishEye",
        "user": "sa",
        "password": "***",
        "driver": "ODBC Driver 17 for SQL Server",
        "options": {
          "TrustServerCertificate": "yes",
          "ConnectionTimeout": "30",
          "CommandTimeout": "300"
        }
      },
      "target": {
        "type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "fish_eye",
        "user": "postgres",
        "password": "***",
        "ssl": "prefer",
        "options": {
          "connect_timeout": "30",
          "command_timeout": "300"
        }
      },
      "active": true,
      "created": "2025-10-07",
      "last_used": null
    }
  ],
  "default_profile": "test_task_2"
}
```

### Создание нового профиля

1. **Скопировать** существующий профиль
2. **Изменить** `profile_id` и `task_id`
3. **Обновить** параметры подключений (host, database, user, password)
4. **Установить** `active: true` если нужно
5. **Обновить** `default_profile` при необходимости

### Важные поля

| Поле | Обязательное | Описание |
|------|-------------|----------|
| `profile_id` | Да | Уникальный идентификатор профиля |
| `task_id` | Да | ID задачи миграции (по умолчанию 2) |
| `name` | Да | Читаемое имя профиля |
| `source` | Да | Параметры подключения к MS SQL Server |
| `target` | Да | Параметры подключения к PostgreSQL |
| `active` | Нет | Активен ли профиль (по умолчанию true) |
| `default_profile` | Да | ID профиля по умолчанию |

---

## Режимы работы

### 🔧 Режим разработки

```python
# В режиме разработки используется connections.json
# По умолчанию task_id=2
from src.code.infrastructure.classes import ConnectionManager

manager = ConnectionManager()  # автоматически task_id=2
conn = manager.get_postgres_connection()

# Информация о подключении
info = manager.get_connection_info()
print(f"Режим: Разработка")
print(f"Task ID: {info['task_id']}")
print(f"Профиль: {info['profile_name']}")
```

### 🚀 Режим эксплуатации

```python
# В режиме эксплуатации также используется connections.json
# task_id может быть указан явно или взят из параметров миграции
from src.code.infrastructure.classes import ConnectionManager

# Явное указание task_id для продакшн миграции
manager = ConnectionManager(task_id=production_task_id)
conn = manager.get_postgres_connection()

# Информация о подключении
info = manager.get_connection_info()
print(f"Режим: Эксплуатация")
print(f"Task ID: {info['task_id']}")
print(f"Профиль: {info['profile_name']}")
```

### Вывод

**Оба режима используют одинаковый механизм подключений!**

Разница только в том, как определяется task_id:
- **Разработка:** task_id=2 по умолчанию
- **Эксплуатация:** task_id указывается явно или берется из параметров

---

## Безопасность

### Хранение паролей

⚠️ **КРИТИЧЕСКИ ВАЖНО:**

```bash
# НЕ коммитьте connections.json в Git!
# Этот файл содержит пароли к БД
```

### Настройка .gitignore

```gitignore
# Конфиденциальные конфигурации
src/code/infrastructure/config/connections.json
```

### Использование example-файлов

1. Создайте `connections.example.json` с шаблоном:

```json
{
  "profiles": [{
    "profile_id": "test_task_1",
    "task_id": 1,
    "source": {
      "password": "ЗАМЕНИТЕ_МЕНЯ"
    },
    "target": {
      "password": "ЗАМЕНИТЕ_МЕНЯ"
    }
  }]
}
```

2. Пользователь копирует и создает `connections.json`:
```bash
cp connections.example.json connections.json
# Редактирует пароли в connections.json
```

3. `connections.json` игнорируется Git'ом

---

## Обработка ошибок

### Базовая обработка

```python
from src.code.infrastructure.classes import ConnectionManager
import psycopg2
import pyodbc

try:
    manager = ConnectionManager(task_id=2)
    conn = manager.get_postgres_connection()
    
    # Ваш код...
    
except ValueError as e:
    print(f"❌ Ошибка загрузки профиля: {e}")
    print("Проверьте connections.json и убедитесь, что профиль для task_id=2 существует")
    
except psycopg2.OperationalError as e:
    print(f"❌ Ошибка подключения к PostgreSQL: {e}")
    print("Проверьте: PostgreSQL запущен? Верные учетные данные?")
    
except pyodbc.Error as e:
    print(f"❌ Ошибка подключения к MS SQL Server: {e}")
    print("Проверьте: MS SQL Server запущен? Верные учетные данные?")
    
finally:
    if 'manager' in locals():
        manager.close_all_connections()
```

### Расширенная обработка с retry

```python
import time
from src.code.infrastructure.classes import ConnectionManager

def get_connection_with_retry(max_retries=3, delay=5):
    """Получение подключения с повторными попытками"""
    for attempt in range(max_retries):
        try:
            manager = ConnectionManager()
            conn = manager.get_postgres_connection()
            return manager, conn
        except Exception as e:
            print(f"Попытка {attempt + 1}/{max_retries} не удалась: {e}")
            if attempt < max_retries - 1:
                print(f"Ожидание {delay} секунд перед следующей попыткой...")
                time.sleep(delay)
    raise ConnectionError(f"Не удалось подключиться после {max_retries} попыток")
```

---

## Часто задаваемые вопросы

### Как узнать текущий task_id?

```python
manager = ConnectionManager()
print(f"Текущий task_id: {manager.task_id}")  # Выведет: 2
```

### Как переключиться на другую задачу миграции?

```python
manager = ConnectionManager()  # task_id=2
# ... работа с task_id=2

manager.switch_task(1)  # переключение на task_id=1
# ... работа с task_id=1
```

### Как проверить доступность БД?

```python
from src.code.infrastructure.classes import ConnectionManager, ConnectionDiagnostics

manager = ConnectionManager()
diagnostics = ConnectionDiagnostics(manager)

# Проверка PostgreSQL
pg_check = diagnostics.test_postgres_connection()
if pg_check['status'] == 'success':
    print("✅ PostgreSQL доступен!")
else:
    print(f"❌ PostgreSQL недоступен: {pg_check['error']}")
```

### Где взять параметры для нового профиля?

1. Откройте `src/code/infrastructure/config/connections.example.json`
2. Скопируйте структуру профиля
3. Создайте новый профиль в `connections.json`
4. Укажите свои параметры подключения

### Можно ли использовать несколько профилей одновременно?

Да! Создайте несколько менеджеров:

```python
manager1 = ConnectionManager(task_id=1)
manager2 = ConnectionManager(task_id=2)

conn1 = manager1.get_postgres_connection()
conn2 = manager2.get_postgres_connection()
```

### Как узнать, какие профили доступны?

```python
from src.code.infrastructure.classes import ConnectionProfileLoader

loader = ConnectionProfileLoader()
profiles = loader.list_profiles()

for profile in profiles:
    print(f"Task ID: {profile['task_id']}")
    print(f"Name: {profile['name']}")
    print(f"Active: {profile['active']}")
    print("---")
```

### Что делать если забыл task_id?

```python
manager = ConnectionManager()  # По умолчанию task_id=2
info = manager.get_connection_info()
print(f"Вы работаете с task_id: {info['task_id']}")
```

---

## Связанные документы

- **Общие правила проекта:** `docs/project-documentation-rules.md`
- **Описание конфигурационных файлов:** `src/code/infrastructure/config/README.md`
- **Курсор правила:** `.cursorrules` (краткая ссылка на этот документ)

---

**Документ утвержден:** 2025-10-07  
**Следующий пересмотр:** 2026-01-07  
**Ответственный:** Александр  
**Статус:** Действующий
