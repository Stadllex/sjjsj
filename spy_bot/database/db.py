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
                "Россия", "США", "Германия", "Франция", "Япония", "Китай", "Бразилия", "Австралия", "Индия", "Италия",
                "Испания", "Канада", "Мексика", "Аргентина", "Египет", "Турция", "Южная Корея", "Саудовская Аравия", "ЮАР", "Норвегия",
                "Швеция", "Швейцария", "Нидерланды", "Греция", "Польша", "Таиланд", "Вьетнам", "Индонезия", "ОАЭ", "Португалия",
                "Финляндия", "Дания", "Австрия", "Бельгия", "Чехия", "Венгрия", "Израиль", "Марокко", "Куба", "Чили",
                "Перу", "Казахстан", "Грузия", "Исландия", "Новая Зеландия", "Сингапур", "Ирландия", "Малайзия", "Сербия", "Нигерия",
                "Алжир", "Ангола", "Боливия", "Ватикан", "Венесуэла", "Гана", "Доминикана", "Иран", "Ирак", "Кения",
                "Колумбия", "Люксембург", "Монако", "Монголия", "Пакистан", "Панама", "Уругвай", "Филиппины", "Хорватия", "Эстония"
            ],
            ("Фильмы", "🎬"): [
                "Интерстеллар", "Начало", "Титаник", "Аватар", "Матрица", "Зелёная книга", "Паразиты", "Джокер", "Дюна", "Оппенгеймер",
                "Бойцовский клуб", "Форрест Гамп", "Побег из Шоушенка", "Гладиатор", "Властелин колец", "Гарри Поттер", "Люди в чёрном", "Терминатор",
                "Крёстный отец", "Криминальное чтиво", "Леон", "Назад в будущее", "Парк Юрского периода", "Челюсти", "Звёздные войны", "Пираты Карибского моря",
                "Шрэк", "Король Лев", "Клаус", "Джентльмены", "Ла-Ла Ленд", "Великий Гэтсби", "Волк с Уолл-стрит", "Джанго освобождённый",
                "1+1", "Легенда №17", "Брат", "Служебный роман", "Иван Васильевич меняет профессию", "Бриллиантовая рука", "Кин-дза-дза!",
                "Чужой", "Хищник", "Молчание ягнят", "Семь", "Престиж", "Остров проклятых", "Поймай меня, если сможешь", "Один дома", "Крепкий орешек",
                "Звезда родилась", "Мемуары гейши", "Пианист", "Список Шиндлера", "Красотка", "Гордость и предубеждение", "Дневник памяти", "Мальчишник в Вегасе",
                "Джон Уик", "Безумный Макс", "Черная пантера", "Чудо-женщина", "Мстители", "Лабиринт Фавна", "Большой Лебовски", "Карты, деньги, два ствола",
                "Зодиак", "Социальная сеть", "Гравитация", "Бегущий по лезвию"
            ],
            ("Сериалы", "📺"): [
                "Игра престолов", "Во все тяжкие", "Чернобыль", "Ведьмак", "Мандалорец", "Очень странные дела" "Острые козырьки",
                "Друзья", "Шерлок", "Лучше звоните Солу", "Эйфория", "Офис",
             "Теория большого взрыва", "Доктор Хаус", , "Сверхъестественное",
                "Ходячие мертвецы", "Бумажный дом", "Игра в кальмара", "Черное зеркало",
                "Пацаны", "Рик и Морти", "Симпсоны", "Гриффины", "Южный Парк",
                 "Остаться в живых", "Побег",
                "Уэнсдей", "Одни из нас",
                "Кухня", "Интерны", "Мистер Робот", "Декстер", "Сопрано"
            ],
            ("Мобильные игры", "📱"): [
                "Clash of Clans", "PUBG Mobile", "Genshin Impact", "Brawl Stars", "Among Us", "Clash Royale", "Pokemon GO", "Subway Surfers",
                "Candy Crush", "Mobile Legends", "Free Fire", "Hearthstone", "Arena of Valor", "Wild Rift", "Asphalt 9", "Hill Climb Racing",
                "Gardenscapes", "Roblox", "Minecraft PE", "Call of Duty Mobile", "Angry Birds", "Plants vs Zombies", "Fruit Ninja", "Doodle Jump",
                "Jetpack Joyride", "Temple Run", "Shadow Fight 2", "Vector", "Flappy Bird", "Cut the Rope", "Talking Tom", "SimCity BuildIt",
                "8 Ball Pool", "Stardew Valley Mobile", "Dead by Daylight Mobile", "Toca Boca", "Homescapes", "Fishdom", "State of Survival",
                "Rise of Kingdoms", "Summoners War", "Raid: Shadow Legends", "Afk Arena", "Honkai: Star Rail", "Diablo Immortal", "Eternium",
                "TETRIS", "Bad Piggies", "Pixel Gun 3D", "Last Day on Earth", "Plague Inc", "Terraria", "Limbo", "Monument Valley",
                "Modern Combat 5", "World of Tanks Blitz", "Shadowgun", "Injustice 2", "Mortal Kombat Mobile", "Real Racing 3", "Dead Trigger 2",
                "Angry Birds 2", "Plants vs Zombies 2", "CSR Racing 2", "War Robots"
            ],
            ("ПК игры", "🖥"): [
                "Minecraft", "GTA 5", "CS:GO", "Dota 2", "League of Legends", "Cyberpunk 2077", "The Witcher 3", "Red Dead Redemption 2",
                "Fortnite", "Valorant", "Elden Ring", "Skyrim", "Half-Life", "Portal", "Terraria", "Stardew Valley", "Overwatch", "Apex Legends",
                "World of Warcraft", "StarCraft 2", "Diablo 4", "Baldur's Gate 3", "Hades", "Doom Eternal", "Resident Evil Village",
                "Fallout 4", "Mass Effect", "Dragon Age", "BioShock", "Dishonored", "Assassin's Creed", "Far Cry", "Call of Duty",
                "Battlefield", "Sims 4", "Civilization VI", "Cities: Skylines", "Euro Truck Simulator 2", "Phasmophobia", "Rust",
                "DayZ", "Tarkov", "Starfield", "Hollow Knight", "Cuphead", "Dark Souls", "Bloodborne", "Sekiro", "Forza Horizon 5",
                "Life is Strange", "Detroit: Become Human", "Control", "Death Stranding", "Dead Space", "Alan Wake 2", "God of War",
                "Spider-Man", "Horizon Zero Dawn", "The Last of Us", "Uncharted", "Portal 2", "Left 4 Dead 2", "Team Fortress 2", "Garry's Mod",
                "Payday 2", "Outer Wilds", "Sea of Thieves", "Subnautica", "Crysis", "Metal Gear Solid"
            ],
            ("Приложения", "📲"): [
                "Instagram", "TikTok", "YouTube", "Telegram", "WhatsApp", "Spotify", "Netflix", "Uber", "Google Maps", "Shazam",
                "Discord", "Zoom", "Duolingo", "Notion", "Figma", "Canva", "Pinterest", "Reddit", "Twitter", "Snapchat",
                "Viber", "Skype", "Slack", "Microsoft Teams", "Trello", "Evernote", "Airbnb", "Booking.com", "Tinder", "AliExpress",
                "Wildberries", "Ozon", "Avito", "Яндекс Go", "Delivery Club", "Самокат", "Сбербанк Онлайн", "Тинькофф", "Госуслуги",
                "CapCut", "PicsArt", "VSCO", "Lightroom", "Google Drive", "Dropbox", "Kindle", "Twitch", "Steam", "SoundCloud",
                "LinkedIn", "eBay", "Amazon", "Behance", "WolframAlpha", "Speedtest", "Truecaller", "Remini", "SkyScanner", "TripAdvisor",
                "FaceApp", "Reface", "Nike Run Club", "Flo", "MyFitnessPal", "Strava", "InShot", "Kwai", "Badoo", "Hinge"
            ],
            ("Марвел персонажи", "🦸"): [
                "Человек-паук", "Железный человек", "Тор", "Капитан Америка", "Халк", "Чёрная вдова", "Доктор Стрэндж", "Чёрная пантера",
                "Локи", "Ванда", "Звёздный Лорд", "Дэдпул", "Антмен", "Соколиный глаз", "Капитан Марвел", "Шан-Чи", "Веном",
                "Танос", "Гамора", "Грут", "Ракета", "Дракс", "Небула", "Мантис", "Вижн", "Сокол", "Зимний Солдат",
                "Алая Ведьма", "Ртуть", "Ник Фьюри", "Альтрон", "Хела", "Мистерио", "Зелёный Гоблин", "Доктор Октавиус", "Сорвиголова",
                "Каратель", "Джессика Джонс", "Люк Кейдж", "Железный Кулак", "Профессор Икс", "Магнето", "Росомаха", "Циклоп",
                "Шторм", "Джин Грей", "Зверь", "Гамбит", "Роуг", "Ночной Змей", "Колосс", "Китти Прайд", "Кейбл", "Домино",
                "Блэйд", "Морбиус", "Призрачный гонщик", "Лунный рыцарь", "Вечные", "Один", "Электра", "Кингпин", "Карнаж", "Зорро"
            ],
            ("DC персонажи", "🦇"): [
                "Бэтмен", "Супермен", "Чудо-женщина", "Флэш", "Аквамен", "Джокер", "Харли Квинн", "Лекс Лютор", "Зелёная стрела",
                "Киборг", "Шазам", "Ядовитый Плющ", "Пингвин", "Риддлер", "Найтвинг", "Зелёный фонарь", "Женщина-кошка", "Бэйн",
                "Пугало", "Двуликий", "Детстроук", "Лобо", "Черный Адам", "Миротворец", "Кровавый спорт", "Король Акул",
                "Синий Жук", "Константин", "Болотная тварь", "Затанна", "Обратный Флэш", "Генерал Зод", "Дарксайд", "Степной Волк",
                "Марсианский охотник", "Старфаер", "Бистбой", "Рэйвен", "Робин", "Бэтгёрл", "Супергёрл", "Атом", "Человек-ястреб",
                "Орлица", "Черная Канарейка", "Доктор Фэйт", "Песочный человек", "Люцифер", "Роршах", "Доктор Манхэттен", "Комедиант",
                "Озимандия", "Шелковый призрак", "Ночная сова", "Бизарро", "Брейниак", "Думсдэй", "Глиноликий", "Виктор Зсасз", "Киллер Фрост"
            ],
            ("Известные люди", "🌟"): [
                "Илон Маск", "Билл Гейтс", "Стив Джобс", "Альберт Эйнштейн", "Леонардо да Винчи", "Наполеон", "Моцарт", "Майкл Джексон",
                "Мухаммед Али", "Криштиану Роналду", "Лионель Месси", "Опра Уинфри", "Стивен Хокинг", "Чарли Чаплин", "Мэрилин Монро",
                "Юрий Гагарин", "Уинстон Черчилль", "Королева Елизавета II", "Дональд Трамп", "Барак Обама", "Владимир Путин",
                "Павел Дуров", "Марк Цукерберг", "Джефф Безос", "Генри Форд", "Томас Эдисон", "Никола Тесла", "Исаак Ньютон",
                "Чарльз Дарвин", "Зигмунд Фрейд", "Пабло Пикассо", "Винсент Ван Гог", "Вильям Шекспир", "Александр Пушкин",
                "Лев Толстой", "Федор Достоевский", "Джон Леннон", "Фредди Меркьюри", "Анджелина Джоли", "Брэд Питт",
                "Леонардо Ди Каприо", "Том Круз", "Джонни Депп", "Киану Ривз", "Бенедикт Камбербэтч", "Мадонна", "Бейонсе", "Тейлор Свифт",
                "Адель", "Эминем", "Канье Уэст", "Рианна", "Джастин Бибер", "Леди Гага", "Моргенштерн", "Хабиб Нурмагомедов",
                "Конор Макгрегор", "Майк Тайсон", "Пеле", "Марадона", "Майкл Джордан", "Коби Брайант", "Льюис Хэмилтон", "Шумахер"
            ],
            ("Футбольные команды", "⚽"): [
                "Реал Мадрид", "Барселона", "Манчестер Сити", "Манчестер Юнайтед", "Ливерпуль", "Челси", "Арсенал", "ПСЖ",
                "Бавария", "Ювентус", "Милан", "Интер", "Атлетико Мадрид", "Боруссия Дортмунд", "Аякс", "Зенит", "Спартак",
                "ЦСКА", "Локомотив", "Краснодар", "Динамо Киев", "Шахтер", "Бенфика", "Порту", "Спортинг", "Наполи", "Рома",
                "Лацио", "Фиорентина", "Байер", "РБ Лейпциг", "Тоттенхэм", "Ньюкасл", "Вест Хэм", "Астон Вилла", "Севилья",
                "Вильярреал", "Валенсия", "Лион", "Марсель", "Монако", "Лилль", "Галатасарай", "Фенербахче", "Бешикташ",
                "Фламенго", "Палмейрас", "Бока Хуниорс", "Ривер Плейт", "Аль-Наср", "Аль-Хиляль", "Интер Майами", "Лос-Анджелес Гэлакси",
                "Селтик", "Рейнджерс", "Фейеноорд", "ПСВ", "Брюгге", "Андерлехт", "Олимпиакос", "Панатинаикос", "Црвена Звезда", "Партизан"
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
