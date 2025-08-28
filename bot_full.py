#!/usr/bin/env python3
"""
Полнофункциональная версия Telegram бота для Railway
"""

import os
import asyncio
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import requests
import json

# Конфигурация вопросов
QUESTIONS = [
    {
        "id": 1,
        "question": "Де ви частіше шукаєте, чим зайнятись у вільний час?",
        "type": "single_choice",
        "options": [
            "У подорожах",
            "У своєму місті", 
            "І там, і там",
            "Я не шукаю спеціально"
        ]
    },
    {
        "id": 2,
        "question": "Як ви зазвичай знаходите розваги? (можна обрати декілька варіантів)",
        "type": "multiple_choice",
        "options": [
            "Через Google",
            "Через карти (Google Maps, 2ГІС тощо)",
            "Через друзів/знайомих",
            "Через соцмережі (Instagram, Telegram-канали тощо)",
            "Через сайти-агрегатори або сервіси",
            "Я не шукаю — все виходить спонтанно"
        ]
    },
    {
        "id": 3,
        "question": "Буває, що ви точно знаєте, чим хочете зайнятись (наприклад, покататись на квадроциклах, поїхати на риболовлю), але не знаєте, де це знайти?",
        "type": "single_choice",
        "options": [
            "Так, часто",
            "Іноді",
            "Ні, легко знаходжу",
            "Я не шукаю такі активності"
        ]
    },
    {
        "id": 4,
        "question": "Якщо ви просто хочете \"щось активне\" або \"відпочити\", але без конкретної ідеї — як ви шукаєте варіанти?",
        "type": "single_choice",
        "options": [
            "Просто гуглю \"що робити в [місті]\"",
            "Дивлюсь у соцмережах/каналах",
            "Питаю у друзів",
            "Не шукаю — якщо не знаю, чого хочу, значить і не треба",
            "Інше"
        ]
    },
    {
        "id": 5,
        "question": "Було б вам зручно бачити всі доступні розваги поруч на карті, з фільтрами за типом, часом, бюджетом тощо?",
        "type": "single_choice",
        "options": [
            "Так, це зручно і цікаво",
            "Можливо, якщо все буде просто",
            "Не думаю, що це мені потрібно"
        ]
    }
]

ADDITIONAL_QUESTIONS = [
    {
        "id": "age",
        "question": "Вік:",
        "type": "text"
    },
    {
        "id": "city",
        "question": "Місто:",
        "type": "text"
    },
    {
        "id": "suggestions",
        "question": "Маєте ідеї або побажання до такого застосунку?",
        "type": "text"
    }
]

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

class FullTelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.user_states = {}  # Состояния пользователей
        self.user_answers = {}  # Ответы пользователей
    
    def send_message(self, chat_id, text, reply_markup=None):
        """Отправляет сообщение в Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            if reply_markup:
                data["reply_markup"] = reply_markup
            
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print(f"✅ Сообщение отправлено в {chat_id}")
            else:
                print(f"❌ Ошибка отправки: {response.text}")
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения: {e}")
    
    def create_keyboard(self, options, question_type="single_choice"):
        """Создает клавиатуру для ответов"""
        keyboard = []
        
        if question_type == "single_choice":
            for i, option in enumerate(options, 1):
                keyboard.append([{"text": f"{i}. {option}"}])
        elif question_type == "multiple_choice":
            for i, option in enumerate(options, 1):
                keyboard.append([{"text": f"{i}. {option}"}])
            keyboard.append([{"text": "✅ Завершити вибір"}])
        
        return {
            "keyboard": keyboard,
            "resize_keyboard": True,
            "one_time_keyboard": True
        }
    
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
                self.start_survey(chat_id)
            elif text == "/stats":
                self.show_stats(chat_id)
            else:
                self.handle_answer(chat_id, text)
    
    def start_survey(self, chat_id):
        """Начинает опрос"""
        self.user_states[chat_id] = {"current_question": 0, "phase": "main"}
        self.user_answers[chat_id] = {}
        
        welcome_text = """
🤖 Привіт! Я бот для збору відповідей на питання про пошук розваг та активностей.

📋 Описування займе приблизно 5-10 хвилин.
💾 Всі ваші відповіді будуть збережені анонімно.

Готові почати опитування? Натисніть кнопку нижче!
        """
        
        keyboard = {
            "keyboard": [[{"text": "🚀 Почати опитування"}]],
            "resize_keyboard": True
        }
        
        self.send_message(chat_id, welcome_text, keyboard)
    
    def handle_answer(self, chat_id, text):
        """Обрабатывает ответ пользователя"""
        if chat_id not in self.user_states:
            self.send_message(chat_id, "Використайте /start для початку опитування.")
            return
        
        state = self.user_states[chat_id]
        
        if text == "🚀 Почати опитування":
            self.send_question(chat_id)
        elif text == "✅ Завершити вибір":
            self.finish_multiple_choice(chat_id)
        elif text.startswith("1.") or text.startswith("2.") or text.startswith("3.") or text.startswith("4.") or text.startswith("5.") or text.startswith("6."):
            self.process_answer(chat_id, text)
        elif state["phase"] == "additional":
            self.process_text_answer(chat_id, text)
        else:
            self.send_message(chat_id, "Будь ласка, використайте кнопки для відповіді.")
    
    def send_question(self, chat_id):
        """Отправляет текущий вопрос"""
        state = self.user_states[chat_id]
        current_question = state["current_question"]
        
        if state["phase"] == "main":
            if current_question < len(QUESTIONS):
                question_data = QUESTIONS[current_question]
                question_text = f"❓ {question_data['question']}"
                
                keyboard = self.create_keyboard(question_data['options'], question_data['type'])
                self.send_message(chat_id, question_text, keyboard)
            else:
                # Переходим к дополнительным вопросам
                state["phase"] = "additional"
                state["current_question"] = 0
                self.send_additional_question(chat_id)
        elif state["phase"] == "additional":
            if current_question < len(ADDITIONAL_QUESTIONS):
                self.send_additional_question(chat_id)
            else:
                self.finish_survey(chat_id)
    
    def send_additional_question(self, chat_id):
        """Отправляет дополнительный вопрос"""
        state = self.user_states[chat_id]
        current_question = state["current_question"]
        question_data = ADDITIONAL_QUESTIONS[current_question]
        
        question_text = f"📝 {question_data['question']}"
        keyboard = {
            "keyboard": [[{"text": "⏭ Пропустити"}]],
            "resize_keyboard": True
        }
        
        self.send_message(chat_id, question_text, keyboard)
    
    def process_answer(self, chat_id, text):
        """Обрабатывает ответ на вопрос"""
        state = self.user_states[chat_id]
        current_question = state["current_question"]
        
        if state["phase"] == "main":
            question_data = QUESTIONS[current_question]
            answer_index = int(text.split(".")[0]) - 1
            
            if answer_index < len(question_data['options']):
                selected_answer = question_data['options'][answer_index]
                
                if question_data['type'] == 'single_choice':
                    self.user_answers[chat_id][f"q{question_data['id']}"] = selected_answer
                    state["current_question"] += 1
                    self.send_question(chat_id)
                elif question_data['type'] == 'multiple_choice':
                    if f"q{question_data['id']}" not in self.user_answers[chat_id]:
                        self.user_answers[chat_id][f"q{question_data['id']}"] = []
                    
                    if selected_answer in self.user_answers[chat_id][f"q{question_data['id']}"]:
                        self.user_answers[chat_id][f"q{question_data['id']}"].remove(selected_answer)
                    else:
                        self.user_answers[chat_id][f"q{question_data['id']}"].append(selected_answer)
                    
                    # Обновляем клавиатуру
                    self.update_multiple_choice_keyboard(chat_id, question_data)
    
    def update_multiple_choice_keyboard(self, chat_id, question_data):
        """Обновляет клавиатуру для множественного выбора"""
        current_answers = self.user_answers[chat_id].get(f"q{question_data['id']}", [])
        
        keyboard = []
        for i, option in enumerate(question_data['options'], 1):
            if option in current_answers:
                keyboard.append([{"text": f"☑ {i}. {option}"}])
            else:
                keyboard.append([{"text": f"☐ {i}. {option}"}])
        
        keyboard.append([{"text": "✅ Завершити вибір"}])
        
        reply_markup = {
            "keyboard": keyboard,
            "resize_keyboard": True
        }
        
        question_text = f"❓ {question_data['question']}"
        self.send_message(chat_id, question_text, reply_markup)
    
    def finish_multiple_choice(self, chat_id):
        """Завершает множественный выбор"""
        state = self.user_states[chat_id]
        state["current_question"] += 1
        self.send_question(chat_id)
    
    def process_text_answer(self, chat_id, text):
        """Обрабатывает текстовый ответ"""
        state = self.user_states[chat_id]
        current_question = state["current_question"]
        question_data = ADDITIONAL_QUESTIONS[current_question]
        
        if text == "⏭ Пропустити":
            pass
        else:
            self.user_answers[chat_id][question_data['id']] = text
        
        state["current_question"] += 1
        self.send_question(chat_id)
    
    def finish_survey(self, chat_id):
        """Завершает опрос"""
        finish_text = """
🎉 Дякуємо за участь в опитуванні!

Ваші відповіді успішно збережені. Це допоможе нам створити кращий сервіс для пошуку розваг та активностей.

Бот працює на Railway! 🚂
        """
        
        # Очищаем состояние пользователя
        if chat_id in self.user_states:
            del self.user_states[chat_id]
        if chat_id in self.user_answers:
            del self.user_answers[chat_id]
        
        keyboard = {
            "keyboard": [[{"text": "🏠 Головна"}]],
            "resize_keyboard": True
        }
        
        self.send_message(chat_id, finish_text, keyboard)
        print(f"📊 Опрос завершен для пользователя {chat_id}")
    
    def show_stats(self, chat_id):
        """Показывает статистику"""
        stats_text = f"""
📊 Статистика опитування:

Активних опросов: {len(self.user_states)}
Завершенных опросов: {len([k for k in self.user_answers.keys() if k not in self.user_states])}

Бот працює на Railway! 🚂
        """
        self.send_message(chat_id, stats_text)

def run_telegram_bot():
    """Запускает Telegram бота"""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("❌ TELEGRAM_TOKEN не найден")
        return
    
    bot = FullTelegramBot(token)
    print("🤖 Полнофункциональный Telegram бот запущен")
    
    try:
        while True:
            bot.get_updates()
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Telegram бот остановлен")

def main():
    """Основная функция"""
    print("🤖 Запуск полнофункционального Telegram бота...")
    
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
