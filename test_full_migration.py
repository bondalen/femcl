#!/usr/bin/env python3
"""
Тестовый скрипт для полной миграции таблицы accnt с индексами
"""

import sys
import os
sys.path.append('/home/alex/projects/sql/femcl')

from config.config_loader import ConfigLoader
from src.classes.table_migrator import TableMigrator


def test_full_migration():
    """Тестирование полной миграции таблицы accnt"""
    
    print("🔍 Тестирование полной миграции таблицы accnt")
    print("=" * 60)
    
    try:
        # Загружаем конфигурацию
        config_loader = ConfigLoader()
        
        # Создаем мигратор
        migrator = TableMigrator("accnt", config_loader, force=True, verbose=True)
        
        print("🚀 Начинаем миграцию...")
        result = migrator.migrate()
        
        print("\n📊 Результат миграции:")
        print(f"  Успешно: {result['success']}")
        
        if result['success']:
            print(f"  Длительность: {result['duration']}")
            print(f"  Перенесено строк: {result['rows_migrated']}")
        else:
            print(f"  Ошибка: {result['error']}")
            if 'errors' in result:
                print("  Детали ошибок:")
                for error in result['errors']:
                    print(f"    - {error}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_migration()
    sys.exit(0 if success else 1)