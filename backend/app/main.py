from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database import init_db, engine
from .routers import auth
from . import models
from .routers import auth, scans, questionnaire, derm_locator

# ... then


# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup/shutdown events."""
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📊 Database crated")
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    yield

    logger.info("👋 Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
    },
)


# Custom OpenAPI to fix Swagger UI authorization
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Fix security scheme for Swagger UI
    if "components" in openapi_schema:
        if "securitySchemes" in openapi_schema["components"]:
            # Update OAuth2 scheme to not require client credentials
            if (
                "OAuth2PasswordBearer"
                in openapi_schema["components"]["securitySchemes"]
            ):
                scheme = openapi_schema["components"]["securitySchemes"][
                    "OAuth2PasswordBearer"
                ]
                # Remove client credentials requirement
                scheme["x-client-credentials"] = False
                # Ensure it's password flow only
                scheme["flow"] = "password"

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ============ ROUTERS ============

app.include_router(auth.router)
app.include_router(scans.router)
app.include_router(questionnaire.router)
app.include_router(derm_locator.router)
# ============ HEALTH CHECKS ============


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }


@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {str(e)}",
        )
    return {"status": "ready"}


# ============ ERROR HANDLERS ============


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "status_code": 500},
    )
