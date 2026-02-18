"""SQLAlchemy Document model."""

import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from sdlc_lens.db.models.base import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("project_id", "file_path"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    doc_type: Mapped[str] = mapped_column(String(20), nullable=False)
    doc_id: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(10), nullable=True)
    story_points: Mapped[int | None] = mapped_column(nullable=True)
    epic: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    story: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    metadata_json: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    synced_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())
