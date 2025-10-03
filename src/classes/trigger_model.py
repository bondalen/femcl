"""
TriggerModel - Модель триггера
"""


class TriggerModel:
    """Модель триггера"""
    
    def __init__(self, name: str, event_type: str, trigger_type: str):
        self.name = name
        self.event_type = event_type
        self.trigger_type = trigger_type
        self.function_name = ""
    
    def get_ddl_definition(self) -> str:
        """Генерация DDL определения триггера"""
        return (f"CREATE TRIGGER {self.name} "
                f"{self.trigger_type} {self.event_type} "
                f"ON ... FOR EACH ROW EXECUTE FUNCTION {self.function_name}()")
    
    def validate(self) -> bool:
        """Валидация триггера"""
        return bool(self.name) and bool(self.event_type) and bool(self.trigger_type)
