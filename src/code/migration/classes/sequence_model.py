"""
SequenceModel - Модель последовательности PostgreSQL
"""

from typing import Optional


class SequenceModel:
    """Модель последовательности PostgreSQL"""
    
    def __init__(self, sequence_name: str, column_id: int):
        self.sequence_name = sequence_name
        self.start_value = 1
        self.increment = 1
        self.max_value: Optional[int] = None
        self.min_value: Optional[int] = None
        self.is_cycled = False
        self.is_called = False
        self.column_id = column_id
    
    def get_ddl_definition(self) -> str:
        """Генерация DDL определения последовательности"""
        definition = f"CREATE SEQUENCE {self.sequence_name}"
        
        if self.start_value != 1:
            definition += f" START WITH {self.start_value}"
        
        if self.increment != 1:
            definition += f" INCREMENT BY {self.increment}"
        
        if self.min_value is not None:
            definition += f" MINVALUE {self.min_value}"
        
        if self.max_value is not None:
            definition += f" MAXVALUE {self.max_value}"
        
        if self.is_cycled:
            definition += " CYCLE"
        
        return definition
    
    def validate(self) -> bool:
        """Валидация последовательности"""
        return bool(self.sequence_name)
    
    def create_sequence(self) -> str:
        """Создание последовательности"""
        return self.get_ddl_definition()
    
    def drop_sequence(self) -> str:
        """Удаление последовательности"""
        return f"DROP SEQUENCE IF EXISTS {self.sequence_name}"
