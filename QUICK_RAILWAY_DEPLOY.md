# 🚀 Быстрый деплой на Railway

## Шаги деплоя (5 минут)

### 1. Подготовка (1 мин)
```bash
# Проверьте готовность проекта
python3 check_config.py
```

### 2. GitHub (1 мин)
```bash
# Добавьте все файлы в git
git add .
git commit -m "Подготовка к деплою на Railway"
git push origin main
```

### 3. Railway (2 мин)
1. Откройте [railway.app](https://railway.app)
2. Нажмите "New Project" → "Deploy from GitHub repo"
3. Выберите ваш репозиторий
4. Дождитесь сборки

### 4. Переменные окружения (1 мин)
В Railway Dashboard → Variables добавьте:
```
TELEGRAM_TOKEN=ваш_токен
SUPABASE_URL=ваш_url
SUPABASE_KEY=ваш_ключ
RAILWAY_ENVIRONMENT=true
```

### 5. Webhook URL
После деплоя скопируйте URL приложения и добавьте:
```
WEBHOOK_URL=https://ваш-проект.railway.app
```

## Проверка работы
1. Откройте URL приложения → "Bot is running!"
2. Найдите бота в Telegram → `/start`
3. Проверьте логи в Railway Dashboard

## Готово! 🎉

Бот работает на Railway и автоматически перезапускается при обновлениях.
