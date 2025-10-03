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
    
    print("=== Структура mssql_indexes ===")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'mcl' AND table_name = 'mssql_indexes'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"{col[0]}: {col[1]}")
    
    print("\n=== Структура mssql_tables ===")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'mcl' AND table_name = 'mssql_tables'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"{col[0]}: {col[1]}")
    
    print("\n=== Данные в mssql_tables ===")
    cursor.execute("SELECT id, object_name FROM mcl.mssql_tables WHERE object_name = 'accnt'")
    tables = cursor.fetchall()
    print(f"Таблицы accnt: {tables}")
    
    if tables:
        table_id = tables[0][0]
        print(f"\n=== Индексы для таблицы {table_id} ===")
        cursor.execute("SELECT id, index_name, is_unique, is_primary_key FROM mcl.mssql_indexes WHERE table_id = %s", (table_id,))
        indexes = cursor.fetchall()
        print(f"Найдено индексов: {len(indexes)}")
        for idx in indexes:
            print(f"  {idx[1]} - unique: {idx[2]}, pk: {idx[3]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Ошибка: {e}")
    sys.exit(1)