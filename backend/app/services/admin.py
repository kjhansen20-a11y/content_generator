from sqlmodel import Session, select, func

from app.models.auth import User
from app.models.content import ContentCalendarItem, GeneratedPost
from app.models.prompts import PromptTemplate, PromptVersion
from app.models.publishing import PublishingJob
from app.models.tenancy import Company, CompanyUser
from app.models.usage import UsageEvent
from app.schemas.admin import (
    AdminCompanyRead,
    AdminJobRead,
    AdminPromptRead,
    AdminUsageSummary,
    AdminUserRead,
)


def list_admin_companies(session: Session) -> list[AdminCompanyRead]:
    companies = session.exec(select(Company).order_by(Company.created_at.desc())).all()
    result: list[AdminCompanyRead] = []

    for company in companies:
        member_count = session.exec(
            select(func.count()).select_from(CompanyUser).where(CompanyUser.company_id == company.id)
        ).one()
        post_count = session.exec(
            select(func.count())
            .select_from(GeneratedPost)
            .where(GeneratedPost.company_id == company.id)
        ).one()
        usage_row = session.exec(
            select(
                func.coalesce(func.sum(UsageEvent.total_tokens), 0),
                func.coalesce(func.sum(UsageEvent.estimated_cost_usd), 0.0),
            ).where(UsageEvent.company_id == company.id)
        ).one()

        result.append(
            AdminCompanyRead(
                id=company.id,
                name=company.name,
                slug=company.slug,
                member_count=member_count,
                post_count=post_count,
                total_tokens=int(usage_row[0]),
                total_cost_usd=float(usage_row[1]),
                created_at=company.created_at,
            )
        )
    return result


def get_usage_summary(session: Session) -> AdminUsageSummary:
    companies = list_admin_companies(session)
    total_events = session.exec(select(func.count()).select_from(UsageEvent)).one()
    totals = session.exec(
        select(
            func.coalesce(func.sum(UsageEvent.total_tokens), 0),
            func.coalesce(func.sum(UsageEvent.estimated_cost_usd), 0.0),
        )
    ).one()
    return AdminUsageSummary(
        total_events=total_events,
        total_tokens=int(totals[0]),
        total_cost_usd=float(totals[1]),
        by_company=companies,
    )


def list_admin_users(session: Session) -> list[AdminUserRead]:
    users = session.exec(select(User).order_by(User.created_at.desc())).all()
    result: list[AdminUserRead] = []
    for user in users:
        company_count = session.exec(
            select(func.count()).select_from(CompanyUser).where(CompanyUser.user_id == user.id)
        ).one()
        result.append(
            AdminUserRead(
                id=user.id,
                email=user.email,
                is_platform_admin=user.is_platform_admin,
                company_count=company_count,
                created_at=user.created_at,
            )
        )
    return result


def list_admin_prompts(session: Session) -> list[AdminPromptRead]:
    templates = session.exec(select(PromptTemplate).order_by(PromptTemplate.key)).all()
    result: list[AdminPromptRead] = []
    for template in templates:
        active = session.exec(
            select(PromptVersion).where(
                PromptVersion.template_id == template.id,
                PromptVersion.is_active == True,  # noqa: E712
            )
        ).first()
        body_preview = None
        if active:
            body_preview = active.body[:300] + ("…" if len(active.body) > 300 else "")
        result.append(
            AdminPromptRead(
                id=template.id,
                key=template.key,
                kind=template.kind,
                description=template.description,
                active_version=active.version if active else None,
                active_version_id=active.id if active else None,
                body_preview=body_preview,
            )
        )
    return result


def list_admin_jobs(session: Session, limit: int = 100) -> list[AdminJobRead]:
    rows = session.exec(
        select(PublishingJob, Company, ContentCalendarItem)
        .join(Company, Company.id == PublishingJob.company_id)
        .join(ContentCalendarItem, ContentCalendarItem.id == PublishingJob.calendar_item_id)
        .order_by(PublishingJob.created_at.desc())
        .limit(limit)
    ).all()
    return [
        AdminJobRead(
            id=job.id,
            company_id=company.id,
            company_name=company.name,
            calendar_item_id=job.calendar_item_id,
            status=job.status.value,
            platform=item.platform.value,
            hook_preview=item.hook_preview,
            external_post_id=job.external_post_id,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )
        for job, company, item in rows
    ]
