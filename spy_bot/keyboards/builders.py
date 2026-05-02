from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from .callbacks import (
    SetupCallback, CategoryCallback, RevealCallback,
    NextPlayerCallback, TimerCallback, AdminCallback, WordPageCallback,
)
from database import Category, Word


# ─── Setup keyboards ────────────────────────────────────────────

def players_keyboard(selected: int = 3) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for n in range(2, 13):
        mark = "✅ " if n == selected else ""
        builder.button(
            text=f"{mark}{n}",
            callback_data=SetupCallback(action="players", value=n),
        )
    builder.adjust(4)
    builder.row(
        InlineKeyboardButton(
            text="Next ➡️",
            callback_data=SetupCallback(action="confirm_players", value=selected).pack(),
        )
    )
    return builder.as_markup()


def spies_keyboard(player_count: int, selected: int = 1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    max_spies = max(1, player_count // 3)
    for n in range(1, max_spies + 1):
        mark = "✅ " if n == selected else ""
        builder.button(
            text=f"{mark}{n}",
            callback_data=SetupCallback(action="spies", value=n),
        )
    builder.adjust(4)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data=SetupCallback(action="back_to_players", value=0).pack(),
        ),
        InlineKeyboardButton(
            text="Next ➡️",
            callback_data=SetupCallback(action="confirm_spies", value=selected).pack(),
        ),
    )
    return builder.as_markup()


def categories_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"{cat.emoji} {cat.name}",
            callback_data=CategoryCallback(category_id=cat.id),
        )
    builder.adjust(2)
    return builder.as_markup()


# ─── Game keyboards ─────────────────────────────────────────────

def reveal_keyboard(
    player_index: int,
    total_players: int,
    spy_count: int,
    category_id: int,
    spy_slots: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="👁 Reveal My Role",
        callback_data=RevealCallback(
            player_index=player_index,
            total_players=total_players,
            spy_count=spy_count,
            category_id=category_id,
            spy_slots=spy_slots,
        ),
    )
    return builder.as_markup()


def next_player_keyboard(
    player_index: int,
    total_players: int,
    spy_count: int,
    category_id: int,
    spy_slots: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    is_last = player_index >= total_players
    next_label = "▶️ Start Game" if is_last else f"📱 Pass to Player {player_index + 1}"

    builder.button(
        text=next_label,
        callback_data=NextPlayerCallback(
            player_index=player_index,
            total_players=total_players,
            spy_count=spy_count,
            category_id=category_id,
            spy_slots=spy_slots,
        ),
    )
    return builder.as_markup()


def timer_keyboard(duration: int = 300) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, secs in [("3 min", 180), ("5 min", 300), ("8 min", 480), ("10 min", 600)]:
        mark = "✅ " if secs == duration else ""
        builder.button(
            text=f"{mark}{label}",
            callback_data=TimerCallback(action="choose", duration=secs),
        )
    builder.adjust(4)
    builder.row(
        InlineKeyboardButton(
            text="⏱ Start Timer",
            callback_data=TimerCallback(action="start", duration=duration).pack(),
        )
    )
    return builder.as_markup()


def stop_timer_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏹ Stop Timer",
        callback_data=TimerCallback(action="stop", duration=0),
    )
    return builder.as_markup()


# ─── Admin keyboards ────────────────────────────────────────────

def admin_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📂 Manage Categories", callback_data=AdminCallback(action="categories"))
    builder.button(text="➕ Add Category", callback_data=AdminCallback(action="add_category"))
    builder.adjust(1)
    return builder.as_markup()


def admin_categories_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"{cat.emoji} {cat.name}",
            callback_data=AdminCallback(action="words", target_id=cat.id),
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data=AdminCallback(action="back").pack(),
        )
    )
    return builder.as_markup()


def admin_category_detail_keyboard(category_id: int, page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="➕ Add Word",
        callback_data=AdminCallback(action="add_word", target_id=category_id),
    )
    builder.button(
        text="🗑 Delete Category",
        callback_data=AdminCallback(action="del_cat", target_id=category_id),
    )
    builder.button(
        text="⬅️ Back",
        callback_data=AdminCallback(action="categories"),
    )
    builder.adjust(1)
    return builder.as_markup()


def admin_words_keyboard(words: list[Word], category_id: int, page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    page_size = 8
    start = page * page_size
    page_words = words[start : start + page_size]

    for word in page_words:
        img_icon = "🖼 " if word.image_id else ""
        builder.button(
            text=f"{img_icon}{word.word} ✕",
            callback_data=AdminCallback(action="del_word", target_id=word.id),
        )
    builder.adjust(2)

    # Pagination
    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                text="⬅️ Prev",
                callback_data=WordPageCallback(category_id=category_id, page=page - 1).pack(),
            )
        )
    if start + page_size < len(words):
        nav.append(
            InlineKeyboardButton(
                text="Next ➡️",
                callback_data=WordPageCallback(category_id=category_id, page=page + 1).pack(),
            )
        )
    if nav:
        builder.row(*nav)

    builder.row(
        InlineKeyboardButton(
            text="➕ Add Word",
            callback_data=AdminCallback(action="add_word", target_id=category_id).pack(),
        ),
        InlineKeyboardButton(
            text="🔙 Categories",
            callback_data=AdminCallback(action="categories").pack(),
        ),
    )
    return builder.as_markup()


def confirm_delete_keyboard(action: str, target_id: int, back_id: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Yes, Delete",
        callback_data=AdminCallback(action=f"confirm_{action}", target_id=target_id),
    )
    builder.button(
        text="❌ Cancel",
        callback_data=AdminCallback(action="words", target_id=back_id),
    )
    builder.adjust(2)
    return builder.as_markup()
