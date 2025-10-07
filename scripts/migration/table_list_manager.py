#!/usr/bin/env python3
"""
Модуль управления списком таблиц для миграции

ОБНОВЛЕНО: Использует ConnectionManager
"""
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID

# Добавляем путь к модулям проекта
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "code"))

from infrastructure.classes import ConnectionManager

console = Console()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/alex/projects/sql/femcl/logs/migration_status.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TableListManager:
    """
    Класс для управления списком таблиц миграции.
    
    ОБНОВЛЕНО: Использует ConnectionManager для подключений к БД.
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        """
        Инициализация менеджера.
        
        Args:
            connection_manager: Экземпляр ConnectionManager
        """
        self.conn_mgr = connection_manager
        self.task_id = connection_manager.task_id
        self._ensure_migration_table()
    
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
    
    def _ensure_migration_table(self):
        """Создание таблицы статуса миграции если не существует"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS mcl.migration_status (
            id SERIAL PRIMARY KEY,
            table_name VARCHAR(255) NOT NULL UNIQUE,
            current_status VARCHAR(50) NOT NULL DEFAULT 'pending',
            previous_status VARCHAR(50),
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            attempt_count INTEGER DEFAULT 0,
            last_error TEXT,
            error_details JSONB,
            metrics JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_indexes_query = """
        CREATE INDEX IF NOT EXISTS idx_migration_status_table_name 
        ON mcl.migration_status(table_name);
        
        CREATE INDEX IF NOT EXISTS idx_migration_status_current_status 
        ON mcl.migration_status(current_status);
        
        CREATE INDEX IF NOT EXISTS idx_migration_status_updated_at 
        ON mcl.migration_status(updated_at);
        """
        
        try:
            self._execute_query(create_table_query)
            self._execute_query(create_indexes_query)
            logger.info("Таблица migration_status создана или уже существует")
        except Exception as e:
            logger.error(f"Ошибка создания таблицы migration_status: {e}")
            raise
    
    def initialize_table_list(self) -> Dict[str, Any]:
        """
        Инициализация списка таблиц для миграции
        
        Returns:
            dict: Словарь с информацией о таблицах и их статусах
        """
        console.print("[blue]🚀 Инициализация списка таблиц для миграции[/blue]")
        
        # Получаем список всех таблиц из метаданных
        query = """
        SELECT DISTINCT mt.object_name as table_name
        FROM mcl.mssql_tables mt
        JOIN mcl.postgres_tables pt ON mt.id = pt.source_table_id
        ORDER BY mt.object_name
        """
        
        tables = self._execute_query(query)
        table_names = [table['table_name'] for table in tables]
        
        console.print(f"📊 Найдено {len(table_names)} таблиц для миграции")
        
        # Инициализируем статусы для всех таблиц
        initialized_count = 0
        for table_name in table_names:
            # Проверяем, существует ли уже запись
            check_query = "SELECT id FROM mcl.migration_status WHERE table_name = %s"
            existing = self._execute_query(check_query, (table_name,))
            
            if not existing:
                # Создаём новую запись
                insert_query = """
                INSERT INTO mcl.migration_status (table_name, current_status, start_time)
                VALUES (%s, %s, %s)
                """
                self._execute_query(insert_query, (table_name, 'pending', datetime.now()))
                initialized_count += 1
        
        result = {
            'total_tables': len(table_names),
            'initialized': initialized_count,
            'already_exists': len(table_names) - initialized_count,
            'tables': table_names
        }
        
        console.print(f"✅ Инициализировано {initialized_count} новых таблиц")
        console.print(f"ℹ️ {len(table_names) - initialized_count} таблиц уже существовали")
        
        logger.info(f"Инициализация списка таблиц завершена: {result}")
        return result
    
    def get_incomplete_tables(self) -> List[str]:
        """
        Получение списка незавершённых таблиц
        
        Returns:
            list: Список таблиц, которые ещё не завершены
        """
        query = """
        SELECT table_name 
        FROM mcl.migration_status 
        WHERE current_status NOT IN ('completed', 'blocked')
        ORDER BY table_name
        """
        
        tables = self._execute_query(query)
        incomplete_tables = [table['table_name'] for table in tables]
        
        logger.info(f"Найдено {len(incomplete_tables)} незавершённых таблиц")
        return incomplete_tables
    
    def update_table_status(self, table_name: str, status: str, details: Optional[Dict] = None) -> bool:
        """
        Обновление статуса таблицы
        
        Args:
            table_name (str): Имя таблицы
            status (str): Новый статус
            details (dict): Дополнительные детали
        
        Returns:
            bool: True если обновление успешно
        """
        try:
            # Получаем текущий статус
            current_query = "SELECT current_status FROM mcl.migration_status WHERE table_name = %s"
            current_result = self._execute_query(current_query, (table_name,))
            
            if not current_result:
                logger.warning(f"Таблица {table_name} не найдена в списке миграции")
                return False
            
            previous_status = current_result[0]['current_status']
            
            # Обновляем статус
            update_query = """
            UPDATE mcl.migration_status 
            SET current_status = %s, 
                previous_status = %s, 
                updated_at = CURRENT_TIMESTAMP,
                error_details = %s
            WHERE table_name = %s
            """
            
            error_details = json.dumps(details) if details else None
            self._execute_query(update_query, (status, previous_status, error_details, table_name))
            
            logger.info(f"Статус таблицы {table_name} изменён: {previous_status} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления статуса таблицы {table_name}: {e}")
            return False
    
    def mark_table_completed(self, table_name: str, metrics: Optional[Dict] = None) -> bool:
        """
        Отметка таблицы как завершённой
        
        Args:
            table_name (str): Имя таблицы
            metrics (dict): Метрики миграции
        
        Returns:
            bool: True если операция успешна
        """
        try:
            update_query = """
            UPDATE mcl.migration_status 
            SET current_status = 'completed',
                end_time = CURRENT_TIMESTAMP,
                metrics = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE table_name = %s
            """
            
            metrics_json = json.dumps(metrics) if metrics else None
            self._execute_query(update_query, (metrics_json, table_name))
            
            console.print(f"[green]✅ Таблица {table_name} отмечена как завершённая[/green]")
            logger.info(f"Таблица {table_name} успешно завершена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отметки таблицы {table_name} как завершённой: {e}")
            return False
    
    def get_migration_progress(self) -> Dict[str, Any]:
        """
        Получение информации о прогрессе миграции
        
        Returns:
            dict: Статистика прогресса миграции
        """
        query = """
        SELECT 
            current_status,
            COUNT(*) as count
        FROM mcl.migration_status 
        GROUP BY current_status
        ORDER BY current_status
        """
        
        status_counts = self._execute_query(query)
        
        # Подсчитываем общую статистику
        total = sum(status['count'] for status in status_counts)
        completed = sum(status['count'] for status in status_counts 
                       if status['current_status'] == 'completed')
        
        progress = {
            'total': total,
            'completed': completed,
            'percentage': (completed / total * 100) if total > 0 else 0,
            'status_breakdown': {status['current_status']: status['count'] 
                               for status in status_counts}
        }
        
        return progress
    
    def get_table_status(self, table_name: str) -> Optional[str]:
        """
        Получение текущего статуса таблицы
        
        Args:
            table_name (str): Имя таблицы
        
        Returns:
            str: Текущий статус таблицы или None если не найдена
        """
        query = "SELECT current_status FROM mcl.migration_status WHERE table_name = %s"
        result = self._execute_query(query, (table_name,))
        
        return result[0]['current_status'] if result else None
    
    def get_failed_tables(self) -> List[str]:
        """
        Получение списка таблиц с ошибками
        
        Returns:
            list: Список таблиц со статусом 'failed'
        """
        query = "SELECT table_name FROM mcl.migration_status WHERE current_status = 'failed'"
        tables = self._execute_query(query)
        return [table['table_name'] for table in tables]
    
    def get_blocked_tables(self) -> List[str]:
        """
        Получение списка заблокированных таблиц
        
        Returns:
            list: Список таблиц со статусом 'blocked'
        """
        query = "SELECT table_name FROM mcl.migration_status WHERE current_status = 'blocked'"
        tables = self._execute_query(query)
        return [table['table_name'] for table in tables]
    
    def retry_failed_table(self, table_name: str) -> bool:
        """
        Повторная попытка миграции таблицы
        
        Args:
            table_name (str): Имя таблицы
        
        Returns:
            bool: True если попытка инициирована
        """
        try:
            update_query = """
            UPDATE mcl.migration_status 
            SET current_status = 'pending',
                attempt_count = attempt_count + 1,
                last_error = NULL,
                error_details = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE table_name = %s AND current_status = 'failed'
            """
            
            result = self._execute_query(update_query, (table_name,))
            
            if result:
                console.print(f"[yellow]🔄 Повторная попытка для таблицы {table_name} инициирована[/yellow]")
                logger.info(f"Повторная попытка для таблицы {table_name} инициирована")
                return True
            else:
                logger.warning(f"Таблица {table_name} не найдена или не в статусе 'failed'")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка инициации повторной попытки для {table_name}: {e}")
            return False
    
    def get_migration_statistics(self) -> Dict[str, Any]:
        """
        Получение детальной статистики миграции
        
        Returns:
            dict: Подробная статистика по всем таблицам
        """
        # Общая статистика
        progress = self.get_migration_progress()
        
        # Статистика по времени
        time_query = """
        SELECT 
            COUNT(*) as total_tables,
            COUNT(CASE WHEN end_time IS NOT NULL THEN 1 END) as completed_tables,
            AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration_seconds,
            MIN(start_time) as first_start,
            MAX(end_time) as last_completion
        FROM mcl.migration_status
        """
        
        time_stats = self._execute_query(time_query)
        
        # Статистика ошибок
        error_query = """
        SELECT 
            COUNT(*) as total_errors,
            COUNT(CASE WHEN current_status = 'failed' THEN 1 END) as current_failures,
            AVG(attempt_count) as avg_attempts
        FROM mcl.migration_status
        WHERE attempt_count > 0 OR current_status = 'failed'
        """
        
        error_stats = self._execute_query(error_query)
        
        statistics = {
            'progress': progress,
            'time_statistics': time_stats[0] if time_stats else {},
            'error_statistics': error_stats[0] if error_stats else {}
        }
        
        return statistics
    
    def display_progress_table(self):
        """Отображение таблицы прогресса миграции"""
        progress = self.get_migration_progress()
        
        table = Table(title="Прогресс миграции таблиц")
        table.add_column("Статус", style="cyan")
        table.add_column("Количество", style="magenta")
        table.add_column("Процент", style="green")
        
        total = progress['total']
        for status, count in progress['status_breakdown'].items():
            percentage = (count / total * 100) if total > 0 else 0
            table.add_row(status, str(count), f"{percentage:.1f}%")
        
        table.add_row("ИТОГО", str(total), "100.0%", style="bold")
        
        console.print(table)
        console.print(f"\n[bold green]Общий прогресс: {progress['percentage']:.1f}% ({progress['completed']}/{progress['total']})[/bold green]")
    
    def close(self):
        """Закрытие подключения"""
        if self.connection and not self.connection.closed:
            self.connection.close()

# Примеры использования
if __name__ == "__main__":
    # Инициализация ConnectionManager (task_id=2 по умолчанию)
    conn_manager = ConnectionManager()
    
    info = conn_manager.get_connection_info()
    console.print(f"[green]✅ Профиль: {info['profile_name']} (task_id={info['task_id']})[/green]\n")
    
    # Создаём менеджер
    manager = TableListManager(conn_manager)
    
    try:
        # Инициализация списка таблиц
        result = manager.initialize_table_list()
        console.print(f"Инициализировано {result['initialized']} новых таблиц")
        
        # Отображение прогресса
        manager.display_progress_table()
        
        # Получение незавершённых таблиц
        incomplete = manager.get_incomplete_tables()
        console.print(f"\nНезавершённых таблиц: {len(incomplete)}")
        
        # Статистика
        stats = manager.get_migration_statistics()
        console.print(f"\nСтатистика миграции:")
        console.print(f"Среднее время миграции: {stats['time_statistics'].get('avg_duration_seconds', 0):.1f} сек")
        console.print(f"Среднее количество попыток: {stats['error_statistics'].get('avg_attempts', 0):.1f}")
        
    finally:
        manager.close()