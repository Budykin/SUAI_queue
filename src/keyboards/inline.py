from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def subjects_keyboard(subjects: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=disc.name, callback_data=f"subject:{disc.id}")]
        for disc in subjects
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_change_users_keyboard(users: list) -> InlineKeyboardMarkup:
    buttons = []
    for idx, user in enumerate(users, start=1):
        buttons.append([
            InlineKeyboardButton(text=f"{idx}. {user.full_name}", callback_data=f"rename:user:{user.tg_id}"),
            InlineKeyboardButton(text="❌Удалить", callback_data=f"delete:user:{user.tg_id}")
        ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def available_queues(subjects: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=disc.name, callback_data=f"subject:{disc.id}")]
        for disc in subjects
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def queue_actions_keyboard(
    subject_id: int,
    in_queue: bool,
    is_admin: bool,
) -> InlineKeyboardMarkup:
    buttons = []

    if in_queue:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="Покинуть очередь",
                    callback_data=f"queue:leave:{subject_id}",
                )
            ]
        )
    else:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="Встать в очередь",
                    callback_data=f"queue:join:{subject_id}",
                )
            ]
        )

    if is_admin:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="Очистить очередь",
                    callback_data=f"queue:clear1:{subject_id}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def queue_clear_confirmation_keyboard(subject_id: int)-> InlineKeyboardMarkup:
    buttons = []
    buttons.append([
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"subject:{subject_id}",
        ),
        InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data=f"queue:clear2:{subject_id}",
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_subjects_keyboard(subjects: list) -> InlineKeyboardMarkup:
    """Клавиатура для админов: список дисциплин с кнопками редактирования и удаления"""
    buttons = []
    for disc in subjects:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"✏️ {disc.name}",
                    callback_data=f"admin:edit_disc:{disc.id}",
                ),
                InlineKeyboardButton(
                    text="❌",
                    callback_data=f"admin:delete_disc:{disc.id}",
                ),
            ]
        )
    buttons.append([InlineKeyboardButton(text="➕ Добавить дисциплину", callback_data="admin:add_disc")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin:subjects_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_delete_subject_keyboard(subject_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления дисциплины"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data=f"admin:confirm_delete:{subject_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="admin:subjects_back",
                ),
            ]
        ]
    )

