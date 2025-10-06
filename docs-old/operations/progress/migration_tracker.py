#!/usr/bin/env python3
"""
Трекер прогресса миграции FEMCL
Автоматическое отслеживание и обновление прогресса миграции
"""
import os
import sys
import psycopg2
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

class MigrationTracker:
    """Класс для отслеживания прогресса миграции"""
    
    def __init__(self, task_id=2):
        self.task_id = task_id
        self.progress_dir = "/home/alex/projects/sql/femcl/progress"
        self.current_file = None
        
    def connect_database(self):
        """Подключение к базе данных"""
        try:
            self.conn = psycopg2.connect(
                host="localhost",
                port=5432,
                dbname="fish_eye",
                user="postgres",
                password="postgres"
            )
            return True
        except Exception as e:
            console.print(f"[red]❌ Ошибка подключения к БД: {e}[/red]")
            return False
    
    def get_migration_stats(self):
        """Получение статистики миграции"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_tables,
                        COUNT(CASE WHEN migration_status = 'completed' THEN 1 END) as completed,
                        COUNT(CASE WHEN migration_status = 'in_progress' THEN 1 END) as in_progress,
                        COUNT(CASE WHEN migration_status = 'pending' THEN 1 END) as pending,
                        COUNT(CASE WHEN migration_status = 'failed' THEN 1 END) as failed
                    FROM mcl.mssql_tables 
                    WHERE task_id = %s
                """, (self.task_id,))
                
                stats = cur.fetchone()
                return {
                    'total': stats[0],
                    'completed': stats[1],
                    'in_progress': stats[2],
                    'pending': stats[3],
                    'failed': stats[4]
                }
        except Exception as e:
            console.print(f"[red]❌ Ошибка получения статистики: {e}[/red]")
            return None
    
    def get_tables_by_status(self):
        """Получение таблиц по статусам"""
        try:
            with self.conn.cursor() as cur:
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
                """, (self.task_id,))
                
                tables = cur.fetchall()
                
                # Группировка по статусам
                status_groups = {
                    'completed': [],
                    'in_progress': [],
                    'pending': [],
                    'failed': []
                }
                
                for table_name, schema_name, status, migration_date, target_name in tables:
                    status_groups[status].append((table_name, schema_name, migration_date, target_name))
                
                return status_groups
        except Exception as e:
            console.print(f"[red]❌ Ошибка получения таблиц: {e}[/red]")
            return None
    
    def create_progress_file(self):
        """Создание нового файла прогресса"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.current_file = f"{self.progress_dir}/{timestamp}_migration_progress.md"
        
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write(f"""# 📊 ПРОГРЕСС МИГРАЦИИ FEMCL

## 📋 Информация о сессии

**Дата создания:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}  
**Задача миграции:** ID={self.task_id}  
**Статус:** 🚀 НАЧАЛО МИГРАЦИИ  
**Автор:** AI Assistant  

## 🎯 Общая статистика

- **Всего таблиц для миграции:** 0
- **Завершено:** 0
- **В процессе:** 0  
- **Ожидает:** 0
- **Ошибок:** 0
- **Прогресс:** 0%

## 📊 Текущая итерация

### **Итерация #{timestamp}** ({datetime.now().strftime('%d.%m.%Y %H:%M:%S')})
**Статус:** 🔄 ПОДГОТОВКА

#### Список таблиц для текущей итерации:
*Таблицы будут добавлены при начале миграции*

#### Ход переноса:
*Детали переноса будут отображаться в реальном времени*

## 📈 История итераций

*История итераций будет вестись по мере выполнения миграции*

## 🚨 Проблемы и ошибки

*Проблемы будут документироваться по мере их возникновения*

## 📝 Заметки

*Дополнительные заметки о ходе миграции*

---
*Файл создан: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*  
*Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*
""")
        
        console.print(f"[green]✅ Создан файл прогресса: {self.current_file}[/green]")
        return self.current_file
    
    def update_progress_file(self):
        """Обновление файла прогресса"""
        if not self.current_file:
            self.create_progress_file()
        
        stats = self.get_migration_stats()
        if not stats:
            return False
        
        tables = self.get_tables_by_status()
        if not tables:
            return False
        
        progress_percent = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write(f"""# 📊 ПРОГРЕСС МИГРАЦИИ FEMCL

## 📋 Информация о сессии

**Дата обновления:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}  
**Задача миграции:** ID={self.task_id}  
**Статус:** 🔄 МИГРАЦИЯ В ПРОЦЕССЕ  
**Автор:** AI Assistant  

## 🎯 Общая статистика

- **Всего таблиц для миграции:** {stats['total']}
- **Завершено:** {stats['completed']}
- **В процессе:** {stats['in_progress']}  
- **Ожидает:** {stats['pending']}
- **Ошибок:** {stats['failed']}
- **Прогресс:** {progress_percent:.1f}%

## 📊 Текущая итерация

### **Итерация #{datetime.now().strftime('%Y%m%d_%H%M%S')}** ({datetime.now().strftime('%d.%m.%Y %H:%M:%S')})
**Статус:** 🔄 В ПРОЦЕССЕ

#### Список таблиц для текущей итерации:

""")
            
            # Завершенные таблицы
            if tables['completed']:
                f.write("#### ✅ Завершенные таблицы:\n")
                for table_name, schema_name, migration_date, target_name in tables['completed']:
                    f.write(f"- **{table_name}** ({schema_name}) → {target_name} - {migration_date}\n")
                f.write("\n")
            
            # Таблицы в процессе
            if tables['in_progress']:
                f.write("#### 🔄 Таблицы в процессе:\n")
                for table_name, schema_name, migration_date, target_name in tables['in_progress']:
                    f.write(f"- **{table_name}** ({schema_name}) → {target_name} - {migration_date}\n")
                f.write("\n")
            
            # Ожидающие таблицы
            if tables['pending']:
                f.write("#### ⏳ Ожидающие таблицы:\n")
                for table_name, schema_name, migration_date, target_name in tables['pending']:
                    f.write(f"- **{table_name}** ({schema_name})\n")
                f.write("\n")
            
            # Ошибочные таблицы
            if tables['failed']:
                f.write("#### ❌ Таблицы с ошибками:\n")
                for table_name, schema_name, migration_date, target_name in tables['failed']:
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
        
        console.print(f"[blue]📊 Прогресс обновлен: {progress_percent:.1f}% ({stats['completed']}/{stats['total']})[/blue]")
        return True
    
    def display_progress_table(self):
        """Отображение таблицы прогресса"""
        stats = self.get_migration_stats()
        if not stats:
            return
        
        table = Table(title="📊 Прогресс миграции")
        table.add_column("Метрика", style="cyan")
        table.add_column("Значение", style="green")
        table.add_column("Процент", style="yellow")
        
        total = stats['total']
        completed = stats['completed']
        in_progress = stats['in_progress']
        pending = stats['pending']
        failed = stats['failed']
        
        progress_percent = (completed / total * 100) if total > 0 else 0
        
        table.add_row("Всего таблиц", str(total), "100%")
        table.add_row("Завершено", str(completed), f"{progress_percent:.1f}%")
        table.add_row("В процессе", str(in_progress), f"{(in_progress/total*100):.1f}%" if total > 0 else "0%")
        table.add_row("Ожидает", str(pending), f"{(pending/total*100):.1f}%" if total > 0 else "0%")
        table.add_row("Ошибок", str(failed), f"{(failed/total*100):.1f}%" if total > 0 else "0%")
        
        console.print(table)
    
    def start_monitoring(self, interval=30):
        """Запуск мониторинга прогресса"""
        console.print(Panel.fit("[bold blue]🚀 Запуск мониторинга прогресса миграции[/bold blue]", border_style="blue"))
        
        if not self.connect_database():
            return False
        
        self.create_progress_file()
        
        try:
            while True:
                self.update_progress_file()
                self.display_progress_table()
                
                console.print(f"[blue]⏰ Следующее обновление через {interval} секунд...[/blue]")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]⏹️ Мониторинг остановлен пользователем[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Ошибка мониторинга: {e}[/red]")
        finally:
            if hasattr(self, 'conn'):
                self.conn.close()

def main():
    """Основная функция"""
    tracker = MigrationTracker()
    tracker.start_monitoring()

if __name__ == "__main__":
    main()