import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from database.db import init_db
from handlers import setup_routers
from middlewares.subscription import SubscriptionMiddleware
from tasks import setup_weekly_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    await init_db()
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    router = setup_routers()
    router.message.middleware(SubscriptionMiddleware())
    router.callback_query.middleware(SubscriptionMiddleware())
    dp.include_router(router)

    setup_weekly_digest(bot, config.DB_PATH)

    logger.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
