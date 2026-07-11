"""Backfill ref_id for documents that predate migration 007's column addition.

Migration 007 added ``ref_id`` as a nullable column with no backfill, so every
document synced before it landed carries ``ref_id = NULL``. Reference resolution
(parent breadcrumbs, depends-on, dependents) now matches on ``ref_id``, so those
legacy rows resolve to nothing until repopulated. This migration performs the
one-off backfill so existing deployments heal immediately on upgrade rather than
waiting for the next sync of each file.

Only ``ref_id`` is recomputed here; epic/story/depends_on/aliases are left to the
next sync (see ``sync_engine`` reparsing rows whose ``ref_id`` is NULL). ``ref_id``
is what unblocks resolution for legacy sequential ids.

Revision ID: 009
Revises: 008
Create Date: 2026-07-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from sdlc_lens.utils.sdlc_ids import id_head, norm_id

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    # Only touch rows still missing a ref_id, so the migration is idempotent and
    # never overwrites a value that a sync has already computed.
    rows = bind.execute(
        sa.text("SELECT id, doc_id FROM documents WHERE ref_id IS NULL")
    ).fetchall()
    for row in rows:
        ref_id = norm_id(id_head(row.doc_id))
        if ref_id is None:
            # Singletons (prd, trd, ...) have no artefact id head - leave NULL.
            continue
        bind.execute(
            sa.text("UPDATE documents SET ref_id = :ref_id WHERE id = :id"),
            {"ref_id": ref_id, "id": row.id},
        )


def downgrade() -> None:
    # No-op: the ref_id column itself is removed by 007's downgrade.
    pass
