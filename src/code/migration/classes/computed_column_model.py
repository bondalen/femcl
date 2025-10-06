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
        # Колонка сама управляет своим маппингом
        self.function_mapping: Optional['FunctionMappingModel'] = None
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
    
    def analyze_function_state(self, config_loader) -> 'FunctionMappingState':
        """Анализ состояния функции с проверкой метаданных"""
        from .function_mapping_state import FunctionMappingState
        
        # Создаем состояние с проверкой метаданных
        function_state = FunctionMappingState(self.source_expression, config_loader)
        
        # Устанавливаем состояние
        self.function_mapping = function_state
        self.mapping_status = function_state.status
        self.computed_mapping_confidence = function_state.confidence
        self.computed_mapping_notes = function_state.notes
        
        return function_state
    
    def map_function(self) -> bool:
        """Маппинг функции MS SQL в PostgreSQL"""
        if not self.function_mapping:
            self.mapping_status = "no_mapping_loaded"
            return False
        
        if self.function_mapping.requires_manual_review:
            self.mapping_status = "manual_review_required"
            return False
        
        if self.function_mapping.function_mapping_model:
            try:
                # Применяем маппинг к выражению
                self.target_expression = self.function_mapping._apply_mapping(
                    self.source_expression, 
                    self.function_mapping.function_mapping_model
                )
                self.is_mapped = True
                self.mapping_status = "mapped"
                return True
            except Exception as e:
                self.mapping_status = f"mapping_error: {e}"
                return False
        else:
            self.mapping_status = "no_mapping_model"
            return False
    
    def get_mapping_status(self) -> str:
        """Получение статуса маппинга"""
        return self.mapping_status
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для JSON"""
        return {
            'name': self.name,
            'source_expression': self.source_expression,
            'target_expression': self.target_expression,
            'data_type': self.data_type,
            'is_mapped': self.is_mapped,
            'function_mapping': self.function_mapping.to_dict() if self.function_mapping else None,
            'mapping_status': self.mapping_status,
            'computed_mapping_confidence': self.computed_mapping_confidence,
            'computed_mapping_attempts': self.computed_mapping_attempts,
            'computed_mapping_notes': self.computed_mapping_notes
        }
