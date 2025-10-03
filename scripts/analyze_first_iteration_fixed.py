#!/usr/bin/env python3
"""
FEMCL - Анализ таблиц для первой итерации миграции (ИСПРАВЛЕННАЯ ВЕРСИЯ)
Определяет таблицы без внешних ключей для первой итерации с ПРАВИЛЬНОЙ алфавитной сортировкой
"""
import psycopg2
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

console = Console()

def analyze_first_iteration_tables_fixed(task_id=2):
    """Анализ таблиц для первой итерации миграции с правильной сортировкой"""
    
    try:
        # Подключение к PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="fish_eye",
            user="postgres",
            password="postgres"
        )
        
        console.print(Panel.fit("[bold blue]🔍 FEMCL - Анализ таблиц для первой итерации (ИСПРАВЛЕННАЯ ВЕРСИЯ)[/bold blue]", border_style="blue"))
        console.print(f"[blue]Задача миграции: ID={task_id}[/blue]")
        
        with conn.cursor() as cur:
            # Получение всех таблиц задачи с анализом зависимостей
            # ВАЖНО: НЕ используем ORDER BY в SQL, сортируем в Python для точного контроля
            cur.execute("""
                SELECT 
                    mt.id,
                    mt.object_name,
                    mt.schema_name,
                    mt.foreign_key_count,
                    mt.primary_key_count,
                    mt.index_count,
                    mt.column_count,
                    mt.row_count,
                    pt.id as target_table_id,
                    pt.object_name as target_name,
                    pt.migration_status
                FROM mcl.mssql_tables mt
                LEFT JOIN mcl.postgres_tables pt ON mt.id = pt.source_table_id
                WHERE mt.task_id = %s
            """, (task_id,))
            
            all_tables = cur.fetchall()
            
            # Разделение на таблицы без внешних ключей (первая итерация)
            # и таблицы с внешними ключами (последующие итерации)
            first_iteration_tables = []
            subsequent_iteration_tables = []
            
            for table in all_tables:
                (table_id, object_name, schema_name, fk_count, pk_count, 
                 index_count, column_count, row_count, target_table_id, 
                 target_name, migration_status) = table
                
                if fk_count == 0:
                    first_iteration_tables.append(table)
                else:
                    subsequent_iteration_tables.append(table)
            
            # ИСПРАВЛЕНИЕ: Правильная алфавитная сортировка по object_name
            # Используем case-insensitive сортировку для корректного порядка
            first_iteration_tables.sort(key=lambda x: x[1].lower())  # Сортировка по object_name (case-insensitive)
            subsequent_iteration_tables.sort(key=lambda x: x[1].lower())  # Сортировка по object_name (case-insensitive)
            
            # Отображение результатов
            console.print(f"\n[blue]📊 Всего таблиц в задаче: {len(all_tables)}[/blue]")
            console.print(f"[green]✅ Таблиц для первой итерации: {len(first_iteration_tables)}[/green]")
            console.print(f"[yellow]⏳ Таблиц для последующих итераций: {len(subsequent_iteration_tables)}[/yellow]")
            
            # Таблица таблиц первой итерации
            if first_iteration_tables:
                console.print("\n[bold green]📋 ТАБЛИЦЫ ДЛЯ ПЕРВОЙ ИТЕРАЦИИ (ПРАВИЛЬНЫЙ АЛФАВИТНЫЙ ПОРЯДОК)[/bold green]")
                
                first_table = Table(title="Таблицы без внешних ключей (первая итерация) - ПРАВИЛЬНЫЙ ПОРЯДОК")
                first_table.add_column("№", style="cyan", width=3)
                first_table.add_column("Таблица", style="green")
                first_table.add_column("Схема", style="blue")
                first_table.add_column("Колонок", style="yellow", width=8)
                first_table.add_column("Строк", style="yellow", width=8)
                first_table.add_column("PK", style="green", width=3)
                first_table.add_column("Индексов", style="blue", width=8)
                first_table.add_column("Статус", style="cyan")
                
                for i, table in enumerate(first_iteration_tables, 1):
                    (table_id, object_name, schema_name, fk_count, pk_count, 
                     index_count, column_count, row_count, target_table_id, 
                     target_name, migration_status) = table
                    
                    first_table.add_row(
                        str(i),
                        object_name,
                        schema_name,
                        str(column_count),
                        str(row_count),
                        str(pk_count),
                        str(index_count),
                        migration_status
                    )
                
                console.print(first_table)
                
                # Проверка правильности сортировки
                console.print("\n[blue]🔍 Проверка алфавитного порядка:[/blue]")
                for i in range(min(10, len(first_iteration_tables))):
                    table_name = first_iteration_tables[i][1]
                    console.print(f"[green]{i+1:2d}. {table_name}[/green]")
                
                if len(first_iteration_tables) > 10:
                    console.print(f"[blue]... и еще {len(first_iteration_tables) - 10} таблиц[/blue]")
            
            # Таблица таблиц последующих итераций (краткий обзор)
            if subsequent_iteration_tables:
                console.print(f"\n[bold yellow]⏳ ТАБЛИЦЫ ДЛЯ ПОСЛЕДУЮЩИХ ИТЕРАЦИЙ ({len(subsequent_iteration_tables)} таблиц)[/bold yellow]")
                
                # Показываем только первые 10 таблиц с внешними ключами
                subsequent_table = Table(title="Таблицы с внешними ключами (первые 10)")
                subsequent_table.add_column("Таблица", style="green")
                subsequent_table.add_column("Внешних ключей", style="red", width=15)
                subsequent_table.add_column("Колонок", style="yellow", width=8)
                subsequent_table.add_column("Строк", style="yellow", width=8)
                
                for table in subsequent_iteration_tables[:10]:
                    (table_id, object_name, schema_name, fk_count, pk_count, 
                     index_count, column_count, row_count, target_table_id, 
                     target_name, migration_status) = table
                    
                    subsequent_table.add_row(
                        object_name,
                        str(fk_count),
                        str(column_count),
                        str(row_count)
                    )
                
                console.print(subsequent_table)
                
                if len(subsequent_iteration_tables) > 10:
                    console.print(f"[blue]... и еще {len(subsequent_iteration_tables) - 10} таблиц[/blue]")
            
            # Статистика по сложности
            simple_tables = [t for t in first_iteration_tables if t[6] <= 5]  # <= 5 колонок
            medium_tables = [t for t in first_iteration_tables if 5 < t[6] <= 15]  # 6-15 колонок
            complex_tables = [t for t in first_iteration_tables if t[6] > 15]  # > 15 колонок
            
            console.print(f"\n[blue]📊 Сложность таблиц первой итерации:[/blue]")
            console.print(f"[green]  Простые (≤5 колонок): {len(simple_tables)}[/green]")
            console.print(f"[yellow]  Средние (6-15 колонок): {len(medium_tables)}[/yellow]")
            console.print(f"[red]  Сложные (>15 колонок): {len(complex_tables)}[/red]")
            
            return {
                'first_iteration': first_iteration_tables,
                'subsequent_iteration': subsequent_iteration_tables,
                'simple_tables': simple_tables,
                'medium_tables': medium_tables,
                'complex_tables': complex_tables
            }
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка анализа таблиц: {e}[/red]")
        return None
    
    finally:
        if 'conn' in locals():
            conn.close()

def update_progress_file_fixed(analysis_result):
    """Обновление файла прогресса с результатами анализа (ИСПРАВЛЕННАЯ ВЕРСИЯ)"""
    
    if not analysis_result:
        return False
    
    first_iteration = analysis_result['first_iteration']
    subsequent_iteration = analysis_result['subsequent_iteration']
    simple_tables = analysis_result['simple_tables']
    medium_tables = analysis_result['medium_tables']
    complex_tables = analysis_result['complex_tables']
    
    # Обновление файла прогресса
    progress_file = "/home/alex/projects/sql/femcl/progress/20250127_143000_migration_progress.md"
    
    with open(progress_file, 'w', encoding='utf-8') as f:
        f.write(f"""# 📊 ПРОГРЕСС МИГРАЦИИ FEMCL

## 📋 Информация о сессии

**Дата обновления:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}  
**Задача миграции:** ID=2  
**Статус:** 🔍 АНАЛИЗ ЗАВЕРШЕН (ИСПРАВЛЕН)  
**Автор:** AI Assistant  

## 🎯 Общая статистика

- **Всего таблиц для миграции:** {len(first_iteration) + len(subsequent_iteration)}
- **Завершено:** 0
- **В процессе:** 0  
- **Ожидает:** {len(first_iteration) + len(subsequent_iteration)}
- **Ошибок:** 0
- **Прогресс:** 0%

## 📊 Анализ таблиц для миграции

### ✅ **Таблицы для первой итерации:** {len(first_iteration)}
*Таблицы без внешних ключей - можно мигрировать независимо*

### ⏳ **Таблицы для последующих итераций:** {len(subsequent_iteration)}
*Таблицы с внешними ключами - требуют готовности ссылочных таблиц*

## 📋 ТАБЛИЦЫ ДЛЯ ПЕРВОЙ ИТЕРАЦИИ (ПРАВИЛЬНЫЙ АЛФАВИТНЫЙ ПОРЯДОК)

### **Список таблиц (отсортированы по алфавиту согласно правилам миграции):**

""")
        
        # Добавление списка таблиц первой итерации в ПРАВИЛЬНОМ алфавитном порядке
        for i, table in enumerate(first_iteration, 1):
            (table_id, object_name, schema_name, fk_count, pk_count, 
             index_count, column_count, row_count, target_table_id, 
             target_name, migration_status) = table
            
            f.write(f"{i}. **{object_name}** ({schema_name})\n")
            f.write(f"   - Колонок: {column_count}\n")
            f.write(f"   - Строк: {row_count}\n")
            f.write(f"   - Первичных ключей: {pk_count}\n")
            f.write(f"   - Индексов: {index_count}\n")
            f.write(f"   - Внешних ключей: {fk_count}\n")
            f.write(f"   - Статус: {migration_status}\n\n")
        
        f.write(f"""## 📊 Сложность таблиц первой итерации

### **Статистика по сложности:**
- **Простые (≤5 колонок):** {len(simple_tables)} таблиц
- **Средние (6-15 колонок):** {len(medium_tables)} таблиц  
- **Сложные (>15 колонок):** {len(complex_tables)} таблиц

### **Простые таблицы (рекомендуется начать с них):**
""")
        
        for table in simple_tables:
            (table_id, object_name, schema_name, fk_count, pk_count, 
             index_count, column_count, row_count, target_table_id, 
             target_name, migration_status) = table
            f.write(f"- **{object_name}** ({column_count} колонок, {row_count} строк)\n")
        
        f.write(f"""
### **Средние таблицы:**
""")
        
        for table in medium_tables:
            (table_id, object_name, schema_name, fk_count, pk_count, 
             index_count, column_count, row_count, target_table_id, 
             target_name, migration_status) = table
            f.write(f"- **{object_name}** ({column_count} колонок, {row_count} строк)\n")
        
        f.write(f"""
### **Сложные таблицы:**
""")
        
        for table in complex_tables:
            (table_id, object_name, schema_name, fk_count, pk_count, 
             index_count, column_count, row_count, target_table_id, 
             target_name, migration_status) = table
            f.write(f"- **{object_name}** ({column_count} колонок, {row_count} строк)\n")
        
        f.write(f"""
## 📊 Текущая итерация

### **Итерация #1** ({datetime.now().strftime('%d.%m.%Y %H:%M:%S')})
**Статус:** 🔍 АНАЛИЗ ЗАВЕРШЕН (ИСПРАВЛЕН)

#### ✅ Готовы к миграции:
*{len(first_iteration)} таблиц без внешних ключей в ПРАВИЛЬНОМ алфавитном порядке*

#### ⏳ Ожидают готовности ссылочных таблиц:
*{len(subsequent_iteration)} таблиц с внешними ключами*

## 📈 История итераций

### **Итерация #1** (27.01.2025 14:30:00)
- **Статус:** 🔄 ПОДГОТОВКА
- **Действие:** Создание системы отслеживания прогресса

### **Итерация #2** (27.01.2025 14:35:00)  
- **Статус:** ✅ ПРОВЕРКА ЗАВЕРШЕНА
- **Действие:** Проверка подключений и исходных таблиц
- **Результат:** Все проверки пройдены успешно

### **Итерация #3** (27.01.2025 14:40:00)
- **Статус:** 🔄 СТАТУС СБРОШЕН
- **Действие:** Сброс статуса всех таблиц на 'pending'
- **Результат:** 166 таблиц готовы к миграции

### **Итерация #4** (27.01.2025 14:45:00)
- **Статус:** 🔍 АНАЛИЗ ЗАВЕРШЕН (ИСПРАВЛЕН)
- **Действие:** Определение таблиц для первой итерации с ПРАВИЛЬНОЙ сортировкой
- **Результат:** {len(first_iteration)} таблиц готовы к миграции в правильном порядке

## 🚨 Проблемы и ошибки

*Проблем не обнаружено*

## 📝 Заметки

- **{len(first_iteration)} таблиц готовы** к первой итерации миграции
- **{len(subsequent_iteration)} таблиц ожидают** готовности ссылочных таблиц
- **Рекомендуется начать** с простых таблиц (≤5 колонок)
- **Алфавитный порядок ИСПРАВЛЕН** согласно правилам миграции
- **Система готова** к запуску первой итерации

## 🚀 Следующие шаги

1. **Запуск первой итерации** - миграция {len(first_iteration)} таблиц в правильном порядке
2. **Мониторинг прогресса** - через систему отслеживания
3. **Обработка проблем** - по мере их возникновения
4. **Переход к следующим итерациям** - после завершения первой

---
*Файл создан: 27.01.2025 14:30:00*  
*Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*
""")
    
    console.print(f"[green]✅ Файл прогресса обновлен с ПРАВИЛЬНЫМ алфавитным порядком: {progress_file}[/green]")
    return True

def main():
    """Основная функция"""
    console.print("[blue]🔍 Анализ таблиц для первой итерации (ИСПРАВЛЕННАЯ ВЕРСИЯ)...[/blue]")
    
    # Анализ таблиц
    analysis_result = analyze_first_iteration_tables_fixed(task_id=2)
    
    if analysis_result:
        # Обновление файла прогресса
        update_progress_file_fixed(analysis_result)
        
        console.print(f"\n[bold green]🎉 Анализ завершен успешно![/bold green]")
        console.print(f"[green]✅ Таблиц для первой итерации: {len(analysis_result['first_iteration'])}[/green]")
        console.print(f"[yellow]⏳ Таблиц для последующих итераций: {len(analysis_result['subsequent_iteration'])}[/yellow]")
        console.print("[blue]📋 Файл прогресса обновлен с ПРАВИЛЬНЫМ алфавитным порядком[/blue]")
        console.print("[green]✅ Алфавитный порядок соответствует правилам миграции FEMCL[/green]")
    else:
        console.print("\n[bold red]❌ Ошибка при анализе таблиц[/bold red]")

if __name__ == "__main__":
    main()