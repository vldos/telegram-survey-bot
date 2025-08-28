#!/usr/bin/env python3
"""
Скрипт для проверки конфигурации перед деплоем на Railway
"""

import os
from dotenv import load_dotenv

def check_environment():
    """Проверяет наличие необходимых переменных окружения"""
    print("🔍 Проверка переменных окружения...")
    
    required_vars = [
        'TELEGRAM_TOKEN',
        'SUPABASE_URL', 
        'SUPABASE_KEY'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * len(os.getenv(var)[:10])}...")
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные: {', '.join(missing_vars)}")
        return False
    
    print("✅ Все необходимые переменные окружения настроены")
    return True

def check_railway_config():
    """Проверяет конфигурацию для Railway"""
    print("\n🔍 Проверка конфигурации Railway...")
    
    required_files = [
        'Procfile',
        'runtime.txt', 
        'requirements.txt',
        'railway.json'
    ]
    
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"✅ {file}")
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    
    print("✅ Все необходимые файлы конфигурации присутствуют")
    return True

def check_dependencies():
    """Проверяет зависимости"""
    print("\n🔍 Проверка зависимостей...")
    
    required_packages = [
        'python-telegram-bot',
        'supabase',
        'python-dotenv',
        'aiohttp'
    ]
    
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
            
        for package in required_packages:
            if package in content:
                print(f"✅ {package}")
            else:
                print(f"❌ {package} отсутствует в requirements.txt")
                return False
                
        print("✅ Все зависимости указаны в requirements.txt")
        return True
        
    except FileNotFoundError:
        print("❌ Файл requirements.txt не найден")
        return False

def main():
    """Основная функция проверки"""
    print("🚀 Проверка готовности к деплою на Railway\n")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    checks = [
        check_environment(),
        check_railway_config(),
        check_dependencies()
    ]
    
    print("\n" + "="*50)
    
    if all(checks):
        print("🎉 Все проверки пройдены! Проект готов к деплою на Railway.")
        print("\n📋 Следующие шаги:")
        print("1. Запушьте код в GitHub")
        print("2. Создайте проект на Railway.app")
        print("3. Подключите репозиторий")
        print("4. Настройте переменные окружения")
        print("5. Дождитесь деплоя")
    else:
        print("❌ Обнаружены проблемы. Исправьте их перед деплоем.")
        print("\n📖 См. RAILWAY_DEPLOYMENT.md для подробных инструкций")

if __name__ == "__main__":
    main()
