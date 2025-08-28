#!/usr/bin/env python3
"""
Простой тестовый сервер для проверки health check на Railway
"""

import os
import asyncio
from aiohttp import web

async def health_check(request):
    """Простой health check endpoint"""
    print(f"🏥 Health check запрос от {request.remote}")
    return web.Response(
        text="Test server is running! 🚀", 
        status=200,
        content_type='text/plain'
    )

async def main():
    """Запуск тестового сервера"""
    port = int(os.getenv('PORT', 8080))
    
    print(f"🔧 Запуск тестового сервера на порту {port}")
    
    app = web.Application()
    app.router.add_get('/', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"🚀 Тестовый сервер запущен на порту {port}")
    print("📡 Ожидание запросов...")
    
    try:
        await asyncio.Future()  # Бесконечное ожидание
    except KeyboardInterrupt:
        print("🛑 Получен сигнал остановки")
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
