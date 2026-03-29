# ⚡ Flight Disruption Intelligence System

Real-time flight monitoring, region-aware passenger rights, AI-ranked recovery options, and a context-aware disruption assistant.

---

## Features

- **Real-time flight status** — live data via AviationStack (terminal, gate, delay minutes, severity)
- **Live weather at origin airport** — Tomorrow.io, used to contextualise disruption cause
- **Passenger rights engine** — region inferred from IATA codes; rights, entitlements, and next steps returned from a pre-ingested MongoDB knowledge base
- **AI recovery options** — refund eligibility, alternative flights (same day + next day), hotel cancellation, compensation claims, insurance pathways; Gemini ranks top 3–5 per case
- **AI draft email generator** — ready-to-send templates (To, Subject, Body) in 3 tones: firm, polite, friendly
- **Context-aware chat assistant** — sidebar AI with full access to case data; chat history persisted per case in PostgreSQL

---

## Data Flow

```
User creates disruption case (flight number, airline, IATA codes, date)
        ↓
Parallel enrichment:
  ├── AviationStack → flight status + severity
  ├── Tomorrow.io → origin airport weather
  └── IATA code → region lookup → MongoDB → passenger rights
        ↓
All data persisted to PostgreSQL
        ↓
Gemini → generate + rank recovery options
        ↓
Gemini → generate draft email templates (3 tones)
        ↓
Render cards to user
        ↓
Chat assistant queries (grounded in case data, history in PostgreSQL)
```

---

## Knowledge Base Architecture

Passenger rights regulations are pre-ingested into MongoDB (not fetched live):

- **Why MongoDB:** document model fits nested rights/steps/source links better than relational tables
- **Why pre-ingested:** regulations change infrequently; live web search per case adds latency and cost
- **Region mapping:** IATA origin/destination codes → country/region → regulation (DGCA CAR, EU261, DOT, Montreal Convention)

Ingestion is done via `scripts/ingest_policies.py` and refreshed manually when regulations update.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Flight status | AviationStack API |
| Weather | Tomorrow.io API |
| Passenger rights | MongoDB (pre-ingested knowledge base) |
| Options ranking | Gemini API |
| Email generation | Gemini API |
| Chat assistant | Gemini API |
| Data storage | PostgreSQL (Neon) |
| Chat history | PostgreSQL (per case) |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/disruptions/cases` | Create disruption case |
| GET | `/api/disruptions/cases` | Get all cases for user |
| GET | `/api/disruptions/cases/{id}` | Get case with enriched data |
| POST | `/api/disruptions/cases/{id}/options` | Generate recovery options |
| POST | `/api/disruptions/cases/{id}/messages` | Generate draft emails |
| GET | `/api/disruptions/cases/{id}/rights` | Get passenger rights |
| POST | `/api/disruptions/chat` | Chat assistant message |
