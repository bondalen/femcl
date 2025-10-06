"""
RegularTableModel - Модель обычной таблицы
Наследует от TableModel, добавляет специфичные свойства для обычных таблиц
"""

from typing import List
from .table_model import TableModel


class RegularTableModel(TableModel):
    """Модель обычной таблицы без вычисляемых колонок"""
    
    def __init__(self, source_table_name: str):
        super().__init__(source_table_name)
        self.target_table_name = ""
    
    def generate_table_ddl(self) -> str:
        """Генерация DDL для обычной таблицы"""
        # TODO: Реализовать генерацию DDL для обычной таблицы
        return f"CREATE TABLE {self.target_table_name} (...)"
    
    def generate_indexes_ddl(self) -> List[str]:
        """Генерация DDL для индексов обычной таблицы"""
        # TODO: Реализовать генерацию DDL для индексов
        return []
    
    def migrate_data(self) -> bool:
        """Миграция данных обычной таблицы"""
        # TODO: Реализовать миграцию данных
        return True
