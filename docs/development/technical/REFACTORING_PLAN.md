# План рефакторинга скриптов на ConnectionManager

**Дата создания:** 2025-10-07  
**Статус:** В работе  
**Цель:** Переход всех скриптов на использование ConnectionManager

---

## 📊 Статистика

- **Всего скриптов с прямыми подключениями:** 22
- **Удалено устаревших файлов:** 40
- **Осталось для рефакторинга:** 22

---

## 🎯 Категории скриптов для рефакторинга

### Категория A: КРИТИЧНЫЕ - рефакторить в первую очередь ⭐⭐⭐

| Файл | Статус | Приоритет | Назначение |
|------|--------|-----------|------------|
| `scripts/check_connections_and_tables.py` | ⚙️ Рефакторить | Высокий | Проверка подключений → ConnectionDiagnostics |
| `scripts/check_mcl_schema.py` | ⚙️ Рефакторить | Высокий | Проверка схемы mcl → ConnectionDiagnostics |
| `scripts/migration_manager.py` | ⚙️ Рефакторить | Критический | Основной менеджер миграции |
| `scripts/reset_migration_status.py` | ⚙️ Рефакторить | Высокий | Сброс статусов миграции |

### Категория B: РЕФЕРЕНСНЫЕ - оставить как примеры ✅

| Файл | Статус | Действие |
|------|--------|----------|
| `scripts/migrate_cn.py` | ⚙️ Рефакторить | Референсный пример миграции таблицы |
| `scripts/check_cn.py` | ⚙️ Рефакторить | Референсный пример проверки таблицы |

### Категория C: МИГРАЦИЯ - основные скрипты ⭐⭐

| Файл | Статус | Приоритет |
|------|--------|-----------|
| `scripts/migrate_single_table.py` | ⚙️ Рефакторить | Средний |
| `scripts/migration/full_structure_migration.py` | ⚙️ Рефакторить | Высокий |
| `scripts/migration/dependency_analyzer.py` | ⚙️ Рефакторить | Высокий |
| `scripts/migration/table_list_manager.py` | ⚙️ Рефакторить | Средний |
| `scripts/migration/monitoring_reporter.py` | ⚙️ Рефакторить | Средний |
| `scripts/migration/start_migration.py` | ⚙️ Рефакторить | Высокий |
| `scripts/monitoring/check_status.py` | ⚙️ Рефакторить | Средний |

### Категория D: ДАННЫЕ - скрипты переноса данных ⭐

| Файл | Статус | Приоритет |
|------|--------|-----------|
| `scripts/migration/extract_mssql_data.py` | ⚙️ Рефакторить | Средний |
| `scripts/migration/load_postgres_data.py` | ⚙️ Рефакторить | Средний |
| `scripts/migration/migrate_accnt_data.py` | ⚙️ Рефакторить | Низкий |

### Категория E: ТЕСТОВЫЕ - удалить или отрефакторить ❌

| Файл | Статус | Действие |
|------|--------|----------|
| `scripts/migration/real_data_migration.py` | ❌ Удалить | Старая версия |
| `scripts/migration/real_data_migration_fixed.py` | ❌ Удалить | Старая версия |
| `scripts/migration/real_data_migration_final.py` | ⚙️ Рефакторить | Актуальная версия |
| `scripts/migration/test_data_migration.py` | ❌ Удалить | Тестовый |
| `scripts/migration/test_three_tables_real_migration.py` | ❌ Удалить | Тестовый |
| `scripts/migration/check_mssql_tables.py` | ⚙️ Рефакторить | Проверка таблиц |

---

## 📝 План действий

### Этап 1: Рефакторинг критичных скриптов (приоритет)

1. ✅ `check_connections_and_tables.py` → использовать ConnectionDiagnostics
2. ✅ `check_mcl_schema.py` → использовать ConnectionDiagnostics
3. ✅ `migration_manager.py` → использовать ConnectionManager
4. ✅ `reset_migration_status.py` → использовать ConnectionManager

### Этап 2: Рефакторинг референсных примеров

5. ✅ `migrate_cn.py` → пример использования ConnectionManager
6. ✅ `check_cn.py` → пример использования ConnectionManager

### Этап 3: Рефакторинг скриптов миграции

7. ✅ `migration/full_structure_migration.py`
8. ✅ `migration/dependency_analyzer.py`
9. ✅ `migration/table_list_manager.py`
10. ✅ `migration/start_migration.py`

### Этап 4: Удаление тестовых версий

11. ❌ Удалить устаревшие тестовые скрипты (5 файлов)

---

## 🎯 Ожидаемый результат

После рефакторинга все скрипты будут использовать:

```python
from src.code.infrastructure.classes import ConnectionManager

manager = ConnectionManager()  # task_id=2 по умолчанию
pg_conn = manager.get_postgres_connection()
ms_conn = manager.get_mssql_connection()
```

Вместо прямых вызовов `psycopg2.connect()` и `pyodbc.connect()`

