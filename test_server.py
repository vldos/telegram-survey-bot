#!/usr/bin/env python3
"""
Простой тестовый сервер для проверки health check на Railway
"""

import os
import asyncio
import sys
from aiohttp import web

async def health_check(request):
    """Простой health check endpoint"""
    print(f"🏥 Health check запрос от {request.remote}")
    print(f"🏥 User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    print(f"🏥 Method: {request.method}")
    print(f"🏥 Path: {request.path}")
    
    return web.Response(
        text="Test server is running! 🚀", 
        status=200,
        content_type='text/plain'
    )

async def main():
    """Запуск тестового сервера"""
    try:
        port = int(os.getenv('PORT', 8080))
        print(f"🔧 Запуск тестового сервера на порту {port}")
        print(f"🔧 Переменные окружения: PORT={os.getenv('PORT')}")
        
        app = web.Application()
        app.router.add_get('/', health_check)
        app.router.add_get('/health', health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        print(f"🚀 Тестовый сервер запущен на порту {port}")
        print("📡 Ожидание запросов...")
        print("📡 Доступные пути: /, /health")
        
        # Держим сервер запущенным
        try:
            await asyncio.Future()  # Бесконечное ожидание
        except KeyboardInterrupt:
            print("🛑 Получен сигнал остановки")
            await runner.cleanup()
            
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
