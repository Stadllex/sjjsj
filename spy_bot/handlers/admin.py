from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_all_categories, get_category_by_id, create_category, delete_category,
    get_words_by_category, get_word_by_id, add_word, set_word_image, delete_word,
)
from keyboards import (
    AdminCallback, WordPageCallback, WordImageCallback,
    admin_main_keyboard, admin_categories_keyboard,
    admin_words_keyboard, word_detail_keyboard, confirm_delete_keyboard,
)
from utils import escape_md

router = Router()


class AdminState(StatesGroup):
    waiting_category_name = State()
    waiting_word_text = State()
    waiting_word_image = State()
    waiting_existing_word_image = State()  # Фото для уже существующего слова


# ─── /admin ──────────────────────────────────────────────────────

@router.message(Command("admin"))
@router.message(Command("settings"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "⚙️ *Панель управления*\n\n"
        "Управляй категориями и локациями\\.",
        parse_mode="MarkdownV2",
        reply_markup=admin_main_keyboard(),
    )


# ─── Главное меню ─────────────────────────────────────────────────

@router.callback_query(AdminCallback.filter(F.action == "back"))
async def cb_admin_back(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.edit_text(
        "⚙️ *Панель управления*\n\n"
        "Управляй категориями и локациями\\.",
        parse_mode="MarkdownV2",
        reply_markup=admin_main_keyboard(),
    )
    await query.answer()


# ─── Список категорий ─────────────────────────────────────────────

@router.callback_query(AdminCallback.filter(F.action == "categories"))
async def cb_admin_categories(query: CallbackQuery, state: FSMContext):
    await state.clear()
    categories = await get_all_categories()
    await query.message.edit_text(
        f"📂 *Категории* \\({len(categories)}\\)\n\n"
        "Нажми на категорию для управления\\.",
        parse_mode="MarkdownV2",
        reply_markup=admin_categories_keyboard(categories),
    )
    await query.answer()


# ─── Добавить категорию ───────────────────────────────────────────

@router.callback_query(AdminCallback.filter(F.action == "add_category"))
async def cb_add_category_start(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text(
        "➕ *Новая категория*\n\n"
        "Отправь название категории\\.\n"
        "_Можно начать с эмодзи, например: `🏖 Пляжи`_\n\n"
        "/cancel для отмены\\.",
        parse_mode="MarkdownV2",
    )
    await state.set_state(AdminState.waiting_category_name)
    await query.answer()


@router.message(AdminState.waiting_category_name)
async def msg_category_name(message: Message, state: FSMContext):
    raw = message.text.strip()
    if not raw:
        await message.answer("⚠️ Название не может быть пустым\\.", parse_mode="MarkdownV2")
        return

    emoji = "🌍"
    name = raw
    words = raw.split(maxsplit=1)
    if words and len(words[0]) <= 4 and not words[0].isascii():
        emoji = words[0]
        name = words[1] if len(words) > 1 else raw

    try:
        cat = await create_category(name=name, emoji=emoji)
        await message.answer(
            f"✅ Категория *{escape_md(cat.emoji + ' ' + cat.name)}* создана\\!",
            parse_mode="MarkdownV2",
            reply_markup=admin_main_keyboard(),
        )
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {escape_md(str(e))}", parse_mode="MarkdownV2")
    await state.clear()


# ─── Слова категории ──────────────────────────────────────────────

@router.callback_query(AdminCallback.filter(F.action == "words"))
async def cb_admin_words(query: CallbackQuery, callback_data: AdminCallback, state: FSMContext):
    await state.clear()
    category_id = callback_data.target_id
    category = await get_category_by_id(category_id)
    if not category:
        await query.answer("Категория не найдена.", show_alert=True)
        return

    words = await get_words_by_category(category_id)
    safe_cat = escape_md(f"{category.emoji} {category.name}")

    await query.message.edit_text(
        f"📂 *{safe_cat}* — {len(words)} слов\n\n"
        "Нажми на слово для управления\\.\n"
        "🖼 — есть фото",
        parse_mode="MarkdownV2",
        reply_markup=admin_words_keyboard(words, category_id=category_id, page=0),
    )
    await query.answer()


@router.callback_query(WordPageCallback.filter())
async def cb_word_page(query: CallbackQuery, callback_data: WordPageCallback, state: FSMContext):
    await state.clear()
    category_id = callback_data.category_id
    page = callback_data.page
    category = await get_category_by_id(category_id)
    words = await get_words_by_category(category_id)
    safe_cat = escape_md(f"{category.emoji} {category.name}")

    await query.message.edit_text(
        f"📂 *{safe_cat}* — {len(words)} слов",
        parse_mode="MarkdownV2",
        reply_markup=admin_words_keyboard(words, category_id=category_id, page=page),
    )
    await query.answer()


# ─── Детали слова ─────────────────────────────────────────────────

@router.callback_query(AdminCallback.filter(F.action == "word_detail"))
async def cb_word_detail(query: CallbackQuery, callback_data: AdminCallback):
    word_id = callback_data.target_id
    word = await get_word_by_id(word_id)
    if not word:
        await query.answer("Слово не найдено.", show_alert=True)
        return

    category = await get_category_by_id(word.category_id)
    safe_word = escape_md(word.word)
    photo_status = "✅ Есть фото" if word.image_id else "❌ Фото нет"

    text = (
        f"📝 *{safe_word}*\n\n"
        f"Фото: {photo_status}"
    )

    if word.image_id:
        try:
            await query.message.delete()
            await query.message.answer_photo(
                photo=word.image_id,
                caption=text,
                parse_mode="MarkdownV2",
                reply_markup=word_detail_keyboard(word, word.category_id),
            )
        except Exception:
            await query.message.edit_text(
                text=text,
                parse_mode="MarkdownV2",
                reply_markup=word_detail_keyboard(word, word.category_id),
            )
    else:
        await query.message.edit_text(
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=word_detail_keyboard(word, word.category_id),
        )
    await query.answer()


# ─── Прикрепить/заменить фото к существующему слову ──────────────

@router.callback_query(WordImageCallback.filter())
async def cb_attach_image_start(query: CallbackQuery, callback_data: WordImageCallback, state: FSMContext):
    word = await get_word_by_id(callback_data.word_id)
    if not word:
        await query.answer("Слово не найдено.", show_alert=True)
        return

    await state.set_state(AdminState.waiting_existing_word_image)
    await state.update_data(word_id=callback_data.word_id, category_id=callback_data.category_id)

    action = "заменить" if word.image_id else "прикрепить"
    safe_word = escape_md(word.word)

    try:
        await query.message.delete()
    except Exception:
        pass

    await query.message.answer(
        f"📷 Отправь фото чтобы {action} его к слову *{safe_word}*\\.\n\n"
        "/cancel для отмены\\.",
        parse_mode="MarkdownV2",
    )
    await query.answer()


@router.message(AdminState.waiting_existing_word_image, F.photo)
async def msg_existing_word_image(message: Message, state: FSMContext):
    data = await state.get_data()
    word_id = data["word_id"]
    category_id = data["category_id"]

    file_id = message.photo[-1].file_id
    word = await set_word_image(word_id=word_id, image_id=file_id)

    if not word:
        await message.answer("⚠️ Слово не найдено\\.", parse_mode="MarkdownV2")
        await state.clear()
        return

    safe_word = escape_md(word.word)
    await message.answer_photo(
        photo=file_id,
        caption=f"✅ Фото для *{safe_word}* сохранено\\!",
        parse_mode="MarkdownV2",
        reply_markup=admin_main_keyboard(),
    )
    await state.clear()


# ─── Добавить новое слово ─────────────────────────────────────────

@router.callback_query(AdminCallback.filter(F.action == "add_word"))
async def cb_add_word_start(query: CallbackQuery, callback_data: AdminCallback, state: FSMContext):
    category_id = callback_data.target_id
    category = await get_category_by_id(category_id)
    safe_cat = escape_md(f"{category.emoji} {category.name}" if category else "?")

    await query.message.edit_text(
        f"➕ *Добавить слово в {safe_cat}*\n\n"
        "Отправь название локации текстом\\.\n"
        "/cancel для отмены\\.",
        parse_mode="MarkdownV2",
    )
    await state.set_state(AdminState.waiting_word_text)
    await state.update_data(category_id=category_id)
    await query.answer()


@router.message(AdminState.waiting_word_text, F.text)
async def msg_word_text(message: Message, state: FSMContext):
    word_text = message.text.strip()
    if not word_text:
        await message.answer("⚠️ Слово не может быть пустым\\.", parse_mode="MarkdownV2")
        return

    await state.update_data(word_text=word_text)
    await message.answer(
        f"📝 Слово: *{escape_md(word_text)}*\n\n"
        "Отправь *фото* для этой локации \\(необязательно\\)\\.\n"
        "Или /skip чтобы сохранить без фото\\.",
        parse_mode="MarkdownV2",
    )
    await state.set_state(AdminState.waiting_word_image)


@router.message(AdminState.waiting_word_image, F.photo)
async def msg_word_image(message: Message, state: FSMContext):
    data = await state.get_data()
    file_id = message.photo[-1].file_id
    word = await add_word(category_id=data["category_id"], word=data["word_text"], image_id=file_id)
    category = await get_category_by_id(data["category_id"])
    safe_cat = escape_md(f"{category.emoji} {category.name}" if category else "")
    await message.answer(
        f"✅ *{escape_md(word.word)}* добавлено в *{safe_cat}* с фото\\!",
        parse_mode="MarkdownV2",
        reply_markup=admin_main_keyboard(),
    )
    await state.clear()


@router.message(AdminState.waiting_word_image, F.text.startswith("/skip"))
async def msg_word_skip_image(message: Message, state: FSMContext):
    data = await state.get_data()
    word = await add_word(category_id=data["category_id"], word=data["word_text"])
    category = await get_category_by_id(data["category_id"])
    safe_cat = escape_md(f"{category.emoji} {category.name}" if category else "")
    await message.answer(
        f"✅ *{escape_md(word.word)}* добавлено в *{safe_cat}*\\.",
        parse_mode="MarkdownV2",
        reply_markup=admin_main_keyboard(),
    )
    await state.clear()


# ─── Удалить слово ────────────────────────────────────────────────

@router.callback_query(AdminCallback.filter(F.action == "del_word"))
async def cb_del_word_confirm(query: CallbackQuery, callback_data: AdminCallback):
    word_id = callback_data.target_id
    word = await get_word_by_id(word_id)
    if not word:
        await query.answer("Слово не найдено.", show_alert=True)
        return

    try:
        await query.message.delete()
    except Exception:
        pass

    await query.message.answer(
        f"🗑 Удалить *{escape_md(word.word)}*?\n\nЭто нельзя отменить\\.",
        parse_mode="MarkdownV2",
        reply_markup=confirm_delete_keyboard("word", word_id, back_id=word.category_id),
    )
    await query.answer()


@router.callback_query(AdminCallback.filter(F.action == "confirm_word"))
async def cb_del_word_execute(query: CallbackQuery, callback_data: AdminCallback):
    word_id = callback_data.target_id
    word = await get_word_by_id(word_id)
    category_id = word.category_id if word else 0
    await delete_word(word_id)
    await query.answer("✅ Слово удалено.")

    categories = await get_all_categories()
    await query.message.edit_text(
        "📂 *Категории*\n\nНажми на категорию для управления\\.",
        parse_mode="MarkdownV2",
        reply_markup=admin_categories_keyboard(categories),
    )


# ─── Удалить категорию ────────────────────────────────────────────

@router.callback_query(AdminCallback.filter(F.action == "del_cat"))
async def cb_del_cat_confirm(query: CallbackQuery, callback_data: AdminCallback):
    cat_id = callback_data.target_id
    category = await get_category_by_id(cat_id)
    if not category:
        await query.answer("Категория не найдена.", show_alert=True)
        return

    words = await get_words_by_category(cat_id)
    safe_cat = escape_md(f"{category.emoji} {category.name}")

    await query.message.edit_text(
        f"🗑 Удалить *{safe_cat}*?\n\n"
        f"⚠️ Также удалится *{len(words)} слов*\\. Нельзя отменить\\.",
        parse_mode="MarkdownV2",
        reply_markup=confirm_delete_keyboard("cat", cat_id, back_id=cat_id),
    )
    await query.answer()


@router.callback_query(AdminCallback.filter(F.action == "confirm_cat"))
async def cb_del_cat_execute(query: CallbackQuery, callback_data: AdminCallback):
    cat_id = callback_data.target_id
    await delete_category(cat_id)
    await query.answer("✅ Категория удалена.")
    categories = await get_all_categories()
    await query.message.edit_text(
        "📂 *Категории*",
        parse_mode="MarkdownV2",
        reply_markup=admin_categories_keyboard(categories),
    )


# ─── /cancel ─────────────────────────────────────────────────────

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    from handlers.setup import main_menu_keyboard
    await state.clear()
    await message.answer(
        "❌ Отменено\\.",
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )
