"""
CheckConstraintModel - Модель check ограничения
"""

from typing import Optional


class CheckConstraintModel:
    """Модель check ограничения"""
    
    def __init__(self, name: str, check_clause: str):
        self.id: Optional[int] = None
        self.name = name
        self.check_clause = check_clause
        self.column_name: Optional[str] = None
        self.function_mapping_rule_id: Optional[int] = None
        self.mapping_status = "pending"
        self.mapping_complexity = "simple"
        self.mapping_notes = ""
    
    def get_ddl_definition(self) -> str:
        """Генерация DDL определения check ограничения"""
        return f"ALTER TABLE ... ADD CONSTRAINT {self.name} CHECK ({self.check_clause})"
    
    def validate(self) -> bool:
        """Валидация check ограничения"""
        return bool(self.name) and bool(self.check_clause)
