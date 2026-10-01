# CreativeLens

CreativeLens is a lightweight, clean, local-first marketing creative evaluation platform. It enables marketing teams and brands to create campaigns, upload multiple creative assets (images and videos), extract rich media metadata and sampled video keyframes, inspect visual previews, and establish the persistent foundation required for multi-model AI evaluation.

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
- Local filesystem & SQLite persistence
- Robust media processing pipeline with Pillow (images) and FFmpeg (videos)
- Automated video frame extraction at configurable sampling rates (default: 1 FPS)
- Clean React web interface for campaign and asset management with native visual/video previews, metadata badges, and interactive frame gallery strips

---

## 2. Architecture

CreativeLens is built with strict separation of concerns, keeping business logic, file storage, and data access decoupled.

```
CreativeLens/
├── backend/
│   ├── app/
│   │   ├── core/         # Configuration & environment settings
│   │   ├── db/           # SQLAlchemy engine, session maker, Base
│   │   ├── models/       # SQLAlchemy ORM models (Campaign, Asset, MediaProcessing)
│   │   ├── schemas/      # Pydantic schemas for request validation & API contracts
│   │   ├── services/     # Business logic: storage, media detection, image & FFmpeg processing
│   │   ├── routers/      # FastAPI endpoint definitions (health, campaigns, assets)
│   │   └── main.py       # FastAPI application entrypoint & CORS middleware
│   ├── tests/            # Pytest test suite (health, campaigns, assets, upload, processing, robustness)
│   └── requirements.txt  # Python package dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # React components (CampaignList, CreateCampaign, CampaignDetails)
│   │   ├── services/     # API client service layer (campaigns, assets, processing, frames)
│   │   ├── types/        # TypeScript interfaces & types
│   │   ├── App.tsx       # Main UI state & view router
│   │   └── App.css       # Clean, framework-free responsive styles
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
└── data/
    ├── creative_lens.db  # SQLite database
    └── campaigns/        # Campaign storage directory
        └── <campaign_id>/
            ├── assets/
            │   └── <asset_id>_<sanitized_filename>
            └── processed/
                └── <asset_id>/
                    └── frames/
                        ├── frame_000001.jpg
                        ├── frame_000002.jpg
                        └── ...
```

---

## 3. Tech Stack

- **Backend**:
  - Python 3.10+
  - FastAPI (REST API framework)
  - Pydantic v2 (Request/Response schemas and validation)
  - SQLAlchemy 2.0 (ORM and database queries)
  - SQLite (Local database persistence)
  - Pillow (Image metadata extraction & validation)
  - FFmpeg & ffprobe (Subprocess-isolated video analysis & keyframe extraction)
  - Pytest & HTTPX (Automated test suite)
- **Frontend**:
  - React 19
  - Vite 8
  - TypeScript
  - Native HTML5 Video & Image preview elements with extracted frame gallery strip
- **Storage**:
  - Local filesystem with filename sanitization, directory traversal guards, and automatic failure cleanup

---

## 4. External Dependencies & Installation

### FFmpeg Installation

The media processing service uses `ffprobe` for video metadata extraction and `ffmpeg` for keyframe sampling. Both must be installed on your machine and available on `PATH`.

- **macOS (Homebrew)**:
  ```bash
  brew install ffmpeg
  ```

- **Ubuntu / Debian**:
  ```bash
  sudo apt update
  sudo apt install -y ffmpeg
  ```

- **Arch Linux**:
  ```bash
  sudo pacman -S ffmpeg
  ```

- **Windows (Chocolatey / Scoop)**:
  ```powershell
  choco install ffmpeg
  # or
  scoop install ffmpeg
  ```

To verify installation:
```bash
ffmpeg -version
ffprobe -version
```

If FFmpeg is not installed, the platform will continue running, but video processing requests will return a structured `failed` status with a clear message instructing the user to install FFmpeg.

---

## 5. How to Run Backend

### Prerequisites
- Python 3.10 or higher
- FFmpeg (for video processing)

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

4. Run automated tests (all 60 unit, integration, and robustness tests):
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

## 6. How to Run Frontend

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

## 7. Media Processing Service

The Media Processing Service inspects, validates, and prepares uploaded creative assets for downstream AI evaluation.

### Supported Formats
- **Images**: `.jpg`, `.jpeg`, `.png`, `.webp`
- **Videos**: `.mp4`, `.mov`, `.webm`

### Processing Lifecycle & Status Flow
Each asset has an associated `MediaProcessing` record that follows a strict state transition:
```
       [ Upload ]
           │
           ▼
       ( pending )
           │
           │ POST /assets/{asset_id}/process
           ▼
     ( processing )
       ╱        ╲
      ╱          ╲
     ▼            ▼
( completed )   ( failed )
```

- **`pending`**: Asset uploaded but media processing not yet triggered.
- **`processing`**: Media inspection and frame extraction actively running. Duplicate requests while in this state are safely ignored.
- **`completed`**: Metadata successfully extracted and saved. For videos, sampled frames have been generated and indexed.
- **`failed`**: An error occurred (e.g. corrupt media, 0 bytes, missing file, missing FFmpeg). A descriptive error message is saved in `error_message`, and partial artifacts are automatically cleaned up.

### Frame Extraction Behavior
For video assets, frames are extracted using FFmpeg at a configurable sampling rate:
- **Default rate**: `sample_fps = 1.0` (1 frame per second). For example, a 10-second video yields approximately 10 frames.
- **Frame naming**: `frame_000001.jpg`, `frame_000002.jpg`, `frame_000003.jpg`, etc.
- **Quality**: Jpeg quality factor `-q:v 2` for high fidelity.
- **Storage Location**:
  ```
  data/campaigns/<campaign_id>/processed/<asset_id>/frames/frame_000001.jpg
  ```

---

## 8. Media Processing API Reference

### 1. Trigger Media Processing
```http
POST /assets/{asset_id}/process
Content-Type: application/json
```
**Request Body (optional):**
```json
{
  "sample_fps": 1.0,
  "force": false
}
```
* `sample_fps` (float, optional, default: `1.0`): Target frames per second to extract (`0 < sample_fps <= 60`).
* `force` (bool, optional, default: `false`): If `true`, re-runs processing even if previously completed.

**Example Response (Image):**
```json
{
  "id": "7a35368a-cf8e-49b0-9cfd-d4218eb5b62b",
  "asset_id": "b6a7a0de-f222-4114-8f78-656cfb2f0bdf",
  "media_type": "image",
  "status": "completed",
  "width": 1200,
  "height": 628,
  "format": "PNG",
  "color_mode": "RGB",
  "duration_ms": null,
  "frame_rate": null,
  "total_frames": null,
  "frames_extracted": null,
  "frame_directory": null,
  "processed_at": "2026-10-01T09:30:00Z",
  "error_message": null,
  "created_at": "2026-10-01T09:29:55Z",
  "updated_at": "2026-10-01T09:30:00Z"
}
```

**Example Response (Video):**
```json
{
  "id": "3c983c5a-5231-409b-a3d8-5e4c6c9e05e1",
  "asset_id": "c1f7b9e0-8fa3-4cb5-8d59-281b3769910d",
  "media_type": "video",
  "status": "completed",
  "width": 1920,
  "height": 1080,
  "format": "h264",
  "color_mode": null,
  "duration_ms": 10000,
  "frame_rate": 30.0,
  "total_frames": 300,
  "frames_extracted": 10,
  "frame_directory": "data/campaigns/4fe8a04b-325d-4fcf-84a1-b4f8cb080b06/processed/c1f7b9e0-8fa3-4cb5-8d59-281b3769910d/frames",
  "processed_at": "2026-10-01T09:30:05Z",
  "error_message": null,
  "created_at": "2026-10-01T09:29:55Z",
  "updated_at": "2026-10-01T09:30:05Z"
}
```

### 2. Get Asset Processing Record
```http
GET /assets/{asset_id}/processing
```
Returns HTTP 200 with the `MediaProcessingResponse` schema, or HTTP 404 if not found.

### 3. Get Asset Frames List
```http
GET /assets/{asset_id}/frames
```
**Example Response:**
```json
{
  "asset_id": "c1f7b9e0-8fa3-4cb5-8d59-281b3769910d",
  "total_frames": 10,
  "frame_directory": "data/campaigns/.../frames",
  "frames": [
    {
      "frame_number": 1,
      "filename": "frame_000001.jpg",
      "url": "/assets/c1f7b9e0-8fa3-4cb5-8d59-281b3769910d/frames/frame_000001.jpg"
    },
    {
      "frame_number": 2,
      "filename": "frame_000002.jpg",
      "url": "/assets/c1f7b9e0-8fa3-4cb5-8d59-281b3769910d/frames/frame_000002.jpg"
    }
  ]
}
```

### 4. Fetch Individual Extracted Frame File
```http
GET /assets/{asset_id}/frames/{frame_filename}
```
Returns the JPEG image binary stream (`image/jpeg`).

---

## 9. Current Limitations

1. **AI Processing Not Included**: Model adapters (OpenAI, Gemini, Anthropic, local models) and inference evaluation are intentionally deferred to Phase 3.
2. **Local Single-Node Processing**: Processing runs locally via synchronous subprocess invocation; distributed background task queues (e.g. Celery/Redis) are avoided to maintain lightweight setup.
3. **No Automatic Downscaling**: Extracted frames retain original video source resolution.

---

## 10. Planned Next Phases

### Phase 3: Model Inference & Adapters
1. **Model Adapter Architecture**:
   - Provider adapters for Gemini, GPT-4 Vision, Claude 3.5, and local Ollama/vLLM models
   - Standardized inference interface for OCR text extraction and contextual scene understanding
2. **Execution & Configuration**:
   - Prompt templates and evaluation configs per campaign
   - Multi-model runner for single-asset and batch campaign evaluation
3. **Metrics Tracking**:
   - Latency (time-to-first-token, total generation time)
   - Token usage and cost tracking per asset and model

### Phase 4: Evaluation Engine & Benchmarking
1. **Ground Truth & Accuracy Metrics**:
   - Character Error Rate (CER) and Word Error Rate (WER) for extracted text
   - Semantic similarity embeddings for contextual understanding
2. **Side-by-Side Comparison UI**:
   - Comparison matrix displaying model outputs, accuracy scores, latency, and costs
   - Benchmark exports in JSON and CSV
