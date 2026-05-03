import re
import random
import asyncio
from typing import Optional


def escape_md(text: str) -> str:
    special = r"\_*[]()~`>#+-=|{}.!"
    return re.sub(r"([" + re.escape(special) + r"])", r"\\\1", str(text))


def generate_spy_slots(total_players: int, spy_count: int) -> str:
    slots = random.sample(range(1, total_players + 1), spy_count)
    return ",".join(str(s) for s in slots)


def is_spy(player_index: int, spy_slots: str) -> bool:
    if not spy_slots:
        return False
    return str(player_index) in spy_slots.split(",")


def ordinal(n: int) -> str:
    return f"{n}-й"


async def countdown_task(bot, chat_id: int, message_id: int, total_seconds: int) -> None:
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from keyboards.callbacks import TimerCallback

    remaining = total_seconds
    interval = 10

    while remaining > 0:
        await asyncio.sleep(min(interval, remaining))
        remaining -= interval

        mins, secs = divmod(max(remaining, 0), 60)
        try:
            builder = InlineKeyboardBuilder()
            builder.button(
                text="⏹ Остановить таймер",
                callback_data=TimerCallback(action="stop", duration=0),
            )
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=(
                    f"⏱ *Осталось:* `{mins:02d}:{secs:02d}`\n\n"
                    f"Обсуждайте, кто может быть шпионом\\!"
                ),
                parse_mode="MarkdownV2",
                reply_markup=builder.as_markup(),
            )
        except Exception:
            return

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="🔔 *Время вышло\\!* Голосуйте — кто шпион?",
            parse_mode="MarkdownV2",
        )
    except Exception:
        pass
