"""
TableModel - Оптимизированная версия с прямыми связями
"""

from typing import List, Optional
from datetime import datetime


class TableModelOptimized:
    """Оптимизированная модель таблицы с прямыми связями"""
    
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
    
    def load_indexes_optimized(self, config_loader):
        """Оптимизированная загрузка индексов с прямыми связями"""
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
            
            # УПРОЩЕННЫЙ запрос с прямыми связями
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
                JOIN mcl.postgres_tables pt ON pi.table_id = pt.id
                WHERE pt.object_name = %s
                ORDER BY pi.index_name
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
    
    def verify_index_consistency(self, config_loader):
        """Проверка согласованности индексов между MS SQL и PostgreSQL"""
        try:
            import psycopg2
            
            pg_config = config_loader.get_database_config('postgres')
            pg_config_clean = {
                'host': pg_config['host'],
                'port': pg_config['port'], 
                'database': pg_config['database'],
                'user': pg_config['user'],
                'password': pg_config['password']
            }
            
            conn = psycopg2.connect(**pg_config_clean)
            cursor = conn.cursor()
            
            # ИСПРАВЛЕННАЯ проверка соответствия индексов
            cursor.execute("""
                SELECT 
                    mi.id as mssql_index_id,
                    mi.index_name as mssql_index_name,
                    mi.table_id as mssql_table_id,
                    pi.id as postgres_index_id,
                    pi.index_name as postgres_index_name,
                    pi.table_id as postgres_table_id,
                    pi.source_index_id,
                    pt.source_table_id as postgres_source_table_id,
                    CASE 
                        WHEN mi.id = pi.source_index_id THEN '✅'
                        ELSE '❌'
                    END as source_match,
                    CASE 
                        WHEN mi.table_id = pt.source_table_id THEN '✅'
                        ELSE '❌'
                    END as table_match
                FROM mcl.mssql_indexes mi
                JOIN mcl.postgres_indexes pi ON mi.id = pi.source_index_id
                JOIN mcl.mssql_tables mt ON mi.table_id = mt.id
                JOIN mcl.postgres_tables pt ON pi.table_id = pt.id
                WHERE mt.object_name = %s AND pt.object_name = %s
                ORDER BY mi.index_name
            """, (self.source_table_name, self.source_table_name))
            
            consistency_results = cursor.fetchall()
            
            print(f"🔍 Проверка согласованности для таблицы {self.source_table_name}:")
            print(f"   Найдено связей: {len(consistency_results)}")
            
            all_consistent = True
            for result in consistency_results:
                mssql_id, mssql_name, mssql_table_id, pg_id, pg_name, pg_table_id, source_id, pg_source_table_id, source_match, table_match = result
                
                print(f"\n   Индекс: {mssql_name} -> {pg_name}")
                print(f"     MS SQL ID: {mssql_id}, table_id: {mssql_table_id}")
                print(f"     PG ID: {pg_id}, table_id: {pg_table_id}")
                print(f"     Source ID: {source_id} {source_match}")
                print(f"     PG source_table_id: {pg_source_table_id}")
                print(f"     Table ID: {table_match}")
                
                if source_match == '❌' or table_match == '❌':
                    all_consistent = False
            
            cursor.close()
            conn.close()
            
            if all_consistent:
                print(f"\n✅ Все связи согласованы для таблицы {self.source_table_name}")
            else:
                print(f"\n❌ Найдены несогласованности для таблицы {self.source_table_name}")
            
            return all_consistent
            
        except Exception as e:
            self.log_error(f"Ошибка проверки согласованности: {e}")
            return False