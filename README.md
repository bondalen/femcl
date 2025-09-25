# 🐟 FEMCL - Fish_Eye Migration Control Layer

## 📋 Описание проекта

**FEMCL** (Fish_Eye Migration Control Layer) - специализированная система для переноса базы данных Fish_Eye из MS SQL Server в PostgreSQL с использованием продвинутой системы контроля миграции.

## 🎯 Цели проекта

- **Миграция данных:** Перенос 167 таблиц из MS SQL Server в PostgreSQL
- **Контроль процесса:** Детальный учет всех этапов миграции
- **Решение проблем:** Обработка 16 выявленных проблем совместимости
- **Автоматизация:** Python скрипты для автоматизации процесса
- **Документация:** Полная документация процесса миграции

## 🏗️ Архитектура

### База данных
- **PostgreSQL:** Прямая установка на Fedora 42
- **База данных:** Fish_Eye
- **Схема:** mcl (Migration Control Layer) - 56 таблиц
- **Статус:** 167 MS SQL таблиц, 166 PostgreSQL таблиц

### Система контроля миграции
- **Задачи миграции:** 2 задачи (включая основную v2.0)
- **Проблемы:** 16 проблем (7 high, 6 medium, 3 low)
- **Статусы:** Все объекты в статусе pending
- **Мониторинг:** Представления для отслеживания прогресса

## 📁 Структура проекта

```
femcl/
├── README.md                          # Основная документация
├── SETUP.md                          # Инструкции по установке
├── FIRST_CHAT_REQUEST.md             # Первый запрос для чата
├── GIT_SETUP.md                      # Настройка Git репозитория
├── CHAT_SESSION_REPORT.md            # Отчет о работе в чате
├── PROJECT_CREATION_REPORT.md        # Отчет о создании проекта
├── requirements.txt                   # Python зависимости
├── .env.example                      # Пример переменных окружения
├── database/                         # База данных
│   ├── backups/                      # Резервные копии
│   │   ├── fish_eye_mcl_backup.dump  # Бинарная копия (356 KB)
│   │   ├── fish_eye_mcl_backup.sql   # Текстовая копия (1.2 MB)
│   │   ├── fish_eye_mcl_backup_report.txt # Отчет о копии
│   │   └── fedora_restore_instructions.md # Инструкции для Fedora 42
│   ├── init/                        # Скрипты инициализации
│   └── migrations/                  # Скрипты миграции
├── docs/                            # Документация
│   ├── migration/                   # Документация миграции
│   ├── architecture/                # Архитектурные диаграммы
│   └── reports/                     # Отчеты
├── scripts/                         # Python скрипты
│   ├── database/                    # Скрипты работы с БД
│   │   └── test_connection.py        # Тестирование подключения
│   ├── migration/                   # Скрипты миграции
│   │   └── start_migration.py        # Запуск миграции
│   └── monitoring/                  # Скрипты мониторинга
│       └── check_status.py          # Проверка статуса
├── rules/                           # Модульные правила
│   └── migration.md                 # Правила миграции
└── schemas/                         # Диаграммы процессов
    ├── entity-relationship/         # ER диаграммы
    └── uml/                        # UML диаграммы
```

## 🚀 Быстрый старт

### 1. Установка зависимостей (Fedora 42)
```bash
# PostgreSQL
sudo dnf install postgresql postgresql-server postgresql-contrib

# Python зависимости
pip install psycopg2-binary pandas sqlalchemy

# Дополнительные инструменты
sudo dnf install git plantuml
```

### 2. Настройка PostgreSQL
```bash
# Инициализация базы данных
sudo postgresql-setup --initdb

# Запуск службы
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Создание пользователя и базы
sudo -u postgres createuser -s alex
sudo -u postgres createdb Fish_Eye
```

### 3. Восстановление базы данных
```bash
# Восстановление из резервной копии
pg_restore -U alex -d Fish_Eye database/backups/fish_eye_mcl_backup.dump
```

### 4. Проверка статуса
```bash
# Проверка подключения
psql -U alex -d Fish_Eye -c "SELECT version();"

# Проверка схемы mcl
psql -U alex -d Fish_Eye -c "\dn"

# Статус миграции
psql -U alex -d Fish_Eye -c "SELECT migration_status, count(*) FROM mcl.mssql_tables GROUP BY migration_status;"
```

## 📚 Документация

- **Правила миграции:** `rules/migration.md`
- **Шаблоны запросов:** `rules/migration-query-templates.md`
- **Диаграммы процесса:** `schemas/entity-relationship/`
- **Отчеты:** `docs/reports/`
- **Отчет о сессии:** `CHAT_SESSION_REPORT.md`

## 🔧 Использование

### Первый запрос для чата
Используйте файл `FIRST_CHAT_REQUEST.md` для быстрого старта работы с AI ассистентом.

### Python скрипты
```bash
# Запуск скриптов миграции
python scripts/migration/start_migration.py

# Мониторинг прогресса
python scripts/monitoring/check_status.py

# Генерация отчетов
python scripts/reports/generate_report.py
```

## 🚨 Известные проблемы

- **P250817-02:** Проблема блокировки терминала (pager)
- **P250825-01:** Цикл чтения файлов в AI ассистенте
- **Совместимость типов:** 7 проблем high уровня
- **Именование:** 8 проблем naming_convention

## 📊 Статус проекта

- **База данных:** ✅ Готова
- **Документация:** ✅ Готова
- **Скрипты:** ✅ Готовы
- **Резервные копии:** ✅ Доступны в репозитории
- **Миграция:** ⏳ Ожидает запуска

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE для подробностей.

## 📈 История проекта

### Версия 1.0.0 (25 сентября 2025)
- **Создание проекта** - Выделение из основного проекта Vuege
- **Адаптация для Fedora 42** - Настройка без Docker
- **Размещение на GitHub** - Загрузка в репозиторий
- **Решение проблем** - Исправление отсутствующих резервных копий
- **Документация** - Полная система инструкций

---

**Автор:** AI Assistant  
**Дата создания:** 25 сентября 2025  
**Версия:** 1.0.0  
**Статус:** ✅ ГОТОВ К РАБОТЕ