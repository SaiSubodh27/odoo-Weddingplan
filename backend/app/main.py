from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.routes.clients import router as clients_router
from app.routes.enquiries import router as enquiries_router
from app.routes.auth import router as auth_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production-grade backend service for **The Royal Knot** Luxury Wedding Planning Agency "
        "(Jaipur & Udaipur operations). Manages enquiry workflows, client registration dossiers, "
        "registration document exchange, and client account activation."
    ),
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
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
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth")

# Top-level /health route
@app.get("/health", tags=["System Health"])
def root_health():
    return {
        "service": settings.PROJECT_NAME,
        "status": "operational",
        "version": "1.1.0",
        "api_v1_docs": "/docs"
    }

# Root welcome endpoint
@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "operating_hubs": ["Jaipur", "Udaipur"],
        "api_v1_endpoints": {
            "health": f"{settings.API_V1_STR}/health",
            "enquiries": f"{settings.API_V1_STR}/enquiries",
            "clients": f"{settings.API_V1_STR}/clients",
            "auth": f"{settings.API_V1_STR}/auth",
            "documentation": "/docs"
        }
    }
