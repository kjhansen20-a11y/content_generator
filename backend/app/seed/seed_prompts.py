"""Seed prompt templates from backend/prompts/*.md files."""

from pathlib import Path

from sqlmodel import Session, select

from app.database import engine
from app.models.prompts import PromptTemplate, PromptVersion

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"

PROMPT_DEFINITIONS: dict[str, dict[str, str]] = {
    "base": {"kind": "system", "description": "Base system prompt and JSON contract"},
    "post_professional": {"kind": "post_type", "description": "Professional/educational post style"},
    "post_personal": {"kind": "post_type", "description": "Personal/founder post style"},
    "platform_linkedin": {"kind": "platform", "description": "LinkedIn platform rules"},
    "platform_facebook": {"kind": "platform", "description": "Facebook platform rules"},
    "platform_instagram": {"kind": "platform", "description": "Instagram platform rules"},
    "quality_check": {"kind": "quality", "description": "Quality and compliance review"},
    "marketing_plan": {"kind": "planning", "description": "AI marketing plan generation guide"},
    "post_brief": {"kind": "generation", "description": "Auto-brief for post generation"},
    "post_revise": {"kind": "generation", "description": "Revise draft from quality feedback"},
    "company_profile_scrape": {
        "kind": "profile",
        "description": "Extract company profile fields from website content",
    },
}


def seed_prompts() -> None:
    with Session(engine) as session:
        for key, meta in PROMPT_DEFINITIONS.items():
            path = PROMPTS_DIR / f"{key}.md"
            if not path.exists():
                continue

            body = path.read_text(encoding="utf-8").strip()
            template = session.exec(select(PromptTemplate).where(PromptTemplate.key == key)).first()
            if template is None:
                template = PromptTemplate(
                    key=key,
                    kind=meta["kind"],
                    description=meta["description"],
                )
                session.add(template)
                session.flush()

            active = session.exec(
                select(PromptVersion).where(
                    PromptVersion.template_id == template.id,
                    PromptVersion.is_active == True,  # noqa: E712
                )
            ).first()

            if active is None:
                version = PromptVersion(template_id=template.id, version=1, body=body, is_active=True)
                session.add(version)
            elif active.body != body:
                active.is_active = False
                session.add(active)
                next_version = (
                    session.exec(
                        select(PromptVersion)
                        .where(PromptVersion.template_id == template.id)
                        .order_by(PromptVersion.version.desc())
                    ).first()
                )
                version_num = (next_version.version if next_version else 0) + 1
                session.add(
                    PromptVersion(
                        template_id=template.id,
                        version=version_num,
                        body=body,
                        is_active=True,
                    )
                )

        session.commit()
