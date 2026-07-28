# SkinSpect

AI-powered skin analysis platform that detects acne and wrinkles from a photo, generates personalized skincare recommendations, tracks progress over time, and connects users with nearby dermatologists.

**Stack:** FastAPI · PostgreSQL · SQLAlchemy · PyTorch · React · Vite · Tailwind CSS

---

## Overview

SkinSpect combines a computer vision inference pipeline with a full-stack web application. A user uploads a photo, the backend runs it through two independently-trained models (an acne severity classifier and a wrinkle segmentation model), and the results feed into a rule-based recommendation engine that produces a skincare routine and an overall skin health score. Users can track how that score changes across scans, and find nearby dermatologists if their results suggest a follow-up.

## Features

- **AI skin analysis** — acne severity classification (MobileNetV2, 4-class) and wrinkle segmentation (U-Net + EfficientNet-B4 encoder) run on each uploaded photo
- **Personalized recommendations** — a rule-based engine maps detected conditions + skin type + questionnaire responses to a prioritized skincare routine
- **Progress tracking** — health score trends across scans, visualized on a dashboard
- **Dermatologist locator** — finds the nearest dermatology-specific clinics using OpenStreetMap's Overpass API, with a progressive search-radius expansion so users are never left with a dead-end "no results" screen, and one-tap directions via Google Maps
- **Authentication & email verification** — JWT-based auth with a full email verification flow (verified users unlock scanning; unverified users can still explore the app)
- **Photo quality gating** — a preprocessing stage checks brightness, face detection confidence, and image size before running inference, so users get actionable feedback instead of a garbage result

## Architecture

```
skinspect/
├── backend/           FastAPI REST API
│   └── app/
│       ├── auth/       JWT handling, dependency-injected auth guards
│       ├── models/     SQLAlchemy ORM models
│       ├── routers/    API endpoints (auth, scans, questionnaire, derm-locator)
│       ├── schemas/    Pydantic request/response models
│       └── services/   Business logic (email, dermatologist search)
├── ml/                 Inference pipeline (separate from the API layer)
│   ├── models/          Model architectures + inference wrappers
│   ├── pipeline/        Preprocessing, orchestration, product recommendation
│   └── engine/           Recommendation + progress-tracking logic
└── skinspect-frontend/ React + Vite SPA
```

The ML pipeline is intentionally decoupled from the API layer — `ml/` has no FastAPI dependency and could be run standalone via `run_inference.py` for batch testing or model evaluation.

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, Tailwind CSS, Axios |
| Backend | FastAPI, SQLAlchemy, Pydantic, JWT (python-jose) |
| Database | PostgreSQL |
| ML / CV | PyTorch, OpenCV, segmentation-models-pytorch, torchvision |
| External APIs | OpenStreetMap Overpass API (dermatologist search) |
| Infra | Docker Compose (PostgreSQL) |

## Getting Started

### Prerequisites
- Python 3.12
- Node.js 18+
- Docker (for PostgreSQL)

### Backend

```bash
# Start the database
docker compose up -d postgres

# Set up the environment
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
pip install -r ../ml/requirements.txt

# Configure environment variables
cp .env.example .env
# fill in DATABASE_URL, SECRET_KEY, etc. — see Configuration below

uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs` once running.

### Frontend

```bash
cd skinspect-frontend
npm install
npm run dev
```

Runs at `http://localhost:3000`.

### Configuration

Key environment variables (`backend/.env`):

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/skinspect_db
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Email verification (optional — omit to run in dev mode, which logs
# verification links to the console instead of sending real emails)
SMTP_HOST=
SMTP_USERNAME=
SMTP_PASSWORD=
```

### Model Weights

Trained model weights (`ml/models/*.pth`) are not committed to this repository due to size. [Describe here how to obtain them — e.g. a download link, or instructions to retrain using the scripts in `ml/training/`.]

## API Overview

| Endpoint | Description |
|---|---|
| `POST /api/auth/register` | Create an account, triggers email verification |
| `POST /api/auth/login` | Authenticate, returns JWT |
| `POST /api/auth/verify-email` | Verify email via token |
| `POST /api/scans/upload` | Upload a photo for AI analysis (requires verified email) |
| `GET /api/scans/history` | List past scans |
| `GET /api/scans/{scan_id}` | Get full detail for a single scan |
| `GET /api/derm-locator/nearby` | Find nearest dermatology clinics |

Full interactive documentation at `/docs` (Swagger UI).

## Known Limitations

- Model class-label mapping was hand-verified against training data but should be re-confirmed if models are retrained
- Dermatologist search quality depends on OpenStreetMap tagging coverage, which varies significantly by region
- No automated test suite yet for the ML pipeline

## Roadmap

- [ ] Expand training dataset for both models
- [ ] Add automated tests (pytest for backend, model evaluation harness for ML pipeline)
- [ ] CI/CD pipeline
- [ ] Deploy to production (currently local-dev only)
