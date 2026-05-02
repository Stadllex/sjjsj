from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, delete
from .models import Base, Category, Word
from typing import Optional
import random

DATABASE_URL = "sqlite+aiosqlite:///spy_bot.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    """Create all tables and seed default data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_default_data()


async def seed_default_data():
    """Seed the database with default categories and words if empty."""
    async with async_session_factory() as session:
        result = await session.execute(select(Category))
        if result.scalars().first():
            return  # Already seeded

        default_data = {
            ("🌍 Locations", "🌍"): [
                "Airport", "Bank", "Beach", "Casino", "Cathedral",
                "Circus", "Corporate Party", "Crusader Army", "Day Spa",
                "Embassy", "Hospital", "Hotel", "Military Base", "Movie Studio",
                "Ocean Liner", "Passenger Train", "Pirate Ship", "Polar Station",
                "Police Station", "Restaurant", "School", "Service Station",
                "Space Station", "Submarine", "Supermarket", "Theater",
                "University", "World War II Squad",
            ],
            ("🚀 Sci-Fi", "🚀"): [
                "Space Colony", "Alien Mothership", "Time Machine",
                "Asteroid Mine", "Cyberpunk City", "Robot Factory",
                "Parallel Universe", "Wormhole Station", "Terraformed Mars",
                "Space Casino", "Galactic Senate", "Cloning Facility",
            ],
            ("🏰 Fantasy", "🏰"): [
                "Dragon's Lair", "Wizard Tower", "Elven Forest",
                "Dwarf Mine", "Haunted Castle", "Mermaid Kingdom",
                "Ancient Ruins", "Enchanted Tavern", "Fairy Market",
                "Giant's Castle", "Portal Nexus", "Sacred Temple",
            ],
            ("🍕 Food & Drink", "🍕"): [
                "Sushi Restaurant", "Pizza Parlor", "Wine Cellar",
                "Candy Factory", "Brewery", "Bakery", "Food Truck",
                "Ice Cream Shop", "Coffee Roastery", "Cheese Cave",
            ],
        }

        for (name, emoji), words in default_data.items():
            category = Category(name=name, emoji=emoji)
            session.add(category)
            await session.flush()

            for word_text in words:
                word = Word(category_id=category.id, word=word_text)
                session.add(word)

        await session.commit()


# ─── Category CRUD ──────────────────────────────────────────────

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
        result = await session.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()
        if not category:
            return False
        await session.delete(category)
        await session.commit()
        return True


# ─── Word CRUD ──────────────────────────────────────────────────

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
