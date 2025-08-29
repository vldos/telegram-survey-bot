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
from datetime import datetime
from supabase import create_client, Client

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

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
    },
    {
        "id": 6,
        "question": "Які фільтри були б вам корисні при виборі розваг? (можна обрати декілька варіантів)",
        "type": "multiple_choice",
        "options": [
            "Відстань від мене або вибраного місця",
            "Час/дата",
            "Ціна",
            "Тривалість",
            "Тип (активні, спокійні тощо)",
            "Кількість учасників",
            "Підходить для дітей/сім'ї",
            "Інше"
        ]
    },
    {
        "id": 7,
        "question": "Наскільки складно вам зазвичай знайти розваги, які вас цікавлять?",
        "type": "single_choice",
        "options": [
            "Дуже складно, все розкидано по різних сайтах",
            "Іноді важко",
            "Зазвичай швидко знаходжу",
            "Я не шукаю розваги спеціально"
        ]
    },
    {
        "id": 8,
        "question": "Ви зазвичай бронюєте щось заздалегідь чи приймаєте рішення в день активності?",
        "type": "single_choice",
        "options": [
            "Тільки заздалегідь",
            "Іноді заздалегідь, іноді в той же день",
            "Майже завжди в останній момент",
            "Взагалі не бронюю — все спонтанно"
        ]
    },
    {
        "id": 9,
        "question": "Було б вам цікаво, якби застосунок сам пропонував розваги за вашим настроєм, стилем відпочинку або погодою?",
        "type": "single_choice",
        "options": [
            "Так, було б зручно",
            "Можливо, якщо можна налаштовувати",
            "Ні, я сам обираю"
        ]
    },
    {
        "id": 10,
        "question": "Ви б хотіли користуватись таким застосунком?",
        "type": "single_choice",
        "options": [
            "Так, обов'язково спробую",
            "Залежить від зручності",
            "Скоріше за все, не буду"
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
        "id": "obstacles",
        "question": "Що вам зазвичай заважає знаходити розваги?",
        "type": "text"
    },
    {
        "id": "suggestions",
        "question": "Маєте ідеї або побажання до такого застосунку?",
        "type": "text"
    }
]

class DatabaseManager:
    def __init__(self):
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("✅ Подключение к Supabase установлено")
            except Exception as e:
                print(f"❌ Ошибка подключения к Supabase: {e}")
                self.supabase = None
        else:
            print("⚠️ SUPABASE_URL или SUPABASE_KEY не установлены")
            self.supabase = None
    
    def save_survey_response(self, user_id: int, username: str, answers: dict):
        """
        Сохраняет ответы пользователя в базу данных
        """
        if not self.supabase:
            print("❌ База данных недоступна")
            return False, "База данных недоступна"
        
        try:
            # Подготавливаем данные для сохранения
            survey_data = {
                "user_id": user_id,
                "username": username,
                "created_at": datetime.now().isoformat(),
                "answers": json.dumps(answers, ensure_ascii=False)
            }
            
            # Сохраняем в таблицу survey_responses
            result = self.supabase.table("survey_responses").insert(survey_data).execute()
            
            print(f"✅ Ответы пользователя {user_id} сохранены в базу данных")
            return True, "Ответы успешно сохранены"
        except Exception as e:
            print(f"❌ Ошибка при сохранении: {str(e)}")
            return False, f"Ошибка при сохранении: {str(e)}"
    
    def get_all_responses_count(self):
        """
        Получает количество всех ответов
        """
        if not self.supabase:
            return 0
        
        try:
            result = self.supabase.table("survey_responses").select("id", count="exact").execute()
            return result.count if hasattr(result, 'count') else 0
        except Exception as e:
            print(f"❌ Ошибка при получении количества ответов: {str(e)}")
            return 0

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

class FullTelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.user_states = {}  # Состояния пользователей
        self.user_answers = {}  # Ответы пользователей
        self.user_info = {}  # Информация о пользователях
        self.db = DatabaseManager()  # Менеджер базы данных
    
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
            
            # Сохраняем информацию о пользователе
            if chat_id not in self.user_info:
                self.user_info[chat_id] = {
                    "username": message.get("from", {}).get("username", ""),
                    "first_name": message.get("from", {}).get("first_name", ""),
                    "last_name": message.get("from", {}).get("last_name", "")
                }
            
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

📋 Описування складається з:
   • 10 основних питань (5-7 хвилин)
   • 4 додаткових питань (2-3 хвилини)

💾 Всі ваші відповіді будуть збережені анонімно в базі даних.

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
        elif text == "↩ Назад до варіантів":
            # Возвращаемся к вариантам ответов
            if "waiting_for_other" in state and state["waiting_for_other"]:
                state["waiting_for_other"] = False
                self.send_question(chat_id)
        elif (text.startswith("1.") or text.startswith("2.") or text.startswith("3.") or text.startswith("4.") or text.startswith("5.") or text.startswith("6.") or 
              text.startswith("☑ 1.") or text.startswith("☑ 2.") or text.startswith("☑ 3.") or text.startswith("☑ 4.") or text.startswith("☑ 5.") or text.startswith("☑ 6.") or
              text.startswith("☐ 1.") or text.startswith("☐ 2.") or text.startswith("☐ 3.") or text.startswith("☐ 4.") or text.startswith("☐ 5.") or text.startswith("☐ 6.")):
            self.process_answer(chat_id, text)
        elif state.get("waiting_for_other", False):
            # Обрабатываем ввод текста для "Інше"
            self.process_other_answer(chat_id, text)
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
            
            # Извлекаем номер опции, убирая возможные символы галочек
            clean_text = text.replace("☑ ", "").replace("☐ ", "")
            answer_index = int(clean_text.split(".")[0]) - 1
            
            if answer_index < len(question_data['options']):
                selected_answer = question_data['options'][answer_index]
                
                print(f"🔍 Обработка ответа: {text} -> {selected_answer}")
                
                # Проверяем, выбрал ли пользователь "Інше"
                if selected_answer == "Інше":
                    # Переводим в режим ввода текста для "Інше"
                    state["waiting_for_other"] = True
                    state["current_question_id"] = question_data['id']
                    state["question_type"] = question_data['type']
                    
                    keyboard = {
                        "keyboard": [[{"text": "↩ Назад до варіантів"}]],
                        "resize_keyboard": True
                    }
                    
                    self.send_message(chat_id, "📝 Будь ласка, введіть ваш варіант відповіді:", keyboard)
                    return
                
                if question_data['type'] == 'single_choice':
                    self.user_answers[chat_id][f"q{question_data['id']}"] = selected_answer
                    state["current_question"] += 1
                    self.send_question(chat_id)
                elif question_data['type'] == 'multiple_choice':
                    question_key = f"q{question_data['id']}"
                    if question_key not in self.user_answers[chat_id]:
                        self.user_answers[chat_id][question_key] = []
                    
                    current_answers = self.user_answers[chat_id][question_key]
                    print(f"📊 Текущие ответы для вопроса {question_data['id']}: {current_answers}")
                    print(f"🎯 Выбранный ответ: {selected_answer}")
                    print(f"🔍 Тип current_answers: {type(current_answers)}")
                    
                    if selected_answer in current_answers:
                        current_answers.remove(selected_answer)
                        print(f"❌ Удален ответ: {selected_answer}")
                    else:
                        current_answers.append(selected_answer)
                        print(f"✅ Добавлен ответ: {selected_answer}")
                    
                    print(f"📊 Обновленные ответы: {self.user_answers[chat_id][question_key]}")
                    
                    # Обновляем клавиатуру
                    self.update_multiple_choice_keyboard(chat_id, question_data)
    
    def update_multiple_choice_keyboard(self, chat_id, question_data):
        """Обновляет клавиатуру для множественного выбора"""
        question_key = f"q{question_data['id']}"
        current_answers = self.user_answers[chat_id].get(question_key, [])
        
        print(f"🔄 Обновление клавиатуры для вопроса {question_data['id']}")
        print(f"📊 Ключ вопроса: {question_key}")
        print(f"📊 Текущие ответы: {current_answers}")
        print(f"🔍 Тип current_answers: {type(current_answers)}")
        print(f"🔍 Все ответы пользователя: {self.user_answers[chat_id]}")
        
        keyboard = []
        for i, option in enumerate(question_data['options'], 1):
            # Проверяем, выбрана ли опция
            is_selected = option in current_answers
            
            # Если это опция "Інше", проверяем также наличие ответов "Інше:"
            if option == "Інше":
                has_other_answer = any(answer.startswith("Інше:") for answer in current_answers if isinstance(answer, str))
                is_selected = is_selected or has_other_answer
            
            button_text = f"☑ {i}. {option}" if is_selected else f"☐ {i}. {option}"
            keyboard.append([{"text": button_text}])
            
            print(f"   {i}. {option}: {'☑' if is_selected else '☐'} (в списке: {option in current_answers})")
        
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
    
    def process_other_answer(self, chat_id, text):
        """Обрабатывает ввод текста для опции 'Інше'"""
        state = self.user_states[chat_id]
        question_id = state["current_question_id"]
        question_type = state["question_type"]
        
        # Сохраняем введенный текст
        if question_type == 'single_choice':
            self.user_answers[chat_id][f"q{question_id}"] = f"Інше: {text}"
        elif question_type == 'multiple_choice':
            if f"q{question_id}" not in self.user_answers[chat_id]:
                self.user_answers[chat_id][f"q{question_id}"] = []
            self.user_answers[chat_id][f"q{question_id}"].append(f"Інше: {text}")
        
        # Очищаем состояние ожидания
        state["waiting_for_other"] = False
        if "current_question_id" in state:
            del state["current_question_id"]
        if "question_type" in state:
            del state["question_type"]
        
        # Переходим к следующему вопросу
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
        """Завершает опрос и сохраняет в базу данных"""
        # Сохраняем ответы в базу данных
        username = self.user_info.get(chat_id, {}).get("username", "")
        if not username:
            username = f"user_{chat_id}"
        
        success, message = self.db.save_survey_response(chat_id, username, self.user_answers[chat_id])
        
        if success:
            finish_text = """
🎉 Дякуємо за участь в опитуванні!

✅ Ваші відповіді успішно збережені в базу даних.
📊 Це допоможе нам створити кращий сервіс для пошуку розваг та активностей.

Бот працює на Railway! 🚂
            """
        else:
            finish_text = """
🎉 Дякуємо за участь в опитуванні!

⚠️ Ваші відповіді збережені локально, але виникла проблема з базою даних.
📊 Ми все одно використаємо ваші відповіді для аналізу.

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
        db_count = self.db.get_all_responses_count()
        active_surveys = len(self.user_states)
        
        stats_text = f"""
📊 Статистика опитування:

🗄️ Всього відповідей в базі даних: {db_count}
🔄 Активних опросів: {active_surveys}

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
    
    # Проверяем настройки базы данных
    if SUPABASE_URL and SUPABASE_KEY:
        print("✅ Настройки Supabase найдены")
    else:
        print("⚠️ Настройки Supabase не найдены - ответы будут сохраняться только локально")
    
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
