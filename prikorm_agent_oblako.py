import os
import time
from google import genai
from telegram import Bot
import asyncio

# =====================================================================
# НАСТРОЙКИ И КЛЮЧИ (Вставьте ваши данные)
# =====================================================================
GEMINI_API_KEY = "ВАШ_КЛЮЧ_AIzaSy..."          
TELEGRAM_BOT_TOKEN = "ВАШ_ТОКЕН_БОТА"         
TELEGRAM_CHAT_ID = "ID_НОВОГО_КАНАЛА_ПРИКОРМ"  

SEARCH_QUERY = "infant complementary feeding introduction baby led weaning nutritional guidelines solid foods under 1 year" 
AI_MODEL = "gemini-3.5-flash"

ai_client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# В облаке мы сохраняем историю в текущую папку скрипта
HISTORY_FILE = "published_history_baby_feeding.txt"

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
    print(f"🚀 ИИ-Агент запущен в облаке. Начинаю цикл поиска...")
    
    already_published = load_history()
    ignored_titles = ", ".join(already_published) if already_published else "Пока нет"
    
    prompt = f"""
    Используя свою фундаментальную академическую базу данных медицинских и нутрициологических публикаций (PubMed, Cochrane, Embase, гайдлайны WHO, ESPGHAN, AAP), найди ОДНО самое важное клиническое исследование, метаанализ или официальное руководство по теме ПРИКОРМА И ПИТАНИЯ ДЕТЕЙ ДО 1 ГОДА (тема: {SEARCH_QUERY}) за последние 5 лет (с 2021 по 2026 год).
    
    ВАЖНОЕ УСЛОВИЕ: Полностью проигнорируй и НЕ выбирай статьи из этого списка:
    [{ignored_titles}]
    
    Напиши подробный структурированный клинический обзор этой статьи на РУССКОМ языке.
    НЕ используй никаких HTML-тегов, знаков *, _, ` или < >. Только чистый текст.
    
    Форматируй текст строго по шаблону:
    [Источник: Название источника]
    [ДАТА ПУБЛИКАЦИИ: Месяц и год]
    [НАЗВАНИЕ СТАТЬИ НА РУССКОМ ЯЗЫКЕ]
    
    - Суть исследования: (Подробно в 2-3 предложениях).
    - Ключевой результат: (Главный научный вывод, цифры, проценты).
    - Клиническое значение: (Как применить на практике).
    
    Оригинальное название на английском: (Точное название)
    Прямая ссылка на статью: (Интернет-ссылка на эту статью в PubMed)
    """

    try:
        full_text = await generate_with_retry_protection(prompt)
        clean_post = full_text.strip()
        
        if len(clean_post) > 50:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=clean_post)
            print("✅ Статья успешно опубликована в Telegram!")
            
            first_line = clean_post.split("\n")[0]
            save_to_history(first_line) 
    except Exception as e:
        print(f"🚨 Ошибка в цикле: {e}")

async def main():
    while True:
        await run_agent()
        print("⏳ Задача выполнена успешно. Следующий запуск ровно через 48 часов...")
        # Спим 48 часов (48 часов * 60 минут * 60 секунд)
        await asyncio.sleep(48 * 60 * 60)

if __name__ == "__main__":
    asyncio.run(main())
