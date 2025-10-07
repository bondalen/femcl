# Тесты FEMCL

**Версия:** 1.0.0  
**Дата создания:** 2025-10-07  
**Последнее обновление:** 2025-10-07  

---

## 📁 Структура

```
tests/
├── unit/                  # Юнит-тесты (без реальных БД)
│   ├── infrastructure/    # Тесты инфраструктуры
│   ├── migration/         # Тесты модуля миграции
│   └── metadata/          # Тесты модуля метаданных
│
├── integration/           # Интеграционные тесты (с БД)
│   └── test_connection_manager.py
│
├── e2e/                  # End-to-end тесты
│
├── fixtures/             # Тестовые данные и моки
│
├── conftest.py          # Pytest фикстуры
└── pytest.ini           # Настройки pytest
```

---

## 🚀 Запуск тестов

### Все тесты:
```bash
pytest tests/
```

### Только юнит-тесты:
```bash
pytest tests/unit/
```

### Только интеграционные:
```bash
pytest tests/integration/
```

### Конкретный файл:
```bash
pytest tests/integration/test_connection_manager.py
```

### С verbose выводом:
```bash
pytest tests/ -v
```

### С покрытием кода:
```bash
pytest tests/ --cov=src/code --cov-report=html
```

---

## 🏷️ Маркеры тестов

Используйте маркеры для категоризации:


### Доступные маркеры:

```python
@pytest.mark.unit              # Юнит-тест (без БД)
@pytest.mark.integration       # Интеграционный тест (с БД)
@pytest.mark.e2e              # End-to-end тест
@pytest.mark.slow             # Медленный тест
@pytest.mark.requires_mssql   # Требует MS SQL Server
@pytest.mark.requires_postgres # Требует PostgreSQL
```

### Запуск по маркерам:

```bash
# Только юнит-тесты
pytest -m unit

# Только интеграционные
pytest -m integration

# Исключить медленные тесты
pytest -m "not slow"

# Только тесты PostgreSQL
pytest -m requires_postgres
```

---

## 🔧 Fixtures

### Доступные фикстуры (из conftest.py):

| Fixture | Scope | Описание |
|---------|-------|----------|
| `connection_manager` | session | ConnectionManager для всей сессии |
| `fresh_connection_manager` | function | Новый ConnectionManager для каждого теста |
| `connection_diagnostics` | session | ConnectionDiagnostics |
| `postgres_connection` | function | Прямое подключение к PostgreSQL |
| `mssql_connection` | function | Прямое подключение к MS SQL Server |
| `task_id` | function | task_id по умолчанию (2) |

---

## 📝 Примеры тестов

### Юнит-тест (без БД):

```python
# tests/unit/infrastructure/test_function_mapping_model.py
import pytest
from infrastructure.classes import FunctionMappingModel

@pytest.mark.unit
def test_function_mapping_creation():
    """Тест создания модели маппинга"""
    mapping = FunctionMappingModel("getdate", "NOW", "direct")
    assert mapping.source_function == "getdate"
    assert mapping.target_function == "NOW"
    assert mapping.mapping_type == "direct"
```

### Интеграционный тест (с БД):

```python
# tests/integration/test_connection_manager.py
import pytest

@pytest.mark.integration
@pytest.mark.requires_postgres
def test_postgres_connection(connection_manager):
    """Тест подключения к PostgreSQL"""
    conn = connection_manager.get_postgres_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()
    assert version is not None
    cursor.close()

@pytest.mark.integration
@pytest.mark.requires_mssql
def test_mssql_connection(connection_manager):
    """Тест подключения к MS SQL Server"""
    conn = connection_manager.get_mssql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()
    assert version is not None
    cursor.close()
```

---

## 🔍 Отладка тестов

### Запуск с отладочным выводом:
```bash
pytest tests/ -v -s
```

### Запуск с pdb при ошибке:
```bash
pytest tests/ --pdb
```

### Запуск последнего упавшего теста:
```bash
pytest tests/ --lf
```

---

## 📊 Покрытие кода

### Генерация HTML отчета:
```bash
pytest tests/ --cov=src/code --cov-report=html
open htmlcov/index.html
```

### Краткий отчет в терминале:
```bash
pytest tests/ --cov=src/code --cov-report=term
```

---

## 🎯 Требования

### Для запуска тестов установите:

```bash
pip install pytest pytest-cov pytest-mock
```

### Для интеграционных тестов требуется:
- ✅ PostgreSQL (localhost:5432, БД: fish_eye)
- ✅ MS SQL Server (localhost:1433, БД: FishEye)
- ✅ Настроенный connections.json с task_id=2

---

## 📚 Связанные документы

- **Правила подключений:** `docs/infrastructure/database-connections-rules.md`
- **Конфигурация:** `src/code/infrastructure/config/README.md`
- **Проектная документация:** `docs/project-documentation-rules.md`

---

**Создан:** 2025-10-07  
**Автор:** Александр  
**Статус:** Действующий
