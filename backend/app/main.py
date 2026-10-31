import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.database.session import SessionLocal
from app.routes.clients import router as clients_router
from app.routes.enquiries import router as enquiries_router
from app.routes.auth import router as auth_router
from app.routes.emails import router as emails_router
from app.routes.registrations import router as registrations_router
from app.services.email_sync_service import email_sync_service

logger = logging.getLogger("royal_knot")


async def periodic_email_sync():
    """Background task that checks agency Gmail inbox periodically when IMAP is configured."""
    while True:
        try:
            await asyncio.sleep(settings.EMAIL_POLL_INTERVAL_SECONDS)
            if email_sync_service.is_imap_configured():
                db = SessionLocal()
                try:
                    logger.info("Executing scheduled IMAP mailbox check...")
                    email_sync_service.sync_mailbox(db)
                except Exception as e:
                    logger.error(f"Error during periodic mailbox sync: {e}")
                finally:
                    db.close()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Background email sync loop error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    sync_task = asyncio.create_task(periodic_email_sync())
    yield
    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production-grade backend service for **The Royal Knot** Luxury Wedding Planning Agency "
        "(Jaipur & Udaipur operations). Manages enquiry workflows, real Gmail incoming/outgoing communication, "
        "registration document exchange, and client account activation."
    ),
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Custom validation error handler for client-friendly error messages
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append({
            "field": field,
            "message": err.get("msg"),
            "type": err.get("type")
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Data validation failed. Please check the submitted fields.",
            "errors": errors
        }
    )


# Mount API v1 routers
app.include_router(clients_router, prefix=settings.API_V1_STR)
app.include_router(enquiries_router, prefix=f"{settings.API_V1_STR}/enquiries")
app.include_router(registrations_router, prefix=f"{settings.API_V1_STR}/registrations")
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth")
app.include_router(emails_router, prefix=f"{settings.API_V1_STR}/emails")


# Top-level /health route
@app.get("/health", tags=["System Health"])
def root_health():
    return {
        "service": settings.PROJECT_NAME,
        "status": "operational",
        "version": "1.2.0",
        "agency_email": settings.AGENCY_EMAIL,
        "imap_configured": email_sync_service.is_imap_configured(),
        "api_v1_docs": "/docs"
    }


# Root welcome endpoint
@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "operating_hubs": ["Jaipur", "Udaipur"],
        "agency_email": settings.AGENCY_EMAIL,
        "api_v1_endpoints": {
            "health": f"{settings.API_V1_STR}/health",
            "enquiries": f"{settings.API_V1_STR}/enquiries",
            "clients": f"{settings.API_V1_STR}/clients",
            "emails": f"{settings.API_V1_STR}/emails",
            "auth": f"{settings.API_V1_STR}/auth",
            "documentation": "/docs"
        }
    }
