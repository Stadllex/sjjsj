from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    emoji = Column(String(10), default="🌍")
    created_at = Column(DateTime, default=datetime.utcnow)

    words = relationship("Word", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category id={self.id} name={self.name!r}>"


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    word = Column(String(200), nullable=False)
    image_id = Column(String(200), nullable=True)  # Telegram file_id
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="words")

    def __repr__(self):
        return f"<Word id={self.id} word={self.word!r}>"
