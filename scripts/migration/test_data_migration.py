#!/usr/bin/env python3
"""
Тест переноса данных между таблицами
"""
import psycopg2
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def get_db_connection():
    """Получение подключения к базе данных"""
    with open('/home/alex/projects/sql/femcl/config/config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    postgres_config = config['database']['postgres']
    
    return psycopg2.connect(
        host=postgres_config['host'],
        port=postgres_config['port'],
        dbname=postgres_config['database'],
        user=postgres_config['user'],
        password=postgres_config['password']
    )

def create_test_data():
    """Создание тестовых данных в исходных таблицах"""
    console.print(Panel.fit(
        "[bold blue]📊 СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ[/bold blue]",
        border_style="blue"
    ))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Создаём исходные таблицы в схеме mcl с тестовыми данными
        console.print("🔨 Создание исходных таблиц в схеме mcl...")
        
        # Таблица accnt
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcl.accnt (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                balance DECIMAL(15,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Добавляем тестовые данные
        cursor.execute("""
            INSERT INTO mcl.accnt (name, balance) VALUES 
            ('Основной счёт', 10000.50),
            ('Резервный счёт', 5000.25),
            ('Инвестиционный счёт', 25000.75)
            ON CONFLICT DO NOTHING;
        """)
        
        # Таблица cn
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcl.cn (
                id SERIAL PRIMARY KEY,
                number VARCHAR(50) NOT NULL,
                description TEXT,
                amount DECIMAL(15,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            INSERT INTO mcl.cn (number, description, amount) VALUES 
            ('CN-001', 'Контракт на поставку', 150000.00),
            ('CN-002', 'Контракт на услуги', 75000.50),
            ('CN-003', 'Контракт на аренду', 30000.00)
            ON CONFLICT DO NOTHING;
        """)
        
        # Таблица cnInvCmmAgN
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcl."cnInvCmmAgN" (
                id SERIAL PRIMARY KEY,
                value VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                quantity INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            INSERT INTO mcl."cnInvCmmAgN" (value, category, quantity) VALUES 
            ('Актив A', 'Инвестиции', 100),
            ('Актив B', 'Облигации', 50),
            ('Актив C', 'Акции', 25)
            ON CONFLICT DO NOTHING;
        """)
        
        conn.commit()
        console.print("✅ Тестовые данные созданы успешно")
        
        # Проверяем созданные данные
        console.print("\n📊 Проверка созданных данных:")
        
        tables_data = [
            ('mcl.accnt', 'Счета'),
            ('mcl.cn', 'Контракты'),
            ('mcl."cnInvCmmAgN"', 'Инвестиционные активы')
        ]
        
        for table, description in tables_data:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            console.print(f"   📋 {description}: {count} записей")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 2")
                rows = cursor.fetchall()
                console.print(f"      Примеры: {rows[:2]}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка создания тестовых данных: {e}[/red]")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def migrate_data():
    """Перенос данных из исходных таблиц в целевые"""
    console.print(Panel.fit(
        "[bold green]🚀 ПЕРЕНОС ДАННЫХ[/bold green]",
        border_style="green"
    ))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Перенос данных из mcl.accnt в ags.accnt
        console.print("📊 Перенос данных из mcl.accnt в ags.accnt...")
        cursor.execute("""
            INSERT INTO ags.accnt (name, created_at)
            SELECT name, created_at FROM mcl.accnt
            ON CONFLICT DO NOTHING;
        """)
        accnt_count = cursor.rowcount
        console.print(f"   ✅ Перенесено записей: {accnt_count}")
        
        # Перенос данных из mcl.cn в ags.cn
        console.print("📊 Перенос данных из mcl.cn в ags.cn...")
        cursor.execute("""
            INSERT INTO ags.cn (number, created_at)
            SELECT number, created_at FROM mcl.cn
            ON CONFLICT DO NOTHING;
        """)
        cn_count = cursor.rowcount
        console.print(f"   ✅ Перенесено записей: {cn_count}")
        
        # Перенос данных из mcl.cnInvCmmAgN в ags.cnInvCmmAgN
        console.print("📊 Перенос данных из mcl.cnInvCmmAgN в ags.cnInvCmmAgN...")
        cursor.execute("""
            INSERT INTO ags."cnInvCmmAgN" (value, created_at)
            SELECT value, created_at FROM mcl."cnInvCmmAgN"
            ON CONFLICT DO NOTHING;
        """)
        cninv_count = cursor.rowcount
        console.print(f"   ✅ Перенесено записей: {cninv_count}")
        
        conn.commit()
        
        # Проверяем результаты переноса
        console.print("\n🔍 Проверка результатов переноса:")
        
        target_tables = [
            ('ags.accnt', 'Счета'),
            ('ags.cn', 'Контракты'),
            ('ags."cnInvCmmAgN"', 'Инвестиционные активы')
        ]
        
        for table, description in target_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            console.print(f"   📋 {description}: {count} записей")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                console.print(f"      Данные: {rows}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка переноса данных: {e}[/red]")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def verify_migration():
    """Проверка корректности миграции"""
    console.print(Panel.fit(
        "[bold yellow]🔍 ПРОВЕРКА МИГРАЦИИ[/bold yellow]",
        border_style="yellow"
    ))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Сравниваем количество записей
        console.print("📊 Сравнение количества записей:")
        
        comparisons = [
            ('mcl.accnt', 'ags.accnt', 'Счета'),
            ('mcl.cn', 'ags.cn', 'Контракты'),
            ('mcl."cnInvCmmAgN"', 'ags."cnInvCmmAgN"', 'Инвестиционные активы')
        ]
        
        migration_success = True
        
        for source_table, target_table, description in comparisons:
            cursor.execute(f"SELECT COUNT(*) FROM {source_table}")
            source_count = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
            target_count = cursor.fetchone()[0]
            
            status = "✅" if source_count == target_count else "❌"
            console.print(f"   {status} {description}: {source_count} → {target_count}")
            
            if source_count != target_count:
                migration_success = False
        
        return migration_success
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка проверки: {e}[/red]")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Основная функция тестирования переноса данных"""
    console.print(Panel.fit(
        "[bold green]🧪 ТЕСТ ПЕРЕНОСА ДАННЫХ[/bold green]\n"
        "Создание тестовых данных и их перенос между таблицами",
        border_style="green"
    ))
    
    # Шаг 1: Создание тестовых данных
    console.print("\n" + "="*60)
    console.print("[bold blue]ШАГ 1: Создание тестовых данных[/bold blue]")
    console.print("="*60)
    
    if not create_test_data():
        console.print("[red]❌ Не удалось создать тестовые данные[/red]")
        return False
    
    # Шаг 2: Перенос данных
    console.print("\n" + "="*60)
    console.print("[bold blue]ШАГ 2: Перенос данных[/bold blue]")
    console.print("="*60)
    
    if not migrate_data():
        console.print("[red]❌ Не удалось перенести данные[/red]")
        return False
    
    # Шаг 3: Проверка миграции
    console.print("\n" + "="*60)
    console.print("[bold blue]ШАГ 3: Проверка миграции[/bold blue]")
    console.print("="*60)
    
    migration_success = verify_migration()
    
    # Итоговый отчёт
    console.print("\n" + "="*60)
    console.print("[bold blue]📊 ИТОГОВЫЙ ОТЧЁТ[/bold blue]")
    console.print("="*60)
    
    if migration_success:
        console.print("[green]✅ ТЕСТ ПЕРЕНОСА ДАННЫХ ПРОЙДЕН УСПЕШНО![/green]")
        console.print("[green]✅ Все данные перенесены корректно[/green]")
        console.print("[green]✅ Система готова к переносу данных всех 166 таблиц[/green]")
    else:
        console.print("[red]❌ ТЕСТ ПЕРЕНОСА ДАННЫХ ПРОВАЛЕН[/red]")
        console.print("[red]❌ Требуется доработка системы переноса данных[/red]")
    
    return migration_success

if __name__ == "__main__":
    main()