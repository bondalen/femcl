"""
ConnectionProfileLoader класс для загрузки профилей подключений.

Этот класс отвечает за чтение, загрузку и управление профилями подключений
из файла connections.json для работы в режиме ЭКСПЛУАТАЦИИ.
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConnectionProfileLoader:
    """
    Класс для загрузки и управления профилями подключений к БД.
    
    Работает с файлом connections.json для режима ЭКСПЛУАТАЦИИ.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Инициализация ConnectionProfileLoader.
        
        Args:
            config_path: Путь к файлу connections.json. 
                        Если не указан, использует стандартное расположение.
        """
        self.logger = logging.getLogger(__name__)
        
        if config_path is None:
            # Стандартный путь к конфигурации
            base_path = Path(__file__).parent.parent / "config"
            self.config_path = base_path / "connections.json"
        else:
            self.config_path = Path(config_path)
        
        self.profiles_data = None
        self._load_profiles()
    
    def _load_profiles(self) -> None:
        """Загрузить profiles из connections.json."""
        try:
            if not self.config_path.exists():
                self.logger.warning(
                    f"Файл {self.config_path} не найден. "
                    "Создайте connections.json из connections.example.json"
                )
                self.profiles_data = None
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.profiles_data = json.load(f)
            
            self.logger.info(f"Профили загружены из {self.config_path}")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга JSON в {self.config_path}: {e}")
            self.profiles_data = None
        except Exception as e:
            self.logger.error(f"Ошибка загрузки профилей: {e}")
            self.profiles_data = None
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        Получить список всех доступных профилей.
        
        Returns:
            Список словарей с информацией о профилях
        """
        if self.profiles_data is None:
            self.logger.warning("Профили не загружены")
            return []
        
        profiles = self.profiles_data.get('profiles', [])
        
        # Возвращаем краткую информацию о профилях
        return [
            {
                'profile_id': p.get('profile_id'),
                'name': p.get('name'),
                'task_id': p.get('task_id'),
                'description': p.get('description'),
                'active': p.get('active', True),
                'last_used': p.get('last_used')
            }
            for p in profiles
        ]
    
    def load_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Загрузить конкретный профиль по ID.
        
        Args:
            profile_id: Идентификатор профиля
            
        Returns:
            Словарь с полными данными профиля или None
        """
        if self.profiles_data is None:
            self.logger.error("Профили не загружены")
            return None
        
        profiles = self.profiles_data.get('profiles', [])
        
        for profile in profiles:
            if profile.get('profile_id') == profile_id:
                self.logger.info(f"Профиль '{profile_id}' загружен")
                
                # Обновляем last_used
                self._update_last_used(profile_id)
                
                return {
                    'profile_id': profile.get('profile_id'),
                    'name': profile.get('name'),
                    'task_id': profile.get('task_id'),
                    'description': profile.get('description'),
                    'source': profile.get('source'),
                    'target': profile.get('target'),
                    'active': profile.get('active', True)
                }
        
        self.logger.warning(f"Профиль '{profile_id}' не найден")
        return None
    
    def get_default_profile(self) -> Optional[Dict[str, Any]]:
        """
        Получить профиль по умолчанию.
        
        Returns:
            Словарь с данными профиля по умолчанию или None
        """
        if self.profiles_data is None:
            return None
        
        default_profile_id = self.profiles_data.get('default_profile')
        
        if default_profile_id:
            return self.load_profile(default_profile_id)
        
        # Если default не указан, берем первый активный профиль
        profiles = self.list_profiles()
        active_profiles = [p for p in profiles if p.get('active', True)]
        
        if active_profiles:
            return self.load_profile(active_profiles[0]['profile_id'])
        
        return None
    
    def _update_last_used(self, profile_id: str) -> None:
        """Обновить last_used для профиля."""
        from datetime import datetime
        
        try:
            if self.profiles_data is None:
                return
            
            profiles = self.profiles_data.get('profiles', [])
            
            for profile in profiles:
                if profile.get('profile_id') == profile_id:
                    profile['last_used'] = datetime.now().isoformat()
                    break
            
            # Сохраняем обновленные данные
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.profiles_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.warning(f"Не удалось обновить last_used для профиля '{profile_id}': {e}")
    
    def get_profile_by_task_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить профиль по task_id.
        
        Args:
            task_id: ID задачи миграции
            
        Returns:
            Словарь с данными профиля или None
        """
        if self.profiles_data is None:
            return None
        
        profiles = self.profiles_data.get('profiles', [])
        
        for profile in profiles:
            if profile.get('task_id') == task_id:
                return self.load_profile(profile.get('profile_id'))
        
        self.logger.warning(f"Профиль для task_id={task_id} не найден")
        return None
    
    def validate_profile(self, profile: Dict[str, Any]) -> bool:
        """
        Валидация структуры профиля.
        
        Args:
            profile: Словарь с данными профиля
            
        Returns:
            True если профиль валиден, иначе False
        """
        required_fields = ['profile_id', 'name', 'task_id', 'source', 'target']
        
        for field in required_fields:
            if field not in profile:
                self.logger.error(f"Отсутствует обязательное поле '{field}' в профиле")
                return False
        
        # Валидация source
        source_required = ['type', 'host', 'database', 'user', 'password']
        for field in source_required:
            if field not in profile['source']:
                self.logger.error(f"Отсутствует поле '{field}' в source")
                return False
        
        # Валидация target
        target_required = ['type', 'host', 'database', 'user', 'password']
        for field in target_required:
            if field not in profile['target']:
                self.logger.error(f"Отсутствует поле '{field}' в target")
                return False
        
        return True
