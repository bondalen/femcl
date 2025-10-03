"""
BaseTableModel - Модель базовой таблицы с вычисляемыми колонками
Наследует от TableModel, добавляет поддержку представлений
"""

from .table_model import TableModel
from .view_model import ViewModel


class BaseTableModel(TableModel):
    """Модель базовой таблицы с вычисляемыми колонками"""
    
    def __init__(self, source_table_name: str):
        super().__init__(source_table_name)
        self.target_base_table_name = ""
        self.view_reference: ViewModel = None
    
    def generate_base_table_ddl(self) -> str:
        """Генерация DDL для базовой таблицы"""
        # TODO: Реализовать генерацию DDL для базовой таблицы
        return f"CREATE TABLE {self.target_base_table_name} (...)"
    
    def create_view(self) -> bool:
        """Создание представления"""
        if self.view_reference:
            return self.view_reference.generate_view_ddl()
        return False
    
    def separate_columns(self) -> dict:
        """Разделение колонок на базовые и вычисляемые"""
        base_columns = [col for col in self.columns if not getattr(col, 'is_computed', False)]
        computed_columns = [col for col in self.columns if getattr(col, 'is_computed', False)]
        
        return {
            "base_columns": base_columns,
            "computed_columns": computed_columns
        }
