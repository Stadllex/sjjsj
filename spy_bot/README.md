# 🕵️ Spy Bot — Pass the Phone Edition

A feature-complete Telegram "Spy" social deduction game built with **aiogram 3.x** and **SQLite/SQLAlchemy**.

---

## 📁 Project Structure

```
spy_bot/
├── main.py                  # Bot entry point
├── requirements.txt
├── .env.example
│
├── database/
│   ├── __init__.py
│   ├── models.py            # SQLAlchemy ORM models
│   └── db.py                # Async CRUD operations + seeding
│
├── keyboards/
│   ├── __init__.py
│   ├── callbacks.py         # CallbackData factories
│   └── builders.py          # InlineKeyboardMarkup builders
│
├── handlers/
│   ├── __init__.py
│   ├── setup.py             # /start, player/spy count, category selection
│   ├── game.py              # Reveal roles, pass phone, timer
│   └── admin.py             # /admin — manage categories & words
│
└── utils/
    ├── __init__.py
    └── helpers.py           # MD escaping, spy slot logic, timer task
```

---

## 🚀 Setup & Installation

### 1. Clone & install dependencies

```bash
cd spy_bot
pip install -r requirements.txt
```

### 2. Create your bot

1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the **API token**

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and set BOT_TOKEN=your_token_here
export BOT_TOKEN=your_token_here
```

### 4. Run

```bash
python main.py
```

The SQLite database (`spy_bot.db`) is created automatically on first run with **4 default categories** and **60+ words**.

---

## 🎮 How to Play

### Game Flow

```
/start
  └─► Choose Players (2–12)
        └─► Choose Spies (1 to P/3)
              └─► Choose Category
                    └─► Player 1: "Pick up the phone" → [Reveal My Role]
                          └─► Role shown (Location or "You are the Spy!")
                                └─► [Pass to Player 2] → message DELETED
                                      └─► ... repeat for all players ...
                                            └─► Timer selection
                                                  └─► Discussion → Vote!
```

### Security: The Delete Mechanism

When "Pass to Player N" is pressed, the bot **immediately deletes** the previous message containing the role. This means:
- ✅ Players cannot scroll up to see previous roles
- ✅ The spy's identity is protected
- ✅ Photo locations (if set) are also deleted

---

## ⚙️ Admin Panel

Access via `/admin` or `/settings`:

| Action | Description |
|--------|-------------|
| **📂 Manage Categories** | Browse all categories |
| **➕ Add Category** | Type a name (optional leading emoji) |
| **Add Word** | Type the location name, then optionally send a photo |
| **Delete Word** | Tap any word in the list (with confirmation) |
| **Delete Category** | Deletes category + all its words |

### Adding a Word with an Image

1. `/admin` → tap a category → **➕ Add Word**
2. Send the location name as text
3. Send a photo (or `/skip` for no image)

The photo's `file_id` is stored in the database. When a player with an image location reveals their role, the bot sends a `send_photo` message instead of plain text — giving a premium feel.

---

## 🗄️ Database Schema

### `categories`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer PK | Auto-increment |
| `name` | String(100) | Category name |
| `emoji` | String(10) | Leading emoji |
| `created_at` | DateTime | Creation timestamp |

### `words`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer PK | Auto-increment |
| `category_id` | Integer FK | References `categories.id` |
| `word` | String(200) | Location name |
| `image_id` | String(200) | Telegram `file_id` (nullable) |
| `created_at` | DateTime | Creation timestamp |

---

## 🔧 Customization

### Add your own default categories

Edit `database/db.py` → `seed_default_data()` and add entries to `default_data`.

### Change timer intervals

Edit `handlers/game.py` → `cb_timer_choose` and `keyboards/builders.py` → `timer_keyboard()`.

### Persistent FSM storage (production)

Replace `MemoryStorage()` in `main.py` with Redis storage:

```python
from aiogram.fsm.storage.redis import RedisStorage
storage = RedisStorage.from_url("redis://localhost:6379")
```

---

## 🛡️ Technical Notes

- **MarkdownV2**: All user-generated text is escaped via `utils.escape_md()` before rendering
- **Callback factories**: All game state (player index, spy slots, location) travels through aiogram's `CallbackData` — no server-side session needed for the core game loop
- **Spy slots**: Randomly generated once at game start and encoded as a comma-separated string in callback data (e.g. `"2,5"`)
- **Image handling**: If a word has an `image_id`, the bot uses `send_photo`; otherwise `send_message`
- **Timer**: Runs as a background `asyncio.Task`, editing the message every 10 seconds

---

## 📝 Commands

| Command | Description |
|---------|-------------|
| `/start` | Start a new game |
| `/admin` | Open admin panel |
| `/settings` | Alias for `/admin` |
| `/cancel` | Cancel current action |
