import re
import random
import asyncio
from typing import Optional


def escape_md(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    special = r"\_*[]()~`>#+-=|{}.!"
    return re.sub(r"([" + re.escape(special) + r"])", r"\\\1", str(text))


def generate_spy_slots(total_players: int, spy_count: int) -> str:
    """
    Randomly pick which player slots are spies.
    Returns a comma-separated string of 1-based player indices.
    Example: "2,5" means players 2 and 5 are spies.
    """
    slots = random.sample(range(1, total_players + 1), spy_count)
    return ",".join(str(s) for s in slots)


def is_spy(player_index: int, spy_slots: str) -> bool:
    """Return True if player_index (1-based) is a spy."""
    if not spy_slots:
        return False
    return str(player_index) in spy_slots.split(",")


def ordinal(n: int) -> str:
    """Return English ordinal string: 1 -> '1st', 2 -> '2nd', etc."""
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10 if n % 100 not in (11, 12, 13) else 0, "th")
    return f"{n}{suffix}"


async def countdown_task(
    bot,
    chat_id: int,
    message_id: int,
    total_seconds: int,
) -> None:
    """
    Background task: counts down and edits the timer message every 10 seconds.
    Sends a final "Time's up!" notification when done.
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from keyboards.callbacks import TimerCallback

    remaining = total_seconds
    interval = 10  # update every 10 seconds

    while remaining > 0:
        await asyncio.sleep(min(interval, remaining))
        remaining -= interval

        mins, secs = divmod(max(remaining, 0), 60)
        try:
            builder = InlineKeyboardBuilder()
            builder.button(
                text="⏹ Stop Timer",
                callback_data=TimerCallback(action="stop", duration=0),
            )
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=(
                    f"⏱ *Time remaining:* `{mins:02d}:{secs:02d}`\n\n"
                    f"Discuss who the spy might be\\!"
                ),
                parse_mode="MarkdownV2",
                reply_markup=builder.as_markup(),
            )
        except Exception:
            return  # Message was deleted or timer was stopped

    # Time's up
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="🔔 *Time's up\\!* Make your vote — who is the spy?",
            parse_mode="MarkdownV2",
        )
    except Exception:
        pass
