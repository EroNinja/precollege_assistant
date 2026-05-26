# Precollege Assistant

An AI-assisted pre-college program recommendation system that helps high school students discover programs aligned with their academic interests, goals, budget, preferred format, location, academic background, and prior experience.

The application uses a guided chat-style intake flow to collect student preferences, normalizes messy free-text answers into structured profile fields, scores available programs using a transparent recommendation engine, and returns the top matched programs with human-readable explanations.

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Repository Structure](#repository-structure)
- [How the Application Works](#how-the-application-works)
- [Backend Deep Dive](#backend-deep-dive)
- [Frontend Deep Dive](#frontend-deep-dive)
- [Data Layer](#data-layer)
- [Normalization Pipeline](#normalization-pipeline)
- [Recommendation Engine](#recommendation-engine)
- [API Reference](#api-reference)
- [Setup and Installation](#setup-and-installation)
- [Running the Project](#running-the-project)
- [Example Usage Flow](#example-usage-flow)
- [Testing the Backend Manually](#testing-the-backend-manually)
- [Technical Decisions](#technical-decisions)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)
- [Tech Stack](#tech-stack)

---

## Overview

Precollege Assistant is a full-stack Python application for matching students with pre-college programs. The system acts like a lightweight AI counselor: it asks the student a sequence of guided questions, interprets free-text answers, builds a structured student profile, and recommends programs based on weighted fit criteria.

The project is intentionally designed as a hybrid AI system rather than a fully LLM-driven chatbot. The core matching logic is deterministic and explainable, while an optional local LLM fallback can be used only when rule-based and fuzzy matching are not confident enough.

This makes the system more predictable for educational advising use cases, where the user needs clear reasoning rather than vague chatbot output.

---

## Problem Statement

High school students often struggle to choose pre-college programs because program pages are scattered, requirements are inconsistent, and students may not know how to express their goals clearly. A student might say:

- "I want doctor stuff"
- "I like AI and coding"
- "summar program"
- "eastcoast"
- "2 weaks"
- "faculty help"

A normal search/filter UI expects clean inputs, but real students often provide informal, misspelled, partial, or ambiguous answers.

Precollege Assistant solves this by converting messy student language into canonical fields such as:

- `interest_area`
- `program_goal`
- `budget`
- `format`
- `location`
- `selectivity`
- `duration`
- `season`
- `grade_level`
- `support_type`
- `gpa_range`
- `coursework_level`
- `prior_experience`

Those structured fields are then used by the recommendation engine to rank pre-college programs and explain why each result fits the student.

---

## Key Features

### Guided student intake

The application loads a structured question flow from `data/questions/questions.json`. Each question has an ID, display text, target field, and allowed canonical options.

### Free-text answer normalization

Students do not need to pick from a dropdown. They can type natural answers, typos, synonyms, or short phrases. The backend normalizes those answers into canonical values.

Example mappings:

| Raw student input | Normalized value |
|---|---|
| `doctor`, `med`, `medical field` | `medicine` |
| `cs`, `coding`, `building apps` | `computer science` |
| `ai`, `genai`, `llms` | `artificial intelligence` |
| `eastcoast`, `Boston`, `MIT` | `East Coast` |
| `summar`, `july`, `summer break` | `summer` |
| `ap`, `ib`, `honors` | `honors / AP / IB level` |

### Hybrid rule-based + fuzzy + optional LLM pipeline

The backend normalizer checks answers using this order:

1. Exact canonical match
2. Exact synonym match
3. Substring synonym match
4. Fuzzy string similarity match
5. Optional local LLM fallback through Ollama

This keeps the system fast and predictable for common inputs while still allowing fallback handling for difficult answers.

### Explainable recommendations

The recommendation engine does not only return program names. It also returns `reasons` and `reasons_text`, such as:

- `strong match with your interest`
- `aligned with your goal`
- `fits your budget`
- `matches preferred format`
- `good academic fit`
- `coursework level matches`
- `experience level matches`

### Reflex-based frontend

The frontend is built with Reflex and presents the experience as a chat-style counseling interface. It includes:

- Navigation bar
- Hero section
- Guided chat panel
- Student profile summary
- Recommendation cards
- Featured program sections for Biomedical / Pre-Health, Computer Science / AI, and Business / Entrepreneurship

### Data-driven design

The question flow, synonym mappings, and program catalog are stored in data files instead of being hard-coded into backend routes. This makes the recommendation behavior easier to update without rewriting application logic.

---

## System Architecture

```text
User
  |
  v
Reflex Frontend
  |
  |  GET /api/chat/questions
  |  POST /api/chat/answer
  |  POST /api/recommend/
  v
Flask Backend
  |
  +--> Question Loader
  |       reads data/questions/questions.json
  |
  +--> Normalization Service
  |       reads data/mappings/option_maps.json
  |       applies exact, synonym, substring, fuzzy, and optional LLM fallback matching
  |
  +--> Recommendation Service
  |       reads data/programs/programs.csv
  |       scores programs against the normalized student profile
  |
  v
Ranked Program Recommendations
  |
  v
Frontend Recommendation Cards
```

---

## Repository Structure

```text
precollege_assistant/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/
│   │   ├── routes/
│   │   │   ├── chat.py
│   │   │   └── recommend.py
│   │   ├── services/
│   │   │   ├── normalizer.py
│   │   │   └── recommender.py
│   │   └── utils/
│   │       └── helpers.py
│   ├── config.py
│   ├── requirements.txt
│   └── run.py
│
├── data/
│   ├── mappings/
│   │   └── option_maps.json
│   ├── programs/
│   │   └── programs.csv
│   └── questions/
│       └── questions.json
│
├── frontend/
│   ├── uiapp/
│   │   └── uiapp.py
│   ├── app.py
│   ├── requirements.txt
│   └── rxconfig.py
│
├── .gitignore
└── README.md
```

---

## How the Application Works

### 1. Frontend loads the question flow

When the user clicks **Load Questions**, the Reflex frontend calls:

```text
GET http://127.0.0.1:5000/api/chat/questions
```

The backend loads `questions.json` and returns the ordered intake questions.

### 2. User answers one question at a time

The frontend stores the current question index in the Reflex `State` class. When the student submits an answer, the frontend sends:

```json
{
  "question_id": "interest_area",
  "user_text": "I like coding and AI"
}
```

### 3. Backend normalizes the answer

The backend normalizer cleans the input, compares it against canonical options and synonyms, applies fuzzy matching if needed, and optionally calls an Ollama model if no deterministic match is strong enough.

The backend returns a structured field:

```json
{
  "question_id": "interest_area",
  "raw_text": "I like coding and AI",
  "cleaned_text": "I like coding and AI",
  "structured_fields": {
    "normalized_value": "computer science",
    "confidence": 0.9
  },
  "next_step": "placeholder"
}
```

### 4. Frontend builds a student profile

The frontend stores normalized answers inside `profile`:

```json
{
  "interest_area": "computer science",
  "program_goal": "hands-on projects",
  "budget": "moderate cost is okay",
  "format": "online only",
  "location": "remote only",
  "gpa_range": "3.8+",
  "coursework_level": "honors / AP / IB level",
  "prior_experience": "some experience"
}
```

### 5. User requests recommendations

After the guided flow is complete, the frontend calls:

```text
POST http://127.0.0.1:5000/api/recommend/
```

with the structured profile.

### 6. Backend ranks programs

The recommender reads `programs.csv`, scores each program against the profile, sorts programs by descending score, and returns the top 3 recommendations.

---

## Backend Deep Dive

The backend is a Flask application organized around application factory initialization, route blueprints, service modules, and data-loading utilities.

### `backend/run.py`

Entry point for the Flask backend.

Responsibilities:

- Imports `create_app()` from the backend application package
- Creates the Flask app instance
- Runs the development server on port `5000`

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

### `backend/app/__init__.py`

Defines the Flask application factory.

Responsibilities:

- Creates the Flask app
- Enables CORS through `flask_cors.CORS`
- Registers the chat blueprint under `/api/chat`
- Registers the recommendation blueprint under `/api/recommend`
- Exposes a health-check endpoint at `/api/health`

Registered route groups:

```text
/api/chat
/api/recommend
/api/health
```

The health endpoint returns:

```json
{
  "status": "ok",
  "message": "Backend is running"
}
```

### `backend/app/routes/chat.py`

Handles question loading and answer normalization.

#### `GET /api/chat/questions`

Loads the intake questions using `load_questions()` and returns:

```json
{
  "questions": [ ... ]
}
```

#### `POST /api/chat/answer`

Accepts one answer at a time:

```json
{
  "question_id": "interest_area",
  "user_text": "I want to do medicine"
}
```

Then calls:

```python
normalize_answer(question_id, user_text)
```

and returns the normalized result.

### `backend/app/routes/recommend.py`

Handles recommendation generation.

#### `POST /api/recommend/`

Accepts a completed student profile:

```json
{
  "profile": {
    "interest_area": "medicine",
    "program_goal": "research experience",
    "budget": "moderate cost is okay",
    "format": "in-person only",
    "location": "West Coast"
  }
}
```

Then calls:

```python
recommend_programs(profile)
```

and returns:

```json
{
  "recommendations": [ ... ]
}
```

### `backend/app/utils/helpers.py`

Centralized data-loading helper module.

Responsibilities:

- Resolves the backend project root using `pathlib.Path`
- Loads question definitions from JSON
- Loads synonym/canonical option maps from JSON
- Loads program records from CSV using pandas

Functions:

```python
def load_questions():
    ...

def load_option_maps():
    ...

def load_programs():
    ...
```

This separates file I/O from route and service logic.

### `backend/app/services/normalizer.py`

The normalization service is one of the most important parts of the system. It converts raw student text into canonical answer values.

Core functions:

```python
def clean_text(text: str) -> str
```

Lowercases text, strips whitespace, removes unsupported characters, and collapses repeated spaces.

```python
def similarity(a: str, b: str) -> float
```

Uses Python's `SequenceMatcher` to compute fuzzy similarity between the cleaned input and known canonical/synonym candidates.

```python
def get_question_config(question_id: str) -> dict
```

Finds the question configuration from `questions.json` for a given question ID.

```python
def llm_fallback(question_id: str, user_text: str) -> dict
```

Optionally uses a local Ollama model to classify ambiguous input into one allowed canonical option.

```python
def normalize_answer(question_id: str, user_text: str) -> dict
```

Main normalization function used by the API route.

### `backend/app/services/recommender.py`

The recommender scores each program against the structured profile.

Core functions:

```python
def score_program(program, profile):
    ...
```

Calculates a numeric score and list of explanation reasons.

```python
def recommend_programs(profile):
    ...
```

Loads all programs, scores each one, sorts them by score, and returns the top 3.

---

## Frontend Deep Dive

The frontend is built with Reflex, a Python UI framework. The main frontend logic lives in:

```text
frontend/uiapp/uiapp.py
```

### State management

The Reflex `State` class stores the full UI state:

```python
class State(rx.State):
    questions: list[dict] = []
    current_question_index: int = 0
    user_input: str = ""
    chat_history: list[dict] = []
    loading_questions: bool = False
    profile: dict = {}
    recommendations: list[dict] = []
```

Important state variables:

| State field | Purpose |
|---|---|
| `questions` | Stores loaded question flow from backend |
| `current_question_index` | Tracks which question the user is answering |
| `user_input` | Stores current text input |
| `chat_history` | Stores assistant and user chat bubbles |
| `profile` | Stores normalized answers by question ID |
| `recommendations` | Stores backend recommendation results |

### Main frontend methods

#### `load_questions()`

Calls the Flask backend to load the intake question flow. It resets the UI state, clears previous recommendations, and starts the chat with the first question.

#### `send_answer()`

Sends the current answer to `/api/chat/answer`, receives the normalized value, updates `profile`, advances the question index, and appends the next question to the chat history.

#### `get_recommendations()`

Sends the completed `profile` to `/api/recommend/` and stores the returned recommendations.

#### `profile_summary`

A computed Reflex variable that formats the structured student profile into a readable summary such as:

```text
Interest: medicine | Goal: research experience | Budget: moderate cost is okay | Format: in-person only
```

### UI components

The frontend is broken into reusable component functions:

| Component | Purpose |
|---|---|
| `navbar()` | Top navigation section |
| `hero_section()` | Main marketing-style headline |
| `chat_panel()` | Main guided Q&A interface |
| `chat_bubble()` | Renders assistant/user messages |
| `sample_question_card()` | Shows clickable sample prompts |
| `recommendation_card()` | Displays one recommended program |
| `recommendations_panel()` | Displays the final recommendation list |
| `featured_program_card()` | Shows featured static program cards |
| `featured_section()` | Groups featured programs by category |
| `index()` | Main page layout |

---

## Data Layer

The application uses simple local data files instead of a database.

### `data/questions/questions.json`

Defines the guided intake flow.

Each question object contains:

```json
{
  "id": "interest_area",
  "text": "What subjects, careers, or areas are you most interested in?",
  "field": "interests",
  "options": ["medicine", "computer science", "business"]
}
```

The current question flow covers:

- Interest area
- Program goal
- Budget
- Format
- Location
- Selectivity
- Duration
- Season
- Grade level
- Support type
- GPA range
- Coursework level
- Prior experience

### `data/mappings/option_maps.json`

Maps each canonical option to synonyms, paraphrases, common terms, and typo-tolerant phrases.

Example structure:

```json
{
  "interest_area": {
    "medicine": ["doctor", "medical", "hospital", "physician"],
    "computer science": ["cs", "coding", "programming", "software"],
    "artificial intelligence": ["ai", "genai", "llms"]
  }
}
```

This file is the foundation of the rule-based normalization layer.

### `data/programs/programs.csv`

Stores the program catalog used by the recommendation engine.

The recommender expects program fields such as:

| Field | Used for |
|---|---|
| `name` / `Program Name` / `program_name` | Displaying the program name |
| `description` / `Description` | Displaying program description |
| `interests` | Matching against `interest_area` |
| `goals` | Matching against `program_goal` |
| `budget` | Matching against budget preference |
| `format` | Matching against online/in-person preference |
| `location_preference` / `location` | Matching against location preference |
| `recommended_gpa_range` | Matching academic fit |
| `coursework_background_expected` | Matching coursework preparation |
| `prior_experience_expected` | Matching experience level |
| `source_type` | Adds a small boost for real programs |

---

## Normalization Pipeline

The system is designed to normalize student answers before recommendation. This is important because the recommender expects clean canonical values, while users often type informal free text.

### Step 1: Clean input

The raw input is lowercased, stripped, and cleaned using regular expressions.

```text
"I want to do AI!!!" -> "i want to do ai"
```

### Step 2: Exact canonical match

If the cleaned user input exactly matches a canonical option, the system returns it with high confidence.

Example:

```text
Input: medicine
Output: medicine
Confidence: 0.99
Method: exact_canonical
```

### Step 3: Exact synonym match

If the input exactly matches a synonym, the system maps it to the canonical value.

Example:

```text
Input: doctor
Output: medicine
Confidence: 0.95
Method: exact_synonym
```

### Step 4: Substring synonym match

If a synonym appears inside a longer user answer, the system still maps it correctly.

Example:

```text
Input: I want to work in a hospital
Output: medicine
Confidence: 0.90
Method: substring_synonym
```

### Step 5: Fuzzy matching

If no exact or substring match is found, the system compares the input against all canonical options and synonyms using string similarity.

The fuzzy threshold is adaptive:

| Input length | Fuzzy threshold |
|---|---:|
| 8 characters or fewer | 0.72 |
| 15 characters or fewer | 0.78 |
| Longer inputs | 0.84 |

This helps catch short typo-style inputs such as:

```text
nirse -> nursing
summar -> summer
juniar -> junior high school
facultiy -> faculty mentorship
```

### Step 6: Optional LLM fallback

If deterministic matching fails, the system can optionally call a local Ollama model:

```text
llama3.1:8b
```

The LLM is used as a strict classifier. It receives:

- Question ID
- Question text
- Allowed canonical options
- Synonym hints
- User answer

The model is instructed to return exactly one allowed option or `null`.

This fallback is intentionally last in the pipeline so that predictable matching handles most cases.

---

## Recommendation Engine

The recommendation system is implemented in `backend/app/services/recommender.py`.

It uses a transparent weighted scoring model. Each program receives points based on how well it matches the normalized student profile.

### Scoring logic

| Criterion | Score impact | Explanation reason |
|---|---:|---|
| Interest match | `+4` | `strong match with your interest` |
| Interest mismatch | `-2` | No reason added |
| Goal match | `+3` | `aligned with your goal` |
| Budget match | `+1` | `fits your budget` |
| Format match | `+1` | `matches preferred format` |
| Location match | `+1` | `matches location preference` |
| GPA match | `+2` | `good academic fit` |
| GPA mismatch | `-1` | No reason added |
| Coursework match | `+1` | `coursework level matches` |
| Prior experience match | `+1` | `experience level matches` |
| Real program source | `+0.5` | Ranking boost only |

### Why this design works

The scoring model is simple, inspectable, and easy to tune. For an educational advising prototype, this is preferable to an opaque model because the user can understand why a program was recommended.

### Output format

Each recommendation contains:

```json
{
  "name": "Example Program",
  "score": 8.5,
  "reasons": [
    "strong match with your interest",
    "aligned with your goal",
    "good academic fit"
  ],
  "reasons_text": "strong match with your interest, aligned with your goal, good academic fit",
  "description": "Program description here"
}
```

The backend returns only the top 3 programs after sorting by score.

---

## API Reference

### Health check

```http
GET /api/health
```

Response:

```json
{
  "status": "ok",
  "message": "Backend is running"
}
```

---

### Load questions

```http
GET /api/chat/questions
```

Response:

```json
{
  "questions": [
    {
      "id": "interest_area",
      "text": "What subjects, careers, or areas are you most interested in?",
      "field": "interests",
      "options": ["medicine", "computer science", "business"]
    }
  ]
}
```

---

### Normalize one answer

```http
POST /api/chat/answer
Content-Type: application/json
```

Request:

```json
{
  "question_id": "interest_area",
  "user_text": "I want to become a doctor"
}
```

Response:

```json
{
  "question_id": "interest_area",
  "raw_text": "I want to become a doctor",
  "cleaned_text": "I want to become a doctor",
  "structured_fields": {
    "normalized_value": "medicine",
    "confidence": 0.9
  },
  "next_step": "placeholder"
}
```

---

### Generate recommendations

```http
POST /api/recommend/
Content-Type: application/json
```

Request:

```json
{
  "profile": {
    "interest_area": "medicine",
    "program_goal": "research experience",
    "budget": "moderate cost is okay",
    "format": "in-person only",
    "location": "West Coast",
    "gpa_range": "3.8+",
    "coursework_level": "honors / AP / IB level",
    "prior_experience": "some experience"
  }
}
```

Response:

```json
{
  "recommendations": [
    {
      "name": "Example Pre-College Program",
      "score": 9.5,
      "reasons": [
        "strong match with your interest",
        "aligned with your goal",
        "good academic fit"
      ],
      "reasons_text": "strong match with your interest, aligned with your goal, good academic fit",
      "description": "Example program description."
    }
  ]
}
```

---

## Setup and Installation

### Prerequisites

- Python 3.10+
- pip
- Optional: Ollama, if you want local LLM fallback behavior
- Git

---

## Running the Project

Clone the repository:

```bash
git clone https://github.com/EroNinja/precollege_assistant.git
cd precollege_assistant
```

### 1. Run the backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

On macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the Flask backend:

```bash
python run.py
```

The backend should run at:

```text
http://127.0.0.1:5000
```

Check health:

```bash
curl http://127.0.0.1:5000/api/health
```

Expected response:

```json
{
  "status": "ok",
  "message": "Backend is running"
}
```

---

### 2. Run the frontend

Open a new terminal from the repository root:

```bash
cd frontend
python -m venv .venv
```

Activate the virtual environment.

On macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Reflex app:

```bash
reflex run
```

The frontend is configured as a Reflex app named `uiapp`. The frontend code points to the Flask backend at:

```python
BACKEND_URL = "http://127.0.0.1:5000"
```

Make sure the Flask backend is running before using the frontend.

---

## Optional Ollama Setup

The app can run without Ollama. If Ollama is not installed or the model is unavailable, the normalizer falls back to deterministic matching and returns a low-confidence unavailable result only when matching fails.

To enable the LLM fallback:

```bash
ollama pull llama3.1:8b
```

Then keep Ollama running locally while using the app.

The configured model name is:

```python
OLLAMA_MODEL = "llama3.1:8b"
```

---

## Example Usage Flow

1. Start the Flask backend.
2. Start the Reflex frontend.
3. Open the frontend in the browser.
4. Click **Load Questions**.
5. Answer the guided questions in natural language.
6. The backend normalizes each answer into a structured profile field.
7. When the question flow is complete, click **Get Recommendations**.
8. Review the top recommended programs and explanation reasons.

Example answers:

```text
Interest: I want to do AI and coding
Goal: hands on projects
Budget: moderate is okay
Format: online
Location: remote
Season: summer
Grade: junior
Support: faculty help
GPA: 3.8
Coursework: AP level
Experience: a few projects
```

Possible structured profile:

```json
{
  "interest_area": "artificial intelligence",
  "program_goal": "hands-on projects",
  "budget": "moderate cost is okay",
  "format": "online only",
  "location": "remote only",
  "season": "summer",
  "grade_level": "junior high school",
  "support_type": "faculty mentorship",
  "gpa_range": "3.8+",
  "coursework_level": "honors / AP / IB level",
  "prior_experience": "some experience"
}
```

---

## Testing the Backend Manually

### Health check

```bash
curl http://127.0.0.1:5000/api/health
```

### Load questions

```bash
curl http://127.0.0.1:5000/api/chat/questions
```

### Normalize an answer

```bash
curl -X POST http://127.0.0.1:5000/api/chat/answer \
  -H "Content-Type: application/json" \
  -d '{"question_id":"interest_area","user_text":"I like coding and AI"}'
```

### Generate recommendations

```bash
curl -X POST http://127.0.0.1:5000/api/recommend/ \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "interest_area": "computer science",
      "program_goal": "hands-on projects",
      "budget": "moderate cost is okay",
      "format": "online only",
      "location": "remote only",
      "gpa_range": "3.8+",
      "coursework_level": "honors / AP / IB level",
      "prior_experience": "some experience"
    }
  }'
```

---

## Technical Decisions

### Rule-based normalization before LLM fallback

The system does not send every answer directly to an LLM. Instead, it first uses exact matching, synonym matching, substring matching, and fuzzy matching. This reduces latency, avoids unnecessary model calls, and makes results more predictable.

### Structured profile instead of freeform conversation memory

The frontend builds a clean dictionary of normalized fields. This makes the recommendation step simple, debuggable, and testable.

### Transparent scoring instead of black-box ranking

The recommender uses explicit weights. This makes it easy to explain why a program was recommended and easy to tune the scoring model later.

### File-based data layer

The current version uses JSON and CSV files. This keeps the prototype lightweight and easy to run locally without setting up a database.

### Human-readable reasons

Each score contribution can produce a reason. This turns the recommender from a simple ranked list into an explainable advising tool.

---

## Limitations

- The current backend uses local JSON/CSV files rather than a persistent database.
- The scoring model is heuristic-based and does not learn from user feedback yet.
- The frontend and backend are configured for local development.
- The LLM fallback depends on local Ollama availability and the configured model.
- The recommendation quality depends heavily on the completeness and accuracy of `programs.csv` and `option_maps.json`.
- The current API returns a `next_step` placeholder from the answer route, so dynamic branching is not implemented yet.
- Program ranking currently returns the top 3 only.

---

## Future Improvements

- Add automated unit tests for normalization edge cases.
- Add tests for recommendation scoring and ranking behavior.
- Add a database layer for storing users, profiles, and saved recommendations.
- Add an admin interface for updating questions, option maps, and program records.
- Add richer program metadata such as deadlines, tuition, eligibility, application links, and institution names.
- Add feedback collection so users can mark recommendations as useful or not useful.
- Add semantic search over program descriptions.
- Add authentication for saved student profiles.
- Add deployment configuration for cloud hosting.
- Add analytics for common student interests and unmatched inputs.
- Add confidence display for debugging or admin mode.
- Add stricter validation for profile fields before recommendation.

---

## Tech Stack

### Backend

- Python
- Flask
- Flask-CORS
- pandas
- difflib / SequenceMatcher
- Regex-based text cleaning
- Optional Ollama local LLM fallback

### Frontend

- Python
- Reflex
- Requests

### Data

- JSON question definitions
- JSON canonical option and synonym maps
- CSV program catalog

### AI / Recommendation Logic

- Rule-based matching
- Synonym matching
- Fuzzy string matching
- Optional local LLM classification
- Weighted explainable recommendation scoring

---

## Summary

Precollege Assistant demonstrates a practical AI-assisted recommendation workflow for education advising. It combines a guided frontend experience, structured backend APIs, robust answer normalization, transparent scoring, and explainable recommendation output.

The project is strongest as a prototype of a real counseling assistant because it avoids relying entirely on generative AI. Instead, it uses deterministic logic where possible, optional AI fallback where useful, and clear scoring rules so the final recommendations remain understandable and auditable.
