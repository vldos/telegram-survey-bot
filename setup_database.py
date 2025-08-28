#!/usr/bin/env python3
"""
Скрипт для настройки базы данных Supabase
"""

def main():
    print("🔧 Налаштування бази даних Supabase...")
    
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
    
    print("\n📋 SQL код для створення таблиці:")
    print("=" * 50)
    print(sql)
    print("=" * 50)
    
    print("\n✅ Налаштування завершено!")
    print("\n📋 Що потрібно зробити:")
    print("1. Перейдіть в Supabase Dashboard")
    print("2. Відкрийте SQL Editor")
    print("3. Виконайте SQL код, який було показано вище")
    print("4. Створіть файл .env з вашими ключами:")
    print("   SUPABASE_URL=your_supabase_url_here")
    print("   SUPABASE_KEY=your_supabase_anon_key_here")
    print("   TELEGRAM_TOKEN=your_telegram_bot_token_here")
    print("5. Запустіть бота командою: python bot.py")
    
    print("\n🔗 Корисні посилання:")
    print("- Supabase: https://supabase.com")
    print("- BotFather: https://t.me/botfather")

if __name__ == "__main__":
    main()
