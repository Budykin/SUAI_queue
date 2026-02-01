from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="Выбрать дисциплину"),
            KeyboardButton(text="Мои очереди"),
        ],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="⚙️ Управление дисциплинами")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

