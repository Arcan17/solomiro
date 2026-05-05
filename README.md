# SoloMiro

![CI](https://img.shields.io/github/actions/workflow/status/your-org/solomiro/ci.yml?label=CI)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![Next.js 14](https://img.shields.io/badge/Next.js-14-black)
![License MIT](https://img.shields.io/badge/license-MIT-green)

**AI-powered car advisor for Chile.** Tell SoloMiro what car you have and what you want to improve. In under one minute, it tells you whether switching makes sense and which car is your best option.

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
     ├── Calculator (costs, savings, payback)
     ├── AI Service (Anthropic/OpenAI/Gemini)
     └── PostgreSQL (recommendations + leads)
```

---

## Quickstart

### Docker (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/your-org/solomiro.git
cd solomiro

# 2. Add your API key to backend/.env
cp backend/.env.example backend/.env
# Edit backend/.env and set AI_API_KEY=sk-ant-...
# Also change DATABASE_URL to the postgres URL if using docker-compose

# 3. Start services
docker compose up --build

# 4. Visit http://localhost:3000 (or run the frontend separately)
```

### Local development

#### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in AI_API_KEY
mkdir -p data
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

The API will be available at <http://localhost:8000>.
Interactive docs: <http://localhost:8000/docs>

#### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

The frontend will be available at <http://localhost:3000>.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/solomiro.db` | SQLAlchemy connection string |
| `AI_PROVIDER` | `anthropic` | AI backend: `anthropic`, `openai`, `gemini` |
| `AI_API_KEY` | *(empty)* | API key for the selected AI provider |
| `AI_MODEL` | `claude-sonnet-4-5` | Model ID to use |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `FUEL_PRICE_95` | `1100` | CLP per litre of 95-octane gasoline |
| `FUEL_PRICE_DIESEL` | `1050` | CLP per litre of diesel |
| `FUEL_PRICE_KWH` | `120` | CLP per kWh of electricity |

---

## How to get API keys

### Anthropic (default)
1. Go to <https://console.anthropic.com>
2. Navigate to **API Keys** and create a new key.
3. Set `AI_PROVIDER=anthropic` and `AI_API_KEY=sk-ant-...`
4. Set `AI_MODEL=claude-sonnet-4-5` (or another Claude model)

### OpenAI
1. Go to <https://platform.openai.com/api-keys>
2. Create a new secret key.
3. Set `AI_PROVIDER=openai`, `AI_API_KEY=sk-...`, `AI_MODEL=gpt-4o`

### Gemini
1. Go to <https://aistudio.google.com/app/apikey>
2. Create an API key.
3. Set `AI_PROVIDER=gemini`, `AI_API_KEY=AIza...`, `AI_MODEL=gemini-1.5-pro`

---

## Running tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

All 21 tests run with SQLite in-memory and a `MockAIProvider`. No external API calls are made.

```
tests/test_calculator.py   — 7 tests  (cost calculations)
tests/test_recommender.py  — 8 tests  (filtering, scoring, recommend pipeline)
tests/test_api.py          — 6 tests  (HTTP endpoints, DB persistence)
```
