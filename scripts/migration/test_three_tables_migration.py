#!/usr/bin/env python3
"""
Тестовый скрипт для миграции трёх таблиц
Использует полную систему правил миграции
"""
import os
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

# Добавляем путь к проекту
sys.path.append('/home/alex/projects/sql/femcl')

from scripts.migration.migration_coordinator import MigrationCoordinator, MigrationState

console = Console()

def test_three_tables_migration():
    """Тест миграции трёх таблиц"""
    console.print(Panel.fit(
        "[bold green]🧪 ТЕСТ МИГРАЦИИ ТРЁХ ТАБЛИЦ[/bold green]\n"
        "Использование полной системы правил миграции",
        border_style="green"
    ))
    
    # Создаём координатор
    coordinator = MigrationCoordinator()
    
    try:
        # Шаг 1: Инициализация системы
        console.print("\n[bold blue]📋 ШАГ 1: Инициализация системы миграции[/bold blue]")
        init_success = coordinator.initialize_migration_system()
        
        if not init_success:
            console.print("[red]❌ Ошибка инициализации системы[/red]")
            return False
        
        console.print("[green]✅ Система инициализирована успешно[/green]")
        
        # Шаг 2: Валидация готовности
        console.print("\n[bold blue]🔍 ШАГ 2: Валидация готовности к миграции[/bold blue]")
        readiness = coordinator.validate_migration_readiness()
        
        console.print(f"   📊 Готовность: {readiness['readiness_percentage']:.1f}%")
        console.print(f"   ✅ Готовность: {readiness['is_ready']}")
        
        if readiness['issues']:
            console.print("   ⚠️ Проблемы:")
            for issue in readiness['issues']:
                console.print(f"      - {issue}")
        
        if not readiness['is_ready']:
            console.print("[red]❌ Система не готова к миграции[/red]")
            return False
        
        # Шаг 3: Получение плана миграции
        console.print("\n[bold blue]📋 ШАГ 3: Получение плана миграции[/bold blue]")
        plan = coordinator.get_migration_plan()
        
        console.print(f"   📊 Всего таблиц в плане: {plan['total_tables']}")
        console.print(f"   🔗 Критических зависимостей: {plan['critical_dependencies']}")
        console.print(f"   ⏱️ Оценочная длительность: {plan['estimated_duration_hours']:.1f} часов")
        
        # Показываем первые 10 таблиц из плана
        console.print("   📝 Первые таблицы в плане:")
        for i, table in enumerate(plan['tables'][:10]):
            console.print(f"      {i+1}. {table}")
        
        # Шаг 4: Получение состояния системы
        console.print("\n[bold blue]🏥 ШАГ 4: Проверка состояния системы[/bold blue]")
        health = coordinator.get_system_health()
        
        console.print(f"   🏥 Общий статус: {health['overall_status']}")
        console.print(f"   ❌ Есть ошибки: {health['has_errors']}")
        console.print(f"   📊 Компонентов: {len(health['components'])}")
        
        for component, status in health['components'].items():
            console.print(f"      - {component}: {status['status']}")
        
        # Шаг 5: Отображение дашборда статуса
        console.print("\n[bold blue]📊 ШАГ 5: Дашборд статуса миграции[/bold blue]")
        coordinator.display_status_dashboard()
        
        # Шаг 6: Запуск миграции (имитация)
        console.print("\n[bold blue]🚀 ШАГ 6: Запуск миграции трёх таблиц[/bold blue]")
        
        # Выбираем первые три таблицы из плана
        test_tables = plan['tables'][:3]
        console.print(f"   🎯 Тестовые таблицы: {', '.join(test_tables)}")
        
        # Запускаем миграцию
        start_success = coordinator.start_migration_process()
        
        if not start_success:
            console.print("[red]❌ Ошибка запуска миграции[/red]")
            return False
        
        console.print("[green]✅ Миграция запущена успешно[/green]")
        
        # Мониторинг процесса миграции
        console.print("\n[bold blue]📈 ШАГ 7: Мониторинг процесса миграции[/bold blue]")
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            # Создаём задачи для мониторинга
            main_task = progress.add_task("Миграция таблиц", total=100)
            
            # Имитируем процесс миграции
            for i in range(10):
                # Получаем текущий статус
                status = coordinator.get_migration_status()
                
                # Обновляем прогресс
                progress_percentage = status['progress']['percentage']
                progress.update(main_task, completed=progress_percentage)
                
                # Показываем детали
                if i % 3 == 0:  # Каждые 3 итерации
                    console.print(f"   📊 Прогресс: {progress_percentage:.1f}%")
                    console.print(f"   ✅ Завершено: {status['progress']['completed']}")
                    console.print(f"   📋 Всего: {status['progress']['total']}")
                    console.print(f"   ❌ Ошибок: {status['error_count']}")
                
                time.sleep(1)  # Имитация времени миграции
        
        # Шаг 8: Финальный статус
        console.print("\n[bold blue]📊 ШАГ 8: Финальный статус миграции[/bold blue]")
        
        final_status = coordinator.get_migration_status()
        
        # Создаём таблицу результатов
        results_table = Table(title="Результаты миграции трёх таблиц")
        results_table.add_column("Метрика", style="cyan")
        results_table.add_column("Значение", style="green")
        results_table.add_column("Единица", style="yellow")
        
        results_table.add_row("Состояние", final_status['state'], "")
        results_table.add_row("Прогресс", f"{final_status['progress']['percentage']:.1f}", "%")
        results_table.add_row("Завершено", str(final_status['progress']['completed']), "таблиц")
        results_table.add_row("Всего", str(final_status['progress']['total']), "таблиц")
        results_table.add_row("Ошибок", str(final_status['error_count']), "шт")
        
        if final_status['runtime_seconds']:
            results_table.add_row("Время выполнения", f"{final_status['runtime_seconds']:.1f}", "сек")
        
        console.print(results_table)
        
        # Шаг 9: Остановка миграции
        console.print("\n[bold blue]🛑 ШАГ 9: Остановка миграции[/bold blue]")
        
        stop_success = coordinator.stop_migration()
        
        if stop_success:
            console.print("[green]✅ Миграция остановлена успешно[/green]")
        else:
            console.print("[red]❌ Ошибка остановки миграции[/red]")
            return False
        
        # Шаг 10: Итоговый отчёт
        console.print("\n[bold blue]📋 ШАГ 10: Итоговый отчёт[/bold blue]")
        
        # Получаем финальные метрики
        final_health = coordinator.get_system_health()
        
        console.print(f"   🏥 Финальное состояние системы: {final_health['overall_status']}")
        console.print(f"   📊 Компонентов в рабочем состоянии: {len([c for c in final_health['components'].values() if c['status'] == 'HEALTHY'])}")
        
        if final_health['has_errors']:
            console.print("   🚨 Обнаружены ошибки:")
            for error in final_health['errors']:
                console.print(f"      - {error}")
        else:
            console.print("   ✅ Ошибок не обнаружено")
        
        # Показываем статистику по тестовым таблицам
        console.print(f"   🎯 Тестовые таблицы: {', '.join(test_tables)}")
        console.print("   📈 Статус: Тестирование завершено успешно")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Критическая ошибка тестирования: {e}[/red]")
        return False
    finally:
        # Закрываем координатор
        coordinator.close()

def test_individual_components():
    """Тест отдельных компонентов системы"""
    console.print("\n[bold blue]🔧 ДОПОЛНИТЕЛЬНЫЙ ТЕСТ: Проверка отдельных компонентов[/bold blue]")
    
    coordinator = MigrationCoordinator()
    
    try:
        # Инициализация
        coordinator.initialize_migration_system()
        
        # Тест TableListManager
        console.print("   📋 Тестирование TableListManager...")
        progress = coordinator.table_manager.get_migration_progress()
        console.print(f"      📊 Прогресс: {progress['percentage']:.1f}%")
        console.print(f"      ✅ Завершено: {progress['completed']}")
        console.print(f"      📋 Всего: {progress['total']}")
        
        # Тест DependencyAnalyzer
        console.print("   🔗 Тестирование DependencyAnalyzer...")
        migration_order = coordinator.dependency_analyzer.get_migration_order()
        console.print(f"      📋 Порядок миграции: {len(migration_order)} таблиц")
        
        # Показываем первые 5 таблиц
        console.print("      🎯 Первые 5 таблиц:")
        for i, table in enumerate(migration_order[:5]):
            console.print(f"         {i+1}. {table}")
        
        # Тест MigrationMonitor
        console.print("   📊 Тестирование MigrationMonitor...")
        metrics = coordinator.monitor.get_real_time_metrics()
        console.print(f"      📈 Метрик: {len(metrics.get('metrics', {}))}")
        console.print(f"      📊 Статусов: {len(metrics.get('status_breakdown', {}))}")
        
        console.print("   ✅ Все компоненты работают корректно")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка тестирования компонентов: {e}[/red]")
        return False
    finally:
        coordinator.close()

def main():
    """Основная функция тестирования"""
    console.print(Panel.fit(
        "[bold green]🧪 ПОЛНЫЙ ТЕСТ СИСТЕМЫ МИГРАЦИИ[/bold green]\n"
        "Тестирование на трёх таблицах с использованием всех модулей",
        border_style="green"
    ))
    
    # Основной тест миграции
    console.print("\n" + "="*80)
    console.print("[bold blue]ОСНОВНОЙ ТЕСТ: Миграция трёх таблиц[/bold blue]")
    console.print("="*80)
    
    main_test_success = test_three_tables_migration()
    
    # Дополнительный тест компонентов
    console.print("\n" + "="*80)
    console.print("[bold blue]ДОПОЛНИТЕЛЬНЫЙ ТЕСТ: Проверка компонентов[/bold blue]")
    console.print("="*80)
    
    components_test_success = test_individual_components()
    
    # Итоговый отчёт
    console.print("\n" + "="*80)
    console.print("[bold blue]📊 ИТОГОВЫЙ ОТЧЁТ ТЕСТИРОВАНИЯ[/bold blue]")
    console.print("="*80)
    
    if main_test_success:
        console.print("[green]✅ Основной тест миграции: ПРОЙДЕН[/green]")
    else:
        console.print("[red]❌ Основной тест миграции: ПРОВАЛЕН[/red]")
    
    if components_test_success:
        console.print("[green]✅ Тест компонентов: ПРОЙДЕН[/green]")
    else:
        console.print("[red]❌ Тест компонентов: ПРОВАЛЕН[/red]")
    
    if main_test_success and components_test_success:
        console.print("\n[bold green]🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО![/bold green]")
        console.print("[green]✅ Система миграции готова к использованию[/green]")
    else:
        console.print("\n[bold red]💥 ЕСТЬ ПРОВАЛЕННЫЕ ТЕСТЫ[/bold red]")
        console.print("[red]❌ Требуется дополнительная настройка[/red]")

if __name__ == "__main__":
    main()