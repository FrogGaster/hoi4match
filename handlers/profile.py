from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.db import get_user_by_telegram_id, get_profile_by_user_id, update_last_seen
from keyboards.reply import get_main_menu

router = Router()


@router.message(Command("profile"))
@router.message(F.text == "👤 Мой профиль")
async def cmd_profile(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала нажми /start")
        return

    await update_last_seen(message.from_user.id)
    profile = await get_profile_by_user_id(user.id)
    if not profile:
        await message.answer("Сначала пройди регистрацию через /start")
        return

    exp_names = {1: "🌱 Новичок", 2: "📖 Мало часов", 3: "⚖️ Средний", 4: "⭐ Опытный", 5: "🏆 Ветеран"}
    exp = exp_names.get(profile.world_level, str(profile.world_level))
    text = (
        "🎖 <b>Твой профиль</b>\n\n"
        f"👤 Ник: <b>{profile.nickname}</b>\n"
        f"📊 Опыт: {exp}\n"
        f"🌍 Любимая нация: {profile.main_dps}\n"
        f"🎮 Режим/моды: {profile.server}\n"
        f"📝 О себе: {profile.description or '—'}\n"
    )
    if profile.photo_file_id:
        await message.answer_photo(profile.photo_file_id, caption=text)
    else:
        await message.answer(text)

    await message.answer(
        "💡 Редактирование профиля — в разработке. Пока используй поиск! 🔍",
        reply_markup=get_main_menu()
    )
