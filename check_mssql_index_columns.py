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
    
    print("=== Структура mssql_index_columns ===")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'mcl' AND table_name = 'mssql_index_columns'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"{col[0]}: {col[1]}")
    
    print("\n=== Примеры данных mssql_index_columns ===")
    cursor.execute("SELECT * FROM mcl.mssql_index_columns LIMIT 5")
    rows = cursor.fetchall()
    for i, row in enumerate(rows, 1):
        print(f"Запись {i}: {row}")
    
    print("\n=== Поиск индексов для accnt через mssql_indexes ===")
    # Проверяем, есть ли связь между mssql_indexes и mssql_tables
    cursor.execute("SELECT * FROM mcl.mssql_indexes LIMIT 3")
    index_rows = cursor.fetchall()
    print("Примеры mssql_indexes:")
    for i, row in enumerate(index_rows, 1):
        print(f"  {i}: {row}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Ошибка: {e}")
    sys.exit(1)