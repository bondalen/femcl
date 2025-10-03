"""
ForeignKeyModel - Модель внешнего ключа
"""

from typing import List


class ForeignKeyModel:
    """Модель внешнего ключа"""
    
    def __init__(self, name: str):
        self.name = name
        self.columns: List[str] = []
        self.referenced_table = ""
        self.referenced_columns: List[str] = []
        self.delete_action = "NO ACTION"
        self.update_action = "NO ACTION"
    
    def get_ddl_definition(self) -> str:
        """Генерация DDL определения внешнего ключа"""
        return (f"ALTER TABLE ... ADD CONSTRAINT {self.name} "
                f"FOREIGN KEY ({', '.join(self.columns)}) "
                f"REFERENCES {self.referenced_table} ({', '.join(self.referenced_columns)}) "
                f"ON DELETE {self.delete_action} ON UPDATE {self.update_action}")
    
    def validate(self) -> bool:
        """Валидация внешнего ключа"""
        return (bool(self.name) and 
                len(self.columns) > 0 and 
                bool(self.referenced_table) and 
                len(self.referenced_columns) > 0)
