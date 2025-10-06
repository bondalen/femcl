#!/usr/bin/env python3
"""
Быстрое обновление прогресса миграции
"""
import sys
import os
sys.path.append('/home/alex/projects/sql/femcl/progress')

from migration_tracker import MigrationTracker
from rich.console import Console

console = Console()

def quick_update():
    """Быстрое обновление прогресса"""
    console.print("[blue]🔄 Быстрое обновление прогресса...[/blue]")
    
    tracker = MigrationTracker()
    
    if not tracker.connect_database():
        console.print("[red]❌ Ошибка подключения к БД[/red]")
        return False
    
    # Найти последний файл прогресса
    progress_files = [f for f in os.listdir(tracker.progress_dir) if f.endswith('_migration_progress.md')]
    if progress_files:
        latest_file = sorted(progress_files)[-1]
        tracker.current_file = f"{tracker.progress_dir}/{latest_file}"
        console.print(f"[blue]📄 Используем файл: {latest_file}[/blue]")
    else:
        tracker.create_progress_file()
    
    # Обновить прогресс
    if tracker.update_progress_file():
        console.print("[green]✅ Прогресс обновлен успешно![/green]")
        tracker.display_progress_table()
        return True
    else:
        console.print("[red]❌ Ошибка обновления прогресса[/red]")
        return False

if __name__ == "__main__":
    quick_update()