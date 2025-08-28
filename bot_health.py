#!/usr/bin/env python3
"""
Простая версия бота только для health check
"""

import os
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
            if key in ['PORT', 'RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_ID', 'TELEGRAM_TOKEN', 'SUPABASE_URL']:
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
    print("🤖 Запуск простого health check сервера...")
    
    # Проверяем переменные окружения
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    if telegram_token:
        print("✅ TELEGRAM_TOKEN найден")
    else:
        print("⚠️ TELEGRAM_TOKEN не установлен")
    
    # Проверяем настройки базы данных
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    if supabase_url and supabase_key:
        print("✅ Настройки Supabase найдены")
    else:
        print("⚠️ Настройки Supabase не найдены")
    
    # Запускаем health check сервер
    run_health_server()

if __name__ == "__main__":
    main()
