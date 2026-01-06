# AI Travel Copilot - System Architecture

## Overview

The AI Travel Copilot is a full-stack web application consisting of four interconnected modules, all sharing a common backend infrastructure.



## Module Breakdown

### 1. Trip Planner
- **Purpose:** AI-powered itinerary generation and re-planning
- **Backend:** `api/planner.py`, `services/planner_service.py`, `ai/planner_agent.py`
- **Data:** PostgreSQL (trips, days, activities), Qdrant (travel guides)

### 2. Disruption Copilot
- **Purpose:** Handle flight delays/cancellations, explain rights, suggest alternatives
- **Backend:** `api/disruptions.py`, `services/disruption_service.py`, `ai/disruption_agent.py`
- **Data:** PostgreSQL (disruption cases), Qdrant (airline/hotel policies)

### 3. Local Discovery
- **Purpose:** Hyper-local POI recommendations using RAG
- **Backend:** `api/local.py`, `services/local_service.py`, `ai/local_agent.py`
- **Data:** MongoDB (POIs from Places API), Qdrant (local blogs/guides)

### 4. Safety & Scam Awareness
- **Purpose:** Safety Q&A, scam alerts, crowdsourced reports
- **Backend:** `api/safety.py`, `services/safety_service.py`, `ai/safety_agent.py`
- **Data:** MongoDB (safety reports), Qdrant (government advisories)

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React/Next.js, TypeScript, Tailwind CSS |
| **Backend API** | FastAPI, Python 3.10+ |
| **Relational DB** | PostgreSQL (Neon) |
| **NoSQL DB** | MongoDB Atlas |
| **Vector DB** | Qdrant Cloud |
| **LLM** | Google Gemini |
| **AI Framework** | LangChain |
| **Auth** | JWT / OAuth (Google) |
| **Deployment** | Render/Railway (backend), Vercel (frontend) |

## Data Flow Example: Trip Planning

1. User submits trip constraints via frontend form
2. Frontend calls `POST /trips/` → creates trip record in PostgreSQL
3. User clicks "Generate Itinerary"
4. Frontend calls `POST /trips/{id}/plan`
5. Backend:
   - `PlannerAgent` queries Qdrant for city guides (with caching)
   - If cache miss → web search → embed → store in Qdrant
   - Gemini generates day-by-day itinerary using retrieved context
   - Saves `TripDay` and `Activity` records to PostgreSQL
6. Frontend fetches updated trip and displays itinerary

## Security & Performance

- **Auth:** JWT tokens for protected endpoints
- **Rate Limiting:** Per-user limits on AI generation endpoints
- **Caching:** Qdrant caches travel guides and policies (TTL: 30-90 days)
- **API Keys:** Stored in environment variables, never committed to git
- **CORS:** Restricted to frontend domain

## Future Enhancements

- Real-time notifications via WebSockets
- Multi-language support
- Offline itinerary access (PWA)
- Integration with booking platforms
- Advanced analytics dashboard