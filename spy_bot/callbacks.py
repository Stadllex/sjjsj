from aiogram.filters.callback_data import CallbackData


class SetupCallback(CallbackData, prefix="setup"):
    """Callback for game setup (player/spy count selection)."""
    action: str       # "players" | "spies" | "confirm"
    value: int = 0


class CategoryCallback(CallbackData, prefix="cat"):
    """Callback for category selection."""
    category_id: int


class RevealCallback(CallbackData, prefix="reveal"):
    """Callback to reveal role for current player."""
    player_index: int    # 1-based current player
    total_players: int
    spy_count: int
    category_id: int
    # Comma-separated spy slot indices (1-based), e.g. "2,5"
    spy_slots: str


class NextPlayerCallback(CallbackData, prefix="next"):
    """Callback to proceed to the next player."""
    player_index: int    # next player's index
    total_players: int
    spy_count: int
    category_id: int
    spy_slots: str
    location_word: str   # the chosen location for this game
    location_image_id: str = ""  # Telegram file_id or empty


class TimerCallback(CallbackData, prefix="timer"):
    """Callback to start / manage discussion timer."""
    action: str     # "start" | "stop"
    duration: int   # seconds


# ─── Admin callbacks ────────────────────────────────────────────

class AdminCallback(CallbackData, prefix="admin"):
    action: str     # "categories" | "add_category" | "words" | "add_word" | "del_cat" | "del_word" | "back"
    target_id: int = 0


class WordPageCallback(CallbackData, prefix="wpage"):
    """Paginate words inside a category."""
    category_id: int
    page: int
