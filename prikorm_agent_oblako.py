import os
import time
from google import genai
from telegram import Bot
import asyncio

# =====================================================================
# НАСТРОЙКИ И КЛЮЧИ (Считываются из скрытого раздела Environment)
# =====================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = "8974862777:AAGlmHU7AL65zRJDHTBIYrL9psUyorzWiPg"     
TELEGRAM_CHAT_ID = "-1003961458761"

# Поиск строго по авторитетным базам гайдлайнов
SEARCH_QUERY = "CDC Infant Toddler Nutrition, AAP HealthyChildren solid foods, NHS Start for Life Weaning, ESPGHAN complementary feeding position paper guidelines"

ai_client = genai.Client()
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Файл памяти строго для прикорма
HISTORY_FILE = "published_history_baby_feeding_v5.txt"

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
            print(f"⏳ Запрашиваю данные у ИИ-модели {model_name}...")
            task = ai_client.models.generate_content(model=model_name, contents=prompt)
            response = await asyncio.wait_for(asyncio.to_thread(lambda: task), timeout=40.0)
            return response.text
        except Exception as e:
            print(f"⚠️ Модель {model_name} временно недоступна. Ошибка: {e}")
            continue
    raise Exception("🚨 Все доступные модели Google сейчас перегружены.")

async def run_agent():
    print("🔍 ИИ-Агент начинает поиск нового гайдлайна по детскому питанию...")
    
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
    
    Напиши подробный структурированный клинический обзор этой статьи на РУССКОМ языке.
    НЕ используй никаких HTML-тегов, знаков *, _, ` или < >. Только чистый текст.
    
    Форматируй текст строго по шаблону (скопируй заголовки один в один):
    📌 РУБРИКА: НАУЧНЫЙ ПРИКОРМ ДЛЯ РОДИТЕЛЕЙ
    
    [ЗАГОЛОВОК КРУПНЫМИ БУКВАМИ]
    
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
            first_line = clean_post.split("\n")[0].strip()
            
            if first_line in already_published:
                print(f"🔄 Повтор статьи: '{first_line[:40]}...'. Ищу заново через 10 минут...")
                return False
            
            print("📨 Отправляю готовый обзор для родителей в Telegram...")
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=clean_post)
            print("✅ ПОСТ УСПЕШНО ДОСТАВЛЕН В ТЕЛЕГРАМ-КАНАЛ!")
            
            save_to_history(first_line)
            return True
        else:
            print("⚠️ ИИ вернул слишком короткий текст.")
            return False
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА ОБРАБОТКИ ИЛИ ОТПРАВКИ: {e}")
        return False

async def main():
    print("🚀 Сверхлегкий фоновый ИИ-Агент Прикорма успешно запущен на Amvera!")
    # Даем серверу 2 секунды на полную стабилизацию
    await asyncio.sleep(2)
    
    while True:
        success = await run_agent()
        if success:
            print("⏳ Задача выполнена успешно. Следующий запуск ровно через 24 часа...")
            await asyncio.sleep(24 * 60 * 60)
        else:
            print("⏳ Повтор темы или сбой сети. Ищу другую статью через 10 минут...")
            await asyncio.sleep(10 * 60)

if __name__ == "__main__":
    asyncio.run(main())
