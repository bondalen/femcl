#!/usr/bin/env python3
"""
Модуль для загрузки и работы с конфигурацией системы миграции FEMCL
"""
import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path
from rich.console import Console

console = Console()

class ConfigLoader:
    """Класс для загрузки и управления конфигурацией"""
    
    def __init__(self, config_path: str = "../config/config.yaml"):
        """Инициализация загрузчика конфигурации"""
        self.config_path = Path(config_path)
        self.config: Optional[Dict[str, Any]] = None
        self.load_config()
    
    def load_config(self) -> None:
        """Загрузка конфигурации из YAML файла"""
        try:
            if not self.config_path.exists():
                console.print(f"[red]❌ Файл конфигурации не найден: {self.config_path}[/red]")
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
            
            console.print(f"[green]✅ Конфигурация загружена из {self.config_path}[/green]")
            
        except yaml.YAMLError as e:
            console.print(f"[red]❌ Ошибка парсинга YAML: {e}[/red]")
            raise
        except Exception as e:
            console.print(f"[red]❌ Ошибка загрузки конфигурации: {e}[/red]")
            raise
    
    def get_database_config(self, db_type: str) -> Dict[str, Any]:
        """Получение конфигурации базы данных"""
        if not self.config:
            raise ValueError("Конфигурация не загружена")
        
        db_config = self.config.get('database', {}).get(db_type, {})
        if not db_config:
            raise ValueError(f"Конфигурация для {db_type} не найдена")
        
        return db_config
    
    def get_migration_config(self) -> Dict[str, Any]:
        """Получение конфигурации миграции"""
        if not self.config:
            raise ValueError("Конфигурация не загружена")
        
        return self.config.get('migration', {})
    
    def get_readiness_check(self) -> Dict[str, Any]:
        """Получение конфигурации проверки готовности"""
        if not self.config:
            raise ValueError("Конфигурация не загружена")
        
        return self.config.get('readiness_check', {})
    
    def get_table_creation_config(self) -> Dict[str, Any]:
        """Получение конфигурации создания таблиц"""
        if not self.config:
            raise ValueError("Конфигурация не загружена")
        
        return self.config.get('table_creation', {})
    
    def get_data_migration_config(self) -> Dict[str, Any]:
        """Получение конфигурации переноса данных"""
        if not self.config:
            raise ValueError("Конфигурация не загружена")
        
        return self.config.get('data_migration', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Получение конфигурации мониторинга"""
        if not self.config:
            raise ValueError("Конфигурация не загружена")
        
        return self.config.get('monitoring', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Получение конфигурации безопасности"""
        if not self.config:
            raise ValueError("Конфигурация не загружена")
        
        return self.config.get('security', {})
    
    def get_development_config(self) -> Dict[str, Any]:
        """Получение конфигурации разработки"""
        if not self.config:
            raise ValueError("Конфигурация не загружена")
        
        return self.config.get('development', {})
    
    def get_github_config(self) -> Dict[str, Any]:
        """Получение конфигурации GitHub"""
        if not self.config:
            raise ValueError("Конфигурация не загружена")
        
        return self.config.get('github', {})
    
    def get_connection_string(self, db_type: str) -> str:
        """Получение строки подключения к базе данных"""
        db_config = self.get_database_config(db_type)
        
        if db_type == 'mssql':
            return (
                f"DRIVER={{{db_config.get('driver', 'ODBC Driver 17 for SQL Server')}}};"
                f"SERVER={db_config.get('server')},{db_config.get('port')};"
                f"DATABASE={db_config.get('database')};"
                f"UID={db_config.get('user')};"
                f"PWD={db_config.get('password')};"
                f"TrustServerCertificate={'yes' if db_config.get('trust_certificate') else 'no'};"
            )
        elif db_type == 'postgres':
            return (
                f"host={db_config.get('host')} "
                f"port={db_config.get('port')} "
                f"dbname={db_config.get('database')} "
                f"user={db_config.get('user')} "
                f"password={db_config.get('password')} "
                f"sslmode={db_config.get('ssl_mode', 'prefer')}"
            )
        else:
            raise ValueError(f"Неподдерживаемый тип базы данных: {db_type}")
    
    def validate_config(self) -> bool:
        """Валидация конфигурации"""
        if not self.config:
            console.print("[red]❌ Конфигурация не загружена[/red]")
            return False
        
        required_sections = [
            'database', 'migration', 'readiness_check', 
            'table_creation', 'data_migration'
        ]
        
        for section in required_sections:
            if section not in self.config:
                console.print(f"[red]❌ Отсутствует обязательная секция: {section}[/red]")
                return False
        
        # Проверка конфигурации баз данных
        mssql_config = self.config.get('database', {}).get('mssql', {})
        postgres_config = self.config.get('database', {}).get('postgres', {})
        
        # Проверка MS SQL Server
        mssql_required_keys = ['server', 'port', 'database', 'user', 'password']
        for key in mssql_required_keys:
            if key not in mssql_config:
                console.print(f"[red]❌ Отсутствует обязательный параметр mssql.{key}[/red]")
                return False
        
        # Проверка PostgreSQL
        postgres_required_keys = ['host', 'port', 'database', 'user', 'password']
        for key in postgres_required_keys:
            if key not in postgres_config:
                console.print(f"[red]❌ Отсутствует обязательный параметр postgres.{key}[/red]")
                return False
        
        console.print("[green]✅ Конфигурация валидна[/green]")
        return True
    
    def print_config_summary(self) -> None:
        """Вывод краткой информации о конфигурации"""
        if not self.config:
            console.print("[red]❌ Конфигурация не загружена[/red]")
            return
        
        console.print("[blue]📋 Краткая информация о конфигурации:[/blue]")
        
        # Базы данных
        mssql_config = self.config.get('database', {}).get('mssql', {})
        postgres_config = self.config.get('database', {}).get('postgres', {})
        
        console.print(f"  MS SQL Server: {mssql_config.get('server')}:{mssql_config.get('port')}/{mssql_config.get('database')}")
        console.print(f"  PostgreSQL: {postgres_config.get('host')}:{postgres_config.get('port')}/{postgres_config.get('database')}")
        
        # Настройки миграции
        migration_config = self.config.get('migration', {})
        console.print(f"  Целевая схема: {migration_config.get('target_schema')}")
        console.print(f"  Размер пакета: {migration_config.get('batch_size')}")
        console.print(f"  Максимум попыток: {migration_config.get('max_retries')}")
        
        # Проверка готовности
        readiness_config = self.config.get('readiness_check', {})
        console.print(f"  Минимальный процент готовности: {readiness_config.get('min_readiness_percentage')}%")
        
        # Безопасность
        security_config = self.config.get('security', {})
        console.print(f"  Шифрование паролей: {'Да' if security_config.get('encrypt_passwords') else 'Нет'}")
        console.print(f"  SSL соединения: {'Да' if security_config.get('use_ssl_connections') else 'Нет'}")

# Глобальный экземпляр конфигурации
config = ConfigLoader()

def get_config() -> ConfigLoader:
    """Получение глобального экземпляра конфигурации"""
    return config

if __name__ == "__main__":
    # Тестирование загрузки конфигурации
    try:
        config_loader = ConfigLoader()
        
        if config_loader.validate_config():
            config_loader.print_config_summary()
        else:
            console.print("[red]❌ Конфигурация содержит ошибки[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Ошибка: {e}[/red]")