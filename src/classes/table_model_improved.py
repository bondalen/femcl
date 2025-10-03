"""
TableModel - Улучшенная версия с использованием представления для индексов
"""

from typing import List, Optional
from datetime import datetime


class TableModelImproved:
    """Улучшенная модель таблицы с оптимизированной загрузкой индексов"""
    
    def __init__(self, source_table_name: str):
        self.source_table_name = source_table_name
        self.migration_status = "pending"
        self.source_exists = False
        self.source_row_count = 0
        self.migration_duration: Optional[str] = None
        self.errors: List[str] = []
        
        # Элементы таблицы
        self.columns: List['ColumnModel'] = []
        self.indexes: List['IndexModel'] = []
        self.foreign_keys: List['ForeignKeyModel'] = []
        self.unique_constraints: List['UniqueConstraintModel'] = []
        self.check_constraints: List['CheckConstraintModel'] = []
        self.triggers: List['TriggerModel'] = []
    
    def load_indexes_improved(self, config_loader):
        """Улучшенная загрузка индексов с использованием представления"""
        try:
            from src.classes.index_model import IndexModel
            import psycopg2
            
            # Получаем конфигурацию PostgreSQL
            pg_config = config_loader.get_database_config('postgres')
            pg_config_clean = {
                'host': pg_config['host'],
                'port': pg_config['port'], 
                'database': pg_config['database'],
                'user': pg_config['user'],
                'password': pg_config['password']
            }
            
            # Подключаемся к PostgreSQL
            conn = psycopg2.connect(**pg_config_clean)
            cursor = conn.cursor()
            
            # Упрощенный запрос с использованием представления
            cursor.execute("""
                SELECT 
                    index_id,
                    index_name,
                    original_index_name,
                    index_type,
                    is_unique,
                    is_primary_key,
                    migration_status,
                    migration_date,
                    error_message,
                    fill_factor,
                    is_concurrent,
                    name_conflict_resolved,
                    name_conflict_reason,
                    alternative_name,
                    postgres_definition,
                    source_index_id
                FROM mcl.v_postgres_indexes_by_table
                WHERE table_name = %s
                ORDER BY index_name
            """, (self.source_table_name,))
            
            indexes_data = cursor.fetchall()
            
            # Создаем модели индексов
            self.indexes = []
            for index_row in indexes_data:
                index_id = index_row[0]
                index_name = index_row[1]
                
                # Создаем модель индекса
                index = IndexModel(
                    name=index_name,
                    table_name=self.source_table_name
                )
                
                # Заполняем свойства
                index.original_name = index_row[2]
                index.index_type = index_row[3] or "btree"
                index.is_unique = index_row[4] or False
                index.is_primary_key = index_row[5] or False
                index.migration_status = index_row[6] or "pending"
                index.migration_date = index_row[7]
                index.error_message = index_row[8]
                index.fill_factor = index_row[9] or 90
                index.is_concurrent = index_row[10] or False
                index.name_conflict_resolved = index_row[11] or False
                index.name_conflict_reason = index_row[12]
                index.alternative_name = index_row[13]
                index.postgres_definition = index_row[14]
                index.source_index_id = index_row[15]
                
                # Получаем колонки индекса (упрощенный запрос)
                cursor.execute("""
                    SELECT 
                        pc.column_name,
                        pic.ordinal_position,
                        pic.is_descending
                    FROM mcl.postgres_index_columns pic
                    JOIN mcl.postgres_columns pc ON pic.column_id = pc.id
                    WHERE pic.index_id = %s
                    ORDER BY pic.ordinal_position
                """, (index_id,))
                
                columns_data = cursor.fetchall()
                for col_name, ordinal, is_desc in columns_data:
                    index.add_column(col_name, ordinal, is_desc)
                
                self.indexes.append(index)
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            self.log_error(f"Ошибка загрузки индексов: {e}")
            return False
    
    def log_error(self, error: str):
        """Логирование ошибок"""
        self.errors.append(f"{datetime.now()}: {error}")
    
    def get_indexes_summary(self) -> dict:
        """Получение сводки по индексам"""
        return {
            "total_indexes": len(self.indexes),
            "unique_indexes": len([idx for idx in self.indexes if idx.is_unique]),
            "primary_keys": len([idx for idx in self.indexes if idx.is_primary_key]),
            "completed_indexes": len([idx for idx in self.indexes if idx.migration_status == "completed"]),
            "pending_indexes": len([idx for idx in self.indexes if idx.migration_status == "pending"]),
            "failed_indexes": len([idx for idx in self.indexes if idx.migration_status == "failed"])
        }