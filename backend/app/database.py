from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from sqlalchemy import text

from app.config import BACKEND_DIR, get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)


def _sqlite_migrations() -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.connect() as conn:
        cols = conn.execute(text("PRAGMA table_info(generated_posts)")).fetchall()
        col_names = {row[1] for row in cols}
        if "image_file_id" not in col_names:
            conn.execute(text("ALTER TABLE generated_posts ADD COLUMN image_file_id INTEGER"))
            conn.commit()

        cal_cols = conn.execute(text("PRAGMA table_info(content_calendar_items)")).fetchall()
        cal_col_names = {row[1] for row in cal_cols}
        if "scheduled_time" not in cal_col_names:
            conn.execute(text("ALTER TABLE content_calendar_items ADD COLUMN scheduled_time VARCHAR(5)"))
            conn.commit()
        if "posting_rule_id" not in cal_col_names:
            conn.execute(text("ALTER TABLE content_calendar_items ADD COLUMN posting_rule_id INTEGER"))
            conn.commit()
        if "content_pillar_id" not in cal_col_names:
            conn.execute(text("ALTER TABLE content_calendar_items ADD COLUMN content_pillar_id INTEGER"))
            conn.commit()

        rule_cols = conn.execute(text("PRAGMA table_info(posting_rules)")).fetchall()
        rule_col_names = {row[1] for row in rule_cols}
        if "content_pillar_id" not in rule_col_names:
            conn.execute(text("ALTER TABLE posting_rules ADD COLUMN content_pillar_id INTEGER"))
            conn.commit()

        acct_cols = conn.execute(text("PRAGMA table_info(connected_accounts)")).fetchall()
        acct_col_names = {row[1] for row in acct_cols}
        oauth_columns = {
            "external_account_id": "VARCHAR(255)",
            "account_type": "VARCHAR(32)",
            "access_token_encrypted": "TEXT",
            "refresh_token_encrypted": "TEXT",
            "token_expires_at": "DATETIME",
            "scopes": "VARCHAR(1000)",
            "connected_by_user_id": "INTEGER",
            "updated_at": "DATETIME",
        }
        for col, col_type in oauth_columns.items():
            if col not in acct_col_names:
                conn.execute(text(f"ALTER TABLE connected_accounts ADD COLUMN {col} {col_type}"))
                conn.commit()


def init_db() -> None:
    # Import models so SQLModel registers all tables before create_all.
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    uploads_path = BACKEND_DIR / settings.uploads_dir
    uploads_path.mkdir(parents=True, exist_ok=True)
    _sqlite_migrations()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
