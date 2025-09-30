#!/usr/bin/env python3
"""
Скрипт для синхронизации с GitHub
"""
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from config_loader import get_config

console = Console()

class GitHubSync:
    """Класс для синхронизации с GitHub"""
    
    def __init__(self):
        """Инициализация синхронизации"""
        self.config = get_config()
        self.github_config = self.config.get_github_config()
        self.token = self._load_token()
        
    def _load_token(self):
        """Загрузка токена GitHub"""
        token_file = self.github_config.get('token_file', 'config/github_token.txt')
        token_path = Path(f"../{token_file}")
        
        if not token_path.exists():
            console.print(f"[red]❌ Файл токена не найден: {token_file}[/red]")
            return None
            
        try:
            with open(token_path, 'r') as f:
                token = f.read().strip()
            console.print("[green]✅ Токен GitHub загружен[/green]")
            return token
        except Exception as e:
            console.print(f"[red]❌ Ошибка загрузки токена: {e}[/red]")
            return None
    
    def _setup_remote(self):
        """Настройка удаленного репозитория"""
        remote_url = self.github_config.get('remote_url')
        if not remote_url:
            console.print("[red]❌ URL удаленного репозитория не настроен[/red]")
            return False
            
        # Заменяем URL на URL с токеном
        if self.token:
            if "github.com" in remote_url:
                remote_url = remote_url.replace("https://", f"https://{self.token}@")
        
        try:
            # Проверяем существование удаленного репозитория
            result = subprocess.run(['git', 'remote', '-v'], 
                                  capture_output=True, text=True, cwd='.')
            if remote_url not in result.stdout:
                # Добавляем или обновляем удаленный репозиторий
                subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url], 
                              cwd='.', check=True)
                console.print("[green]✅ Удаленный репозиторий настроен[/green]")
            else:
                console.print("[blue]ℹ️ Удаленный репозиторий уже настроен[/blue]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ Ошибка настройки удаленного репозитория: {e}[/red]")
            return False
    
    def _generate_commit_message(self, action, description):
        """Генерация сообщения коммита"""
        template = self.github_config.get('commit_message_template', '🚀 {action}: {description}')
        
        # Заменяем плейсхолдеры
        message = template.format(action=action, description=description)
        
        # Добавляем временную метку если нужно
        if self.github_config.get('include_timestamp', True):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message += f"\n\n*Синхронизация: {timestamp}*"
        
        return message
    
    def sync_changes(self, action="Update", description="Project changes"):
        """Синхронизация изменений с GitHub"""
        console.print("[blue]🔄 Начало синхронизации с GitHub[/blue]")
        
        try:
            # Настройка удаленного репозитория
            if not self._setup_remote():
                return False
            
            # Проверка статуса
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd='.')
            if not result.stdout.strip():
                console.print("[yellow]⚠️ Нет изменений для синхронизации[/yellow]")
                return True
            
            # Добавление всех изменений
            if self.github_config.get('auto_add_all', True):
                subprocess.run(['git', 'add', '.'], cwd='.', check=True)
                console.print("[green]✅ Изменения добавлены в индекс[/green]")
            
            # Создание коммита
            commit_message = self._generate_commit_message(action, description)
            subprocess.run(['git', 'commit', '-m', commit_message], cwd='.', check=True)
            console.print("[green]✅ Коммит создан[/green]")
            
            # Отправка на GitHub
            branch = self.github_config.get('branch', 'main')
            subprocess.run(['git', 'push', 'origin', branch], cwd='.', check=True)
            console.print("[green]✅ Изменения отправлены на GitHub[/green]")
            
            console.print("[bold green]🎉 Синхронизация завершена успешно![/bold green]")
            return True
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ Ошибка синхронизации: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]❌ Неожиданная ошибка: {e}[/red]")
            return False
    
    def check_status(self):
        """Проверка статуса репозитория"""
        console.print("[blue]📊 Проверка статуса репозитория[/blue]")
        
        try:
            # Статус Git
            result = subprocess.run(['git', 'status'], 
                                  capture_output=True, text=True, cwd='.')
            console.print(result.stdout)
            
            # Информация о последнем коммите
            result = subprocess.run(['git', 'log', '-1', '--oneline'], 
                                  capture_output=True, text=True, cwd='.')
            if result.stdout:
                console.print(f"[blue]Последний коммит: {result.stdout.strip()}[/blue]")
            
            # Информация о ветке
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, cwd='.')
            current_branch = result.stdout.strip()
            console.print(f"[blue]Текущая ветка: {current_branch}[/blue]")
            
            return True
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ Ошибка проверки статуса: {e}[/red]")
            return False
    
    def show_config(self):
        """Показать конфигурацию GitHub"""
        console.print("[blue]🔧 Конфигурация GitHub:[/blue]")
        console.print(f"  Репозиторий: {self.github_config.get('repository')}")
        console.print(f"  Ветка: {self.github_config.get('branch')}")
        console.print(f"  URL: {self.github_config.get('remote_url')}")
        console.print(f"  Токен: {'Настроен' if self.token else 'Не настроен'}")
        console.print(f"  Автосинхронизация: {self.github_config.get('auto_sync')}")
        console.print(f"  Синхронизация при изменениях: {self.github_config.get('sync_on_changes')}")

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        console.print("[blue]Использование:[/blue]")
        console.print("  python3 github_sync.py sync [action] [description]")
        console.print("  python3 github_sync.py status")
        console.print("  python3 github_sync.py config")
        return
    
    command = sys.argv[1]
    sync = GitHubSync()
    
    if command == "sync":
        action = sys.argv[2] if len(sys.argv) > 2 else "Update"
        description = sys.argv[3] if len(sys.argv) > 3 else "Project changes"
        success = sync.sync_changes(action, description)
        sys.exit(0 if success else 1)
        
    elif command == "status":
        success = sync.check_status()
        sys.exit(0 if success else 1)
        
    elif command == "config":
        sync.show_config()
        
    else:
        console.print(f"[red]❌ Неизвестная команда: {command}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()