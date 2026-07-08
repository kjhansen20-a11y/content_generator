from sqlmodel import Session, select

from app.models.profile import BrandProfile, CompanyProfile
from app.models.tenancy import Company
from app.schemas.planning import GenerateMarketingPlanRequest
from app.services.knowledge import knowledge_context_block
from app.services.optimal_posting_times import optimal_posting_guidance_block
from app.services.prompt_builder import get_active_prompt_body


def build_marketing_plan_system(session: Session) -> str:
    return get_active_prompt_body(session, "marketing_plan")


def build_marketing_plan_user(
    session: Session,
    company: Company,
    request: GenerateMarketingPlanRequest,
) -> str:
    company_profile = session.exec(
        select(CompanyProfile).where(CompanyProfile.company_id == company.id)
    ).first()
    brand_profile = session.exec(
        select(BrandProfile).where(BrandProfile.company_id == company.id)
    ).first()

    sections: list[str] = [f"Company name: {company.name}"]

    if company_profile:
        if company_profile.industry:
            sections.append(f"Industry: {company_profile.industry}")
        if company_profile.description:
            sections.append(f"Description: {company_profile.description}")
        if company_profile.target_audience:
            sections.append(f"Target audience: {company_profile.target_audience}")
        if company_profile.products_services:
            sections.append(f"Products/services: {company_profile.products_services}")

    if brand_profile:
        if brand_profile.tone_of_voice:
            sections.append(f"Tone of voice: {brand_profile.tone_of_voice}")
        if brand_profile.brand_voice_description:
            sections.append(f"Brand voice: {brand_profile.brand_voice_description}")

    knowledge = knowledge_context_block(session, company.id)
    if knowledge:
        sections.append(f"Company knowledge:\n{knowledge}")

    expectations = (request.plan_expectations or "").strip()
    if expectations:
        sections.append(f"Plan expectations & direction:\n{expectations}")
    keywords = request.keywords.strip()
    if keywords:
        sections.append(f"Keywords / themes: {keywords}")
    if request.focus_areas:
        sections.append(f"Focus areas: {request.focus_areas.strip()}")
    if request.platforms:
        sections.append(f"Target platforms: {', '.join(p.value for p in request.platforms)}")
    if request.plan_name:
        sections.append(f"Suggested plan name: {request.plan_name.strip()}")
    if request.period_weeks:
        sections.append(f"Planning horizon: {request.period_weeks} weeks")
    sections.append(
        f"Target posts per week: {request.posts_per_week} "
        "(TOTAL across all platforms — not per platform)"
    )
    sections.append(
        f"Create EXACTLY {request.posts_per_week} posting_rules — no more, no fewer. "
        "Each rule is one planned post per week, linked to a pillar by name."
    )
    sections.append(optimal_posting_guidance_block(request.platforms))
    sections.append(
        "Design a complete marketing plan with goals, content pillars, and posting rules. "
        "Return JSON matching the required schema."
    )
    return "\n\n".join(sections)


def build_marketing_plan_import_user(
    session: Session,
    company: Company,
    document_text: str,
    plan_name: str | None,
) -> str:
    company_profile = session.exec(
        select(CompanyProfile).where(CompanyProfile.company_id == company.id)
    ).first()
    brand_profile = session.exec(
        select(BrandProfile).where(BrandProfile.company_id == company.id)
    ).first()

    sections: list[str] = [f"Company name: {company.name}"]

    if company_profile and company_profile.industry:
        sections.append(f"Industry: {company_profile.industry}")
    if brand_profile and brand_profile.tone_of_voice:
        sections.append(f"Tone of voice: {brand_profile.tone_of_voice}")

    knowledge = knowledge_context_block(session, company.id)
    if knowledge:
        sections.append(f"Company knowledge:\n{knowledge}")

    if plan_name:
        sections.append(f"Preferred plan name: {plan_name.strip()}")

    sections.append(
        "The user uploaded a marketing plan document. Extract goals, content pillars, and posting rules "
        "from the document below. Preserve specifics from the source where present; infer reasonable "
        "defaults only for clearly missing sections. Return JSON matching the required schema."
    )
    sections.append(optimal_posting_guidance_block())
    sections.append(f"Uploaded document:\n\n{document_text.strip()}")
    return "\n\n".join(sections)
