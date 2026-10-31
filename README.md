# The Royal Knot — Wedding Planning Management System

A bespoke, luxury wedding planning management platform for **The Royal Knot**, operating across premier heritage venues in **Jaipur** and **Udaipur**, India.

---

## 🗂️ Project Repository Structure

This repository is organized into dedicated **frontend** and **backend** workspaces:

```
odoo-Weddingplan/
├── frontend/                  # React + Vite + TypeScript luxury UI dashboard
│   ├── src/
│   │   ├── components/        # Layout, Sidebar, Topbar, ClientTable, ClientForm
│   │   ├── context/           # Client state store & local persistence
│   │   ├── data/              # Mock client & palace wedding datasets
│   │   ├── pages/             # Login, Dashboard, Clients, Add Client, Details, Weddings, Settings
│   │   ├── types/             # TypeScript client & package definitions
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
│
├── backend/                   # Node.js API Service & REST Endpoints
│   ├── src/
│   │   ├── data/
│   │   │   └── mockClients.json
│   │   └── server.js          # REST server (/api/clients, /api/weddings, /api/health)
│   ├── .env.example
│   ├── package.json
│   └── README.md
│
├── package.json               # Root scripts runner
└── README.md
```

---

## 🚀 Running the Project

You can run commands directly from the root, or by navigating into either directory:

### Option 1: From the Root Directory

- **Run Frontend (Vite Dev Server)**:
  ```bash
  npm run dev
  # or
  npm run dev:frontend
  ```
  Accessible at: `http://localhost:5173/`

- **Run Backend (API Server)**:
  ```bash
  npm run dev:backend
  ```
  Accessible at: `http://localhost:5000/`

- **Build Frontend for Production**:
  ```bash
  npm run build
  ```

---

### Option 2: Running from Dedicated Subfolders

#### 🎨 Frontend
```bash
cd frontend
npm run dev
```

#### ⚙️ Backend
```bash
cd backend
npm run dev
```

---

## 🏛️ Frontend Design Philosophy
- **Light Color Palette**: Warm ivory (`#FAF8F5`), pure linen white (`#FFFFFF`), sand (`#F5F2EB`), subtle royal gold (`#9E7D3B`), and dark charcoal (`#1F2421`).
- **No Border Radius (`rounded-none`)**: Strict architectural, flat rectangular edges for a high-end luxury editorial look.
- **No Heavy Shadows**: Clean, tactile $1\text{px}$ hairline borders (`border-[#E5E0D8]`).
- **Mock Persistence**: Synchronized in-memory state with browser `localStorage`, allowing added clients to persist seamlessly across sessions.
