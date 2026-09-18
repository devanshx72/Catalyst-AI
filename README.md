# Catalyst AI: AI-Powered Career Readiness Platform

**Catalyst AI**: Personalized Blueprint for Skill & Career — Ignited by AI Coaching & Intelligent Tutoring

Catalyst AI is an intelligent career acceleration platform designed to bridge the gap between academic learning and industry requirements. By combining personalized AI mentorship, multi-phase curriculum roadmaps, interactive streaming AI tutoring, and real-world project guidance, Catalyst AI equips students and self-learners to land their target engineering roles.

---

## 🚀 The Problem We're Solving

Despite abundant online resources, aspiring engineers face critical roadblocks:

- **Personalization Gap**: Standard curricula follow a rigid one-size-fits-all model.
- **Lack of Structured Guidance**: Learners waste months piecing together disparate tutorials without clear milestones.
- **Disconnect Between Learning & Industry**: Coursework rarely aligns with actual job requirements and interview expectations.
- **Limited Mentorship**: 1-on-1 industry guidance and portfolio reviews remain inaccessible to most students.

Catalyst AI solves this by delivering an adaptive, automated career blueprint tailored to each learner's background, dream companies, and available study hours.

---

## 🛠️ Key Features

### 🔍 Personalized Profile & Goal Tracking
- Comprehensive profile capturing target roles, dream companies, timeline durations, and technical background.
- Integration with GitHub repositories to contextualize project experience.
- Automated safeguards ensuring curriculum timelines adapt dynamically when target roles evolve.

### 🗺️ AI-Generated Career Roadmaps
- **4-Phase Milestone Architecture**: Progressively guides learners from Fundamentals to Core Technologies, Advanced Systems, and Capstone & Interview Preparation.
- **Weekly Schedule & Daily Tasks**: Generates 4-week actionable breakdowns for each phase with daily task checklists.
- **Progress Tracking**: Real-time task completion persistence and milestone progress visualization.

### 🤖 Interactive Streaming AI Tutor
- Module-specific tutoring retaining conversation history within each learning unit.
- **Real-Time Token Streaming**: Consumes Groq LLM completions token-by-token over Server-Sent Events (SSE) with sub-second time-to-first-token.
- **Curated Multi-Source Resource Hub**:
  - Educational videos via YouTube Data API v3
  - Academic research papers via Google Scholar (RapidAPI)
  - Curated engineering documentation via Google Custom Search

### 🦁 Career Coach Leo (Mistral AI)
- 24/7 intelligent career advisor analyzing candidate aspirations and portfolio repos.
- **Mandatory PII Redaction Pipeline**: Redacts and generalizes sensitive personal identifiers before formulating LLM prompts to ensure user privacy.
- Formats actionable advice with rendered HTML, bullet points, and code snippets, protected by strict DOMPurify XSS sanitization.
- Full conversation history with single-click history wipe controls.

### 📰 Tech News & Industry Discoveries
- Real-time engineering articles and tech blogs across 26 trending domains powered by the Medium RapidAPI integration.
- Topic search, category pill filtering, and paginated exploration.

---

## 🧠 Modern System Architecture

Catalyst AI is built as a decoupled, production-grade web application:

```
Catalyst-AI/
├── backend/                  # FastAPI Backend (Python 3.9+)
│   ├── app/
│   │   ├── core/             # Configuration, Database (Motor), Security (HMAC Sessions)
│   │   ├── routers/          # FastAPI Route Handlers (Auth, Profile, Roadmap, Tutor, Coach, Home)
│   │   ├── services/         # Business Logic, LLM Providers (Groq, Mistral), PII Redaction
│   │   ├── repositories/     # MongoDB Data Access Layer
│   │   └── schemas/          # Typed Pydantic v2 Request/Response Models
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # Next.js 16 (App Router, TypeScript, React 19)
│   ├── app/                  # App Router Pages ((auth), (app) dashboard, roadmap, tutor, coach)
│   ├── components/           # Reusable UI Components (Navbar, Sidebar)
│   ├── hooks/                # Client State Hooks (useAuth)
│   ├── lib/                  # Centralized Typed API Client & Auth Context
│   └── types/                # TypeScript Interface Contracts matching Backend Schemas
├── docs/                     # Architecture Plans, Migration Rules, Verification Checklists
└── tests/                    # Automated Test Suites
```

### Technology Stack
- **Frontend**: Next.js 16 (App Router), TypeScript, React 19, DOMPurify, CSS Design System (Glassmorphism / Dark Mode).
- **Backend**: FastAPI, Pydantic v2, Motor (Async MongoDB Driver), Uvicorn.
- **Database**: MongoDB.
- **Authentication**: HTTP-only, SameSite, Secure signed session cookies (HMAC-SHA256). No sensitive tokens stored in localStorage.
- **AI & LLM Services**:
  - **Groq Cloud** (`meta-llama/llama-4-scout-17b-16e-instruct`) for AI Tutor SSE streaming and structured learning plan generation.
  - **Mistral AI** (`open-mistral-nemo`) for Career Coach Leo with PII redaction.
- **External APIs**: Medium (RapidAPI), YouTube Data API v3, Google Scholar (RapidAPI), Google Custom Search API, GitHub REST API.

---

## ⚙️ Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+ and npm
- MongoDB running locally (default: `mongodb://localhost:27017`) or a MongoDB Atlas URI

---

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv ../venv
   source ../venv/bin/activate   # On Windows: ..\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables in `backend/.env`:
   ```ini
   MONGO_URI=mongodb://localhost:27017
   DB_NAME=catalyst_ai_db
   SECRET_KEY=generate-a-secure-random-secret-key-at-least-32-chars
   COOKIE_SECURE=false  # Set to true in production with HTTPS

   # LLM Providers (Fallbacks run cleanly if omitted)
   GROQ_API_KEY=your-groq-api-key
   GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
   MISTRAL_API_KEY=your-mistral-api-key
   MISTRAL_MODEL=open-mistral-nemo

   # Resource & Search APIs (Optional)
   YOUTUBE_API_KEY=your-youtube-api-key
   GOOGLE_SCHOLOR_API_KEY=your-rapidapi-scholar-key
   GOOGLE_CUSTOM_SEARCH_API_KEY=your-google-search-key
   GOOGLE_CUSTOM_SEARCH_CX=017576662512468239146:omuauf_lfve
   MEDIUM_API_KEY=your-medium-rapidapi-key
   ```

5. Start the FastAPI backend server:
   ```bash
   python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
   ```
   Interactive API documentation will be available at [http://localhost:8000/api/docs](http://localhost:8000/api/docs).

---

### 2. Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser. All API calls route automatically through Next.js rewrites to the FastAPI server at port 8000.

---

## 🧪 Testing & Verification

Run backend unit tests and verification suites:
```bash
# Run LLM utility and fallback tests
pytest tests/test_llm_utils.py

# Verify frontend production build
cd frontend && npm run build
```

---

## 💫 Impact & Purpose

Catalyst AI aligns directly with the **United Nations Sustainable Development Goal 4 (Quality Education)** by democratizing access to high-caliber career mentorship and technical education:

- **Empowering Underserved Learners**: Provides 24/7 personal coaching without requiring thousands of dollars in private bootcamp fees.
- **Career Transitioners**: Equips self-taught developers with structured milestones and verified curricula.
- **Privacy First**: Incorporates automated PII stripping so learners can benefit from state-of-the-art LLMs without exposing personal identifying data.

---

## 👤 Creators & Maintainers

- **Devansh Sharma**
- **Karunendra Dwivedy**
- **Pankhuri Agrawal**

---

## 🙏 Acknowledgements

- [Groq](https://groq.com/) for ultra-low latency LLM inference.
- [Mistral AI](https://mistral.ai/) for high-reasoning coaching models.
- [FastAPI](https://fastapi.tiangolo.com/) and [Next.js](https://nextjs.org/) for the modern application stack.
- [MongoDB](https://www.mongodb.com/) for flexible document storage.
