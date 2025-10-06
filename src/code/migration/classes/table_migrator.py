"""
TableMigrator - Класс для выполнения миграции таблицы
"""

from typing import Optional, Dict, Any
import pyodbc
import psycopg2
import psycopg2.extensions
import time
from datetime import datetime


class TableMigrator:
    """Класс для выполнения миграции таблицы"""
    
    def __init__(self, table_name: str, config_loader, force: bool = False, verbose: bool = False):
        self.table_name = table_name
        self.config_loader = config_loader
        self.force = force
        self.verbose = verbose
        
        # Конфигурации баз данных
        self.mssql_config = config_loader.get_database_config('mssql')
        self.pg_config = config_loader.get_database_config('postgres')
        
        # Подключения
        self.mssql_conn: Optional[pyodbc.Connection] = None
        self.pg_conn: Optional[psycopg2.extensions.connection] = None
        
        # Результаты миграции
        self.migration_start_time = None
        self.migration_end_time = None
        self.rows_migrated = 0
        self.errors = []
    
    def get_mssql_connection(self) -> pyodbc.Connection:
        """Получение подключения к MS SQL"""
        if not self.mssql_conn:
            connection_string = (
                f"DRIVER={{{self.mssql_config['driver']}}};"
                f"SERVER={self.mssql_config['server']};"
                f"DATABASE={self.mssql_config['database']};"
                f"UID={self.mssql_config['user']};"
                f"PWD={self.mssql_config['password']}"
            )
            self.mssql_conn = pyodbc.connect(connection_string)
        return self.mssql_conn
    
    def get_pg_connection(self) -> psycopg2.extensions.connection:
        """Получение подключения к PostgreSQL"""
        if not self.pg_conn:
            # Убираем неподдерживаемые параметры
            pg_config_clean = {
                'host': self.pg_config['host'],
                'port': self.pg_config['port'], 
                'database': self.pg_config['database'],
                'user': self.pg_config['user'],
                'password': self.pg_config['password']
            }
            self.pg_conn = psycopg2.connect(**pg_config_clean)
        return self.pg_conn
    
    def create_table(self, table_model, force: bool = False) -> bool:
        """Создание таблицы"""
        # TODO: Реализовать создание таблицы
        return True
    
    def create_indexes(self, table_model) -> bool:
        """Создание индексов"""
        try:
            if not table_model.indexes:
                if self.verbose:
                    print(f"ℹ️ Индексы для таблицы {self.table_name} не найдены")
                return True
            
            conn = self.get_pg_connection()
            cursor = conn.cursor()
            
            created_count = 0
            failed_count = 0
            
            for index in table_model.indexes:
                try:
                    # Пропускаем индексы, которые уже созданы
                    if index.migration_status == "completed":
                        if self.verbose:
                            print(f"⏭️ Индекс {index.name} уже создан")
                        continue
                    
                    # Генерируем SQL для создания индекса
                    create_sql = index.generate_create_sql()
                    
                    if self.verbose:
                        print(f"🔨 Создаем индекс: {index.name}")
                        print(f"   SQL: {create_sql}")
                    
                    # Выполняем создание индекса
                    if index.is_concurrent:
                        # Для concurrent индексов используем CONCURRENTLY
                        concurrent_sql = create_sql.replace("CREATE ", "CREATE CONCURRENTLY ")
                        cursor.execute(concurrent_sql)
                    else:
                        cursor.execute(create_sql)
                    
                    # Обновляем статус в базе данных
                    cursor.execute("""
                        UPDATE mcl.postgres_indexes 
                        SET migration_status = 'completed', 
                            migration_date = NOW()
                        WHERE index_name = %s AND source_index_id IN (
                            SELECT mi.id 
                            FROM mcl.mssql_indexes mi
                            JOIN mcl.mssql_index_columns mic ON mi.id = mic.index_id
                            JOIN mcl.mssql_columns mc ON mic.column_id = mc.id
                            JOIN mcl.mssql_tables mt ON mc.table_id = mt.id
                            WHERE mt.object_name = %s
                        )
                    """, (index.name, self.table_name))
                    
                    conn.commit()
                    created_count += 1
                    
                    if self.verbose:
                        print(f"✅ Индекс {index.name} создан успешно")
                    
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Ошибка создания индекса {index.name}: {e}"
                    
                    # Обновляем статус ошибки в базе данных
                    try:
                        cursor.execute("""
                            UPDATE mcl.postgres_indexes 
                            SET migration_status = 'failed', 
                                error_message = %s,
                                migration_date = NOW()
                            WHERE index_name = %s AND source_index_id IN (
                                SELECT mi.id 
                                FROM mcl.mssql_indexes mi
                                JOIN mcl.mssql_index_columns mic ON mi.id = mic.index_id
                                JOIN mcl.mssql_columns mc ON mic.column_id = mc.id
                                JOIN mcl.mssql_tables mt ON mc.table_id = mt.id
                                WHERE mt.object_name = %s
                            )
                        """, (error_msg, index.name, self.table_name))
                        conn.commit()
                    except:
                        pass  # Игнорируем ошибки обновления статуса
                    
                    if self.verbose:
                        print(f"❌ {error_msg}")
                    
                    self.errors.append(error_msg)
            
            cursor.close()
            
            if self.verbose:
                print(f"📊 Создано индексов: {created_count}, ошибок: {failed_count}")
            
            return failed_count == 0
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Критическая ошибка создания индексов: {e}")
            self.errors.append(f"Критическая ошибка создания индексов: {e}")
            return False
    
    def create_foreign_keys(self, table_model) -> bool:
        """Создание внешних ключей"""
        # TODO: Реализовать создание внешних ключей
        return True
    
    def create_constraints(self, table_model) -> bool:
        """Создание ограничений"""
        # TODO: Реализовать создание ограничений
        return True
    
    def create_triggers(self, table_model) -> bool:
        """Создание триггеров"""
        # TODO: Реализовать создание триггеров
        return True
    
    def migrate_data(self, table_model) -> bool:
        """Перенос данных"""
        # TODO: Реализовать перенос данных
        return True
    
    def validate_migration(self, table_model) -> bool:
        """Валидация миграции"""
        # TODO: Реализовать валидацию миграции
        return True
    
    def migrate(self) -> Dict[str, Any]:
        """Основной метод миграции таблицы"""
        self.migration_start_time = datetime.now()
        
        try:
            if self.verbose:
                print(f"🔍 Начинаем миграцию таблицы: {self.table_name}")
            
            # Проверка существования таблицы в MS SQL
            if not self.check_source_table_exists():
                return {
                    'success': False,
                    'error': f'Таблица {self.table_name} не найдена в MS SQL Server'
                }
            
            # Получение метаданных
            metadata = self.get_table_metadata()
            if not metadata:
                return {
                    'success': False,
                    'error': f'Не удалось получить метаданные для таблицы {self.table_name}'
                }
            
            # Создание таблицы
            if not self.create_target_table(metadata):
                return {
                    'success': False,
                    'error': f'Не удалось создать целевую таблицу {self.table_name}'
                }
            
            # Перенос данных
            if not self.migrate_table_data(metadata):
                return {
                    'success': False,
                    'error': f'Не удалось перенести данные таблицы {self.table_name}'
                }
            
            # Создание индексов
            if not self.create_indexes(metadata['table_model']):
                return {
                    'success': False,
                    'error': f'Не удалось создать индексы для таблицы {self.table_name}'
                }
            
            # Валидация
            if not self.validate_migration():
                return {
                    'success': False,
                    'error': f'Валидация миграции таблицы {self.table_name} не прошла'
                }
            
            self.migration_end_time = datetime.now()
            duration = (self.migration_end_time - self.migration_start_time).total_seconds()
            
            return {
                'success': True,
                'duration': f'{duration:.2f} секунд',
                'rows_migrated': self.rows_migrated
            }
            
        except Exception as e:
            self.errors.append(str(e))
            return {
                'success': False,
                'error': f'Критическая ошибка: {e}'
            }
    
    def check_source_table_exists(self) -> bool:
        """Проверка существования таблицы в MS SQL"""
        try:
            conn = self.get_mssql_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = ?
            """, (self.table_name,))
            
            count = cursor.fetchone()[0]
            cursor.close()
            
            if self.verbose:
                print(f"✅ Таблица {self.table_name} найдена в MS SQL Server")
            
            return count > 0
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Ошибка проверки таблицы: {e}")
            return False
    
    def get_table_metadata(self) -> Optional[Dict]:
        """Получение метаданных таблицы через модель таблицы"""
        try:
            from src.classes.table_model import TableModel
            
            # Получаем информацию о наличии вычисляемых колонок
            has_computed_columns = self._check_has_computed_columns()
            
            # Создаем экземпляр модели таблицы через фабричный метод
            table_model = TableModel.create_table_model(self.table_name, has_computed_columns)
            
            # Загружаем метаданные
            if not table_model.load_metadata(self.config_loader):
                return None
            
            if self.verbose:
                print(f"📊 Найдено колонок: {len(table_model.columns)}")
            
            # Извлекаем имена колонок из модели
            source_columns = [col.source_name for col in table_model.columns]
            target_columns = [col.name for col in table_model.columns]
            
            return {
                'table_name': self.table_name,
                'table_model': table_model,
                'source_columns': source_columns,
                'target_columns': target_columns,
                'has_computed_columns': has_computed_columns
            }
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Ошибка получения метаданных: {e}")
            return None
    
    def _check_has_computed_columns(self) -> bool:
        """Проверка наличия вычисляемых колонок в таблице"""
        try:
            import psycopg2
            
            # Подключение к PostgreSQL
            conn = psycopg2.connect(
                host=self.pg_config['host'],
                port=self.pg_config['port'],
                dbname=self.pg_config['database'],
                user=self.pg_config['user'],
                password=self.pg_config['password']
            )
            cursor = conn.cursor()
            
            # Проверяем наличие вычисляемых колонок
            cursor.execute("""
                SELECT pt.has_computed_columns
                FROM mcl.postgres_tables pt
                JOIN mcl.mssql_tables mt ON pt.source_table_id = mt.id
                WHERE pt.object_name = %s AND mt.task_id = 2
            """, (self.table_name,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return result[0] if result else False
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Ошибка проверки вычисляемых колонок: {e}")
            return False
    
    def create_target_table(self, metadata: Dict) -> bool:
        """Создание целевой таблицы"""
        try:
            conn = self.get_pg_connection()
            cursor = conn.cursor()
            
            # Удаляем таблицу если force=True
            if self.force:
                cursor.execute(f"DROP TABLE IF EXISTS ags.{self.table_name} CASCADE")
                if self.verbose:
                    print(f"🗑️ Удалена существующая таблица: {self.table_name}")
            
            # Создаем таблицу используя модель
            table_model = metadata['table_model']
            columns_ddl = []
            
            for column in table_model.columns:
                # Определяем nullable для identity колонок
                nullable = "NULL" if column.is_nullable else "NOT NULL"
                # Для identity колонок добавляем GENERATED ALWAYS AS IDENTITY
                identity_clause = " GENERATED ALWAYS AS IDENTITY" if column.is_identity else ""
                columns_ddl.append(f"    {column.name} {column.data_type}{identity_clause} {nullable}")
            
            create_sql = f"""
                CREATE TABLE ags.{self.table_name} (
                    {','.join(columns_ddl)}
                )
            """
            
            cursor.execute(create_sql)
            conn.commit()
            cursor.close()
            
            if self.verbose:
                print(f"✅ Создана таблица: ags.{self.table_name}")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Ошибка создания таблицы: {e}")
            return False
    
    def migrate_table_data(self, metadata: Dict) -> bool:
        """Перенос данных таблицы"""
        try:
            mssql_conn = self.get_mssql_connection()
            pg_conn = self.get_pg_connection()
            
            # Получаем данные из MS SQL
            mssql_cursor = mssql_conn.cursor()
            pg_cursor = pg_conn.cursor()
            
            # Формируем SELECT запрос с ИСХОДНЫМИ именами колонок
            source_column_names = metadata['source_columns']
            select_sql = f"SELECT {', '.join(source_column_names)} FROM ags.{self.table_name}"
            
            mssql_cursor.execute(select_sql)
            
            # Формируем INSERT запрос с ЦЕЛЕВЫМИ именами колонок
            target_column_names = metadata['target_columns']
            insert_sql = f"INSERT INTO ags.{self.table_name} ({', '.join(target_column_names)}) OVERRIDING SYSTEM VALUE VALUES ({', '.join(['%s'] * len(target_column_names))})"
            
            # Переносим данные пакетами
            batch_size = 1000
            total_rows = 0
            
            while True:
                rows = mssql_cursor.fetchmany(batch_size)
                if not rows:
                    break
                
                # Переносим данные
                pg_cursor.executemany(insert_sql, rows)
                
                total_rows += len(rows)
                
                if self.verbose and total_rows % 5000 == 0:
                    print(f"📊 Перенесено строк: {total_rows}")
            
            pg_conn.commit()
            self.rows_migrated = total_rows
            
            mssql_cursor.close()
            pg_cursor.close()
            
            if self.verbose:
                print(f"✅ Перенесено строк: {total_rows}")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Ошибка переноса данных: {e}")
            return False
    
    def validate_migration(self) -> bool:
        """Валидация миграции"""
        try:
            mssql_conn = self.get_mssql_connection()
            pg_conn = self.get_pg_connection()
            
            # Подсчитываем строки в исходной таблице
            mssql_cursor = mssql_conn.cursor()
            mssql_cursor.execute(f"SELECT COUNT(*) FROM ags.{self.table_name}")
            source_count = mssql_cursor.fetchone()[0]
            mssql_cursor.close()
            
            # Подсчитываем строки в целевой таблице
            pg_cursor = pg_conn.cursor()
            pg_cursor.execute(f"SELECT COUNT(*) FROM ags.{self.table_name}")
            target_count = pg_cursor.fetchone()[0]
            pg_cursor.close()
            
            if self.verbose:
                print(f"📊 Исходная таблица: {source_count} строк")
                print(f"📊 Целевая таблица: {target_count} строк")
            
            if source_count == target_count:
                if self.verbose:
                    print("✅ Валидация прошла успешно")
                return True
            else:
                if self.verbose:
                    print("❌ Валидация не прошла - количество строк не совпадает")
                return False
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Ошибка валидации: {e}")
            return False
