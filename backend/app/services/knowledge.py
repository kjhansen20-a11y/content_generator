from sqlmodel import Session, select

from app.models.knowledge import CompanyKnowledge
from app.schemas.knowledge import KnowledgeCreate, KnowledgeRead


def list_knowledge(session: Session, company_id: int) -> list[KnowledgeRead]:
    rows = session.exec(
        select(CompanyKnowledge)
        .where(CompanyKnowledge.company_id == company_id)
        .order_by(CompanyKnowledge.created_at.desc())
    ).all()
    return [KnowledgeRead.model_validate(row) for row in rows]


def create_knowledge(session: Session, company_id: int, payload: KnowledgeCreate) -> KnowledgeRead:
    entry = CompanyKnowledge(
        company_id=company_id,
        title=payload.title.strip(),
        content=payload.content.strip(),
        source="manual",
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return KnowledgeRead.model_validate(entry)


def delete_knowledge(session: Session, company_id: int, entry_id: int) -> None:
    entry = session.get(CompanyKnowledge, entry_id)
    if entry is None or entry.company_id != company_id:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge entry not found")
    session.delete(entry)
    session.commit()


def knowledge_context_block(session: Session, company_id: int, max_chars: int = 8000) -> str | None:
    return retrieve_knowledge_context(session, company_id, query=None, max_chars=max_chars)


def retrieve_knowledge_context(
    session: Session,
    company_id: int,
    *,
    query: str | None = None,
    max_chars: int = 4000,
) -> str | None:
    entries = list(
        session.exec(
            select(CompanyKnowledge)
            .where(CompanyKnowledge.company_id == company_id)
            .order_by(CompanyKnowledge.created_at.desc())
        ).all()
    )
    if not entries:
        return None

    if query and query.strip():
        terms = [t.lower() for t in query.split() if len(t) > 2]
        scored: list[tuple[int, CompanyKnowledge]] = []
        for entry in entries:
            haystack = f"{entry.title} {entry.content}".lower()
            score = sum(1 for term in terms if term in haystack)
            scored.append((score, entry))
        scored.sort(key=lambda x: (-x[0], -x[1].created_at.timestamp()))
        ordered = [e for _, e in scored]
    else:
        ordered = entries

    parts: list[str] = []
    total = 0
    for entry in ordered:
        chunk = f"### {entry.title}\n{entry.content.strip()}"
        if total + len(chunk) > max_chars:
            remaining = max_chars - total
            if remaining > 100:
                parts.append(chunk[:remaining] + "…")
            break
        parts.append(chunk)
        total += len(chunk)
    return "\n\n".join(parts) if parts else None
