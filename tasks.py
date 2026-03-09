"""Фоновые задачи: еженедельный дайджест."""
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


def setup_weekly_digest(bot, db_path: str):
    """Запуск еженедельной рассылки «появились новые»."""
    import aiosqlite

    async def send_weekly_digest():
        try:
            async with aiosqlite.connect(db_path) as db:
                cursor = await db.execute(
                    """SELECT u.telegram_id FROM users u
                       JOIN profiles p ON p.user_id = u.id
                       WHERE u.id NOT IN (SELECT user_id FROM banned_users)"""
                )
                ids = [row[0] for row in await cursor.fetchall()]

            for tid in ids:
                try:
                    await bot.send_message(
                        tid,
                        "📬 <b>Еженедельный дайджест</b>\n\n"
                        "Появились новые тиммейты! Загляни в поиск 🔍"
                    )
                except Exception as e:
                    logger.debug("Weekly digest skip %s: %s", tid, e)

        except Exception as e:
            logger.exception("Weekly digest error: %s", e)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_weekly_digest,
        "cron",
        day_of_week="sun",
        hour=12,
        minute=0,
        id="weekly_digest",
    )
    scheduler.start()
    return scheduler
