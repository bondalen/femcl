"""
IndexModel - Модель для представления индекса
"""

from typing import List, Optional
from datetime import datetime


class IndexModel:
    """Модель для представления индекса таблицы"""
    
    def __init__(self, name: str, table_name: str):
        self.name = name
        self.table_name = table_name
        self.original_name: Optional[str] = None
        self.index_type: str = "btree"
        self.is_unique: bool = False
        self.is_primary_key: bool = False
        self.migration_status: str = "pending"
        self.migration_date: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.fill_factor: int = 90
        self.is_concurrent: bool = False
        self.name_conflict_resolved: bool = False
        self.name_conflict_reason: Optional[str] = None
        self.alternative_name: Optional[str] = None
        
        # Колонки индекса
        self.columns: List['IndexColumnModel'] = []
        
        # PostgreSQL определение
        self.postgres_definition: Optional[str] = None
        
        # Связи с исходными данными
        self.source_index_id: Optional[int] = None
        self.table_id: Optional[int] = None
    
    def add_column(self, column_name: str, ordinal_position: int, is_descending: bool = False):
        """Добавление колонки в индекс"""
        from src.classes.index_column_model import IndexColumnModel
        
        column = IndexColumnModel(
            index_name=self.name,
            column_name=column_name,
            ordinal_position=ordinal_position,
            is_descending=is_descending
        )
        self.columns.append(column)
    
    def get_columns_sql(self) -> str:
        """Получение SQL для колонок индекса"""
        columns_sql = []
        for col in sorted(self.columns, key=lambda x: x.ordinal_position):
            direction = "DESC" if col.is_descending else "ASC"
            columns_sql.append(f"{col.column_name} {direction}")
        return ", ".join(columns_sql)
    
    def generate_create_sql(self) -> str:
        """Генерация SQL для создания индекса"""
        if not self.columns:
            raise ValueError(f"Индекс {self.name} не содержит колонок")
        
        # Определяем тип индекса
        index_type_clause = ""
        if self.index_type != "btree":
            index_type_clause = f" USING {self.index_type}"
        
        # Определяем уникальность
        unique_clause = "UNIQUE " if self.is_unique else ""
        
        # Определяем имя индекса
        index_name = self.alternative_name if self.alternative_name else self.name
        
        # Определяем схему
        schema_name = "ags"  # Целевая схема
        
        # Генерируем SQL
        sql = f"""CREATE {unique_clause}INDEX {index_name} ON {schema_name}.{self.table_name}{index_type_clause} ({self.get_columns_sql()})"""
        
        # Добавляем параметры
        if self.fill_factor != 90:
            sql += f" WITH (fillfactor={self.fill_factor})"
        
        return sql
    
    def validate(self) -> bool:
        """Валидация индекса"""
        if not self.name:
            return False
        if not self.columns:
            return False
        if self.index_type not in ["btree", "hash", "gist", "spgist", "gin", "brin"]:
            return False
        return True
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для JSON"""
        return {
            'name': self.name,
            'table_name': self.table_name,
            'index_type': self.index_type,
            'is_unique': self.is_unique,
            'is_primary_key': self.is_primary_key,
            'fill_factor': self.fill_factor,
            'columns': [col.to_dict() for col in self.columns],
            'postgres_definition': self.postgres_definition,
            'source_index_id': self.source_index_id,
            'table_id': self.table_id
        }
    
    def __str__(self) -> str:
        return f"IndexModel(name={self.name}, table={self.table_name}, columns={len(self.columns)})"