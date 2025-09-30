#!/usr/bin/env python3
"""
Проверка схемы mcl в PostgreSQL
"""
import psycopg2
from rich.console import Console

console = Console()

def check_mcl_schema():
    """Проверка существования таблиц в схеме mcl"""
    try:
        # Подключение к PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="fish_eye",
            user="postgres",
            password="postgres"
        )
        cursor = conn.cursor()
        
        # Получаем список таблиц в схеме mcl
        cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'mcl' 
        ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        console.print("[blue]📋 Таблицы в схеме mcl:[/blue]")
        
        for table in tables:
            console.print(f"  - {table[0]}")
        
        # Проверяем соответствие с описанием в правилах
        expected_tables = [
            'mssql_objects', 'postgres_objects',
            'mssql_tables', 'postgres_tables',
            'mssql_columns', 'postgres_columns',
            'mssql_indexes', 'postgres_indexes',
            'mssql_primary_keys', 'postgres_primary_keys',
            'mssql_foreign_keys', 'postgres_foreign_keys',
            'mssql_unique_constraints', 'postgres_unique_constraints',
            'mssql_check_constraints', 'postgres_check_constraints',
            'mssql_default_constraints', 'postgres_default_constraints',
            'mssql_triggers', 'postgres_triggers',
            'mssql_identity_columns', 'postgres_sequences',
            'problems_tb_slt_mp'
        ]
        
        existing_tables = [table[0] for table in tables]
        
        console.print("\n[blue]🔍 Проверка соответствия с описанием в правилах:[/blue]")
        
        missing_tables = []
        extra_tables = []
        
        for expected in expected_tables:
            if expected not in existing_tables:
                missing_tables.append(expected)
        
        for existing in existing_tables:
            if existing not in expected_tables:
                extra_tables.append(existing)
        
        if missing_tables:
            console.print(f"[red]❌ Отсутствующие таблицы: {missing_tables}[/red]")
        else:
            console.print("[green]✅ Все ожидаемые таблицы присутствуют[/green]")
        
        if extra_tables:
            console.print(f"[yellow]⚠️ Дополнительные таблицы: {extra_tables}[/yellow]")
        
        # Проверяем структуру ключевых таблиц
        console.print("\n[blue]📊 Структура ключевых таблиц:[/blue]")
        
        key_tables = ['mssql_objects', 'postgres_objects', 'mssql_tables', 'postgres_tables']
        
        for table in key_tables:
            if table in existing_tables:
                cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'mcl' AND table_name = '{table}'
                ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                console.print(f"\n[blue]{table}:[/blue]")
                for col in columns:
                    console.print(f"  {col[0]}: {col[1]}")
        
        conn.close()
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка: {e}[/red]")
        return False

if __name__ == "__main__":
    check_mcl_schema()