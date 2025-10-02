#!/usr/bin/env python3
"""
Тестовый скрипт для модуля управления списком таблиц
"""
import os
import sys
import time
from rich.console import Console
from rich.panel import Panel

# Добавляем путь к проекту
sys.path.append('/home/alex/projects/sql/femcl')

from scripts.migration.table_list_manager import TableListManager

console = Console()

def test_initialization():
    """Тест инициализации списка таблиц"""
    console.print("[bold blue]🧪 ТЕСТ 1: Инициализация списка таблиц[/bold blue]")
    
    manager = TableListManager()
    
    try:
        # Инициализация
        result = manager.initialize_table_list()
        
        console.print(f"✅ Результат инициализации:")
        console.print(f"   - Всего таблиц: {result['total_tables']}")
        console.print(f"   - Инициализировано: {result['initialized']}")
        console.print(f"   - Уже существовали: {result['already_exists']}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка инициализации: {e}[/red]")
        return False
    finally:
        manager.close()

def test_progress_tracking():
    """Тест отслеживания прогресса"""
    console.print("\n[bold blue]🧪 ТЕСТ 2: Отслеживание прогресса[/bold blue]")
    
    manager = TableListManager()
    
    try:
        # Получение прогресса
        progress = manager.get_migration_progress()
        
        console.print(f"✅ Прогресс миграции:")
        console.print(f"   - Всего таблиц: {progress['total']}")
        console.print(f"   - Завершено: {progress['completed']}")
        console.print(f"   - Процент: {progress['percentage']:.1f}%")
        
        # Отображение таблицы
        manager.display_progress_table()
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка получения прогресса: {e}[/red]")
        return False
    finally:
        manager.close()

def test_status_management():
    """Тест управления статусами"""
    console.print("\n[bold blue]🧪 ТЕСТ 3: Управление статусами[/bold blue]")
    
    manager = TableListManager()
    
    try:
        # Получаем список незавершённых таблиц
        incomplete = manager.get_incomplete_tables()
        
        if not incomplete:
            console.print("[yellow]⚠️ Нет незавершённых таблиц для тестирования[/yellow]")
            return True
        
        test_table = incomplete[0]
        console.print(f"📊 Тестируем на таблице: {test_table}")
        
        # Получаем текущий статус
        initial_status = manager.get_table_status(test_table)
        console.print(f"   - Начальный статус: {initial_status}")
        
        # Обновляем статус
        success = manager.update_table_status(test_table, 'in_progress', {'test': True})
        if success:
            console.print("   ✅ Статус обновлён на 'in_progress'")
            
            # Проверяем обновление
            new_status = manager.get_table_status(test_table)
            console.print(f"   - Новый статус: {new_status}")
            
            # Возвращаем исходный статус
            manager.update_table_status(test_table, initial_status)
            console.print(f"   ✅ Статус возвращён к '{initial_status}'")
        else:
            console.print("   ❌ Ошибка обновления статуса")
            return False
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка управления статусами: {e}[/red]")
        return False
    finally:
        manager.close()

def test_table_completion():
    """Тест отметки таблицы как завершённой"""
    console.print("\n[bold blue]🧪 ТЕСТ 4: Отметка таблицы как завершённой[/bold blue]")
    
    manager = TableListManager()
    
    try:
        # Получаем список незавершённых таблиц
        incomplete = manager.get_incomplete_tables()
        
        if not incomplete:
            console.print("[yellow]⚠️ Нет незавершённых таблиц для тестирования[/yellow]")
            return True
        
        test_table = incomplete[0]
        console.print(f"📊 Тестируем на таблице: {test_table}")
        
        # Получаем начальный статус
        initial_status = manager.get_table_status(test_table)
        
        # Отмечаем как завершённую с метриками
        metrics = {
            'duration_seconds': 45.2,
            'records_migrated': 1250,
            'structure_elements': 8,
            'data_size_mb': 2.5
        }
        
        success = manager.mark_table_completed(test_table, metrics)
        if success:
            console.print("   ✅ Таблица отмечена как завершённая")
            
            # Проверяем статус
            new_status = manager.get_table_status(test_table)
            console.print(f"   - Новый статус: {new_status}")
            
            # Возвращаем исходный статус
            manager.update_table_status(test_table, initial_status)
            console.print(f"   ✅ Статус возвращён к '{initial_status}'")
        else:
            console.print("   ❌ Ошибка отметки как завершённой")
            return False
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка отметки завершения: {e}[/red]")
        return False
    finally:
        manager.close()

def test_failed_tables():
    """Тест работы с таблицами с ошибками"""
    console.print("\n[bold blue]🧪 ТЕСТ 5: Работа с таблицами с ошибками[/bold blue]")
    
    manager = TableListManager()
    
    try:
        # Получаем список таблиц с ошибками
        failed_tables = manager.get_failed_tables()
        blocked_tables = manager.get_blocked_tables()
        
        console.print(f"📊 Таблицы с ошибками: {len(failed_tables)}")
        console.print(f"📊 Заблокированные таблицы: {len(blocked_tables)}")
        
        # Если есть таблицы с ошибками, тестируем повторную попытку
        if failed_tables:
            test_table = failed_tables[0]
            console.print(f"   🔄 Тестируем повторную попытку для: {test_table}")
            
            success = manager.retry_failed_table(test_table)
            if success:
                console.print("   ✅ Повторная попытка инициирована")
            else:
                console.print("   ❌ Ошибка инициации повторной попытки")
        else:
            console.print("   ℹ️ Нет таблиц с ошибками для тестирования")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка работы с таблицами с ошибками: {e}[/red]")
        return False
    finally:
        manager.close()

def test_statistics():
    """Тест получения статистики"""
    console.print("\n[bold blue]🧪 ТЕСТ 6: Получение статистики[/bold blue]")
    
    manager = TableListManager()
    
    try:
        # Получаем детальную статистику
        stats = manager.get_migration_statistics()
        
        console.print("✅ Детальная статистика:")
        console.print(f"   - Прогресс: {stats['progress']['percentage']:.1f}%")
        console.print(f"   - Всего таблиц: {stats['progress']['total']}")
        console.print(f"   - Завершено: {stats['progress']['completed']}")
        
        if stats['time_statistics'] and stats['time_statistics'].get('avg_duration_seconds'):
            avg_duration = stats['time_statistics'].get('avg_duration_seconds', 0)
            console.print(f"   - Среднее время миграции: {avg_duration:.1f} сек")
        
        if stats['error_statistics'] and stats['error_statistics'].get('avg_attempts'):
            avg_attempts = stats['error_statistics'].get('avg_attempts', 0)
            console.print(f"   - Среднее количество попыток: {avg_attempts:.1f}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка получения статистики: {e}[/red]")
        return False
    finally:
        manager.close()

def main():
    """Основная функция тестирования"""
    console.print(Panel.fit(
        "[bold green]🧪 ТЕСТИРОВАНИЕ МОДУЛЯ УПРАВЛЕНИЯ СПИСКОМ ТАБЛИЦ[/bold green]\n"
        "Тестирование всех функций TableListManager",
        border_style="green"
    ))
    
    tests = [
        ("Инициализация списка таблиц", test_initialization),
        ("Отслеживание прогресса", test_progress_tracking),
        ("Управление статусами", test_status_management),
        ("Отметка завершения", test_table_completion),
        ("Работа с ошибками", test_failed_tables),
        ("Получение статистики", test_statistics)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        console.print(f"\n{'='*60}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                console.print(f"[green]✅ {test_name}: ПРОЙДЕН[/green]")
            else:
                console.print(f"[red]❌ {test_name}: ПРОВАЛЕН[/red]")
        except Exception as e:
            console.print(f"[red]❌ {test_name}: ОШИБКА - {e}[/red]")
            results.append((test_name, False))
    
    # Итоговый отчёт
    console.print(f"\n{'='*60}")
    console.print("[bold blue]📊 ИТОГОВЫЙ ОТЧЁТ ТЕСТИРОВАНИЯ:[/bold blue]")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        console.print(f"  {test_name}: {status}")
    
    console.print(f"\n[bold green]Результат: {passed}/{total} тестов пройдено[/bold green]")
    
    if passed == total:
        console.print("[bold green]🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО![/bold green]")
    else:
        console.print("[bold red]💥 ЕСТЬ ПРОВАЛЕННЫЕ ТЕСТЫ[/bold red]")

if __name__ == "__main__":
    main()