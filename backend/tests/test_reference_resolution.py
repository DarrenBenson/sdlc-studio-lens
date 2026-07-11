"""CR-01KX8Y2G: reference resolution across id forms + depends-on + aliases."""

import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.documents import get_related_documents
from sdlc_lens.utils.sdlc_ids import id_head, norm_id


async def _project(session: AsyncSession) -> Project:
    p = Project(slug="ref", name="Ref", sdlc_path="/tmp/ref")
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


def _doc(project_id, doc_type, doc_id, *, epic=None, story=None, depends_on=None, aliases=None):
    return Document(
        project_id=project_id,
        doc_type=doc_type,
        doc_id=doc_id,
        title=doc_id,
        status="Done",
        epic=norm_id(epic) if epic else None,
        story=norm_id(story) if story else None,
        ref_id=norm_id(id_head(doc_id)),
        depends_on=depends_on,
        aliases=aliases,
        content=f"# {doc_id}",
        file_path=f"{doc_type}s/{doc_id}.md",
        file_hash=f"{doc_id:<64}"[:64],
        synced_at=datetime.datetime.now(tz=datetime.UTC),
    )


async def test_ulid_epic_child_resolves(session: AsyncSession) -> None:
    p = await _project(session)
    epic = _doc(p.id, "epic", "EP-01KX8AAA-auth")
    story = _doc(p.id, "story", "US-01KX8BBB-login", epic="EP-01KX8AAA")
    session.add_all([epic, story])
    await session.commit()

    parents, children, _dep, _dependents = await get_related_documents(session, p.id, epic)
    assert [c.doc_id for c in children] == ["US-01KX8BBB-login"]
    parents2, _c, _d, _dd = await get_related_documents(session, p.id, story)
    assert [pp.doc_id for pp in parents2] == ["EP-01KX8AAA-auth"]


async def test_hyphenated_reference_resolves(session: AsyncSession) -> None:
    p = await _project(session)
    epic = _doc(p.id, "epic", "EP0007-sync")
    # child references the hyphenated display form "EP-0007"
    story = _doc(p.id, "story", "US0028-schema", epic="EP-0007")
    session.add_all([epic, story])
    await session.commit()

    _p, children, _d, _dd = await get_related_documents(session, p.id, epic)
    assert [c.doc_id for c in children] == ["US0028-schema"]


async def test_depends_on_and_dependents(session: AsyncSession) -> None:
    p = await _project(session)
    a = _doc(p.id, "cr", "CR-01KX8A11-foundation")
    b = _doc(p.id, "cr", "CR-01KX8B22-builds-on-a", depends_on=norm_id("CR-01KX8A11"))
    session.add_all([a, b])
    await session.commit()

    _p, _c, depends_on, _dd = await get_related_documents(session, p.id, b)
    assert [d.doc_id for d in depends_on] == ["CR-01KX8A11-foundation"]
    _p2, _c2, _d2, dependents = await get_related_documents(session, p.id, a)
    assert [d.doc_id for d in dependents] == ["CR-01KX8B22-builds-on-a"]


async def test_alias_reference_resolves(session: AsyncSession) -> None:
    p = await _project(session)
    # renumbered story keeps its old sequential id as an alias
    story = _doc(p.id, "story", "US-01KX8CCC-renamed", aliases=norm_id("US0001"))
    plan = _doc(p.id, "plan", "PL0001-plan", story="US0001")  # references the OLD id
    session.add_all([story, plan])
    await session.commit()

    parents, _c, _d, _dd = await get_related_documents(session, p.id, plan)
    assert [pp.doc_id for pp in parents] == ["US-01KX8CCC-renamed"]


async def test_self_reference_not_linked(session: AsyncSession) -> None:
    """A document naming its own id is never its own parent/child/dependency."""
    p = await _project(session)
    # epic that (erroneously) names itself as epic, and depends on itself
    doc = _doc(p.id, "epic", "EP0001-self", epic="EP0001", depends_on=norm_id("EP0001"))
    session.add(doc)
    await session.commit()

    parents, children, depends_on, dependents = await get_related_documents(session, p.id, doc)
    assert parents == []
    assert children == []
    assert depends_on == []
    assert dependents == []
