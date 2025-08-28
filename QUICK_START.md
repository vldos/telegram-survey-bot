# ⚡ Швидкий старт

## 🎯 Що це?

Telegram бот для збору відповідей на питання про пошук розваг та активностей. Всі відповіді зберігаються в Supabase.

## 🚀 Швидкий запуск (5 хвилин)

### 1. Створіть Telegram бота
```bash
# Напишіть @BotFather в Telegram
# Команда: /newbot
# Отримайте токен
```

### 2. Створіть проект Supabase
```bash
# Перейдіть на supabase.com
# Створіть новий проект
# Скопіюйте URL та API ключ
```

### 3. Налаштуйте проект
```bash
# Клонуйте проект
git clone <repository>
cd Chat_bot_M_v1

# Створіть віртуальне середовище
python3 -m venv venv
source venv/bin/activate

# Встановіть залежності
pip install -r requirements.txt
```

### 4. Створіть .env файл
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
TELEGRAM_TOKEN=your-bot-token
```

### 5. Налаштуйте базу даних
```bash
# Запустіть скрипт налаштування
python setup_database.py

# Виконайте SQL код в Supabase Dashboard
```

### 6. Запустіть бота
```bash
python bot.py
```

## 📊 Аналіз даних

```bash
# Запустіть аналіз
python analyze_data.py
```

## 📁 Структура файлів

- `bot.py` - Основний файл бота
- `config.py` - Конфігурація та питання
- `database.py` - Робота з Supabase
- `analyze_data.py` - Аналіз відповідей
- `setup_database.py` - Налаштування БД

## 🔗 Корисні посилання

- [Supabase](https://supabase.com) - База даних
- [@BotFather](https://t.me/botfather) - Створення бота
- [Повна документація](README.md)
- [Інструкції розгортання](DEPLOYMENT.md)

## 🆘 Проблеми?

1. Перевірте `.env` файл
2. Запустіть `python setup_database.py`
3. Перегляньте [DEPLOYMENT.md](DEPLOYMENT.md)
