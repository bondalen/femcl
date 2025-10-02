#!/usr/bin/env python3
"""
Тестирование обновлённых правил создания таблиц с полными элементами
"""
import os
import sys
import yaml
import pyodbc
import psycopg2
from rich.console import Console

# Добавляем путь к проекту
sys.path.append('/home/alex/projects/sql/femcl')

console = Console()

# Загрузка конфигурации
def load_config(config_path="/home/alex/projects/sql/femcl/config/config.yaml"):
    """Загрузка конфигурации из файла"""
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

config = load_config()

# Подключение к PostgreSQL
def get_postgres_connection():
    """Получение подключения к PostgreSQL"""
    postgres_config = config['database']['postgres']
    return psycopg2.connect(
        host=postgres_config['host'],
        port=postgres_config['port'],
        dbname=postgres_config['database'],
        user=postgres_config['user'],
        password=postgres_config['password'],
        connect_timeout=postgres_config['connection_timeout'],
        sslmode=postgres_config['ssl_mode']
    )

def execute_query(query, params=None):
    """Выполнение SQL запроса"""
    conn = get_postgres_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        else:
            conn.commit()
            return []
    finally:
        conn.close()

def get_table_name(target_table_id):
    """Получение имени таблицы по ID"""
    query = "SELECT object_name FROM mcl.postgres_tables WHERE id = %s"
    result = execute_query(query, (target_table_id,))
    return result[0]['object_name'] if result else None

def get_referenced_table_name(referenced_table_id):
    """Получение имени ссылочной таблицы по ID"""
    query = "SELECT object_name FROM mcl.postgres_tables WHERE id = %s"
    result = execute_query(query, (referenced_table_id,))
    return result[0]['object_name'] if result else None

def execute_ddl(ddl):
    """Выполнение DDL команды"""
    console.print(f"[blue]Выполнение DDL: {ddl[:100]}...[/blue]")
    execute_query(ddl)

def generate_table_ddl(target_table_id):
    """Генерация DDL для создания таблицы"""
    query = """
    SELECT 
        pc.column_name,
        pdt.typname_with_params as postgres_type,
        pdt.is_nullable,
        pc.is_identity,
        pc.default_value
    FROM mcl.postgres_tables pt
    JOIN mcl.postgres_columns pc ON pt.id = pc.table_id
    JOIN mcl.postgres_derived_types pdt ON pc.postgres_data_type_id = pdt.id
    WHERE pt.id = %s
    ORDER BY pc.ordinal_position
    """
    columns = execute_query(query, (target_table_id,))
    
    ddl_parts = []
    for col in columns:
        col_def = f"    {col['column_name']} {col['postgres_type']}"
        if col['is_identity']:
            col_def += " GENERATED ALWAYS AS IDENTITY"
        if not col['is_nullable']:
            col_def += " NOT NULL"
        if col['default_value']:
            col_def += f" DEFAULT {col['default_value']}"
        ddl_parts.append(col_def)
    
    table_name = get_table_name(target_table_id)
    ddl = f"CREATE TABLE ags.{table_name} (\n" + ",\n".join(ddl_parts) + "\n);"
    return ddl

def create_primary_keys(target_table_id, table_name):
    """Создание первичных ключей"""
    query = """
    SELECT 
        ppk.constraint_name,
        ppkc.ordinal_position,
        pc.column_name
    FROM mcl.postgres_primary_keys ppk
    JOIN mcl.postgres_primary_key_columns ppkc ON ppk.id = ppkc.primary_key_id
    JOIN mcl.postgres_columns pc ON ppkc.column_id = pc.id
    WHERE ppk.table_id = %s
    ORDER BY ppkc.ordinal_position
    """
    pk_data = execute_query(query, (target_table_id,))
    
    if pk_data:
        columns = [row['column_name'] for row in pk_data]
        constraint_name = pk_data[0]['constraint_name']
        ddl = f"ALTER TABLE ags.{table_name} ADD CONSTRAINT {constraint_name} PRIMARY KEY ({', '.join(columns)});"
        execute_ddl(ddl)
        console.print(f"[green]✅ Первичный ключ {constraint_name} создан[/green]")
    else:
        console.print(f"[yellow]⚠️ Первичные ключи не найдены для {table_name}[/yellow]")

def create_indexes(target_table_id, table_name):
    """Создание индексов"""
    query = """
    SELECT 
        pi.index_name,
        pi.index_type,
        pi.is_unique,
        pic.ordinal_position,
        pc.column_name,
        pic.is_descending
    FROM mcl.postgres_indexes pi
    JOIN mcl.postgres_index_columns pic ON pi.id = pic.index_id
    JOIN mcl.postgres_columns pc ON pic.column_id = pc.id
    WHERE pi.table_id = %s
    ORDER BY pi.index_name, pic.ordinal_position
    """
    index_data = execute_query(query, (target_table_id,))
    
    if index_data:
        # Группировка по индексам
        indexes = {}
        for row in index_data:
            index_name = row['index_name']
            if index_name not in indexes:
                indexes[index_name] = {
                    'is_unique': row['is_unique'],
                    'columns': []
                }
            indexes[index_name]['columns'].append({
                'name': row['column_name'],
                'descending': row['is_descending']
            })
        
        # Создание индексов
        for index_name, index_info in indexes.items():
            # Проверяем, не является ли это индексом первичного ключа
            if index_name.startswith('pk_'):
                console.print(f"[yellow]⚠️ Пропускаем индекс {index_name} (первичный ключ уже создан)[/yellow]")
                continue
                
            columns = []
            for col in index_info['columns']:
                col_def = col['name']
                if col['descending']:
                    col_def += " DESC"
                columns.append(col_def)
            
            unique_keyword = "UNIQUE " if index_info['is_unique'] else ""
            ddl = f"CREATE {unique_keyword}INDEX {index_name} ON ags.{table_name} ({', '.join(columns)});"
            execute_ddl(ddl)
            console.print(f"[green]✅ Индекс {index_name} создан[/green]")
    else:
        console.print(f"[yellow]⚠️ Индексы не найдены для {table_name}[/yellow]")

def create_foreign_keys(target_table_id, table_name):
    """Создание внешних ключей"""
    query = """
    SELECT 
        pfk.constraint_name,
        pfk.referenced_table_id,
        pfkc.ordinal_position,
        pc.column_name,
        pc_ref.column_name as referenced_column_name,
        pfk.delete_action,
        pfk.update_action
    FROM mcl.postgres_foreign_keys pfk
    JOIN mcl.postgres_foreign_key_columns pfkc ON pfk.id = pfkc.foreign_key_id
    JOIN mcl.postgres_columns pc ON pfkc.column_id = pc.id
    JOIN mcl.postgres_columns pc_ref ON pfkc.referenced_column_id = pc_ref.id
    WHERE pfk.table_id = %s
    ORDER BY pfk.constraint_name, pfkc.ordinal_position
    """
    fk_data = execute_query(query, (target_table_id,))
    
    if fk_data:
        # Группировка по внешним ключам
        foreign_keys = {}
        for row in fk_data:
            constraint_name = row['constraint_name']
            if constraint_name not in foreign_keys:
                foreign_keys[constraint_name] = {
                    'referenced_table_id': row['referenced_table_id'],
                    'delete_action': row['delete_action'],
                    'update_action': row['update_action'],
                    'columns': []
                }
            foreign_keys[constraint_name]['columns'].append({
                'column': row['column_name'],
                'referenced_column': row['referenced_column_name']
            })
        
        # Создание внешних ключей
        for constraint_name, fk_info in foreign_keys.items():
            columns = [col['column'] for col in fk_info['columns']]
            referenced_columns = [col['referenced_column'] for col in fk_info['columns']]
            
            # Получение имени ссылочной таблицы
            ref_table_name = get_referenced_table_name(fk_info['referenced_table_id'])
            
            ddl = f"""ALTER TABLE ags.{table_name} 
ADD CONSTRAINT {constraint_name} 
FOREIGN KEY ({', '.join(columns)}) 
REFERENCES ags.{ref_table_name} ({', '.join(referenced_columns)})
ON DELETE {fk_info['delete_action']} ON UPDATE {fk_info['update_action']};"""
            execute_ddl(ddl)
            console.print(f"[green]✅ Внешний ключ {constraint_name} создан[/green]")
    else:
        console.print(f"[yellow]⚠️ Внешние ключи не найдены для {table_name}[/yellow]")

def create_unique_constraints(target_table_id, table_name):
    """Создание уникальных ограничений"""
    query = """
    SELECT 
        puc.constraint_name,
        pucc.ordinal_position,
        pc.column_name
    FROM mcl.postgres_unique_constraints puc
    JOIN mcl.postgres_unique_constraint_columns pucc ON puc.id = pucc.unique_constraint_id
    JOIN mcl.postgres_columns pc ON pucc.column_id = pc.id
    WHERE puc.table_id = %s
    ORDER BY puc.constraint_name, pucc.ordinal_position
    """
    uc_data = execute_query(query, (target_table_id,))
    
    if uc_data:
        # Группировка по уникальным ограничениям
        unique_constraints = {}
        for row in uc_data:
            constraint_name = row['constraint_name']
            if constraint_name not in unique_constraints:
                unique_constraints[constraint_name] = []
            unique_constraints[constraint_name].append(row['column_name'])
        
        # Создание уникальных ограничений
        for constraint_name, columns in unique_constraints.items():
            ddl = f"ALTER TABLE ags.{table_name} ADD CONSTRAINT {constraint_name} UNIQUE ({', '.join(columns)});"
            execute_ddl(ddl)
            console.print(f"[green]✅ Уникальное ограничение {constraint_name} создано[/green]")
    else:
        console.print(f"[yellow]⚠️ Уникальные ограничения не найдены для {table_name}[/yellow]")

def create_check_constraints(target_table_id, table_name):
    """Создание проверочных ограничений"""
    query = """
    SELECT 
        pcc.constraint_name,
        pcc.definition
    FROM mcl.postgres_check_constraints pcc
    WHERE pcc.table_id = %s
    """
    cc_data = execute_query(query, (target_table_id,))
    
    if cc_data:
        for row in cc_data:
            ddl = f"ALTER TABLE ags.{table_name} ADD CONSTRAINT {row['constraint_name']} CHECK ({row['definition']});"
            execute_ddl(ddl)
            console.print(f"[green]✅ Проверочное ограничение {row['constraint_name']} создано[/green]")
    else:
        console.print(f"[yellow]⚠️ Проверочные ограничения не найдены для {table_name}[/yellow]")

def create_triggers(target_table_id, table_name):
    """Создание триггеров"""
    query = """
    SELECT 
        pt.trigger_name,
        pt.event_type,
        pt.trigger_type,
        pt.function_name
    FROM mcl.postgres_triggers pt
    WHERE pt.table_id = %s
    """
    trigger_data = execute_query(query, (target_table_id,))
    
    if trigger_data:
        for row in trigger_data:
            ddl = f"""CREATE TRIGGER {row['trigger_name']}
    {row['trigger_type']} {row['event_type']} ON ags.{table_name}
    FOR EACH ROW
    EXECUTE FUNCTION {row['function_name']};"""
            execute_ddl(ddl)
            console.print(f"[green]✅ Триггер {row['trigger_name']} создан[/green]")
    else:
        console.print(f"[yellow]⚠️ Триггеры не найдены для {table_name}[/yellow]")

def create_sequences(target_table_id, table_name):
    """Создание последовательностей"""
    query = """
    SELECT 
        ps.sequence_name,
        ps.start_value,
        ps.increment_value
    FROM mcl.postgres_sequences ps
    WHERE ps.table_id = %s
    """
    sequence_data = execute_query(query, (target_table_id,))
    
    if sequence_data:
        for row in sequence_data:
            ddl = f"""CREATE SEQUENCE ags.{row['sequence_name']}
    START WITH {row['start_value']}
    INCREMENT BY {row['increment_value']};"""
            execute_ddl(ddl)
            console.print(f"[green]✅ Последовательность {row['sequence_name']} создана[/green]")
    else:
        console.print(f"[yellow]⚠️ Последовательности не найдены для {table_name}[/yellow]")

def verify_table_elements(table_name):
    """Проверка полноты всех элементов таблицы"""
    query = """
    SELECT 
        'columns' as element_type,
        COUNT(*) as count
    FROM information_schema.columns 
    WHERE table_schema = 'ags' AND table_name = %s

    UNION ALL

    SELECT 
        'primary_keys' as element_type,
        COUNT(*) as count
    FROM information_schema.table_constraints 
    WHERE table_schema = 'ags' AND table_name = %s 
    AND constraint_type = 'PRIMARY KEY'

    UNION ALL

    SELECT 
        'indexes' as element_type,
        COUNT(*) as count
    FROM pg_indexes 
    WHERE schemaname = 'ags' AND tablename = %s

    UNION ALL

    SELECT 
        'foreign_keys' as element_type,
        COUNT(*) as count
    FROM information_schema.table_constraints 
    WHERE table_schema = 'ags' AND table_name = %s 
    AND constraint_type = 'FOREIGN KEY'

    UNION ALL

    SELECT 
        'unique_constraints' as element_type,
        COUNT(*) as count
    FROM information_schema.table_constraints 
    WHERE table_schema = 'ags' AND table_name = %s 
    AND constraint_type = 'UNIQUE'

    UNION ALL

    SELECT 
        'check_constraints' as element_type,
        COUNT(*) as count
    FROM information_schema.table_constraints 
    WHERE table_schema = 'ags' AND table_name = %s 
    AND constraint_type = 'CHECK'

    UNION ALL

    SELECT 
        'triggers' as element_type,
        COUNT(*) as count
    FROM information_schema.triggers 
    WHERE event_object_schema = 'ags' AND event_object_table = %s

    UNION ALL

    SELECT 
        'sequences' as element_type,
        COUNT(*) as count
    FROM information_schema.sequences 
    WHERE sequence_schema = 'ags' AND sequence_name LIKE %s
    """
    results = execute_query(query, (table_name, table_name, table_name, table_name, table_name, table_name, table_name, f"{table_name}%"))
    
    console.print(f"[blue]📊 Результаты проверки элементов таблицы {table_name}:[/blue]")
    for result in results:
        console.print(f"  {result['element_type']}: {result['count']}")
    
    return True

def create_table_structure(target_table_id, table_name):
    """Создание полной структуры таблицы включая все элементы"""
    
    console.print(f"[bold blue]🚀 Создание структуры таблицы {table_name}[/bold blue]")
    
    try:
        # 4.1 Создание таблицы
        console.print("[blue]4.1 Создание таблицы[/blue]")
        create_table_ddl = generate_table_ddl(target_table_id)
        execute_ddl(create_table_ddl)
        
        # 4.4 Создание первичных ключей
        console.print("[blue]4.4 Создание первичных ключей[/blue]")
        create_primary_keys(target_table_id, table_name)
        
        # 4.5 Создание индексов
        console.print("[blue]4.5 Создание индексов[/blue]")
        create_indexes(target_table_id, table_name)
        
        # 4.6 Создание внешних ключей
        console.print("[blue]4.6 Создание внешних ключей[/blue]")
        create_foreign_keys(target_table_id, table_name)
        
        # 4.7 Создание уникальных ограничений
        console.print("[blue]4.7 Создание уникальных ограничений[/blue]")
        create_unique_constraints(target_table_id, table_name)
        
        # 4.8 Создание проверочных ограничений
        console.print("[blue]4.8 Создание проверочных ограничений[/blue]")
        create_check_constraints(target_table_id, table_name)
        
        # 4.9 Создание триггеров
        console.print("[blue]4.9 Создание триггеров[/blue]")
        create_triggers(target_table_id, table_name)
        
        # 4.10 Создание последовательностей
        console.print("[blue]4.10 Создание последовательностей[/blue]")
        create_sequences(target_table_id, table_name)
        
        # 4.11 Проверка полноты элементов
        console.print("[blue]4.11 Проверка полноты элементов[/blue]")
        verify_table_elements(table_name)
        
        console.print(f"[green]✅ Структура таблицы {table_name} создана полностью![/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка создания структуры таблицы: {e}[/red]")
        return False

def test_table_creation(table_name):
    """Тестирование создания таблицы с обновлёнными правилами"""
    
    console.print(f"[bold green]🧪 ТЕСТИРОВАНИЕ СОЗДАНИЯ ТАБЛИЦЫ {table_name}[/bold green]")
    
    # Получение ID таблицы
    query = """
    SELECT 
        mt.id as source_table_id,
        pt.id as target_table_id,
        pt.object_name as target_table_name
    FROM mcl.mssql_tables mt
    JOIN mcl.postgres_tables pt ON mt.id = pt.source_table_id
    WHERE mt.object_name = %s
    """
    table_info = execute_query(query, (table_name,))
    
    if not table_info:
        console.print(f"[red]❌ Таблица {table_name} не найдена в метаданных[/red]")
        return False
    
    target_table_id = table_info[0]['target_table_id']
    target_table_name = table_info[0]['target_table_name']
    
    console.print(f"📊 Исходная таблица: {table_name}")
    console.print(f"📊 Целевая таблица: {target_table_name} (ID: {target_table_id})")
    
    # Создание структуры таблицы
    success = create_table_structure(target_table_id, target_table_name)
    
    if success:
        console.print(f"[green]🎉 ТЕСТ ПРОЙДЕН: Таблица {table_name} создана успешно![/green]")
    else:
        console.print(f"[red]💥 ТЕСТ ПРОВАЛЕН: Ошибка создания таблицы {table_name}[/red]")
    
    return success

if __name__ == "__main__":
    # Тестируем создание всех трёх таблиц
    tables_to_test = ['accnt', 'cn', 'cnInvCmmAgN']
    
    console.print("[bold blue]🧪 ТЕСТИРОВАНИЕ ОБНОВЛЁННЫХ ПРАВИЛ СОЗДАНИЯ ТАБЛИЦ[/bold blue]")
    console.print("=" * 80)
    
    results = []
    for table_name in tables_to_test:
        console.print("\n" + "=" * 80)
        success = test_table_creation(table_name)
        results.append((table_name, success))
        console.print("=" * 80)
    
    # Итоговый отчёт
    console.print("\n[bold blue]📊 ИТОГОВЫЙ ОТЧЁТ ТЕСТИРОВАНИЯ:[/bold blue]")
    for table_name, success in results:
        status = "✅ УСПЕШНО" if success else "❌ ПРОВАЛЕН"
        console.print(f"  {table_name}: {status}")
    
    total_success = sum(1 for _, success in results if success)
    console.print(f"\n[bold green]Результат: {total_success}/{len(results)} тестов пройдено[/bold green]")







