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
    
    print("=== Структура postgres_index_columns ===")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'mcl' AND table_name = 'postgres_index_columns'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"{col[0]}: {col[1]}")
    
    print("\n=== Примеры данных postgres_index_columns ===")
    cursor.execute("SELECT * FROM mcl.postgres_index_columns LIMIT 5")
    rows = cursor.fetchall()
    for i, row in enumerate(rows, 1):
        print(f"Запись {i}: {row}")
    
    print("\n=== Поиск колонок для индекса pk_accnt (ID: 81) ===")
    cursor.execute("""
        SELECT pic.*, pc.column_name
        FROM mcl.postgres_index_columns pic
        JOIN mcl.postgres_columns pc ON pic.column_id = pc.id
        WHERE pic.index_id = 81
        ORDER BY pic.ordinal_position
    """)
    
    index_columns = cursor.fetchall()
    print(f"Найдено колонок для индекса: {len(index_columns)}")
    for col in index_columns:
        print(f"  {col}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Ошибка: {e}")
    sys.exit(1)