#!/usr/bin/env python3
"""
Тестирование оптимизированной архитектуры с прямыми связями
"""

import sys
import os
import time
sys.path.append('/home/alex/projects/sql/femcl')

from config.config_loader import ConfigLoader
from src.classes.table_model_optimized import TableModelOptimized
import psycopg2

def test_optimized_architecture():
    """Тестирование оптимизированной архитектуры"""
    
    print("🚀 Тестирование оптимизированной архитектуры с прямыми связями")
    print("=" * 70)
    
    try:
        # Загружаем конфигурацию
        config_loader = ConfigLoader()
        pg_config = config_loader.get_database_config('postgres')
        pg_config_clean = {
            'host': pg_config['host'],
            'port': pg_config['port'], 
            'database': pg_config['database'],
            'user': pg_config['user'],
            'password': pg_config['password']
        }
        
        # Подключаемся к базе
        conn = psycopg2.connect(**pg_config_clean)
        cursor = conn.cursor()
        
        print("1. Сравнение производительности запросов:")
        
        # Старый способ (сложный запрос)
        print("   Старый способ (сложный запрос):")
        start_time = time.time()
        cursor.execute("""
            SELECT pi.id, pi.index_name
            FROM mcl.postgres_indexes pi
            WHERE pi.source_index_id IN (
                SELECT mi.id 
                FROM mcl.mssql_indexes mi
                JOIN mcl.mssql_index_columns mic ON mi.id = mic.index_id
                JOIN mcl.mssql_columns mc ON mic.column_id = mc.id
                JOIN mcl.mssql_tables mt ON mc.table_id = mt.id
                WHERE mt.object_name = 'accnt'
            )
        """)
        old_result = cursor.fetchall()
        old_time = (time.time() - start_time) * 1000
        print(f"     Результат: {len(old_result)} индексов за {old_time:.2f} мс")
        
        # Новый способ (прямые связи)
        print("   Новый способ (прямые связи):")
        start_time = time.time()
        cursor.execute("""
            SELECT pi.id, pi.index_name
            FROM mcl.postgres_indexes pi
            JOIN mcl.postgres_tables pt ON pi.table_id = pt.id
            WHERE pt.object_name = 'accnt'
        """)
        new_result = cursor.fetchall()
        new_time = (time.time() - start_time) * 1000
        print(f"     Результат: {len(new_result)} индексов за {new_time:.2f} мс")
        
        if old_time > 0:
            improvement = ((old_time - new_time) / old_time) * 100
            print(f"   🚀 Улучшение производительности: {improvement:.1f}%")
        
        print("\n2. Тестирование оптимизированной загрузки индексов:")
        start_time = time.time()
        
        # Создаем оптимизированную модель таблицы
        table_model = TableModelOptimized("accnt")
        
        if table_model.load_indexes_optimized(config_loader):
            end_time = time.time()
            load_time = (end_time - start_time) * 1000  # в миллисекундах
            
            print(f"✅ Загружено индексов: {len(table_model.indexes)}")
            print(f"⏱️ Время загрузки: {load_time:.2f} мс")
            
            # Показываем сводку
            summary = table_model.get_indexes_summary()
            print(f"\n📊 Сводка по индексам:")
            print(f"   Всего индексов: {summary['total_indexes']}")
            print(f"   Уникальных: {summary['unique_indexes']}")
            print(f"   Первичных ключей: {summary['primary_keys']}")
            print(f"   Завершенных: {summary['completed_indexes']}")
            print(f"   Ожидающих: {summary['pending_indexes']}")
            print(f"   Ошибок: {summary['failed_indexes']}")
            
            # Показываем детали индексов
            for i, index in enumerate(table_model.indexes, 1):
                print(f"\n   {i}. {index.name}")
                print(f"      Тип: {index.index_type}")
                print(f"      Уникальный: {index.is_unique}")
                print(f"      Первичный ключ: {index.is_primary_key}")
                print(f"      Статус: {index.migration_status}")
                print(f"      Колонки: {len(index.columns)}")
                
                if index.columns:
                    for col in index.columns:
                        direction = "DESC" if col.is_descending else "ASC"
                        print(f"        - {col.column_name} {direction}")
        else:
            print("❌ Ошибка загрузки индексов")
            if table_model.errors:
                for error in table_model.errors:
                    print(f"   {error}")
        
        print("\n3. Проверка согласованности связей:")
        if table_model.verify_index_consistency(config_loader):
            print("✅ Все связи согласованы")
        else:
            print("❌ Найдены несогласованности")
        
        print("\n4. Тестирование упрощенных запросов:")
        
        # Запрос через MS SQL индексы
        print("   MS SQL индексы для accnt:")
        cursor.execute("""
            SELECT mi.id, mi.index_name, mi.is_primary_key, mi.is_unique
            FROM mcl.mssql_indexes mi
            JOIN mcl.mssql_tables mt ON mi.table_id = mt.id
            WHERE mt.object_name = 'accnt'
        """)
        mssql_indexes = cursor.fetchall()
        for idx in mssql_indexes:
            print(f"     {idx[1]} ({'PK' if idx[2] else ''} {'UNIQUE' if idx[3] else ''})")
        
        # Запрос через PostgreSQL индексы
        print("   PostgreSQL индексы для accnt:")
        cursor.execute("""
            SELECT pi.id, pi.index_name, pi.is_primary_key, pi.is_unique, pi.migration_status
            FROM mcl.postgres_indexes pi
            JOIN mcl.postgres_tables pt ON pi.table_id = pt.id
            WHERE pt.object_name = 'accnt'
        """)
        pg_indexes = cursor.fetchall()
        for idx in pg_indexes:
            print(f"     {idx[1]} ({'PK' if idx[2] else ''} {'UNIQUE' if idx[3] else ''}) - {idx[4]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Тестирование оптимизированной архитектуры завершено!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_optimized_architecture()
    sys.exit(0 if success else 1)