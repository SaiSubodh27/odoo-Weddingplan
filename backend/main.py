"""Root ASGI entrypoint for The Royal Knot backend.

Allows running either:
    uvicorn main:app --reload
or:
    uvicorn app.main:app --reload
"""
from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

