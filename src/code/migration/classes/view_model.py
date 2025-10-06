"""
ViewModel - Модель представления для вычисляемых колонок
"""

from typing import List
from .computed_column_model import ComputedColumnModel
from .function_mapping_model import FunctionMappingModel


class ViewModel:
    """Модель представления для вычисляемых колонок"""
    
    def __init__(self, view_name: str, base_table_name: str):
        self.view_name = view_name
        self.base_table_name = base_table_name
        self.computed_columns: List[ComputedColumnModel] = []
        # Убираем function_mappings - это теперь ответственность колонок
        self.view_definition = ""
        # Добавляем ссылку на базовую таблицу для доступа к колонкам
        self.base_table_model = None
    
    def set_base_table_model(self, base_table_model):
        """Установка ссылки на базовую таблицу"""
        self.base_table_model = base_table_model
    
    def load_computed_columns(self, config_loader=None):
        """Загрузка вычисляемых колонок"""
        if not self.base_table_model:
            return
        
        # Получаем вычисляемые колонки из базовой таблицы
        columns_info = self.base_table_model.separate_columns()
        computed_columns = columns_info["computed_columns"]
        
        # Создаем ComputedColumnModel для каждой вычисляемой колонки
        from .computed_column_model import ComputedColumnModel
        
        self.computed_columns = []
        for col in computed_columns:
            computed_col = ComputedColumnModel(
                name=col.name,
                source_expression=getattr(col, 'computed_definition', ''),
                data_type=col.data_type
            )
            
            # Анализируем состояние функции с проверкой метаданных
            if config_loader:
                function_state = computed_col.analyze_function_state(config_loader)
                # function_state автоматически проверит метаданные и создаст правильное состояние
            else:
                # Без config_loader - устанавливаем базовые значения
                computed_col.mapping_status = 'pending'
                computed_col.computed_mapping_notes = 'Требуется анализ состояния функции'
            
            self.computed_columns.append(computed_col)
    
    def load_function_mappings(self, config_loader) -> None:
        """Загрузка маппингов функций для всех вычисляемых колонок"""
        # Маппинги уже загружены в load_computed_columns через analyze_function_state
        # Этот метод оставлен для совместимости
        pass
    
    def generate_view_ddl(self) -> str:
        """Генерация DDL для представления с базовыми и вычисляемыми колонками"""
        if not self.base_table_model:
            raise ValueError("Базовая таблица не установлена")
        
        # Разделяем колонки
        columns_info = self.base_table_model.separate_columns()
        base_columns = columns_info["base_columns"]
        computed_columns = columns_info["computed_columns"]
        
        # Формируем SELECT clause
        select_parts = []
        
        # 1. Добавляем все базовые колонки
        for col in base_columns:
            select_parts.append(f'    "{col.name}"')
        
        # 2. Добавляем вычисляемые колонки
        for col in computed_columns:
            if hasattr(col, 'postgres_computed_definition') and col.postgres_computed_definition:
                select_parts.append(f'    {col.postgres_computed_definition} AS "{col.name}"')
            else:
                # Если определение не замаппировано, используем NULL
                select_parts.append(f'    NULL AS "{col.name}"')
        
        select_clause = ',\n'.join(select_parts)
        
        return f'''CREATE OR REPLACE VIEW ags."{self.view_name}" AS
SELECT
{select_clause}
FROM ags."{self.base_table_name}";'''
    
    def validate_functions(self) -> bool:
        """Валидация функций в представлении"""
        # TODO: Реализовать валидацию функций
        return True
    
    def map_mssql_to_postgres_functions(self) -> bool:
        """Оркестрация маппинга функций для всех вычисляемых колонок"""
        all_mapped = True
        for col in self.computed_columns:
            if not col.map_function():
                all_mapped = False
                print(f"❌ Не удалось замаппировать колонку '{col.name}': {col.mapping_status}")
        return all_mapped
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для JSON"""
        return {
            'view_name': self.view_name,
            'base_table_name': self.base_table_name,
            'computed_columns': [col.to_dict() for col in self.computed_columns],
            'view_definition': self.view_definition
        }
