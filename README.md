# Candivue: AI-Powered Adaptive Technical Interview Preparation & Evaluation System

> **Tagline:** *Know your gaps. Master your interviews.*

Candivue is a Python-first, desktop-optimized web application engineered to help college students excel in campus placement technical interviews. It provides adaptive mock interview sessions, transparent concept-based answer scoring, explainable recommendations, real-time analytics, and persistent SQLite history.

---

## 🌟 Key Features

1. **Authentication & User Isolation**
   - Secure password hashing using `bcrypt` (with standard PBKDF2-HMAC-SHA256 fallback).
   - Duplicate-email prevention and strict input validation.
   - User-specific session state and strict SQLite database isolation.

2. **Adaptive Technical Mock Interviews**
   - **5 Core Placement Subjects:** Python Programming, SQL, Object-Oriented Programming (OOP), Database Management Systems (DBMS), and Computer Networks.
   - **3 Difficulty Tiers:** Beginner, Intermediate, and Advanced.
   - Flexible lengths: 5, 10, or 15 questions per session.
   - Real-time progress bar, dynamic status indicators, and complete question reviews.

3. **Hybrid Answer Evaluation Engine**
   - **Guaranteed Offline Rule-Based Engine (Default):** Evaluates technical correctness, concept coverage, vocabulary overlap with reference answers, and formatting cues. Identifies both correctly explained and omitted concepts without requiring any external API key.
   - **Optional AI Integration:** Supports Google Gemini and OpenAI REST APIs when configured via environment variables or the user Settings panel. Automatically handles network timeouts, rate limits, and errors with seamless fallback to rule-based evaluation.

4. **Student Dashboard & Analytics**
   - **4 Metric Cards:** Questions Attempted, Average Score, Interviews Completed, and Focus Areas.
   - **Plotly Visualizations:** Interactive subject-wise bar charts, chronological score progression with rolling averages, and topic mastery matrices.
   - **Personalized Recommendations:** Detects weak topics (< 6.5/10), prioritizes missing concepts, recommends targeted practice, and offers cold-start onboarding.
   - **Motivational Quotes:** Handpicked inspiration for campus interview preparation.

5. **Visual Design & Dark / Light Mode**
   - Aesthetic inspired by modern educational platforms: deep plum and charcoal backgrounds in dark mode, warm off-white in light mode, with pastel pink (`#F9B8D0`), lavender (`#D8B4F8`), and soft yellow (`#FDE293`) accents.
   - Fully interactive Dark / Light mode toggle that dynamically restyles the interface, cards, and Plotly charts.

6. **Personal Project Management ("My Projects")**
   - Plan, track, and showcase personal development projects for placement portfolios.
   - Project dashboard with metrics: Total Projects, In Progress, Completed, and Overdue.
   - Comprehensive filtering by status, category, priority, and text search, plus sorting.
   - Milestone and task management per project with automatic progress calculation:
     $$\text{Progress} = (\text{completed tasks} / \text{total tasks}) \times 100$$
   - Overdue deadline tracking, tech stack tags, external GitHub / demo links, and detailed notes.
   - User-isolated database operations: students can only access and modify their own projects.

7. **Interview History & Archive**
   - Comprehensive log of past completed sessions with drill-down review into questions, candidate submissions, scores, feedback, and model answers.

---

## 🛠️ Technology Stack

- **Core Application & Logic:** Python 3.10+ (tested on Python 3.14)
- **Web UI & Navigation:** Streamlit
- **Persistence:** SQLite (`sqlite3`) with foreign key constraints, automated migrations, and user isolation
- **Data Analytics:** Pandas
- **Interactive Visualizations:** Plotly
- **Security:** Bcrypt / PBKDF2-HMAC-SHA256
- **Automated Testing:** Pytest

---

## 📁 Project Structure

```
CANDIVUE/
├── app.py                      # Streamlit main entry point and page router
├── requirements.txt            # Application dependencies
├── README.md                   # Comprehensive documentation
├── .env.example                # Configuration template
├── .gitignore                  # Git exclusions (db, cache, secrets)
├── .streamlit/
│   └── config.toml             # Streamlit server & theme defaults
├── data/
│   └── questions.json          # Curated multi-subject technical question bank
├── database/
│   ├── __init__.py
│   ├── db.py                   # SQLite DatabaseManager & CRUD operations
│   └── seed.py                 # Optional demo student profile seeder
├── services/
│   ├── __init__.py
│   ├── auth.py                 # Authentication, hashing, and validation
│   ├── evaluator.py            # Rule-based & optional AI answer evaluation
│   ├── recommendations.py      # Explainable recommendation engine
│   ├── analytics.py            # Metric aggregation & chart data preparation
│   └── projects.py             # Personal project & task management service
├── components/
│   ├── __init__.py
│   ├── styles.py               # Custom CSS injection, themes, metric cards, badges
│   └── charts.py               # Theme-aware Plotly charts
└── tests/
    ├── __init__.py
    ├── test_auth.py            # Tests for registration, hashing, and login
    ├── test_db.py              # Tests for SQLite schema, sessions, and isolation
    ├── test_evaluator.py       # Tests for answer scoring, partials, and irrelevance
    ├── test_recommendations.py # Tests for cold start and weak topic detection
    ├── test_projects.py        # Tests for project CRUD, task progress, and isolation
    └── test_e2e_flow.py        # End-to-end integration test of full interview lifecycle
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10 or higher installed.

### 2. Installation
Clone the repository and install the dependencies:
```bash
pip install -r requirements.txt
```

### 3. Running the Application
Launch the Streamlit app:
```bash
streamlit run app.py
```
Or alternatively:
```bash
python -m streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 🧪 Running Automated Tests

Run the complete test suite with verbose output:
```bash
pytest tests/ -v
```
Or via Python module:
```bash
python -m pytest tests/ -v
```

All 22 unit and integration tests verify:
- Registration, password hashing, and login.
- Duplicate email prevention and input validation.
- Database initialization, session lifecycle, and user data isolation.
- Answer evaluation: full credit, partial credit, and rejection of irrelevant/gibberish answers.
- Recommendation generation for both new and returning students.
- Personal project management: CRUD, task checklists, automatic progress calculation, and isolation.
- Complete end-to-end student interview and project lifecycles.

---

## ⚙️ Configuration & Optional AI Engine

Candivue works 100% out of the box with its built-in rule-based evaluation engine. No API key is required.

To enable optional AI-powered evaluations:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Set your Google Gemini or OpenAI API key:
   ```env
   GEMINI_API_KEY=your_key_here
   # OR
   OPENAI_API_KEY=your_key_here
   ```
3. Alternatively, enter the key directly inside the in-app **Settings** page.

---

## 💡 Quick Demo Credentials

For rapid inspection of a fully populated student dashboard with existing interview history, charts, and recommendations:
- **Email:** `demo@candivue.edu`
- **Password:** `candivue2026`

Or click the **"⚡ Sign in with Demo Account (Adam William)"** button on the login screen.

---

## ⚠️ Known Limitations
- The built-in rule-based evaluation relies on keyword/concept coverage and semantic token overlap; nuanced multi-sentence code logic is best assessed with the optional LLM mode enabled.
- SQLite is designed for single-node deployments; for high-concurrency multi-tenant cloud deployments, PostgreSQL can be plugged into `DatabaseManager`.
#   c a n d i v u e  
 #   c a n d i v u e  
 