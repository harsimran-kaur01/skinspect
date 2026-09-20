# SkinSpect

AI-powered skin analysis platform that detects acne and wrinkles from a photo, generates personalized skincare recommendations, tracks progress over time, and connects users with nearby dermatologists.

**Stack:** FastAPI · PostgreSQL · SQLAlchemy · PyTorch · React · Vite · Tailwind CSS

---

## Overview
# SkinSpect

![License](https://img.shields.io/github/license/harsimran-kaur01/skinspect)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)
![React](https://img.shields.io/badge/React-Vite-61DAFB)

AI-powered skin analysis platform. Upload a photo and SkinSpect detects **acne** and **wrinkles**, combines the results with your questionnaire answers to build a personalised AM/PM skincare routine, tracks your progress across scans, and helps you find a nearby dermatologist when a follow-up is warranted.

**Stack:** FastAPI · PostgreSQL · SQLAlchemy · PyTorch · React · Vite · Tailwind CSS

> **Not a medical device.** SkinSpect gives general skincare guidance and is not a substitute for professional diagnosis or treatment. Severe findings trigger a prompt to see a dermatologist.

<!-- Add a demo GIF or screenshots here, for example:
![SkinSpect demo](docs/demo.gif)
-->

---

## Features

- **AI skin analysis.** Acne severity classification (MobileNetV2, 4-class) and wrinkle segmentation (U-Net with an EfficientNet-B4 encoder) run on every uploaded photo.
- **Personalised recommendations.** Scan results, questionnaire answers, skin type and age are merged into one profile that drives product picks, routines and lifestyle tips (see [Recommendation engine](#recommendation-engine)).
- **Progress tracking.** Health-score trends across scans, plus per-condition changes such as "acne improved (moderate → mild)".
- **Dermatologist locator.** Finds the nearest dermatology clinics via OpenStreetMap's Overpass API, expanding the search radius progressively so users never hit a dead-end "no results" screen, with one-tap Google Maps directions.
- **Authentication and email verification.** JWT-based auth with a full verification flow. Verified users unlock scanning; unverified users can still explore the app.
- **Photo quality gating.** Brightness, face-detection confidence and image size are checked before inference, so users get actionable feedback instead of a bad result.

## How it works

```mermaid
flowchart LR
  U["User uploads photo"] --> API["FastAPI"]
  API --> Q{"Quality gate"}
  Q -->|fail| F["Actionable feedback"]
  Q -->|pass| A["Acne classifier<br/>MobileNetV2"]
  Q -->|pass| W["Wrinkle segmentation<br/>U-Net + EfficientNet-B4"]
  A --> R["Recommendation engine"]
  W --> R
  QN["Questionnaire"] --> R
  R --> DB[("PostgreSQL")]
  DB --> UI["React dashboard"]
```

The ML pipeline is decoupled from the API layer. `ml/` has no FastAPI dependency and can be run standalone for batch testing or model evaluation.

## Recommendation engine

The engine in `ml/engine/` is rule-based and deterministic, so every recommendation can be explained and unit-tested.

1. **One merged profile.** Scan findings, questionnaire concerns, skin type and age become a single scored list of findings. A concern that appears in both the scan and the questionnaire scores higher than one seen in only one.
2. **Coverage-aware selection.** Products are chosen greedily by marginal benefit, so acne, wrinkles and questionnaire needs are each addressed instead of stacking several products for one concern.
3. **Safety rules.** Pregnancy, sensitivity, allergy, vegan and fragrance-free preferences filter the catalog when the questionnaire provides them. Only one product per ingredient family is chosen, conflicting actives (for example a retinoid with an exfoliating acid) are never combined, and total irritation load is capped.
4. **Explainable output.** Every pick includes a "Why this for you" line and usage instructions, and the engine builds separate AM and PM routines. Severe findings add a dermatologist referral.
5. **Variety over time.** Lifestyle tips are chosen from the user's actual answers, and tips shown on the previous scan are rotated out. Core products stay stable while the condition persists, because a consistent routine matters more than novelty.

## Project structure

```
skinspect/
├── backend/              FastAPI REST API
│   └── app/
│       ├── auth/          JWT handling and auth guards
│       ├── models/        SQLAlchemy ORM models
│       ├── routers/       auth, scans, questionnaire, derm-locator
│       ├── schemas/       Pydantic request/response models
│       └── services/      email, dermatologist search
├── ml/                   Inference and recommendation logic
│   ├── models/            model architectures + inference wrappers
│   ├── pipeline/          preprocessing and orchestration (config.yaml)
│   └── engine/            recommendation engine + product catalog
├── skinspect-frontend/   React + Vite SPA
├── docs/                 project documentation
└── docker-compose.yml    PostgreSQL
```

## Tech stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, Tailwind CSS, Axios |
| Backend | FastAPI, SQLAlchemy, Pydantic, JWT (python-jose) |
| Database | PostgreSQL |
| ML / CV | PyTorch, OpenCV, segmentation-models-pytorch, torchvision |
| External APIs | OpenStreetMap Overpass API |
| Infra | Docker Compose (PostgreSQL) |

## Getting started

### Prerequisites
- Python 3.12
- Node.js 18+
- Docker (for PostgreSQL)

### Backend

```bash
# Start the database
docker compose up -d postgres

# Create the environment
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
pip install -r ../ml/requirements.txt

# Configure environment variables
cp .env.example .env          # then fill in the values below

uvicorn app.main:app --reload --port 8000
```

Interactive API docs are at `http://localhost:8000/docs`.

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

# Email verification (optional). Omit to run in dev mode, which logs
# verification links to the console instead of sending real emails.
SMTP_HOST=
SMTP_USERNAME=
SMTP_PASSWORD=
```

### Model weights

Trained weights are not committed because of their size. Download them from this repository's **Releases** page and place them in `ml/models/`. The expected filenames are listed in `ml/pipeline/config.yaml`.

## API overview

| Endpoint | Description |
|---|---|
| `POST /api/auth/register` | Create an account and trigger email verification |
| `POST /api/auth/login` | Authenticate and receive a JWT |
| `POST /api/auth/verify-email` | Verify an email address with a token |
| `POST /api/scans/upload` | Upload a photo for analysis (verified email required) |
| `GET /api/scans/history` | List past scans |
| `GET /api/scans/{scan_id}` | Full detail for one scan |
| `POST /api/questionnaire/` | Create or update the skincare questionnaire |
| `GET /api/questionnaire/` | Fetch the stored questionnaire |
| `DELETE /api/questionnaire/` | Delete the questionnaire |
| `GET /api/questionnaire/check` | Check whether a questionnaire exists |
| `GET /api/derm-locator/nearby` | Find the nearest dermatology clinics |

## Testing

```bash
cd backend
pytest
```

Authentication tests are in place. Coverage for the recommendation engine and scan endpoint is on the roadmap.

## Privacy and data handling

Uploaded photos are stored on the server under `backend/uploads/`, which is excluded from version control. No user images or personal data are committed to this repository. An endpoint for users to delete their own scans and images is on the roadmap.

## Known limitations

- Model accuracy has not yet been benchmarked across skin tones. Performance on darker skin tones needs dedicated evaluation, and results should not be assumed equal across groups.
- Wrinkle severity thresholds are still being calibrated.
- Product names and links in the recommendation catalog are placeholders.
- Dermatologist search quality depends on OpenStreetMap tagging coverage, which varies by region.
- Class-label mappings were hand-verified against the training data and should be re-checked if models are retrained.

## Roadmap

- [ ] Publish evaluation metrics per condition, including skin-tone-stratified results
- [ ] Expand the training dataset for both models
- [ ] Automated tests for the recommendation engine, scan endpoint and ML pipeline
- [ ] User-initiated deletion of scans and images
- [ ] CI/CD pipeline
- [ ] Production deployment (currently local-dev only)

## License

See [LICENSE](LICENSE).
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
