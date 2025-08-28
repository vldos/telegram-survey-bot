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
    
    # Здесь можно добавить логику Telegram бота
    # Пока просто ждем
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Получен сигнал остановки")

if __name__ == "__main__":
    main()
