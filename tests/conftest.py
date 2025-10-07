"""
Pytest fixtures для тестов FEMCL

Общие фикстуры для всех типов тестов.
"""
import pytest
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "code"))

from infrastructure.classes import ConnectionManager, ConnectionDiagnostics


@pytest.fixture(scope="session")
def connection_manager():
    """
    Session-level fixture для ConnectionManager.
    
    Создается один раз для всей сессии тестирования.
    task_id=2 по умолчанию.
    
    Example:
        def test_something(connection_manager):
            conn = connection_manager.get_postgres_connection()
    """
    manager = ConnectionManager(task_id=2)
    yield manager
    manager.close_all_connections()


@pytest.fixture(scope="function")
def fresh_connection_manager():
    """
    Function-level fixture для ConnectionManager.
    
    Создается новый для каждого теста.
    Используйте когда нужно изолированное подключение.
    
    Example:
        def test_something(fresh_connection_manager):
            # Каждый тест получает новый менеджер
            conn = fresh_connection_manager.get_postgres_connection()
    """
    manager = ConnectionManager(task_id=2)
    yield manager
    manager.close_all_connections()


@pytest.fixture(scope="session")
def connection_diagnostics(connection_manager):
    """
    Session-level fixture для ConnectionDiagnostics.
    
    Example:
        def test_health(connection_diagnostics):
            report = connection_diagnostics.check_postgres_health()
    """
    return ConnectionDiagnostics(connection_manager)


@pytest.fixture
def postgres_connection(connection_manager):
    """
    Fixture для прямого подключения к PostgreSQL.
    
    Подключение автоматически закроется через connection_manager.
    
    Example:
        def test_query(postgres_connection):
            cursor = postgres_connection.cursor()
            cursor.execute("SELECT 1")
    """
    conn = connection_manager.get_postgres_connection()
    yield conn
    # Подключение закроется через connection_manager


@pytest.fixture
def mssql_connection(connection_manager):
    """
    Fixture для прямого подключения к MS SQL Server.
    
    Подключение автоматически закроется через connection_manager.
    
    Example:
        def test_query(mssql_connection):
            cursor = mssql_connection.cursor()
            cursor.execute("SELECT @@VERSION")
    """
    conn = connection_manager.get_mssql_connection()
    yield conn
    # Подключение закроется через connection_manager


@pytest.fixture
def task_id():
    """Fixture для task_id (по умолчанию 2)"""
    return 2
