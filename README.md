# CreativeLens

CreativeLens is a lightweight, clean, local-first marketing creative evaluation platform. It enables marketing teams and brands to create campaigns, upload multiple creative assets (images and videos), inspect previews, and establish the persistence layer needed for multi-model evaluation.

---

## 1. Project Overview

Marketing creatives require continuous evaluation across different AI vision and multimodal models to measure:
- Extracted text accuracy (OCR)
- Contextual scene understanding
- Inference speed / latency
- Cost per evaluation

CreativeLens provides the foundational platform:
- Organizing marketing campaigns
- Uploading and locally storing creative assets (images & videos)
- Metadata and file persistence with SQLite and local storage
- Clean React web interface for campaign and asset management with native visual/video previews

---

## 2. Architecture

CreativeLens is built with strict separation of concerns, keeping business logic, file storage, and data access decoupled.

```
CreativeLens/
├── backend/
│   ├── app/
│   │   ├── core/         # Configuration & environment settings
│   │   ├── db/           # SQLAlchemy engine, session maker, Base
│   │   ├── models/       # SQLAlchemy ORM models (Campaign, Asset)
│   │   ├── schemas/      # Pydantic schemas for request validation & API contracts
│   │   ├── services/     # Business logic & local filesystem storage services
│   │   ├── routers/      # FastAPI endpoint definitions (health, campaigns, assets)
│   │   └── main.py       # FastAPI application entrypoint & middleware
│   ├── tests/            # Pytest test suite (health, campaigns, assets, upload)
│   └── requirements.txt  # Python package dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # React components (CampaignList, CreateCampaign, CampaignDetails)
│   │   ├── services/     # API client service layer
│   │   ├── types/        # TypeScript interfaces & types
│   │   ├── App.tsx       # Main UI state & view router
│   │   └── App.css       # Clean, framework-free responsive styles
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
└── data/
    ├── creative_lens.db  # SQLite database
    └── campaigns/        # Campaign asset storage directory
        └── <campaign_id>/
            └── assets/
                └── <asset_id>_<sanitized_filename>
```

---

## 3. Tech Stack

- **Backend**:
  - Python 3.10+
  - FastAPI (REST API framework)
  - Pydantic v2 (Request/Response schemas and validation)
  - SQLAlchemy 2.0 (ORM and database queries)
  - SQLite (Local database persistence)
  - Pytest & HTTPX (Automated test suite)
- **Frontend**:
  - React 19
  - Vite 8
  - TypeScript
  - Native HTML5 Video & Image preview elements
- **Storage**:
  - Local filesystem with filename sanitization and directory traversal guards

---

## 4. How to Run Backend

### Prerequisites
- Python 3.10 or higher

### Steps
1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run automated tests:
   ```bash
   PYTHONPATH=. pytest tests
   ```

5. Start the backend server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

The backend API will run at `http://localhost:8000`.
- Health check: `GET http://localhost:8000/health`
- Interactive API documentation: `http://localhost:8000/docs`

---

## 5. How to Run Frontend

### Prerequisites
- Node.js 18 or higher & npm

### Steps
1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run typecheck and production build:
   ```bash
   npm run build
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will run at `http://localhost:5173`.

---

## 6. How Campaigns & Assets Are Stored

### Database Persistence (SQLite)
All relational data is stored locally in `data/creative_lens.db`:
- **`campaigns`**:
  - `id`: Unique identifier (UUIDv4)
  - `name`: Campaign name (required, non-blank)
  - `created_at`: Timestamp (UTC)
  - `updated_at`: Timestamp (UTC)
- **`assets`**:
  - `id`: Unique identifier (UUIDv4)
  - `campaign_id`: Foreign key referencing `campaigns.id` (cascades on delete)
  - `filename`: Sanitized original filename
  - `file_path`: Relative filesystem path (`data/campaigns/<campaign_id>/assets/...`)
  - `media_type`: `'image'` or `'video'`
  - `mime_type`: Standard MIME type (e.g. `image/jpeg`, `image/png`, `video/mp4`)
  - `file_size`: File size in bytes
  - `created_at`: Timestamp (UTC)

### Local Filesystem Storage
Uploaded files are stored in the local `data/campaigns` directory:
```
data/
    campaigns/
        <campaign_id>/
            assets/
                <asset_id>_<sanitized_original_filename>
```
**Filesystem Safety & Sanitization**:
- Filenames are sanitized using regex (`sanitize_filename`), removing path separators (`/`, `\`), null bytes (`\x00`), and directory traversal indicators (`..`).
- Supported image formats: `.jpg`, `.jpeg`, `.png`, `.webp`.
- Supported video formats: `.mp4`, `.mov`, `.webm`.
- Unsupported extensions are rejected with a clear 400 Bad Request error.
- Asset files are served via `GET /assets/{asset_id}/file` with HTTP range request support for smooth streaming.

---

## 7. Current Limitations

1. **AI Processing Not Included**: Model adapters (OpenAI, Gemini, Anthropic, local models) and inference evaluation are intentionally deferred to future phases.
2. **Video Frame Extraction**: Video previews use the browser's native `<video>` element; server-side video frame extraction via FFmpeg is not yet implemented.
3. **Local Single-Node Storage**: Assets and database reside on the local disk (by design for this induction phase).
4. **Synchronous Upload Processing**: Files are written synchronously via FastAPI streaming chunks; background task queues (e.g., Celery/Redis) are avoided for architectural simplicity.

---

## 8. Planned Next Phases

1. **Media Processing Pipeline**:
   - Automated video keyframe extraction via FFmpeg
   - Image normalization and thumbnail generation
2. **AI Model Adapters**:
   - Provider adapters for Gemini, GPT-4 Vision, Claude 3.5, and local multimodal models
   - Standardized interface for OCR text extraction and contextual image captioning
3. **Evaluation Engine**:
   - Ground truth comparison and Levenshtein/character error rate (CER) metrics
   - Semantic contextual similarity scoring
   - Latency (time-to-first-token & total execution time) tracking
   - Cost estimation per model and per asset
4. **Evaluation Dashboard**:
   - Side-by-side model comparison UI
   - Exportable benchmark reports
