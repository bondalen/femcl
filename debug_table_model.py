#!/usr/bin/env python3
import sys
import os
sys.path.append('/home/alex/projects/sql/femcl')

from config.config_loader import ConfigLoader
from src.classes.table_model import TableModel

def debug_table_model():
    """Отладка TableModel"""
    
    print("🔍 Отладка TableModel для таблицы accnt")
    print("=" * 50)
    
    try:
        # Загружаем конфигурацию
        config_loader = ConfigLoader()
        
        # Создаем модель таблицы
        table_model = TableModel("accnt")
        
        print("📊 Загружаем колонки...")
        if table_model.load_columns(config_loader):
            print(f"✅ Загружено колонок: {len(table_model.columns)}")
        else:
            print("❌ Ошибка загрузки колонок")
            return False
        
        print("📊 Загружаем индексы...")
        if table_model.load_indexes(config_loader):
            print(f"✅ Загружено индексов: {len(table_model.indexes)}")
            
            for i, index in enumerate(table_model.indexes, 1):
                print(f"\n{i}. {index.name}")
                print(f"   Тип: {index.index_type}")
                print(f"   Уникальный: {index.is_unique}")
                print(f"   Первичный ключ: {index.is_primary_key}")
                print(f"   Статус: {index.migration_status}")
                print(f"   Колонки: {len(index.columns)}")
                
                if index.columns:
                    print("   Детали колонок:")
                    for col in index.columns:
                        direction = "DESC" if col.is_descending else "ASC"
                        print(f"     - {col.column_name} {direction} (позиция: {col.ordinal_position})")
        else:
            print("❌ Ошибка загрузки индексов")
            if table_model.errors:
                print("Ошибки:")
                for error in table_model.errors:
                    print(f"  - {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_table_model()
    sys.exit(0 if success else 1)