"""
TableModel - Базовый класс для модели таблицы
Содержит общие свойства и методы для всех типов таблиц
"""

from typing import List, Optional
from datetime import datetime


class TableModel:
    """Базовый класс для модели переносимой таблицы"""
    
    def __init__(self, source_table_name: str):
        self.source_table_name = source_table_name
        self.migration_status = "pending"
        self.source_exists = False
        self.source_row_count = 0
        self.migration_duration: Optional[str] = None
        self.errors: List[str] = []
        
        # ОБЩИЕ элементы таблицы (для всех типов)
        self.columns: List['ColumnModel'] = []
        self.indexes: List['IndexModel'] = []
        self.foreign_keys: List['ForeignKeyModel'] = []
        self.unique_constraints: List['UniqueConstraintModel'] = []
        self.check_constraints: List['CheckConstraintModel'] = []
        self.triggers: List['TriggerModel'] = []
    
    def load_metadata(self, config_loader) -> bool:
        """Загрузка всех метаданных таблицы"""
        try:
            self.load_columns(config_loader)
            self.load_indexes(config_loader)
            self.load_foreign_keys()
            self.load_constraints()
            self.load_triggers()
            return True
        except Exception as e:
            self.log_error(f"Ошибка загрузки метаданных: {e}")
            return False
    
    def check_source_exists(self) -> bool:
        """Проверка существования в MS SQL"""
        # TODO: Реализовать проверку существования таблицы в MS SQL
        return True
    
    def validate_metadata(self) -> bool:
        """Валидация загруженных метаданных"""
        # TODO: Реализовать валидацию метаданных
        return True
    
    def is_ready_for_migration(self) -> bool:
        """Проверка готовности к миграции"""
        return (self.source_exists and 
                len(self.columns) > 0 and 
                self.validate_metadata())
    
    def get_migration_summary(self) -> dict:
        """Получение сводки миграции"""
        return {
            "table_name": self.source_table_name,
            "status": self.migration_status,
            "source_exists": self.source_exists,
            "source_row_count": self.source_row_count,
            "columns_count": len(self.columns),
            "indexes_count": len(self.indexes),
            "foreign_keys_count": len(self.foreign_keys),
            "errors_count": len(self.errors)
        }
    
    def log_error(self, error: str):
        """Логирование ошибок"""
        self.errors.append(f"{datetime.now()}: {error}")
    
    def update_status(self, status: str):
        """Обновление статуса"""
        self.migration_status = status
    
    # ОБЩИЕ методы для элементов таблицы
    def load_columns(self, config_loader):
        """Загрузка метаданных колонок"""
        try:
            from src.classes.column_model import ColumnModel
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
            
            # Получаем метаданные колонок
            cursor.execute("""
                SELECT 
                    pc.column_name as target_column_name,
                    mc.column_name as source_column_name,
                    pdt.typname_with_params,
                    pc.is_identity,
                    pc.ordinal_position,
                    pdt.precision_value,
                    pdt.scale_value,
                    pdt.length_value
                FROM mcl.postgres_columns pc
                JOIN mcl.postgres_tables pt ON pc.table_id = pt.id
                JOIN mcl.postgres_derived_types pdt ON pc.postgres_data_type_id = pdt.id
                JOIN mcl.mssql_columns mc ON pc.source_column_id = mc.id
                WHERE pt.object_name = %s
                ORDER BY pc.ordinal_position
            """, (self.source_table_name,))
            
            columns_data = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Создаем экземпляры ColumnModel
            self.columns = []
            for target_name, source_name, data_type, is_identity, ordinal, precision, scale, length in columns_data:
                column = ColumnModel(
                    name=target_name,
                    source_name=source_name,
                    data_type=data_type
                )
                column.is_identity = is_identity
                column.ordinal_position = ordinal
                column.data_type_precision = precision
                column.data_type_scale = scale
                column.data_type_max_length = length
                column.is_nullable = not is_identity  # Identity колонки обычно NOT NULL
                
                self.columns.append(column)
            
            return True
            
        except Exception as e:
            self.log_error(f"Ошибка загрузки колонок: {e}")
            return False
    
    def load_indexes(self, config_loader):
        """Загрузка метаданных индексов"""
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
            
            # Получаем метаданные индексов через связь с исходными индексами
            cursor.execute("""
                SELECT 
                    pi.id,
                    pi.index_name,
                    pi.original_index_name,
                    pi.index_type,
                    pi.is_unique,
                    pi.is_primary_key,
                    pi.migration_status,
                    pi.migration_date,
                    pi.error_message,
                    pi.fill_factor,
                    pi.is_concurrent,
                    pi.name_conflict_resolved,
                    pi.name_conflict_reason,
                    pi.alternative_name,
                    pi.postgres_definition,
                    pi.source_index_id
                FROM mcl.postgres_indexes pi
                WHERE pi.source_index_id IN (
                    SELECT mi.id 
                    FROM mcl.mssql_indexes mi
                    JOIN mcl.mssql_index_columns mic ON mi.id = mic.index_id
                    JOIN mcl.mssql_columns mc ON mic.column_id = mc.id
                    JOIN mcl.mssql_tables mt ON mc.table_id = mt.id
                    WHERE mt.object_name = %s
                )
                ORDER BY pi.index_name
            """, (self.source_table_name,))
            
            indexes_data = cursor.fetchall()
            
            # Получаем колонки для каждого индекса
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
                
                # Получаем колонки индекса
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
    
    def load_foreign_keys(self):
        """Загрузка метаданных внешних ключей"""
        # TODO: Реализовать загрузку внешних ключей из mcl.postgres_foreign_keys
        pass
    
    def load_constraints(self):
        """Загрузка метаданных ограничений"""
        # TODO: Реализовать загрузку ограничений из mcl.postgres_*_constraints
        pass
    
    def load_triggers(self):
        """Загрузка метаданных триггеров"""
        # TODO: Реализовать загрузку триггеров из mcl.postgres_triggers
        pass
    
    def generate_table_ddl(self) -> str:
        """Генерация DDL для создания таблицы"""
        # TODO: Реализовать генерацию DDL
        return ""
    
    def generate_indexes_ddl(self) -> List[str]:
        """Генерация DDL для индексов"""
        # TODO: Реализовать генерацию DDL для индексов
        return []
