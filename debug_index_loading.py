#!/usr/bin/env python3
import psycopg2
import sys
import os
sys.path.append('/home/alex/projects/sql/femcl')
from config.config_loader import ConfigLoader

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
    
    print("=== Отладка загрузки индексов ===")
    
    # Проверяем запрос из TableModel
    cursor.execute("""
        SELECT 
            pi.id,
            pi.index_name,
            pi.original_index_name,
            pi.index_type,
            pi.is_unique,
            pi.is_primary_key,
            pi.migration_status,
            pi.migration_date,
            pi.error_message,
            pi.fill_factor,
            pi.is_concurrent,
            pi.name_conflict_resolved,
            pi.name_conflict_reason,
            pi.alternative_name,
            pi.postgres_definition,
            pi.source_index_id
        FROM mcl.postgres_indexes pi
        WHERE pi.source_index_id IN (
            SELECT mi.id 
            FROM mcl.mssql_indexes mi
            JOIN mcl.mssql_index_columns mic ON mi.id = mic.index_id
            JOIN mcl.mssql_columns mc ON mic.column_id = mc.id
            JOIN mcl.mssql_tables mt ON mc.table_id = mt.id
            WHERE mt.object_name = %s
        )
        ORDER BY pi.index_name
    """, ('accnt',))
    
    indexes_data = cursor.fetchall()
    print(f"Найдено индексов: {len(indexes_data)}")
    
    for idx in indexes_data:
        print(f"  {idx[1]} (ID: {idx[0]}, source: {idx[15]})")
    
    # Проверяем подзапрос отдельно
    print("\n=== Проверка подзапроса ===")
    cursor.execute("""
        SELECT mi.id 
        FROM mcl.mssql_indexes mi
        JOIN mcl.mssql_index_columns mic ON mi.id = mic.index_id
        JOIN mcl.mssql_columns mc ON mic.column_id = mc.id
        JOIN mcl.mssql_tables mt ON mc.table_id = mt.id
        WHERE mt.object_name = %s
    """, ('accnt',))
    
    source_ids = cursor.fetchall()
    print(f"Исходные ID индексов: {[row[0] for row in source_ids]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)