import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import TELEGRAM_TOKEN, QUESTIONS, ADDITIONAL_QUESTIONS
from database import DatabaseManager
import json

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
        self.waiting_for_other = {} # Состояние ожидания ввода для "Інше"
    
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
        """Обрабатывает текстовые сообщения для дополнительных вопросов"""
        user_id = update.effective_user.id
        text = update.message.text
        
        if user_id not in self.user_states:
            await update.message.reply_text("Використайте /start для початку опитування.")
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

Якщо у вас є додаткові ідеї або пропозиції, ви завжди можете написати нам!
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
    
    def run(self):
        """Запускает бота"""
        # Создаем приложение
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("stats", self.stats))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        
        # Запускаем бота
        print("🤖 Бот запущен...")
        application.run_polling()

if __name__ == "__main__":
    bot = SurveyBot()
    bot.run()
