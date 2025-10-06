#!/bin/bash

# Скрипт реорганизации структуры проекта FEMCL
# Создает новую структуру папок и перемещает файлы

set -e  # Остановка при ошибке

echo "🏗️ Начинаю реорганизацию структуры проекта FEMCL..."

# Создание новой структуры папок
echo "📁 Создаю новую структуру папок..."

# Создаем папку code
mkdir -p src/code

# Создаем модули
mkdir -p src/code/metadata/classes
mkdir -p src/code/metadata/scripts
mkdir -p src/code/migration/classes
mkdir -p src/code/migration/scripts
mkdir -p src/code/infrastructure/classes
mkdir -p src/code/infrastructure/config

# Создаем __init__.py файлы
touch src/code/__init__.py
touch src/code/metadata/__init__.py
touch src/code/metadata/classes/__init__.py
touch src/code/metadata/scripts/__init__.py
touch src/code/migration/__init__.py
touch src/code/migration/classes/__init__.py
touch src/code/migration/scripts/__init__.py
touch src/code/infrastructure/__init__.py
touch src/code/infrastructure/classes/__init__.py
touch src/code/infrastructure/config/__init__.py

echo "✅ Структура папок создана"

# Перемещение файлов
echo "📦 Перемещаю файлы..."

# Модуль migration - основные классы миграции
mv src/classes/table_migrator.py src/code/migration/classes/
mv src/classes/table_model.py src/code/migration/classes/
mv src/classes/regular_table_model.py src/code/migration/classes/
mv src/classes/base_table_model.py src/code/migration/classes/
mv src/classes/view_model.py src/code/migration/classes/

# Модуль migration - модели элементов данных
mv src/classes/column_model.py src/code/migration/classes/
mv src/classes/computed_column_model.py src/code/migration/classes/
mv src/classes/index_model.py src/code/migration/classes/
mv src/classes/index_column_model.py src/code/migration/classes/
mv src/classes/foreign_key_model.py src/code/migration/classes/
mv src/classes/unique_constraint_model.py src/code/migration/classes/
mv src/classes/check_constraint_model.py src/code/migration/classes/
mv src/classes/default_constraint_model.py src/code/migration/classes/
mv src/classes/trigger_model.py src/code/migration/classes/
mv src/classes/sequence_model.py src/code/migration/classes/

# Модуль infrastructure - маппинг функций
mv src/classes/function_mapping_model.py src/code/infrastructure/classes/
mv src/classes/function_mapping_state.py src/code/infrastructure/classes/

# Скрипты миграции
mv src/scripts/migrate_table.py src/code/migration/scripts/

# Конфигурация
mv config/config_loader.py src/code/infrastructure/config/
mv config/config.yaml src/code/infrastructure/config/
mv config/README.md src/code/infrastructure/config/

echo "✅ Файлы перемещены"

# Удаление старых папок (если пустые)
echo "🧹 Очищаю старые папки..."

# Удаляем старые папки classes и scripts
rm -rf src/classes
rm -rf src/scripts

# Удаляем старую папку config (если пустая)
if [ -d "config" ] && [ -z "$(ls -A config)" ]; then
    rm -rf config
fi

echo "✅ Старые папки удалены"

# Создание заглушек для планируемых файлов
echo "📝 Создаю заглушки для планируемых файлов..."

# Модуль metadata - планируемые файлы
cat > src/code/metadata/classes/analyzer.py << 'EOF'
"""
Модуль анализа структуры исходной БД MS SQL Server
Планируется к реализации
"""

class Analyzer:
    """Анализатор структуры БД MS SQL Server"""
    
    def __init__(self):
        pass
    
    def scan_database(self):
        """Сканирование структуры БД"""
        pass
EOF

cat > src/code/metadata/classes/transformer.py << 'EOF'
"""
Модуль трансформации метаданных MS SQL → PostgreSQL
Планируется к реализации
"""

class Transformer:
    """Трансформатор метаданных"""
    
    def __init__(self):
        pass
    
    def transform_metadata(self):
        """Трансформация метаданных"""
        pass
EOF

cat > src/code/metadata/classes/writer.py << 'EOF'
"""
Модуль записи метаданных в схему mcl
Планируется к реализации
"""

class Writer:
    """Записыватель метаданных в БД"""
    
    def __init__(self):
        pass
    
    def write_metadata(self):
        """Запись метаданных в схему mcl"""
        pass
EOF

cat > src/code/metadata/scripts/generate_metadata.py << 'EOF'
#!/usr/bin/env python3
"""
Скрипт генерации метаданных для миграции
Планируется к реализации
"""

if __name__ == "__main__":
    print("Генерация метаданных - планируется к реализации")
EOF

# Модуль infrastructure - планируемые файлы
cat > src/code/infrastructure/classes/connection_manager.py << 'EOF'
"""
Менеджер подключений к БД
Планируется к реализации
"""

class ConnectionManager:
    """Менеджер подключений к БД"""
    
    def __init__(self):
        pass
    
    def get_mssql_connection(self):
        """Получение подключения к MS SQL Server"""
        pass
    
    def get_postgresql_connection(self):
        """Получение подключения к PostgreSQL"""
        pass
EOF

echo "✅ Заглушки созданы"

echo "🎉 Реорганизация завершена!"
echo ""
echo "📋 Новая структура:"
echo "src/"
echo "├── ai-rules/                    # Правила AI (без изменений)"
echo "└── code/                        # Весь код системы"
echo "    ├── metadata/                # МОДУЛЬ 1: Формирование метаданных (planned)"
echo "    │   ├── classes/             # Анализатор, Трансформатор, Записыватель"
echo "    │   └── scripts/             # generate_metadata.py"
echo "    ├── migration/               # МОДУЛЬ 2: Перенос данных (implemented)"
echo "    │   ├── classes/             # Все классы миграции"
echo "    │   └── scripts/             # migrate_table.py"
echo "    └── infrastructure/          # МОДУЛЬ 3: Инфраструктура (implemented)"
echo "        ├── classes/              # ConnectionManager, FunctionMapping*"
echo "        └── config/               # ConfigLoader, config.yaml"
echo ""
echo "⚠️  Следующий шаг: обновить импорты в файлах!"
