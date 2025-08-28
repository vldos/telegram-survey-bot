#!/usr/bin/env python3
"""
Упрощенная версия Telegram бота для Railway
"""

import os
import asyncio
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import requests
import json

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"🏥 GET запрос: {self.path}")
        print(f"🏥 От: {self.client_address[0]}")
        print(f"🏥 User-Agent: {self.headers.get('User-Agent', 'Unknown')}")
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        
        response = "Telegram Bot is running! 🤖"
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        print(f"📝 {format % args}")

def run_health_server():
    """Запускает простой HTTP сервер для health check"""
    try:
        port = int(os.getenv('PORT', 8080))
        print(f"🔧 Запуск health check сервера на порту {port}")
        print(f"🔧 Переменные окружения:")
        for key, value in os.environ.items():
            if key in ['PORT', 'RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_ID', 'TELEGRAM_TOKEN']:
                print(f"   {key}={value[:10] + '...' if len(value) > 10 else value}")
        
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f"🚀 Health check сервер запущен на порту {port}")
        print("📡 Ожидание запросов...")
        
        server.serve_forever()
        
    except Exception as e:
        print(f"❌ Ошибка health check сервера: {e}")
        import traceback
        traceback.print_exc()

class SimpleTelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
    
    def send_message(self, chat_id, text):
        """Отправляет сообщение в Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print(f"✅ Сообщение отправлено в {chat_id}")
            else:
                print(f"❌ Ошибка отправки: {response.text}")
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения: {e}")
    
    def get_updates(self):
        """Получает обновления от Telegram"""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                "offset": self.offset,
                "timeout": 30
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        self.handle_update(update)
                        self.offset = update["update_id"] + 1
        except Exception as e:
            print(f"❌ Ошибка получения обновлений: {e}")
    
    def handle_update(self, update):
        """Обрабатывает обновление от Telegram"""
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "")
            
            print(f"📨 Получено сообщение от {chat_id}: {text}")
            
            if text == "/start":
                welcome_text = """
🤖 Привіт! Я бот для збору відповідей на питання про пошук розваг та активностей.

📋 Описування займе приблизно 5-10 хвилин.
💾 Всі ваші відповіді будуть збережені анонімно.

Готові почати опитування? Відправте "Почати" для початку!
                """
                self.send_message(chat_id, welcome_text)
            
            elif text.lower() in ["почати", "start", "начать"]:
                survey_text = """
🎯 Чудово! Починаємо опитування.

❓ Питання 1: Де ви частіше шукаєте, чим зайнятись у вільний час?

Варіанти відповідей:
1. У подорожах
2. У своєму місті
3. І там, і там
4. Я не шукаю спеціально

Відправте номер відповіді (1-4):
                """
                self.send_message(chat_id, survey_text)
            
            else:
                help_text = """
💡 Доступні команди:
/start - Почати роботу з ботом
Почати - Почати опитування

Бот працює в тестовому режимі на Railway! 🚂
                """
                self.send_message(chat_id, help_text)

def run_telegram_bot():
    """Запускает Telegram бота"""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("❌ TELEGRAM_TOKEN не найден")
        return
    
    bot = SimpleTelegramBot(token)
    print("🤖 Telegram бот запущен")
    
    try:
        while True:
            bot.get_updates()
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Telegram бот остановлен")

def main():
    """Основная функция"""
    print("🤖 Запуск упрощенного Telegram бота...")
    
    # Проверяем переменные окружения
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    if not telegram_token:
        print("⚠️ TELEGRAM_TOKEN не установлен, запускаем только health check сервер")
        run_health_server()
        return
    
    print("✅ TELEGRAM_TOKEN найден")
    
    # Запускаем health check сервер в отдельном потоке
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    print("🔄 Запуск основного бота...")
    
    # Запускаем Telegram бота в отдельном потоке
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    print("✅ Все компоненты запущены")
    
    # Ждем завершения
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Получен сигнал остановки")

if __name__ == "__main__":
    main()
