# The Royal Knot — Backend API Service

API backend service for **The Royal Knot** Luxury Wedding Planning Management System (Jaipur & Udaipur operations).

---

## 🚀 Quick Start

Run the backend server directly:
```bash
npm run dev
```
By default, the server starts on `http://localhost:5000`.

---

## 📡 Available API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check & operating hubs status |
| `GET` | `/api/clients` | List all client dossiers (supports `?search=` and `?status=`) |
| `GET` | `/api/clients/:id` | Fetch specific client dossier by ID |
| `POST` | `/api/clients` | Create and register a new client dossier |
| `PATCH`| `/api/clients/:id/status` | Update client registration status |
| `GET` | `/api/weddings` | List palace wedding schedules and timelines |
| `GET` | `/api/agreements` | *Phase 2 preview* |
| `GET` | `/api/catering` | *Phase 2 preview* |
| `GET` | `/api/vendors` | *Phase 2 preview* |
| `GET` | `/api/payments` | *Phase 2 preview* |

---

## 📁 Structure

```
backend/
├── src/
│   ├── data/
│   │   └── mockClients.json   # Persistent mock database store
│   └── server.js              # Standalone REST API with CORS & JSON routing
├── .env.example
├── package.json
└── README.md
```
