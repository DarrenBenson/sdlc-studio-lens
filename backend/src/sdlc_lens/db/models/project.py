"""SQLAlchemy Project model."""

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sdlc_lens.db.models.base import Base

if TYPE_CHECKING:
    from sdlc_lens.db.models.document import Document


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sdlc_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default="local")
    repo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    repo_branch: Mapped[str] = mapped_column(String(255), nullable=False, server_default="main")
    repo_path: Mapped[str] = mapped_column(
        String(500), nullable=False, server_default="sdlc-studio"
    )
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Optional stored credential (CR-01KXAZX9). When set, its token is used for
    # the sync in preference to the per-project access_token above, so an
    # existing project with its own token keeps working with no migration.
    connection_id: Mapped[int | None] = mapped_column(
        ForeignKey("github_connections.id"), nullable=True, index=True
    )
    sync_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="never_synced"
    )
    sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    profile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # JSON string of {doc_type: [status, ...]} custom vocabulary from .config.yaml.
    status_vocab: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON string of {filename: git blob SHA} for the .config.yaml / .version we last
    # read. An incremental sync gets each config file's blob SHA free in the Trees
    # response, so this lets it detect a config edit at ZERO API cost - and fetch the
    # config blob only when it actually moved. Without it, "nothing changed" would either
    # cost two blob requests every sync, or silently ignore a config change until some
    # unrelated document happened to change. NULL = unknown: re-read the config.
    config_blob_shas: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    documents: Mapped[list["Document"]] = relationship(
        "Document", cascade="all, delete-orphan", passive_deletes=True
    )
