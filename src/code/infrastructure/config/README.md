# Конфигурационные файлы FEMCL

**Версия:** 1.0.0  
**Дата создания:** 2025-10-07  
**Последнее обновление:** 2025-10-07  

---

## 📋 Файлы конфигурации

### 1. `connections.json` 🔐

**Назначение:** Профили подключений к базам данных

**Используется для:**
- Все подключения к MS SQL Server и PostgreSQL
- В режиме разработки (task_id=2 по умолчанию)
- В режиме эксплуатации (task_id указывается явно)

**⚠️ БЕЗОПАСНОСТЬ:**
- Содержит пароли к БД
- **НЕ коммитьте** этот файл в Git!
- Используйте `connections.example.json` как шаблон

**Структура:**
```json
{
  "metadata": { ... },
  "profiles": [
    {
      "profile_id": "test_task_2",
      "task_id": 2,
      "source": { ... },  // MS SQL Server
      "target": { ... }   // PostgreSQL
    }
  ],
  "default_profile": "test_task_2"
}
```

**Документация:** См. `docs/infrastructure/database-connections-rules.md`

---

### 2. `config.yaml` ⚙️

**Назначение:** Общие настройки миграции

**Используется для:**
- Параметры процесса миграции (batch_size, timeout)
- Настройки проверки готовности
- Параметры мониторинга
- GitHub синхронизация
- Логирование

**НЕ содержит:**
- Параметров подключения к БД (они в connections.json)

**Основные разделы:**
```yaml
migration:
  batch_size: 1000
  timeout: 300
  log_level: INFO

readiness_check:
  min_readiness_percentage: 95

monitoring:
  track_execution_time: true

security:
  encrypt_passwords: true
```

---

### 3. `connections.example.json` 📝

**Назначение:** Шаблон для создания connections.json

**Использование:**
```bash
cp connections.example.json connections.json
# Отредактируйте connections.json, укажите свои пароли
```

---

## 🔧 Использование

### Загрузка профиля подключения

```python
from src.code.infrastructure.classes import ConnectionManager

# По умолчанию task_id=2
manager = ConnectionManager()

# Или явно указать task_id
manager = ConnectionManager(task_id=1)
```

### Загрузка общих настроек

```python
from src.code.infrastructure.config import ConfigLoader

loader = ConfigLoader()
migration_settings = loader.get_migration_settings()
print(f"Batch size: {migration_settings['batch_size']}")
```

---

## 🔒 Безопасность

### .gitignore

Убедитесь, что `connections.json` добавлен в `.gitignore`:

```gitignore
# Конфиденциальные конфигурации
src/code/infrastructure/config/connections.json
```

### Работа с паролями

**❌ НЕ делайте так:**
```python
# Жестко закодированные пароли
password = "my_secret_password"
```

**✅ Правильно:**
```python
# Пароли из connections.json через ConnectionManager
manager = ConnectionManager()
# Менеджер сам загрузит пароли из профиля
```

---

## 📚 Связанные документы

- **Детальные правила подключений:** `docs/infrastructure/database-connections-rules.md`
- **Общие правила проекта:** `docs/project-documentation-rules.md`
- **Курсор правила:** `.cursorrules`

---

**Автор:** Александр  
**Статус:** Действующий
