#!/usr/bin/env python3
"""
Максимально простой сервер для диагностики Railway
"""

import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"🏥 GET запрос: {self.path}")
        print(f"🏥 От: {self.client_address[0]}")
        print(f"🏥 User-Agent: {self.headers.get('User-Agent', 'Unknown')}")
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        
        response = "Simple server is running! 🚀"
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        print(f"📝 {format % args}")

def main():
    try:
        port = int(os.getenv('PORT', 8080))
        print(f"🔧 Запуск простого сервера на порту {port}")
        print(f"🔧 PID: {os.getpid()}")
        print(f"🔧 Python: {sys.version}")
        print(f"🔧 Переменные окружения:")
        for key, value in os.environ.items():
            if key in ['PORT', 'RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_ID']:
                print(f"   {key}={value}")
        
        server = HTTPServer(('0.0.0.0', port), SimpleHandler)
        print(f"🚀 Сервер запущен на порту {port}")
        print("📡 Ожидание запросов...")
        
        server.serve_forever()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
