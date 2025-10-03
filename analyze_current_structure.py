#!/usr/bin/env python3
"""
Анализ текущей структуры для добавления table_id в индексы
"""

import psycopg2
import sys
import os
sys.path.append('/home/alex/projects/sql/femcl')
from config.config_loader import ConfigLoader

def analyze_current_structure():
    """Анализ текущей структуры"""
    
    print("🔍 Анализ текущей структуры для добавления table_id")
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
        
        print("1. Анализ структуры mssql_indexes:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema = 'mcl' AND table_name = 'mssql_indexes'
            ORDER BY ordinal_position
        """)
        mssql_columns = cursor.fetchall()
        print("   Колонки:")
        for col in mssql_columns:
            print(f"     {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        print("\n2. Анализ структуры postgres_indexes:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema = 'mcl' AND table_name = 'postgres_indexes'
            ORDER BY ordinal_position
        """)
        pg_columns = cursor.fetchall()
        print("   Колонки:")
        for col in pg_columns:
            print(f"     {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        print("\n3. Проверка связей для таблицы accnt:")
        cursor.execute("""
            SELECT 
                mt.object_name as table_name,
                mt.id as table_id,
                mi.id as index_id,
                mi.index_name,
                mi.is_primary_key,
                mi.is_unique
            FROM mcl.mssql_tables mt
            JOIN mcl.mssql_columns mc ON mt.id = mc.table_id
            JOIN mcl.mssql_index_columns mic ON mc.id = mic.column_id
            JOIN mcl.mssql_indexes mi ON mic.index_id = mi.id
            WHERE mt.object_name = 'accnt'
            GROUP BY mt.id, mt.object_name, mi.id, mi.index_name, mi.is_primary_key, mi.is_unique
            ORDER BY mi.index_name
        """)
        
        mssql_indexes = cursor.fetchall()
        print(f"   Найдено индексов в MS SQL: {len(mssql_indexes)}")
        for table_name, table_id, index_id, index_name, is_pk, is_unique in mssql_indexes:
            print(f"     {index_name} (ID: {index_id}, table_id: {table_id}) - {'PK' if is_pk else ''} {'UNIQUE' if is_unique else ''}")
        
        print("\n4. Проверка связей в PostgreSQL:")
        cursor.execute("""
            SELECT 
                pi.id as pg_index_id,
                pi.index_name as pg_index_name,
                pi.source_index_id,
                pi.is_primary_key,
                pi.is_unique,
                pi.migration_status
            FROM mcl.postgres_indexes pi
            WHERE pi.source_index_id IN (
                SELECT mi.id 
                FROM mcl.mssql_indexes mi
                JOIN mcl.mssql_index_columns mic ON mi.id = mic.index_id
                JOIN mcl.mssql_columns mc ON mic.column_id = mc.id
                JOIN mcl.mssql_tables mt ON mc.table_id = mt.id
                WHERE mt.object_name = 'accnt'
            )
            ORDER BY pi.index_name
        """)
        
        pg_indexes = cursor.fetchall()
        print(f"   Найдено индексов в PostgreSQL: {len(pg_indexes)}")
        for pg_id, pg_name, source_id, is_pk, is_unique, status in pg_indexes:
            print(f"     {pg_name} (ID: {pg_id}, source: {source_id}) - {'PK' if is_pk else ''} {'UNIQUE' if is_unique else ''} - {status}")
        
        print("\n5. Проверка соответствия:")
        if len(mssql_indexes) == len(pg_indexes):
            print("   ✅ Количество индексов совпадает")
        else:
            print(f"   ❌ Количество не совпадает: MS SQL={len(mssql_indexes)}, PG={len(pg_indexes)}")
        
        # Проверяем соответствие по именам
        mssql_names = {row[3] for row in mssql_indexes}
        pg_names = {row[1] for row in pg_indexes}
        if mssql_names == pg_names:
            print("   ✅ Имена индексов соответствуют")
        else:
            print(f"   ❌ Имена не соответствуют: MS SQL={mssql_names}, PG={pg_names}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = analyze_current_structure()
    sys.exit(0 if success else 1)