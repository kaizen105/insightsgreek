# 📊 InsightGreek-Brain CRM

**An AI-Powered Enterprise CRM prototype featuring dynamic NLP-driven sentiment analysis, intelligent lead scoring, and role-based access control, built with Next.js and Flask.**

[![Next.js](https://img.shields.io/badge/Next.js-14+-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Inference_API-FFD21E?style=flat-square&logo=huggingface&logoColor=black)](https://huggingface.co/inference-api)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)

---

## 🚀 Project Overview

**InsightGreek-Brain** is a full-stack, AI-first CRM designed to transform raw customer interactions into actionable insights. It couples a blazing-fast, modern Next.js frontend with a robust Python/Flask backend. 

Instead of relying on a monolithic, hardware-heavy local ML runtime, InsightGreek offloads its heavy lifting to the **Hugging Face Inference API**. This decoupled approach enables seamless consumption of advanced AI models (like fine-tuned `DistilBERT` for sentiment/lead scoring and `Qwen2.5-7B-Instruct` for the chatbot) directly via HTTP, making the application incredibly lightweight, easily deployable, and highly scalable.

Access control is rigidly enforced via a **3-tier JWT authentication system** (Developer, Manager, and Salesperson tiers). Data is durably persisted using an extensible **SQLite/PostgreSQL** backend.

---

## ✨ Key Features

- 🎯 **AI Lead Scoring** — Automatically scores inbound leads with confidence percentages to identify high-value prospects instantly.
- 💬 **Intelligent Chat Assistant (Fully Functional End-to-End)** — A persistent, floating AI Sales Coach chatbot built directly into the UI. It provides real-time pitch refinement, actionable next steps, and synthetic lead generation based on active user context, powered live by Qwen2.5.
- 📝 **Grammar & Feedback Analysis** — Processes raw customer feedback text for actionable sentiment classification (Positive/Neutral/Negative) and offers one-click grammar correction via LLM.
- 🎨 **Dynamic UI/UX** — Fully responsive frontend built with **Next.js App Router** and **Tailwind CSS**. Features smooth page transitions, glassmorphism components, interactive gradients, and real-time form validation.
- 🔒 **Role-Based Access Control (RBAC)** — Three distinct tiers of access:
  - **Salesperson**: Submit leads, analyze feedback, and use the AI coach.
  - **Manager**: View aggregated analytics, lead performance across the team, and qualitative visualizations.
  - **Developer**: Access system logs, API health, and model performance metrics.

---

## 🏗️ Architecture Overview

```mermaid
graph TD
    Client[Next.js Client UI] <-->|JSON over HTTP| Flask[Flask REST API]
    
    subgraph Frontend [Next.js App Router]
        SalesDashboard[Salesperson Dashboard]
        ManagerDashboard[Manager Dashboard]
        DevDashboard[Developer Dashboard]
        ChatWidget[Floating AI Chatbot]
    end
    
    subgraph Backend [Flask Server]
        Auth[JWT Auth & RBAC]
        LeadRouter[/api/submit-lead]
        FeedbackRouter[/api/analyze-feedback]
        ChatRouter[/api/chat]
    end
    
    subgraph External [Hugging Face Models]
        DistilBERT[DistilBERT Text Classification]
        Qwen[Qwen2.5-7B-Instruct LLM]
    end

    Client --> Frontend
    Frontend --> Auth
    Auth --> LeadRouter & FeedbackRouter & ChatRouter
    LeadRouter & FeedbackRouter --> DistilBERT
    ChatRouter --> Qwen
    
    Backend <--> Database[(SQLite / PostgreSQL)]
```

---

## 💻 Tech Stack

### Frontend
- **Framework**: Next.js (App Router, Turbopack)
- **Styling**: Tailwind CSS, PostCSS
- **State/Routing**: React Hooks, `useRouter`
- **Animations**: Custom Keyframe CSS & Tailwind utility classes

### Backend
- **Framework**: Python / Flask 2.x
- **Database**: SQLite (Dev) / PostgreSQL (Prod)
- **Authentication**: JSON Web Tokens (JWT)
- **Async Execution**: Python `threading` for background ML initialization

### Machine Learning & AI
- **LLM/Chatbot**: `Qwen/Qwen2.5-7B-Instruct`
- **Lead/Sentiment Classification**: `Kaizen696/my_lead_model` (distilbert-base-uncased via Gradio Client)
- **Inference**: Hugging Face Inference API / Gradio Client

---

## 🚀 Deployment

The recommended deployment architecture is a **Split Architecture** to maximize Next.js edge caching while running the heavy Python API safely in a server environment.

### 1. Deploy Backend to Render (or similar)
1. Push your repository to GitHub.
2. In Render, create a new **Web Service**.
3. Set the Root Directory to `backend/`.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app` (Make sure to add `gunicorn` to your requirements.txt).
6. Copy the resulting backend URL (e.g., `https://insightgreek-api.onrender.com`).

### 2. Deploy Frontend to Vercel
1. In Vercel, import your GitHub repository.
2. Set the Root Directory to `frontend/`.
3. The Build command and Output directory will be auto-detected by Vercel for Next.js.
4. **CRITICAL**: Since you aren't using `.env` variables for proxying currently, you'll need to update `next.config.ts` in production to proxy to your Render URL instead of `127.0.0.1:5000`.

---

## 🛠️ Local Development Setup

### 1. Prerequisites
- **Node.js** 18+ (for frontend)
- **Python** 3.10+ (for backend)

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** The backend automatically connects to Hugging Face APIs via `gradio_client` and `huggingface_hub`. No heavy local `torch` or `transformers` installations are required.

Start the backend:
```bash
python app.py
```
*The Flask server will start on `http://127.0.0.1:5000`.*

### 3. Frontend Setup

In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
*The Next.js server will start on `http://localhost:3000` and automatically proxy `/api/*` requests to the Flask backend on port 5000.*

---

## 🔮 Future Roadmap

- [ ] **Real-time WebSockets**: Upgrade the AI Chatbot to support streaming token generation.
- [x] **Advanced Data Visualization**: Add `Recharts` or `Chart.js` for Manager Dashboard analytics.
- [ ] **Dark Mode Toggle**: Implement dynamic theme switching with Tailwind's `dark:` classes.
- [ ] **OAuth2 Integration**: Add Google/GitHub SSO login.
- [ ] **Batch Processing**: Introduce Celery/Redis for bulk lead file uploads (CSV).

---

## 🌐 Status
*The application is fully functional end-to-end locally, with real live HTTP connections to both the Gradio DistilBERT endpoint and HuggingFace inference APIs for Qwen2.5. Deployments to Vercel (frontend) and Render (backend) are pending.*
```
