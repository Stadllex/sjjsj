from aiogram.filters.callback_data import CallbackData


class SetupCallback(CallbackData, prefix="setup"):
    action: str
    value: int = 0


class CategoryCallback(CallbackData, prefix="cat"):
    category_id: int


class RevealCallback(CallbackData, prefix="reveal"):
    player_index: int
    total_players: int
    spy_count: int
    category_id: int
    spy_slots: str


class NextPlayerCallback(CallbackData, prefix="next"):
    player_index: int
    total_players: int
    spy_count: int
    category_id: int
    spy_slots: str


class TimerCallback(CallbackData, prefix="timer"):
    action: str
    duration: int


class AdminCallback(CallbackData, prefix="admin"):
    action: str
    target_id: int = 0


class WordPageCallback(CallbackData, prefix="wpage"):
    category_id: int
    page: int


class WordImageCallback(CallbackData, prefix="wimg"):
    word_id: int
    category_id: int
