#!/usr/bin/env python3
"""
Скрипт для проверки структуры таблиц
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import ConfigLoader
import psycopg2


def check_table_structure():
    """Проверка структуры таблиц"""
    
    print("🔍 Проверка структуры таблиц")
    print("=" * 50)
    
    try:
        # Загружаем конфигурацию
        config_loader = ConfigLoader()
        pg_config = config_loader.get_database_config('postgres')
        pg_config_clean = {
            'host': pg_config['host'],
            'port': pg_config['port'], 
            'database': pg_config['database'],
            'user': pg_config['user'],
            'password': pg_config['password']
        }
        
        # Подключаемся к базе
        conn = psycopg2.connect(**pg_config_clean)
        cursor = conn.cursor()
        
        # Проверяем структуру postgres_indexes
        print("📋 Структура таблицы mcl.postgres_indexes:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema = 'mcl' AND table_name = 'postgres_indexes'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        # Проверяем данные в postgres_indexes
        print(f"\n📋 Данные в mcl.postgres_indexes:")
        cursor.execute("SELECT COUNT(*) FROM mcl.postgres_indexes")
        count = cursor.fetchone()[0]
        print(f"  Всего записей: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM mcl.postgres_indexes LIMIT 3")
            rows = cursor.fetchall()
            for i, row in enumerate(rows, 1):
                print(f"  Запись {i}: {row}")
        
        # Проверяем связь с таблицами
        print(f"\n📋 Проверяем связь с таблицами:")
        cursor.execute("""
            SELECT pt.object_name, COUNT(pi.id) as index_count
            FROM mcl.postgres_tables pt
            LEFT JOIN mcl.postgres_indexes pi ON pt.id = pi.table_id
            WHERE pt.object_name = 'accnt'
            GROUP BY pt.id, pt.object_name
        """)
        
        result = cursor.fetchone()
        if result:
            table_name, index_count = result
            print(f"  Таблица {table_name}: {index_count} индексов")
        else:
            print("  Таблица accnt не найдена")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    success = check_table_structure()
    sys.exit(0 if success else 1)

