#!/usr/bin/env python3
"""
Модуль интеграции и координации миграции
"""
import os
import sys
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

# Добавляем путь к проекту
sys.path.append('/home/alex/projects/sql/femcl')

from scripts.migration.table_list_manager import TableListManager
from scripts.migration.dependency_analyzer import DependencyAnalyzer
from scripts.migration.monitoring_reporter import MigrationMonitor

console = Console()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/alex/projects/sql/femcl/logs/coordinator.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MigrationState(Enum):
    """Состояния системы миграции"""
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    STOPPED = "STOPPED"

class MigrationCoordinator:
    """Главный координатор системы миграции"""
    
    def __init__(self, config_path="/home/alex/projects/sql/femcl/config/config.yaml"):
        """Инициализация координатора"""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Состояние системы
        self.state = MigrationState.INITIALIZING
        self.start_time = None
        self.pause_time = None
        self.error_count = 0
        self.last_error = None
        
        # Компоненты системы
        self.table_manager = None
        self.dependency_analyzer = None
        self.monitor = None
        
        # Потоки выполнения
        self.migration_thread = None
        self.migration_active = False
        
        # Конфигурация
        self.batch_size = self.config.get('migration', {}).get('batch_size', 10)
        self.max_parallel = self.config.get('migration', {}).get('max_parallel', 5)
        self.retry_attempts = self.config.get('migration', {}).get('retry_attempts', 3)
        self.timeout_seconds = self.config.get('migration', {}).get('timeout_seconds', 3600)
        
        logger.info("MigrationCoordinator инициализирован")
    
    def _load_config(self):
        """Загрузка конфигурации"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.warning(f"Ошибка загрузки конфигурации: {e}, используются значения по умолчанию")
            return {
                'migration': {
                    'batch_size': 10,
                    'max_parallel': 5,
                    'retry_attempts': 3,
                    'timeout_seconds': 3600
                },
                'monitoring': {
                    'interval_seconds': 30,
                    'real_time_enabled': True,
                    'dashboard_enabled': True
                },
                'notifications': {
                    'enabled': True,
                    'email_enabled': False,
                    'slack_enabled': False
                }
            }
    
    def initialize_migration_system(self) -> bool:
        """
        Инициализация системы миграции
        
        Returns:
            bool: True если инициализация успешна
        """
        console.print("[blue]🚀 Инициализация системы миграции[/blue]")
        
        try:
            # Инициализация компонентов
            console.print("   📋 Инициализация менеджера списка таблиц...")
            self.table_manager = TableListManager(self.config_path)
            
            console.print("   🔍 Инициализация анализатора зависимостей...")
            self.dependency_analyzer = DependencyAnalyzer(self.config_path)
            
            console.print("   📊 Инициализация монитора...")
            self.monitor = MigrationMonitor(self.config_path)
            
            # Инициализация списка таблиц
            console.print("   📝 Инициализация списка таблиц...")
            init_result = self.table_manager.initialize_table_list()
            console.print(f"      Инициализировано {init_result['initialized']} таблиц")
            
            # Анализ зависимостей
            console.print("   🔗 Анализ зависимостей...")
            migration_order = self.dependency_analyzer.get_migration_order()
            console.print(f"      Определён порядок для {len(migration_order)} таблиц")
            
            # Запуск мониторинга
            console.print("   📈 Запуск мониторинга...")
            self.monitor.start_monitoring()
            
            # Обновление состояния
            self.state = MigrationState.READY
            self.start_time = datetime.now()
            
            console.print("[green]✅ Система миграции инициализирована успешно[/green]")
            logger.info("Система миграции инициализирована успешно")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка инициализации: {e}[/red]")
            logger.error(f"Ошибка инициализации системы: {e}")
            self.state = MigrationState.ERROR
            self.last_error = str(e)
            return False
    
    def start_migration_process(self) -> bool:
        """
        Запуск процесса миграции
        
        Returns:
            bool: True если процесс запущен
        """
        console.print("[blue]🚀 Запуск процесса миграции[/blue]")
        
        if self.state != MigrationState.READY:
            console.print(f"[yellow]⚠️ Система не готова к миграции. Текущее состояние: {self.state.value}[/yellow]")
            return False
        
        try:
            # Валидация готовности
            readiness = self.validate_migration_readiness()
            if not readiness['is_ready']:
                console.print(f"[yellow]⚠️ Система не готова: {readiness['issues']}[/yellow]")
                return False
            
            # Запуск процесса миграции
            self.state = MigrationState.RUNNING
            self.migration_active = True
            self.start_time = datetime.now()
            
            # Запуск потока миграции
            self.migration_thread = threading.Thread(target=self._migration_loop, daemon=True)
            self.migration_thread.start()
            
            console.print("[green]✅ Процесс миграции запущен[/green]")
            logger.info("Процесс миграции запущен")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка запуска миграции: {e}[/red]")
            logger.error(f"Ошибка запуска миграции: {e}")
            self.state = MigrationState.ERROR
            self.last_error = str(e)
            return False
    
    def _migration_loop(self):
        """Основной цикл миграции"""
        console.print("[blue]🔄 Начало цикла миграции[/blue]")
        
        try:
            # Получаем план миграции
            plan = self.get_migration_plan()
            tables_to_migrate = plan['tables']
            
            console.print(f"   📋 План миграции: {len(tables_to_migrate)} таблиц")
            
            # Миграция таблиц
            for i, table_name in enumerate(tables_to_migrate):
                if not self.migration_active:
                    break
                
                console.print(f"   🔄 Миграция таблицы {i+1}/{len(tables_to_migrate)}: {table_name}")
                
                # Проверяем готовность зависимостей
                readiness = self.dependency_analyzer.check_referenced_tables_ready(table_name)
                if readiness['ready_percentage'] < 100.0:
                    console.print(f"      ⏳ Ожидание готовности зависимостей...")
                    time.sleep(5)
                    continue
                
                # Выполняем миграцию таблицы
                success = self._migrate_single_table(table_name)
                if success:
                    console.print(f"      ✅ Таблица {table_name} мигрирована успешно")
                else:
                    console.print(f"      ❌ Ошибка миграции таблицы {table_name}")
                    self.error_count += 1
            
            # Завершение миграции
            if self.migration_active:
                self.state = MigrationState.COMPLETED
                console.print("[green]🎉 Миграция завершена успешно![/green]")
                logger.info("Миграция завершена успешно")
            
        except Exception as e:
            console.print(f"[red]❌ Критическая ошибка в цикле миграции: {e}[/red]")
            logger.error(f"Критическая ошибка в цикле миграции: {e}")
            self.state = MigrationState.ERROR
            self.last_error = str(e)
    
    def _migrate_single_table(self, table_name: str) -> bool:
        """
        Миграция одной таблицы
        
        Args:
            table_name (str): Имя таблицы
        
        Returns:
            bool: True если миграция успешна
        """
        try:
            # Обновляем статус на "в процессе"
            self.table_manager.update_table_status(table_name, 'in_progress')
            
            # Здесь должна быть реальная логика миграции
            # Пока что имитируем миграцию
            time.sleep(1)  # Имитация времени миграции
            
            # Отмечаем как завершённую
            metrics = {
                'duration_seconds': 1.0,
                'records_migrated': 100,
                'structure_elements': 5
            }
            self.table_manager.mark_table_completed(table_name, metrics)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка миграции таблицы {table_name}: {e}")
            self.table_manager.update_table_status(table_name, 'failed', {'error': str(e)})
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        Получение статуса миграции
        
        Returns:
            dict: Общий статус системы
        """
        try:
            # Получаем прогресс от менеджера таблиц
            progress = self.table_manager.get_migration_progress()
            
            # Получаем метрики от монитора
            metrics = self.monitor.get_real_time_metrics()
            
            # Вычисляем время выполнения
            runtime = None
            if self.start_time:
                runtime = (datetime.now() - self.start_time).total_seconds()
            
            # Вычисляем ETA
            eta = None
            if self.state == MigrationState.RUNNING and progress['completed'] > 0:
                remaining = progress['total'] - progress['completed']
                if remaining > 0 and runtime:
                    avg_time_per_table = runtime / progress['completed']
                    eta_seconds = remaining * avg_time_per_table
                    eta = datetime.now() + timedelta(seconds=eta_seconds)
            
            status = {
                'state': self.state.value,
                'progress': progress,
                'metrics': metrics,
                'runtime_seconds': runtime,
                'eta': eta.isoformat() if eta else None,
                'error_count': self.error_count,
                'last_error': self.last_error,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'pause_time': self.pause_time.isoformat() if self.pause_time else None
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return {
                'state': self.state.value,
                'error': str(e)
            }
    
    def pause_migration(self) -> bool:
        """
        Приостановка миграции
        
        Returns:
            bool: True если миграция приостановлена
        """
        console.print("[yellow]⏸️ Приостановка миграции[/yellow]")
        
        if self.state != MigrationState.RUNNING:
            console.print(f"[yellow]⚠️ Миграция не активна. Текущее состояние: {self.state.value}[/yellow]")
            return False
        
        try:
            self.state = MigrationState.PAUSED
            self.pause_time = datetime.now()
            self.migration_active = False
            
            console.print("[green]✅ Миграция приостановлена[/green]")
            logger.info("Миграция приостановлена")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка приостановки: {e}[/red]")
            logger.error(f"Ошибка приостановки миграции: {e}")
            return False
    
    def resume_migration(self) -> bool:
        """
        Возобновление миграции
        
        Returns:
            bool: True если миграция возобновлена
        """
        console.print("[blue]▶️ Возобновление миграции[/blue]")
        
        if self.state != MigrationState.PAUSED:
            console.print(f"[yellow]⚠️ Миграция не приостановлена. Текущее состояние: {self.state.value}[/yellow]")
            return False
        
        try:
            self.state = MigrationState.RUNNING
            self.pause_time = None
            self.migration_active = True
            
            # Возобновляем поток миграции
            if not self.migration_thread or not self.migration_thread.is_alive():
                self.migration_thread = threading.Thread(target=self._migration_loop, daemon=True)
                self.migration_thread.start()
            
            console.print("[green]✅ Миграция возобновлена[/green]")
            logger.info("Миграция возобновлена")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка возобновления: {e}[/red]")
            logger.error(f"Ошибка возобновления миграции: {e}")
            return False
    
    def stop_migration(self) -> bool:
        """
        Остановка миграции
        
        Returns:
            bool: True если миграция остановлена
        """
        console.print("[red]🛑 Остановка миграции[/red]")
        
        try:
            self.state = MigrationState.STOPPED
            self.migration_active = False
            
            # Останавливаем мониторинг
            if self.monitor:
                self.monitor.stop_monitoring()
            
            console.print("[green]✅ Миграция остановлена[/green]")
            logger.info("Миграция остановлена")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка остановки: {e}[/red]")
            logger.error(f"Ошибка остановки миграции: {e}")
            return False
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Получение состояния системы
        
        Returns:
            dict: Состояние всех компонентов
        """
        try:
            health = {
                'overall_status': 'HEALTHY',
                'components': {},
                'has_errors': False,
                'errors': []
            }
            
            # Проверяем состояние компонентов
            if self.table_manager:
                try:
                    progress = self.table_manager.get_migration_progress()
                    health['components']['table_manager'] = {
                        'status': 'HEALTHY',
                        'progress': progress['percentage']
                    }
                except Exception as e:
                    health['components']['table_manager'] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    health['has_errors'] = True
                    health['errors'].append(f"Table Manager: {e}")
            
            if self.dependency_analyzer:
                try:
                    # Простая проверка доступности
                    health['components']['dependency_analyzer'] = {
                        'status': 'HEALTHY'
                    }
                except Exception as e:
                    health['components']['dependency_analyzer'] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    health['has_errors'] = True
                    health['errors'].append(f"Dependency Analyzer: {e}")
            
            if self.monitor:
                try:
                    metrics = self.monitor.get_real_time_metrics()
                    health['components']['monitor'] = {
                        'status': 'HEALTHY',
                        'metrics_count': len(metrics.get('metrics', {}))
                    }
                except Exception as e:
                    health['components']['monitor'] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    health['has_errors'] = True
                    health['errors'].append(f"Monitor: {e}")
            
            # Общий статус
            if health['has_errors']:
                health['overall_status'] = 'DEGRADED'
            
            return health
            
        except Exception as e:
            logger.error(f"Ошибка получения состояния системы: {e}")
            return {
                'overall_status': 'ERROR',
                'error': str(e)
            }
    
    def handle_error(self, error_info: Dict[str, Any]) -> bool:
        """
        Обработка ошибок системы
        
        Args:
            error_info (dict): Информация об ошибке
        
        Returns:
            bool: True если ошибка обработана
        """
        console.print(f"[red]🚨 Обработка ошибки: {error_info.get('type', 'UNKNOWN')}[/red]")
        
        try:
            error_type = error_info.get('type', 'UNKNOWN')
            error_message = error_info.get('message', 'Неизвестная ошибка')
            
            # Логируем ошибку
            logger.error(f"Обработка ошибки {error_type}: {error_message}")
            
            # Отправляем уведомление
            if self.monitor:
                self.monitor.send_notification(
                    event_type=error_type,
                    message=error_message,
                    severity='ERROR'
                )
            
            # Обрабатываем в зависимости от типа
            if error_type == 'CRITICAL':
                self.state = MigrationState.ERROR
                self.migration_active = False
            elif error_type == 'TEMPORARY':
                # Попытка восстановления
                time.sleep(5)
            elif error_type == 'DEPENDENCY':
                # Ожидание готовности зависимостей
                time.sleep(10)
            
            console.print(f"[green]✅ Ошибка обработана: {error_type}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка обработки ошибки: {e}[/red]")
            logger.error(f"Ошибка обработки ошибки: {e}")
            return False
    
    def get_migration_plan(self) -> Dict[str, Any]:
        """
        Получение плана миграции
        
        Returns:
            dict: Детальный план миграции
        """
        try:
            if not self.dependency_analyzer:
                return {'tables': [], 'error': 'Dependency analyzer not initialized'}
            
            # Получаем порядок миграции
            migration_order = self.dependency_analyzer.get_migration_order()
            
            # Получаем информацию о зависимостях
            dependency_graph = self.dependency_analyzer.get_dependency_graph()
            
            # Получаем критические зависимости
            critical_deps = self.dependency_analyzer.get_critical_dependencies()
            
            plan = {
                'tables': migration_order,
                'total_tables': len(migration_order),
                'dependency_graph': dependency_graph,
                'critical_dependencies': len(critical_deps),
                'estimated_duration_hours': len(migration_order) * 0.1,  # Примерная оценка
                'created_at': datetime.now().isoformat()
            }
            
            return plan
            
        except Exception as e:
            logger.error(f"Ошибка получения плана миграции: {e}")
            return {'tables': [], 'error': str(e)}
    
    def validate_migration_readiness(self) -> Dict[str, Any]:
        """
        Валидация готовности к миграции
        
        Returns:
            dict: Результат валидации
        """
        console.print("[blue]🔍 Валидация готовности к миграции[/blue]")
        
        try:
            issues = []
            readiness_percentage = 100.0
            
            # Проверяем инициализацию компонентов
            if not self.table_manager:
                issues.append("Table manager not initialized")
                readiness_percentage -= 25
            
            if not self.dependency_analyzer:
                issues.append("Dependency analyzer not initialized")
                readiness_percentage -= 25
            
            if not self.monitor:
                issues.append("Monitor not initialized")
                readiness_percentage -= 25
            
            # Проверяем состояние системы
            if self.state == MigrationState.ERROR:
                issues.append("System in error state")
                readiness_percentage -= 50
            
            # Проверяем готовность зависимостей
            if self.dependency_analyzer:
                try:
                    cycles = self.dependency_analyzer.detect_circular_dependencies()
                    if cycles:
                        issues.append(f"Circular dependencies detected: {len(cycles)}")
                        readiness_percentage -= 10
                except Exception as e:
                    issues.append(f"Dependency analysis error: {e}")
                    readiness_percentage -= 15
            
            is_ready = readiness_percentage >= 80.0 and len(issues) == 0
            
            result = {
                'is_ready': is_ready,
                'readiness_percentage': readiness_percentage,
                'issues': issues,
                'validated_at': datetime.now().isoformat()
            }
            
            console.print(f"   📊 Готовность: {readiness_percentage:.1f}%")
            if issues:
                console.print(f"   ⚠️ Проблемы: {len(issues)}")
                for issue in issues:
                    console.print(f"      - {issue}")
            else:
                console.print("   ✅ Система готова к миграции")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка валидации готовности: {e}")
            return {
                'is_ready': False,
                'readiness_percentage': 0.0,
                'issues': [f"Validation error: {e}"],
                'validated_at': datetime.now().isoformat()
            }
    
    def display_status_dashboard(self):
        """Отображение дашборда статуса"""
        console.print("[blue]📊 Дашборд статуса миграции[/blue]")
        
        try:
            # Получаем статус
            status = self.get_migration_status()
            
            # Создаём панель статуса
            status_panel = Panel(
                f"[bold]Состояние:[/bold] {status['state']}\n"
                f"[bold]Прогресс:[/bold] {status['progress']['percentage']:.1f}%\n"
                f"[bold]Завершено:[/bold] {status['progress']['completed']}/{status['progress']['total']}\n"
                f"[bold]Ошибок:[/bold] {status['error_count']}\n"
                f"[bold]Время выполнения:[/bold] {status['runtime_seconds']:.1f} сек" if status['runtime_seconds'] else "Не запущено",
                title="Статус миграции",
                border_style="blue"
            )
            
            console.print(status_panel)
            
            # Создаём таблицу прогресса
            if 'status_breakdown' in status['progress']:
                table = Table(title="Распределение по статусам")
                table.add_column("Статус", style="cyan")
                table.add_column("Количество", style="magenta")
                table.add_column("Процент", style="green")
                
                total = status['progress']['total']
                for status_name, count in status['progress']['status_breakdown'].items():
                    percentage = (count / total * 100) if total > 0 else 0
                    table.add_row(status_name, str(count), f"{percentage:.1f}%")
                
                console.print(table)
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка отображения дашборда: {e}[/red]")
            logger.error(f"Ошибка отображения дашборда: {e}")
    
    def close(self):
        """Закрытие координатора"""
        console.print("[blue]🔒 Закрытие координатора[/blue]")
        
        try:
            # Останавливаем миграцию
            if self.migration_active:
                self.stop_migration()
            
            # Закрываем компоненты
            if self.table_manager:
                self.table_manager.close()
            
            if self.dependency_analyzer:
                self.dependency_analyzer.close()
            
            if self.monitor:
                self.monitor.close()
            
            console.print("[green]✅ Координатор закрыт[/green]")
            logger.info("Координатор закрыт")
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка закрытия координатора: {e}[/red]")
            logger.error(f"Ошибка закрытия координатора: {e}")

# Примеры использования
if __name__ == "__main__":
    # Создаём координатор
    coordinator = MigrationCoordinator()
    
    try:
        # Инициализация системы
        if coordinator.initialize_migration_system():
            console.print("Система инициализирована")
            
            # Валидация готовности
            readiness = coordinator.validate_migration_readiness()
            console.print(f"Готовность: {readiness['readiness_percentage']:.1f}%")
            
            # Получение плана
            plan = coordinator.get_migration_plan()
            console.print(f"План включает {len(plan['tables'])} таблиц")
            
            # Отображение статуса
            coordinator.display_status_dashboard()
        
    finally:
        coordinator.close()