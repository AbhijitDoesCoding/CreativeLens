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
│   │   ├── adapters/     # Model adapter contract (base, mock, registry)
│   │   ├── core/         # Configuration & environment settings
│   │   ├── db/           # SQLAlchemy engine, session maker, Base
│   │   ├── models/       # ORM models (Campaign, Asset, MediaProcessing, Model, InferenceRun)
│   │   ├── schemas/      # Pydantic validation schemas (campaign, asset, processing, model, inference, pipeline)
│   │   ├── services/     # Business logic (storage, detection, processing, ffmpeg, model, inference, pipeline)
│   │   ├── routers/      # FastAPI endpoint definitions (health, campaigns, assets, processing, models, inference, pipeline)
│   │   └── main.py       # FastAPI application entrypoint & CORS middleware
│   ├── tests/            # Pytest test suite (105 unit, integration, e2e, and robustness tests)
│   └── requirements.txt  # Python package dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # React components (CampaignList, CreateCampaign, CampaignDetails, ModelManagement)
│   │   ├── services/     # API client service layer (campaigns, assets, processing, models, inference)
│   │   ├── types/        # TypeScript interfaces & types
│   │   ├── App.tsx       # Main UI state, navigation, & view router
│   │   └── App.css       # Clean, modern responsive styles
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

## 9. Model Architecture & Inference Layer

Phase 3 introduces an extensible, decoupled model inference layer. The platform executes multimodal vision models against creative assets while remaining strictly agnostic to specific vendor SDKs.

### Adapter Pattern
All AI vision and multimodal providers plug into CreativeLens via a uniform `ModelAdapter` contract:

```python
class ModelAdapter(ABC):
    @abstractmethod
    def run(self, request: ModelRequest) -> ModelResponse:
        """Executes model inference on media inputs and returns standardized outputs."""
        pass

    def is_available(self) -> bool:
        """Indicates whether provider credentials and runtime are ready."""
        return True
```

The core pipeline interacts solely through `ModelRequest` and `ModelResponse`:
* **`ModelRequest`**: Encapsulates `image_path` (for images), `video_path` (for native video models), `frame_paths` (for sampled video frames), user `prompt`, model `configuration`, and asset `metadata`.
* **`ModelResponse`**: Returns normalized OCR `text`, structured `context` (`brand`, `product`, `offer`, `cta`, `summary`), telemetry (`latency_ms`, `ttft_ms`), token counts (`input_tokens`, `output_tokens`), and simulated or calculated `estimated_cost_usd`.

### Model Registry & Lifecycle
Models are managed dynamically in SQLite:
* **Fields**: `id`, `name`, `provider`, `model_key`, `model_type`, `enabled`, `configuration_json`, `pricing_json`, timestamps.
* **Lifecycle State**: Models can be enabled or disabled at any time via the UI or API (`POST /models/{id}/enable`, `POST /models/{id}/disable`).
* **Safety Guards**: Attempting inference with a disabled model is rejected with an HTTP 400 Bad Request error. Disabled models are excluded from automated campaign pipeline runs.

### Image & Video Media Handling
CreativeLens supports both image creatives and video creatives. For video assets, the platform supports two inference modes without requiring changes to the inference pipeline:

* **Image Assets**: Passed directly by absolute filesystem path (`image_path`) to the model adapter.
* **Video Assets (Dual Representation)**:
  * **A. Native video inference**: `video_path` is provided pointing directly to the source video file on disk, allowing adapters designed for native video understanding to consume the video file directly.
  * **B. Frame-based inference**: `frame_paths` is provided containing an ordered list of keyframe paths sampled during media processing (`frame_000001.jpg`, `frame_000002.jpg`, etc.), allowing vision models that accept image frame sequences to evaluate the creative.

Adapters may choose whichever representation they support. When video processing is complete, both `video_path` and `frame_paths` are made available simultaneously in `ModelRequest`.

### Telemetry & Cost Accounting
Every inference run tracks comprehensive telemetry stored in `InferenceRun`:
* **Latency**: Measured wall-clock time and adapter-reported `latency_ms`, plus optional time-to-first-token (`ttft_ms`).
* **Token Usage**: `input_tokens` and `output_tokens`.
* **Cost Estimation**: Automatically computed based on the model's `pricing_json` (e.g., `input_per_million` and `output_per_million` rates) or passed directly from the provider.

### Fault Tolerance & Isolation
* **No Server Crashes**: Realistic failures (timeouts, network errors, malformed responses, provider failures, missing configurations, missing usage statistics) are caught, isolated, and persisted to `InferenceRun` with `status: "failed"` and a descriptive `error_message`.
* **Campaign Pipeline Isolation**: Campaign-level runs (`POST /campaigns/{id}/run`) use a bounded thread pool. A failure in one model or asset never blocks or aborts inference for other assets or models.
* **UI Visibility**: Failed runs are rendered directly in the React UI with red error badges and expandable diagnostic messages.

---

## 10. Model Inference API Reference

### 1. Register a Model
```http
POST /models
Content-Type: application/json
```
**Request Body:**
```json
{
  "name": "Deterministic Mock Vision",
  "provider": "mock",
  "model_key": "mock-vision-v1",
  "model_type": "multimodal",
  "enabled": true,
  "configuration_json": {
    "simulated_latency_ms": 120,
    "timeout_seconds": 30.0
  },
  "pricing_json": {
    "input_per_million": 0.50,
    "output_per_million": 1.50
  }
}
```

### 2. Enable / Disable a Model
```http
POST /models/{model_id}/enable
POST /models/{model_id}/disable
```

### 3. Run Inference on a Single Asset
```http
POST /assets/{asset_id}/infer/{model_id}
Content-Type: application/json
```
**Request Body (optional):**
```json
{
  "prompt": "Extract marketing text and core messaging"
}
```
**Example Response:**
```json
{
  "id": "e44d3221-a3f1-43ef-92e7-fec5d5392cf9",
  "asset_id": "b6a7a0de-f222-4114-8f78-656cfb2f0bdf",
  "model_id": "713ba0c1-3a05-4f4b-84ba-04f5e7144e54",
  "status": "completed",
  "text": "Brand Campaign: Colgate Pure Gold SBW. 20% Off Limited Time.",
  "context": {
    "brand": "Colgate",
    "product": "Pure Gold SBW",
    "offer": "20% Off Limited Time",
    "cta": "Shop Now",
    "summary": "Image marketing creative showcasing brand promo with call to action."
  },
  "latency_ms": 120,
  "ttft_ms": 48,
  "input_tokens": 375,
  "output_tokens": 76,
  "estimated_cost_usd": 0.000302,
  "error_message": null,
  "created_at": "2026-10-01T10:15:00Z",
  "model_name": "Deterministic Mock Vision",
  "model_key": "mock-vision-v1",
  "provider": "mock"
}
```

### 4. List Inference Runs for an Asset
```http
GET /assets/{asset_id}/inference-runs
```
Returns an array of `InferenceRunResponse` objects sorted by creation timestamp descending.

### 5. Retrieve an Individual Inference Run
```http
GET /inference-runs/{run_id}
```

### 6. Run Campaign Inference Pipeline
Executes all enabled models across all processable assets in a campaign with bounded concurrency:
```http
POST /campaigns/{campaign_id}/run
Content-Type: application/json
```
**Request Body (optional):**
```json
{
  "prompt": "Analyze creative text, offer, and call to action",
  "max_workers": 3
}
```
**Example Response:**
```json
{
  "campaign_id": "4fe8a04b-325d-4fcf-84a1-b4f8cb080b06",
  "assets": 4,
  "enabled_models": 2,
  "runs_created": 8,
  "successful_runs": 8,
  "failed_runs": 0
}
```

---

## 11. Planned Next Phase: Phase 4 (Model Evaluation & Benchmarking)

In Phase 4, CreativeLens will add automated evaluation and side-by-side benchmarking:

1. **Ground Truth Annotation**:
   - Defining and persisting campaign ground truth text, product naming, offers, and calls to action.
2. **Text Accuracy Metrics**:
   - Character Error Rate (CER) and Word Error Rate (WER) against verified ground truth.
   - Case-insensitive, punctuation-normalized OCR evaluation.
3. **Context Understanding Accuracy**:
   - Attribute-level precision / recall scoring for Brand, Product, Offer, and Call to Action.
   - Semantic similarity scoring for creative summaries using embedding distance.
4. **Model Comparison & Ranking Matrix**:
   - Interactive side-by-side matrix ranking models on accuracy vs. latency vs. cost.
   - Leaderboard exports in CSV and JSON.

