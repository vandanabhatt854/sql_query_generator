# QueryGenie

AI agentic assistant for natural language to SQL conversion, built for the "Building for Bharat with the Power of Agentic AI" hackathon.

## Modules

1. Prompt Processing Agent: normalizes the user prompt and classifies intent.
2. Schema Understanding Agent: reflects the SQLite schema on startup and exposes `/schema`.
3. Query Generation Agent: generates candidate SQL and validates against the live schema map.
4. Query Explanation Agent: returns structured explanations for each SQL candidate.
5. Query Impact Analyzer: estimates rows impacted or returned and flags risky operations.
6. Validation & Optimization Agent: blocks unsafe SQL, detects inefficient patterns, and suggests alternatives.
7. Selection & Execution Agent: lets the user choose a candidate and execute it safely.

## Setup

Backend:

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment

- `ANTHROPIC_API_KEY` is read from the backend environment only.
- `GOOGLE_API_KEY` can be set to enable Google Gemini via `LLM_PROVIDER=GOOGLE`.
- `SIMULATE_WRITES_ONLY=True` is enabled by default, so INSERT/UPDATE/DELETE are validated and previewed but not executed unless you explicitly disable it.

## Hackathon Fit

- Bharat-focused NL support includes `₹` currency normalization and examples such as salary, students, departments, and colleges.
- The demo uses SQLite locally, but the SQL emitted follows standard syntax that is compatible with MySQL/PostgreSQL style workflows.
- The architecture is agentic: each step of the pipeline is separated into a distinct module with clear responsibility.

## Security Measures

- SQL injection protection through single-statement validation and blocked dangerous keywords.
- UPDATE/DELETE guardrails require `WHERE` clauses.
- Write simulation mode is on by default.
- Rate limiting is enabled on `/generate` and `/execute`.
- Secrets stay server-side only and are never exposed to the frontend.
- User input is capped at 500 characters in both frontend and backend.
- History content is escaped before storage/display.
- Schema validation rejects hallucinated tables or columns.
- API errors are sanitized and do not expose stack traces or connection details.

## API

- `POST /generate`
- `POST /execute`
- `GET /schema`
- `GET /history`

