#!/usr/bin/env python3
"""
Анализ архитектуры индексов в системе FEMCL
"""

import psycopg2
import sys
import os
sys.path.append('/home/alex/projects/sql/femcl')
from config.config_loader import ConfigLoader

def analyze_index_architecture():
    """Анализ архитектуры индексов"""
    
    print("🔍 Анализ архитектуры индексов в системе FEMCL")
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
        
        print("📋 Текущая архитектура:")
        print("\n1. MS SQL структура:")
        cursor.execute("""
            SELECT 
                mt.object_name as table_name,
                mi.index_name,
                mi.is_primary_key,
                mi.is_unique,
                COUNT(mic.id) as column_count
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
        for table, idx_name, is_pk, is_unique, col_count in mssql_indexes:
            print(f"   - {idx_name} ({'PK' if is_pk else ''} {'UNIQUE' if is_unique else ''}) - {col_count} колонок")
        
        print("\n2. PostgreSQL структура:")
        cursor.execute("""
            SELECT 
                pi.index_name,
                pi.is_primary_key,
                pi.is_unique,
                pi.migration_status,
                COUNT(pic.id) as column_count
            FROM mcl.postgres_indexes pi
            LEFT JOIN mcl.postgres_index_columns pic ON pi.id = pic.index_id
            WHERE pi.source_index_id IN (
                SELECT mi.id 
                FROM mcl.mssql_indexes mi
                JOIN mcl.mssql_index_columns mic ON mi.id = mic.index_id
                JOIN mcl.mssql_columns mc ON mic.column_id = mc.id
                JOIN mcl.mssql_tables mt ON mc.table_id = mt.id
                WHERE mt.object_name = 'accnt'
            )
            GROUP BY pi.id, pi.index_name, pi.is_primary_key, pi.is_unique, pi.migration_status
            ORDER BY pi.index_name
        """)
        
        pg_indexes = cursor.fetchall()
        print(f"   Найдено индексов в PostgreSQL: {len(pg_indexes)}")
        for idx_name, is_pk, is_unique, status, col_count in pg_indexes:
            print(f"   - {idx_name} ({'PK' if is_pk else ''} {'UNIQUE' if is_unique else ''}) - статус: {status} - {col_count} колонок")
        
        print("\n3. Проблемы текущей архитектуры:")
        print("   ❌ postgres_indexes НЕ связана напрямую с postgres_tables")
        print("   ❌ Связь только через source_index_id -> mssql_indexes -> mssql_index_columns -> mssql_columns -> mssql_tables")
        print("   ❌ Сложные запросы для поиска индексов таблицы")
        print("   ❌ Нет прямого способа получить все индексы таблицы")
        
        print("\n4. Статистика связей:")
        cursor.execute("SELECT COUNT(*) FROM mcl.postgres_indexes WHERE source_index_id IS NOT NULL")
        with_source = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM mcl.postgres_indexes WHERE source_index_id IS NULL")
        without_source = cursor.fetchone()[0]
        print(f"   Индексов с source_index_id: {with_source}")
        print(f"   Индексов без source_index_id: {without_source}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = analyze_index_architecture()
    sys.exit(0 if success else 1)