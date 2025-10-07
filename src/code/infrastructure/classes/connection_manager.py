"""
ConnectionManager - Менеджер подключений к БД

Центральная точка для всех операций с подключениями к базам данных.
Использует ConnectionProfileLoader для загрузки профилей из connections.json.

По умолчанию: task_id=2
"""

import logging
from typing import Optional, Dict, Any
import pyodbc
import psycopg2

from .connection_profile_loader import ConnectionProfileLoader


logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Менеджер подключений к базам данных.
    
    Управляет подключениями к MS SQL Server и PostgreSQL используя
    профили из connections.json.
    
    Attributes:
        profile_loader: Загрузчик профилей подключений
        task_id: ID текущей задачи миграции (по умолчанию 2)
        current_profile: Текущий активный профиль
        _mssql_connection: Активное подключение к MS SQL Server
        _postgres_connection: Активное подключение к PostgreSQL
    
    Example:
        >>> manager = ConnectionManager()  # task_id=2 по умолчанию
        >>> pg_conn = manager.get_postgres_connection()
        >>> ms_conn = manager.get_mssql_connection()
        >>> manager.close_all_connections()
    """
    
    def __init__(self, 
                 profile_loader: Optional[ConnectionProfileLoader] = None,
                 task_id: int = 2):
        """
        Инициализация ConnectionManager.
        
        Args:
            profile_loader: Загрузчик профилей (опционально, создается автоматически)
            task_id: ID задачи миграции (по умолчанию 2)
        
        Raises:
            ValueError: Если профиль для указанного task_id не найден
        """
        self.logger = logging.getLogger(__name__)
        self.profile_loader = profile_loader or ConnectionProfileLoader()
        self.task_id = task_id
        self.current_profile: Optional[Dict[str, Any]] = None
        self._mssql_connection: Optional[pyodbc.Connection] = None
        self._postgres_connection: Optional[psycopg2.extensions.connection] = None
        
        # Загружаем профиль при инициализации
        self._load_profile_by_task_id(task_id)
        
        self.logger.info(
            f"ConnectionManager инициализирован для task_id={task_id}, "
            f"профиль: {self.current_profile.get('name') if self.current_profile else 'не загружен'}"
        )
    
    def _load_profile_by_task_id(self, task_id: int) -> None:
        """
        Загрузка профиля по task_id.
        
        Args:
            task_id: ID задачи миграции
        
        Raises:
            ValueError: Если профиль не найден
        """
        self.current_profile = self.profile_loader.get_profile_by_task_id(task_id)
        
        if not self.current_profile:
            error_msg = (
                f"Профиль для task_id={task_id} не найден в connections.json. "
                f"Проверьте файл конфигурации."
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Валидация профиля
        if not self.profile_loader.validate_profile(self.current_profile):
            error_msg = f"Профиль для task_id={task_id} имеет некорректную структуру"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.info(f"Профиль для task_id={task_id} успешно загружен")
    
    def get_mssql_connection(self) -> pyodbc.Connection:
        """
        Получение подключения к MS SQL Server.
        
        Использует параметры из source в текущем профиле.
        Переиспользует существующее подключение если оно активно.
        
        Returns:
            pyodbc.Connection: Активное подключение к MS SQL Server
        
        Raises:
            ValueError: Если профиль не загружен
            pyodbc.Error: При ошибке подключения
        
        Example:
            >>> manager = ConnectionManager()
            >>> conn = manager.get_mssql_connection()
            >>> cursor = conn.cursor()
            >>> cursor.execute("SELECT @@VERSION")
        """
        if not self.current_profile:
            raise ValueError("Профиль не загружен. Невозможно создать подключение.")
        
        # Проверяем существующее подключение
        if self._mssql_connection:
            try:
                # Проверка активности подключения
                self._mssql_connection.cursor().execute("SELECT 1")
                self.logger.debug("Переиспользуется существующее подключение к MS SQL Server")
                return self._mssql_connection
            except (pyodbc.Error, AttributeError):
                self.logger.warning("Существующее подключение к MS SQL Server неактивно, создается новое")
                self._mssql_connection = None
        
        # Создаем новое подключение
        source = self.current_profile['source']
        
        try:
            connection_string = (
                f"DRIVER={{{source['driver']}}};"
                f"SERVER={source['host']},{source['port']};"
                f"DATABASE={source['database']};"
                f"UID={source['user']};"
                f"PWD={source['password']};"
            )
            
            # Добавляем опции если есть
            if 'options' in source:
                for key, value in source['options'].items():
                    connection_string += f"{key}={value};"
            
            self.logger.info(
                f"Подключение к MS SQL Server: "
                f"{source['host']}:{source['port']}/{source['database']}"
            )
            
            self._mssql_connection = pyodbc.connect(connection_string)
            self.logger.info("Подключение к MS SQL Server успешно установлено")
            
            return self._mssql_connection
            
        except pyodbc.Error as e:
            self.logger.error(f"Ошибка подключения к MS SQL Server: {e}")
            raise
    
    def get_postgres_connection(self) -> psycopg2.extensions.connection:
        """
        Получение подключения к PostgreSQL.
        
        Использует параметры из target в текущем профиле.
        Переиспользует существующее подключение если оно активно.
        
        Returns:
            psycopg2.extensions.connection: Активное подключение к PostgreSQL
        
        Raises:
            ValueError: Если профиль не загружен
            psycopg2.Error: При ошибке подключения
        
        Example:
            >>> manager = ConnectionManager()
            >>> conn = manager.get_postgres_connection()
            >>> cursor = conn.cursor()
            >>> cursor.execute("SELECT version()")
        """
        if not self.current_profile:
            raise ValueError("Профиль не загружен. Невозможно создать подключение.")
        
        # Проверяем существующее подключение
        if self._postgres_connection:
            try:
                # Проверка активности подключения
                if not self._postgres_connection.closed:
                    cursor = self._postgres_connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    self.logger.debug("Переиспользуется существующее подключение к PostgreSQL")
                    return self._postgres_connection
            except (psycopg2.Error, AttributeError):
                self.logger.warning("Существующее подключение к PostgreSQL неактивно, создается новое")
                self._postgres_connection = None
        
        # Создаем новое подключение
        target = self.current_profile['target']
        
        try:
            connection_params = {
                'host': target['host'],
                'port': target['port'],
                'dbname': target['database'],
                'user': target['user'],
                'password': target['password']
            }
            
            # Добавляем опции если есть
            if 'options' in target:
                if 'connect_timeout' in target['options']:
                    connection_params['connect_timeout'] = int(target['options']['connect_timeout'])
            
            # Добавляем SSL если указан
            if 'ssl' in target:
                connection_params['sslmode'] = target['ssl']
            
            self.logger.info(
                f"Подключение к PostgreSQL: "
                f"{target['host']}:{target['port']}/{target['database']}"
            )
            
            self._postgres_connection = psycopg2.connect(**connection_params)
            self.logger.info("Подключение к PostgreSQL успешно установлено")
            
            return self._postgres_connection
            
        except psycopg2.Error as e:
            self.logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            raise
    
    def close_mssql_connection(self) -> None:
        """
        Закрытие подключения к MS SQL Server.
        
        Безопасно закрывает активное подключение если оно существует.
        """
        if self._mssql_connection:
            try:
                self._mssql_connection.close()
                self.logger.info("Подключение к MS SQL Server закрыто")
            except Exception as e:
                self.logger.warning(f"Ошибка при закрытии подключения к MS SQL Server: {e}")
            finally:
                self._mssql_connection = None
    
    def close_postgres_connection(self) -> None:
        """
        Закрытие подключения к PostgreSQL.
        
        Безопасно закрывает активное подключение если оно существует.
        """
        if self._postgres_connection:
            try:
                self._postgres_connection.close()
                self.logger.info("Подключение к PostgreSQL закрыто")
            except Exception as e:
                self.logger.warning(f"Ошибка при закрытии подключения к PostgreSQL: {e}")
            finally:
                self._postgres_connection = None
    
    def close_all_connections(self) -> None:
        """
        Закрытие всех активных подключений.
        
        Безопасно закрывает подключения к обеим базам данных.
        
        Example:
            >>> manager = ConnectionManager()
            >>> # ... работа с подключениями
            >>> manager.close_all_connections()
        """
        self.close_mssql_connection()
        self.close_postgres_connection()
        self.logger.info("Все подключения закрыты")
    
    def switch_task(self, task_id: int) -> None:
        """
        Переключение на другую задачу миграции.
        
        Закрывает текущие подключения и загружает новый профиль.
        
        Args:
            task_id: ID новой задачи миграции
        
        Raises:
            ValueError: Если профиль для нового task_id не найден
        
        Example:
            >>> manager = ConnectionManager()  # task_id=2
            >>> # ... работа с task_id=2
            >>> manager.switch_task(1)  # переключение на task_id=1
            >>> # ... работа с task_id=1
        """
        self.logger.info(f"Переключение с task_id={self.task_id} на task_id={task_id}")
        
        # Закрываем текущие подключения
        self.close_all_connections()
        
        # Загружаем новый профиль
        self._load_profile_by_task_id(task_id)
        self.task_id = task_id
        
        self.logger.info(f"Успешно переключено на task_id={task_id}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Получение информации о текущих подключениях.
        
        Returns:
            Dict: Словарь с информацией о профиле и подключениях
        
        Example:
            >>> manager = ConnectionManager()
            >>> info = manager.get_connection_info()
            >>> print(f"Task ID: {info['task_id']}")
            >>> print(f"Profile: {info['profile_name']}")
        """
        if not self.current_profile:
            return {
                'task_id': self.task_id,
                'profile_loaded': False,
                'error': 'Профиль не загружен'
            }
        
        return {
            'task_id': self.task_id,
            'profile_id': self.current_profile.get('profile_id'),
            'profile_name': self.current_profile.get('name'),
            'description': self.current_profile.get('description'),
            'source': {
                'type': self.current_profile['source']['type'],
                'host': self.current_profile['source']['host'],
                'port': self.current_profile['source']['port'],
                'database': self.current_profile['source']['database'],
                'user': self.current_profile['source']['user']
            },
            'target': {
                'type': self.current_profile['target']['type'],
                'host': self.current_profile['target']['host'],
                'port': self.current_profile['target']['port'],
                'database': self.current_profile['target']['database'],
                'user': self.current_profile['target']['user']
            },
            'connections': {
                'mssql_active': self._mssql_connection is not None,
                'postgres_active': self._postgres_connection is not None
            }
        }
    
    def is_connected(self, db_type: str) -> bool:
        """
        Проверка наличия активного подключения.
        
        Args:
            db_type: Тип БД ('mssql' или 'postgres')
        
        Returns:
            bool: True если подключение активно
        
        Example:
            >>> manager = ConnectionManager()
            >>> if manager.is_connected('postgres'):
            >>>     print("PostgreSQL подключен")
        """
        if db_type.lower() in ('mssql', 'ms_sql', 'sqlserver'):
            return self._mssql_connection is not None
        elif db_type.lower() in ('postgres', 'postgresql', 'pg'):
            return self._postgres_connection is not None
        else:
            raise ValueError(f"Неизвестный тип БД: {db_type}. Используйте 'mssql' или 'postgres'")
    
    def reconnect(self, db_type: str) -> bool:
        """
        Переподключение к базе данных.
        
        Args:
            db_type: Тип БД ('mssql' или 'postgres')
        
        Returns:
            bool: True если переподключение успешно
        
        Example:
            >>> manager = ConnectionManager()
            >>> if not manager.reconnect('postgres'):
            >>>     print("Не удалось переподключиться")
        """
        try:
            if db_type.lower() in ('mssql', 'ms_sql', 'sqlserver'):
                self.close_mssql_connection()
                self.get_mssql_connection()
                return True
            elif db_type.lower() in ('postgres', 'postgresql', 'pg'):
                self.close_postgres_connection()
                self.get_postgres_connection()
                return True
            else:
                raise ValueError(f"Неизвестный тип БД: {db_type}")
        except Exception as e:
            self.logger.error(f"Ошибка переподключения к {db_type}: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - закрывает все подключения."""
        self.close_all_connections()
    
    def __del__(self):
        """Деструктор - закрывает подключения при удалении объекта."""
        try:
            self.close_all_connections()
        except:
            pass  # Игнорируем ошибки при деструкции
