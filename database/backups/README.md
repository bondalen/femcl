# Резервная копия схемы MCL базы данных Fish_Eye

## Описание
Эта папка содержит резервную копию схемы `mcl` (Migration Control Layer) из базы данных `Fish_Eye`, созданную 25 сентября 2025 года.

## Файлы

### 1. fish_eye_mcl_backup.dump (356 KB)
- **Формат:** PostgreSQL custom database dump v1.15-0
- **Тип:** Бинарная копия для быстрого восстановления
- **Восстановление:** `pg_restore -U postgres -d target_db fish_eye_mcl_backup.dump`

### 2. fish_eye_mcl_backup.sql (1.2 MB)
- **Формат:** SQL скрипт
- **Тип:** Текстовая копия для просмотра и редактирования
- **Восстановление:** `psql -U postgres -d target_db -f fish_eye_mcl_backup.sql`

### 3. fish_eye_mcl_backup_report.txt (2.2 KB)
- **Содержит:** Подробный отчёт о резервной копии
- **Включает:** Статистику, инструкции по восстановлению

## Содержимое схемы MCL

- **56 таблиц** системы управления миграцией
- **2 задачи миграции** (включая основную задачу v2.0)
- **167 MS SQL Server таблиц** (метаданные)
- **166 PostgreSQL таблиц** (метаданные)
- **16 проблем** системы миграции
- **Функции и процедуры** системы контроля
- **Индексы и ограничения**

## Статус миграции
- MS SQL Server таблицы: 167 (все в статусе pending)
- PostgreSQL таблицы: 166 (все в статусе pending)
- Проблемы: 16 (7 high, 6 medium, 3 low)

## Использование

### Восстановление бинарной копии:
```bash
pg_restore -U postgres -d target_database fish_eye_mcl_backup.dump
```

### Восстановление текстовой копии:
```bash
psql -U postgres -d target_database -f fish_eye_mcl_backup.sql
```

## Безопасность
- Файлы созданы с правами доступа 644
- Владелец: alex
- Расположение: /home/alex/fish_eye_mcl_backup/

---
*Создано: 25 сентября 2025, 20:58 MSK*