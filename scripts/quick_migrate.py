#!/usr/bin/env python3
"""
FEMCL - Быстрая миграция таблиц
Версия: 1.0
Автор: FEMCL Team
Дата: 2025-01-27

Описание:
    Быстрый скрипт для миграции таблиц с минимальным выводом
    и максимальной производительностью.

Использование:
    python scripts/quick_migrate.py <table_name> [--force]
    
Примеры:
    python scripts/quick_migrate.py accnt
    python scripts/quick_migrate.py cn --force
"""

import os
import sys
import argparse
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

console = Console()

def quick_migrate(table_name, force=False):
    """Быстрая миграция таблицы"""
    rprint(Panel(f"[bold blue]🚀 Быстрая миграция таблицы {table_name}[/bold blue]", expand=False))
    
    # Формируем команду
    cmd = [sys.executable, "scripts/migrate_single_table.py", table_name]
    if force:
        cmd.append("--force")
    
    try:
        # Выполняем миграцию
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        if result.returncode == 0:
            rprint(f"[green]✅ Таблица {table_name} успешно мигрирована![/green]")
            return True
        else:
            rprint(f"[red]❌ Ошибка миграции таблицы {table_name}:[/red]")
            rprint(result.stderr)
            return False
            
    except Exception as e:
        rprint(f"[red]❌ Ошибка выполнения команды: {e}[/red]")
        return False

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='FEMCL - Быстрая миграция таблиц')
    parser.add_argument('table_name', help='Имя таблицы для миграции')
    parser.add_argument('--force', action='store_true', help='Принудительное пересоздание таблицы')
    
    args = parser.parse_args()
    
    # Выполнение миграции
    success = quick_migrate(args.table_name, args.force)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()