GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = "8974862777:AAGlmHU7AL65zRJDHTBIYrL9psUyorzWiPg"     
TELEGRAM_CHAT_ID = "-1003961458761" 

SEARCH_QUERY = "CDC Infant Toddler Nutrition, AAP HealthyChildren solid foods, NHS Start for Life Weaning, ESPGHAN complementary feeding position paper guidelines"

ai_client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

HISTORY_FILE = "published_history_baby_feeding_v5.txt"
LATEST_DIGEST_TEXT = "🚀 Сервер успешно запущен! ИИ-Агент начинает генерацию статьи..."

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

def save_to_history(title):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(str(title) + "\n")

async def generate_with_retry_protection(prompt):
    models_to_try = ['gemini-3.5-flash', 'gemini-3.1-flash-lite', 'gemini-2.5-pro']
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
    Используя свою фундаментальную академическую базу данных, найди ОДНО самое актуальное официальное руководство, пошаговый гайд или научную публикацию по теме ПРИКОРМА И ПИТАНИЯ ДЕТЕЙ ДО 1 ГОДА строго из следующих источников:
    - CDC (Центры по контролю заболеваний США, раздел Infant and Toddler Nutrition)
    - AAP (Американская академия педиатрии / портал HealthyChildren.org)
    - NHS (Национальная служба здравоохранения Великобритании, проект Start for Life / Weaning)
    - ESPGHAN (Официальные Position Papers и гайдлайны по прикорму)
    
    Тема поиска: {SEARCH_QUERY}
    
    ВАЖНОЕ УСЛОВИЕ: Полностью проигнорируй и НЕ выбирай материалы из этого списка:
    [{ignored_titles}]
    
    Напиши полезный, увлекательный и простой пост по мотивам этого гайда, адаптированный ДЛЯ РОДИТЕЛЕЙ (мам и пап) на РУССКОМ языке. Пиши простыми словами, как заботливый и современный детский нутрициолог. Избегай тяжелых медицинских терминов. 
    НЕ используй никаких HTML-тегов, знаков *, _, ` или < >. Только чистый текст.
    
    Форматируй текст строго по шаблону (скопируй заголовки один в один):
    📌 РУБРИКА: НАУЧНЫЙ ПРИКОРМ ДЛЯ РОДИТЕЛЕЙ
    
    [ПРИВЛЕКАТЕЛЬНЫЙ ЗАГОЛОВОК КРУПНЫМИ БУКВАМИ, НАПРИМЕР: ПРИЗНАКИ ГОТОВНОСТИ К ПРИКОРМУ ПО НАУКЕ]
    
    🍏 О чем говорит источник:
    (Простыми словами в 2-3 предложениях объясни суть гайда от CDC/AAP/NHS/ESPGHAN и почему эксперты обратили на это внимание).
    
    💡 Главный совет для мам и пап:
    (Понятный практический результат: четкие сроки введения продуктов, размеры порций, правила безопасной подачи кусочков или введения опасных аллергенов, переведенные на простой язык).
    
    📝 Как применить на кухне прямо сегодня:
    (Пошаговый, понятный совет маме для повседневной жизни, основанный на этом руководстве).
    
    📑 Информация для вашего педиатра (название первоисточника):
    [Официальный источник: Название организации (CDC, AAP, NHS или ESPGHAN)]
    Оригинальное название материала: (Точное название статьи или гайда на английском языке)
    Прямая ссылка на материал: (Интернет-ссылка на этот материал на официальном сайте организации)
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
            return True  # Возвращаем True, если публикация прошла успешно
        else:
            LATEST_DIGEST_TEXT = "⚠️ ИИ вернул слишком короткий текст."
            return False
    except Exception as e:
        LATEST_DIGEST_TEXT = f"❌ ОШИБКА СЕТИ ИЛИ ПЕРЕГРУЗКА: {e}"
        print(LATEST_DIGEST_TEXT)
        return False  # Возвращаем False при любой ошибке, чтобы запустить повтор

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
            <h2 style="color: #2c3e50; border-bottom: 2px solid #2ecc71; padding-bottom: 10px;">🩺 ИИ-Агент: Прикорм детей до 1 года</h2>
            <pre style="white-space: pre-wrap; font-size: 15px; color: #e67e22; background: #fafafa; padding: 15px; border-radius: 4px; border: 1px solid #eee;">{LATEST_DIGEST_TEXT}</pre>
            <p style="font-size: 11px; color: #95a5a6; margin-top: 20px; border-top: 1px solid #ecf0f1; padding-top: 10px;">Страница обновляется автоматически каждые 15 секунд.</p>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def background_loop():
    await asyncio.sleep(5)
    while True:
        # Пытаемся опубликовать статью
        success = await run_agent()
        
        if success:
            # Если всё прошло успешно, спокойно спим 24 часа до следующего дня
            print("⏳ Задача выполнена успешно. Следующий запуск через 24 часа...")
            await asyncio.sleep(24 * 60 * 60)
        else:
            # А ВОТ И НАША ЗАЩИТА: Если была перегрузка, пишем отчет, ждем 10 минут и пробуем снова!
            global LATEST_DIGEST_TEXT
            LATEST_DIGEST_TEXT += "\n\n⚠️ Сервера Google сейчас заняты. Включена автозащита: я подожду 10 минут и повторю попытку..."
            print("⚠️ Сбой из-за перегрузки. Жду 10 минут до автоматического повтора...")
            await asyncio.sleep(10 * 60) # Спим 10 минут (10 минут * 60 секунд)

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
 
