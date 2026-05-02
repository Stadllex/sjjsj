import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database import get_random_word, get_category_by_id
from keyboards import (
    RevealCallback, NextPlayerCallback, TimerCallback,
    reveal_keyboard, next_player_keyboard, timer_keyboard, stop_timer_keyboard,
)
from utils import escape_md, is_spy, ordinal, countdown_task

router = Router()

# Track active timer tasks: chat_id -> asyncio.Task
_timer_tasks: dict[int, asyncio.Task] = {}


# ─── Reveal Role ────────────────────────────────────────────────

@router.callback_query(RevealCallback.filter())
async def cb_reveal_role(query: CallbackQuery, callback_data: RevealCallback, bot: Bot):
    player_index = callback_data.player_index
    total_players = callback_data.total_players
    spy_count = callback_data.spy_count
    category_id = callback_data.category_id
    spy_slots = callback_data.spy_slots

    is_this_spy = is_spy(player_index, spy_slots)

    if is_this_spy:
        # ── Spy reveal ──
        other_spy_slots = [
            s for s in spy_slots.split(",") if s != str(player_index)
        ]
        spy_note = ""
        if other_spy_slots:
            partners = ", ".join(f"Player {s}" for s in other_spy_slots)
            spy_note = f"\n🤝 _Your partner{'s' if len(other_spy_slots) > 1 else ''}: {escape_md(partners)}_"

        text = (
            f"🔴 *You are the SPY\\!*\n\n"
            f"You don't know the location\\.\n"
            f"Blend in — ask clever questions and avoid suspicion\\!{spy_note}"
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
                location_word="",
                location_image_id="",
            ),
        )
        await query.answer("🕵️ You are the spy!", show_alert=False)

    else:
        # ── Civilian reveal — fetch location ──
        word = await get_random_word(category_id)
        if not word:
            await query.answer("⚠️ No words found in this category!", show_alert=True)
            return

        category = await get_category_by_id(category_id)
        cat_label = f"{category.emoji} {category.name}" if category else "Unknown"
        safe_word = escape_md(word.word)
        safe_cat = escape_md(cat_label)

        caption = (
            f"🟢 *You are a Civilian\\!*\n\n"
            f"📍 *Location:* `{safe_word}`\n"
            f"📂 _Category: {safe_cat}_\n\n"
            f"_Remember the location and discuss naturally\\. "
            f"Help find the spy without being too obvious\\!_"
        )

        next_kb = next_player_keyboard(
            player_index=player_index,
            total_players=total_players,
            spy_count=spy_count,
            category_id=category_id,
            spy_slots=spy_slots,
            location_word=word.word,
            location_image_id=word.image_id or "",
        )

        if word.image_id:
            # Delete text message, send photo with caption
            await query.message.delete()
            await query.message.answer_photo(
                photo=word.image_id,
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

        await query.answer(f"📍 {word.word}", show_alert=False)


# ─── Next Player (The Wipe) ─────────────────────────────────────

@router.callback_query(NextPlayerCallback.filter())
async def cb_next_player(query: CallbackQuery, callback_data: NextPlayerCallback):
    current_player = callback_data.player_index
    total_players = callback_data.total_players
    spy_count = callback_data.spy_count
    category_id = callback_data.category_id
    spy_slots = callback_data.spy_slots

    next_player = current_player + 1

    # SECURITY: Always delete the current message first
    try:
        await query.message.delete()
    except Exception:
        pass  # Already deleted or can't delete

    if next_player > total_players:
        # ── All players have seen their roles — show timer selection ──
        spy_plural = "spies" if spy_count > 1 else "spy"
        await query.message.answer(
            f"✅ *All {total_players} players have seen their roles\\!*\n\n"
            f"There {'are' if spy_count > 1 else 'is'} *{spy_count} {spy_plural}* among you\\.\n\n"
            f"🗣 *Start the discussion\\!* Ask each other questions about the location\\. "
            f"The spy doesn't know it — but must pretend they do\\!\n\n"
            f"⏱ *Set a discussion timer:*",
            parse_mode="MarkdownV2",
            reply_markup=timer_keyboard(duration=300),
        )
    else:
        # ── Next player's turn ──
        safe_name = escape_md(f"Player {next_player}")
        await query.message.answer(
            f"📱 *{safe_name}*, pick up the phone\\!\n\n"
            f"_Press the button below to see your secret role\\._\n\n"
            f"⚠️ _Don't let others see your screen\\!_",
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


# ─── Timer ──────────────────────────────────────────────────────

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

    # Cancel any running timer for this chat
    if chat_id in _timer_tasks:
        _timer_tasks[chat_id].cancel()

    mins = duration // 60
    await query.message.edit_text(
        f"⏱ *Timer started: {mins} minutes*\n\n"
        f"⏳ `{mins:02d}:00` remaining\n\n"
        f"Discuss who the spy might be\\!",
        parse_mode="MarkdownV2",
        reply_markup=stop_timer_keyboard(),
    )

    task = asyncio.create_task(
        countdown_task(
            bot=bot,
            chat_id=chat_id,
            message_id=query.message.message_id,
            total_seconds=duration,
        )
    )
    _timer_tasks[chat_id] = task
    await query.answer(f"⏱ {mins}-minute timer started!")


@router.callback_query(TimerCallback.filter(F.action == "stop"))
async def cb_timer_stop(query: CallbackQuery, bot: Bot):
    chat_id = query.message.chat.id

    if chat_id in _timer_tasks:
        _timer_tasks[chat_id].cancel()
        del _timer_tasks[chat_id]

    await query.message.edit_text(
        "⏹ *Timer stopped\\.*\n\n"
        "Make your vote — who is the spy\\?\n\n"
        "_Use /start to play again\\!_",
        parse_mode="MarkdownV2",
    )
    await query.answer("Timer stopped.")
