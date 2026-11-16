from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, content, emotions, exports, me, moderation, recovery, uxu
from app.core.config import get_settings
from app.db.session import SessionLocal, init_db
from app.services.auth_service import ensure_default_admin
from app.services.content_service import seed_initial_content

settings = get_settings()


def _validate_production_settings() -> None:
    if settings.environment.lower() not in {"prod", "production"}:
        return
    if settings.jwt_secret == "change-me-in-production" or len(settings.jwt_secret) < 32:
        raise RuntimeError("Set MINDEDU_JWT_SECRET to a random value of at least 32 characters in production.")
    if settings.admin_password == "Admin12345" or len(settings.admin_password) < 12:
        raise RuntimeError("Set MINDEDU_ADMIN_PASSWORD to a unique value of at least 12 characters in production.")
    if not settings.cors_origin_list or any("localhost" in origin for origin in settings.cors_origin_list):
        raise RuntimeError("Set MINDEDU_CORS_ORIGINS to the deployed frontend origin in production.")


@asynccontextmanager
async def lifespan(_: FastAPI):
    _validate_production_settings()
    init_db()
    db = SessionLocal()
    try:
        seed_initial_content(db)
        ensure_default_admin(db)
        yield
    finally:
        db.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "ok",
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


app.include_router(auth.router)
app.include_router(recovery.router)
app.include_router(content.router)
app.include_router(emotions.router)
app.include_router(uxu.router)
app.include_router(uxu.coop_router)
app.include_router(me.router)
app.include_router(moderation.router)
app.include_router(admin.router)
app.include_router(exports.router)
