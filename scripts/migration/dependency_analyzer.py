#!/usr/bin/env python3
"""
Модуль анализа зависимостей таблиц для миграции
"""
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
import psycopg2
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

# Добавляем путь к проекту
sys.path.append('/home/alex/projects/sql/femcl')

console = Console()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/alex/projects/sql/femcl/logs/dependency_analysis.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DependencyAnalyzer:
    """Класс для анализа зависимостей между таблицами"""
    
    def __init__(self, config_path="/home/alex/projects/sql/femcl/config/config.yaml"):
        """Инициализация анализатора"""
        import yaml
        with open(config_path, 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)
        
        self.connection = None
        self._dependency_graph = None
        self._migration_order = None
        self._circular_dependencies = None
        self._ensure_dependency_tables()
    
    def _get_connection(self):
        """Получение подключения к PostgreSQL"""
        if self.connection is None or self.connection.closed:
            postgres_config = self.config['database']['postgres']
            self.connection = psycopg2.connect(
                host=postgres_config['host'],
                port=postgres_config['port'],
                dbname=postgres_config['database'],
                user=postgres_config['user'],
                password=postgres_config['password'],
                connect_timeout=postgres_config['connection_timeout'],
                sslmode=postgres_config['ssl_mode']
            )
        return self.connection
    
    def _execute_query(self, query, params=None):
        """Выполнение SQL запроса"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            else:
                conn.commit()
                return []
        finally:
            if cursor:
                cursor.close()
    
    def _ensure_dependency_tables(self):
        """Создание таблиц для анализа зависимостей если не существуют"""
        create_dependencies_table = """
        CREATE TABLE IF NOT EXISTS mcl.table_dependencies (
            id SERIAL PRIMARY KEY,
            source_table_name VARCHAR(255) NOT NULL,
            target_table_name VARCHAR(255) NOT NULL,
            dependency_type VARCHAR(50) NOT NULL,
            is_critical BOOLEAN DEFAULT FALSE,
            is_circular BOOLEAN DEFAULT FALSE,
            dependency_level INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_table_name, target_table_name)
        );
        """
        
        create_readiness_table = """
        CREATE TABLE IF NOT EXISTS mcl.referenced_table_readiness (
            id SERIAL PRIMARY KEY,
            table_name VARCHAR(255) NOT NULL,
            referenced_table_name VARCHAR(255) NOT NULL,
            is_ready BOOLEAN DEFAULT FALSE,
            readiness_reason TEXT,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(table_name, referenced_table_name)
        );
        """
        
        create_indexes = """
        CREATE INDEX IF NOT EXISTS idx_table_dependencies_source 
        ON mcl.table_dependencies(source_table_name);
        
        CREATE INDEX IF NOT EXISTS idx_table_dependencies_target 
        ON mcl.table_dependencies(target_table_name);
        
        CREATE INDEX IF NOT EXISTS idx_table_dependencies_type 
        ON mcl.table_dependencies(dependency_type);
        
        CREATE INDEX IF NOT EXISTS idx_referenced_readiness_table 
        ON mcl.referenced_table_readiness(table_name);
        """
        
        try:
            self._execute_query(create_dependencies_table)
            self._execute_query(create_readiness_table)
            self._execute_query(create_indexes)
            logger.info("Таблицы для анализа зависимостей созданы или уже существуют")
        except Exception as e:
            logger.error(f"Ошибка создания таблиц зависимостей: {e}")
            raise
    
    def analyze_table_dependencies(self, table_name: str) -> Dict:
        """
        Анализ зависимостей для конкретной таблицы
        
        Args:
            table_name (str): Имя таблицы для анализа
        
        Returns:
            dict: Информация о зависимостях таблицы
        """
        console.print(f"[blue]🔍 Анализ зависимостей для таблицы {table_name}[/blue]")
        
        # Получаем внешние ключи для таблицы
        fk_query = """
        SELECT 
            pfk.constraint_name,
            pfk.referenced_table_id,
            pfk.delete_action,
            pfk.update_action,
            pc_ref.column_name as referenced_column_name,
            pc.column_name as source_column_name
        FROM mcl.postgres_foreign_keys pfk
        JOIN mcl.postgres_foreign_key_columns pfkc ON pfk.id = pfkc.foreign_key_id
        JOIN mcl.postgres_columns pc ON pfkc.column_id = pc.id
        JOIN mcl.postgres_columns pc_ref ON pfkc.referenced_column_id = pc_ref.id
        JOIN mcl.postgres_tables pt ON pfk.table_id = pt.id
        WHERE pt.object_name = %s
        """
        
        foreign_keys = self._execute_query(fk_query, (table_name,))
        
        # Получаем имена ссылочных таблиц
        referenced_tables = []
        critical_dependencies = []
        
        for fk in foreign_keys:
            # Получаем имя ссылочной таблицы
            ref_table_query = """
            SELECT object_name FROM mcl.postgres_tables WHERE id = %s
            """
            ref_table_result = self._execute_query(ref_table_query, (fk['referenced_table_id'],))
            
            if ref_table_result:
                ref_table_name = ref_table_result[0]['object_name']
                referenced_tables.append(ref_table_name)
                
                # Определяем критичность зависимости
                is_critical = fk['delete_action'] in ['RESTRICT', 'CASCADE']
                if is_critical:
                    critical_dependencies.append({
                        'constraint_name': fk['constraint_name'],
                        'referenced_table': ref_table_name,
                        'delete_action': fk['delete_action'],
                        'update_action': fk['update_action']
                    })
        
        # Анализируем обратные зависимости (таблицы, которые ссылаются на текущую)
        reverse_query = """
        SELECT DISTINCT pt.object_name as dependent_table
        FROM mcl.postgres_foreign_keys pfk
        JOIN mcl.postgres_tables pt ON pfk.table_id = pt.id
        JOIN mcl.postgres_tables pt_ref ON pfk.referenced_table_id = pt_ref.id
        WHERE pt_ref.object_name = %s
        """
        
        dependent_tables = self._execute_query(reverse_query, (table_name,))
        dependent_table_names = [table['dependent_table'] for table in dependent_tables]
        
        result = {
            'table_name': table_name,
            'referenced_tables': list(set(referenced_tables)),
            'dependent_tables': dependent_table_names,
            'critical_dependencies': critical_dependencies,
            'total_dependencies': len(referenced_tables),
            'critical_count': len(critical_dependencies),
            'dependency_level': len(referenced_tables) + len(dependent_table_names)
        }
        
        console.print(f"   📊 Найдено зависимостей: {result['total_dependencies']}")
        console.print(f"   🔗 Критических: {result['critical_count']}")
        console.print(f"   📈 Уровень зависимости: {result['dependency_level']}")
        
        logger.info(f"Анализ зависимостей для {table_name}: {result}")
        return result
    
    def check_referenced_tables_ready(self, table_name: str) -> Dict:
        """
        Проверка готовности ссылочных таблиц
        
        Args:
            table_name (str): Имя таблицы для проверки
        
        Returns:
            dict: Статус готовности ссылочных таблиц
        """
        console.print(f"[blue]🔍 Проверка готовности ссылочных таблиц для {table_name}[/blue]")
        
        # Получаем зависимости таблицы
        dependencies = self.analyze_table_dependencies(table_name)
        referenced_tables = dependencies['referenced_tables']
        
        if not referenced_tables:
            return {
                'table_name': table_name,
                'ready_percentage': 100.0,
                'ready_tables': [],
                'not_ready_tables': [],
                'total_referenced': 0
            }
        
        # Проверяем готовность каждой ссылочной таблицы
        ready_tables = []
        not_ready_tables = []
        
        for ref_table in referenced_tables:
            # Проверяем существование таблицы в PostgreSQL
            check_table_query = """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'ags' AND table_name = %s
            ) as table_exists
            """
            
            table_exists = self._execute_query(check_table_query, (ref_table,))
            
            if table_exists and table_exists[0]['table_exists']:
                # Проверяем, что таблица завершена
                status_query = """
                SELECT current_status FROM mcl.migration_status WHERE table_name = %s
                """
                status_result = self._execute_query(status_query, (ref_table,))
                
                if status_result and status_result[0]['current_status'] == 'completed':
                    ready_tables.append(ref_table)
                else:
                    not_ready_tables.append({
                        'table': ref_table,
                        'reason': 'not_completed',
                        'status': status_result[0]['current_status'] if status_result else 'unknown'
                    })
            else:
                not_ready_tables.append({
                    'table': ref_table,
                    'reason': 'not_exists',
                    'status': 'missing'
                })
        
        ready_percentage = (len(ready_tables) / len(referenced_tables) * 100) if referenced_tables else 100.0
        
        result = {
            'table_name': table_name,
            'ready_percentage': ready_percentage,
            'ready_tables': ready_tables,
            'not_ready_tables': not_ready_tables,
            'total_referenced': len(referenced_tables)
        }
        
        console.print(f"   ✅ Готовых таблиц: {len(ready_tables)}/{len(referenced_tables)}")
        console.print(f"   📊 Процент готовности: {ready_percentage:.1f}%")
        
        logger.info(f"Проверка готовности для {table_name}: {result}")
        return result
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Выявление циклических зависимостей
        
        Returns:
            list: Список циклических зависимостей
        """
        console.print("[blue]🔍 Поиск циклических зависимостей[/blue]")
        
        # Строим граф зависимостей
        graph = self._build_dependency_graph()
        
        # Используем DFS для поиска циклов
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Найден цикл
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path.copy())
            
            rec_stack.remove(node)
            path.pop()
        
        # Проверяем все узлы
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        console.print(f"   🔄 Найдено циклов: {len(cycles)}")
        for i, cycle in enumerate(cycles, 1):
            console.print(f"   Цикл {i}: {' → '.join(cycle)}")
        
        logger.info(f"Обнаружено {len(cycles)} циклических зависимостей")
        return cycles
    
    def get_migration_order(self) -> List[str]:
        """
        Определение оптимального порядка миграции
        
        Returns:
            list: Список таблиц в порядке миграции
        """
        console.print("[blue]🔍 Определение порядка миграции[/blue]")
        
        # Строим граф зависимостей
        graph = self._build_dependency_graph()
        
        # Топологическая сортировка
        in_degree = defaultdict(int)
        for node in graph:
            in_degree[node] = 0
        
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] += 1
        
        # Алгоритм Kahn
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Добавляем таблицы без зависимостей
        all_tables_query = """
        SELECT object_name FROM mcl.postgres_tables ORDER BY object_name
        """
        all_tables = self._execute_query(all_tables_query)
        all_table_names = [table['object_name'] for table in all_tables]
        
        # Добавляем таблицы, которые не были обработаны
        for table in all_table_names:
            if table not in result:
                result.append(table)
        
        console.print(f"   📋 Определён порядок для {len(result)} таблиц")
        console.print(f"   🎯 Первые 5 таблиц: {result[:5]}")
        
        logger.info(f"Порядок миграции определён для {len(result)} таблиц")
        return result
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Построение графа зависимостей
        
        Returns:
            dict: Граф зависимостей в формате adjacency list
        """
        if self._dependency_graph is not None:
            return self._dependency_graph
        
        console.print("[blue]🔧 Построение графа зависимостей[/blue]")
        
        # Получаем все внешние ключи
        fk_query = """
        SELECT 
            pt.object_name as source_table,
            pt_ref.object_name as target_table,
            pfk.delete_action,
            pfk.update_action
        FROM mcl.postgres_foreign_keys pfk
        JOIN mcl.postgres_tables pt ON pfk.table_id = pt.id
        JOIN mcl.postgres_tables pt_ref ON pfk.referenced_table_id = pt_ref.id
        """
        
        foreign_keys = self._execute_query(fk_query)
        
        # Строим граф
        graph = defaultdict(list)
        
        for fk in foreign_keys:
            source = fk['source_table']
            target = fk['target_table']
            graph[source].append(target)
        
        self._dependency_graph = dict(graph)
        
        console.print(f"   📊 Построен граф с {len(graph)} узлами")
        console.print(f"   🔗 Найдено {len(foreign_keys)} зависимостей")
        
        logger.info(f"Граф зависимостей построен: {len(graph)} узлов, {len(foreign_keys)} рёбер")
        return self._dependency_graph
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Получение графа зависимостей
        
        Returns:
            dict: Граф зависимостей в формате adjacency list
        """
        return self._build_dependency_graph()
    
    def analyze_dependency_chain(self, table_name: str) -> List[str]:
        """
        Анализ цепочки зависимостей для таблицы
        
        Args:
            table_name (str): Имя таблицы
        
        Returns:
            list: Цепочка зависимостей
        """
        console.print(f"[blue]🔍 Анализ цепочки зависимостей для {table_name}[/blue]")
        
        graph = self._build_dependency_graph()
        visited = set()
        chain = []
        
        def dfs(node, path):
            if node in visited:
                return
            
            visited.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path)
        
        dfs(table_name, chain)
        
        console.print(f"   🔗 Цепочка зависимостей: {' → '.join(chain)}")
        logger.info(f"Цепочка зависимостей для {table_name}: {chain}")
        return chain
    
    def get_critical_dependencies(self) -> List[Dict]:
        """
        Получение критических зависимостей
        
        Returns:
            list: Список критических зависимостей
        """
        console.print("[blue]🔍 Поиск критических зависимостей[/blue]")
        
        critical_query = """
        SELECT 
            pt.object_name as source_table,
            pt_ref.object_name as target_table,
            pfk.constraint_name,
            pfk.delete_action,
            pfk.update_action
        FROM mcl.postgres_foreign_keys pfk
        JOIN mcl.postgres_tables pt ON pfk.table_id = pt.id
        JOIN mcl.postgres_tables pt_ref ON pfk.referenced_table_id = pt_ref.id
        WHERE pfk.delete_action IN ('RESTRICT', 'CASCADE')
        """
        
        critical_deps = self._execute_query(critical_query)
        
        console.print(f"   ⚠️ Найдено критических зависимостей: {len(critical_deps)}")
        
        logger.info(f"Найдено {len(critical_deps)} критических зависимостей")
        return critical_deps
    
    def validate_dependency_integrity(self, table_name: str) -> bool:
        """
        Валидация целостности зависимостей
        
        Args:
            table_name (str): Имя таблицы
        
        Returns:
            bool: True если зависимости корректны
        """
        console.print(f"[blue]🔍 Валидация целостности зависимостей для {table_name}[/blue]")
        
        try:
            # Проверяем готовность ссылочных таблиц
            readiness = self.check_referenced_tables_ready(table_name)
            
            # Проверяем, что все ссылочные таблицы готовы
            is_valid = readiness['ready_percentage'] == 100.0
            
            if is_valid:
                console.print(f"   ✅ Все зависимости для {table_name} корректны")
            else:
                console.print(f"   ❌ Не все зависимости для {table_name} готовы")
                for not_ready in readiness['not_ready_tables']:
                    console.print(f"      - {not_ready['table']}: {not_ready['reason']}")
            
            logger.info(f"Валидация целостности для {table_name}: {is_valid}")
            return is_valid
            
        except Exception as e:
            console.print(f"   ❌ Ошибка валидации: {e}")
            logger.error(f"Ошибка валидации для {table_name}: {e}")
            return False
    
    def display_dependency_tree(self, table_name: str):
        """Отображение дерева зависимостей для таблицы"""
        console.print(f"[blue]🌳 Дерево зависимостей для {table_name}[/blue]")
        
        tree = Tree(f"[bold green]{table_name}[/bold green]")
        
        # Получаем зависимости
        dependencies = self.analyze_table_dependencies(table_name)
        
        for ref_table in dependencies['referenced_tables']:
            branch = tree.add(f"[yellow]{ref_table}[/yellow]")
            
            # Рекурсивно добавляем зависимости ссылочной таблицы
            ref_deps = self.analyze_table_dependencies(ref_table)
            for sub_ref in ref_deps['referenced_tables']:
                branch.add(f"[dim]{sub_ref}[/dim]")
        
        console.print(tree)
    
    def get_migration_statistics(self) -> Dict:
        """
        Получение статистики зависимостей
        
        Returns:
            dict: Статистика зависимостей
        """
        console.print("[blue]📊 Получение статистики зависимостей[/blue]")
        
        # Получаем все таблицы
        all_tables_query = "SELECT object_name FROM mcl.postgres_tables ORDER BY object_name"
        all_tables = self._execute_query(all_tables_query)
        all_table_names = [table['object_name'] for table in all_tables]
        
        # Анализируем зависимости для всех таблиц
        total_dependencies = 0
        tables_with_deps = 0
        max_dependencies = 0
        dependency_levels = []
        
        for table_name in all_table_names:
            deps = self.analyze_table_dependencies(table_name)
            if deps['total_dependencies'] > 0:
                tables_with_deps += 1
                total_dependencies += deps['total_dependencies']
                max_dependencies = max(max_dependencies, deps['total_dependencies'])
                dependency_levels.append(deps['dependency_level'])
        
        # Находим циклические зависимости
        cycles = self.detect_circular_dependencies()
        
        # Получаем критические зависимости
        critical = self.get_critical_dependencies()
        
        statistics = {
            'total_tables': len(all_table_names),
            'tables_with_dependencies': tables_with_deps,
            'total_dependencies': total_dependencies,
            'max_dependencies_per_table': max_dependencies,
            'avg_dependencies': total_dependencies / tables_with_deps if tables_with_deps > 0 else 0,
            'circular_dependencies': len(cycles),
            'critical_dependencies': len(critical),
            'avg_dependency_level': sum(dependency_levels) / len(dependency_levels) if dependency_levels else 0
        }
        
        console.print(f"   📊 Всего таблиц: {statistics['total_tables']}")
        console.print(f"   🔗 Таблиц с зависимостями: {statistics['tables_with_dependencies']}")
        console.print(f"   📈 Всего зависимостей: {statistics['total_dependencies']}")
        console.print(f"   🔄 Циклических зависимостей: {statistics['circular_dependencies']}")
        console.print(f"   ⚠️ Критических зависимостей: {statistics['critical_dependencies']}")
        
        logger.info(f"Статистика зависимостей: {statistics}")
        return statistics
    
    def close(self):
        """Закрытие подключения"""
        if self.connection and not self.connection.closed:
            self.connection.close()

# Примеры использования
if __name__ == "__main__":
    # Создаём анализатор
    analyzer = DependencyAnalyzer()
    
    try:
        # Анализ зависимостей для конкретной таблицы
        table_name = "accnt"
        deps = analyzer.analyze_table_dependencies(table_name)
        console.print(f"Зависимости для {table_name}: {deps}")
        
        # Проверка готовности
        readiness = analyzer.check_referenced_tables_ready(table_name)
        console.print(f"Готовность для {table_name}: {readiness}")
        
        # Поиск циклических зависимостей
        cycles = analyzer.detect_circular_dependencies()
        console.print(f"Циклические зависимости: {cycles}")
        
        # Определение порядка миграции
        order = analyzer.get_migration_order()
        console.print(f"Порядок миграции: {order[:10]}...")
        
        # Статистика
        stats = analyzer.get_migration_statistics()
        console.print(f"Статистика: {stats}")
        
    finally:
        analyzer.close()