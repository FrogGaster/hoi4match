import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env file")

DB_PATH = os.getenv("DB_PATH", "teammates.db")

# Канал, подписка на который обязательна
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "The_Club_of_the_Executed")

# Админы (telegram_id через запятую)
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# Лимит просмотров в день
DAILY_VIEW_LIMIT = int(os.getenv("DAILY_VIEW_LIMIT", "50"))
