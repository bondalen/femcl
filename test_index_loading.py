#!/usr/bin/env python3
"""
Тестовый скрипт для проверки загрузки индексов
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import ConfigLoader
from src.classes.table_model import TableModel


def test_index_loading():
    """Тестирование загрузки индексов для таблицы accnt"""
    
    print("🔍 Тестирование загрузки индексов для таблицы accnt")
    print("=" * 60)
    
    try:
        # Загружаем конфигурацию
        config_loader = ConfigLoader()
        
        # Создаем модель таблицы
        table_model = TableModel("accnt")
        
        # Загружаем метаданные
        print("📊 Загружаем метаданные таблицы...")
        if not table_model.load_metadata(config_loader):
            print("❌ Ошибка загрузки метаданных")
            return False
        
        print(f"✅ Загружено колонок: {len(table_model.columns)}")
        print(f"✅ Загружено индексов: {len(table_model.indexes)}")
        
        # Выводим информацию об индексах
        if table_model.indexes:
            print("\n📋 Информация об индексах:")
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
                
                # Показываем SQL для создания
                try:
                    create_sql = index.generate_create_sql()
                    print(f"   SQL: {create_sql}")
                except Exception as e:
                    print(f"   Ошибка генерации SQL: {e}")
        else:
            print("⚠️ Индексы не найдены")
        
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False


if __name__ == "__main__":
    success = test_index_loading()
    sys.exit(0 if success else 1)
