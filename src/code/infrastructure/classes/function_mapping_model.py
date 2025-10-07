"""
FunctionMappingModel - Модель правил маппинга функций
"""

from typing import Optional


class FunctionMappingModel:
    """Модель правил маппинга функций MS SQL в PostgreSQL"""
    
    def __init__(self, source_function: str, target_function: str, mapping_type: str = "automatic", is_automatic: bool = True):
        self.id: Optional[int] = None
        self.source_function = source_function
        self.target_function = target_function
        self.mapping_pattern = ""
        self.replacement_pattern = ""
        self.mapping_type = mapping_type
        self.complexity_level = 1
        self.applicable_objects = ""
        self.description = ""
        self.examples = ""
        self.is_active = True
        self.is_automatic = is_automatic
        self.is_semi_automatic = False
        self.is_manual = False
    
    def get_mapping(self) -> dict:
        """Получение правила маппинга"""
        return {
            "source": self.source_function,
            "target": self.target_function,
            "pattern": self.mapping_pattern,
            "replacement": self.replacement_pattern,
            "type": self.mapping_type
        }
    
    def validate_mapping(self) -> bool:
        """Валидация правила маппинга"""
        return (bool(self.source_function) and 
                bool(self.target_function) and 
                bool(self.mapping_pattern) and 
                bool(self.replacement_pattern))
    
    def map_function(self, source_code: str) -> str:
        """Применение маппинга к исходному коду"""
        # TODO: Реализовать применение маппинга
        return source_code
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для JSON"""
        return {
            'id': self.id,
            'source_function': self.source_function,
            'target_function': self.target_function,
            'mapping_pattern': self.mapping_pattern,
            'replacement_pattern': self.replacement_pattern,
            'mapping_type': self.mapping_type,
            'complexity_level': self.complexity_level,
            'applicable_objects': self.applicable_objects,
            'description': self.description,
            'examples': self.examples,
            'is_active': self.is_active,
            'is_automatic': self.is_automatic,
            'is_semi_automatic': self.is_semi_automatic,
            'is_manual': self.is_manual
        }
