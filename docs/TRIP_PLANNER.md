# 🗺️ Trip Planner Module

AI-powered itinerary generation with real flight/hotel search, live weather, multi-user collaboration, and semantic vector caching.

---

## Features

- **AI itinerary generation** — Gemini generates structured day-by-day itineraries from user inputs (origin, destinations, budget, traveler count, themes)
- **Semantic vector caching** — generated itineraries are embedded and stored in Qdrant; repeat queries for the same destinations within ±7 days trigger a RAG retrieval instead of a new LLM call
- **Activity-level editing** — reorder, delete, edit, or AI-regenerate individual activities
- **Day replanning** — regenerate a single day without affecting the rest of the trip
- **Real flight search** — SerpAPI returns live pricing and availability
- **Real hotel search** — SerpAPI hotel results per destination
- **Live weather** — actual forecast fetched per destination per day
- **Legal documentation** — Gemini with Google Search grounding pulls entry requirements, document checklists, emergency contacts, and legal advisories per destination
- **AI activity explanation** — contextual AI explanation for any activity on demand
- **Multi-user collaboration** — invite collaborators; all edits sync in real-time via WebSockets

---

## Data Flow

```
User Input (origin, destinations, budget, themes)
        ↓
Qdrant semantic search (±7 day window)
        ↓
    Cache hit? ──── YES ──→ Return embedded itinerary (RAG)
        │
       NO
        ↓
Gemini API → generate itinerary
        ↓
Embed + store in Qdrant
        ↓
Store trip/days/activities in PostgreSQL
        ↓
Parallel: SerpAPI (flights + hotels) + Tomorrow.io (weather)
        ↓
Render to user
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Itinerary generation | Gemini API |
| Vector caching | Qdrant + Gemini embeddings |
| Flight/hotel search | SerpAPI |
| Weather | Tomorrow.io |
| Legal docs | Gemini with Google Search grounding |
| Data storage | PostgreSQL (Neon) |
| Real-time sync | WebSockets (per-trip scoped rooms) |

---

## Database Schema (PostgreSQL)

Key tables:
- `users` — Clerk user mapping
- `trips` — trip metadata (origin, budget, travelers, dates)
- `trip_days` — per-day records linked to a trip
- `activities` — individual activities per day
- `flights` — saved flight results per trip
- `hotels` — saved hotel results per trip
- `trip_collaborators` — many-to-many user-trip collaboration

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/planner/trips` | Create a new trip |
| GET | `/api/planner/trips` | Get all trips for user |
| GET | `/api/planner/trips/{id}` | Get trip details |
| POST | `/api/planner/trips/{id}/generate` | Generate itinerary |
| PATCH | `/api/planner/activities/{id}` | Edit an activity |
| POST | `/api/planner/days/{id}/replan` | Replan a single day |
| GET | `/api/flights/search` | Search flights |
| GET | `/api/hotels/search` | Search hotels |
| WS | `/ws/trips/{trip_id}` | WebSocket collaboration |
