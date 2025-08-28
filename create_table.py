#!/usr/bin/env python3
"""
Скрипт для создания таблицы в Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

def create_survey_table():
    """Создает таблицу survey_responses в Supabase"""
    print("🔧 Створення таблиці survey_responses...")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Получаем ключи
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Помилка: Відсутні змінні середовища")
        return False
    
    try:
        # Создаем клиент
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Підключення до Supabase успішне!")
        
        # SQL для создания таблицы
        sql = """
        CREATE TABLE IF NOT EXISTS survey_responses (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            username TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            answers JSONB NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_survey_responses_user_id ON survey_responses(user_id);
        CREATE INDEX IF NOT EXISTS idx_survey_responses_created_at ON survey_responses(created_at);
        """
        
        # Выполняем SQL
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()
        print("✅ Таблиця survey_responses створена успішно!")
        
        # Проверяем создание таблицы
        try:
            result = supabase.table("survey_responses").select("count", count="exact").execute()
            print(f"📊 Таблиця існує. Кількість записів: {result.count}")
        except Exception as e:
            print(f"⚠️ Помилка при перевірці таблиці: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка при створенні таблиці: {str(e)}")
        print("\n📋 Альтернативний спосіб:")
        print("1. Перейдіть в Supabase Dashboard")
        print("2. Відкрийте SQL Editor")
        print("3. Виконайте наступний SQL код:")
        print(sql)
        return False

def test_table_access():
    """Тестирует доступ к таблице"""
    print("\n🧪 Тестування доступу до таблиці...")
    
    load_dotenv()
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Пробуем вставить тестовую запись
        test_data = {
            "user_id": 123456789,
            "username": "test_user",
            "answers": {"test": "data"}
        }
        
        result = supabase.table("survey_responses").insert(test_data).execute()
        print("✅ Тестова запись додана успішно!")
        
        # Удаляем тестовую запись
        supabase.table("survey_responses").delete().eq("user_id", 123456789).execute()
        print("✅ Тестова запись видалена")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка при тестуванні: {str(e)}")
        return False

def main():
    print("🔧 Налаштування бази даних Supabase")
    print("=" * 50)
    
    # Создаем таблицу
    table_created = create_survey_table()
    
    if table_created:
        # Тестируем доступ
        access_ok = test_table_access()
        
        if access_ok:
            print("\n🎉 База даних налаштована успішно!")
            print("Бот готовий до роботи!")
        else:
            print("\n⚠️ Є проблеми з доступом до таблиці")
    else:
        print("\n❌ Не вдалося створити таблицю")

if __name__ == "__main__":
    main()
