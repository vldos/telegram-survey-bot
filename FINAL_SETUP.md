# 🎉 Фінальна настройка бота

## ✅ Що вже зроблено:

1. **Створено всі файли проекту** ✅
2. **Налаштовано віртуальне середовище** ✅
3. **Встановлено залежності** ✅
4. **Створено файл .env з вашими ключами** ✅
5. **Протестовано підключення до Supabase** ✅
6. **Запущено бота** ✅

## 🔧 Що потрібно зробити:

### 1. Створіть таблицю в Supabase

Перейдіть в [Supabase Dashboard](https://supabase.com/dashboard/project/fflyixvsctfesdfiukow) і виконайте наступний SQL код в SQL Editor:

```sql
CREATE TABLE IF NOT EXISTS survey_responses (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    answers JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_survey_responses_user_id ON survey_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_created_at ON survey_responses(created_at);
```

### 2. Протестуйте бота

1. Знайдіть свого бота в Telegram (за токеном: `7538064244:AAEeA6cx_FuTcEkHoF2GngbjLY5u8p2VtGw`)
2. Надішліть команду `/start`
3. Пройдіть опитування

### 3. Перевірте збереження даних

Після проходження опитування перевірте в Supabase Dashboard -> Table Editor -> survey_responses, чи збереглися ваші відповіді.

## 📊 Ваші дані для підключення:

- **Supabase URL**: `https://fflyixvsctfesdfiukow.supabase.co`
- **Supabase Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmbHlpeHZzY3RmZXNkZml1a293Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYzODQyOTYsImV4cCI6MjA3MTk2MDI5Nn0.Ywx4zCjtkeyF9xRFWsSEREvIYt3R-5FxMn2kylzJge4`
- **Telegram Token**: `7538064244:AAEeA6cx_FuTcEkHoF2GngbjLY5u8p2VtGw`

## 🚀 Команди для управління:

```bash
# Запуск бота
source venv/bin/activate && python bot.py

# Тестування підключення
source venv/bin/activate && python test_connection.py

# Аналіз даних (після встановлення pandas)
source venv/bin/activate && python analyze_data.py
```

## 📁 Структура проекту:

```
Chat_bot_M_v1/
├── bot.py              # Основний файл бота
├── config.py           # Конфігурація та питання
├── database.py         # Робота з Supabase
├── test_connection.py  # Тестування підключень
├── create_table.py     # Створення таблиці
├── analyze_data.py     # Аналіз даних
├── requirements.txt    # Залежності
├── .env               # Ваші ключі
├── README.md          # Документація
├── DEPLOYMENT.md      # Інструкції розгортання
└── QUICK_START.md     # Швидкий старт
```

## 🎯 Функції бота:

- ✅ Інтерактивне опитування з кнопками
- ✅ Підтримка одиночного та множинного вибору
- ✅ Збереження в Supabase
- ✅ Український інтерфейс
- ✅ 10 основних питань + 4 додаткових

## 🔗 Корисні посилання:

- [Supabase Dashboard](https://supabase.com/dashboard/project/fflyixvsctfesdfiukow)
- [Telegram Bot](https://t.me/your_bot_username) (замініть на username вашого бота)

## 🆘 Якщо щось не працює:

1. **Бот не відповідає**: Перевірте, чи запущений `python bot.py`
2. **Помилка збереження**: Створіть таблицю в Supabase
3. **Помилка підключення**: Перевірте файл `.env`

## 🎉 Готово!

Ваш бот готовий до роботи! Просто створіть таблицю в Supabase і можете починати збирати відповіді.
