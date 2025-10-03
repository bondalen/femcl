"""
UniqueConstraintModel - Модель уникального ограничения
"""

from typing import List


class UniqueConstraintModel:
    """Модель уникального ограничения"""
    
    def __init__(self, name: str):
        self.name = name
        self.columns: List[str] = []
    
    def get_ddl_definition(self) -> str:
        """Генерация DDL определения уникального ограничения"""
        return f"ALTER TABLE ... ADD CONSTRAINT {self.name} UNIQUE ({', '.join(self.columns)})"
    
    def validate(self) -> bool:
        """Валидация уникального ограничения"""
        return bool(self.name) and len(self.columns) > 0
