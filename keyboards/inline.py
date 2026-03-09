from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData


class ActionCallback(CallbackData, prefix="act"):
    action: str  # "like" | "dislike"
    user_id: int


class ResponseCallback(CallbackData, prefix="resp"):
    """Ответ на лайк: взаимный лайк или отказ."""
    action: str  # "like" | "dislike"
    user_id: int  # кто тебя лайкнул


class ExpCallback(CallbackData, prefix="exp"):
    level: int


class ReportCallback(CallbackData, prefix="report"):
    user_id: int  # кого репортим


def get_response_keyboard(liker_user_id: int) -> InlineKeyboardMarkup:
    """Кнопки ответа на лайк: взаимный лайк или отказ."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="❤️ Взаимный лайк",
            callback_data=ResponseCallback(action="like", user_id=liker_user_id).pack()
        ),
        InlineKeyboardButton(
            text="👎 Нет, спасибо",
            callback_data=ResponseCallback(action="dislike", user_id=liker_user_id).pack()
        )
    )
    builder.adjust(2)
    return builder.as_markup()


def get_action_keyboard(candidate_user_id: int) -> InlineKeyboardMarkup:
    """Кнопки лайк / дизлайк / жалоба."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="❤️ Нравится",
            callback_data=ActionCallback(action="like", user_id=candidate_user_id).pack()
        ),
        InlineKeyboardButton(
            text="➡️ Дальше",
            callback_data=ActionCallback(action="dislike", user_id=candidate_user_id).pack()
        ),
        InlineKeyboardButton(
            text="🚩 Жалоба",
            callback_data=ReportCallback(user_id=candidate_user_id).pack()
        )
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def get_exp_keyboard() -> InlineKeyboardMarkup:
    """Кнопки выбора опыта (1-5)."""
    builder = InlineKeyboardBuilder()
    labels = [
        (1, "🌱 Новичок"),
        (2, "📖 Мало часов"),
        (3, "⚖️ Средний"),
        (4, "⭐ Опытный"),
        (5, "🏆 Ветеран"),
    ]
    for level, label in labels:
        builder.button(text=label, callback_data=ExpCallback(level=level).pack())
    builder.adjust(2, 2, 1)  # 2 + 2 + 1
    return builder.as_markup()
