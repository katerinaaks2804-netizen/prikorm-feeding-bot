import os
import time
from google import genai
from telegram import Bot
import asyncio
import http.server
import threading

# =====================================================================
# НАСТРОЙКИ И КЛЮЧИ (Считываются из скрытого раздела Environment)
# =====================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = "8994835822:AAEstwCe5uYo3QH7c_9vmB8SRRLRJ09bZFc"      
TELEGRAM_CHAT_ID = "-1003977919330"       

SEARCH_QUERY = "general pediatrics clinical trials guidelines" 

ai_client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

HISTORY_FILE = "published_history_general_pediatrics.txt"

# Глобальная переменная, чтобы хранить последний текст для вывода в браузер
LATEST_DIGEST_TEXT = "Робот запущен. Идет генерация первой статьи, подождите..."

# ---------------------------------------------------------------------
# СЕРВЕР-ВЕРИФИКАТОР ПОРТОВ (Теперь выводит статью прямо в браузер!)
# ---------------------------------------------------------------------
class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        # Выводим на экран текст статьи, чтобы вы могли читать её с iPad
        self.wfile.write(LATEST_DIGEST_TEXT.encode('utf-8'))

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, CustomHandler)
    print(f"🌐 Системный веб-порт {port} успешно открыт.")
    httpd.serve_forever()

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
            print(f"⏳ Запрашиваю данные у модели {model_name}...")
            response = ai_client.models.generate_content(model=model_name, contents=prompt)
            print(f"✅ Модель {model_name} успешно ответила!")
            return response.text
        except Exception as e:
            print(f"⚠️ Модель {model_name} временно недоступна. Ошибка: {e}")
            continue
    raise Exception("🚨 Все модели Google перегружены.")

async def run_agent():
    global LATEST_DIGEST_TEXT
    print(f"🚀 ИИ-Агент по педиатрии запускает цикл поиска новой статьи...")
    
    already_published = load_history()
    print(f"📋 Найдено ранее опубликованных статей в истории: {len(already_published)}")
    ignored_titles = ", ".join(already_published) if already_published else "Пока нет"
    
    prompt = f"""
    Используя свою фундаментальную академическую базу данных медицинских публикаций (PubMed, Cochrane, Embase), найди ОДНО самое важное и значимое клиническое исследование или руководство (guidelines) в области общей ПЕДИАТРИИ (тема: {SEARCH_QUERY}) за последние 5 лет (с 2021 по 2026 год).
    
    ВАЖНОЕ УСЛОВИЕ: Полностью проигнорируй и НЕ выбирай статьи из этого списка:
    [{ignored_titles}]
    
    Напиши подробный структурированный клинический обзор этой статьи на РУССКОМ языке.
    НЕ используй никаких HTML-тегов, знаков *, _, ` или < >. Только чистый текст.
    
    Форматируй текст строго по шаблону:
    [Источник: Название источника]
    [ДАТА ПУБЛИКАЦИИ: Месяц и год]
    [НАЗВАНИЕ СТАТЬИ НА РУССКОМ ЯЗЫКЕ]
    
    - Суть исследования: (Подробно в 2-3 предложениях).
    - Ключевой результат: (Главный научный вывод исследования, важные цифры).
    - Клиническое значение: (Как это знание применять на практике врачу-педиатру).
    
    Оригинальное название на английском: (Точное название)
    Прямая ссылка на статью: (Интернет-ссылка на эту статью в PubMed)
    """

    try:
        full_text = await generate_with_retry_protection(prompt)
        clean_post = full_text.strip()
        
        if len(clean_post) > 50:
            LATEST_DIGEST_TEXT = clean_post  # Сохраняем для вывода на экран
            
            print(f"📨 Отправляю обзор в Telegram (ID: {TELEGRAM_CHAT_ID})...")
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=clean_post)
            print("✅ ПОСТ УСПЕШНО ДОСТАВЛЕН В ТЕЛЕГРАМ-КАНАЛ!")
            
            first_line = clean_post.split("\n")[0]
            save_to_history(first_line)
            print(f"💾 Успешно сохранено в историю.")
        else:
            print("⚠️ ИИ сгенерировал пустой текст.")
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА ОБРАБОТКИ ИЛИ ОТПРАВКИ: {e}")

async def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    while True:
        await run_agent()
        print("⏳ Задача выполнена. Следующий автоматический запуск ровно через 24 часа...")
        await asyncio.sleep(24 * 60 * 60)

if __name__ == "__main__":
    asyncio.run(main())
