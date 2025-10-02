#!/usr/bin/env python3
"""
Тестовый скрипт для модуля анализа зависимостей
"""
import os
import sys
from rich.console import Console
from rich.panel import Panel

# Добавляем путь к проекту
sys.path.append('/home/alex/projects/sql/femcl')

from scripts.migration.dependency_analyzer import DependencyAnalyzer

console = Console()

def test_dependency_analysis():
    """Тест анализа зависимостей для конкретной таблицы"""
    console.print("[bold blue]🧪 ТЕСТ 1: Анализ зависимостей таблицы[/bold blue]")
    
    analyzer = DependencyAnalyzer()
    
    try:
        # Тестируем на таблице accnt
        table_name = "accnt"
        dependencies = analyzer.analyze_table_dependencies(table_name)
        
        console.print(f"✅ Результат анализа зависимостей для {table_name}:")
        console.print(f"   - Ссылочные таблицы: {dependencies['referenced_tables']}")
        console.print(f"   - Зависимые таблицы: {dependencies['dependent_tables']}")
        console.print(f"   - Всего зависимостей: {dependencies['total_dependencies']}")
        console.print(f"   - Критических: {dependencies['critical_count']}")
        console.print(f"   - Уровень зависимости: {dependencies['dependency_level']}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка анализа зависимостей: {e}[/red]")
        return False
    finally:
        analyzer.close()

def test_readiness_check():
    """Тест проверки готовности ссылочных таблиц"""
    console.print("\n[bold blue]🧪 ТЕСТ 2: Проверка готовности ссылочных таблиц[/bold blue]")
    
    analyzer = DependencyAnalyzer()
    
    try:
        # Тестируем готовность для таблицы accnt
        table_name = "accnt"
        readiness = analyzer.check_referenced_tables_ready(table_name)
        
        console.print(f"✅ Результат проверки готовности для {table_name}:")
        console.print(f"   - Процент готовности: {readiness['ready_percentage']:.1f}%")
        console.print(f"   - Готовых таблиц: {len(readiness['ready_tables'])}")
        console.print(f"   - Не готовых таблиц: {len(readiness['not_ready_tables'])}")
        console.print(f"   - Всего ссылочных: {readiness['total_referenced']}")
        
        if readiness['not_ready_tables']:
            console.print("   📋 Не готовые таблицы:")
            for not_ready in readiness['not_ready_tables']:
                console.print(f"      - {not_ready['table']}: {not_ready['reason']}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка проверки готовности: {e}[/red]")
        return False
    finally:
        analyzer.close()

def test_circular_dependencies():
    """Тест поиска циклических зависимостей"""
    console.print("\n[bold blue]🧪 ТЕСТ 3: Поиск циклических зависимостей[/bold blue]")
    
    analyzer = DependencyAnalyzer()
    
    try:
        # Поиск циклических зависимостей
        cycles = analyzer.detect_circular_dependencies()
        
        console.print(f"✅ Результат поиска циклов:")
        console.print(f"   - Найдено циклов: {len(cycles)}")
        
        if cycles:
            console.print("   📋 Циклические зависимости:")
            for i, cycle in enumerate(cycles, 1):
                console.print(f"      Цикл {i}: {' → '.join(cycle)}")
        else:
            console.print("   ✅ Циклических зависимостей не найдено")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка поиска циклов: {e}[/red]")
        return False
    finally:
        analyzer.close()

def test_migration_order():
    """Тест определения порядка миграции"""
    console.print("\n[bold blue]🧪 ТЕСТ 4: Определение порядка миграции[/bold blue]")
    
    analyzer = DependencyAnalyzer()
    
    try:
        # Определение порядка миграции
        order = analyzer.get_migration_order()
        
        console.print(f"✅ Результат определения порядка:")
        console.print(f"   - Всего таблиц в порядке: {len(order)}")
        console.print(f"   - Первые 10 таблиц: {order[:10]}")
        
        if len(order) > 10:
            console.print(f"   - Последние 5 таблиц: {order[-5:]}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка определения порядка: {e}[/red]")
        return False
    finally:
        analyzer.close()

def test_dependency_graph():
    """Тест построения графа зависимостей"""
    console.print("\n[bold blue]🧪 ТЕСТ 5: Построение графа зависимостей[/bold blue]")
    
    analyzer = DependencyAnalyzer()
    
    try:
        # Получение графа зависимостей
        graph = analyzer.get_dependency_graph()
        
        console.print(f"✅ Результат построения графа:")
        console.print(f"   - Узлов в графе: {len(graph)}")
        
        # Показываем несколько примеров зависимостей
        example_count = 0
        for source, targets in graph.items():
            if example_count < 5:  # Показываем только первые 5
                console.print(f"   - {source} → {targets}")
                example_count += 1
        
        if len(graph) > 5:
            console.print(f"   ... и ещё {len(graph) - 5} узлов")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка построения графа: {e}[/red]")
        return False
    finally:
        analyzer.close()

def test_dependency_chain():
    """Тест анализа цепочки зависимостей"""
    console.print("\n[bold blue]🧪 ТЕСТ 6: Анализ цепочки зависимостей[/bold blue]")
    
    analyzer = DependencyAnalyzer()
    
    try:
        # Анализ цепочки для таблицы accnt
        table_name = "accnt"
        chain = analyzer.analyze_dependency_chain(table_name)
        
        console.print(f"✅ Результат анализа цепочки для {table_name}:")
        console.print(f"   - Цепочка зависимостей: {' → '.join(chain)}")
        console.print(f"   - Длина цепочки: {len(chain)}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка анализа цепочки: {e}[/red]")
        return False
    finally:
        analyzer.close()

def test_critical_dependencies():
    """Тест поиска критических зависимостей"""
    console.print("\n[bold blue]🧪 ТЕСТ 7: Поиск критических зависимостей[/bold blue]")
    
    analyzer = DependencyAnalyzer()
    
    try:
        # Поиск критических зависимостей
        critical = analyzer.get_critical_dependencies()
        
        console.print(f"✅ Результат поиска критических зависимостей:")
        console.print(f"   - Найдено критических: {len(critical)}")
        
        if critical:
            console.print("   📋 Критические зависимости:")
            for i, dep in enumerate(critical[:5], 1):  # Показываем первые 5
                console.print(f"      {i}. {dep['source_table']} → {dep['target_table']} ({dep['delete_action']})")
            
            if len(critical) > 5:
                console.print(f"      ... и ещё {len(critical) - 5} зависимостей")
        else:
            console.print("   ✅ Критических зависимостей не найдено")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка поиска критических зависимостей: {e}[/red]")
        return False
    finally:
        analyzer.close()

def test_dependency_validation():
    """Тест валидации целостности зависимостей"""
    console.print("\n[bold blue]🧪 ТЕСТ 8: Валидация целостности зависимостей[/bold blue]")
    
    analyzer = DependencyAnalyzer()
    
    try:
        # Валидация для таблицы accnt
        table_name = "accnt"
        is_valid = analyzer.validate_dependency_integrity(table_name)
        
        console.print(f"✅ Результат валидации для {table_name}:")
        if is_valid:
            console.print("   ✅ Все зависимости корректны")
        else:
            console.print("   ❌ Есть проблемы с зависимостями")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка валидации: {e}[/red]")
        return False
    finally:
        analyzer.close()

def test_dependency_statistics():
    """Тест получения статистики зависимостей"""
    console.print("\n[bold blue]🧪 ТЕСТ 9: Получение статистики зависимостей[/bold blue]")
    
    analyzer = DependencyAnalyzer()
    
    try:
        # Получение статистики
        stats = analyzer.get_migration_statistics()
        
        console.print(f"✅ Результат получения статистики:")
        console.print(f"   - Всего таблиц: {stats['total_tables']}")
        console.print(f"   - Таблиц с зависимостями: {stats['tables_with_dependencies']}")
        console.print(f"   - Всего зависимостей: {stats['total_dependencies']}")
        console.print(f"   - Максимум зависимостей на таблицу: {stats['max_dependencies_per_table']}")
        console.print(f"   - Среднее количество зависимостей: {stats['avg_dependencies']:.1f}")
        console.print(f"   - Циклических зависимостей: {stats['circular_dependencies']}")
        console.print(f"   - Критических зависимостей: {stats['critical_dependencies']}")
        console.print(f"   - Средний уровень зависимости: {stats['avg_dependency_level']:.1f}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка получения статистики: {e}[/red]")
        return False
    finally:
        analyzer.close()

def test_dependency_tree():
    """Тест отображения дерева зависимостей"""
    console.print("\n[bold blue]🧪 ТЕСТ 10: Отображение дерева зависимостей[/bold blue]")
    
    analyzer = DependencyAnalyzer()
    
    try:
        # Отображение дерева для таблицы accnt
        table_name = "accnt"
        console.print(f"🌳 Дерево зависимостей для {table_name}:")
        analyzer.display_dependency_tree(table_name)
        
        console.print("✅ Дерево зависимостей отображено")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка отображения дерева: {e}[/red]")
        return False
    finally:
        analyzer.close()

def main():
    """Основная функция тестирования"""
    console.print(Panel.fit(
        "[bold green]🧪 ТЕСТИРОВАНИЕ МОДУЛЯ АНАЛИЗА ЗАВИСИМОСТЕЙ[/bold green]\n"
        "Тестирование всех функций DependencyAnalyzer",
        border_style="green"
    ))
    
    tests = [
        ("Анализ зависимостей таблицы", test_dependency_analysis),
        ("Проверка готовности ссылочных таблиц", test_readiness_check),
        ("Поиск циклических зависимостей", test_circular_dependencies),
        ("Определение порядка миграции", test_migration_order),
        ("Построение графа зависимостей", test_dependency_graph),
        ("Анализ цепочки зависимостей", test_dependency_chain),
        ("Поиск критических зависимостей", test_critical_dependencies),
        ("Валидация целостности зависимостей", test_dependency_validation),
        ("Получение статистики зависимостей", test_dependency_statistics),
        ("Отображение дерева зависимостей", test_dependency_tree)
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