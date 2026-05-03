import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database import get_random_word, get_category_by_id
from keyboards import (
    RevealCallback, NextPlayerCallback, TimerCallback,
    reveal_keyboard, next_player_keyboard, timer_keyboard, stop_timer_keyboard,
)
from utils import escape_md, is_spy, countdown_task

router = Router()

# Состояние игры в памяти: chat_id -> {location_word, location_image_id}
_game_state: dict[int, dict] = {}

# Таймеры: chat_id -> asyncio.Task
_timer_tasks: dict[int, asyncio.Task] = {}


# ─── Показ роли ──────────────────────────────────────────────────

@router.callback_query(RevealCallback.filter())
async def cb_reveal_role(query: CallbackQuery, callback_data: RevealCallback, bot: Bot):
    player_index = callback_data.player_index
    total_players = callback_data.total_players
    spy_count = callback_data.spy_count
    category_id = callback_data.category_id
    spy_slots = callback_data.spy_slots
    chat_id = query.message.chat.id

    is_this_spy = is_spy(player_index, spy_slots)

    if is_this_spy:
        other_spy_slots = [s for s in spy_slots.split(",") if s != str(player_index)]
        spy_note = ""
        if other_spy_slots:
            partners = ", ".join(f"Игрок {s}" for s in other_spy_slots)
            spy_note = f"\n🤝 _Твой{'и' if len(other_spy_slots) > 1 else ''} партнёр{'ы' if len(other_spy_slots) > 1 else ''}: {escape_md(partners)}_"

        text = (
            f"🔴 *Ты ШПИОН\\!*\n\n"
            f"Ты не знаешь локацию\\.\n"
            f"Притворись своим — задавай умные вопросы и не раскройся\\!{spy_note}"
        )

        await query.message.edit_text(
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=next_player_keyboard(
                player_index=player_index,
                total_players=total_players,
                spy_count=spy_count,
                category_id=category_id,
                spy_slots=spy_slots,
            ),
        )
        await query.answer("🕵️ Ты шпион!", show_alert=False)

    else:
        state = _game_state.get(chat_id, {})
        # Сбрасываем состояние если это первый мирный игрок,
        # категория изменилась, или состояние отсутствует
        if (
            not state.get("location_word")
            or state.get("category_id") != category_id
            or player_index == 1
        ):
            word = await get_random_word(category_id)
            if not word:
                await query.answer("⚠️ В категории нет слов!", show_alert=True)
                return
            _game_state[chat_id] = {
                "location_word": word.word,
                "location_image_id": word.image_id or "",
                "category_id": category_id,
            }
            state = _game_state[chat_id]

        location_word = state["location_word"]
        location_image_id = state["location_image_id"]

        category = await get_category_by_id(category_id)
        cat_label = f"{category.emoji} {category.name}" if category else "Неизвестно"
        safe_word = escape_md(location_word)
        safe_cat = escape_md(cat_label)

        caption = (
            f"🟢 *Ты Мирный житель\\!*\n\n"
            f"📍 *Локация:* `{safe_word}`\n"
            f"📂 _Категория: {safe_cat}_\n\n"
            f"_Запомни локацию и веди себя естественно\\. "
            f"Помоги найти шпиона, не раскрывая себя\\!_"
        )

        next_kb = next_player_keyboard(
            player_index=player_index,
            total_players=total_players,
            spy_count=spy_count,
            category_id=category_id,
            spy_slots=spy_slots,
        )

        if location_image_id:
            await query.message.delete()
            await query.message.answer_photo(
                photo=location_image_id,
                caption=caption,
                parse_mode="MarkdownV2",
                reply_markup=next_kb,
            )
        else:
            await query.message.edit_text(
                text=caption,
                parse_mode="MarkdownV2",
                reply_markup=next_kb,
            )

        await query.answer(f"📍 {location_word}", show_alert=False)


# ─── Следующий игрок ─────────────────────────────────────────────

@router.callback_query(NextPlayerCallback.filter())
async def cb_next_player(query: CallbackQuery, callback_data: NextPlayerCallback):
    current_player = callback_data.player_index
    total_players = callback_data.total_players
    spy_count = callback_data.spy_count
    category_id = callback_data.category_id
    spy_slots = callback_data.spy_slots
    chat_id = query.message.chat.id

    next_player = current_player + 1

    try:
        await query.message.delete()
    except Exception:
        pass

    if next_player > total_players:
        # Сохраняем локацию до очистки, чтобы показать её по кнопке
        final_state = _game_state.pop(chat_id, {})
        location_word = final_state.get("location_word", "???")
        location_image_id = final_state.get("location_image_id", "")

        spy_word = "шпион" if spy_count == 1 else "шпиона" if spy_count < 5 else "шпионов"
        await query.message.answer(
            f"✅ *Все {total_players} игроков увидели свои роли\\!*\n\n"
            f"Среди вас *{spy_count} {spy_word}*\\.\n\n"
            f"🗣 *Начинайте обсуждение\\!* Задавайте друг другу вопросы о локации\\. "
            f"Шпион не знает её — но делает вид, что знает\\!\n\n"
            f"⏱ *Выберите время обсуждения:*",
            parse_mode="MarkdownV2",
            reply_markup=timer_keyboard(duration=300),
        )
        # Сохраняем локацию для раскрытия после голосования
        _game_state[chat_id] = {
            "reveal_word": location_word,
            "reveal_image_id": location_image_id,
            "category_id": -1,  # маркер "игра завершена"
        }
    else:
        await query.message.answer(
            f"📱 *Игрок {next_player}*, возьми телефон\\!\n\n"
            f"_Нажми кнопку ниже, чтобы увидеть свою роль\\._\n\n"
            f"⚠️ _Не показывай экран другим\\!_",
            parse_mode="MarkdownV2",
            reply_markup=reveal_keyboard(
                player_index=next_player,
                total_players=total_players,
                spy_count=spy_count,
                category_id=category_id,
                spy_slots=spy_slots,
            ),
        )

    await query.answer()


# ─── Таймер ──────────────────────────────────────────────────────

@router.callback_query(TimerCallback.filter(F.action == "choose"))
async def cb_timer_choose(query: CallbackQuery, callback_data: TimerCallback):
    await query.message.edit_reply_markup(
        reply_markup=timer_keyboard(duration=callback_data.duration)
    )
    await query.answer()


@router.callback_query(TimerCallback.filter(F.action == "start"))
async def cb_timer_start(query: CallbackQuery, callback_data: TimerCallback, bot: Bot):
    duration = callback_data.duration
    chat_id = query.message.chat.id

    if chat_id in _timer_tasks:
        _timer_tasks[chat_id].cancel()

    mins = duration // 60
    await query.message.edit_text(
        f"⏱ *Таймер запущен: {mins} минут*\n\n"
        f"⏳ `{mins:02d}:00` осталось\n\n"
        f"Обсуждайте, кто может быть шпионом\\!",
        parse_mode="MarkdownV2",
        reply_markup=stop_timer_keyboard(),
    )

    task = asyncio.create_task(
        countdown_task(
            bot=bot,
            chat_id=chat_id,
            message_id=query.message.message_id,
            total_seconds=duration,
            timer_tasks=_timer_tasks,
        )
    )
    _timer_tasks[chat_id] = task
    await query.answer(f"⏱ Таймер {mins} мин запущен!")


@router.callback_query(TimerCallback.filter(F.action == "reveal"))
async def cb_reveal_location(query: CallbackQuery):
    chat_id = query.message.chat.id
    state = _game_state.pop(chat_id, {})
    word = state.get("reveal_word", "???")
    image_id = state.get("reveal_image_id", "")

    safe_word = escape_md(word)
    text = (
        f"🔍 *Локация была:* `{safe_word}`\\!\n\n"
        f"_Используй /start чтобы сыграть снова\\._"
    )

    try:
        await query.message.delete()
    except Exception:
        pass

    if image_id:
        await query.message.answer_photo(photo=image_id, caption=text, parse_mode="MarkdownV2")
    else:
        await query.message.answer(text, parse_mode="MarkdownV2")
    await query.answer()


@router.callback_query(TimerCallback.filter(F.action == "stop"))
async def cb_timer_stop(query: CallbackQuery, bot: Bot):
    chat_id = query.message.chat.id

    if chat_id in _timer_tasks:
        _timer_tasks[chat_id].cancel()
        del _timer_tasks[chat_id]

    # Очищаем активную игру, но сохраняем локацию для раскрытия
    reveal_state = _game_state.get(chat_id, {})
    reveal_word = reveal_state.get("reveal_word")

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from keyboards.callbacks import TimerCallback as TC
    builder = InlineKeyboardBuilder()
    if reveal_word:
        builder.button(
            text="🔍 Раскрыть локацию",
            callback_data=TimerCallback(action="reveal", duration=0),
        )

    await query.message.edit_text(
        "⏹ *Таймер остановлен\\.*\n\n"
        "Голосуйте — кто шпион\\?\n\n"
        "_Используй /start чтобы сыграть снова\\!_",
        parse_mode="MarkdownV2",
        reply_markup=builder.as_markup() if reveal_word else None,
    )
    await query.answer("Таймер остановлен.")
