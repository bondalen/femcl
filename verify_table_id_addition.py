#!/usr/bin/env python3
"""
Проверка добавления table_id в таблицы индексов
"""

import psycopg2
import sys
import os
sys.path.append('/home/alex/projects/sql/femcl')
from config.config_loader import ConfigLoader

def verify_table_id_addition():
    """Проверка добавления table_id"""
    
    print("🔍 Проверка добавления table_id в таблицы индексов")
    print("=" * 60)
    
    try:
        config_loader = ConfigLoader()
        pg_config = config_loader.get_database_config('postgres')
        pg_config_clean = {
            'host': pg_config['host'],
            'port': pg_config['port'], 
            'database': pg_config['database'],
            'user': pg_config['user'],
            'password': pg_config['password']
        }
        
        conn = psycopg2.connect(**pg_config_clean)
        cursor = conn.cursor()
        
        print("1. Проверяем наличие колонки table_id в mssql_indexes:")
        try:
            cursor.execute("SELECT table_id FROM mcl.mssql_indexes LIMIT 1")
            result = cursor.fetchone()
            print("   ✅ Колонка table_id существует")
        except Exception as e:
            print(f"   ❌ Колонка table_id не найдена: {e}")
            return False
        
        print("\n2. Проверяем наличие колонки table_id в postgres_indexes:")
        try:
            cursor.execute("SELECT table_id FROM mcl.postgres_indexes LIMIT 1")
            result = cursor.fetchone()
            print("   ✅ Колонка table_id существует")
        except Exception as e:
            print(f"   ❌ Колонка table_id не найдена: {e}")
            return False
        
        print("\n3. Статистика заполнения:")
        cursor.execute("""
            SELECT 
                'mssql_indexes' as table_name,
                COUNT(*) as total_records,
                COUNT(table_id) as with_table_id,
                COUNT(*) - COUNT(table_id) as without_table_id
            FROM mcl.mssql_indexes
            UNION ALL
            SELECT 
                'postgres_indexes' as table_name,
                COUNT(*) as total_records,
                COUNT(table_id) as with_table_id,
                COUNT(*) - COUNT(table_id) as without_table_id
            FROM mcl.postgres_indexes
        """)
        
        stats = cursor.fetchall()
        for table_name, total, with_id, without_id in stats:
            print(f"   {table_name}:")
            print(f"     Всего записей: {total}")
            print(f"     С table_id: {with_id}")
            print(f"     Без table_id: {without_id}")
            if without_id > 0:
                print(f"     ⚠️ Есть записи без table_id!")
            else:
                print(f"     ✅ Все записи имеют table_id")
        
        print("\n4. Проверка связей для таблицы accnt:")
        cursor.execute("""
            SELECT 
                mi.id as mssql_index_id,
                mi.index_name as mssql_index_name,
                mi.table_id as mssql_table_id,
                pi.id as postgres_index_id,
                pi.index_name as postgres_index_name,
                pi.table_id as postgres_table_id,
                pi.source_index_id,
                mt.object_name as table_name
            FROM mcl.mssql_indexes mi
            JOIN mcl.postgres_indexes pi ON mi.id = pi.source_index_id
            JOIN mcl.mssql_tables mt ON mi.table_id = mt.id
            WHERE mt.object_name = 'accnt'
        """)
        
        links = cursor.fetchall()
        print(f"   Найдено связей: {len(links)}")
        
        for link in links:
            mssql_id, mssql_name, mssql_table_id, pg_id, pg_name, pg_table_id, source_id, table_name = link
            print(f"\n   Индекс: {mssql_name} -> {pg_name}")
            print(f"     MS SQL ID: {mssql_id}, table_id: {mssql_table_id}")
            print(f"     PG ID: {pg_id}, table_id: {pg_table_id}")
            print(f"     Source ID: {source_id}")
            print(f"     Таблица: {table_name}")
            
            # Проверяем соответствие
            if mssql_id == source_id:
                print(f"     ✅ Source ID соответствует")
            else:
                print(f"     ❌ Source ID не соответствует")
            
            if mssql_table_id == pg_table_id:
                print(f"     ✅ Table ID соответствует")
            else:
                print(f"     ❌ Table ID не соответствует")
        
        print("\n5. Тестируем упрощенные запросы:")
        print("   Запрос индексов для таблицы accnt через mssql_indexes:")
        cursor.execute("""
            SELECT id, index_name, is_primary_key, is_unique
            FROM mcl.mssql_indexes 
            WHERE table_id = (
                SELECT id FROM mcl.mssql_tables WHERE object_name = 'accnt'
            )
        """)
        mssql_indexes = cursor.fetchall()
        print(f"     Найдено: {len(mssql_indexes)} индексов")
        for idx in mssql_indexes:
            print(f"       {idx[1]} ({'PK' if idx[2] else ''} {'UNIQUE' if idx[3] else ''})")
        
        print("\n   Запрос индексов для таблицы accnt через postgres_indexes:")
        cursor.execute("""
            SELECT id, index_name, is_primary_key, is_unique, migration_status
            FROM mcl.postgres_indexes 
            WHERE table_id = (
                SELECT id FROM mcl.postgres_tables WHERE object_name = 'accnt'
            )
        """)
        pg_indexes = cursor.fetchall()
        print(f"     Найдено: {len(pg_indexes)} индексов")
        for idx in pg_indexes:
            print(f"       {idx[1]} ({'PK' if idx[2] else ''} {'UNIQUE' if idx[3] else ''}) - {idx[4]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_table_id_addition()
    sys.exit(0 if success else 1)