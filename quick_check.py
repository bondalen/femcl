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
    
    print("=== Структура postgres_indexes ===")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'mcl' AND table_name = 'postgres_indexes'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"{col[0]}: {col[1]}")
    
    print("\n=== Данные в postgres_indexes ===")
    cursor.execute("SELECT COUNT(*) FROM mcl.postgres_indexes")
    count = cursor.fetchone()[0]
    print(f"Всего записей: {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM mcl.postgres_indexes LIMIT 1")
        row = cursor.fetchone()
        print(f"Пример записи: {row}")
    
    print("\n=== Проверка связи с таблицами ===")
    cursor.execute("SELECT id, object_name FROM mcl.postgres_tables WHERE object_name = 'accnt'")
    tables = cursor.fetchall()
    print(f"Таблицы accnt: {tables}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Ошибка: {e}")
    sys.exit(1)