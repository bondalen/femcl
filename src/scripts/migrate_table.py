#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FEMCL - Скрипт переноса отдельной таблицы
Использует классы из src/classes для выполнения миграции
"""

import sys
import os
import argparse
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.classes.table_migrator import TableMigrator
from config.config_loader import ConfigLoader


def main():
    """Основная функция скрипта"""
    
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description='FEMCL - Миграция отдельной таблицы')
    parser.add_argument('table_name', help='Имя таблицы для миграции')
    parser.add_argument('--force', action='store_true', help='Принудительное пересоздание таблицы')
    parser.add_argument('--verbose', '-v', action='store_true', help='Подробный вывод')
    
    args = parser.parse_args()
    
    print(f"🚀 FEMCL - Миграция таблицы: {args.table_name}")
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 Режим: {'Принудительный' if args.force else 'Обычный'}")
    print("-" * 60)
    
    try:
        # Загружаем конфигурацию
        config_loader = ConfigLoader()
        
        # Создаем мигратор
        migrator = TableMigrator(
            table_name=args.table_name,
            config_loader=config_loader,
            force=args.force,
            verbose=args.verbose
        )
        
        # Выполняем миграцию
        result = migrator.migrate()
        
        if result['success']:
            print(f"✅ Миграция таблицы {args.table_name} завершена успешно!")
            print(f"⏱️ Время выполнения: {result.get('duration', 'N/A')}")
            print(f"📊 Перенесено строк: {result.get('rows_migrated', 'N/A')}")
        else:
            print(f"❌ Ошибка при миграции таблицы {args.table_name}")
            print(f"🔍 Детали: {result.get('error', 'Неизвестная ошибка')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()