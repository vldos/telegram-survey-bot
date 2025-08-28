from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    def save_survey_response(self, user_id: int, username: str, answers: dict):
        """
        Сохраняет ответы пользователя в базу данных
        """
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
            
            return True, "Ответы успешно сохранены"
        except Exception as e:
            return False, f"Ошибка при сохранении: {str(e)}"
    
    def get_user_responses(self, user_id: int):
        """
        Получает все ответы пользователя
        """
        try:
            result = self.supabase.table("survey_responses").select("*").eq("user_id", user_id).execute()
            return result.data
        except Exception as e:
            print(f"Ошибка при получении ответов: {str(e)}")
            return []
    
    def get_all_responses(self):
        """
        Получает все ответы из базы данных
        """
        try:
            result = self.supabase.table("survey_responses").select("*").execute()
            return result.data
        except Exception as e:
            print(f"Ошибка при получении всех ответов: {str(e)}")
            return []
    
    def create_tables(self):
        """
        Создает необходимые таблицы в Supabase (если их нет)
        """
        # SQL для создания таблицы (выполняется в Supabase Dashboard)
        sql = """
        CREATE TABLE IF NOT EXISTS survey_responses (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            username TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            answers JSONB NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_survey_responses_user_id ON survey_responses(user_id);
        CREATE INDEX IF NOT EXISTS idx_survey_responses_created_at ON survey_responses(created_at);
        """
        print("SQL для создания таблиц:")
        print(sql)
        print("\nВыполните этот SQL в Supabase Dashboard -> SQL Editor")
