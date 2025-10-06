#!/usr/bin/env python3
"""
Скрипт для обновления прогресса миграции
"""
import os
import sys
import psycopg2
from datetime import datetime
from rich.console import Console

console = Console()

def update_migration_progress(task_id=2):
    """Обновление файла прогресса миграции"""
    
    try:
        # Подключение к PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="fish_eye",
            user="postgres",
            password="postgres"
        )
        
        # Получение статистики миграции
        with conn.cursor() as cur:
            # Общая статистика
            cur.execute("""
                SELECT 
                    COUNT(*) as total_tables,
                    COUNT(CASE WHEN migration_status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN migration_status = 'in_progress' THEN 1 END) as in_progress,
                    COUNT(CASE WHEN migration_status = 'pending' THEN 1 END) as pending,
                    COUNT(CASE WHEN migration_status = 'failed' THEN 1 END) as failed
                FROM mcl.mssql_tables 
                WHERE task_id = %s
            """, (task_id,))
            
            stats = cur.fetchone()
            total, completed, in_progress, pending, failed = stats
            
            # Текущая итерация
            cur.execute("""
                SELECT 
                    mt.object_name,
                    mt.schema_name,
                    mt.migration_status,
                    mt.migration_date,
                    pt.object_name as target_name
                FROM mcl.mssql_tables mt
                LEFT JOIN mcl.postgres_tables pt ON mt.id = pt.source_table_id
                WHERE mt.task_id = %s
                ORDER BY mt.migration_status, mt.object_name
            """, (task_id,))
            
            tables = cur.fetchall()
            
        # Обновление файла прогресса
        progress_file = f"/home/alex/projects/sql/femcl/progress/{datetime.now().strftime('%Y%m%d_%H%M%S')}_migration_progress.md"
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            f.write(f"""# 📊 ПРОГРЕСС МИГРАЦИИ FEMCL

## 📋 Информация о сессии

**Дата обновления:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}  
**Задача миграции:** ID={task_id}  
**Статус:** 🔄 МИГРАЦИЯ В ПРОЦЕССЕ  
**Автор:** AI Assistant  

## 🎯 Общая статистика

- **Всего таблиц для миграции:** {total}
- **Завершено:** {completed}
- **В процессе:** {in_progress}  
- **Ожидает:** {pending}
- **Ошибок:** {failed}
- **Прогресс:** {(completed/total*100):.1f}%

## 📊 Текущая итерация

### **Итерация #{datetime.now().strftime('%Y%m%d_%H%M%S')}** ({datetime.now().strftime('%d.%m.%Y %H:%M:%S')})
**Статус:** 🔄 В ПРОЦЕССЕ

#### Список таблиц для текущей итерации:

""")
            
            # Группировка по статусам
            status_groups = {
                'completed': [],
                'in_progress': [],
                'pending': [],
                'failed': []
            }
            
            for table_name, schema_name, status, migration_date, target_name in tables:
                status_groups[status].append((table_name, schema_name, migration_date, target_name))
            
            # Завершенные таблицы
            if status_groups['completed']:
                f.write("#### ✅ Завершенные таблицы:\n")
                for table_name, schema_name, migration_date, target_name in status_groups['completed']:
                    f.write(f"- **{table_name}** ({schema_name}) → {target_name} - {migration_date}\n")
                f.write("\n")
            
            # Таблицы в процессе
            if status_groups['in_progress']:
                f.write("#### 🔄 Таблицы в процессе:\n")
                for table_name, schema_name, migration_date, target_name in status_groups['in_progress']:
                    f.write(f"- **{table_name}** ({schema_name}) → {target_name} - {migration_date}\n")
                f.write("\n")
            
            # Ожидающие таблицы
            if status_groups['pending']:
                f.write("#### ⏳ Ожидающие таблицы:\n")
                for table_name, schema_name, migration_date, target_name in status_groups['pending']:
                    f.write(f"- **{table_name}** ({schema_name})\n")
                f.write("\n")
            
            # Ошибочные таблицы
            if status_groups['failed']:
                f.write("#### ❌ Таблицы с ошибками:\n")
                for table_name, schema_name, migration_date, target_name in status_groups['failed']:
                    f.write(f"- **{table_name}** ({schema_name}) - {migration_date}\n")
                f.write("\n")
            
            f.write(f"""## 📈 История итераций

*История итераций ведется автоматически*

## 🚨 Проблемы и ошибки

*Проблемы документируются автоматически*

## 📝 Заметки

*Дополнительные заметки о ходе миграции*

---
*Файл создан: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*  
*Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*
""")
        
        console.print(f"[green]✅ Файл прогресса обновлен: {progress_file}[/green]")
        console.print(f"[blue]📊 Статистика: {completed}/{total} таблиц завершено ({(completed/total*100):.1f}%)[/blue]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка обновления прогресса: {e}[/red]")
        return False

if __name__ == "__main__":
    update_migration_progress()