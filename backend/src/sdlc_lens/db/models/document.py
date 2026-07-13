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
    # Normalised id head of this document (norm_id(id_head(doc_id))), for reference
    # resolution across id forms (sequential / hyphenated / v3 ULID). None for singletons.
    ref_id: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    # Normalised, comma-joined dependency ids (from a `Depends on` field).
    depends_on: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Normalised, comma-joined prior ids (from a v3 migration `Aliases` field).
    aliases: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)
    # Parser/schema epoch that produced this row's derived fields (doc_type, status,
    # epic/story, depends_on, aliases). Bumped in sync_engine.PARSER_EPOCH whenever the
    # parsing/inference/canonicalisation logic changes; a row below the current epoch is
    # re-parsed on the next sync even if its content hash is unchanged. 0 = pre-epoch.
    parser_epoch: Mapped[int | None] = mapped_column(nullable=True, default=0)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    # sha256 of the raw bytes. Ours, not git's - used to skip a byte-unchanged file.
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    # The git blob SHA-1 of the raw bytes: sha1("blob {len}\0" + bytes). This is what
    # GitHub's Trees API reports per path, so it is what an incremental sync diffs
    # against to decide which blobs to fetch. Distinct from file_hash (sha256) and not
    # derivable from `content` (already-decoded text).
    #
    # NULL = unknown, i.e. a row written before migration 012. Such a row is backfilled
    # by sync_engine's `needs_blob_sha_backfill` clause, which makes it ineligible for
    # the byte-unchanged skip so it gets rewritten once. Note the backfill comes from
    # THAT clause, not from the tarball merely having the bytes: without it an unchanged
    # file is skipped and the NULL persists forever (RFC-01KXARHK, D1).
    blob_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    synced_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())
