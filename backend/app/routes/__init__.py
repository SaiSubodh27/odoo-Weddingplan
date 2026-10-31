from app.routes.clients import router as clients_router
from app.routes.enquiries import router as enquiries_router
from app.routes.auth import router as auth_router

__all__ = [
    "clients_router",
    "enquiries_router",
    "auth_router",
]
