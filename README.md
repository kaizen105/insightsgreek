# InsightGreek CRM

**Enterprise CRM prototype with NLP-powered sentiment analysis, lead scoring, and role-based access control.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Inference_API-FFD21E?style=flat-square&logo=huggingface&logoColor=black)](https://huggingface.co/inference-api)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## Project Overview

InsightGreek is a full-stack CRM prototype designed around an API-first architecture. It combines a Flask REST backend with NLP-driven lead intelligence to surface actionable insights from customer interactions — without requiring a heavyweight monolithic ML runtime.

The system was originally built around a **locally fine-tuned DistilBERT model** (trained on domain-specific CRM interaction data), which achieved **85.4% classification accuracy** and outperformed rule-based industry baselines by **+17.4%** (vs. VADER and TextBlob). The current architecture has since migrated to a **Hugging Face Inference API-first approach**: the fine-tuned model is hosted on Hugging Face Spaces and consumed via HTTP, decoupling the ML runtime from the Flask application layer. This makes the backend significantly leaner — no `torch` or `transformers` installation required on the server — while preserving full model capability.

Access control is enforced via a **3-tier JWT authentication system** with role-based dashboards, backed by a **PostgreSQL** relational store for leads, contacts, and interaction history.

---

## Key Features

- **Sentiment Analysis** — Customer interaction text is classified via the fine-tuned DistilBERT model served through Hugging Face Inference API. Outperforms VADER/TextBlob by 17.4% on domain-specific CRM data.
- **Lead Conversion Scoring** — `/predict` endpoint returns a conversion probability score for inbound leads based on structured feature inputs.
- **Chatbot Intent Handling** — `/api/chat` processes natural language queries and routes them to the appropriate CRM action or response.
- **3-Tier JWT Authentication** — Role separation across Admin, Manager, and Agent tiers. Each tier exposes a scoped dashboard and restricted API surface.
- **API-First ML Architecture** — Hugging Face Inference API replaces the local PyTorch runtime. Removes heavy dependencies, enables deployment on minimal compute, and allows model versioning independently of the application layer.
- **PostgreSQL Backend** — Relational schema for leads, users, roles, and interaction logs. Designed for extensibility.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Client Layer                      │
│        (Role-Based Dashboards / API Consumers)      │
└──────────────────────┬──────────────────────────────┘
                       │  JWT Auth (3-Tier)
┌──────────────────────▼──────────────────────────────┐
│               Flask REST API (server.py)             │
│                                                     │
│   /predict          /api/chat         /auth/*       │
└────────┬─────────────────┬────────────────┬─────────┘
         │                 │                │
┌────────▼───────┐ ┌───────▼──────┐ ┌──────▼────────┐
│  Lead Scoring  │ │ Intent Router│ │  JWT + RBAC   │
│    Module      │ │   (NLP)      │ │   Handler     │
└────────┬───────┘ └───────┬──────┘ └──────┬────────┘
         │                 │                │
         └────────┬────────┘                │
┌────────────────▼──────────────┐  ┌────────▼────────┐
│  Hugging Face Inference API   │  │   PostgreSQL    │
│  (Fine-tuned DistilBERT)      │  │   Database      │
│  85.4% acc | API-first deploy │  │  (Leads, Users) │
└───────────────────────────────┘  └─────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API Framework** | Flask 2.x |
| **NLP Model** | DistilBERT (fine-tuned, hosted on Hugging Face Spaces) |
| **ML Inference** | Hugging Face Inference API (API-first, no local torch) |
| **Lead Scoring** | Custom ML model via `/predict` |
| **Authentication** | JWT (3-tier: Admin / Manager / Agent) |
| **Database** | PostgreSQL 15 |
| **Baseline Comparison** | VADER, TextBlob (+17.4% improvement) |
| **Original Training** | PyTorch + HuggingFace `transformers` (local fine-tune) |
| **Deployment** | Hugging Face Spaces, Flask server |

---

## Local Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 15 running locally or via a connection string
- A Hugging Face account with access to the hosted model endpoint

### 1. Clone and create virtual environment

```bash
git clone https://github.com/kaizen105/insightsgreek.git
cd insightsgreek

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** No `torch` or `transformers` installation required. The ML inference layer calls the Hugging Face Inference API remotely.

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
# Hugging Face
HF_API_TOKEN=hf_your_token_here
HF_MODEL_ENDPOINT=https://api-inference.huggingface.co/models/your-model-id

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/insightgreek

# JWT
JWT_SECRET_KEY=your_secret_key_here
JWT_EXPIRY_HOURS=8
```

### 4. Initialise the database

```bash
flask db upgrade        # or: python init_db.py
```

### 5. Run the server

```bash
python server.py
```

Server starts at `http://localhost:5000`.

---

## API Endpoint Reference

### Authentication

All protected endpoints require a JWT bearer token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

---

### `POST /auth/login`

Authenticate a user and receive a JWT token.

**Request**
```json
{
  "email": "manager@insightgreek.com",
  "password": "your_password"
}
```

**Response**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "role": "manager",
  "expires_in": 28800
}
```

---

### `POST /predict`

Score an inbound lead for conversion probability. Returns a score in `[0, 1]`.

**Request**
```json
{
  "lead_source": "organic_search",
  "industry": "fintech",
  "company_size": "51-200",
  "interactions_count": 4,
  "last_interaction_days": 3,
  "email_open_rate": 0.68,
  "sentiment_score": 0.81
}
```

**Response**
```json
{
  "lead_id": "lead_8a3f92",
  "conversion_probability": 0.847,
  "risk_tier": "high-value",
  "recommended_action": "escalate_to_senior_rep"
}
```

---

### `POST /api/chat`

Submit a natural language message for intent classification and CRM routing. Powered by the fine-tuned DistilBERT model via Hugging Face Inference API.

**Request**
```json
{
  "session_id": "sess_4c7d12",
  "user_id": "usr_019",
  "message": "I'd like to upgrade our plan and talk to someone about enterprise pricing."
}
```

**Response**
```json
{
  "intent": "upgrade_inquiry",
  "sentiment": "positive",
  "sentiment_confidence": 0.923,
  "crm_action": "create_opportunity",
  "reply": "I've flagged this as an upgrade inquiry and notified your account manager. Expect a follow-up within 24 hours.",
  "model_version": "distilbert-insightgreek-v2"
}
```

---

### `GET /leads` *(Manager / Admin only)*

Retrieve paginated leads with sentiment and scoring metadata.

**Request**
```
GET /leads?page=1&limit=20&risk_tier=high-value
Authorization: Bearer <token>
```

**Response**
```json
{
  "page": 1,
  "total": 142,
  "leads": [
    {
      "lead_id": "lead_8a3f92",
      "name": "Acme Corp",
      "conversion_probability": 0.847,
      "sentiment": "positive",
      "risk_tier": "high-value",
      "last_interaction": "2025-06-10T14:32:00Z"
    }
  ]
}
```

---

## Model Notes

The sentiment analysis model is a **DistilBERT** checkpoint fine-tuned on domain-specific CRM interaction data (customer emails, chat transcripts, support tickets). Training was performed locally using the HuggingFace `transformers` library and PyTorch before being pushed to Hugging Face Spaces.

| Model | Accuracy | Notes |
|---|---|---|
| **DistilBERT (fine-tuned)** | **85.4%** | Domain-specific CRM training data |
| VADER | ~68% | Rule-based, no fine-tuning |
| TextBlob | ~68% | Rule-based, no fine-tuning |

The current production path calls the hosted model via Hugging Face Inference API. This eliminates the `torch`/`transformers` dependency from the Flask server environment, reducing container size and cold-start latency for deployment on lightweight infrastructure.

---

## Roadmap

- [ ] Webhook support for real-time CRM event triggers
- [ ] Model A/B testing via feature flags
- [ ] Async task queue (Celery + Redis) for bulk lead scoring
- [ ] OpenAPI / Swagger documentation auto-generation
- [ ] Admin dashboard for model performance monitoring

---

## License

MIT License. See [LICENSE](LICENSE) for details.
