import os
import random
from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from .models import Base, Category, Word


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///spy_bot.db")

    # Railway даёт postgres:// — меняем на правильный asyncpg драйвер
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    # Если вдруг уже postgresql:// без asyncpg
    elif url.startswith("postgresql://"):
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
            return  # Уже засеяно

        default_data = {
            ("Локации", "🌍"): [
                "Аэропорт", "Банк", "Пляж", "Казино", "Собор",
                "Цирк", "Корпоратив", "Армия крестоносцев", "Спа-салон",
                "Посольство", "Больница", "Отель", "Военная база", "Киностудия",
                "Океанский лайнер", "Пассажирский поезд", "Пиратский корабль",
                "Полярная станция", "Полицейский участок", "Ресторан", "Школа",
                "Автозаправка", "Космическая станция", "Подводная лодка",
                "Супермаркет", "Театр", "Университет",
            ],
            ("Фантастика", "🚀"): [
                "Космическая колония", "Корабль пришельцев", "Машина времени",
                "Астероидный рудник", "Киберпанк-город", "Завод роботов",
                "Параллельная вселенная", "Галактический сенат", "Терраформированный Марс",
            ],
            ("Фэнтези", "🏰"): [
                "Логово дракона", "Башня волшебника", "Лес эльфов",
                "Шахта гномов", "Замок с привидениями", "Королевство русалок",
                "Древние руины", "Зачарованная таверна", "Рынок фей",
            ],
            ("Еда и напитки", "🍕"): [
                "Суши-ресторан", "Пиццерия", "Винный погреб",
                "Кондитерская фабрика", "Пивоварня", "Пекарня",
                "Фудтрак", "Кафе-мороженое", "Кофейня",
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


async def add_word(category_id: int, word: str, image_id: Optional[str] = None) -> Word:
    async with async_session_factory() as session:
        new_word = Word(category_id=category_id, word=word, image_id=image_id)
        session.add(new_word)
        await session.commit()
        await session.refresh(new_word)
        return new_word


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
