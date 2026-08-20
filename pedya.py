import os
import time
from google import genai
from telegram import Bot
import asyncio
from aiohttp import web

# =====================================================================
# НАСТРОЙКИ И КЛЮЧИ (Считываются из скрытого раздела Environment)
# =====================================================================
GEMINI_API_KEY = "AQ.Ab8RN6KZlJ5H_dZmY0TxkA3f0yPKWTTEJAIjVT3OaU71Zmjv-w" 
TELEGRAM_BOT_TOKEN = "8994835822:AAEstwCe5uYo3QH7c_9vmB8SRRLRJ09bZFc"
TELEGRAM_CHAT_ID = "-1003977919330"

SEARCH_QUERY = "general pediatrics clinical trials guidelines" 

ai_client = genai.Client()
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Файл памяти строго для педиатрии
HISTORY_FILE = "published_history_general_pediatrics_v4.txt"
LATEST_DIGEST_TEXT = "🚀 Сервер успешно запущен! ИИ-Агент педиатрии начинает генерацию статьи..."

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
            global LATEST_DIGEST_TEXT
            LATEST_DIGEST_TEXT = f"⏳ Запрашиваю данные у ИИ-модели {model_name}..."
            print(LATEST_DIGEST_TEXT)
            
            task = ai_client.models.generate_content(model=model_name, contents=prompt)
            response = await asyncio.wait_for(asyncio.to_thread(lambda: task), timeout=40.0)
            return response.text
        except Exception as e:
            print(f"⚠️ Модель {model_name} временно недоступна. Ошибка: {e}")
            continue
    raise Exception("🚨 Все доступные модели Google сейчас перегружены.")

async def run_agent():
    global LATEST_DIGEST_TEXT
    LATEST_DIGEST_TEXT = "🔍 ИИ-Агент по педиатрии ищет новую уникальную статью..."
    print(LATEST_DIGEST_TEXT)
    
    already_published = load_history()
    ignored_titles = ", ".join(already_published) if already_published else "Пока нет"
    
    prompt = f"""
    Используя свою фундаментальную академическую базу данных медицинских публикаций (PubMed, Cochrane, Embase), найди ОДНО самое важное и значимое руководство (guidelines) или исследование в области общей ПЕДИАТРИИ за последние 5 лет (с 2021 по 2026 год).
    Тема: {SEARCH_QUERY}
    
    ВАЖНОЕ УСЛОВИЕ: Полностью проигнорируй и НЕ выбирай статьи из этого списка:
    [{ignored_titles}]
    
    Напиши подробный структурированный клинический обзор этой статьи на РУССКОМ языке.
    НЕ используй никаких HTML-тегов, знаков *, _, ` или < >. Только чистый текст.
    
    Форматируй текст строго по шаблону:
    [Источник: Название источника]
    [ДАТА ПУБЛИКАЦИИ: Месяц и год]
    [НАЗВАНИЕ СТАТЬИ НА РУССКОМ ЯЗЫКЕ]
    
    - Суть исследования: (В 2-3 предложениях).
    - Ключевой результат: (Главный вывод исследования, важные цифры).
    - Клиническое значение: (Как это знание применять на практике врачу-педиатру).
    
    Оригинальное название на английском: (Точное название)
    Прямая ссылка на статью: (Интернет-ссылка на эту статью в PubMed)
    """

    try:
        full_text = await generate_with_retry_protection(prompt)
        clean_post = full_text.strip()
        
        if len(clean_post) > 50:
            LATEST_DIGEST_TEXT = clean_post
            print("📨 Отправляю обзор в Telegram...")
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=clean_post)
            print("✅ ПОСТ УСПЕШНО ДОСТАВЛЕН В ТЕЛЕГРАМ-КАНАЛ!")
            
            first_line = clean_post.split("\n")
            save_to_history(first_line)
            return True
        else:
            LATEST_DIGEST_TEXT = "⚠️ ИИ вернул слишком короткий текст."
            return False
    except Exception as e:
        LATEST_DIGEST_TEXT = f"❌ ОШИБКА СЕТИ ИЛИ ПЕРЕГРУЗКА: {e}"
        print(LATEST_DIGEST_TEXT)
        return False

async def handle_request(request):
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="15">
        <title>Мониторинг Педиатрии</title>
    </head>
    <body style="font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; background: #f4f6f9;">
        <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #2ecc71; padding-bottom: 10px;">🩺 ИИ-Агент: Общая педиатрия</h2>
            <pre style="white-space: pre-wrap; font-size: 15px; color: #34495e; background: #fafafa; padding: 15px; border-radius: 4px; border: 1px solid #eee;">{LATEST_DIGEST_TEXT}</pre>
            <p style="font-size: 11px; color: #95a5a6; margin-top: 20px; border-top: 1px solid #ecf0f1; padding-top: 10px;">Страница обновляется автоматически каждые 15 секунд.</p>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def background_loop():
    await asyncio.sleep(5)
    while True:
        success = await run_agent()
        if success:
            print("⏳ Задача выполнена успешно. Следующий запуск через 24 часа...")
            await asyncio.sleep(24 * 60 * 60)
        else:
            global LATEST_DIGEST_TEXT
            LATEST_DIGEST_TEXT += "\n\n⚠️ Сервера Google сейчас заняты. Включена автозащита: я подожду 10 минут и повторю попытку..."
            print("⚠️ Сбой из-за перегрузки. Жду 10 минут до автоматического повтора...")
            await asyncio.sleep(10 * 60)

async def main():
    app = web.Application()
    app.router.add_get('/', handle_request)
    asyncio.create_task(background_loop())
    
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
