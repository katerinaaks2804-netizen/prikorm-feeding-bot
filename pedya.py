import os
import time
from google import genai
from telegram import Bot
import asyncio
from aiohttp import web
import urllib.parse

# =====================================================================
# НАСТРОЙКИ И КЛЮЧИ (Считываются из скрытого раздела Environment)
# =====================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = "8974862777:AAGlmHU7AL65zRJDHTBIYrL9psUyorzWiPg"     
TELEGRAM_CHAT_ID = "-1003961458761" 

SEARCH_QUERY = "CDC Infant Toddler Nutrition, AAP HealthyChildren solid foods, NHS Start for Life Weaning, ESPGHAN complementary feeding position paper guidelines"

ai_client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

HISTORY_FILE = "published_history_baby_feeding_v5.txt"
LATEST_DIGEST_TEXT = "🚀 Сервер прикорма успешно запущен! ИИ-Агент начинает работу..."

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
    LATEST_DIGEST_TEXT = "🔍 ИИ-Агент ищет гайдлайны и подбирает картинку..."
    print(LATEST_DIGEST_TEXT)
    
    already_published = load_history()
    ignored_titles = ", ".join(already_published) if already_published else "Пока нет"
    
    prompt = f"""
    Используя свою фундаментальную академическую базу данных, найди ОДНО самое актуальное официальное руководство, пошаговый гайд или научную публикацию по теме ПРИКОРМА И ПИТАНИЯ ДЕТЕЙ ДО 1 ГОДА строго из следующих источников:
    - CDC (раздел Infant and Toddler Nutrition)
    - AAP (портал HealthyChildren.org)
    - NHS (проект Start for Life / Weaning)
    - ESPGHAN (Официальные Position Papers)
    
    Тема поиска: {SEARCH_QUERY}
    
    ВАЖНОЕ УСЛОВИЕ: Полностью проигнорируй и НЕ выбирай материалы из этого списка: [{ignored_titles}]
    
    Напиши полезный, увлекательный и простой пост по мотивам этого гайда, адаптированный ДЛЯ РОДИТЕЛЕЙ (мам и пап) на РУССКОМ языке. Пиши простыми словами, как заботливый и современный детский нутрициолог. 
    НЕ используй никаких HTML-тегов, знаков *, _, ` или < >. Только чистый текст.
    
    Форматируй текст строго по шаблону (скопируй заголовки один в один):
    📌 РУБРИКА: НАУЧНЫЙ ПРИКОРМ ДЛЯ РОДИТЕЛЕЙ
    
    [ЗАГОЛОВОК КРУПНЫМИ БУКВАМИ]
    
    🍏 О чем говорит источник:
    (Суть гайда в 2-3 предложениях).
    
    💡 Главный совет для мам и пап:
    (Практический результат для родителей).
    
    📝 Как применить на кухне прямо сегодня:
    (Пошаговый, понятный совет маме).
    
    📑 Информация для вашего педиатра (название первоисточника):
    [Официальный источник: Название организации]
    Оригинальное название материала: (На английском)
    Прямая ссылка на материал: (Ссылка в PubMed или на сайт организации)
    
    В САМОМ КОНЦЕ ТЕКСТА С НОВОЙ СТРОКИ ОБЯЗАТЕЛЬНО ДОБАВЬ ПАРАМЕТР ФОТО С 2-3 СЛОВАМИ НА АНГЛИЙСКОМ СЛЕДУЮЩИМ ОБРАЗОМ (НАПРИМЕР):
    [PHOTO_KEYWORDS: baby eating broccoli]
    """

    try:
        full_text = await generate_with_retry_protection(prompt)
        clean_post = full_text.strip()
        
        if len(clean_post) > 50:
            # Вырезаем ключевые слова для поиска картинки
            keywords = "baby eating"
            if "[PHOTO_KEYWORDS:" in clean_post:
                parts = clean_post.split("[PHOTO_KEYWORDS:")
                clean_post = parts[0].strip()
                keywords = parts[1].replace("]", "").strip()
            
            encoded_keywords = urllib.parse.quote(keywords)
            # Ссылка на бесплатную базу Unsplash по ключевым словам
            dynamic_photo_url = f"https://unsplash.com"
            
            LATEST_DIGEST_TEXT = clean_post
            print(f"📨 Отправляем картинку и подробный текст в Telegram...")
            
            try:
                # 1. Сначала отправляем только картинку
                await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=dynamic_photo_url)
                # Даем мессенджеру полсекунды паузы, чтобы картинка встала первой
                await asyncio.sleep(0.5)
            except Exception as photo_err:
                print(f"⚠️ Картинка не отправилась, отправляем только текст: {photo_err}")
            
            # 2. Следом отправляем наш полный подробный текст обзора без ограничений по длине!
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=clean_post)
            print("✅ ПОСТ С КАРТИНКОЙ УСПЕШНО ДОСТАВЛЕН В ТЕЛЕГРАМ-КАНАЛ!")
            
            first_line = clean_post.split("\n")
            save_to_history(first_line[0])
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
    <html><head><meta charset="utf-8"><meta http-equiv="refresh" content="15"><title>Мониторинг</title></head>
    <body style="font-family: Arial; margin: 40px; background: #f4f6f9;">
        <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #e67e22; padding-bottom: 10px;">🍏 ИИ-Агент: Прикорм (Устойчивый режим с фото)</h2>
            <pre style="white-space: pre-wrap; font-size: 15px; color: #34495e;">{LATEST_DIGEST_TEXT}</pre>
        </div>
    </body></html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def background_loop():
    await asyncio.sleep(5)
    while True:
        success = await run_agent()
        if success:
            await asyncio.sleep(24 * 60 * 60)
        else:
            global LATEST_DIGEST_TEXT
            LATEST_DIGEST_TEXT += "\n\n⚠️ Ошибка отправки. Жду 10 минут..."
            await asyncio.sleep(10 * 60)

async def main():
    app = web.Application()
    app.router.add_get('/', handle_request)
    asyncio.create_task(background_loop())
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
