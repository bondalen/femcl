#!/usr/bin/env python3
"""
Исправление согласованности table_id между MS SQL и PostgreSQL
"""

import psycopg2
import sys
import os
sys.path.append('/home/alex/projects/sql/femcl')
from config.config_loader import ConfigLoader

def fix_table_id_consistency():
    """Исправление согласованности table_id"""
    
    print("🔧 Исправление согласованности table_id")
    print("=" * 50)
    
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
        
        print("1. Анализ проблемы:")
        cursor.execute("""
            SELECT 
                mi.id as mssql_index_id,
                mi.index_name as mssql_index_name,
                mi.table_id as mssql_table_id,
                mt.object_name as mssql_table_name,
                pi.id as postgres_index_id,
                pi.index_name as postgres_index_name,
                pi.table_id as postgres_table_id,
                pt.object_name as postgres_table_name,
                pi.source_index_id
            FROM mcl.mssql_indexes mi
            JOIN mcl.postgres_indexes pi ON mi.id = pi.source_index_id
            JOIN mcl.mssql_tables mt ON mi.table_id = mt.id
            JOIN mcl.postgres_tables pt ON pi.table_id = pt.id
            WHERE mt.object_name = 'accnt'
        """)
        
        results = cursor.fetchall()
        for result in results:
            mssql_id, mssql_name, mssql_table_id, mssql_table_name, pg_id, pg_name, pg_table_id, pg_table_name, source_id = result
            print(f"   MS SQL: {mssql_name} (table_id: {mssql_table_id}, table: {mssql_table_name})")
            print(f"   PG: {pg_name} (table_id: {pg_table_id}, table: {pg_table_name})")
            print(f"   Source ID: {source_id}")
            print(f"   Проблема: table_id не совпадают ({mssql_table_id} vs {pg_table_id})")
        
        print("\n2. Проверяем связь между таблицами:")
        cursor.execute("""
            SELECT 
                mt.id as mssql_table_id,
                mt.object_name as mssql_table_name,
                pt.id as postgres_table_id,
                pt.object_name as postgres_table_name,
                pt.source_table_id
            FROM mcl.mssql_tables mt
            JOIN mcl.postgres_tables pt ON mt.id = pt.source_table_id
            WHERE mt.object_name = 'accnt'
        """)
        
        table_links = cursor.fetchall()
        for link in table_links:
            mssql_id, mssql_name, pg_id, pg_name, source_id = link
            print(f"   MS SQL: {mssql_name} (ID: {mssql_id})")
            print(f"   PG: {pg_name} (ID: {pg_id}, source: {source_id})")
            print(f"   Связь: MS SQL ID {mssql_id} -> PG source_table_id {source_id}")
        
        print("\n3. Исправляем table_id в postgres_indexes:")
        # Обновляем table_id в postgres_indexes на основе правильной связи
        cursor.execute("""
            UPDATE mcl.postgres_indexes 
            SET table_id = (
                SELECT pt.id 
                FROM mcl.postgres_tables pt
                JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
                JOIN mcl.mssql_indexes mi ON mt.id = mi.table_id
                WHERE mi.id = postgres_indexes.source_index_id
                LIMIT 1
            )
            WHERE source_index_id IN (
                SELECT mi.id 
                FROM mcl.mssql_indexes mi
                JOIN mcl.mssql_tables mt ON mi.table_id = mt.id
                WHERE mt.object_name = 'accnt'
            )
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        print(f"   ✅ Обновлено записей: {updated_count}")
        
        print("\n4. Проверяем исправление:")
        cursor.execute("""
            SELECT 
                mi.id as mssql_index_id,
                mi.index_name as mssql_index_name,
                mi.table_id as mssql_table_id,
                pi.id as postgres_index_id,
                pi.index_name as postgres_index_name,
                pi.table_id as postgres_table_id,
                pi.source_index_id,
                CASE 
                    WHEN mi.id = pi.source_index_id THEN '✅'
                    ELSE '❌'
                END as source_match,
                CASE 
                    WHEN mi.table_id = (
                        SELECT pt.source_table_id 
                        FROM mcl.postgres_tables pt 
                        WHERE pt.id = pi.table_id
                    ) THEN '✅'
                    ELSE '❌'
                END as table_match
            FROM mcl.mssql_indexes mi
            JOIN mcl.postgres_indexes pi ON mi.id = pi.source_index_id
            JOIN mcl.mssql_tables mt ON mi.table_id = mt.id
            WHERE mt.object_name = 'accnt'
        """)
        
        fixed_results = cursor.fetchall()
        for result in fixed_results:
            mssql_id, mssql_name, mssql_table_id, pg_id, pg_name, pg_table_id, source_id, source_match, table_match = result
            print(f"   Индекс: {mssql_name} -> {pg_name}")
            print(f"     Source ID: {source_match}")
            print(f"     Table ID: {table_match}")
        
        print("\n5. Финальная проверка согласованности:")
        all_consistent = all(result[7] == '✅' and result[8] == '✅' for result in fixed_results)
        
        if all_consistent:
            print("   ✅ Все связи согласованы!")
        else:
            print("   ❌ Остались несогласованности")
        
        cursor.close()
        conn.close()
        
        return all_consistent
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_table_id_consistency()
    sys.exit(0 if success else 1)