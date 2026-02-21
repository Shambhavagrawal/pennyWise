from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.challenge import router as challenge_router
from src.core.config import settings

app = FastAPI(
    title="PennyWise API",
    description="Automated retirement savings through expense-based micro-investments",
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
    allow_headers=["Authorization", "Content-Type"],
)

# All feature routes go under /api — matches nginx routing in production
api_router = APIRouter(prefix="/api")
# Example: api_router.include_router(users.router)
app.include_router(api_router)

# Challenge routes (no /api prefix — spec requires /blackrock/challenge/v1/...)
app.include_router(challenge_router)


# Health check at root (nginx routes /health directly to backend)
@app.get("/health")
async def health():
    return {"status": "healthy"}
