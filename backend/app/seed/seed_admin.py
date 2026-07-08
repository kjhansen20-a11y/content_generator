from sqlmodel import Session, select

from app.database import engine
from app.models.auth import User


def seed_platform_admin(email: str | None) -> None:
    if not email or not email.strip():
        return

    normalized = email.strip().lower()
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == normalized)).first()
        if user is None:
            return
        if not user.is_platform_admin:
            user.is_platform_admin = True
            session.add(user)
            session.commit()
