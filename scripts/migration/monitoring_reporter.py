#!/usr/bin/env python3
"""
Модуль мониторинга и отчётности для миграции

ОБНОВЛЕНО: Использует ConnectionManager
"""
import os
import sys
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

# Добавляем путь к модулям проекта
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "code"))

from infrastructure.classes import ConnectionManager

console = Console()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/alex/projects/sql/femcl/logs/monitoring.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MigrationMonitor:
    """
    Класс для мониторинга и отчётности миграции.
    
    ОБНОВЛЕНО: Использует ConnectionManager для подключений к БД.
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        """
        Инициализация монитора.
        
        Args:
            connection_manager: Экземпляр ConnectionManager
        """
        self.conn_mgr = connection_manager
        self.task_id = connection_manager.task_id
        self.monitoring_active = False
        self.monitoring_thread = None
        self._ensure_monitoring_tables()
    
    def _execute_query(self, query, params=None):
        """
        Выполнение SQL запроса.
        
        Args:
            query: SQL запрос
            params: Параметры запроса
        
        Returns:
            List[Dict]: Результаты запроса как список словарей
        """
        conn = self.conn_mgr.get_postgres_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
        else:
            conn.commit()
            result = []
        
        cursor.close()
        return result
                cursor.close()
    
    def _ensure_monitoring_tables(self):
        """Создание таблиц для мониторинга если не существуют"""
        create_metrics_table = """
        CREATE TABLE IF NOT EXISTS mcl.migration_metrics (
            id SERIAL PRIMARY KEY,
            metric_name VARCHAR(100) NOT NULL,
            metric_value DECIMAL(15,4),
            metric_unit VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            table_name VARCHAR(255),
            phase VARCHAR(50)
        );
        """
        
        create_events_table = """
        CREATE TABLE IF NOT EXISTS mcl.migration_events (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(100) NOT NULL,
            event_message TEXT,
            severity VARCHAR(20) DEFAULT 'INFO',
            table_name VARCHAR(255),
            phase VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        );
        """
        
        create_notifications_table = """
        CREATE TABLE IF NOT EXISTS mcl.migration_notifications (
            id SERIAL PRIMARY KEY,
            notification_type VARCHAR(100) NOT NULL,
            title VARCHAR(255),
            message TEXT,
            severity VARCHAR(20),
            status VARCHAR(20) DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP,
            recipient VARCHAR(255)
        );
        """
        
        create_indexes = """
        CREATE INDEX IF NOT EXISTS idx_migration_metrics_name_time 
        ON mcl.migration_metrics(metric_name, timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_migration_events_type_time 
        ON mcl.migration_events(event_type, timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_migration_notifications_status 
        ON mcl.migration_notifications(status);
        """
        
        try:
            self._execute_query(create_metrics_table)
            self._execute_query(create_events_table)
            self._execute_query(create_notifications_table)
            self._execute_query(create_indexes)
            logger.info("Таблицы для мониторинга созданы или уже существуют")
        except Exception as e:
            logger.error(f"Ошибка создания таблиц мониторинга: {e}")
            raise
    
    def start_monitoring(self) -> bool:
        """
        Запуск мониторинга в реальном времени
        
        Returns:
            bool: True если мониторинг запущен успешно
        """
        console.print("[blue]🚀 Запуск мониторинга миграции[/blue]")
        
        if self.monitoring_active:
            console.print("[yellow]⚠️ Мониторинг уже активен[/yellow]")
            return True
        
        try:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            console.print("[green]✅ Мониторинг запущен успешно[/green]")
            logger.info("Мониторинг миграции запущен")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка запуска мониторинга: {e}[/red]")
            logger.error(f"Ошибка запуска мониторинга: {e}")
            return False
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        console.print("[blue]🛑 Остановка мониторинга[/blue]")
        
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        console.print("[green]✅ Мониторинг остановлен[/green]")
        logger.info("Мониторинг миграции остановлен")
    
    def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while self.monitoring_active:
            try:
                # Собираем метрики
                self._collect_metrics()
                
                # Проверяем события
                self._check_events()
                
                # Отправляем уведомления
                self._process_notifications()
                
                # Ждём перед следующей итерацией
                time.sleep(30)  # Обновление каждые 30 секунд
                
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                time.sleep(60)  # Увеличиваем интервал при ошибке
    
    def _collect_metrics(self):
        """Сбор метрик миграции"""
        try:
            # Получаем общий прогресс
            progress_query = """
            SELECT 
                COUNT(*) as total_tables,
                COUNT(CASE WHEN current_status = 'completed' THEN 1 END) as completed_tables,
                COUNT(CASE WHEN current_status = 'failed' THEN 1 END) as failed_tables,
                COUNT(CASE WHEN current_status = 'in_progress' THEN 1 END) as in_progress_tables
            FROM mcl.migration_status
            """
            
            progress_data = self._execute_query(progress_query)
            if progress_data:
                progress = progress_data[0]
                total = progress['total_tables']
                completed = progress['completed_tables']
                failed = progress['failed_tables']
                in_progress = progress['in_progress_tables']
                
                # Сохраняем метрики
                self._save_metric('progress_percentage', (completed / total * 100) if total > 0 else 0, '%')
                self._save_metric('completed_tables', completed, 'tables')
                self._save_metric('failed_tables', failed, 'tables')
                self._save_metric('in_progress_tables', in_progress, 'tables')
                
                # Вычисляем скорость миграции
                speed_query = """
                SELECT 
                    COUNT(*) as tables_completed_today,
                    AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration_seconds
                FROM mcl.migration_status 
                WHERE current_status = 'completed' 
                AND DATE(end_time) = CURRENT_DATE
                """
                
                speed_data = self._execute_query(speed_query)
                if speed_data and speed_data[0]['tables_completed_today']:
                    tables_today = speed_data[0]['tables_completed_today']
                    avg_duration = speed_data[0]['avg_duration_seconds'] or 0
                    
                    # Скорость в таблицах в час
                    hours_elapsed = (datetime.now().hour + 1) if datetime.now().hour > 0 else 1
                    speed_per_hour = tables_today / hours_elapsed
                    
                    self._save_metric('migration_speed', speed_per_hour, 'tables/hour')
                    self._save_metric('avg_migration_time', avg_duration, 'seconds')
                
        except Exception as e:
            logger.error(f"Ошибка сбора метрик: {e}")
    
    def _save_metric(self, name: str, value: float, unit: str, table_name: str = None, phase: str = None):
        """Сохранение метрики"""
        try:
            insert_query = """
            INSERT INTO mcl.migration_metrics (metric_name, metric_value, metric_unit, table_name, phase)
            VALUES (%s, %s, %s, %s, %s)
            """
            self._execute_query(insert_query, (name, value, unit, table_name, phase))
        except Exception as e:
            logger.error(f"Ошибка сохранения метрики {name}: {e}")
    
    def _check_events(self):
        """Проверка событий и генерация уведомлений"""
        try:
            # Проверяем критические ошибки
            critical_errors_query = """
            SELECT table_name, last_error, updated_at
            FROM mcl.migration_status 
            WHERE current_status = 'failed' 
            AND attempt_count >= 3
            AND updated_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
            """
            
            critical_errors = self._execute_query(critical_errors_query)
            for error in critical_errors:
                self._log_event(
                    'CRITICAL_ERROR',
                    f"Критическая ошибка в таблице {error['table_name']}: {error['last_error']}",
                    'CRITICAL',
                    error['table_name']
                )
            
            # Проверяем долго выполняющиеся операции
            long_running_query = """
            SELECT table_name, start_time
            FROM mcl.migration_status 
            WHERE current_status = 'in_progress' 
            AND start_time < CURRENT_TIMESTAMP - INTERVAL '2 hours'
            """
            
            long_running = self._execute_query(long_running_query)
            for table in long_running:
                self._log_event(
                    'LONG_RUNNING',
                    f"Таблица {table['table_name']} выполняется более 2 часов",
                    'WARNING',
                    table['table_name']
                )
                
        except Exception as e:
            logger.error(f"Ошибка проверки событий: {e}")
    
    def _log_event(self, event_type: str, message: str, severity: str, table_name: str = None, metadata: Dict = None):
        """Логирование события"""
        try:
            insert_query = """
            INSERT INTO mcl.migration_events (event_type, event_message, severity, table_name, metadata)
            VALUES (%s, %s, %s, %s, %s)
            """
            metadata_json = json.dumps(metadata) if metadata else None
            self._execute_query(insert_query, (event_type, message, severity, table_name, metadata_json))
            
            logger.info(f"Событие: {event_type} - {message}")
            
        except Exception as e:
            logger.error(f"Ошибка логирования события: {e}")
    
    def _process_notifications(self):
        """Обработка уведомлений"""
        try:
            # Получаем неотправленные уведомления
            pending_query = """
            SELECT * FROM mcl.migration_notifications 
            WHERE status = 'PENDING' 
            ORDER BY created_at
            """
            
            pending_notifications = self._execute_query(pending_query)
            
            for notification in pending_notifications:
                # Отправляем уведомление
                success = self._send_notification_internal(notification)
                
                # Обновляем статус
                if success:
                    update_query = """
                    UPDATE mcl.migration_notifications 
                    SET status = 'SENT', sent_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                    """
                    self._execute_query(update_query, (notification['id'],))
                
        except Exception as e:
            logger.error(f"Ошибка обработки уведомлений: {e}")
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """
        Получение метрик в реальном времени
        
        Returns:
            dict: Текущие метрики миграции
        """
        console.print("[blue]📊 Получение метрик в реальном времени[/blue]")
        
        try:
            # Получаем последние метрики
            metrics_query = """
            SELECT metric_name, metric_value, metric_unit, timestamp
            FROM mcl.migration_metrics 
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
            ORDER BY timestamp DESC
            """
            
            metrics_data = self._execute_query(metrics_query)
            
            # Группируем метрики по имени
            metrics = {}
            for metric in metrics_data:
                name = metric['metric_name']
                if name not in metrics:
                    metrics[name] = {
                        'value': metric['metric_value'],
                        'unit': metric['metric_unit'],
                        'timestamp': metric['timestamp']
                    }
            
            # Получаем дополнительную информацию
            status_query = """
            SELECT 
                current_status,
                COUNT(*) as count
            FROM mcl.migration_status 
            GROUP BY current_status
            """
            
            status_data = self._execute_query(status_query)
            status_breakdown = {status['current_status']: status['count'] for status in status_data}
            
            result = {
                'metrics': metrics,
                'status_breakdown': status_breakdown,
                'timestamp': datetime.now().isoformat()
            }
            
            console.print(f"   📈 Прогресс: {metrics.get('progress_percentage', {}).get('value', 0):.1f}%")
            console.print(f"   🏃 Скорость: {metrics.get('migration_speed', {}).get('value', 0):.1f} таблиц/час")
            console.print(f"   ✅ Завершено: {status_breakdown.get('completed', 0)}")
            console.print(f"   ❌ Ошибок: {status_breakdown.get('failed', 0)}")
            
            logger.info(f"Получены метрики в реальном времени: {result}")
            return result
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка получения метрик: {e}[/red]")
            logger.error(f"Ошибка получения метрик: {e}")
            return {}
    
    def generate_progress_report(self) -> Dict[str, Any]:
        """
        Генерация отчёта о прогрессе миграции
        
        Returns:
            dict: Детальный отчёт о прогрессе
        """
        console.print("[blue]📋 Генерация отчёта о прогрессе[/blue]")
        
        try:
            # Общая статистика
            overall_query = """
            SELECT 
                COUNT(*) as total_tables,
                COUNT(CASE WHEN current_status = 'completed' THEN 1 END) as completed_tables,
                COUNT(CASE WHEN current_status = 'failed' THEN 1 END) as failed_tables,
                COUNT(CASE WHEN current_status = 'in_progress' THEN 1 END) as in_progress_tables,
                COUNT(CASE WHEN current_status = 'pending' THEN 1 END) as pending_tables
            FROM mcl.migration_status
            """
            
            overall_data = self._execute_query(overall_query)
            overall = overall_data[0] if overall_data else {}
            
            # Временные метрики
            time_query = """
            SELECT 
                MIN(start_time) as first_start,
                MAX(end_time) as last_completion,
                AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration_seconds,
                COUNT(CASE WHEN current_status = 'completed' AND DATE(end_time) = CURRENT_DATE THEN 1 END) as completed_today
            FROM mcl.migration_status
            WHERE start_time IS NOT NULL
            """
            
            time_data = self._execute_query(time_query)
            time_metrics = time_data[0] if time_data else {}
            
            # Статистика ошибок
            error_query = """
            SELECT 
                COUNT(*) as total_errors,
                COUNT(CASE WHEN attempt_count > 1 THEN 1 END) as retry_count,
                AVG(attempt_count) as avg_attempts
            FROM mcl.migration_status
            WHERE attempt_count > 0
            """
            
            error_data = self._execute_query(error_query)
            error_metrics = error_data[0] if error_data else {}
            
            # Вычисляем ETA
            total = overall.get('total_tables', 0)
            completed = overall.get('completed_tables', 0)
            remaining = total - completed
            
            eta = None
            if completed > 0 and time_metrics.get('avg_duration_seconds') and time_metrics['avg_duration_seconds'] is not None:
                avg_duration = float(time_metrics['avg_duration_seconds'])
                eta_seconds = remaining * avg_duration
                eta = datetime.now() + timedelta(seconds=eta_seconds)
            
            report = {
                'overall_progress': {
                    'total_tables': total,
                    'completed_tables': completed,
                    'failed_tables': overall.get('failed_tables', 0),
                    'in_progress_tables': overall.get('in_progress_tables', 0),
                    'pending_tables': overall.get('pending_tables', 0),
                    'completion_percentage': (completed / total * 100) if total > 0 else 0
                },
                'time_metrics': {
                    'first_start': time_metrics.get('first_start'),
                    'last_completion': time_metrics.get('last_completion'),
                    'avg_duration_seconds': time_metrics.get('avg_duration_seconds'),
                    'completed_today': time_metrics.get('completed_today', 0)
                },
                'error_metrics': {
                    'total_errors': error_metrics.get('total_errors', 0),
                    'retry_count': error_metrics.get('retry_count', 0),
                    'avg_attempts': error_metrics.get('avg_attempts', 0)
                },
                'estimated_completion': eta.isoformat() if eta else None,
                'generated_at': datetime.now().isoformat()
            }
            
            console.print(f"   📊 Общий прогресс: {report['overall_progress']['completion_percentage']:.1f}%")
            console.print(f"   ⏱️ Среднее время миграции: {time_metrics.get('avg_duration_seconds', 0):.1f} сек")
            console.print(f"   🔄 Среднее количество попыток: {error_metrics.get('avg_attempts', 0):.1f}")
            
            logger.info(f"Сгенерирован отчёт о прогрессе: {report}")
            return report
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка генерации отчёта: {e}[/red]")
            logger.error(f"Ошибка генерации отчёта: {e}")
            return {}
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Генерация отчёта о производительности
        
        Returns:
            dict: Отчёт о производительности
        """
        console.print("[blue]⚡ Генерация отчёта о производительности[/blue]")
        
        try:
            # Метрики производительности за последние 24 часа
            performance_query = """
            SELECT 
                metric_name,
                AVG(metric_value) as avg_value,
                MAX(metric_value) as max_value,
                MIN(metric_value) as min_value,
                COUNT(*) as sample_count
            FROM mcl.migration_metrics 
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
            AND metric_name IN ('migration_speed', 'avg_migration_time', 'progress_percentage')
            GROUP BY metric_name
            """
            
            performance_data = self._execute_query(performance_query)
            performance_metrics = {metric['metric_name']: metric for metric in performance_data}
            
            # Статистика по фазам (упрощённая версия без phase)
            phase_query = """
            SELECT 
                'migration' as phase,
                COUNT(*) as table_count,
                AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration
            FROM mcl.migration_status 
            WHERE end_time IS NOT NULL
            """
            
            phase_data = self._execute_query(phase_query)
            phase_metrics = {phase['phase']: phase for phase in phase_data}
            
            report = {
                'performance_metrics': performance_metrics,
                'phase_metrics': phase_metrics,
                'generated_at': datetime.now().isoformat()
            }
            
            console.print(f"   📈 Средняя скорость: {performance_metrics.get('migration_speed', {}).get('avg_value', 0):.1f} таблиц/час")
            console.print(f"   ⏱️ Среднее время: {performance_metrics.get('avg_migration_time', {}).get('avg_value', 0):.1f} сек")
            
            logger.info(f"Сгенерирован отчёт о производительности: {report}")
            return report
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка генерации отчёта о производительности: {e}[/red]")
            logger.error(f"Ошибка генерации отчёта о производительности: {e}")
            return {}
    
    def generate_error_analysis_report(self) -> Dict[str, Any]:
        """
        Генерация отчёта об анализе ошибок
        
        Returns:
            dict: Отчёт об ошибках
        """
        console.print("[blue]🔍 Генерация отчёта об анализе ошибок[/blue]")
        
        try:
            # Статистика ошибок
            error_stats_query = """
            SELECT 
                current_status,
                COUNT(*) as count,
                AVG(attempt_count) as avg_attempts,
                MAX(attempt_count) as max_attempts
            FROM mcl.migration_status 
            WHERE attempt_count > 0
            GROUP BY current_status
            """
            
            error_stats = self._execute_query(error_stats_query)
            
            # Анализ типов ошибок
            error_types_query = """
            SELECT 
                event_type,
                COUNT(*) as count,
                severity
            FROM mcl.migration_events 
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
            GROUP BY event_type, severity
            ORDER BY count DESC
            """
            
            error_types = self._execute_query(error_types_query)
            
            # Таблицы с наибольшим количеством ошибок
            problematic_tables_query = """
            SELECT 
                table_name,
                attempt_count,
                last_error,
                updated_at
            FROM mcl.migration_status 
            WHERE attempt_count > 2
            ORDER BY attempt_count DESC
            LIMIT 10
            """
            
            problematic_tables = self._execute_query(problematic_tables_query)
            
            report = {
                'error_statistics': error_stats,
                'error_types': error_types,
                'problematic_tables': problematic_tables,
                'generated_at': datetime.now().isoformat()
            }
            
            console.print(f"   📊 Типов ошибок: {len(error_types)}")
            console.print(f"   🔥 Проблемных таблиц: {len(problematic_tables)}")
            
            logger.info(f"Сгенерирован отчёт об анализе ошибок: {report}")
            return report
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка генерации отчёта об ошибках: {e}[/red]")
            logger.error(f"Ошибка генерации отчёта об ошибках: {e}")
            return {}
    
    def create_dashboard(self) -> str:
        """
        Создание интерактивного дашборда
        
        Returns:
            str: HTML дашборд
        """
        console.print("[blue]📊 Создание дашборда[/blue]")
        
        try:
            # Получаем данные для дашборда
            metrics = self.get_real_time_metrics()
            progress_report = self.generate_progress_report()
            
            # Создаём HTML дашборд
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Migration Dashboard</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 1200px; margin: 0 auto; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                    .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }}
                    .metric-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .metric-value {{ font-size: 2em; font-weight: bold; color: #333; }}
                    .metric-label {{ color: #666; margin-top: 5px; }}
                    .chart-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
                    .status-table {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #f8f9fa; }}
                    .status-completed {{ color: #28a745; }}
                    .status-failed {{ color: #dc3545; }}
                    .status-in-progress {{ color: #ffc107; }}
                    .status-pending {{ color: #6c757d; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚀 Migration Dashboard</h1>
                        <p>Real-time monitoring of database migration progress</p>
                        <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">{metrics.get('metrics', {}).get('progress_percentage', {}).get('value', 0):.1f}%</div>
                            <div class="metric-label">Overall Progress</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{metrics.get('metrics', {}).get('migration_speed', {}).get('value', 0):.1f}</div>
                            <div class="metric-label">Tables/Hour</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{progress_report.get('overall_progress', {}).get('completed_tables', 0)}</div>
                            <div class="metric-label">Completed Tables</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{progress_report.get('overall_progress', {}).get('failed_tables', 0)}</div>
                            <div class="metric-label">Failed Tables</div>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Migration Progress</h3>
                        <canvas id="progressChart" width="400" height="200"></canvas>
                    </div>
                    
                    <div class="status-table">
                        <h3>Table Status Breakdown</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Status</th>
                                    <th>Count</th>
                                    <th>Percentage</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            # Добавляем строки таблицы статусов
            status_breakdown = metrics.get('status_breakdown', {})
            total_tables = sum(status_breakdown.values())
            
            for status, count in status_breakdown.items():
                percentage = (count / total_tables * 100) if total_tables > 0 else 0
                status_class = f"status-{status.replace('_', '-')}"
                html_content += f"""
                                <tr>
                                    <td class="{status_class}">{status.title()}</td>
                                    <td>{count}</td>
                                    <td>{percentage:.1f}%</td>
                                </tr>
                """
            
            html_content += """
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <script>
                    // Создаём график прогресса
                    const ctx = document.getElementById('progressChart').getContext('2d');
                    const progressChart = new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: ['Completed', 'Failed', 'In Progress', 'Pending'],
                            datasets: [{
                                data: [
                                    """ + f"{status_breakdown.get('completed', 0)}, {status_breakdown.get('failed', 0)}, {status_breakdown.get('in_progress', 0)}, {status_breakdown.get('pending', 0)}" + """,
                                backgroundColor: [
                                    '#28a745',
                                    '#dc3545', 
                                    '#ffc107',
                                    '#6c757d'
                                ]
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: {
                                    position: 'bottom'
                                }
                            }
                        }
                    });
                    
                    // Автообновление каждые 30 секунд
                    setInterval(() => {
                        location.reload();
                    }, 30000);
                </script>
            </body>
            </html>
            """
            
            console.print("   📊 HTML дашборд создан")
            logger.info("Создан HTML дашборд")
            return html_content
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка создания дашборда: {e}[/red]")
            logger.error(f"Ошибка создания дашборда: {e}")
            return ""
    
    def send_notification(self, event_type: str, message: str, severity: str) -> bool:
        """
        Отправка уведомления
        
        Args:
            event_type (str): Тип события
            message (str): Текст сообщения
            severity (str): Уровень критичности
        
        Returns:
            bool: True если уведомление отправлено
        """
        console.print(f"[blue]📧 Отправка уведомления: {event_type}[/blue]")
        
        try:
            # Сохраняем уведомление в базу
            insert_query = """
            INSERT INTO mcl.migration_notifications (notification_type, title, message, severity)
            VALUES (%s, %s, %s, %s)
            """
            
            title = f"Migration {event_type}"
            self._execute_query(insert_query, (event_type, title, message, severity))
            
            # Логируем событие
            self._log_event(event_type, message, severity)
            
            console.print(f"   ✅ Уведомление сохранено: {title}")
            logger.info(f"Уведомление отправлено: {event_type} - {message}")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Ошибка отправки уведомления: {e}[/red]")
            logger.error(f"Ошибка отправки уведомления: {e}")
            return False
    
    def _send_notification_internal(self, notification: Dict) -> bool:
        """Внутренняя отправка уведомления"""
        try:
            # Здесь можно добавить реальную отправку email/SMS/Slack
            # Пока просто логируем
            logger.info(f"Отправка уведомления: {notification['title']} - {notification['message']}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
            return False
    
    def export_report(self, format_type: str, report_data: Dict) -> str:
        """
        Экспорт отчёта в различных форматах
        
        Args:
            format_type (str): Формат экспорта (PDF, Excel, CSV)
            report_data (dict): Данные отчёта
        
        Returns:
            str: Путь к экспортированному файлу
        """
        console.print(f"[blue]📤 Экспорт отчёта в формате {format_type}[/blue]")
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if format_type.upper() == 'CSV':
                # Экспорт в CSV
                import csv
                filename = f"/home/alex/projects/sql/femcl/reports/migration_report_{timestamp}.csv"
                
                # Создаём папку если не существует
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Metric', 'Value', 'Unit', 'Timestamp'])
                    
                    for metric_name, metric_data in report_data.get('metrics', {}).items():
                        writer.writerow([
                            metric_name,
                            metric_data.get('value', ''),
                            metric_data.get('unit', ''),
                            metric_data.get('timestamp', '')
                        ])
                
                console.print(f"   ✅ CSV отчёт сохранён: {filename}")
                return filename
                
            elif format_type.upper() == 'JSON':
                # Экспорт в JSON
                filename = f"/home/alex/projects/sql/femcl/reports/migration_report_{timestamp}.json"
                
                # Создаём папку если не существует
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                with open(filename, 'w', encoding='utf-8') as jsonfile:
                    json.dump(report_data, jsonfile, indent=2, ensure_ascii=False, default=str)
                
                console.print(f"   ✅ JSON отчёт сохранён: {filename}")
                return filename
                
            else:
                console.print(f"[yellow]⚠️ Формат {format_type} не поддерживается[/yellow]")
                return ""
                
        except Exception as e:
            console.print(f"[red]❌ Ошибка экспорта отчёта: {e}[/red]")
            logger.error(f"Ошибка экспорта отчёта: {e}")
            return ""
    
    def display_live_dashboard(self):
        """Отображение живого дашборда в консоли"""
        console.print("[blue]📊 Запуск живого дашборда[/blue]")
        
        try:
            with Live(console=console, refresh_per_second=2) as live:
                while True:
                    # Получаем метрики
                    metrics = self.get_real_time_metrics()
                    
                    # Создаём layout
                    layout = Layout()
                    layout.split_column(
                        Layout(Panel("🚀 Migration Dashboard", style="bold blue"), size=3),
                        Layout(name="main"),
                        Layout(Panel("Press Ctrl+C to exit", style="dim"), size=1)
                    )
                    
                    layout["main"].split_row(
                        Layout(name="left"),
                        Layout(name="right")
                    )
                    
                    # Левая панель - метрики
                    metrics_table = Table(title="Real-time Metrics")
                    metrics_table.add_column("Metric", style="cyan")
                    metrics_table.add_column("Value", style="green")
                    metrics_table.add_column("Unit", style="yellow")
                    
                    for metric_name, metric_data in metrics.get('metrics', {}).items():
                        metrics_table.add_row(
                            metric_name.replace('_', ' ').title(),
                            f"{metric_data.get('value', 0):.2f}",
                            metric_data.get('unit', '')
                        )
                    
                    layout["left"].update(metrics_table)
                    
                    # Правая панель - статусы
                    status_table = Table(title="Table Status")
                    status_table.add_column("Status", style="cyan")
                    status_table.add_column("Count", style="green")
                    status_table.add_column("Percentage", style="yellow")
                    
                    status_breakdown = metrics.get('status_breakdown', {})
                    total = sum(status_breakdown.values())
                    
                    for status, count in status_breakdown.items():
                        percentage = (count / total * 100) if total > 0 else 0
                        status_table.add_row(
                            status.title(),
                            str(count),
                            f"{percentage:.1f}%"
                        )
                    
                    layout["right"].update(status_table)
                    
                    live.update(layout)
                    time.sleep(2)
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]🛑 Дашборд остановлен[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Ошибка дашборда: {e}[/red]")
            logger.error(f"Ошибка дашборда: {e}")
    
    def close(self):
        """Закрытие монитора"""
        self.stop_monitoring()
        if self.connection and not self.connection.closed:
            self.connection.close()

# Примеры использования
if __name__ == "__main__":
    # Инициализация ConnectionManager (task_id=2 по умолчанию)
    manager = ConnectionManager()
    
    info = manager.get_connection_info()
    console.print(f"[green]✅ Профиль: {info['profile_name']} (task_id={info['task_id']})[/green]\n")
    
    # Создаём монитор
    monitor = MigrationMonitor(manager)
    
    try:
        # Запуск мониторинга
        monitor.start_monitoring()
        
        # Получение метрик
        metrics = monitor.get_real_time_metrics()
        console.print(f"Метрики: {metrics}")
        
        # Генерация отчёта
        report = monitor.generate_progress_report()
        console.print(f"Отчёт: {report}")
        
        # Создание дашборда
        dashboard = monitor.create_dashboard()
        with open('/home/alex/projects/sql/femcl/reports/dashboard.html', 'w') as f:
            f.write(dashboard)
        
        # Отправка уведомления
        monitor.send_notification('TEST', 'Test notification', 'INFO')
        
    finally:
        monitor.close()