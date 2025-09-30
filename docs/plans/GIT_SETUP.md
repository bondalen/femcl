# 🔧 Настройка Git репозитория FEMCL

## 📋 Требования для доступа к репозиторию

### 1. GitHub аккаунт и права доступа
- **Репозиторий:** [https://github.com/bondalen/femcl.git](https://github.com/bondalen/femcl.git)
- **Владелец:** bondalen
- **Права доступа:** Write/Admin права для репозитория
- **Аутентификация:** SSH ключи или Personal Access Token

### 2. Настройка Git на Fedora 42
```bash
# Установка Git (если не установлен)
sudo dnf install git

# Настройка пользователя
git config --global user.name "Ваше имя"
git config --global user.email "ваш@email.com"

# Генерация SSH ключа
ssh-keygen -t ed25519 -C "ваш@email.com"

# Добавление ключа в ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Копирование публичного ключа
cat ~/.ssh/id_ed25519.pub
```

### 3. Добавление SSH ключа в GitHub
1. Перейдите в **Settings** → **SSH and GPG keys**
2. Нажмите **"New SSH key"**
3. Вставьте публичный ключ из команды выше
4. Сохраните ключ

### 4. Клонирование репозитория
```bash
# Клонирование пустого репозитория
git clone https://github.com/bondalen/femcl.git
cd femcl

# Или через SSH (если настроен)
git clone git@github.com:bondalen/femcl.git
```

## 🚀 Инициализация проекта FEMCL

### 1. Инициализация Git репозитория
```bash
# Инициализация Git
git init

# Добавление удаленного репозитория
git remote add origin https://github.com/bondalen/femcl.git

# Или через SSH
git remote add origin git@github.com:bondalen/femcl.git
```

### 2. Создание .gitignore
```bash
# Создание .gitignore файла
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Database
*.db
*.sqlite3
*.dump
*.sql

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
EOF
```

### 3. Первый коммит
```bash
# Добавление всех файлов
git add .

# Создание первого коммита
git commit -m "Initial commit: FEMCL project structure

- Created project structure
- Added documentation
- Added Python scripts
- Added database backups
- Added migration rules
- Added setup instructions"

# Отправка в GitHub
git push -u origin main
```

## 🔄 Рабочий процесс

### 1. Ежедневная работа
```bash
# Проверка статуса
git status

# Добавление изменений
git add .

# Создание коммита
git commit -m "Описание изменений"

# Отправка изменений
git push
```

### 2. Создание веток для функций
```bash
# Создание новой ветки
git checkout -b feature/new-feature

# Работа в ветке
# ... внесение изменений ...

# Коммит изменений
git add .
git commit -m "Add new feature"

# Отправка ветки
git push -u origin feature/new-feature

# Создание Pull Request в GitHub
```

### 3. Синхронизация с основной веткой
```bash
# Переключение на main
git checkout main

# Получение последних изменений
git pull origin main

# Слияние изменений в рабочую ветку
git checkout feature/working-branch
git merge main
```

## 📚 Полезные команды Git

### Основные команды
```bash
# Проверка статуса
git status

# Просмотр истории
git log --oneline

# Просмотр изменений
git diff

# Отмена изменений
git checkout -- filename

# Отмена коммита
git reset --soft HEAD~1
```

### Работа с ветками
```bash
# Список веток
git branch -a

# Создание ветки
git branch new-branch

# Переключение ветки
git checkout branch-name

# Удаление ветки
git branch -d branch-name
```

### Работа с удаленным репозиторием
```bash
# Получение изменений
git fetch origin

# Слияние изменений
git merge origin/main

# Отправка ветки
git push origin branch-name

# Удаление удаленной ветки
git push origin --delete branch-name
```

## 🚨 Устранение неполадок

### Проблема: Ошибка аутентификации
```bash
# Проверка SSH ключей
ssh -T git@github.com

# Переустановка SSH ключа
ssh-add -D
ssh-add ~/.ssh/id_ed25519
```

### Проблема: Конфликты при слиянии
```bash
# Просмотр конфликтов
git status

# Решение конфликтов в файлах
# ... редактирование файлов ...

# Добавление разрешенных файлов
git add .

# Завершение слияния
git commit
```

### Проблема: Отмена последнего коммита
```bash
# Мягкая отмена (сохраняет изменения)
git reset --soft HEAD~1

# Жесткая отмена (удаляет изменения)
git reset --hard HEAD~1
```

## 📋 Чек-лист готовности

После выполнения всех шагов проверьте:

- [ ] Git установлен и настроен
- [ ] SSH ключ добавлен в GitHub
- [ ] Репозиторий клонирован
- [ ] Проект инициализирован
- [ ] Первый коммит создан
- [ ] Файлы отправлены в GitHub
- [ ] .gitignore настроен
- [ ] Рабочий процесс понятен

## 🎯 Следующие шаги

1. **Настройка среды разработки** - установка PostgreSQL и Python
2. **Восстановление базы данных** - из резервных копий
3. **Тестирование подключения** - проверка всех компонентов
4. **Запуск миграции** - начало работы с данными

**Готово к работе с проектом FEMCL!** 🚀