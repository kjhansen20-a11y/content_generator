from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, reload_settings
from app.database import init_db
from app.routers import admin, auth, generation, knowledge, oauth, planning, profile, public_pages, publishing
from app.seed.seed_admin import seed_platform_admin
from app.seed.seed_prompts import seed_prompts

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    reload_settings()
    init_db()
    seed_prompts()
    seed_platform_admin(get_settings().platform_admin_email)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(public_pages.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(planning.router, prefix="/api/v1")
app.include_router(oauth.router)
app.include_router(generation.router, prefix="/api/v1")
app.include_router(publishing.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
