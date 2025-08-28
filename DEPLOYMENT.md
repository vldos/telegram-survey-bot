# 🚀 Інструкції по розгортанню

## 📋 Передумови

- Python 3.8+
- Обліковий запис Supabase
- Telegram бот (створений через @BotFather)

## 🔧 Крок 1: Налаштування Supabase

### 1.1 Створення проекту
1. Перейдіть на [supabase.com](https://supabase.com)
2. Створіть новий проект
3. Зачекайте завершення ініціалізації

### 1.2 Отримання ключів
1. В Dashboard перейдіть в Settings -> API
2. Скопіюйте:
   - **Project URL** (поле `Project URL`)
   - **anon public** ключ (поле `anon public`)

### 1.3 Створення таблиці
1. Перейдіть в SQL Editor
2. Виконайте наступний SQL код:

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

## 🤖 Крок 2: Створення Telegram бота

### 2.1 Отримання токена
1. Напишіть [@BotFather](https://t.me/botfather) в Telegram
2. Використайте команду `/newbot`
3. Вкажіть назву бота (наприклад, "Survey Bot")
4. Вкажіть username бота (наприклад, "my_survey_bot")
5. Скопіюйте отриманий токен

### 2.2 Налаштування бота
1. Встановіть опис бота: `/setdescription`
2. Встановіть інформацію про бота: `/setabouttext`
3. За потреби налаштуйте команди: `/setcommands`

## 💻 Крок 3: Налаштування проекту

### 3.1 Клонування та встановлення
```bash
# Клонуйте проект (якщо використовуєте git)
git clone <repository-url>
cd Chat_bot_M_v1

# Створіть віртуальне середовище
python3 -m venv venv

# Активуйте віртуальне середовище
source venv/bin/activate  # Linux/Mac
# або
venv\Scripts\activate     # Windows

# Встановіть залежності
pip install -r requirements.txt
```

### 3.2 Налаштування змінних середовища
Створіть файл `.env` в корені проекту:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
TELEGRAM_TOKEN=your-bot-token-here
```

## 🚀 Крок 4: Запуск

### 4.1 Тестування
```bash
# Перевірте налаштування
python setup_database.py

# Запустіть бота
python bot.py
```

### 4.2 Виробниче розгортання

#### Варіант 1: Локальний сервер
```bash
# Запустіть бота в фоновому режимі
nohup python bot.py > bot.log 2>&1 &
```

#### Варіант 2: Docker
Створіть `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

```bash
# Збірка та запуск
docker build -t survey-bot .
docker run -d --name survey-bot --env-file .env survey-bot
```

#### Варіант 3: Хмарні платформи

**Heroku:**
```bash
# Створіть Procfile
echo "worker: python bot.py" > Procfile

# Розгорніть
heroku create your-bot-name
heroku config:set SUPABASE_URL=your-url
heroku config:set SUPABASE_KEY=your-key
heroku config:set TELEGRAM_TOKEN=your-token
git push heroku main
```

**Railway:**
1. Підключіть GitHub репозиторій
2. Додайте змінні середовища
3. Railway автоматично розгорне проект

**DigitalOcean App Platform:**
1. Підключіть GitHub репозиторій
2. Налаштуйте змінні середовища
3. Виберіть Python runtime

## 📊 Крок 5: Моніторинг та аналіз

### 5.1 Перегляд статистики
```bash
# Запустіть аналіз даних
python analyze_data.py
```

### 5.2 Supabase Dashboard
- Переглядайте дані в реальному часі
- Створюйте власні запити
- Експортуйте дані

### 5.3 Логи
```bash
# Перегляньте логи бота
tail -f bot.log
```

## 🔒 Безпека

### Рекомендації:
1. **Ніколи не комітьте** файл `.env` в git
2. Використовуйте **сильні паролі** для Supabase
3. Обмежте **доступ до API ключів**
4. Регулярно **оновлюйте залежності**
5. Використовуйте **HTTPS** для всіх з'єднань

### Налаштування RLS (Row Level Security):
```sql
-- Включіть RLS для таблиці
ALTER TABLE survey_responses ENABLE ROW LEVEL SECURITY;

-- Створіть політику (за потреби)
CREATE POLICY "Users can view their own responses" ON survey_responses
    FOR SELECT USING (auth.uid()::text = user_id::text);
```

## 🐛 Вирішення проблем

### Поширені помилки:

**1. "supabase_url is required"**
- Перевірте правильність SUPABASE_URL в .env
- Переконайтеся, що файл .env знаходиться в корені проекту

**2. "Invalid token"**
- Перевірте правильність TELEGRAM_TOKEN
- Переконайтеся, що бот не заблокований

**3. "Table does not exist"**
- Виконайте SQL код для створення таблиці
- Перевірте права доступу до бази даних

**4. "Connection timeout"**
- Перевірте інтернет-з'єднання
- Перевірте налаштування файрволу

## 📞 Підтримка

Якщо у вас виникли проблеми:

1. Перевірте логи: `tail -f bot.log`
2. Запустіть в режимі налагодження: `python -u bot.py`
3. Перевірте з'єднання з Supabase: `python setup_database.py`
4. Створіть issue в репозиторії з детальним описом проблеми

## 🔄 Оновлення

Для оновлення бота:

```bash
# Отримайте останні зміни
git pull origin main

# Оновіть залежності
pip install -r requirements.txt

# Перезапустіть бота
pkill -f bot.py
python bot.py
```
