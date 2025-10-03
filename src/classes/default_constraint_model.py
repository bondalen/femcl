"""
DefaultConstraintModel - Модель ограничения по умолчанию
"""

from typing import Optional


class DefaultConstraintModel:
    """Модель ограничения по умолчанию"""
    
    def __init__(self, name: str, definition: str, column_id: int):
        self.id: Optional[int] = None
        self.name = name
        self.definition = definition
        self.is_system_named = False
        self.column_id = column_id
        self.source_definition = definition
        self.target_definition = ""
        self.function_mapping_rule_id: Optional[int] = None
        self.mapping_status = "pending"
        self.mapping_complexity = "simple"
        self.mapping_notes = ""
    
    def get_ddl_definition(self) -> str:
        """Генерация DDL определения ограничения"""
        if self.target_definition:
            return f"ALTER TABLE ... ADD CONSTRAINT {self.name} DEFAULT {self.target_definition}"
        else:
            return f"-- {self.name}: Не удалось маппировать определение"
    
    def validate(self) -> bool:
        """Валидация ограничения"""
        return bool(self.target_definition)
    
    def map_definition(self) -> bool:
        """Маппинг определения MS SQL в PostgreSQL"""
        # TODO: Реализовать маппинг определения
        return True
