#!/usr/bin/env python3
"""
Скрипт для анализа данных опроса
"""

from database import DatabaseManager
import json
from collections import Counter
import pandas as pd
from datetime import datetime

def analyze_survey_data():
    """Анализирует данные опроса"""
    try:
        db = DatabaseManager()
        responses = db.get_all_responses()
        
        if not responses:
            print("📊 Дані для аналізу відсутні")
            return
        
        print(f"📊 Аналіз {len(responses)} відповідей")
        print("=" * 50)
        
        # Общая статистика
        print(f"\n📈 Загальна статистика:")
        print(f"Кількість відповідей: {len(responses)}")
        
        # Анализ по дням
        dates = [datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')).date() for r in responses]
        date_counts = Counter(dates)
        print(f"\n📅 Відповіді за днями:")
        for date, count in sorted(date_counts.items()):
            print(f"  {date}: {count} відповідей")
        
        # Анализ ответов на вопросы
        print(f"\n❓ Аналіз відповідей на питання:")
        
        for question_num in range(1, 11):
            question_key = f"q{question_num}"
            answers = []
            
            for response in responses:
                answers_data = json.loads(response['answers'])
                if question_key in answers_data:
                    answer = answers_data[question_key]
                    if isinstance(answer, list):
                        answers.extend(answer)
                    else:
                        answers.append(answer)
            
            if answers:
                answer_counts = Counter(answers)
                print(f"\nПитання {question_num}:")
                for answer, count in answer_counts.most_common():
                    percentage = (count / len(answers)) * 100
                    print(f"  {answer}: {count} ({percentage:.1f}%)")
        
        # Анализ дополнительных вопросов
        print(f"\n📝 Аналіз додаткових питань:")
        
        additional_fields = ['age', 'city', 'obstacles', 'suggestions']
        for field in additional_fields:
            values = []
            for response in responses:
                answers_data = json.loads(response['answers'])
                if field in answers_data and answers_data[field]:
                    values.append(answers_data[field])
            
            if values:
                print(f"\n{field.upper()}:")
                if field in ['age', 'city']:
                    # Для возраста и города показываем топ значений
                    value_counts = Counter(values)
                    for value, count in value_counts.most_common(5):
                        percentage = (count / len(values)) * 100
                        print(f"  {value}: {count} ({percentage:.1f}%)")
                else:
                    # Для текстовых полей показываем количество заполненных
                    print(f"  Заповнено: {len(values)} з {len(responses)} ({len(values)/len(responses)*100:.1f}%)")
        
        # Экспорт в CSV
        export_to_csv(responses)
        
    except Exception as e:
        print(f"❌ Помилка при аналізі: {str(e)}")

def export_to_csv(responses):
    """Экспортирует данные в CSV файл"""
    try:
        data = []
        
        for response in responses:
            row = {
                'id': response['id'],
                'user_id': response['user_id'],
                'username': response['username'],
                'created_at': response['created_at']
            }
            
            # Добавляем ответы на вопросы
            answers_data = json.loads(response['answers'])
            for key, value in answers_data.items():
                if isinstance(value, list):
                    row[key] = ', '.join(value)
                else:
                    row[key] = value
            
            data.append(row)
        
        df = pd.DataFrame(data)
        filename = f"survey_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 Дані експортовано в файл: {filename}")
        
    except Exception as e:
        print(f"❌ Помилка при експорті: {str(e)}")

def show_sample_responses():
    """Показывает примеры ответов"""
    try:
        db = DatabaseManager()
        responses = db.get_all_responses()
        
        if not responses:
            print("📊 Дані відсутні")
            return
        
        print(f"\n📋 Приклади відповідей:")
        print("=" * 50)
        
        for i, response in enumerate(responses[:3], 1):
            print(f"\nВідповідь #{i}:")
            print(f"Користувач: {response['username']}")
            print(f"Дата: {response['created_at']}")
            
            answers_data = json.loads(response['answers'])
            for key, value in answers_data.items():
                print(f"  {key}: {value}")
            
            if i < 3:
                print("-" * 30)
    
    except Exception as e:
        print(f"❌ Помилка: {str(e)}")

def main():
    print("📊 Аналіз даних опитування")
    print("=" * 50)
    
    while True:
        print("\nОберіть опцію:")
        print("1. Повний аналіз даних")
        print("2. Показати приклади відповідей")
        print("3. Вихід")
        
        choice = input("\nВаш вибір (1-3): ").strip()
        
        if choice == "1":
            analyze_survey_data()
        elif choice == "2":
            show_sample_responses()
        elif choice == "3":
            print("👋 До побачення!")
            break
        else:
            print("❌ Невірний вибір. Спробуйте ще раз.")

if __name__ == "__main__":
    main()
