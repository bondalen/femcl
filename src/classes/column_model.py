"""
ColumnModel - Модель колонки таблицы
"""

from typing import Optional


class ColumnModel:
    """Модель колонки таблицы"""
    
    def __init__(self, name: str, source_name: str, data_type: str):
        self.name = name
        self.source_name = source_name
        self.data_type = data_type
        self.data_type_precision: Optional[int] = None
        self.data_type_scale: Optional[int] = None
        self.data_type_max_length: Optional[int] = None
        self.is_nullable = True
        self.is_identity = False
        self.default_value: Optional[str] = None
        self.ordinal_position = 0
    
    def get_ddl_definition(self) -> str:
        """Генерация DDL определения колонки"""
        definition = f"{self.name} {self.data_type}"
        
        if self.data_type_precision is not None:
            if self.data_type_scale is not None:
                definition += f"({self.data_type_precision},{self.data_type_scale})"
            else:
                definition += f"({self.data_type_precision})"
        elif self.data_type_max_length is not None:
            definition += f"({self.data_type_max_length})"
        
        if not self.is_nullable:
            definition += " NOT NULL"
        
        if self.default_value:
            definition += f" DEFAULT {self.default_value}"
        
        return definition
    
    def validate(self) -> bool:
        """Валидация колонки"""
        # TODO: Реализовать валидацию колонки
        return True
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для JSON"""
        return {
            'name': self.name,
            'source_name': self.source_name,
            'data_type': self.data_type,
            'data_type_precision': self.data_type_precision,
            'data_type_scale': self.data_type_scale,
            'data_type_max_length': self.data_type_max_length,
            'is_nullable': self.is_nullable,
            'is_identity': self.is_identity,
            'default_value': self.default_value,
            'ordinal_position': self.ordinal_position
        }