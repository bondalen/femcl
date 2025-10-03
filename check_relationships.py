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
    
    print("=== Поиск связей между таблицами и индексами ===")
    
    # Проверяем, есть ли таблица mssql_index_columns
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'mcl' AND table_name LIKE '%index%'
        ORDER BY table_name
    """)
    index_tables = cursor.fetchall()
    print("Таблицы с 'index' в названии:")
    for table in index_tables:
        print(f"  {table[0]}")
    
    print("\n=== Проверка mssql_index_columns ===")
    try:
        cursor.execute("SELECT COUNT(*) FROM mcl.mssql_index_columns")
        count = cursor.fetchone()[0]
        print(f"Записей в mssql_index_columns: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM mcl.mssql_index_columns LIMIT 3")
            rows = cursor.fetchall()
            print("Примеры записей:")
            for row in rows:
                print(f"  {row}")
    except Exception as e:
        print(f"Ошибка при проверке mssql_index_columns: {e}")
    
    print("\n=== Проверка postgres_index_columns ===")
    try:
        cursor.execute("SELECT COUNT(*) FROM mcl.postgres_index_columns")
        count = cursor.fetchone()[0]
        print(f"Записей в postgres_index_columns: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM mcl.postgres_index_columns LIMIT 3")
            rows = cursor.fetchall()
            print("Примеры записей:")
            for row in rows:
                print(f"  {row}")
    except Exception as e:
        print(f"Ошибка при проверке postgres_index_columns: {e}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Ошибка: {e}")
    sys.exit(1)