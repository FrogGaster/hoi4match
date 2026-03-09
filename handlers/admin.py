"""Админ-панель: статистика, рассылка, бан."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import config
from database.db import (
    get_admin_stats,
    get_all_telegram_ids,
    ban_user_by_telegram_id,
    get_user_by_telegram_id,
    get_profile_by_user_id,
)

router = Router()


def is_admin(telegram_id: int) -> bool:
    return telegram_id in config.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return

    stats = await get_admin_stats()
    text = (
        "🔧 <b>Админ-панель</b>\n"
        "━━━━━━━━━━━━━━\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"📋 Анкет: {stats['total_profiles']}\n"
        f"❤️ Лайков всего: {stats['total_likes']}\n"
        f"🚩 Жалоб: {stats['total_reports']}\n"
        f"⛔ Забанено: {stats['total_banned']}\n\n"
        "Команды:\n"
        "/admin_broadcast - Рассылка\n"
        "/admin_ban [id] - Забанить"
    )
    await message.answer(text)


@router.message(Command("admin_broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Отправь текст рассылки: /admin_broadcast Ваш текст")
        return

    text = args[1]
    ids = await get_all_telegram_ids()
    ok, fail = 0, 0
    for tid in ids:
        try:
            await message.bot.send_message(tid, text)
            ok += 1
        except Exception:
            fail += 1

    await message.answer(f"✅ Отправлено: {ok}\n❌ Ошибок: {fail}")


@router.message(Command("admin_ban"))
async def cmd_ban(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /admin_ban 123456789")
        return

    try:
        telegram_id = int(parts[1])
    except ValueError:
        await message.answer("telegram_id должен быть числом")
        return

    reason = " ".join(parts[2:]) if len(parts) > 2 else ""

    if await ban_user_by_telegram_id(telegram_id, reason):
        await message.answer(f"⛔ Пользователь {telegram_id} забанен")
    else:
        await message.answer("Пользователь не найден")
