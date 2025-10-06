"""
FunctionMappingState - Состояние функции и порядок дальнейшей работы
"""

from typing import Optional, List
import re


class FunctionMappingState:
    """Состояние функции и порядок дальнейшей работы"""
    
    def __init__(self, source_expression: str, config_loader=None):
        self.source_expression = source_expression
        self.config_loader = config_loader
        self.function_mapping_model: Optional['FunctionMappingModel'] = None
        
        # Анализируем выражение
        self.functions = self._extract_functions(source_expression)
        self.complexity = self._analyze_complexity()
        
        # Инициализируем базовые поля
        self.status = "pending"
        self.next_action = "no_action"
        self.confidence = 0
        self.notes = ""
        self.requires_manual_review = False
        
        # Проверяем метаданные и создаем состояние
        if config_loader:
            self._check_metadata_and_create_state()
    
    def _extract_functions(self, expression: str) -> List[str]:
        """Извлечение функций из выражения"""
        # Ищем все функции в выражении
        functions = re.findall(r'(\w+)\s*\(', expression)
        # Нормализуем имена функций (в нижний регистр)
        return [func.lower() for func in functions]
    
    def _analyze_complexity(self) -> str:
        """Анализ сложности выражения"""
        if len(self.functions) == 0:
            return "none"
        elif len(self.functions) == 1:
            # Проверяем сложность единственной функции
            if any(func in self.source_expression.upper() for func in ['CONVERT', 'CASE', 'SUBSTRING']):
                return "medium"
            else:
                return "simple"
        else:
            return "complex"
    
    def _check_metadata_and_create_state(self):
        """Проверка метаданных и создание правильного состояния"""
        if len(self.functions) == 0:
            self._create_no_functions_state()
        elif len(self.functions) == 1:
            self._check_single_function_metadata()
        else:
            self._create_complex_expression_state()
    
    def _create_no_functions_state(self):
        """Создание состояния для выражения без функций"""
        self.status = "no_functions"
        self.next_action = "no_action"
        self.confidence = 100
        self.notes = "Выражение не содержит функций"
        self.requires_manual_review = False
    
    def _check_single_function_metadata(self):
        """Проверка метаданных для единственной функции"""
        function_name = self.functions[0]
        
        # Проверяем, есть ли маппинг в метаданных
        mapping_model = self._load_mapping_from_metadata(function_name)
        
        if mapping_model:
            # Функция найдена в метаданных - проверяем результат
            if self._validate_mapping_result(mapping_model):
                # Маппинг корректен - создаем состояние с моделью
                self._create_with_mapping_model(mapping_model)
            else:
                # Маппинг некорректен - создаем состояние без модели
                self._create_without_mapping_model("invalid_mapping")
        else:
            # Функция не найдена в метаданных
            self._create_without_mapping_model("not_found")
    
    def _create_complex_expression_state(self):
        """Создание состояния для сложного выражения"""
        self.status = "manual_review_required"
        self.next_action = "create_manual_review_issue"
        self.confidence = 0
        self.notes = f"Сложное выражение с {len(self.functions)} функциями: {', '.join(self.functions)}"
        self.requires_manual_review = True
    
    def _load_mapping_from_metadata(self, function_name: str) -> Optional['FunctionMappingModel']:
        """Загрузка маппинга из метаданных PostgreSQL"""
        try:
            import psycopg2
            postgres_config = self.config_loader.get_database_config('postgres')
            conn = psycopg2.connect(
                host=postgres_config['host'],
                port=postgres_config['port'],
                dbname=postgres_config['database'],
                user=postgres_config['user'],
                password=postgres_config['password']
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT source_function, target_function, mapping_pattern, replacement_pattern, mapping_type, is_active
                FROM mcl.function_mapping_rules 
                WHERE source_function = %s AND is_active = true
            """, (function_name,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                from .function_mapping_model import FunctionMappingModel
                mapping = FunctionMappingModel(
                    source_function=result[0],
                    target_function=result[1],
                    mapping_type=result[4],
                    is_automatic=result[5]  # is_active
                )
                # Загружаем дополнительные поля
                mapping.mapping_pattern = result[2]
                mapping.replacement_pattern = result[3]
                return mapping
            return None
        except Exception:
            return None
    
    def _validate_mapping_result(self, mapping_model: 'FunctionMappingModel') -> bool:
        """Проверка корректности результата маппинга"""
        try:
            # Применяем маппинг
            mapped_expression = self._apply_mapping(self.source_expression, mapping_model)
            
            # Проверяем корректность
            return self._is_valid_postgres_expression(mapped_expression)
        except Exception:
            return False
    
    def _apply_mapping(self, expression: str, mapping: 'FunctionMappingModel') -> str:
        """Применение маппинга к выражению"""
        try:
            if mapping.mapping_type == "direct":
                # Простая замена функции
                return expression.replace(mapping.source_function, mapping.target_function)
            elif mapping.mapping_type == "regex":
                # Применение regex-маппинга
                if mapping.mapping_pattern and mapping.replacement_pattern:
                    # Применяем regex-замену
                    result = re.sub(mapping.mapping_pattern, mapping.replacement_pattern, expression, flags=re.IGNORECASE)
                    return result
                else:
                    # Fallback к простой замене
                    return expression.replace(mapping.source_function, mapping.target_function)
            else:
                # Неизвестный тип маппинга
                return expression
        except Exception:
            return expression
    
    def _is_valid_postgres_expression(self, expression: str) -> bool:
        """Проверка корректности PostgreSQL выражения"""
        if not expression:
            return True  # NULL допустим
        
        # Проверяем на очевидные ошибки
        if 'CAST( AS )' in expression:
            return False
        if expression.count('(') != expression.count(')'):
            return False
        if '[' in expression or ']' in expression:
            return False
        
        return True
    
    def _create_with_mapping_model(self, mapping_model: 'FunctionMappingModel'):
        """Создание состояния с объектом модели маппинга"""
        self.function_mapping_model = mapping_model
        self.status = "mapped"
        self.confidence = 90
        self.next_action = "use_mapping"
        self.notes = f"Функция {mapping_model.source_function} успешно замаппирована"
        self.requires_manual_review = False
    
    def _create_without_mapping_model(self, reason: str):
        """Создание состояния без объекта модели маппинга"""
        self.function_mapping_model = None
        
        if reason == "not_found":
            self.status = "manual_review_required"
            self.confidence = 0
            self.next_action = "create_manual_review_issue"
            self.notes = f"Функция {self.functions[0]} не найдена в метаданных"
        elif reason == "invalid_mapping":
            self.status = "manual_review_required"
            self.confidence = 0
            self.next_action = "create_manual_review_issue"
            self.notes = f"Маппинг функции {self.functions[0]} некорректен"
        elif reason == "complex_expression":
            self.status = "manual_review_required"
            self.confidence = 0
            self.next_action = "create_manual_review_issue"
            self.notes = "Сложное выражение с несколькими функциями"
        
        self.requires_manual_review = True
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для JSON"""
        return {
            'status': self.status,
            'complexity': self.complexity,
            'functions': self.functions,
            'next_action': self.next_action,
            'confidence': self.confidence,
            'notes': self.notes,
            'requires_manual_review': self.requires_manual_review,
            'function_mapping_model': self.function_mapping_model.to_dict() if self.function_mapping_model else None
        }
    
    def get_status(self) -> str:
        """Получение статуса"""
        return self.status
    
    def get_complexity(self) -> str:
        """Получение сложности"""
        return self.complexity
    
    def get_next_action(self) -> str:
        """Получение следующего действия"""
        return self.next_action
    
    def is_manual_review_required(self) -> bool:
        """Проверка необходимости ручного обзора"""
        return self.requires_manual_review

