from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_all_categories
from keyboards import (
    players_keyboard, spies_keyboard, categories_keyboard,
    reveal_keyboard, SetupCallback, CategoryCallback,
)
from utils import escape_md, generate_spy_slots

router = Router()


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Новая игра"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="📋 Команды")],
        ],
        resize_keyboard=True,
        persistent=True,
    )


class SetupState(StatesGroup):
    choosing_players = State()
    choosing_spies = State()
    choosing_category = State()


@router.message(CommandStart())
@router.message(F.text == "🎮 Новая игра")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🕵️ *Добро пожаловать в Шпиона\\!*\n\n"
        "Классическая игра _«Передай телефон»_\\.\n\n"
        "Один игрок — *Шпион* — не знает локацию\\. "
        "Остальные знают\\. Сможет ли он остаться незамеченным?\n\n"
        "👥 *Сколько игроков?*",
        parse_mode="MarkdownV2",
        reply_markup=players_keyboard(selected=4),
    )
    await state.set_state(SetupState.choosing_players)
    await state.update_data(players=4)


@router.message(Command("commands"))
@router.message(F.text == "📋 Команды")
async def cmd_commands(message: Message):
    await message.answer(
        "📋 *Список команд:*\n\n"
        "/start — 🎮 Начать новую игру\n"
        "/admin — ⚙️ Управление категориями и словами\n"
        "/commands — 📋 Показать этот список\n"
        "/cancel — ❌ Отменить текущее действие",
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )


# ─── Выбор количества игроков ────────────────────────────────────

@router.callback_query(SetupCallback.filter(F.action == "players"), SetupState.choosing_players)
async def cb_players_select(query: CallbackQuery, callback_data: SetupCallback, state: FSMContext):
    await state.update_data(players=callback_data.value)
    await query.message.edit_reply_markup(reply_markup=players_keyboard(selected=callback_data.value))
    await query.answer()


@router.callback_query(SetupCallback.filter(F.action == "confirm_players"), SetupState.choosing_players)
async def cb_players_confirm(query: CallbackQuery, callback_data: SetupCallback, state: FSMContext):
    players = callback_data.value
    await state.update_data(players=players)
    default_spies = 1

    await query.message.edit_text(
        f"👥 *{players} игроков* выбрано\\.\n\n🕵️ *Сколько шпионов?*",
        parse_mode="MarkdownV2",
        reply_markup=spies_keyboard(player_count=players, selected=default_spies),
    )
    await state.set_state(SetupState.choosing_spies)
    await state.update_data(spies=default_spies)
    await query.answer()


@router.callback_query(SetupCallback.filter(F.action == "back_to_players"), SetupState.choosing_spies)
async def cb_back_to_players(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    players = data.get("players", 4)
    await query.message.edit_text(
        "👥 *Сколько игроков?*",
        parse_mode="MarkdownV2",
        reply_markup=players_keyboard(selected=players),
    )
    await state.set_state(SetupState.choosing_players)
    await query.answer()


# ─── Выбор количества шпионов ────────────────────────────────────

@router.callback_query(SetupCallback.filter(F.action == "spies"), SetupState.choosing_spies)
async def cb_spies_select(query: CallbackQuery, callback_data: SetupCallback, state: FSMContext):
    data = await state.get_data()
    players = data.get("players", 4)
    await state.update_data(spies=callback_data.value)
    await query.message.edit_reply_markup(
        reply_markup=spies_keyboard(player_count=players, selected=callback_data.value)
    )
    await query.answer()


@router.callback_query(SetupCallback.filter(F.action == "confirm_spies"), SetupState.choosing_spies)
async def cb_spies_confirm(query: CallbackQuery, callback_data: SetupCallback, state: FSMContext):
    spies = callback_data.value
    await state.update_data(spies=spies)

    categories = await get_all_categories()
    if not categories:
        await query.answer("⚠️ Нет категорий! Добавьте через /admin", show_alert=True)
        return

    spy_word = "шпион" if spies == 1 else "шпиона" if spies < 5 else "шпионов"
    await query.message.edit_text(
        f"🕵️ *{spies} {spy_word}* выбрано\\.\n\n"
        "📂 *Выберите категорию:*",
        parse_mode="MarkdownV2",
        reply_markup=categories_keyboard(categories),
    )
    await state.set_state(SetupState.choosing_category)
    await query.answer()


@router.callback_query(SetupCallback.filter(F.action == "back_to_spies"), SetupState.choosing_category)
async def cb_back_to_spies(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    players = data.get("players", 4)
    spies = data.get("spies", 1)
    await query.message.edit_text(
        f"👥 *{players} игроков* выбрано\\.\n\n🕵️ *Сколько шпионов?*",
        parse_mode="MarkdownV2",
        reply_markup=spies_keyboard(player_count=players, selected=spies),
    )
    await state.set_state(SetupState.choosing_spies)
    await query.answer()


# ─── Выбор категории → начало раздачи ───────────────────────────

@router.callback_query(CategoryCallback.filter(), SetupState.choosing_category)
async def cb_category_selected(query: CallbackQuery, callback_data: CategoryCallback, state: FSMContext):
    data = await state.get_data()
    total_players: int = data.get("players", 4)
    spy_count: int = data.get("spies", 1)
    category_id: int = callback_data.category_id

    spy_slots = generate_spy_slots(total_players, spy_count)

    await query.message.delete()
    await query.message.answer(
        f"📱 *Игрок 1*, возьми телефон\\!\n\n"
        f"_Нажми кнопку ниже, чтобы увидеть свою роль\\._\n\n"
        f"⚠️ _Не показывай экран другим\\!_",
        parse_mode="MarkdownV2",
        reply_markup=reveal_keyboard(
            player_index=1,
            total_players=total_players,
            spy_count=spy_count,
            category_id=category_id,
            spy_slots=spy_slots,
        ),
    )
    await state.clear()
    await query.answer()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Отменено\\. Используй /start для игры или /admin для управления\\.",
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "⚙️ Настройки")
async def btn_settings(message: Message, state: FSMContext):
    await state.clear()
    from keyboards import admin_main_keyboard
    await message.answer(
        "⚙️ *Панель управления*\n\n"
        "Управляй категориями и локациями\\.",
        parse_mode="MarkdownV2",
        reply_markup=admin_main_keyboard(),
    )
