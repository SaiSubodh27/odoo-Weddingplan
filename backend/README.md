# The Royal Knot — FastAPI Backend Service

Backend service for **The Royal Knot** Wedding Planning Management System.

---

## 🗂️ Structure

```
backend/
├── .venv/                     # Python virtual environment
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app entrypoint, CORS & startup seed data
│   ├── database.py            # SQLAlchemy database engine & session dependency
│   ├── models/                # SQLAlchemy ORM database models
│   │   └── __init__.py
│   ├── schemas/               # Pydantic validation schemas
│   │   └── __init__.py
│   └── routes/                # API route controllers (/api/clients, /api/health, etc.)
│       └── __init__.py
├── .env                       # Environment configuration
└── requirements.txt           # Python dependencies
```

---

## 🚀 Running the Backend

Activate the virtual environment and start Uvicorn:

### On Windows PowerShell:
```powershell
backend\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

### Interactive API Documentation
Once running, open:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
