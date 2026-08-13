import os
import time
from google import genai
from telegram import Bot
import asyncio

# =====================================================================
# НАСТРОЙКИ И КЛЮЧИ (Считываются из скрытого раздела Environment)
# =====================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = "8355385666:AAEZBbBlgeh1Mxy6uo2_lbKiM5-7w0Ka4HI"
TELEGRAM_CHAT_ID = "-1004447211467"

SEARCH_QUERY = "general pediatrics clinical trials guidelines" 

# Инициализируем клиента Google и бота Telegram
ai_client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# НАСТРОЙКА 1: Отдельное уникальное имя файла памяти для педиатрии
HISTORY_FILE = "published_history_general_pediatrics.txt"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

def save_to_history(title):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(str(title) + "\n")

async def generate_with_retry_protection(prompt):
    models_to_try = ['gemini-3.5-flash', 'gemini-3.1-flash-lite', 'gemini-2.5-flash']
    for model_name in models_to_try:
        try:
            response = ai_client.models.generate_content(model=model_name, contents=prompt)
            return response.text
        except Exception as e:
            print(f"⚠️ Модель {model_name} временно недоступна. Пробую резервную...")
            continue
    raise Exception("🚨 Все модели Google перегружены.")

async def run_agent():
    print(f"🚀 ИИ-Агент по педиатрии запущен в облаке. Начинаю цикл поиска...")
    
    already_published = load_history()
    ignored_titles = ", ".join(already_published) if already_published else "Пока нет"
    
    prompt = f"""
    Используя свою фундаментальную академическую базу данных медицинских публикаций (PubMed, Cochrane, Embase), найди ОДНО самое важное и значимое клиническое исследование или руководство (guidelines) в области общей ПЕДИАТРИИ (тема: {SEARCH_QUERY}) за последние 5 лет (с 2021 по 2026 год).
    
    ВАЖНОЕ УСЛОВИЕ: Полностью проигнорируй и НЕ выбирай статьи из этого списка (они уже были опубликованы):
    [{ignored_titles}]
    
    Напиши подробный структурированный клинический обзор этой статьи на РУССКОМ языке.
    НЕ используй никаких HTML-тегов, знаков *, _, ` или < >. Только чистый текст.
    
    Форматируй текст строго по шаблону:
    [Источник: Название источника]
    [ДАТА ПУБЛИКАЦИИ: Месяц и год]
    [НАЗВАНИЕ СТАТЬИ НА РУССКОМ ЯЗЫКЕ]
    
    - Суть исследования: (Подробно в 2-3 предложениях: какая выборка детей, цели, методы).
    - Ключевой результат: (Главный научный вывод исследования, статистические данные, проценты, важные цифры).
    - Клиническое значение: (Как это знание применять на практике врачу-педиатру).
    
    Оригинальное название на английском: (Точное название)
    Прямая ссылка на статью: (Интернет-ссылка на эту статью в PubMed, например https://nih.gov)
    """

    try:
        full_text = await generate_with_retry_protection(prompt)
        clean_post = full_text.strip()
        
        if len(clean_post) > 50:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=clean_post)
            print("✅ Новая статья по педиатрии успешно опубликована в Telegram!")
            
            first_line = clean_post.split("\n")
            save_to_history(first_line) 
    except Exception as e:
        print(f"🚨 Ошибка в цикле педиатрии: {e}")

async def main():
    while True:
        await run_agent()
        # НАСТРОЙКА 2: Спим ровно 24 часа для ежедневных публикаций
        print("⏳ Задача выполнена успешно. Следующий запуск ровно через 24 часа...")
        await asyncio.sleep(24 * 60 * 60)

if __name__ == "__main__":
    asyncio.run(main())
