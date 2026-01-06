
# AI Travel Copilot

An intelligent, full-stack AI travel assistant with four core modules:
1. **Agentic Trip Planner** - Plan and re-plan trips with AI
2. **Travel Disruption Copilot** - Handle flight delays, cancellations, and rerouting
3. **Local Experience Discovery** - Find hyper-local experiences and hidden gems
4. **Safety & Scam Awareness** - Stay safe with real-time advisories and scam alerts

## Tech Stack

### Backend
- **Framework:** FastAPI
- **Databases:** PostgreSQL (Neon), MongoDB Atlas, Qdrant (vector DB)
- **AI/LLM:** Google Gemini, LangChain
- **Language:** Python 3.10+

### Frontend
- **Framework:** React / Next.js
- **Language:** TypeScript
- **Styling:** Tailwind CSS

## Project Structure

ai-travel-copilot/
├── backend/ # FastAPI application
├── frontend/ # React/Next.js application
├── scripts/ # Data ingestion and utility scripts
└── docs/ # Documentation and architecture diagrams


## Setup Instructions

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
Create and activate virtual environment:

bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

bash
pip install -r requirements.txt
Configure environment variables:

bash
cp .env.example .env
# Edit .env with your actual credentials
Run the development server:

bash
uvicorn app.main:app --reload
Access the API:

API: http://localhost:8000

Docs: http://localhost:8000/docs

Health: http://localhost:8000/health

Frontend Setup
(Coming in Day 2)

Development Timeline
Days 1-2: Core infrastructure setup

Days 3-10: Trip Planner page

Days 11-15: Disruption Copilot page

Days 16-20: Local Discovery page

Days 21-24: Safety & Scam page

Days 25-32: Auth, testing, deployment

License
MIT License


***
