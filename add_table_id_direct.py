#!/usr/bin/env python3
"""
Прямое добавление table_id через Python
"""

import psycopg2
import sys
import os
sys.path.append('/home/alex/projects/sql/femcl')
from config.config_loader import ConfigLoader

def add_table_id_direct():
    """Прямое добавление table_id"""
    
    print("🔧 Прямое добавление table_id в таблицы индексов")
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
        
        print("1. Добавляем колонку table_id в mssql_indexes...")
        try:
            cursor.execute("ALTER TABLE mcl.mssql_indexes ADD COLUMN table_id INTEGER")
            conn.commit()
            print("   ✅ Колонка добавлена")
        except Exception as e:
            if "already exists" in str(e):
                print("   ⚠️ Колонка уже существует")
            else:
                print(f"   ❌ Ошибка: {e}")
                return False
        
        print("\n2. Добавляем колонку table_id в postgres_indexes...")
        try:
            cursor.execute("ALTER TABLE mcl.postgres_indexes ADD COLUMN table_id INTEGER")
            conn.commit()
            print("   ✅ Колонка добавлена")
        except Exception as e:
            if "already exists" in str(e):
                print("   ⚠️ Колонка уже существует")
            else:
                print(f"   ❌ Ошибка: {e}")
                return False
        
        print("\n3. Заполняем table_id в mssql_indexes...")
        cursor.execute("""
            UPDATE mcl.mssql_indexes 
            SET table_id = (
                SELECT DISTINCT mt.id 
                FROM mcl.mssql_tables mt
                JOIN mcl.mssql_columns mc ON mt.id = mc.table_id
                JOIN mcl.mssql_index_columns mic ON mc.id = mic.column_id
                WHERE mic.index_id = mssql_indexes.id
                LIMIT 1
            )
            WHERE table_id IS NULL
        """)
        updated_mssql = cursor.rowcount
        conn.commit()
        print(f"   ✅ Обновлено записей: {updated_mssql}")
        
        print("\n4. Заполняем table_id в postgres_indexes...")
        cursor.execute("""
            UPDATE mcl.postgres_indexes 
            SET table_id = (
                SELECT DISTINCT pt.id 
                FROM mcl.postgres_tables pt
                JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
                JOIN mcl.mssql_columns mc ON mt.id = mc.table_id
                JOIN mcl.mssql_index_columns mic ON mc.id = mic.column_id
                JOIN mcl.mssql_indexes mi ON mic.index_id = mi.id
                WHERE mi.id = postgres_indexes.source_index_id
                LIMIT 1
            )
            WHERE table_id IS NULL
        """)
        updated_pg = cursor.rowcount
        conn.commit()
        print(f"   ✅ Обновлено записей: {updated_pg}")
        
        print("\n5. Проверяем результат...")
        cursor.execute("""
            SELECT 
                'mssql_indexes' as table_name,
                COUNT(*) as total,
                COUNT(table_id) as with_table_id
            FROM mcl.mssql_indexes
            UNION ALL
            SELECT 
                'postgres_indexes' as table_name,
                COUNT(*) as total,
                COUNT(table_id) as with_table_id
            FROM mcl.postgres_indexes
        """)
        
        stats = cursor.fetchall()
        for table_name, total, with_id in stats:
            print(f"   {table_name}: {with_id}/{total} записей имеют table_id")
        
        print("\n6. Тестируем упрощенные запросы...")
        cursor.execute("""
            SELECT mi.id, mi.index_name, mi.table_id, mt.object_name
            FROM mcl.mssql_indexes mi
            JOIN mcl.mssql_tables mt ON mi.table_id = mt.id
            WHERE mt.object_name = 'accnt'
        """)
        mssql_result = cursor.fetchall()
        print(f"   MS SQL индексы для accnt: {len(mssql_result)}")
        for idx in mssql_result:
            print(f"     {idx[1]} (table_id: {idx[2]})")
        
        cursor.execute("""
            SELECT pi.id, pi.index_name, pi.table_id, pt.object_name
            FROM mcl.postgres_indexes pi
            JOIN mcl.postgres_tables pt ON pi.table_id = pt.id
            WHERE pt.object_name = 'accnt'
        """)
        pg_result = cursor.fetchall()
        print(f"   PostgreSQL индексы для accnt: {len(pg_result)}")
        for idx in pg_result:
            print(f"     {idx[1]} (table_id: {idx[2]})")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Добавление table_id завершено успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_table_id_direct()
    sys.exit(0 if success else 1)