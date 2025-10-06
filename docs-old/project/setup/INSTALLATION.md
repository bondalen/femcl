# 🛠️ ИНСТРУКЦИИ ПО УСТАНОВКЕ FEMCL

## 📋 Системные требования

- **ОС:** Fedora 42
- **PostgreSQL:** 16.x
- **Python:** 3.11+
- **Git:** 2.40+

## 🚀 Установка зависимостей

### 1. Обновление системы
```bash
sudo dnf update -y
```

### 2. Установка PostgreSQL
```bash
# Установка PostgreSQL
sudo dnf install postgresql postgresql-server postgresql-contrib

# Инициализация базы данных
sudo postgresql-setup --initdb

# Запуск службы
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Проверка статуса
sudo systemctl status postgresql
```

### 3. Настройка PostgreSQL
```bash
# Переключение на пользователя postgres
sudo -u postgres psql

# Создание пользователя alex
CREATE USER alex WITH SUPERUSER CREATEDB CREATEROLE;

# Создание базы данных Fish_Eye
CREATE DATABASE "Fish_Eye" OWNER alex;

# Выход из psql
\q
```

### 4. Установка Python зависимостей
```bash
# Установка pip (если не установлен)
sudo dnf install python3-pip

# Установка зависимостей
pip install psycopg2-binary pandas sqlalchemy python-dotenv

# Или из requirements.txt
pip install -r requirements.txt
```

### 5. Дополнительные инструменты
```bash
# Git
sudo dnf install git

# PlantUML для диаграмм
sudo dnf install plantuml

# Дополнительные утилиты
sudo dnf install curl wget unzip
```

## 🔧 Настройка проекта

### 1. Клонирование репозитория
```bash
# Клонирование репозитория
git clone https://github.com/bondalen/femcl.git
cd femcl

# Или через SSH (если настроен)
git clone git@github.com:bondalen/femcl.git
```

### 2. Настройка переменных окружения
```bash
# Копирование примера конфигурации
cp .env.example .env

# Редактирование конфигурации
nano .env
```

### 3. Содержимое .env файла
```bash
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=Fish_Eye
POSTGRES_USER=alex
POSTGRES_PASSWORD=your_password

# Database URI
DATABASE_URI=postgresql://alex:your_password@localhost:5432/Fish_Eye

# Migration Configuration
MIGRATION_TASK_ID=2
MIGRATION_SCHEMA=mcl
```

## 📦 Восстановление базы данных

### 1. Создание структуры папок
```bash
mkdir -p database/backups
mkdir -p database/init
mkdir -p database/migrations
```

### 2. Восстановление из резервной копии
```bash
# Восстановление бинарной копии
pg_restore -U alex -d Fish_Eye database/backups/fish_eye_mcl_backup.dump

# Или восстановление из SQL файла
psql -U alex -d Fish_Eye -f database/backups/fish_eye_mcl_backup.sql
```

### 3. Проверка восстановления
```bash
# Проверка подключения
psql -U alex -d Fish_Eye -c "SELECT version();"

# Проверка схем
psql -U alex -d Fish_Eye -c "\dn"

# Проверка таблиц в схеме mcl
psql -U alex -d Fish_Eye -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'mcl' ORDER BY table_name;"
```

## 🧪 Тестирование установки

### 1. Проверка подключения к базе данных
```bash
python scripts/database/test_connection.py
```

### 2. Проверка статуса миграции
```bash
python scripts/monitoring/check_status.py
```

### 3. Запуск тестов
```bash
python -m pytest tests/
```

## 🔧 Настройка SSH для GitHub

### 1. Генерация SSH ключа
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

### 2. Добавление ключа в ssh-agent
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### 3. Копирование публичного ключа
```bash
cat ~/.ssh/id_ed25519.pub
```

### 4. Добавление ключа в GitHub
1. Перейдите в Settings → SSH and GPG keys
2. Нажмите "New SSH key"
3. Вставьте публичный ключ
4. Сохраните

## 🚨 Устранение неполадок

### Проблема: Ошибка подключения к PostgreSQL
```bash
# Проверка статуса службы
sudo systemctl status postgresql

# Перезапуск службы
sudo systemctl restart postgresql

# Проверка логов
sudo journalctl -u postgresql
```

### Проблема: Ошибка аутентификации
```bash
# Проверка файла pg_hba.conf
sudo nano /var/lib/pgsql/data/pg_hba.conf

# Изменение метода аутентификации на trust
# local   all             all                                     trust
```

### Проблема: Ошибка прав доступа
```bash
# Проверка прав пользователя
sudo -u postgres psql -c "\du"

# Предоставление прав
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE \"Fish_Eye\" TO alex;"
```

## 📚 Дополнительные ресурсы

- **Документация PostgreSQL:** https://www.postgresql.org/docs/
- **Документация Python:** https://docs.python.org/
- **GitHub SSH:** https://docs.github.com/en/authentication/connecting-to-github-with-ssh

## ✅ Проверка готовности

После выполнения всех шагов проверьте:

- [ ] PostgreSQL запущен и доступен
- [ ] База данных Fish_Eye создана
- [ ] Схема mcl восстановлена
- [ ] Python зависимости установлены
- [ ] Git настроен для работы с GitHub
- [ ] Переменные окружения настроены

**Готово к работе с проектом FEMCL!** 🚀