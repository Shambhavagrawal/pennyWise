from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings

app = FastAPI(
    title="API",
    debug=settings.DEBUG,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
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


# Health check at root (nginx routes /health directly to backend)
@app.get("/health")
async def health():
    return {"status": "healthy"}
