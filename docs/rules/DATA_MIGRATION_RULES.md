# 📋 ПРАВИЛА ПЕРЕНОСА ДАННЫХ В СОЗДАННУЮ ТАБЛИЦУ

## 🎯 Назначение документа
Данный документ определяет порядок и правила переноса данных из исходной таблицы MS SQL Server в созданную таблицу PostgreSQL в рамках проекта миграции FEMCL.

---

## 🏗️ ИЕРАРХИЯ ОБЪЕКТОВ В СХЕМЕ MCL

### 📊 **Родительские таблицы (уровень 1)**
- `mssql_objects` - исходные объекты MS SQL
- `postgres_objects` - целевые объекты PostgreSQL

### 📊 **Дочерние таблицы (уровень 2)**
- `mssql_tables` - исходные таблицы MS SQL
- `postgres_tables` - целевые таблицы PostgreSQL

### 📊 **Связанные таблицы (уровень 3)**
- `mssql_columns` / `postgres_columns` - колонки
- `mssql_identity_columns` / `postgres_sequences` - identity колонки/последовательности
- `problems_tb_slt_mp` - проблемы и их решения

---

## 📋 ПОРЯДОК ПЕРЕНОСА ДАННЫХ

### 🔍 **ЭТАП 1: Проверка готовности к переносу данных**

#### 1.1 Проверка существования исходной таблицы в MS SQL
```sql
-- Проверка доступности исходной таблицы
SELECT COUNT(*) as row_count 
FROM ags.[table_name] 
WHERE 1=1;
```

**Критерии готовности:**
- ✅ Исходная таблица должна существовать в MS SQL Server
- ✅ Таблица должна содержать данные (row_count > 0)
- ✅ Подключение к MS SQL Server должно быть активным

#### 1.2 Проверка существования целевой таблицы в PostgreSQL
```sql
-- Проверка существования целевой таблицы
SELECT EXISTS (
    SELECT 1 
    FROM information_schema.tables 
    WHERE table_schema = 'ags' 
    AND table_name = '[table_name]'
) as table_exists;
```

**Критерии готовности:**
- ✅ Целевая таблица должна существовать в схеме `ags`
- ✅ Структура таблицы должна соответствовать метаданным
- ✅ Подключение к PostgreSQL должно быть активным

#### 1.3 Проверка совместимости структур
```sql
-- Сравнение количества колонок
SELECT 
    (SELECT COUNT(*) FROM mcl.mssql_columns WHERE table_id = <table_id>) as source_columns,
    (SELECT COUNT(*) FROM mcl.postgres_columns WHERE table_id = <target_table_id>) as target_columns;
```

**Критерии готовности:**
- ✅ Количество колонок должно совпадать
- ✅ Типы данных должны быть совместимы
- ✅ Identity колонки должны быть правильно настроены

### 🔍 **ЭТАП 2: Подготовка к переносу данных**

#### 2.1 Очистка целевой таблицы
```sql
-- Очистка целевой таблицы перед переносом
DELETE FROM ags.[table_name];
```

**Важные моменты:**
- ⚠️ **ВНИМАНИЕ:** Операция удаляет все существующие данные
- ✅ Выполняется только для тестовых/демонстрационных целей
- ✅ В продакшн среде может потребоваться резервное копирование

#### 2.2 Проверка identity колонок
```sql
-- Проверка настроек identity колонок
SELECT 
    column_name,
    is_identity,
    identity_start,
    identity_increment
FROM information_schema.columns 
WHERE table_schema = 'ags' 
AND table_name = '[table_name]' 
AND is_identity = 'YES';
```

**Критерии готовности:**
- ✅ Identity колонки должны быть настроены
- ✅ Последовательности должны быть созданы
- ✅ Значения должны быть совместимы

### 🔍 **ЭТАП 3: Извлечение данных из MS SQL Server**

#### 3.1 Подключение к MS SQL Server
```python
# Параметры подключения
server = os.getenv('MSSQL_SERVER', 'localhost')
port = os.getenv('MSSQL_PORT', '1433')
database = os.getenv('MSSQL_DB', 'FishEye')
username = os.getenv('MSSQL_USER', 'sa')
password = os.getenv('MSSQL_PASSWORD', 'kolob_OK1')

# Строка подключения
conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server},{port};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "TrustServerCertificate=yes;"
)
```

#### 3.2 Извлечение данных
```python
# SQL запрос для извлечения данных
query = f"SELECT * FROM ags.[table_name] ORDER BY [primary_key_column]"

# Извлечение данных с помощью pandas
df = pd.read_sql(query, mssql_connection)
```

**Критерии успешности:**
- ✅ Данные извлечены без ошибок
- ✅ Количество строк соответствует ожидаемому
- ✅ Структура данных сохранена

### 🔍 **ЭТАП 4: Загрузка данных в PostgreSQL**

#### 4.1 Подключение к PostgreSQL
```python
# Параметры подключения
host = os.getenv('POSTGRES_HOST', 'localhost')
port = os.getenv('POSTGRES_PORT', '5432')
database = os.getenv('POSTGRES_DB', 'fish_eye')
username = os.getenv('POSTGRES_USER', 'postgres')
password = os.getenv('POSTGRES_PASSWORD', 'postgres')

# Строка подключения
conn_str = f"host={host} port={port} dbname={database} user={username} password={password}"
```

#### 4.2 Загрузка данных с обработкой identity колонок
```python
# SQL запрос для вставки с OVERRIDING SYSTEM VALUE
columns = ', '.join(df.columns)
placeholders = ', '.join(['%s'] * len(df.columns))
sql = f"INSERT INTO ags.[table_name] ({columns}) OVERRIDING SYSTEM VALUE VALUES ({placeholders})"

# Выполнение вставки для каждой строки
for index, row in df.iterrows():
    values = []
    for col in df.columns:
        value = row[col]
        if pd.isna(value):
            values.append(None)
        else:
            values.append(value)
    
    cursor.execute(sql, values)
```

**Критерии успешности:**
- ✅ Все строки загружены без ошибок
- ✅ Identity колонки обработаны корректно
- ✅ NULL значения обработаны правильно

### 🔍 **ЭТАП 5: Проверка результатов переноса**

#### 5.1 Проверка количества строк
```sql
-- Подсчет строк в целевой таблице
SELECT COUNT(*) as row_count FROM ags.[table_name];
```

**Критерии успешности:**
- ✅ Количество строк должно совпадать с исходной таблицей
- ✅ Все строки должны быть загружены

#### 5.2 Проверка целостности данных
```sql
-- Проверка первых 5 строк
SELECT * FROM ags.[table_name] ORDER BY [primary_key_column] LIMIT 5;
```

**Критерии успешности:**
- ✅ Данные должны соответствовать исходным
- ✅ Типы данных должны быть корректными
- ✅ NULL значения должны быть обработаны правильно

#### 5.3 Проверка identity колонок
```sql
-- Проверка работы identity колонок
SELECT 
    MIN([identity_column]) as min_value,
    MAX([identity_column]) as max_value,
    COUNT(DISTINCT [identity_column]) as unique_count
FROM ags.[table_name];
```

**Критерии успешности:**
- ✅ Identity колонки должны работать корректно
- ✅ Значения должны быть уникальными
- ✅ Последовательность должна быть правильной

---

## 📊 КРИТЕРИИ ОЦЕНКИ УСПЕШНОСТИ ПЕРЕНОСА

### ✅ **100% УСПЕШНО**
- Все данные извлечены из MS SQL Server
- Все данные загружены в PostgreSQL
- Количество строк совпадает
- Целостность данных сохранена
- Identity колонки работают корректно
- Нет ошибок в процессе переноса

### ⚠️ **95-99% УСПЕШНО**
- Большинство данных перенесено
- Незначительные проблемы с типами данных
- Identity колонки работают с предупреждениями
- Минимальные ошибки в процессе

### ❌ **<95% УСПЕШНО**
- Значительная часть данных не перенесена
- Критические ошибки с типами данных
- Identity колонки не работают
- Множественные ошибки в процессе

---

## 🚀 АЛГОРИТМ ПЕРЕНОСА ДАННЫХ

### 1. **Инициализация**
- Проверить подключения к обеим базам данных
- Проверить существование исходной и целевой таблиц
- Проверить совместимость структур

### 2. **Подготовка**
- Очистить целевую таблицу (если необходимо)
- Проверить настройки identity колонок
- Подготовить SQL запросы

### 3. **Извлечение данных**
- Подключиться к MS SQL Server
- Выполнить SQL запрос для извлечения данных
- Сохранить данные в pandas DataFrame

### 4. **Загрузка данных**
- Подключиться к PostgreSQL
- Выполнить вставку данных с OVERRIDING SYSTEM VALUE
- Обработать NULL значения и типы данных

### 5. **Проверка результатов**
- Подсчитать количество строк
- Проверить целостность данных
- Проверить работу identity колонок

### 6. **Формирование отчета**
- Записать результаты переноса
- Зафиксировать ошибки (если есть)
- Обновить статус миграции

---

## 📋 ШАБЛОН ПЕРЕНОСА ДАННЫХ

```python
#!/usr/bin/env python3
"""
Шаблон для переноса данных таблицы
"""
import os
import sys
import pandas as pd
import pyodbc
import psycopg2
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()

def migrate_table_data(table_name):
    """Перенос данных таблицы из MS SQL в PostgreSQL"""
    
    # 1. Подключение к MS SQL Server
    mssql_conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('MSSQL_SERVER')},{os.getenv('MSSQL_PORT')};"
        f"DATABASE={os.getenv('MSSQL_DB')};"
        f"UID={os.getenv('MSSQL_USER')};"
        f"PWD={os.getenv('MSSQL_PASSWORD')};"
        "TrustServerCertificate=yes;"
    )
    
    # 2. Извлечение данных
    query = f"SELECT * FROM ags.{table_name} ORDER BY account_key"
    df = pd.read_sql(query, mssql_conn)
    console.print(f"Извлечено {len(df)} строк из MS SQL Server")
    
    # 3. Подключение к PostgreSQL
    pg_conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    # 4. Очистка целевой таблицы
    with pg_conn.cursor() as cur:
        cur.execute(f"DELETE FROM ags.{table_name}")
        pg_conn.commit()
    
    # 5. Загрузка данных
    with pg_conn.cursor() as cur:
        for index, row in df.iterrows():
            values = []
            for col in df.columns:
                value = row[col]
                if pd.isna(value):
                    values.append(None)
                else:
                    values.append(value)
            
            columns = ', '.join(df.columns)
            placeholders = ', '.join(['%s'] * len(df.columns))
            sql = f"INSERT INTO ags.{table_name} ({columns}) OVERRIDING SYSTEM VALUE VALUES ({placeholders})"
            cur.execute(sql, values)
        
        pg_conn.commit()
    
    # 6. Проверка результатов
    with pg_conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM ags.{table_name}")
        row_count = cur.fetchone()[0]
        console.print(f"Загружено {row_count} строк в PostgreSQL")
    
    # 7. Закрытие соединений
    mssql_conn.close()
    pg_conn.close()
    
    return True

if __name__ == "__main__":
    success = migrate_table_data("accnt")
    sys.exit(0 if success else 1)
```

---

## 🚨 ВАЖНЫЕ МОМЕНТЫ

### **Identity колонки:**
- **OVERRIDING SYSTEM VALUE:** Обязательно для вставки значений в identity колонки
- **Последовательности:** Должны быть созданы перед переносом данных
- **Значения:** Должны быть совместимы с исходными

### **Типы данных:**
- **NULL значения:** Обрабатываются специально (pd.isna())
- **Типы данных:** Автоматически преобразуются pandas
- **Совместимость:** Проверяется перед переносом

### **Безопасность:**
- **Очистка таблицы:** Выполняется только для тестовых целей
- **Резервное копирование:** Рекомендуется для продакшн данных
- **Транзакции:** Используются для обеспечения целостности

---

## 📞 ПОДДЕРЖКА

При возникновении вопросов по применению правил:
1. Обратитесь к примерам в отчетах проекта
2. Проверьте совместимость типов данных
3. Убедитесь в корректности identity колонок

---

*Документ создан: 2025-01-27*  
*Версия: 1.0*  
*Статус: АКТУАЛЬНЫЙ*