from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, content, emotions, exports, me, moderation, recovery, uxu
from app.core.config import get_settings
from app.db.session import SessionLocal, init_db
from app.services.auth_service import ensure_default_admin
from app.services.content_service import seed_initial_content

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
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
