import asyncio
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import TELEGRAM_TOKEN, QUESTIONS, ADDITIONAL_QUESTIONS
from database import DatabaseManager
import json
from aiohttp import web
import ssl

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SurveyBot:
    def __init__(self):
        self.db = DatabaseManager()
        self.user_states = {}  # Состояния пользователей
        self.user_answers = {}  # Ответы пользователей
        self.waiting_for_other = {}  # Ожидание ввода для "Інше"
        self.application = None
        self.webhook_url = os.getenv('WEBHOOK_URL', '')
        self.port = int(os.getenv('PORT', 8080))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        username = user.username or user.first_name
        
        welcome_text = f"""
Привіт, {user.first_name}! 👋

Я бот для збору відповідей на питання про пошук розваг та активностей.

📋 Описування займе приблизно 5-10 хвилин.
💾 Всі ваші відповіді будуть збережені анонімно.

Готові почати опитування? Натисніть кнопку нижче!
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 Почати опитування", callback_data="start_survey")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback кнопок"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "start_survey":
            # Начинаем опрос
            self.user_states[user_id] = {"current_question": 0, "phase": "main"}
            self.user_answers[user_id] = {}
            await self.send_question(query, user_id)
        
        elif query.data.startswith("answer_"):
            # Обработка ответа на вопрос
            await self.handle_answer(query, user_id)
        elif query.data.startswith("finish_multi_"):
            # Завершение множественного выбора
            await self.handle_finish_multiple_choice(query, user_id)
    
    async def send_question(self, query, user_id):
        """Отправляет текущий вопрос пользователю"""
        state = self.user_states[user_id]
        current_question = state["current_question"]
        
        if state["phase"] == "main":
            if current_question < len(QUESTIONS):
                question_data = QUESTIONS[current_question]
                await self.send_main_question(query, question_data, user_id)
            else:
                # Переходим к дополнительным вопросам
                state["phase"] = "additional"
                state["current_question"] = 0
                await self.send_additional_question(query, user_id)
        
        elif state["phase"] == "additional":
            if current_question < len(ADDITIONAL_QUESTIONS):
                question_data = ADDITIONAL_QUESTIONS[current_question]
                await self.send_additional_question(query, user_id, question_data)
            else:
                # Завершаем опрос
                await self.finish_survey(query, user_id)
    
    async def send_main_question(self, query, question_data, user_id):
        """Отправляет основной вопрос с вариантами ответов"""
        question_text = f"❓ {question_data['question']}"
        
        if question_data['type'] == 'single_choice':
            keyboard = []
            for i, option in enumerate(question_data['options']):
                keyboard.append([InlineKeyboardButton(
                    option, 
                    callback_data=f"answer_{question_data['id']}_{i}"
                )])
        elif question_data['type'] == 'multiple_choice':
            keyboard = []
            for i, option in enumerate(question_data['options']):
                keyboard.append([InlineKeyboardButton(
                    f"☐ {option}", 
                    callback_data=f"answer_{question_data['id']}_{i}_multi"
                )])
            keyboard.append([InlineKeyboardButton("✅ Завершити вибір", callback_data=f"finish_multi_{question_data['id']}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query.message:
            await query.message.edit_text(question_text, reply_markup=reply_markup)
        else:
            await query.message.reply_text(question_text, reply_markup=reply_markup)
    
    async def send_additional_question(self, query, user_id, question_data=None):
        """Отправляет дополнительный вопрос"""
        if not question_data:
            question_data = ADDITIONAL_QUESTIONS[self.user_states[user_id]["current_question"]]
        
        question_text = f"📝 {question_data['question']}"
        
        # Для текстовых вопросов используем обычную клавиатуру
        keyboard = [[KeyboardButton("⏭ Пропустити")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        if query.message:
            await query.message.edit_text(question_text)
            await query.message.reply_text("Введіть ваш відповідь:", reply_markup=reply_markup)
        else:
            await query.message.reply_text(question_text)
            await query.message.reply_text("Введіть ваш відповідь:", reply_markup=reply_markup)
    
    async def handle_answer(self, query, user_id):
        """Обрабатывает ответ пользователя"""
        data = query.data.split("_")
        
        if len(data) >= 3:
            question_id = int(data[1])
            answer_index = int(data[2])
            
            if len(data) > 3 and data[3] == "multi":
                # Множественный выбор
                await self.handle_multiple_choice(query, user_id, question_id, answer_index)
            else:
                # Одиночный выбор
                await self.handle_single_choice(query, user_id, question_id, answer_index)
    
    async def handle_single_choice(self, query, user_id, question_id, answer_index):
        """Обрабатывает одиночный выбор"""
        question_data = QUESTIONS[question_id - 1]  # -1 потому что id начинается с 1
        selected_answer = question_data['options'][answer_index]
        
        print(f"DEBUG: handle_single_choice - question_id={question_id}, answer_index={answer_index}, selected_answer='{selected_answer}'")
        
        # Проверяем, является ли выбранный ответ "Інше"
        if selected_answer == "Інше":
            print(f"DEBUG: Обнаружено 'Інше' для пользователя {user_id}")
            # Сохраняем состояние ожидания ввода для "Інше"
            self.waiting_for_other[user_id] = {
                "question_id": question_id,
                "type": "single",
                "message_id": query.message.message_id
            }
            
            # Запрашиваем ввод собственного варианта
            keyboard = [[KeyboardButton("⏭ Пропустити")]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            
            await query.message.edit_text(f"❓ {question_data['question']}\n\nВведіть ваш варіант для 'Інше':")
            await query.message.reply_text("Введіть ваш варіант:", reply_markup=reply_markup)
            return
        
        # Сохраняем ответ
        if user_id not in self.user_answers:
            self.user_answers[user_id] = {}
        
        self.user_answers[user_id][f"q{question_id}"] = selected_answer
        
        # Переходим к следующему вопросу
        self.user_states[user_id]["current_question"] += 1
        await self.send_question(query, user_id)
    
    async def handle_multiple_choice(self, query, user_id, question_id, answer_index):
        """Обрабатывает множественный выбор"""
        question_data = QUESTIONS[question_id - 1]
        selected_answer = question_data['options'][answer_index]
        
        print(f"DEBUG: handle_multiple_choice - question_id={question_id}, answer_index={answer_index}, selected_answer='{selected_answer}'")
        
        # Проверяем, является ли выбранный ответ "Інше"
        if selected_answer == "Інше":
            print(f"DEBUG: Обнаружено 'Інше' для пользователя {user_id} (множественный выбор)")
            # Сохраняем состояние ожидания ввода для "Інше"
            self.waiting_for_other[user_id] = {
                "question_id": question_id,
                "type": "multiple",
                "message_id": query.message.message_id
            }
            
            # Запрашиваем ввод собственного варианта
            keyboard = [[KeyboardButton("⏭ Пропустити")]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            
            await query.message.edit_text(f"❓ {question_data['question']}\n\nВведіть ваш варіант для 'Інше':")
            await query.message.reply_text("Введіть ваш варіант:", reply_markup=reply_markup)
            return
        
        # Инициализируем список ответов для этого вопроса
        if user_id not in self.user_answers:
            self.user_answers[user_id] = {}
        
        if f"q{question_id}" not in self.user_answers[user_id]:
            self.user_answers[user_id][f"q{question_id}"] = []
        
        # Добавляем или удаляем ответ
        if selected_answer in self.user_answers[user_id][f"q{question_id}"]:
            self.user_answers[user_id][f"q{question_id}"].remove(selected_answer)
        else:
            self.user_answers[user_id][f"q{question_id}"].append(selected_answer)
        
        # Обновляем клавиатуру
        await self.update_multiple_choice_keyboard(query, question_data, user_id, question_id)
    
    async def handle_finish_multiple_choice(self, query, user_id):
        """Обрабатывает завершение множественного выбора"""
        data = query.data.split("_")
        question_id = int(data[2])  # finish_multi_2 -> question_id = 2
        
        # Переходим к следующему вопросу
        self.user_states[user_id]["current_question"] += 1
        await self.send_question(query, user_id)
    
    async def update_multiple_choice_keyboard(self, query, question_data, user_id, question_id):
        """Обновляет клавиатуру для множественного выбора"""
        keyboard = []
        current_answers = self.user_answers[user_id].get(f"q{question_id}", [])
        
        for i, option in enumerate(question_data['options']):
            if option in current_answers:
                keyboard.append([InlineKeyboardButton(
                    f"☑ {option}", 
                    callback_data=f"answer_{question_id}_{i}_multi"
                )])
            else:
                keyboard.append([InlineKeyboardButton(
                    f"☐ {option}", 
                    callback_data=f"answer_{question_id}_{i}_multi"
                )])
        
        keyboard.append([InlineKeyboardButton("✅ Завершити вибір", callback_data=f"finish_multi_{question_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_reply_markup(reply_markup=reply_markup)
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает текстовые сообщения для дополнительных вопросов и "Інше" """
        user_id = update.effective_user.id
        text = update.message.text
        
        print(f"DEBUG: handle_text_message - user_id={user_id}, text='{text}'")
        print(f"DEBUG: waiting_for_other keys: {list(self.waiting_for_other.keys())}")
        
        if user_id not in self.user_states:
            await update.message.reply_text("Використайте /start для початку опитування.")
            return
        
        # Проверяем, ожидаем ли мы ввод для "Інше"
        if user_id in self.waiting_for_other:
            print(f"DEBUG: Обрабатываем ввод для 'Інше' пользователя {user_id}")
            await self.handle_other_input(update, user_id, text)
            return
        
        state = self.user_states[user_id]
        
        if state["phase"] == "additional":
            current_question = state["current_question"]
            question_data = ADDITIONAL_QUESTIONS[current_question]
            
            if text == "⏭ Пропустити":
                # Пропускаем вопрос
                pass
            else:
                # Сохраняем ответ
                if user_id not in self.user_answers:
                    self.user_answers[user_id] = {}
                
                self.user_answers[user_id][question_data['id']] = text
            
            # Переходим к следующему вопросу
            state["current_question"] += 1
            
            if state["current_question"] < len(ADDITIONAL_QUESTIONS):
                next_question = ADDITIONAL_QUESTIONS[state["current_question"]]
                await self.send_additional_question_text(update, next_question)
            else:
                await self.finish_survey_text(update, user_id)
    
    async def handle_other_input(self, update, user_id, text):
        """Обрабатывает ввод для опции "Інше" """
        print(f"DEBUG: handle_other_input - user_id={user_id}, text='{text}'")
        
        other_data = self.waiting_for_other[user_id]
        question_id = other_data["question_id"]
        input_type = other_data["type"]
        
        print(f"DEBUG: other_data={other_data}")
        
        if text == "⏭ Пропустити":
            # Пропускаем ввод "Інше"
            print(f"DEBUG: Пропускаем ввод 'Інше' для пользователя {user_id}")
            pass
        else:
            # Сохраняем собственный вариант
            if user_id not in self.user_answers:
                self.user_answers[user_id] = {}
            
            if input_type == "single":
                # Для одиночного выбора заменяем "Інше" на введенный текст
                self.user_answers[user_id][f"q{question_id}"] = f"Інше: {text}"
                print(f"DEBUG: Сохранен одиночный выбор: {self.user_answers[user_id][f'q{question_id}']}")
            else:
                # Для множественного выбора добавляем к существующим ответам
                if f"q{question_id}" not in self.user_answers[user_id]:
                    self.user_answers[user_id][f"q{question_id}"] = []
                
                # Добавляем собственный вариант
                self.user_answers[user_id][f"q{question_id}"].append(f"Інше: {text}")
                print(f"DEBUG: Добавлен к множественному выбору: {self.user_answers[user_id][f'q{question_id}']}")
        
        # Удаляем состояние ожидания
        del self.waiting_for_other[user_id]
        print(f"DEBUG: Удалено состояние ожидания для пользователя {user_id}")
        
        # Переходим к следующему вопросу
        self.user_states[user_id]["current_question"] += 1
        
        # Отправляем следующий вопрос
        state = self.user_states[user_id]
        if state["phase"] == "main":
            if state["current_question"] < len(QUESTIONS):
                question_data = QUESTIONS[state["current_question"]]
                await self.send_main_question_text(update, question_data, user_id)
            else:
                # Переходим к дополнительным вопросам
                state["phase"] = "additional"
                state["current_question"] = 0
                await self.send_additional_question_text(update, ADDITIONAL_QUESTIONS[0])
        elif state["phase"] == "additional":
            if state["current_question"] < len(ADDITIONAL_QUESTIONS):
                question_data = ADDITIONAL_QUESTIONS[state["current_question"]]
                await self.send_additional_question_text(update, question_data)
            else:
                await self.finish_survey_text(update, user_id)
    
    async def send_main_question_text(self, update, question_data, user_id):
        """Отправляет основной вопрос текстом (для продолжения после "Інше")"""
        question_text = f"❓ {question_data['question']}"
        
        if question_data['type'] == 'single_choice':
            keyboard = []
            for i, option in enumerate(question_data['options']):
                keyboard.append([InlineKeyboardButton(
                    option, 
                    callback_data=f"answer_{question_data['id']}_{i}"
                )])
        elif question_data['type'] == 'multiple_choice':
            keyboard = []
            for i, option in enumerate(question_data['options']):
                keyboard.append([InlineKeyboardButton(
                    f"☐ {option}", 
                    callback_data=f"answer_{question_data['id']}_{i}_multi"
                )])
            keyboard.append([InlineKeyboardButton("✅ Завершити вибір", callback_data=f"finish_multi_{question_data['id']}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(question_text, reply_markup=reply_markup)
    
    async def send_additional_question_text(self, update, question_data):
        """Отправляет дополнительный вопрос текстом"""
        question_text = f"📝 {question_data['question']}"
        keyboard = [[KeyboardButton("⏭ Пропустити")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(question_text)
        await update.message.reply_text("Введіть ваш відповідь:", reply_markup=reply_markup)
    
    async def finish_survey(self, query, user_id):
        """Завершает опрос"""
        await self.save_and_finish(query.message, user_id)
    
    async def finish_survey_text(self, update, user_id):
        """Завершает опрос для текстовых сообщений"""
        await self.save_and_finish(update.message, user_id)
    
    async def save_and_finish(self, message, user_id):
        """Сохраняет ответы и завершает опрос"""
        user = message.from_user
        username = user.username or user.first_name
        
        # Сохраняем в базу данных
        success, result_message = self.db.save_survey_response(
            user_id, username, self.user_answers[user_id]
        )
        
        if success:
            finish_text = """
🎉 Дякуємо за участь в опитуванні!

Ваші відповіді успішно збережені. Це допоможе нам створити кращий сервіс для пошуку розваг та активностей.

            """
        else:
            finish_text = f"""
❌ Виникла помилка при збереженні відповідей: {result_message}

Спробуйте ще раз або зверніться до адміністратора.
            """
        
        # Очищаем состояние пользователя
        if user_id in self.user_states:
            del self.user_states[user_id]
        if user_id in self.user_answers:
            del self.user_answers[user_id]
        if user_id in self.waiting_for_other:
            del self.waiting_for_other[user_id]
        
        # Убираем клавиатуру
        keyboard = [[KeyboardButton("🏠 Головна")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await message.reply_text(finish_text, reply_markup=reply_markup)
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для просмотра статистики (только для админов)"""
        # Здесь можно добавить проверку на админа
        responses = self.db.get_all_responses()
        
        stats_text = f"""
📊 Статистика опитування:

Загальна кількість відповідей: {len(responses)}

Останні 5 відповідей:
        """
        
        for i, response in enumerate(responses[-5:], 1):
            stats_text += f"\n{i}. {response.get('username', 'Анонім')} - {response.get('created_at', 'Невідомо')}"
        
        await update.message.reply_text(stats_text)
    
    async def health_check(self, request):
        """Health check endpoint для Railway"""
        print(f"🏥 Health check запрос от {request.remote}")
        print(f"🏥 User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
        print(f"🏥 Method: {request.method}")
        print(f"🏥 Path: {request.path}")
        
        return web.Response(
            text="Bot is running! 🤖", 
            status=200,
            content_type='text/plain'
        )
    
    async def webhook_handler(self, request):
        """Обработчик webhook от Telegram"""
        if request.method == "POST":
            update = Update.de_json(await request.json(), self.application.bot)
            await self.application.process_update(update)
        return web.Response()
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("stats", self.stats))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
    
    async def start_webhook(self):
        """Запускает бота с webhook"""
        try:
            print(f"🔧 Настройка webhook на порту {self.port}")
            print(f"🔧 Переменные окружения: PORT={os.getenv('PORT')}")
            print(f"🔧 TELEGRAM_TOKEN: {'✅ Установлен' if TELEGRAM_TOKEN else '❌ Отсутствует'}")
            print(f"🔧 SUPABASE_URL: {'✅ Установлен' if SUPABASE_URL else '❌ Отсутствует'}")
            print(f"🔧 SUPABASE_KEY: {'✅ Установлен' if SUPABASE_KEY else '❌ Отсутствует'}")
            
            # Проверяем обязательные переменные
            if not TELEGRAM_TOKEN:
                raise Exception("TELEGRAM_TOKEN не установлен")
            
            # Создаем приложение
            self.application = Application.builder().token(TELEGRAM_TOKEN).build()
            print("✅ Telegram приложение создано")
            
            # Настраиваем обработчики
            self.setup_handlers()
            print("✅ Обработчики настроены")
            
            # Настраиваем webhook
            if self.webhook_url:
                await self.application.bot.set_webhook(url=f"{self.webhook_url}/webhook")
                print(f"✅ Webhook установлен: {self.webhook_url}/webhook")
            else:
                print("⚠️ WEBHOOK_URL не установлен")
            
            # Создаем веб-сервер
            app = web.Application()
            app.router.add_get('/', self.health_check)
            app.router.add_get('/health', self.health_check)
            app.router.add_post('/webhook', self.webhook_handler)
            print("✅ Веб-сервер настроен")
            print("📡 Доступные пути: /, /health, /webhook")
            
            # Запускаем сервер
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', self.port)
            await site.start()
            
            print(f"🚀 Веб-сервер запущен на порту {self.port}")
            print("🤖 Бот готов к работе!")
            print("📡 Ожидание webhook запросов...")
            
            # Держим сервер запущенным
            try:
                await asyncio.Future()  # Бесконечное ожидание
            except KeyboardInterrupt:
                print("🛑 Получен сигнал остановки")
                await runner.cleanup()
                
        except Exception as e:
            print(f"❌ Ошибка запуска бота: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def run_polling(self):
        """Запускает бота в режиме polling (для локальной разработки)"""
        # Создаем приложение
        self.application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Настраиваем обработчики
        self.setup_handlers()
        
        # Запускаем бота
        print("🤖 Бот запущен в режиме polling...")
        self.application.run_polling()
    
    def run(self):
        """Запускает бота в зависимости от окружения"""
        # Проверяем различные признаки Railway окружения
        is_railway = (
            os.getenv('RAILWAY_ENVIRONMENT') or 
            os.getenv('RAILWAY_PROJECT_ID') or 
            os.getenv('PORT') or
            os.getenv('RAILWAY_SERVICE_NAME')
        )
        
        if is_railway:
            # Запуск на Railway с webhook
            print("🚂 Запуск в режиме Railway (webhook)")
            try:
                asyncio.run(self.start_webhook())
            except Exception as e:
                print(f"❌ Ошибка запуска webhook режима: {e}")
                print("🔄 Переключение на fallback режим...")
                self.run_fallback_server()
        else:
            # Локальный запуск с polling
            print("🏠 Запуск в локальном режиме (polling)")
            self.run_polling()
    
    def run_fallback_server(self):
        """Запускает простой веб-сервер для health check без Telegram бота"""
        print("🛟 Запуск fallback сервера...")
        
        async def simple_health_check(request):
            print(f"🏥 Health check запрос от {request.remote}")
            return web.Response(
                text="Bot server is starting... 🤖", 
                status=200,
                content_type='text/plain'
            )
        
        async def main():
            port = int(os.getenv('PORT', 8080))
            print(f"🔧 Запуск fallback сервера на порту {port}")
            
            app = web.Application()
            app.router.add_get('/', simple_health_check)
            app.router.add_get('/health', simple_health_check)
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', port)
            await site.start()
            
            print(f"🚀 Fallback сервер запущен на порту {port}")
            print("📡 Ожидание запросов...")
            
            try:
                await asyncio.Future()
            except KeyboardInterrupt:
                await runner.cleanup()
        
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"❌ Ошибка fallback сервера: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    bot = SurveyBot()
    bot.run()
