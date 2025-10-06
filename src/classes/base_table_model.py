"""
BaseTableModel - Модель базовой таблицы с вычисляемыми колонками
Наследует от TableModel, добавляет поддержку представлений
"""

from typing import List
from .table_model import TableModel
from .view_model import ViewModel


class BaseTableModel(TableModel):
    """Модель базовой таблицы с вычисляемыми колонками"""
    
    def __init__(self, source_table_name: str):
        super().__init__(source_table_name)
        self.target_base_table_name = ""
        # ОБЯЗАТЕЛЬНО создаем ViewModel
        self.view_reference = ViewModel(
            view_name="",  # Будет загружено из метаданных
            base_table_name=""  # Будет загружено из метаданных
        )
    
    def generate_table_ddl(self) -> str:
        """Генерация DDL для базовой таблицы и представления"""
        ddl_statements = []
        
        # 1. Генерируем DDL для базовой таблицы
        base_ddl = self.generate_base_table_ddl()
        ddl_statements.append(base_ddl)
        
        # 2. Генерируем DDL для представления
        if self.view_reference:
            view_ddl = self.view_reference.generate_view_ddl()
            ddl_statements.append(view_ddl)
        
        return "\n\n".join(ddl_statements)
    
    def generate_base_table_ddl(self) -> str:
        """Генерация DDL только для базовой таблицы"""
        # TODO: Реализовать генерацию DDL для базовой таблицы
        return f"CREATE TABLE {self.target_base_table_name} (...)"
    
    def generate_indexes_ddl(self) -> List[str]:
        """Генерация DDL для индексов базовой таблицы"""
        # TODO: Реализовать генерацию DDL для индексов
        return []
    
    def migrate_data(self) -> bool:
        """Миграция данных базовой таблицы"""
        # TODO: Реализовать миграцию данных
        return True
    
    def create_view(self) -> bool:
        """Создание представления"""
        if self.view_reference:
            return self.view_reference.generate_view_ddl()
        return False
    
    def separate_columns(self) -> dict:
        """Разделение колонок на базовые и вычисляемые"""
        base_columns = []
        computed_columns = []
        
        for col in self.columns:
            if getattr(col, 'target_type', 'both') == 'both':
                # Физическая колонка - идет в базовую таблицу
                base_columns.append(col)
            elif getattr(col, 'target_type', '') == 'view':
                # Вычисляемая колонка - идет в представление
                computed_columns.append(col)
        
        return {
            "base_columns": base_columns,
            "computed_columns": computed_columns
        }
    
    def load_metadata(self, config_loader) -> bool:
        """Загрузка всех метаданных таблицы"""
        try:
            # Вызываем родительский метод
            if not super().load_metadata(config_loader):
                return False
            
            # Загружаем метаданные представления
            self.load_view_metadata(config_loader)
            
            # Устанавливаем ссылку на базовую таблицу в представлении
            if self.view_reference:
                self.view_reference.set_base_table_model(self)
                # Загружаем вычисляемые колонки с анализом состояния функций
                self.view_reference.load_computed_columns(config_loader)
            
            return True
        except Exception as e:
            self.log_error(f"Ошибка загрузки метаданных: {e}")
            return False
    
    def load_view_metadata(self, config_loader) -> None:
        """Загрузка метаданных представления"""
        try:
            # Получаем view_name из метаданных
            view_name = self.get_view_name_from_metadata(config_loader)
            
            # Обновляем ViewModel с правильными именами
            self.view_reference.view_name = view_name
            self.view_reference.base_table_name = self.target_base_table_name
            
        except Exception as e:
            self.log_error(f"Ошибка загрузки метаданных представления: {e}")
    
    def get_view_name_from_metadata(self, config_loader) -> str:
        """Получение имени представления из метаданных"""
        try:
            import psycopg2
            
            postgres_config = config_loader.get_database_config('postgres')
            conn = psycopg2.connect(
                host=postgres_config['host'],
                port=postgres_config['port'],
                dbname=postgres_config['database'],
                user=postgres_config['user'],
                password=postgres_config['password']
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT pt.view_name
                FROM mcl.postgres_tables pt
                JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
                WHERE mt.object_name = %s AND mt.task_id = 2
            """, (self.source_table_name,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return result[0] if result else ""
            
        except Exception as e:
            self.log_error(f"Ошибка получения имени представления: {e}")
            return ""
    
    def validate_metadata(self) -> bool:
        """Валидация загруженных метаданных"""
        if not super().validate_metadata():
            return False
        
        # Проверяем, что представление создано
        if not self.view_reference:
            self.log_error("ViewModel не инициализирован для базовой таблицы")
            return False
        
        # Проверяем, что имена загружены
        if not self.view_reference.view_name:
            self.log_error("Имя представления не загружено")
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для JSON"""
        result = super().to_dict()
        
        # Добавляем информацию о представлении
        if self.view_reference:
            result['view_reference'] = {
                'view_name': self.view_reference.view_name,
                'base_table_name': self.view_reference.base_table_name,
                'computed_columns': [col.to_dict() for col in self.view_reference.computed_columns],
                'view_definition': self.view_reference.view_definition
            }
        
        return result
