# CreativeLens

CreativeLens is a lightweight, local-first marketing creative evaluation platform. It allows brands to organize marketing campaigns, upload creative assets (images and videos), and will subsequently evaluate them across multiple AI models for extraction accuracy, contextual understanding, latency, and cost.

## Tech Stack

- **Backend**: Python, FastAPI, Pydantic, SQLAlchemy, SQLite
- **Frontend**: React, Vite, TypeScript
- **Storage**: Local filesystem (`data/campaigns`)

---

## Local Setup & Running

### Prerequisites

- Python 3.10+
- Node.js 18+ & npm

### Backend Setup

1. Navigate to the backend directory and set up a virtual environment:
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run tests:
   ```bash
   PYTHONPATH=. pytest tests
   ```

3. Start the backend development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The backend API will be accessible at `http://localhost:8000`. Health check endpoint: `GET http://localhost:8000/health`.

### Frontend Setup

1. Navigate to the frontend directory and install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Build & typecheck:
   ```bash
   npm run build
   ```

3. Start the frontend development server:
   ```bash
   npm run dev
   ```
   The application will be accessible at `http://localhost:5173`.
