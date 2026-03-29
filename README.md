# ✈️ AI Travel Copilot

A production-deployed, full-stack AI travel assistant built with FastAPI, React, and a multi-database architecture. Three fully functional modules — trip planning, disruption intelligence, and local discovery — each backed by real external APIs, automated data pipelines, and LLM integration.

**Live Demo:** https://ai-travel-copilot.vercel.app

---

## Modules

| Module | Description | Docs |
|--------|-------------|------|
| 🗺️ Trip Planner | AI itinerary generation, flight/hotel search, real-time collaboration | [TRIP_PLANNER.md](docs/TRIP_PLANNER.md) |
| ⚡ Disruption System | Flight status, passenger rights, AI recovery options | [DISRUPTION_SYSTEM.md](docs/DISRUPTION_SYSTEM.md) |
| 📍 Local Discovery | Semantic POI search, geolocation, dual-DB retrieval | [LOCAL_DISCOVERY.md](docs/local_experience.md) |

---

## Tech Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (Python 3.11) |
| Relational DB | PostgreSQL via Neon |
| Document DB | MongoDB Atlas |
| Vector DB | Qdrant Cloud |
| LLM | Google Gemini (generation + embeddings) |
| Scheduler | APScheduler |
| Email | Resend |
| Auth | Clerk |
| Deployment | Railway |

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | React + TypeScript (Vite) |
| Styling | Tailwind CSS |
| Maps | Leaflet.js + OpenStreetMap |
| Auth | Clerk |
| Real-time | WebSockets |
| Deployment | Vercel |

### External APIs
- AviationStack — real-time flight status
- SerpAPI — flight and hotel search
- Foursquare Places — POI enrichment
- Tomorrow.io — live weather data
- Unsplash + Wikimedia — POI photos
- Mapbox — map rendering

---

## Project Structure

```
ai-travel-copilot/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers (planner, flights, hotels, disruptions, discovery, auth, ws)
│   │   ├── core/         # DB connections (postgres, mongo, qdrant, config)
│   │   ├── models/       # SQLAlchemy + Pydantic models
│   │   ├── services/     # Business logic (scheduler, disruption, discovery, etc.)
│   │   └── utils/        # Helpers (datetime, geolocation, formatting)
│   ├── scripts/
│   │   ├── ingest_osm.py         # OSM POI ingestion
│   │   ├── ingest_rss.py         # RSS feed ingestion
│   │   ├── enrich_foursquare.py  # Foursquare enrichment
│   │   └── monitor_storage.py    # Storage monitoring
│   ├── Dockerfile
│   ├── railway.toml
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/          # API service layer
│   │   ├── components/   # React components per module
│   │   ├── hooks/        # Custom hooks (useWebSocket, useLocalDiscovery etc.)
│   │   ├── pages/        # Page-level components
│   │   ├── types/        # TypeScript type definitions
│   │   └── utils/        # Utility functions
│   ├── index.html
│   └── vite.config.ts
├── docs/
│   ├── TRIP_PLANNER.md
│   ├── DISRUPTION_SYSTEM.md
│   └── LOCAL_DISCOVERY.md
└── README.md
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 22+
- Git

### 1. Clone the repo
```bash
git clone https://github.com/ArhaanAli04/ai-travel-copilot.git
cd ai-travel-copilot
```

### 2. Backend setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create your `.env` file in `backend/`:
```bash
cp .env.example .env
# Fill in all values — see Environment Variables section below
```

Start the backend:
```bash
uvicorn app.main:app --reload
```

Backend runs at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### 3. Frontend setup
```bash
cd frontend
npm install
```

Create your `.env` file in `frontend/`:
```bash
cp .env.example .env
# Fill in VITE_ prefixed variables
```

Start the frontend:
```bash
npm run dev
```

Frontend runs at: http://localhost:5173




---

