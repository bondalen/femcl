#!/usr/bin/env python3
"""
Тестовый скрипт для модуля интеграции и координации
"""
import os
import sys
import time
from rich.console import Console
from rich.panel import Panel

# Добавляем путь к проекту
sys.path.append('/home/alex/projects/sql/femcl')

from scripts.migration.migration_coordinator import MigrationCoordinator, MigrationState

console = Console()

def test_coordinator_initialization():
    """Тест инициализации координатора"""
    console.print("[bold blue]🧪 ТЕСТ 1: Инициализация координатора[/bold blue]")
    
    coordinator = MigrationCoordinator()
    
    try:
        # Проверяем начальное состояние
        if coordinator.state == MigrationState.INITIALIZING:
            console.print("   ✅ Начальное состояние корректно")
        else:
            console.print(f"   ❌ Неверное начальное состояние: {coordinator.state}")
            return False
        
        # Проверяем компоненты
        if coordinator.table_manager is None:
            console.print("   ✅ Table manager не инициализирован (ожидаемо)")
        else:
            console.print("   ❌ Table manager не должен быть инициализирован")
            return False
        
        if coordinator.dependency_analyzer is None:
            console.print("   ✅ Dependency analyzer не инициализирован (ожидаемо)")
        else:
            console.print("   ❌ Dependency analyzer не должен быть инициализирован")
            return False
        
        if coordinator.monitor is None:
            console.print("   ✅ Monitor не инициализирован (ожидаемо)")
        else:
            console.print("   ❌ Monitor не должен быть инициализирован")
            return False
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка тестирования инициализации: {e}[/red]")
        return False
    finally:
        coordinator.close()

def test_system_initialization():
    """Тест инициализации системы"""
    console.print("\n[bold blue]🧪 ТЕСТ 2: Инициализация системы[/bold blue]")
    
    coordinator = MigrationCoordinator()
    
    try:
        # Инициализация системы
        success = coordinator.initialize_migration_system()
        
        if success:
            console.print("   ✅ Система инициализирована успешно")
            
            # Проверяем состояние
            if coordinator.state == MigrationState.READY:
                console.print("   ✅ Состояние изменено на READY")
            else:
                console.print(f"   ❌ Неверное состояние после инициализации: {coordinator.state}")
                return False
            
            # Проверяем компоненты
            if coordinator.table_manager is not None:
                console.print("   ✅ Table manager инициализирован")
            else:
                console.print("   ❌ Table manager не инициализирован")
                return False
            
            if coordinator.dependency_analyzer is not None:
                console.print("   ✅ Dependency analyzer инициализирован")
            else:
                console.print("   ❌ Dependency analyzer не инициализирован")
                return False
            
            if coordinator.monitor is not None:
                console.print("   ✅ Monitor инициализирован")
            else:
                console.print("   ❌ Monitor не инициализирован")
                return False
            
            return True
        else:
            console.print("   ❌ Ошибка инициализации системы")
            return False
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка тестирования инициализации системы: {e}[/red]")
        return False
    finally:
        coordinator.close()

def test_migration_readiness_validation():
    """Тест валидации готовности к миграции"""
    console.print("\n[bold blue]🧪 ТЕСТ 3: Валидация готовности к миграции[/bold blue]")
    
    coordinator = MigrationCoordinator()
    
    try:
        # Инициализация системы
        coordinator.initialize_migration_system()
        
        # Валидация готовности
        readiness = coordinator.validate_migration_readiness()
        
        if readiness:
            console.print("   ✅ Валидация выполнена успешно")
            console.print(f"   📊 Готовность: {readiness['readiness_percentage']:.1f}%")
            console.print(f"   ✅ Готовность: {readiness['is_ready']}")
            console.print(f"   📋 Проблемы: {len(readiness['issues'])}")
            
            if readiness['issues']:
                for issue in readiness['issues']:
                    console.print(f"      - {issue}")
            
            return True
        else:
            console.print("   ❌ Ошибка валидации готовности")
            return False
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка тестирования валидации: {e}[/red]")
        return False
    finally:
        coordinator.close()

def test_migration_plan():
    """Тест получения плана миграции"""
    console.print("\n[bold blue]🧪 ТЕСТ 4: Получение плана миграции[/bold blue]")
    
    coordinator = MigrationCoordinator()
    
    try:
        # Инициализация системы
        coordinator.initialize_migration_system()
        
        # Получение плана
        plan = coordinator.get_migration_plan()
        
        if plan and 'tables' in plan:
            console.print("   ✅ План миграции получен успешно")
            console.print(f"   📋 Таблиц в плане: {len(plan['tables'])}")
            console.print(f"   📊 Всего таблиц: {plan.get('total_tables', 0)}")
            console.print(f"   🔗 Критических зависимостей: {plan.get('critical_dependencies', 0)}")
            console.print(f"   ⏱️ Оценочная длительность: {plan.get('estimated_duration_hours', 0):.1f} часов")
            
            # Показываем первые несколько таблиц
            if plan['tables']:
                console.print("   📝 Первые таблицы в плане:")
                for i, table in enumerate(plan['tables'][:5]):
                    console.print(f"      {i+1}. {table}")
                if len(plan['tables']) > 5:
                    console.print(f"      ... и ещё {len(plan['tables']) - 5} таблиц")
            
            return True
        else:
            console.print("   ❌ План миграции не получен")
            return False
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка тестирования плана миграции: {e}[/red]")
        return False
    finally:
        coordinator.close()

def test_system_health():
    """Тест получения состояния системы"""
    console.print("\n[bold blue]🧪 ТЕСТ 5: Получение состояния системы[/bold blue]")
    
    coordinator = MigrationCoordinator()
    
    try:
        # Инициализация системы
        coordinator.initialize_migration_system()
        
        # Получение состояния
        health = coordinator.get_system_health()
        
        if health:
            console.print("   ✅ Состояние системы получено успешно")
            console.print(f"   🏥 Общий статус: {health['overall_status']}")
            console.print(f"   ❌ Есть ошибки: {health['has_errors']}")
            console.print(f"   📊 Компонентов: {len(health['components'])}")
            
            # Показываем состояние компонентов
            for component, status in health['components'].items():
                console.print(f"      - {component}: {status['status']}")
                if 'error' in status:
                    console.print(f"        Ошибка: {status['error']}")
            
            if health['errors']:
                console.print("   🚨 Ошибки системы:")
                for error in health['errors']:
                    console.print(f"      - {error}")
            
            return True
        else:
            console.print("   ❌ Состояние системы не получено")
            return False
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка тестирования состояния системы: {e}[/red]")
        return False
    finally:
        coordinator.close()

def test_migration_status():
    """Тест получения статуса миграции"""
    console.print("\n[bold blue]🧪 ТЕСТ 6: Получение статуса миграции[/bold blue]")
    
    coordinator = MigrationCoordinator()
    
    try:
        # Инициализация системы
        coordinator.initialize_migration_system()
        
        # Получение статуса
        status = coordinator.get_migration_status()
        
        if status:
            console.print("   ✅ Статус миграции получен успешно")
            console.print(f"   📊 Состояние: {status['state']}")
            console.print(f"   📈 Прогресс: {status['progress']['percentage']:.1f}%")
            console.print(f"   ✅ Завершено: {status['progress']['completed']}")
            console.print(f"   📋 Всего: {status['progress']['total']}")
            console.print(f"   ❌ Ошибок: {status['error_count']}")
            
            if status['runtime_seconds']:
                console.print(f"   ⏱️ Время выполнения: {status['runtime_seconds']:.1f} сек")
            
            if status['eta']:
                console.print(f"   🎯 ETA: {status['eta']}")
            
            return True
        else:
            console.print("   ❌ Статус миграции не получен")
            return False
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка тестирования статуса: {e}[/red]")
        return False
    finally:
        coordinator.close()

def test_migration_control():
    """Тест управления миграцией"""
    console.print("\n[bold blue]🧪 ТЕСТ 7: Управление миграцией[/bold blue]")
    
    coordinator = MigrationCoordinator()
    
    try:
        # Инициализация системы
        coordinator.initialize_migration_system()
        
        # Запуск миграции
        console.print("   🚀 Запуск миграции...")
        start_success = coordinator.start_migration_process()
        
        if start_success:
            console.print("   ✅ Миграция запущена успешно")
            
            # Проверяем состояние
            if coordinator.state == MigrationState.RUNNING:
                console.print("   ✅ Состояние изменено на RUNNING")
            else:
                console.print(f"   ❌ Неверное состояние после запуска: {coordinator.state}")
                return False
            
            # Ждём немного
            time.sleep(2)
            
            # Приостановка миграции
            console.print("   ⏸️ Приостановка миграции...")
            pause_success = coordinator.pause_migration()
            
            if pause_success:
                console.print("   ✅ Миграция приостановлена успешно")
                
                # Проверяем состояние
                if coordinator.state == MigrationState.PAUSED:
                    console.print("   ✅ Состояние изменено на PAUSED")
                else:
                    console.print(f"   ❌ Неверное состояние после приостановки: {coordinator.state}")
                    return False
                
                # Возобновление миграции
                console.print("   ▶️ Возобновление миграции...")
                resume_success = coordinator.resume_migration()
                
                if resume_success:
                    console.print("   ✅ Миграция возобновлена успешно")
                    
                    # Проверяем состояние
                    if coordinator.state == MigrationState.RUNNING:
                        console.print("   ✅ Состояние изменено на RUNNING")
                    else:
                        console.print(f"   ❌ Неверное состояние после возобновления: {coordinator.state}")
                        return False
                else:
                    console.print("   ❌ Ошибка возобновления миграции")
                    return False
            else:
                console.print("   ❌ Ошибка приостановки миграции")
                return False
        else:
            console.print("   ❌ Ошибка запуска миграции")
            return False
        
        # Остановка миграции
        console.print("   🛑 Остановка миграции...")
        stop_success = coordinator.stop_migration()
        
        if stop_success:
            console.print("   ✅ Миграция остановлена успешно")
            
            # Проверяем состояние
            if coordinator.state == MigrationState.STOPPED:
                console.print("   ✅ Состояние изменено на STOPPED")
            else:
                console.print(f"   ❌ Неверное состояние после остановки: {coordinator.state}")
                return False
        else:
            console.print("   ❌ Ошибка остановки миграции")
            return False
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка тестирования управления миграцией: {e}[/red]")
        return False
    finally:
        coordinator.close()

def test_error_handling():
    """Тест обработки ошибок"""
    console.print("\n[bold blue]🧪 ТЕСТ 8: Обработка ошибок[/bold blue]")
    
    coordinator = MigrationCoordinator()
    
    try:
        # Инициализация системы
        coordinator.initialize_migration_system()
        
        # Тестируем обработку различных типов ошибок
        error_types = [
            {'type': 'TEMPORARY', 'message': 'Временная ошибка сети'},
            {'type': 'DEPENDENCY', 'message': 'Ошибка зависимости'},
            {'type': 'CRITICAL', 'message': 'Критическая ошибка системы'}
        ]
        
        for error_info in error_types:
            console.print(f"   🚨 Тестирование ошибки: {error_info['type']}")
            
            success = coordinator.handle_error(error_info)
            
            if success:
                console.print(f"   ✅ Ошибка {error_info['type']} обработана успешно")
            else:
                console.print(f"   ❌ Ошибка обработки {error_info['type']}")
                return False
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка тестирования обработки ошибок: {e}[/red]")
        return False
    finally:
        coordinator.close()

def test_status_dashboard():
    """Тест отображения дашборда статуса"""
    console.print("\n[bold blue]🧪 ТЕСТ 9: Отображение дашборда статуса[/bold blue]")
    
    coordinator = MigrationCoordinator()
    
    try:
        # Инициализация системы
        coordinator.initialize_migration_system()
        
        # Отображение дашборда
        console.print("   📊 Отображение дашборда статуса...")
        coordinator.display_status_dashboard()
        
        console.print("   ✅ Дашборд отображён успешно")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка отображения дашборда: {e}[/red]")
        return False
    finally:
        coordinator.close()

def test_coordinator_lifecycle():
    """Тест жизненного цикла координатора"""
    console.print("\n[bold blue]🧪 ТЕСТ 10: Жизненный цикл координатора[/bold blue]")
    
    coordinator = MigrationCoordinator()
    
    try:
        # Проверяем начальное состояние
        if coordinator.state == MigrationState.INITIALIZING:
            console.print("   ✅ Начальное состояние: INITIALIZING")
        else:
            console.print(f"   ❌ Неверное начальное состояние: {coordinator.state}")
            return False
        
        # Инициализация
        init_success = coordinator.initialize_migration_system()
        if not init_success:
            console.print("   ❌ Ошибка инициализации")
            return False
        
        if coordinator.state == MigrationState.READY:
            console.print("   ✅ Состояние после инициализации: READY")
        else:
            console.print(f"   ❌ Неверное состояние после инициализации: {coordinator.state}")
            return False
        
        # Запуск миграции
        start_success = coordinator.start_migration_process()
        if not start_success:
            console.print("   ❌ Ошибка запуска миграции")
            return False
        
        if coordinator.state == MigrationState.RUNNING:
            console.print("   ✅ Состояние после запуска: RUNNING")
        else:
            console.print(f"   ❌ Неверное состояние после запуска: {coordinator.state}")
            return False
        
        # Остановка миграции
        stop_success = coordinator.stop_migration()
        if not stop_success:
            console.print("   ❌ Ошибка остановки миграции")
            return False
        
        if coordinator.state == MigrationState.STOPPED:
            console.print("   ✅ Состояние после остановки: STOPPED")
        else:
            console.print(f"   ❌ Неверное состояние после остановки: {coordinator.state}")
            return False
        
        # Закрытие координатора
        coordinator.close()
        console.print("   ✅ Координатор закрыт успешно")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Ошибка тестирования жизненного цикла: {e}[/red]")
        return False
    finally:
        try:
            coordinator.close()
        except:
            pass

def main():
    """Основная функция тестирования"""
    console.print(Panel.fit(
        "[bold green]🧪 ТЕСТИРОВАНИЕ МОДУЛЯ ИНТЕГРАЦИИ И КООРДИНАЦИИ[/bold green]\n"
        "Тестирование всех функций MigrationCoordinator",
        border_style="green"
    ))
    
    tests = [
        ("Инициализация координатора", test_coordinator_initialization),
        ("Инициализация системы", test_system_initialization),
        ("Валидация готовности к миграции", test_migration_readiness_validation),
        ("Получение плана миграции", test_migration_plan),
        ("Получение состояния системы", test_system_health),
        ("Получение статуса миграции", test_migration_status),
        ("Управление миграцией", test_migration_control),
        ("Обработка ошибок", test_error_handling),
        ("Отображение дашборда статуса", test_status_dashboard),
        ("Жизненный цикл координатора", test_coordinator_lifecycle)
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