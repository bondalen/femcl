#!/usr/bin/env python3
"""
Скрипт для проверки данных индексов в базе
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import ConfigLoader
import psycopg2


def check_indexes_data():
    """Проверка данных индексов в базе"""
    
    print("🔍 Проверка данных индексов в базе")
    print("=" * 50)
    
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
        
        # Проверяем таблицы
        print("📋 Проверяем таблицы в mcl.postgres_tables:")
        cursor.execute("SELECT id, object_name FROM mcl.postgres_tables WHERE object_name = 'accnt'")
        tables = cursor.fetchall()
        for table_id, table_name in tables:
            print(f"  {table_id}: {table_name}")
        
        if not tables:
            print("❌ Таблица accnt не найдена в mcl.postgres_tables")
            return False
        
        table_id = tables[0][0]
        
        # Проверяем индексы
        print(f"\n📋 Проверяем индексы для таблицы {table_id}:")
        cursor.execute("""
            SELECT id, index_name, index_type, is_unique, is_primary_key, migration_status
            FROM mcl.postgres_indexes 
            WHERE table_id = %s
        """, (table_id,))
        
        indexes = cursor.fetchall()
        if indexes:
            for idx_id, name, idx_type, is_unique, is_pk, status in indexes:
                print(f"  {idx_id}: {name} ({idx_type}, unique={is_unique}, pk={is_pk}, status={status})")
        else:
            print("❌ Индексы не найдены")
        
        # Проверяем исходные индексы
        print(f"\n📋 Проверяем исходные индексы в mssql_indexes:")
        cursor.execute("""
            SELECT mi.id, mi.index_name, mi.is_unique, mi.is_primary_key
            FROM mcl.mssql_indexes mi
            JOIN mcl.mssql_tables mt ON mi.table_id = mt.id
            WHERE mt.object_name = 'accnt'
        """)
        
        source_indexes = cursor.fetchall()
        if source_indexes:
            for idx_id, name, is_unique, is_pk in source_indexes:
                print(f"  {idx_id}: {name} (unique={is_unique}, pk={is_pk})")
        else:
            print("❌ Исходные индексы не найдены")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    success = check_indexes_data()
    sys.exit(0 if success else 1)

