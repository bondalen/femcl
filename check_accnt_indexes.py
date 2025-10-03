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
    
    print("=== Поиск индексов для таблицы accnt ===")
    
    # Ищем индексы через связь с исходными индексами
    cursor.execute("""
        SELECT 
            pi.id,
            pi.index_name,
            pi.original_index_name,
            pi.index_type,
            pi.is_unique,
            pi.is_primary_key,
            pi.migration_status,
            mi.index_name as source_index_name
        FROM mcl.postgres_indexes pi
        JOIN mcl.mssql_indexes mi ON pi.source_index_id = mi.id
        JOIN mcl.mssql_tables mt ON mi.table_id = mt.id
        WHERE mt.object_name = 'accnt'
        ORDER BY pi.index_name
    """)
    
    indexes = cursor.fetchall()
    print(f"Найдено индексов для accnt: {len(indexes)}")
    
    for idx in indexes:
        print(f"  {idx[1]} (исходный: {idx[7]}) - {idx[3]} {'UNIQUE' if idx[4] else ''} {'PK' if idx[5] else ''} - статус: {idx[6]}")
    
    print("\n=== Проверка колонок индексов ===")
    for idx in indexes:
        index_id = idx[0]
        index_name = idx[1]
        
        cursor.execute("""
            SELECT column_name, ordinal_position, is_descending
            FROM mcl.postgres_index_columns 
            WHERE index_id = %s
            ORDER BY ordinal_position
        """, (index_id,))
        
        columns = cursor.fetchall()
        print(f"  {index_name}: {len(columns)} колонок")
        for col in columns:
            direction = "DESC" if col[2] else "ASC"
            print(f"    - {col[0]} {direction} (позиция: {col[1]})")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Ошибка: {e}")
    sys.exit(1)