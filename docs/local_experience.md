# 🗺️ Local Experience — Architecture Documentation

> **AI Travel Copilot · Local Discovery & Recommendations**

This document provides a **production‑ready, end‑to‑end architecture overview** of the **Local Experience** feature. It is intended to serve as:

* 📘 Onboarding documentation for new engineers
* 🧠 System design & architecture reference
* 🔌 API and data‑flow documentation
* 🚀 Deployment & scaling guide

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Architecture](#2-system-architecture)
3. [Complete Data Flow](#3-complete-data-flow)
4. [Data Ingestion Pipeline](#4-data-ingestion-pipeline)
5. [Technology Stack Summary](#5-technology-stack-summary)
5. [API Endpoints](#6-api-endpoints)

---

## 1. Overview

The **Local Experience** feature is an AI‑powered discovery engine within the AI Travel Copilot that provides **personalized, context‑aware local recommendations** for travelers.

It combines **geospatial search**, **semantic vector search**, and **Retrieval Augmented Generation (RAG)** to recommend the *best* local points of interest (POIs) — not just nearby ones.

### 🎯 Key Capabilities

* 🧠 **Natural Language Understanding**
  Understands vague and contextual queries like *"romantic dinner for anniversary"* or *"something fun to do nearby"*.

* 🔍 **Hybrid Search**
  Combines:

  * MongoDB geospatial queries
  * Qdrant semantic similarity search

* 🤖 **RAG‑based Recommendations**
  Uses Gemini 2.0 Flash to reason over POIs + local context and generate curated recommendations.

* 📍 **Location‑Aware & Preference‑Aware**
  Considers distance, budget, time, group size, cuisine, dietary needs, and more.

* 🏙️ **Scalable City Model**
  Designed to support multiple cities with minimal ingestion overhead.

---

## 2. System Architecture

### High‑Level Architecture Diagram

```text
+--------------------------------------------------------------------------------+
|                                 Frontend Layer                                 |
|--------------------------------------------------------------------------------|
|  React UI  |  Search Bar  |  Filter Panel  |  (Future) Map Integration          |
+------------------------------------|-------------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------------+
|                                  API Layer                                     |
|--------------------------------------------------------------------------------|
|  FastAPI Application (Python 3.12)                                              |
|                                                                                |
|  POST   /api/local/suggest         → AI Recommendations                         |
|  GET    /api/local/search          → Hybrid Search                              |
|  GET    /api/local/category/...    → Category Search                            |
|  GET    /api/local/pois/{id}       → POI Details                                |
|  GET    /api/local/categories/...  → Categories                                 |
|  GET    /api/local/cuisines/...    → Cuisines                                   |
|  GET    /api/local/cities          → Supported Cities                           |
+------------------------------------|-------------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------------+
|                                Service Layer                                    |
|--------------------------------------------------------------------------------|
|  ┌───────────────────────────┐    ┌───────────────────────────┐               |
|  | LocalDiscoveryService     |    | LocalDiscoveryAgent        |               |
|  |---------------------------|    |---------------------------|               |
|  | • Geo queries             |    | • RAG prompt construction  |               |
|  | • Hybrid scoring          |    | • Recommendation reasoning |               |
|  | • POI ranking             |    | • JSON‑mode generation     |               |
|  └─────────────┬─────────────┘    └─────────────┬─────────────┘               |
|                |                                  |                             |
|  ┌─────────────▼─────────────┐    ┌─────────────▼─────────────┐               |
|  | EmbeddingService          |    | GeminiClient               |               |
|  |---------------------------|    |---------------------------|               |
|  | • Batch embeddings (50)   |    | • Gemini 2.0 Flash         |               |
|  | • Query & document modes  |    | • JSON structured output  |               |
|  └─────────────┬─────────────┘    └─────────────┬─────────────┘               |
|                |                                  |                             |
|  ┌─────────────▼─────────────┐    ┌─────────────▼─────────────┐               |
|  | QdrantService             |    | OSMService                 |               |
|  |---------------------------|    |---------------------------|               |
|  | • Vector search (768‑d)   |    | • Overpass API             |               |
|  | • HNSW index              |    | • POI parsing              |               |
|  └───────────────────────────┘    └───────────────────────────┘               |
+------------------------------------|-------------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------------+
|                                   Data Layer                                    |
|--------------------------------------------------------------------------------|
|  MongoDB Atlas        |  Qdrant Cloud        |  External APIs                   |
|--------------------------------------------------------------------------------|
|  • POIs (GeoJSON)     |  • Vector embeddings |  • Gemini APIs                  |
|  • 2dsphere index     |  • Cosine distance   |  • Overpass API                |
|  • Metadata & tags    |  • On‑disk payload   |  • RSS Feeds                   |
+--------------------------------------------------------------------------------+
```

---

## 3. Complete Data Flow

### A. AI‑Powered Recommendation Flow

**Endpoint:** `POST /api/local/suggest`

**Input Example**

```json
{
  "query": "romantic dinner spot for anniversary",
  "location": { "lat": 19.0596, "lon": 72.8295 },
  "preferences": {
    "budget": "high",
    "group_size": 2
  }
}
```

---

### Step 1: Hybrid Search

```text
User Query
   │
   ├──► MongoDB Geo Query
   │      • 5km radius
   │      • Category + city filter
   │      • ~200 candidates
   │
   ├──► Qdrant Semantic Search
   │      • Query embedding (768‑d)
   │      • Blog posts, tips, POI descriptions
   │      • Top‑N by cosine similarity
   │
   └──► Hybrid Scoring
          • Semantic relevance
          • Distance penalty
          • Final weighted score
```

**Result:**

* ✅ Top **15 POI candidates**
* 📚 **10 supporting context documents**

---

### Step 2: RAG Prompt Construction

The `LocalDiscoveryAgent` constructs a structured prompt with **5 sections**:

1. **System Instructions**
   *"You are a local travel expert..."*

2. **User Context**
   Query, location, preferences, time of day

3. **POI Candidates (15)**
   Name, distance, cuisine, hours, features

4. **Local Insights (10)**
   Blogs, tips, neighborhood advice

5. **Output Instructions**
   Strict JSON schema (no prose)

---

### Step 3: Gemini Generation

* Model: **Gemini 2.5 Flash**
* Mode: **JSON‑only structured output**

**Output Example**

```json
[
  {
    "poi_name": "Bastian",
    "reason": "An upscale seaside restaurant perfect for special occasions.",
    "highlights": ["Sea view", "Fine dining", "Romantic ambiance"],
    "best_for": "Anniversary dinners"
  }
]
```

---

### Step 4: Recommendation Enrichment

```text
AI Output (poi_name)
      │
      ├──► MongoDB lookup
      │      • Exact name match
      │      • City‑scoped fallback
      │
      └──► Merge
             • Full POI metadata
             • AI explanation preserved
```

---

### Step 5: Response Assembly

Final response includes:

* 🏆 Top 5 enriched recommendations
* 📍 Full POI details
* 🧠 AI‑generated reasoning
* 📚 Source references
* ⏱️ Metadata (latency, model)

---




## 4. Data Ingestion Pipeline

### OSM Ingestion Flow

```text
Overpass API
     ↓
Parse + Normalize
     ↓
MongoDB Upsert (osm_id)
     ↓
Generate Descriptions
     ↓
Batch Embeddings (50)
     ↓
Upload to Qdrant (20)
```

**Command**

```bash
python scripts/ingest_osm_pois.py mumbai
```

* ⏱️ Time: ~30–40 minutes
* 📍 POIs: 3,056

---




## 5. Technology Stack Summary

| Component  | Technology           | Purpose         |
| ---------- | -------------------- | --------------- |
| Backend    | FastAPI              | API framework   |
| Language   | Python 3.12          | Core runtime    |
| Database   | MongoDB Atlas        | POI storage     |
| Vector DB  | Qdrant Cloud         | Semantic search |
| Embeddings | Gemini Embedding 001 | Vectorization   |
| LLM        | Gemini 2.0 Flash     | RAG generation  |
| Geo Data   | OpenStreetMap        | POI source      |
| Testing    | Pytest               | Validation      |

---



## 6. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/local-discovery/search` | Search POIs (query + location) |
| POST | `/api/local-discovery/chat` | Chat interface message |
| POST | `/api/local-discovery/feedback` | Submit like/dislike for POI |
| GET | `/api/local-discovery/photos/{poi_id}` | Get POI photos (cached) |
| GET | `/api/local-discovery/preferences` | Get user preferences |
| PUT | `/api/local-discovery/preferences` | Update user preferences |

---