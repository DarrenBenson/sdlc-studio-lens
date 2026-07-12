"""SQLAlchemy GitHubConnection model (CR-01KXAZX9).

A stored, reusable GitHub credential. The PAT lives here once - encrypted at
rest via ``utils.crypto`` - instead of being duplicated across every project
row, so rotating it is a single edit. ``login`` is the account GitHub resolved
for the token at registration time, and ``last_validated_at`` records when the
token was last confirmed live.
"""

import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from sdlc_lens.db.models.base import Base


class GitHubConnection(Base):
    __tablename__ = "github_connections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    login: Mapped[str] = mapped_column(String(255), nullable=False)
    # Fernet ciphertext (or legacy plaintext when no key is configured).
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    last_validated_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
