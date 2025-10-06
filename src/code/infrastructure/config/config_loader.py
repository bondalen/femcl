#!/usr/bin/env python3
"""
FEMCL - Загрузчик конфигурации
Версия: 1.0
Автор: FEMCL Team
Дата: 2025-01-27

Описание:
    Модуль для загрузки и управления конфигурацией системы FEMCL.
"""

import os
import yaml
from typing import Dict, Any

class ConfigLoader:
    """Класс для загрузки конфигурации"""
    
    def __init__(self, config_path=None):
        """
        Инициализация загрузчика конфигурации
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        if config_path is None:
            # Определяем путь к конфигурации относительно корня проекта
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.join(current_dir, 'config.yaml')
        else:
            self.config_path = config_path
    
    def load_config(self) -> Dict[str, Any]:
        """
        Загрузка конфигурации из файла
        
        Returns:
            Словарь с конфигурацией
            
        Raises:
            FileNotFoundError: Если файл конфигурации не найден
            yaml.YAMLError: Если ошибка парсинга YAML
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Файл конфигурации не найден: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Валидация обязательных секций
            required_sections = ['database', 'migration']
            for section in required_sections:
                if section not in config:
                    raise ValueError(f"Отсутствует обязательная секция: {section}")
            
            return config
            
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Ошибка парсинга YAML: {e}")
    
    def get_database_config(self, db_type: str) -> Dict[str, Any]:
        """
        Получение конфигурации базы данных
        
        Args:
            db_type: Тип базы данных ('mssql' или 'postgresql')
            
        Returns:
            Словарь с конфигурацией базы данных
            
        Raises:
            KeyError: Если тип базы данных не найден
        """
        config = self.load_config()
        
        if 'database' not in config:
            raise KeyError("Секция 'database' не найдена в конфигурации")
        
        if db_type not in config['database']:
            raise KeyError(f"Конфигурация для базы данных '{db_type}' не найдена")
        
        return config['database'][db_type]
    
    def get_migration_config(self) -> Dict[str, Any]:
        """
        Получение конфигурации миграции
        
        Returns:
            Словарь с конфигурацией миграции
        """
        config = self.load_config()
        return config.get('migration', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Получение конфигурации логирования
        
        Returns:
            Словарь с конфигурацией логирования
        """
        config = self.load_config()
        return config.get('logging', {})
    
    def get_config_value(self, key_path: str, default=None):
        """
        Получение значения конфигурации по пути
        
        Args:
            key_path: Путь к значению (например, 'database.mssql.host')
            default: Значение по умолчанию
            
        Returns:
            Значение конфигурации или значение по умолчанию
        """
        config = self.load_config()
        keys = key_path.split('.')
        
        value = config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def validate_config(self) -> bool:
        """
        Валидация конфигурации
        
        Returns:
            True если конфигурация валидна, False иначе
        """
        try:
            config = self.load_config()
            
            # Проверяем обязательные секции
            required_sections = ['database', 'migration']
            for section in required_sections:
                if section not in config:
                    return False
            
            # Проверяем конфигурацию баз данных
            db_config = config['database']
            for db_type in ['mssql', 'postgresql']:
                if db_type not in db_config:
                    return False
                
                db_section = db_config[db_type]
                required_db_keys = ['host', 'port', 'database', 'user', 'password']
                for key in required_db_keys:
                    if key not in db_section:
                        return False
            
            return True
            
        except Exception:
            return False