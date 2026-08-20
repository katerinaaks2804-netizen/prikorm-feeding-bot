GEMINI_API_KEY = "AQ.Ab8RN6KZlJ5H_dZmY0TxkA3f0yPKWTTEJAIjVT3OaU71Zmjv-w" 
TELEGRAM_BOT_TOKEN = "8994835822:AAEstwCe5uYo3QH7c_9vmB8SRRLRJ09bZFc"
TELEGRAM_CHAT_ID = "-1003977919330"

# Новый поисковый запрос (ищем общую педиатрию)
SEARCH_QUERY = "general pediatrics clinical trials guidelines" 

# Инициализируем клиента Google и бота Telegram
ai_client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Отдельный независимый файл памяти для канала педиатрии
HISTORY_FILE = os.path.join(tempfile.gettempdir(), "published_history_general_pediatrics.txt")

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

def save_to_history(title):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(str(title) + "\n")

async def generate_with_retry_protection(prompt):
    models_to_try = ['gemini-3.5-flash', 'gemini-2.5-flash', 'gemini-2.5-pro']
    
    for model_name in models_to_try:
        try:
            print(f"⏳ Запрашиваю данные у модели {model_name}...")
            response = ai_client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            err_msg = str(e)
            if "503" in err_msg or "UNAVAILABLE" in err_msg or "404" in err_msg:
                print(f"⚠️ Модель {model_name} временно недоступна. Пробую резервную...")
                continue
            else:
                raise e
    raise Exception("🚨 Все доступные модели Google сейчас перегружены. Попробуйте позже.")

async def main():
    print(f"🚀 ИИ-агент запускает поиск ОДНОЙ новой статьи по теме: '{SEARCH_QUERY}'...")
    
    already_published = load_history()
    ignored_titles = ", ".join(already_published) if already_published else "Пока нет"
    
    prompt = f"""
    Используя свою фундаментальную академическую базу данных медицинских публикаций (PubMed, Cochrane, Embase), найди ОДНО самое важное и значимое клиническое исследование или руководство (guidelines) в области общей ПЕДИАТРИИ (тема: {SEARCH_QUERY}) за последние 5 лет (с 2021 по 2026 год).
    
    ВАЖНОЕ УСЛОВИЕ: Полностью проигнорируй и НЕ выбирай статьи из этого списка (они уже были опубликованы):
    [{ignored_titles}]
    
    Напиши подробный структурированный клинический обзор этой статьи на РУССКОМ языке.
    НЕ используй никаких HTML-тегов, знаков *, _, ` или < >. Только чистый текст.
    
    Форматируй текст строго по этому шаблону:
    
    [Источник: Название источника, например: PubMed / Ланцет Педиатрия]
    [ДАТА ПУБЛИКАЦИИ: Укажи точный месяц и год публикации статьи]
    
    [НАЗВАНИЕ СТАТЬИ НА РУССКОМ ЯЗЫКЕ]
    
    - Суть исследования: (Подробно в 2-3 предложениях: какая выборка детей, цели, методы).
    - Ключевой результат: (Главный научный вывод исследования, статистические данные, проценты, важные цифры).
    - Клиническое значение: (Как это знание применять на практике врачу-педиатру в поликлинике или стационаре).
    
    Оригинальное название на английском: (Укажи точное оригинальное название статьи)
    Прямая ссылка на статью: (Укажи точную работающую интернет-ссылку на эту статью в PubMed, например https://nih.gov)
    """

    try:
        full_text = await generate_with_retry_protection(prompt)
        clean_post = full_text.strip()
        
        if len(clean_post) > 50:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=clean_post)
            print("✅ Новая статья по педиатрии успешно опубликована в Telegram!")
            
            first_line = clean_post.split("\n")[0]
            save_to_history(first_line) 
            
    except Exception as e:
        print(f"🚨 Системная ошибка ИИ-агента: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as main_error:
        print(f"🚨 Ошибка запуска скрипта: {main_error}")
    
    input("\nРабота завершена. Нажмите Enter для выхода...")
