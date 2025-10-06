#!/usr/bin/env python3
"""
Скрипт обновления project-docs.json с новой структурой modules
"""

import json
import os

def update_project_docs():
    """Обновляет project-docs.json с новой структурой modules"""
    
    # Пути к файлам
    project_docs_path = "docs/project/project-docs.json"
    new_modules_path = "new_modules_structure.json"
    
    print("📄 Загружаю project-docs.json...")
    with open(project_docs_path, 'r', encoding='utf-8') as f:
        project_docs = json.load(f)
    
    print("📄 Загружаю новую структуру modules...")
    with open(new_modules_path, 'r', encoding='utf-8') as f:
        new_modules = json.load(f)
    
    print("🔄 Обновляю раздел modules...")
    project_docs['project']['architecture']['modules'] = new_modules['modules']
    
    print("💾 Сохраняю обновленный project-docs.json...")
    with open(project_docs_path, 'w', encoding='utf-8') as f:
        json.dump(project_docs, f, ensure_ascii=False, indent=2)
    
    print("✅ project-docs.json успешно обновлен!")
    print("🗑️ Удаляю временный файл...")
    os.remove(new_modules_path)
    print("🎉 Обновление завершено!")

if __name__ == "__main__":
    update_project_docs()
