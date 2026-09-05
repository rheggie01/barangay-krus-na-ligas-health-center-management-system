from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings


def get_cors_origins() -> list[str]:
    origins = {
        settings.FRONTEND_URL.strip(),
    }

    origins.update(
        origin.strip()
        for origin in settings.BACKEND_CORS_ORIGINS.split(",")
        if origin.strip()
    )

    return sorted(origins)


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# API ROUTES
# =========================================================

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": (
            "Barangay Health Center "
            "website backend is running"
        ),
        "environment": settings.APP_ENV,
    }
