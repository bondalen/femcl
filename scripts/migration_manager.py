#!/usr/bin/env python3
"""
FEMCL - Менеджер миграции таблиц

ОБНОВЛЕНО: Использует ConnectionManager
Версия: 2.0
Дата обновления: 2025-10-07

Описание:
    Менеджер для управления миграцией таблиц с возможностью
    пакетной обработки, мониторинга и отчетности.

Использование:
    python scripts/migration_manager.py <command> [options]
    
Команды:
    list                    - Список таблиц для миграции
    migrate <table_name>    - Миграция одной таблицы
    batch <count>           - Пакетная миграция таблиц
    status                  - Статус миграции
    validate <table_name>   - Валидация таблицы
    report                  - Генерация отчета
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

# Добавляем путь к модулям проекта
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "code"))

from infrastructure.classes import ConnectionManager, ConnectionDiagnostics

console = Console()

class MigrationManager:
    """
    Менеджер миграции таблиц.
    
    ОБНОВЛЕНО: Использует ConnectionManager для подключений к БД.
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        """
        Инициализация MigrationManager.
        
        Args:
            connection_manager: Экземпляр ConnectionManager
        """
        self.conn_mgr = connection_manager
        self.task_id = connection_manager.task_id
    
    def _execute_pg_query(self, query, params=None, fetch_one=False):
        """
        Выполнение запроса к PostgreSQL.
        
        Args:
            query: SQL запрос
            params: Параметры запроса
            fetch_one: Вернуть одну строку (True) или все (False)
        
        Returns:
            Результат запроса
        """
        conn = self.conn_mgr.get_postgres_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if fetch_one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
        
        cursor.close()
        return result
    
    def list_tables(self, task_id=2, status='pending'):
        """Список таблиц для миграции"""
        try:
            query = """
            SELECT 
                mt.object_name,
                mt.row_count,
                mt.column_count,
                mt.has_primary_key,
                mt.foreign_key_count,
                ms.current_status
            FROM mcl.mssql_tables mt
            JOIN mcl.migration_status ms ON mt.id = ms.source_table_id
            WHERE mt.task_id = %s AND ms.current_status = %s
            ORDER BY mt.object_name
            """
            
            tables = self._execute_pg_query(query, (task_id, status))
            
            if not tables:
                rprint(f"[yellow]⚠️ Таблицы со статусом '{status}' не найдены[/yellow]")
                return []
            
            # Создаем таблицу для вывода
            table = Table(title=f"📋 Таблицы со статусом '{status}' (Задача ID={task_id})")
            table.add_column("№", style="cyan", no_wrap=True)
            table.add_column("Таблица", style="cyan", no_wrap=True)
            table.add_column("Строк", justify="right", style="green")
            table.add_column("Колонок", justify="right", style="green")
            table.add_column("PK", style="yellow")
            table.add_column("FK", justify="right", style="blue")
            table.add_column("Статус", style="white")
            
            for i, row in enumerate(tables, 1):
                table.add_row(
                    str(i),
                    row[0],  # object_name
                    str(row[1]),  # row_count
                    str(row[2]),  # column_count
                    "1" if row[3] else "0",  # has_primary_key
                    str(row[4]),  # foreign_key_count
                    row[5]  # current_status
                )
            
            console.print(table)
            rprint(f"📊 Всего таблиц: {len(tables)}")
            return tables
            
        except Exception as e:
            rprint(f"[red]❌ Ошибка получения списка таблиц: {e}[/red]")
            return []
    
    def get_migration_status(self, task_id=2):
        """Получение статуса миграции"""
        try:
            query = """
            SELECT 
                ms.current_status,
                COUNT(ms.id) as count
            FROM mcl.migration_status ms
            JOIN mcl.mssql_tables mt ON ms.source_table_id = mt.id
            WHERE mt.task_id = %s
            GROUP BY ms.current_status
            ORDER BY ms.current_status
            """
            
            status_summary = self._execute_pg_query(query, (task_id,))
            
            if not status_summary:
                rprint("[yellow]⚠️ Статус миграции не найден[/yellow]")
                return {}
            
            # Создаем таблицу для вывода
            table = Table(title="📊 Статус миграции")
            table.add_column("Статус", style="cyan")
            table.add_column("Количество", justify="right", style="green")
            
            total_tables = 0
            status_dict = {}
            
            for row in status_summary:
                status = row[0]
                count = row[1]
                total_tables += count
                status_dict[status] = count
                
                table.add_row(status, str(count))
            
            console.print(table)
            rprint(f"📊 Всего таблиц: {total_tables}")
            
            return status_dict
            
        except Exception as e:
            rprint(f"[red]❌ Ошибка получения статуса миграции: {e}[/red]")
            return {}
    
    def validate_table(self, table_name):
        """Валидация миграции таблицы"""
        try:
            # Проверяем существование таблицы в PostgreSQL
            exists_query = """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'ags' AND table_name = %s
            )
            """
            table_exists = self._execute_pg_query(exists_query, (table_name,), fetch_one=True)[0]
            
            if not table_exists:
                rprint(f"[red]❌ Таблица {table_name} не найдена в PostgreSQL[/red]")
                return False
            
            # Получаем информацию о таблице
            info_query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                ordinal_position
            FROM information_schema.columns 
            WHERE table_schema = 'ags' AND table_name = %s
            ORDER BY ordinal_position
            """
            columns = self._execute_pg_query(info_query, (table_name,))
            
            rprint(f"[green]✅ Таблица {table_name} найдена в PostgreSQL[/green]")
            rprint(f"📊 Колонок: {len(columns)}")
            
            # Выводим структуру таблицы
            table = Table(title=f"📋 Структура таблицы {table_name}")
            table.add_column("Позиция", style="cyan", no_wrap=True)
            table.add_column("Колонка", style="magenta")
            table.add_column("Тип", style="green")
            table.add_column("NULL", style="yellow")
            
            for col in columns:
                table.add_row(
                    str(col[3]),  # ordinal_position
                    col[0],  # column_name
                    col[1],  # data_type
                    "YES" if col[2] else "NO"  # is_nullable
                )
            
            console.print(table)
            return True
            
        except Exception as e:
            rprint(f"[red]❌ Ошибка валидации таблицы: {e}[/red]")
            return False
    
    def generate_report(self, task_id=2):
        """Генерация отчета о миграции"""
        try:
            # Получаем общую статистику
            status_dict = self.get_migration_status(task_id)
            
            # Получаем детальную информацию
            detail_query = """
            SELECT 
                mt.object_name,
                ms.current_status,
                ms.created_at,
                ms.updated_at,
                pt.migration_date,
                pt.error_message
            FROM mcl.mssql_tables mt
            JOIN mcl.migration_status ms ON mt.id = ms.source_table_id
            LEFT JOIN mcl.postgres_tables pt ON mt.id = pt.source_table_id
            WHERE mt.task_id = %s
            ORDER BY ms.current_status, mt.object_name
            """
            
            details = self._execute_pg_query(detail_query, (task_id,))
            
            # Создаем отчет
            report = f"""
# 📊 ОТЧЕТ О МИГРАЦИИ (Задача ID={task_id})
*Сгенерирован: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## 📈 Общая статистика
"""
            
            for status, count in status_dict.items():
                report += f"- **{status}**: {count} таблиц\n"
            
            report += f"\n## 📋 Детальная информация\n\n"
            
            current_status = None
            for row in details:
                table_name, status, created_at, updated_at, migration_date, error_message = row
                
                if status != current_status:
                    report += f"### {status.upper()}\n\n"
                    current_status = status
                
                report += f"**{table_name}**\n"
                report += f"- Создано: {created_at}\n"
                report += f"- Обновлено: {updated_at}\n"
                if migration_date:
                    report += f"- Дата миграции: {migration_date}\n"
                if error_message:
                    report += f"- Ошибка: {error_message}\n"
                report += "\n"
            
            # Сохраняем отчет
            report_filename = f"migration_report_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            report_path = os.path.join(os.path.dirname(__file__), '..', 'reports', report_filename)
            
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            rprint(f"[green]✅ Отчет сохранен: {report_path}[/green]")
            return report_path
            
        except Exception as e:
            rprint(f"[red]❌ Ошибка генерации отчета: {e}[/red]")
            return None

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='FEMCL - Менеджер миграции таблиц')
    parser.add_argument('command', choices=['list', 'migrate', 'batch', 'status', 'validate', 'report'],
                       help='Команда для выполнения')
    parser.add_argument('--table', help='Имя таблицы')
    parser.add_argument('--count', type=int, default=5, help='Количество таблиц для пакетной миграции')
    parser.add_argument('--task-id', type=int, default=2, help='ID задачи миграции')
    parser.add_argument('--status', default='pending', help='Статус таблиц для фильтрации')
    
    args = parser.parse_args()
    
    try:
        # Инициализация ConnectionManager
        conn_manager = ConnectionManager(task_id=args.task_id)
        
        # Информация о профиле
        info = conn_manager.get_connection_info()
        console.print(f"[green]✅ Профиль: {info['profile_name']} (task_id={info['task_id']})[/green]\n")
        
        # Создание менеджера миграции
        manager = MigrationManager(conn_manager)
        
        # Выполнение команды
        if args.command == 'list':
            manager.list_tables(args.task_id, args.status)
        elif args.command == 'status':
            manager.get_migration_status(args.task_id)
        elif args.command == 'validate':
            if not args.table:
                rprint("[red]❌ Необходимо указать имя таблицы с --table[/red]")
                sys.exit(1)
            manager.validate_table(args.table)
        elif args.command == 'report':
            manager.generate_report(args.task_id)
        else:
            rprint(f"[yellow]⚠️ Команда '{args.command}' пока не реализована[/yellow]")
    
    except ValueError as e:
        console.print(f"[red]❌ Ошибка инициализации: {e}[/red]")
        console.print("[yellow]💡 Проверьте connections.json[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Критическая ошибка: {e}[/red]")
        sys.exit(1)
    finally:
        if 'conn_manager' in locals():
            conn_manager.close_all_connections()

if __name__ == "__main__":
    main()