from dataclasses import dataclass

from sqlmodel import Session, select

from app.models.content import GenerateMode, Platform, PostType
from app.models.profile import BrandProfile, CompanyProfile
from app.models.tenancy import Company
from app.schemas.content import GeneratePostRequest
from app.services.files import get_uploaded_file
from app.services.knowledge import retrieve_knowledge_context, tone_examples_context_block
from app.services.post_language import build_post_language_instruction, detect_output_language


POST_TYPE_KEYS = {
    PostType.professional: "post_professional",
    PostType.personal: "post_personal",
}

PLATFORM_KEYS = {
    Platform.linkedin: "platform_linkedin",
    Platform.facebook: "platform_facebook",
    Platform.instagram: "platform_instagram",
}


@dataclass
class ResolvedPostContext:
    platform: Platform
    post_type: PostType
    content_idea: str
    include_planning: bool
    language_source: str = ""
    output_language: str = "English"
    pillar_name: str | None = None
    pillar_description: str | None = None
    slot_label: str | None = None


def get_active_prompt_body(session: Session, key: str) -> str:
    from app.models.prompts import PromptTemplate, PromptVersion

    template = session.exec(select(PromptTemplate).where(PromptTemplate.key == key)).first()
    if template is None:
        raise ValueError(f"Prompt template not found: {key}")

    version = session.exec(
        select(PromptVersion).where(
            PromptVersion.template_id == template.id,
            PromptVersion.is_active == True,  # noqa: E712
        )
    ).first()
    if version is None:
        raise ValueError(f"No active prompt version for: {key}")
    return version.body


def get_active_prompt_version_id(session: Session, key: str) -> int | None:
    from app.models.prompts import PromptTemplate, PromptVersion

    template = session.exec(select(PromptTemplate).where(PromptTemplate.key == key)).first()
    if template is None:
        return None
    version = session.exec(
        select(PromptVersion).where(
            PromptVersion.template_id == template.id,
            PromptVersion.is_active == True,  # noqa: E712
        )
    ).first()
    return version.id if version else None


def build_system_prompt(session: Session, post_type: PostType, platform: Platform) -> str:
    parts = [
        get_active_prompt_body(session, "base"),
        get_active_prompt_body(session, POST_TYPE_KEYS[post_type]),
        get_active_prompt_body(session, PLATFORM_KEYS[platform]),
    ]
    return "\n\n".join(parts)


def build_brief_user_prompt(session: Session, company: Company, ctx: ResolvedPostContext) -> str:
    sections = _company_brand_sections(session, company, ctx, include_planning=ctx.include_planning)
    if ctx.slot_label:
        sections.append(f"Scheduled slot: {ctx.slot_label}")
    if ctx.pillar_name:
        sections.append(f"Content pillar: {ctx.pillar_name}")
        if ctx.pillar_description:
            sections.append(f"Pillar focus: {ctx.pillar_description}")
    if ctx.content_idea.strip():
        sections.append(f"User direction: {ctx.content_idea.strip()}")
    sections.append(
        f"Platform: {ctx.platform.value}. Post type: {ctx.post_type.value}. "
        "Write a creative brief for one social post."
    )
    sections.append(build_post_language_instruction(ctx.output_language, ctx.language_source))
    return "\n\n".join(sections)


def build_user_prompt(
    session: Session,
    company: Company,
    request: GeneratePostRequest,
    ctx: ResolvedPostContext,
) -> str:
    sections = _company_brand_sections(session, company, ctx, include_planning=ctx.include_planning)

    if ctx.slot_label:
        sections.append(f"Scheduled slot: {ctx.slot_label}")
    if ctx.pillar_name:
        sections.append(f"Content pillar: {ctx.pillar_name}")
        if ctx.pillar_description:
            sections.append(f"Pillar focus: {ctx.pillar_description}")

    sections.append(f"Platform: {ctx.platform.value}")
    sections.append(f"Post type: {ctx.post_type.value}")
    sections.append(f"Content brief: {ctx.content_idea.strip()}")

    if request.keywords:
        sections.append(f"Keywords: {request.keywords.strip()}")
    if request.image_file_id:
        try:
            image_file = get_uploaded_file(session, company.id, request.image_file_id)
            sections.append(
                f"An image will be published with this post ({image_file.original_filename}). "
                "Write copy that complements the visual. Set alt_text to an accessibility description."
            )
            if request.image_description:
                sections.append(f"Image description: {request.image_description.strip()}")
        except Exception:
            pass
    elif request.image_notes:
        sections.append(f"Image notes: {request.image_notes.strip()}")

    sections.append(
        "Do not invent product features or claims not supported by the company context above. "
        "Write one post draft. Return JSON matching the required schema. "
        f'Set platform to "{ctx.platform.value}" and post_type to "{ctx.post_type.value}".'
    )
    sections.append(build_post_language_instruction(ctx.output_language, ctx.language_source))
    return "\n\n".join(sections)


def _company_brand_sections(
    session: Session,
    company: Company,
    ctx: ResolvedPostContext,
    *,
    include_planning: bool,
) -> list[str]:
    company_profile = session.exec(
        select(CompanyProfile).where(CompanyProfile.company_id == company.id)
    ).first()
    brand_profile = session.exec(
        select(BrandProfile).where(BrandProfile.company_id == company.id)
    ).first()

    sections: list[str] = [f"Company name: {company.name}"]

    if company_profile:
        if company_profile.description:
            sections.append(f"Company description: {company_profile.description}")
        if company_profile.industry:
            sections.append(f"Industry: {company_profile.industry}")
        if company_profile.target_audience:
            sections.append(f"Target audience: {company_profile.target_audience}")
        if company_profile.products_services:
            sections.append(f"Products/services: {company_profile.products_services}")

    if brand_profile:
        if brand_profile.tone_of_voice:
            sections.append(f"Tone of voice: {brand_profile.tone_of_voice}")
        if brand_profile.brand_voice_description:
            sections.append(f"Brand voice: {brand_profile.brand_voice_description}")
        if brand_profile.do_use:
            sections.append(f"Do use: {brand_profile.do_use}")
        if brand_profile.dont_use:
            sections.append(f"Don't use: {brand_profile.dont_use}")
        if brand_profile.brand_keywords:
            sections.append(f"Brand keywords: {brand_profile.brand_keywords}")

    tone_examples = tone_examples_context_block(session, company.id)
    if tone_examples:
        sections.append(
            "Previous posts (match this voice, tone, and style when writing new posts):\n"
            + tone_examples
        )

    query_parts = [ctx.content_idea or "", ctx.pillar_name or "", ctx.pillar_description or ""]
    knowledge = retrieve_knowledge_context(
        session, company.id, query=" ".join(query_parts), max_chars=4000
    )
    if knowledge:
        sections.append(f"Relevant company knowledge:\n{knowledge}")

    if include_planning:
        from app.services.planning import planning_context_block

        planning = planning_context_block(session, company.id)
        if planning:
            sections.append(f"Marketing plan & posting strategy:\n{planning}")

    return sections
