"""
IndexColumnModel - Модель для представления колонки индекса
"""

from typing import Optional


class IndexColumnModel:
    """Модель для представления колонки в индексе"""
    
    def __init__(self, index_name: str, column_name: str, ordinal_position: int, is_descending: bool = False):
        self.index_name = index_name
        self.column_name = column_name
        self.ordinal_position = ordinal_position
        self.is_descending = is_descending
        
        # Дополнительные свойства
        self.column_id: Optional[int] = None
        self.index_id: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для JSON"""
        return {
            'index_name': self.index_name,
            'column_name': self.column_name,
            'ordinal_position': self.ordinal_position,
            'is_descending': self.is_descending
        }
    
    def __str__(self) -> str:
        direction = "DESC" if self.is_descending else "ASC"
        return f"IndexColumnModel({self.column_name} {direction}, pos={self.ordinal_position})"

