from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class JournalRankCache(Base):
    __tablename__ = "journal_rank_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lookup_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    publication_name: Mapped[str | None] = mapped_column(String(512))
    normalized_name: Mapped[str | None] = mapped_column(String(512), index=True)
    issn: Mapped[str | None] = mapped_column(String(32), index=True)
    source: Mapped[str] = mapped_column(String(64), default="easyscholar", nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    rank_json: Mapped[str | None] = mapped_column(Text)
    raw_response_json: Mapped[str | None] = mapped_column(Text)
    sci: Mapped[str | None] = mapped_column(String(64))
    cas_zone: Mapped[str | None] = mapped_column(String(128))
    cas_small: Mapped[str | None] = mapped_column(String(128))
    cas_top: Mapped[int | None] = mapped_column(Integer)
    impact_factor: Mapped[float | None] = mapped_column(Float)
    five_year_if: Mapped[float | None] = mapped_column(Float)
    ei: Mapped[int | None] = mapped_column(Integer)
    cscd: Mapped[int | None] = mapped_column(Integer)
    pku_core: Mapped[int | None] = mapped_column(Integer)
    cssci: Mapped[int | None] = mapped_column(Integer)
    esi: Mapped[str | None] = mapped_column(String(128))
    warning: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[str] = mapped_column(String(32), nullable=False)
    expires_at: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(32), nullable=False)


class RankQueryLog(Base):
    __tablename__ = "rank_query_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lookup_key: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    request_type: Mapped[str] = mapped_column(String(32), nullable=False)
    cache_hit: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    upstream_status_code: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False)
