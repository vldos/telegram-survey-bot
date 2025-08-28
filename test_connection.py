#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

def test_supabase_connection():
    """Тестирует подключение к Supabase"""
    print("🔧 Тестування підключення до Supabase...")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Получаем ключи
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Помилка: Відсутні змінні середовища")
        print("Створіть файл .env з наступним вмістом:")
        print("SUPABASE_URL=https://fflyixvsctfesdfiukow.supabase.co")
        print("SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmbHlpeHZzY3RmZXNkZml1a293Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYzODQyOTYsImV4cCI6MjA3MTk2MDI5Nn0.Ywx4zCjtkeyF9xRFWsSEREvIYt3R-5FxMn2kylzJge4")
        print("TELEGRAM_TOKEN=7538064244:AAEeA6cx_FuTcEkHoF2GngbjLY5u8p2VtGw")
        return False
    
    try:
        # Создаем клиент
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Підключення до Supabase успішне!")
        
        # Проверяем существование таблицы
        try:
            result = supabase.table("survey_responses").select("count", count="exact").execute()
            print("✅ Таблиця survey_responses існує")
            print(f"📊 Кількість записів: {result.count}")
        except Exception as e:
            print("⚠️ Таблиця survey_responses не існує або немає доступу")
            print("Виконайте SQL код в Supabase Dashboard:")
            print("""
CREATE TABLE IF NOT EXISTS survey_responses (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    answers JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_survey_responses_user_id ON survey_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_created_at ON survey_responses(created_at);
            """)
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка підключення: {str(e)}")
        return False

def test_telegram_token():
    """Тестирует токен Telegram"""
    print("\n🤖 Тестування Telegram токена...")
    
    load_dotenv()
    token = os.getenv('TELEGRAM_TOKEN')
    
    if not token:
        print("❌ Помилка: Відсутній TELEGRAM_TOKEN")
        return False
    
    # Простая проверка формата токена
    if ":" in token and len(token) > 20:
        print("✅ Формат токена правильний")
        return True
    else:
        print("❌ Помилка: Неправильний формат токена")
        return False

def main():
    print("🧪 Тестування підключень")
    print("=" * 50)
    
    # Тестируем Supabase
    supabase_ok = test_supabase_connection()
    
    # Тестируем Telegram
    telegram_ok = test_telegram_token()
    
    print("\n" + "=" * 50)
    if supabase_ok and telegram_ok:
        print("🎉 Всі тести пройшли успішно!")
        print("Можна запускати бота: python bot.py")
    else:
        print("❌ Є проблеми з налаштуванням")
        print("Перевірте файл .env та налаштування")

if __name__ == "__main__":
    main()
