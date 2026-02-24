"""SQLAlchemy models — Full schema defined in docs/05_database_schema.md."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Surah(Base):
    __tablename__ = "surahs"

    id = Column(Integer, primary_key=True)
    name_arabic = Column(String(100), nullable=False)
    name_english = Column(String(100), nullable=False)
    name_transliteration = Column(String(100), nullable=False)
    revelation_type = Column(String(10), nullable=False)  # meccan / medinan
    verse_count = Column(Integer, nullable=False)
    juz_start = Column(Integer)
    page_start = Column(Integer)

    verses = relationship("Verse", back_populates="surah")


class Verse(Base):
    __tablename__ = "verses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    surah_id = Column(Integer, ForeignKey("surahs.id"), nullable=False)
    verse_number = Column(Integer, nullable=False)
    text_uthmani = Column(Text, nullable=False)
    text_simple = Column(Text, nullable=False)
    text_clean = Column(Text, nullable=False)
    juz = Column(Integer)
    hizb = Column(Integer)
    page = Column(Integer)

    surah = relationship("Surah", back_populates="verses")


class Discovery(Base):
    __tablename__ = "discoveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    confidence_tier = Column(String(10), nullable=False, default="tier_0")
    evidence = Column(JSONB, default={})
    objections = Column(JSONB, default=[])
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
