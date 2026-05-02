from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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


class SetupState(StatesGroup):
    choosing_players = State()
    choosing_spies = State()
    choosing_category = State()


# ─── /start ─────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🕵️ *Welcome to Spy\\!*\n\n"
        "The classic _'Pass the Phone'_ social deduction game\\.\n\n"
        "One player will be the *Spy* — they don't know the location\\. "
        "Everyone else does\\. Can they stay hidden?\n\n"
        "👥 *How many players?*",
        parse_mode="MarkdownV2",
        reply_markup=players_keyboard(selected=4),
    )
    await state.set_state(SetupState.choosing_players)
    await state.update_data(players=4)


# ─── Player count selection ──────────────────────────────────────

@router.callback_query(SetupCallback.filter(F.action == "players"), SetupState.choosing_players)
async def cb_players_select(query: CallbackQuery, callback_data: SetupCallback, state: FSMContext):
    await state.update_data(players=callback_data.value)
    await query.message.edit_reply_markup(reply_markup=players_keyboard(selected=callback_data.value))
    await query.answer()


@router.callback_query(SetupCallback.filter(F.action == "confirm_players"), SetupState.choosing_players)
async def cb_players_confirm(query: CallbackQuery, callback_data: SetupCallback, state: FSMContext):
    players = callback_data.value
    await state.update_data(players=players)
    max_spies = max(1, players // 3)
    default_spies = 1

    await query.message.edit_text(
        f"👥 *{players} players* selected\\.\n\n🕵️ *How many spies?*",
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
        "👥 *How many players?*",
        parse_mode="MarkdownV2",
        reply_markup=players_keyboard(selected=players),
    )
    await state.set_state(SetupState.choosing_players)
    await query.answer()


# ─── Spy count selection ─────────────────────────────────────────

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
        await query.answer("⚠️ No categories in the database! Use /admin to add some.", show_alert=True)
        return

    await query.message.edit_text(
        f"🕵️ *{spies} {'spy' if spies == 1 else 'spies'}* selected\\.\n\n"
        "📂 *Choose a category:*",
        parse_mode="MarkdownV2",
        reply_markup=categories_keyboard(categories),
    )
    await state.set_state(SetupState.choosing_category)
    await query.answer()


# ─── Category selection → begin distribution ────────────────────

@router.callback_query(CategoryCallback.filter(), SetupState.choosing_category)
async def cb_category_selected(query: CallbackQuery, callback_data: CategoryCallback, state: FSMContext):
    data = await state.get_data()
    total_players: int = data.get("players", 4)
    spy_count: int = data.get("spies", 1)
    category_id: int = callback_data.category_id

    spy_slots = generate_spy_slots(total_players, spy_count)

    player_num = 1
    safe_name = escape_md(f"Player {player_num}")

    await query.message.delete()
    await query.message.answer(
        f"📱 *{safe_name}*, pick up the phone\\!\n\n"
        f"_Press the button below to see your secret role\\._\n\n"
        f"⚠️ _Don't let others see your screen\\!_",
        parse_mode="MarkdownV2",
        reply_markup=reveal_keyboard(
            player_index=player_num,
            total_players=total_players,
            spy_count=spy_count,
            category_id=category_id,
            spy_slots=spy_slots,
        ),
    )
    await state.clear()
    await query.answer()
