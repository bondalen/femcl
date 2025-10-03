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
    
    # Ищем через mssql_index_columns
    cursor.execute("""
        SELECT 
            mi.id,
            mi.index_name,
            mi.is_unique,
            mi.is_primary_key,
            mic.column_name,
            mic.ordinal_position,
            mic.is_descending
        FROM mcl.mssql_indexes mi
        JOIN mcl.mssql_index_columns mic ON mi.id = mic.index_id
        JOIN mcl.mssql_tables mt ON mic.table_id = mt.id
        WHERE mt.object_name = 'accnt'
        ORDER BY mi.index_name, mic.ordinal_position
    """)
    
    indexes_data = cursor.fetchall()
    print(f"Найдено записей индексов для accnt: {len(indexes_data)}")
    
    # Группируем по индексам
    indexes = {}
    for row in indexes_data:
        index_id = row[0]
        if index_id not in indexes:
            indexes[index_id] = {
                'name': row[1],
                'is_unique': row[2],
                'is_primary_key': row[3],
                'columns': []
            }
        indexes[index_id]['columns'].append({
            'name': row[4],
            'position': row[5],
            'is_descending': row[6]
        })
    
    print(f"Уникальных индексов: {len(indexes)}")
    for index_id, index_info in indexes.items():
        print(f"\n  Индекс {index_info['name']} (ID: {index_id}):")
        print(f"    Уникальный: {index_info['is_unique']}")
        print(f"    Первичный ключ: {index_info['is_primary_key']}")
        print(f"    Колонки ({len(index_info['columns'])}):")
        for col in index_info['columns']:
            direction = "DESC" if col['is_descending'] else "ASC"
            print(f"      - {col['name']} {direction} (позиция: {col['position']})")
    
    print("\n=== Проверка postgres_indexes для accnt ===")
    # Ищем соответствующие postgres индексы
    cursor.execute("""
        SELECT 
            pi.id,
            pi.index_name,
            pi.original_index_name,
            pi.index_type,
            pi.is_unique,
            pi.is_primary_key,
            pi.migration_status,
            pi.source_index_id
        FROM mcl.postgres_indexes pi
        WHERE pi.source_index_id IN (
            SELECT mi.id 
            FROM mcl.mssql_indexes mi
            JOIN mcl.mssql_index_columns mic ON mi.id = mic.index_id
            JOIN mcl.mssql_tables mt ON mic.table_id = mt.id
            WHERE mt.object_name = 'accnt'
        )
        ORDER BY pi.index_name
    """)
    
    pg_indexes = cursor.fetchall()
    print(f"Найдено postgres индексов для accnt: {len(pg_indexes)}")
    
    for idx in pg_indexes:
        print(f"  {idx[1]} (исходный ID: {idx[7]}) - {idx[3]} {'UNIQUE' if idx[4] else ''} {'PK' if idx[5] else ''} - статус: {idx[6]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Ошибка: {e}")
    sys.exit(1)