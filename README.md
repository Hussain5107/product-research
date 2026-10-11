# ProductHunter AI

AI-powered e-commerce product research platform for Amazon USA, Shopify USA, and future Middle East marketplaces.

## Overview

ProductHunter AI helps you discover, validate, compare, and track potentially profitable products using market intelligence, supplier information, financial modeling, and AI-assisted research.

This repository contains:

- `frontend/` — Next.js dashboard
- `backend/` — FastAPI research and data service
- `START_PRODUCTHUNTER.bat` — one-click Windows launcher
- `docker-compose.yml` — optional local PostgreSQL and Redis services

## Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS, shadcn/ui
- Backend: Python, FastAPI, SQLAlchemy, ARQ/Redis-based job concepts
- Database: SQLite by default for no-Docker local use; PostgreSQL optional
- Background jobs: Redis-backed worker concept for future scheduled automation
- AI: pluggable LLM provider layer configured in the backend

## Local setup on Windows without Docker

The current local app can run without Docker. It uses SQLite at `backend/producthunter.db`.

Prerequisites:

- Node.js installed
- Python 3.10 or newer installed

1. Open the project folder:

```powershell
cd "E:\AI\Product Research Tool\ProductHunterAI"
```

2. If the backend virtual environment is already present, double-click:

```text
START_PRODUCTHUNTER.bat
```

The launcher runs migrations, starts the backend, starts the frontend, and opens:

```text
http://127.0.0.1:3000/discovery
```

If you need to set up the backend environment manually:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Install frontend dependencies manually if needed:

```powershell
cd frontend
npm install
```

Run database migrations manually if needed:

```powershell
cd backend
$env:POSTGRES_DSN="sqlite+aiosqlite:///./producthunter.db"
.\.venv\Scripts\alembic.exe upgrade head
```

Start the backend manually:

```powershell
cd backend
$env:POSTGRES_DSN="sqlite+aiosqlite:///./producthunter.db"
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend manually in another terminal:

```powershell
cd frontend
npm run dev -- --hostname 127.0.0.1 --port 3000
```

## Optional Docker/PostgreSQL mode

Docker is only needed if you want PostgreSQL/Redis instead of SQLite.

```bash
docker-compose up -d
```

Then set `POSTGRES_DSN` in `backend/.env` to your PostgreSQL URL and run Alembic migrations.

## Dashboard URLs

Product Finder:

```text
http://127.0.0.1:3000/discovery
```

Supplier Finder:

```text
http://127.0.0.1:3000/supplier-finder
```

Backend API:

```text
http://127.0.0.1:8000
```

## Project structure

```text
ProductHunterAI/
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── scripts/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Important behavior

- This application is designed for personal research use.
- It does not require user registration or login by default.
- Sensitive credentials are stored only on the backend.
- AI features are assisted, not authoritative.
- Financial calculations are deterministic.
- Research results distinguish verified data, estimates, and missing information.

## Development priorities

1. Dashboard and navigation
2. Product discovery workflow
3. AI provider configuration
4. Research connectors
5. Supplier matching
6. Profitability calculations
7. Amazon and Shopify scoring
8. Product details, comparison, watchlist, and history
9. Scheduled research

## Current feature status

| Feature | Status |
| --- | --- |
| Dashboard summary and charts | Partially implemented; uses stored backend data and empty states. |
| Connector registry | Partially implemented; connector health and capabilities are declared, but live external retrieval requires future compliant integrations. |
| Financial calculator | Implemented and covered by deterministic tests. |
| Product comparison financials | Partially implemented; uses stored product costs and calculated sensitivity rows. |
| Global Deal Finder landed-cost ranking | Implemented for manual/user-supplied offers through `POST /global-deals/rank-manual-offers`. Live Amazon marketplace discovery and checkout verification are not yet implemented. |
| AI provider configuration | Partially implemented; keys remain server-side. |
| Automation center | Planned; durable background scheduling is not yet implemented. |

## Global Deal Finder manual ranking

The first Global Deal Finder backend capability accepts user-supplied or manually imported Amazon offers and ranks only qualifying offers. It does not invent prices, shipping, taxes, import fees, delivery eligibility, or discounts.

Endpoint:

```text
POST http://localhost:8000/global-deals/rank-manual-offers
```

An offer qualifies for the top five only when:

- It is an exact match or equivalent regional version.
- UAE delivery eligibility is verified.
- product price, discount, shipping, import charges, taxes, handling, and AED exchange rate are available.
- Delivered-cost verification is not incomplete.

Similar or incomplete products are returned separately with exclusion reasons.

## Implementation plan

See `IMPLEMENTATION_PLAN.md` for the current workspace assessment, reference repository review, data-access limitations, phased roadmap, and next recommended development phase.

## Notes

USA is the primary initial marketplace. UAE and other Middle East markets are supported by architecture but are not populated with placeholder research results in Phase 1.
