"""
ConnectionDiagnostics - Диагностика подключений и состояния БД

Класс для проверки здоровья баз данных, валидации схем и генерации отчетов.
Использует ConnectionManager для получения подключений.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import psycopg2
import pyodbc

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .connection_manager import ConnectionManager


logger = logging.getLogger(__name__)


class ConnectionDiagnostics:
    """
    Диагностика подключений и состояния баз данных.
    
    Предоставляет методы для:
    - Проверки здоровья БД
    - Получения информации о версиях
    - Проверки существования схем
    - Валидации метаданных миграции
    - Генерации диагностических отчетов
    
    Attributes:
        conn_mgr: Менеджер подключений
        console: Rich console для красивого вывода (если доступен)
    
    Example:
        >>> manager = ConnectionManager()
        >>> diagnostics = ConnectionDiagnostics(manager)
        >>> health = diagnostics.check_postgres_health()
        >>> if health['status'] == 'healthy':
        >>>     print("PostgreSQL в порядке!")
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        """
        Инициализация ConnectionDiagnostics.
        
        Args:
            connection_manager: Экземпляр ConnectionManager
        """
        self.conn_mgr = connection_manager
        self.logger = logging.getLogger(__name__)
        self.console = Console() if RICH_AVAILABLE else None
        
        self.logger.info("ConnectionDiagnostics инициализирован")
    
    def test_postgres_connection(self) -> Dict[str, Any]:
        """
        Тестирование подключения к PostgreSQL.
        
        Returns:
            Dict: Результат теста с полями status, message, error
        
        Example:
            >>> result = diagnostics.test_postgres_connection()
            >>> if result['status'] == 'success':
            >>>     print("Подключение работает!")
        """
        try:
            conn = self.conn_mgr.get_postgres_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            
            return {
                'status': 'success',
                'message': 'Подключение к PostgreSQL успешно',
                'timestamp': datetime.now().isoformat()
            }
        except psycopg2.Error as e:
            self.logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            return {
                'status': 'error',
                'message': 'Ошибка подключения к PostgreSQL',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при тестировании PostgreSQL: {e}")
            return {
                'status': 'error',
                'message': 'Неожиданная ошибка',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_mssql_connection(self) -> Dict[str, Any]:
        """
        Тестирование подключения к MS SQL Server.
        
        Returns:
            Dict: Результат теста с полями status, message, error
        """
        try:
            conn = self.conn_mgr.get_mssql_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            
            return {
                'status': 'success',
                'message': 'Подключение к MS SQL Server успешно',
                'timestamp': datetime.now().isoformat()
            }
        except pyodbc.Error as e:
            self.logger.error(f"Ошибка подключения к MS SQL Server: {e}")
            return {
                'status': 'error',
                'message': 'Ошибка подключения к MS SQL Server',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при тестировании MS SQL Server: {e}")
            return {
                'status': 'error',
                'message': 'Неожиданная ошибка',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_all_connections(self) -> Dict[str, Any]:
        """
        Тестирование всех подключений.
        
        Returns:
            Dict: Результаты тестов для обеих БД
        
        Example:
            >>> results = diagnostics.test_all_connections()
            >>> all_ok = (results['postgres']['status'] == 'success' and 
            >>>           results['mssql']['status'] == 'success')
        """
        return {
            'postgres': self.test_postgres_connection(),
            'mssql': self.test_mssql_connection(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_postgres_version(self) -> Optional[str]:
        """
        Получение версии PostgreSQL.
        
        Returns:
            str: Строка с версией PostgreSQL или None при ошибке
        """
        try:
            conn = self.conn_mgr.get_postgres_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            cursor.close()
            return version
        except Exception as e:
            self.logger.error(f"Ошибка получения версии PostgreSQL: {e}")
            return None
    
    def get_mssql_version(self) -> Optional[str]:
        """
        Получение версии MS SQL Server.
        
        Returns:
            str: Строка с версией MS SQL Server или None при ошибке
        """
        try:
            conn = self.conn_mgr.get_mssql_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            cursor.close()
            return version
        except Exception as e:
            self.logger.error(f"Ошибка получения версии MS SQL Server: {e}")
            return None
    
    def get_postgres_database_info(self) -> Dict[str, Any]:
        """
        Получение детальной информации о PostgreSQL БД.
        
        Returns:
            Dict: Информация о БД (имя, размер, кодировка и т.д.)
        """
        try:
            conn = self.conn_mgr.get_postgres_connection()
            cursor = conn.cursor()
            
            # Текущая БД
            cursor.execute("SELECT current_database()")
            current_db = cursor.fetchone()[0]
            
            # Размер БД
            cursor.execute(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            )
            db_size = cursor.fetchone()[0]
            
            # Количество подключений
            cursor.execute(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
            )
            connections_count = cursor.fetchone()[0]
            
            cursor.close()
            
            return {
                'database': current_db,
                'size': db_size,
                'connections': connections_count,
                'version': self.get_postgres_version(),
                'status': 'success'
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о PostgreSQL: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_mssql_database_info(self) -> Dict[str, Any]:
        """
        Получение детальной информации о MS SQL Server БД.
        
        Returns:
            Dict: Информация о БД
        """
        try:
            conn = self.conn_mgr.get_mssql_connection()
            cursor = conn.cursor()
            
            # Текущая БД
            cursor.execute("SELECT DB_NAME()")
            current_db = cursor.fetchone()[0]
            
            # Количество подключений
            cursor.execute(
                "SELECT COUNT(*) FROM sys.dm_exec_sessions WHERE database_id = DB_ID()"
            )
            connections_count = cursor.fetchone()[0]
            
            cursor.close()
            
            return {
                'database': current_db,
                'connections': connections_count,
                'version': self.get_mssql_version(),
                'status': 'success'
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о MS SQL Server: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_schema_exists(self, schema_name: str, db_type: str) -> bool:
        """
        Проверка существования схемы в БД.
        
        Args:
            schema_name: Имя схемы (например, 'mcl')
            db_type: Тип БД ('postgres' или 'mssql')
        
        Returns:
            bool: True если схема существует
        
        Example:
            >>> if diagnostics.check_schema_exists('mcl', 'postgres'):
            >>>     print("Схема mcl существует")
        """
        try:
            if db_type.lower() in ('postgres', 'postgresql'):
                conn = self.conn_mgr.get_postgres_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                    (schema_name,)
                )
                result = cursor.fetchone()
                cursor.close()
                return result is not None
                
            elif db_type.lower() in ('mssql', 'sqlserver'):
                conn = self.conn_mgr.get_mssql_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = ?",
                    (schema_name,)
                )
                result = cursor.fetchone()
                cursor.close()
                return result is not None
            else:
                raise ValueError(f"Неизвестный тип БД: {db_type}")
                
        except Exception as e:
            self.logger.error(f"Ошибка проверки схемы {schema_name}: {e}")
            return False
    
    def get_schema_tables_count(self, schema_name: str, db_type: str) -> int:
        """
        Получение количества таблиц в схеме.
        
        Args:
            schema_name: Имя схемы
            db_type: Тип БД ('postgres' или 'mssql')
        
        Returns:
            int: Количество таблиц или -1 при ошибке
        """
        try:
            if db_type.lower() in ('postgres', 'postgresql'):
                conn = self.conn_mgr.get_postgres_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s",
                    (schema_name,)
                )
                count = cursor.fetchone()[0]
                cursor.close()
                return count
                
            elif db_type.lower() in ('mssql', 'sqlserver'):
                conn = self.conn_mgr.get_mssql_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = ?",
                    (schema_name,)
                )
                count = cursor.fetchone()[0]
                cursor.close()
                return count
            else:
                raise ValueError(f"Неизвестный тип БД: {db_type}")
                
        except Exception as e:
            self.logger.error(f"Ошибка получения количества таблиц в схеме {schema_name}: {e}")
            return -1
    
    def get_schema_info(self, schema_name: str, db_type: str) -> Dict[str, Any]:
        """
        Получение информации о схеме.
        
        Args:
            schema_name: Имя схемы
            db_type: Тип БД
        
        Returns:
            Dict: Информация о схеме
        """
        exists = self.check_schema_exists(schema_name, db_type)
        
        if not exists:
            return {
                'schema': schema_name,
                'exists': False,
                'db_type': db_type
            }
        
        tables_count = self.get_schema_tables_count(schema_name, db_type)
        
        return {
            'schema': schema_name,
            'exists': True,
            'tables_count': tables_count,
            'db_type': db_type
        }
    
    def check_mcl_schema_postgres(self) -> Dict[str, Any]:
        """
        Проверка схемы mcl в PostgreSQL.
        
        Returns:
            Dict: Детальная информация о схеме mcl
        """
        return self.get_schema_info('mcl', 'postgres')
    
    def check_mcl_tables(self) -> Dict[str, Any]:
        """
        Проверка основных таблиц метаданных в схеме mcl.
        
        Returns:
            Dict: Информация о ключевых таблицах
        """
        try:
            conn = self.conn_mgr.get_postgres_connection()
            cursor = conn.cursor()
            
            # Проверяем ключевые таблицы
            key_tables = [
                'migration_tasks',
                'mssql_tables',
                'postgres_tables',
                'mssql_columns',
                'postgres_columns',
                'function_mapping_rules'
            ]
            
            tables_info = {}
            for table in key_tables:
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'mcl' AND table_name = %s",
                    (table,)
                )
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    cursor.execute(f"SELECT COUNT(*) FROM mcl.{table}")
                    row_count = cursor.fetchone()[0]
                    tables_info[table] = {
                        'exists': True,
                        'row_count': row_count
                    }
                else:
                    tables_info[table] = {'exists': False}
            
            cursor.close()
            
            return {
                'status': 'success',
                'tables': tables_info
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки таблиц mcl: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_migration_metadata(self) -> Dict[str, Any]:
        """
        Проверка метаданных миграции.
        
        Returns:
            Dict: Статистика по метаданным миграции
        """
        try:
            conn = self.conn_mgr.get_postgres_connection()
            cursor = conn.cursor()
            
            # Задачи миграции
            cursor.execute("SELECT COUNT(*) FROM mcl.migration_tasks")
            tasks_count = cursor.fetchone()[0]
            
            # MS SQL таблицы
            cursor.execute("SELECT COUNT(*) FROM mcl.mssql_tables")
            mssql_tables_count = cursor.fetchone()[0]
            
            # PostgreSQL таблицы
            cursor.execute("SELECT COUNT(*) FROM mcl.postgres_tables")
            postgres_tables_count = cursor.fetchone()[0]
            
            # Проблемы
            cursor.execute("SELECT COUNT(*) FROM mcl.problems")
            problems_count = cursor.fetchone()[0]
            
            # Статус миграции
            cursor.execute(
                "SELECT migration_status, COUNT(*) "
                "FROM mcl.mssql_tables "
                "GROUP BY migration_status"
            )
            migration_status = dict(cursor.fetchall())
            
            cursor.close()
            
            return {
                'status': 'success',
                'tasks_count': tasks_count,
                'mssql_tables_count': mssql_tables_count,
                'postgres_tables_count': postgres_tables_count,
                'problems_count': problems_count,
                'migration_status': migration_status
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки метаданных миграции: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_postgres_health(self) -> Dict[str, Any]:
        """
        Комплексная проверка здоровья PostgreSQL.
        
        Returns:
            Dict: Детальная информация о состоянии PostgreSQL
        """
        health_report = {
            'db_type': 'PostgreSQL',
            'timestamp': datetime.now().isoformat()
        }
        
        # Тест подключения
        conn_test = self.test_postgres_connection()
        health_report['connection'] = conn_test
        
        if conn_test['status'] != 'success':
            health_report['status'] = 'unhealthy'
            return health_report
        
        # Информация о БД
        db_info = self.get_postgres_database_info()
        health_report['database_info'] = db_info
        
        # Версия
        health_report['version'] = self.get_postgres_version()
        
        # Схема mcl
        mcl_info = self.check_mcl_schema_postgres()
        health_report['mcl_schema'] = mcl_info
        
        # Определяем общий статус
        health_report['status'] = 'healthy'
        
        return health_report
    
    def check_mssql_health(self) -> Dict[str, Any]:
        """
        Комплексная проверка здоровья MS SQL Server.
        
        Returns:
            Dict: Детальная информация о состоянии MS SQL Server
        """
        health_report = {
            'db_type': 'MS SQL Server',
            'timestamp': datetime.now().isoformat()
        }
        
        # Тест подключения
        conn_test = self.test_mssql_connection()
        health_report['connection'] = conn_test
        
        if conn_test['status'] != 'success':
            health_report['status'] = 'unhealthy'
            return health_report
        
        # Информация о БД
        db_info = self.get_mssql_database_info()
        health_report['database_info'] = db_info
        
        # Версия
        health_report['version'] = self.get_mssql_version()
        
        # Определяем общий статус
        health_report['status'] = 'healthy'
        
        return health_report
    
    def generate_health_report(self) -> Dict[str, Any]:
        """
        Генерация полного отчета о здоровье обеих БД.
        
        Returns:
            Dict: Полный отчет о состоянии системы
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'task_id': self.conn_mgr.task_id,
            'profile': self.conn_mgr.get_connection_info(),
            'postgres': self.check_postgres_health(),
            'mssql': self.check_mssql_health(),
            'metadata': self.check_migration_metadata()
        }
    
    def print_diagnostic_report(self) -> None:
        """
        Красивый вывод диагностического отчета.
        
        Использует Rich для форматирования если доступен,
        иначе простой текстовый вывод.
        """
        report = self.generate_health_report()
        
        if self.console and RICH_AVAILABLE:
            self._print_rich_report(report)
        else:
            self._print_text_report(report)
    
    def _print_rich_report(self, report: Dict[str, Any]) -> None:
        """Вывод отчета с помощью Rich."""
        # Заголовок
        self.console.print(Panel.fit(
            "[bold cyan]🔍 ДИАГНОСТИЧЕСКИЙ ОТЧЕТ FEMCL[/bold cyan]",
            border_style="cyan"
        ))
        
        # Информация о профиле
        profile = report['profile']
        self.console.print(f"\n[yellow]📋 Профиль:[/yellow]")
        self.console.print(f"  Task ID: {profile['task_id']}")
        self.console.print(f"  Имя: {profile['profile_name']}")
        
        # PostgreSQL
        pg = report['postgres']
        status_emoji = "✅" if pg['status'] == 'healthy' else "❌"
        self.console.print(f"\n[cyan]{status_emoji} PostgreSQL:[/cyan]")
        if pg['connection']['status'] == 'success':
            self.console.print(f"  [green]Подключение: OK[/green]")
            self.console.print(f"  База: {pg['database_info']['database']}")
            self.console.print(f"  Размер: {pg['database_info']['size']}")
        else:
            self.console.print(f"  [red]Ошибка подключения[/red]")
        
        # MS SQL Server
        ms = report['mssql']
        status_emoji = "✅" if ms['status'] == 'healthy' else "❌"
        self.console.print(f"\n[yellow]{status_emoji} MS SQL Server:[/yellow]")
        if ms['connection']['status'] == 'success':
            self.console.print(f"  [green]Подключение: OK[/green]")
            self.console.print(f"  База: {ms['database_info']['database']}")
        else:
            self.console.print(f"  [red]Ошибка подключения[/red]")
        
        # Метаданные
        if report['metadata']['status'] == 'success':
            md = report['metadata']
            self.console.print(f"\n[magenta]📊 Метаданные миграции:[/magenta]")
            self.console.print(f"  Задач: {md['tasks_count']}")
            self.console.print(f"  MS SQL таблиц: {md['mssql_tables_count']}")
            self.console.print(f"  PostgreSQL таблиц: {md['postgres_tables_count']}")
            self.console.print(f"  Проблем: {md['problems_count']}")
    
    def _print_text_report(self, report: Dict[str, Any]) -> None:
        """Простой текстовый вывод отчета."""
        print("\n" + "="*60)
        print("ДИАГНОСТИЧЕСКИЙ ОТЧЕТ FEMCL")
        print("="*60)
        
        profile = report['profile']
        print(f"\nПрофиль:")
        print(f"  Task ID: {profile['task_id']}")
        print(f"  Имя: {profile['profile_name']}")
        
        pg = report['postgres']
        print(f"\nPostgreSQL: {pg['status']}")
        if pg['connection']['status'] == 'success':
            print(f"  Подключение: OK")
            print(f"  База: {pg['database_info']['database']}")
        
        ms = report['mssql']
        print(f"\nMS SQL Server: {ms['status']}")
        if ms['connection']['status'] == 'success':
            print(f"  Подключение: OK")
            print(f"  База: {ms['database_info']['database']}")
        
        print("="*60)

