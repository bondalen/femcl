"""
ComputedColumnModel - Модель вычисляемой колонки
"""

from typing import Optional


class ComputedColumnModel:
    """Модель вычисляемой колонки"""
    
    def __init__(self, name: str, source_expression: str, data_type: str):
        self.name = name
        self.source_expression = source_expression
        self.target_expression = ""
        self.data_type = data_type
        self.is_mapped = False
        self.function_mapping_rule_id: Optional[int] = None
        self.mapping_status = "pending"
        self.computed_mapping_confidence = 0
        self.computed_mapping_attempts = 0
        self.computed_mapping_notes = ""
    
    def get_ddl_definition(self) -> str:
        """Генерация DDL определения вычисляемой колонки"""
        if self.is_mapped and self.target_expression:
            return f"{self.name} AS ({self.target_expression})"
        else:
            return f"-- {self.name}: Не удалось маппировать выражение"
    
    def validate(self) -> bool:
        """Валидация вычисляемой колонки"""
        return self.is_mapped and bool(self.target_expression)
    
    def map_function(self) -> bool:
        """Маппинг функции MS SQL в PostgreSQL"""
        # TODO: Реализовать маппинг функции
        return True
    
    def get_mapping_status(self) -> str:
        """Получение статуса маппинга"""
        return self.mapping_status
