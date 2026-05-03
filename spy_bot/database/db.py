import os
import random
from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from .models import Base, Category, Word


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///spy_bot.db")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


DATABASE_URL = get_database_url()
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_default_data()


async def seed_default_data():
    async with async_session_factory() as session:
        result = await session.execute(select(Category))
        if result.scalars().first():
            return

        default_data = {
            ("Страны", "🌍"): [
                "Россия", "США", "Германия", "Франция", "Япония",
                "Китай", "Бразилия", "Австралия", "Индия", "Италия",
                "Испания", "Канада", "Мексика", "Аргентина", "Египет",
                "Турция", "Южная Корея", "Саудовская Аравия", "ЮАР", "Норвегия",
            ],
            ("Фильмы", "🎬"): [
                "Интерстеллар", "Начало", "Титаник", "Аватар", "Матрица",
                "Зелёная книга", "Паразиты", "Джокер", "Дюна", "Оппенгеймер",
                "Бойцовский клуб", "Форрест Гамп", "Побег из Шоушенка", "Гладиатор",
                "Властелин колец", "Гарри Поттер", "Люди в чёрном", "Терминатор",
            ],
            ("Сериалы", "📺"): [
                "Игра престолов", "Во все тяжкие", "Чернобыль", "Ведьмак",
                "Мандалорец", "Очень странные дела", "Корона", "Острые козырьки",
                "Друзья", "Шерлок", "Во все тяжкие", "Лучше звоните Солу",
                "Тёмные начала", "Эйфория", "Белый лотос", "Сукцессия",
            ],
            ("Мобильные игры", "📱"): [
                "Clash of Clans", "PUBG Mobile", "Genshin Impact", "Brawl Stars",
                "Among Us", "Clash Royale", "Pokemon GO", "Subway Surfers",
                "Candy Crush", "Mobile Legends", "Free Fire", "Hearthstone",
                "Arena of Valor", "Wild Rift", "Asphalt 9", "Hill Climb Racing",
            ],
            ("ПК игры", "🖥"): [
                "Minecraft", "GTA 5", "CS:GO", "Dota 2", "League of Legends",
                "Cyberpunk 2077", "The Witcher 3", "Red Dead Redemption 2",
                "Fortnite", "Valorant", "Elden Ring", "Skyrim",
                "Half-Life", "Portal", "Terraria", "Stardew Valley",
            ],
            ("Приложения", "📲"): [
                "Instagram", "TikTok", "YouTube", "Telegram", "WhatsApp",
                "Spotify", "Netflix", "Uber", "Google Maps", "Shazam",
                "Discord", "Zoom", "Duolingo", "Notion", "Figma", "Canva",
            ],
            ("Марвел персонажи", "🦸"): [
                "Человек-паук", "Железный человек", "Тор", "Капитан Америка",
                "Халк", "Чёрная вдова", "Доктор Стрэндж", "Чёрная пантера",
                "Локи", "Ванда", "Стражи Галактики", "Дэдпул",
                "Антмен", "Соколиный глаз", "Капитан Марвел", "Шан-Чи",
            ],
            ("DC персонажи", "🦇"): [
                "Бэтмен", "Супермен", "Чудо-женщина", "Флэш", "Аквамен",
                "Джокер", "Харли Квинн", "Лекс Лютор", "Зелёная стрела",
                "Киборг", "Шазам", "Яд Плющ", "Пингвин", "Риддлер",
                "Найтвинг", "Зелёный фонарь",
            ],
            ("Известные люди", "🌟"): [
                "Илон Маск", "Билл Гейтс", "Стив Джобс", "Альберт Эйнштейн",
                "Леонардо да Винчи", "Наполеон", "Моцарт", "Майкл Джексон",
                "Мухаммед Али", "Криштиану Роналду", "Лионель Месси",
                "Опра Уинфри", "Маск", "Стивен Хокинг", "Чарли Чаплин",
            ],
            ("Футбольные команды", "⚽"): [
                "Реал Мадрид", "Барселона", "Манчестер Сити", "Манчестер Юнайтед",
                "Ливерпуль", "Челси", "Арсенал", "ПСЖ", "Бавария",
                "Ювентус", "Милан", "Интер", "Атлетико Мадрид",
                "Боруссия Дортмунд", "Аякс", "Зенит",
            ],
        }

        for (name, emoji), words in default_data.items():
            category = Category(name=name, emoji=emoji)
            session.add(category)
            await session.flush()
            for word_text in words:
                session.add(Word(category_id=category.id, word=word_text))

        await session.commit()


# ─── Категории ───────────────────────────────────────────────────

async def get_all_categories() -> list[Category]:
    async with async_session_factory() as session:
        result = await session.execute(select(Category).order_by(Category.id))
        return result.scalars().all()


async def get_category_by_id(category_id: int) -> Optional[Category]:
    async with async_session_factory() as session:
        result = await session.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()


async def create_category(name: str, emoji: str = "🌍") -> Category:
    async with async_session_factory() as session:
        category = Category(name=name, emoji=emoji)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category


async def delete_category(category_id: int) -> bool:
    async with async_session_factory() as session:
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if not category:
            return False
        await session.delete(category)
        await session.commit()
        return True


# ─── Слова ───────────────────────────────────────────────────────

async def get_words_by_category(category_id: int) -> list[Word]:
    async with async_session_factory() as session:
        result = await session.execute(
            select(Word).where(Word.category_id == category_id).order_by(Word.id)
        )
        return result.scalars().all()


async def get_word_by_id(word_id: int) -> Optional[Word]:
    async with async_session_factory() as session:
        result = await session.execute(select(Word).where(Word.id == word_id))
        return result.scalar_one_or_none()


async def add_word(category_id: int, word: str, image_id: Optional[str] = None) -> Word:
    async with async_session_factory() as session:
        new_word = Word(category_id=category_id, word=word, image_id=image_id)
        session.add(new_word)
        await session.commit()
        await session.refresh(new_word)
        return new_word


async def set_word_image(word_id: int, image_id: str) -> Optional[Word]:
    async with async_session_factory() as session:
        result = await session.execute(select(Word).where(Word.id == word_id))
        word = result.scalar_one_or_none()
        if not word:
            return None
        word.image_id = image_id
        await session.commit()
        await session.refresh(word)
        return word


async def delete_word(word_id: int) -> bool:
    async with async_session_factory() as session:
        result = await session.execute(select(Word).where(Word.id == word_id))
        word = result.scalar_one_or_none()
        if not word:
            return False
        await session.delete(word)
        await session.commit()
        return True


async def get_random_word(category_id: int) -> Optional[Word]:
    words = await get_words_by_category(category_id)
    if not words:
        return None
    return random.choice(words)
