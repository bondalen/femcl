#!/usr/bin/env python3
"""
Модуль для определения имён целевых таблиц в системе миграции
"""
import re
from typing import Optional

class TableNameResolver:
    """Класс для определения имён целевых таблиц"""
    
    def __init__(self, target_schema: str = "ags"):
        """
        Инициализация резолвера имён таблиц
        
        Args:
            target_schema: Целевая схема (по умолчанию "ags")
        """
        self.target_schema = target_schema
    
    def get_target_table_name(self, source_table_name: str) -> str:
        """
        Определение имени целевой таблицы
        
        Args:
            source_table_name: Имя исходной таблицы
            
        Returns:
            Полное имя целевой таблицы
        """
        # Проверяем, нужно ли заключать имя в кавычки
        if self._needs_quotes(source_table_name):
            return f'{self.target_schema}."{source_table_name}"'
        else:
            return f'{self.target_schema}.{source_table_name}'
    
    def _needs_quotes(self, table_name: str) -> bool:
        """
        Проверка, нужно ли заключать имя таблицы в кавычки
        
        Args:
            table_name: Имя таблицы
            
        Returns:
            True, если нужны кавычки
        """
        # Проверяем различные условия для кавычек
        
        # 1. Содержит заглавные буквы
        if any(c.isupper() for c in table_name):
            return True
        
        # 2. Содержит специальные символы (кроме подчёркивания)
        if re.search(r'[^a-z0-9_]', table_name, re.IGNORECASE):
            return True
        
        # 3. Начинается с цифры
        if table_name[0].isdigit():
            return True
        
        # 4. Является зарезервированным словом PostgreSQL
        reserved_words = {
            'user', 'order', 'group', 'select', 'from', 'where', 'table',
            'index', 'view', 'sequence', 'function', 'trigger', 'schema'
        }
        if table_name.lower() in reserved_words:
            return True
        
        return False
    
    def get_safe_column_name(self, column_name: str) -> str:
        """
        Получение безопасного имени колонки
        
        Args:
            column_name: Имя колонки
            
        Returns:
            Безопасное имя колонки
        """
        if self._needs_quotes(column_name):
            return f'"{column_name}"'
        else:
            return column_name
    
    def analyze_table_names(self, table_names: list) -> dict:
        """
        Анализ списка имён таблиц
        
        Args:
            table_names: Список имён таблиц
            
        Returns:
            Словарь с анализом
        """
        analysis = {
            'total_tables': len(table_names),
            'quoted_tables': [],
            'unquoted_tables': [],
            'special_cases': []
        }
        
        for table_name in table_names:
            target_name = self.get_target_table_name(table_name)
            
            if self._needs_quotes(table_name):
                analysis['quoted_tables'].append({
                    'source': table_name,
                    'target': target_name,
                    'reason': self._get_quote_reason(table_name)
                })
            else:
                analysis['unquoted_tables'].append({
                    'source': table_name,
                    'target': target_name
                })
        
        return analysis
    
    def _get_quote_reason(self, table_name: str) -> str:
        """Получение причины необходимости кавычек"""
        reasons = []
        
        if any(c.isupper() for c in table_name):
            reasons.append("заглавные буквы")
        
        if re.search(r'[^a-z0-9_]', table_name, re.IGNORECASE):
            reasons.append("специальные символы")
        
        if table_name[0].isdigit():
            reasons.append("начинается с цифры")
        
        reserved_words = {
            'user', 'order', 'group', 'select', 'from', 'where', 'table'
        }
        if table_name.lower() in reserved_words:
            reasons.append("зарезервированное слово")
        
        return ", ".join(reasons) if reasons else "неизвестная причина"

def main():
    """Демонстрация работы резолвера имён таблиц"""
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    console.print("🔍 ДЕМОНСТРАЦИЯ РЕЗОЛВЕРА ИМЁН ТАБЛИЦ")
    console.print("="*60)
    
    # Создаём резолвер
    resolver = TableNameResolver("ags")
    
    # Тестовые имена таблиц
    test_tables = [
        "accnt",
        "cn", 
        "cnInvCmmAgN",
        "cn_inv_dbt",
        "cn_PrDoc",
        "user",
        "order",
        "123table",
        "table-with-dash",
        "table.with.dots"
    ]
    
    # Анализируем таблицы
    analysis = resolver.analyze_table_names(test_tables)
    
    # Создаём таблицу результатов
    result_table = Table(title="Анализ имён таблиц")
    result_table.add_column("Исходное имя", style="cyan")
    result_table.add_column("Целевое имя", style="green")
    result_table.add_column("Кавычки", style="yellow")
    result_table.add_column("Причина", style="red")
    
    for table_name in test_tables:
        target_name = resolver.get_target_table_name(table_name)
        needs_quotes = resolver._needs_quotes(table_name)
        reason = resolver._get_quote_reason(table_name) if needs_quotes else ""
        
        result_table.add_row(
            table_name,
            target_name,
            "Да" if needs_quotes else "Нет",
            reason
        )
    
    console.print(result_table)
    
    # Статистика
    console.print(f"\n📊 Статистика:")
    console.print(f"   📋 Всего таблиц: {analysis['total_tables']}")
    console.print(f"   🔤 С кавычками: {len(analysis['quoted_tables'])}")
    console.print(f"   📝 Без кавычек: {len(analysis['unquoted_tables'])}")

if __name__ == "__main__":
    main()