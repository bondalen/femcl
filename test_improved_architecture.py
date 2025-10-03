#!/usr/bin/env python3
"""
Тестирование улучшенной архитектуры индексов
"""

import sys
import os
sys.path.append('/home/alex/projects/sql/femcl')

from config.config_loader import ConfigLoader
from src.classes.table_model_improved import TableModelImproved
import psycopg2
import time

def test_improved_architecture():
    """Тестирование улучшенной архитектуры"""
    
    print("🔍 Тестирование улучшенной архитектуры индексов")
    print("=" * 60)
    
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
        
        print("1. Создаем представление для индексов...")
        try:
            # Читаем и выполняем SQL для создания представления
            with open('/home/alex/projects/sql/femcl/create_index_view.sql', 'r') as f:
                sql_content = f.read()
            
            # Выполняем SQL построчно
            for line in sql_content.split(';'):
                line = line.strip()
                if line and not line.startswith('--'):
                    cursor.execute(line)
            
            conn.commit()
            print("✅ Представление создано успешно")
        except Exception as e:
            print(f"⚠️ Ошибка создания представления: {e}")
            # Продолжаем тестирование
        
        print("\n2. Тестируем представление...")
        cursor.execute("SELECT COUNT(*) FROM mcl.v_postgres_indexes_by_table")
        total_count = cursor.fetchone()[0]
        print(f"   Всего записей в представлении: {total_count}")
        
        cursor.execute("SELECT COUNT(*) FROM mcl.v_postgres_indexes_by_table WHERE table_name = 'accnt'")
        accnt_count = cursor.fetchone()[0]
        print(f"   Индексов для таблицы accnt: {accnt_count}")
        
        print("\n3. Тестируем улучшенную загрузку индексов...")
        start_time = time.time()
        
        # Создаем улучшенную модель таблицы
        table_model = TableModelImproved("accnt")
        
        if table_model.load_indexes_improved(config_loader):
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
        
        print("\n4. Сравнение производительности...")
        print("   Текущий метод (сложный запрос):")
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
        
        print("   Улучшенный метод (представление):")
        start_time = time.time()
        cursor.execute("""
            SELECT index_id, index_name
            FROM mcl.v_postgres_indexes_by_table
            WHERE table_name = 'accnt'
        """)
        new_result = cursor.fetchall()
        new_time = (time.time() - start_time) * 1000
        print(f"     Результат: {len(new_result)} индексов за {new_time:.2f} мс")
        
        if old_time > 0:
            improvement = ((old_time - new_time) / old_time) * 100
            print(f"   🚀 Улучшение производительности: {improvement:.1f}%")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_improved_architecture()
    sys.exit(0 if success else 1)