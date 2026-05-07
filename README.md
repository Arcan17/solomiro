# SoloMiro

![CI](https://img.shields.io/github/actions/workflow/status/Arcan17/solomiro/ci.yml?label=CI&logo=github)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white)
![Next.js 14](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![License MIT](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

> **¿Conviene cambiar mi auto?** SoloMiro responde esa pregunta en menos de un minuto.

SoloMiro is an AI-powered car advisor built for the Chilean market. You enter your current car (fuel type, weekly usage, city, maintenance costs) and what you'd like to improve (lower fuel cost, less maintenance, EV). The app calculates the real total cost of ownership, scores candidates from a curated Chilean catalog, and delivers a personalized recommendation — including the payback period if you switch.

**The problem it solves:** Most Chileans make car-switching decisions based on sticker price alone, ignoring fuel cost differences, patente, insurance, and maintenance. SoloMiro turns that into a data-driven decision backed by AI analysis.

---

## Screenshots

| Advisor Form | Recommendation Result |
|---|---|
| *(add screenshot here — `/advisor` page)* | *(add screenshot here — `/result` page)* |

> **To add screenshots:** Run the app locally, take screenshots of the `/advisor` and `/result` pages, and save them to `docs/screenshots/`. Then replace the placeholder text above with `![Advisor](docs/screenshots/advisor.png)`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| AI | Anthropic Claude / OpenAI GPT-4o / Google Gemini (switchable) |
| ORM | SQLAlchemy 2.0 + Alembic |
| Database | PostgreSQL (Docker) / SQLite (local dev) |
| Testing | pytest, 21 tests, MockAIProvider (no API calls) |
| CI/CD | GitHub Actions |
| Containerization | Docker + Docker Compose |

---

## Architecture

```
User Browser
     │
     ▼
[Next.js 14] ──── /advisor ──── /result
     │
     │ POST /recommend
     ▼
[FastAPI Backend]
     ├── CarRecommender (scoring + filtering)
     ├── Calculator (costs, savings, payback period)
     ├── AI Service (Anthropic / OpenAI / Gemini)
     └── PostgreSQL (recommendations + leads)
```

The AI provider is abstracted behind a single interface — switching from Claude to GPT-4o is a one-line environment variable change.

---

## Quickstart

### Docker (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/Arcan17/solomiro.git
cd solomiro

# 2. Add your API key
cp backend/.env.example backend/.env
# Edit backend/.env → set AI_API_KEY=your-key-here

# 3. Start everything
docker compose up --build

# 4. Open http://localhost:3000
```

### Local development

#### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # fill in AI_API_KEY
mkdir -p data
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000` — interactive docs at `http://localhost:8000/docs`

#### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Frontend available at `http://localhost:3000`

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `anthropic` | AI backend: `anthropic`, `openai`, `gemini` |
| `AI_API_KEY` | *(required)* | API key for the selected provider |
| `AI_MODEL` | `claude-sonnet-4-5` | Model ID to use |
| `DATABASE_URL` | `sqlite:///./data/solomiro.db` | SQLAlchemy connection string |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |
| `FUEL_PRICE_95` | `1100` | CLP per litre of 95-octane gasoline |
| `FUEL_PRICE_DIESEL` | `1050` | CLP per litre of diesel |
| `FUEL_PRICE_KWH` | `120` | CLP per kWh of electricity |
| `LOG_LEVEL` | `INFO` | Python logging level |

### Getting an API Key

| Provider | How to get it |
|---|---|
| **Anthropic** (default) | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| **OpenAI** | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| **Gemini** | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |

---

## Running Tests

All 21 tests run with SQLite in-memory and a `MockAIProvider` — no external API calls, no token required.

```bash
cd backend
pytest tests/ -v
```

```
tests/test_calculator.py   — 7 tests   (cost calculations, payback period)
tests/test_recommender.py  — 8 tests   (filtering, scoring, full pipeline)
tests/test_api.py          — 6 tests   (HTTP endpoints, DB persistence)

21 passed in ~1s
```

---

## Roadmap

- [ ] Add real car catalog (from MercadoLibre Chile listings)
- [ ] Deploy public demo (Vercel + Railway)
- [ ] Add comparison mode (side-by-side two candidates)
- [ ] Add shareable result links
- [ ] Spanish-language UI strings
- [ ] User accounts for saved recommendations

---

## License

MIT
