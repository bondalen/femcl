"""
MigrationMetrics класс для динамического расчета метрик миграции.

Этот класс предоставляет методы для получения актуальных метрик миграции
на основе конкретной задачи миграции (task_id).
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MigrationMetrics:
    """
    Класс для расчета и получения метрик миграции.
    
    Предоставляет динамические метрики на основе task_id вместо
    статических значений в документации.
    """
    
    def __init__(self, connection_manager):
        """
        Инициализация MigrationMetrics.
        
        Args:
            connection_manager: Экземпляр ConnectionManager для работы с БД
        """
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(__name__)
    
    def get_migration_metrics(self, task_id: int) -> Dict[str, Any]:
        """
        Получить полные метрики миграции для конкретной задачи.
        
        Args:
            task_id: ID задачи миграции
            
        Returns:
            Словарь с метриками миграции
        """
        try:
            with self.connection_manager.get_postgres_connection() as conn:
                with conn.cursor() as cursor:
                    # Получаем общее количество таблиц для задачи
                    total_tables = self._get_total_tables_for_task(cursor, task_id)
                    
                    # Получаем статусы таблиц
                    status_counts = self._get_status_counts(cursor, task_id)
                    
                    # Рассчитываем процент завершения
                    completion_rate = self._calculate_completion_rate(
                        status_counts.get('completed', 0), 
                        total_tables
                    )
                    
                    return {
                        'task_id': task_id,
                        'total_tables': total_tables,
                        'completed_tables': status_counts.get('completed', 0),
                        'in_progress_tables': status_counts.get('in_progress', 0),
                        'pending_tables': status_counts.get('pending', 0),
                        'failed_tables': status_counts.get('failed', 0),
                        'completion_rate': f"{completion_rate:.1f}%",
                        'last_update': datetime.now().isoformat(),
                        'data_source': 'mcl.migration_status'
                    }
                    
        except Exception as e:
            self.logger.error(f"Ошибка получения метрик для задачи {task_id}: {e}")
            return self._get_error_metrics(task_id, str(e))
    
    def get_table_metrics(self, task_id: int) -> Dict[str, Any]:
        """
        Получить метрики таблиц для конкретной задачи.
        
        Args:
            task_id: ID задачи миграции
            
        Returns:
            Словарь с метриками таблиц
        """
        try:
            with self.connection_manager.get_postgres_connection() as conn:
                with conn.cursor() as cursor:
                    # Получаем недавно завершенные таблицы
                    recently_completed = self._get_recently_completed_tables(cursor, task_id)
                    
                    # Получаем статистику по времени выполнения
                    performance_stats = self._get_performance_stats(cursor, task_id)
                    
                    return {
                        'task_id': task_id,
                        'recently_completed': recently_completed,
                        'performance': performance_stats,
                        'last_update': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            self.logger.error(f"Ошибка получения метрик таблиц для задачи {task_id}: {e}")
            return {'error': str(e), 'task_id': task_id}
    
    def get_completion_rate(self, task_id: int) -> float:
        """
        Получить процент завершения миграции.
        
        Args:
            task_id: ID задачи миграции
            
        Returns:
            Процент завершения (0.0 - 100.0)
        """
        try:
            with self.connection_manager.get_postgres_connection() as conn:
                with conn.cursor() as cursor:
                    total_tables = self._get_total_tables_for_task(cursor, task_id)
                    completed_tables = self._get_status_counts(cursor, task_id).get('completed', 0)
                    
                    return self._calculate_completion_rate(completed_tables, total_tables)
                    
        except Exception as e:
            self.logger.error(f"Ошибка расчета процента завершения для задачи {task_id}: {e}")
            return 0.0
    
    def _get_total_tables_for_task(self, cursor, task_id: int) -> int:
        """Получить общее количество таблиц для задачи."""
        cursor.execute("""
            SELECT COUNT(*) 
            FROM mcl.migration_status 
            WHERE table_name IN (
                SELECT table_name 
                FROM mcl.migration_tasks 
                WHERE task_id = %s
            )
        """, (task_id,))
        
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def _get_status_counts(self, cursor, task_id: int) -> Dict[str, int]:
        """Получить количество таблиц по статусам."""
        cursor.execute("""
            SELECT 
                current_status,
                COUNT(*) as count
            FROM mcl.migration_status ms
            JOIN mcl.migration_tasks mt ON ms.table_name = mt.table_name
            WHERE mt.task_id = %s
            GROUP BY current_status
        """, (task_id,))
        
        results = cursor.fetchall()
        status_counts = {}
        
        for status, count in results:
            status_counts[status] = count
            
        return status_counts
    
    def _get_recently_completed_tables(self, cursor, task_id: int, limit: int = 5) -> List[Dict]:
        """Получить недавно завершенные таблицы."""
        cursor.execute("""
            SELECT 
                ms.table_name,
                ms.end_time,
                ms.current_status
            FROM mcl.migration_status ms
            JOIN mcl.migration_tasks mt ON ms.table_name = mt.table_name
            WHERE mt.task_id = %s 
            AND ms.current_status = 'completed'
            AND ms.end_time IS NOT NULL
            ORDER BY ms.end_time DESC
            LIMIT %s
        """, (task_id, limit))
        
        results = cursor.fetchall()
        return [
            {
                'name': row[0],
                'completion_date': row[1].isoformat() if row[1] else None,
                'status': row[2]
            }
            for row in results
        ]
    
    def _get_performance_stats(self, cursor, task_id: int) -> Dict[str, Any]:
        """Получить статистику производительности."""
        cursor.execute("""
            SELECT 
                AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration_seconds,
                COUNT(*) as total_completed,
                MIN(start_time) as first_start,
                MAX(end_time) as last_end
            FROM mcl.migration_status ms
            JOIN mcl.migration_tasks mt ON ms.table_name = mt.table_name
            WHERE mt.task_id = %s 
            AND ms.current_status = 'completed'
            AND ms.start_time IS NOT NULL 
            AND ms.end_time IS NOT NULL
        """, (task_id,))
        
        result = cursor.fetchone()
        if result and result[0]:
            avg_duration = result[0]
            return {
                'average_table_time_minutes': round(avg_duration / 60, 1),
                'total_completed': result[1],
                'first_start': result[2].isoformat() if result[2] else None,
                'last_end': result[3].isoformat() if result[3] else None
            }
        else:
            return {
                'average_table_time_minutes': 0,
                'total_completed': 0,
                'first_start': None,
                'last_end': None
            }
    
    def _calculate_completion_rate(self, completed: int, total: int) -> float:
        """Рассчитать процент завершения."""
        if total == 0:
            return 0.0
        return (completed / total) * 100.0
    
    def _get_error_metrics(self, task_id: int, error_message: str) -> Dict[str, Any]:
        """Получить метрики ошибки."""
        return {
            'task_id': task_id,
            'error': error_message,
            'total_tables': 0,
            'completed_tables': 0,
            'in_progress_tables': 0,
            'pending_tables': 0,
            'failed_tables': 0,
            'completion_rate': '0.0%',
            'last_update': datetime.now().isoformat(),
            'data_source': 'error'
        }