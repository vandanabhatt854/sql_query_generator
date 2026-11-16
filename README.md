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
python -m uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment

### English query understanding

The backend loads `backend/.env` regardless of its launch directory. To enable
broader natural-language requests, configure one provider and restart the backend:

```dotenv
LLM_PROVIDER=ANTHROPIC
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-sonnet-4-6
```

Or use Google:

```dotenv
LLM_PROVIDER=GOOGLE
GOOGLE_API_KEY=your_key_here
GOOGLE_MODEL=gemini-3.1-flash-lite
```

Keep keys in the backend environment, never frontend code or Git. Model names are
configurable to match your provider account. AI mode receives the current schema
and local date, asks for clarification when necessary, and checks generated SQL
against an in-memory copy of the schema before returning it. AI interpretation
can still be wrong; review the generated SQL and explanation before execution.

Without a key, local mode supports a bounded set of requests, including:

- `Calculate total salary`
- `What is the average salary in each department?`
- `Who earns the most?` (returns all employees tied for highest salary)
- `Show employees who joined last year` (previous calendar year in Asia/Kolkata)
- `Show all employees whose salary is greater than 50,000`
- `Get all students enrolled in Computer Science`

Unrecognized local requests ask the user to rephrase or enable AI mode; they never
silently become a query for all employees. Missing fields (such as letter grades,
which are absent from this demo) are reported explicitly. Provider failures do not
fall back to a different query. Structured errors use `detail.code` and
`detail.message`; `/generation-status` reports whether AI is configured (it does
not verify provider credentials). Query generation does not execute the query;
use **Execute Query** to fetch database results.

Run backend regression checks from the project root:

```bash
backend/.venv/Scripts/python.exe -m unittest discover -s backend/tests -v
```

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


## Local demo accounts and navigation

The navigation links open the generator, shared query history and live schema.
Register a local account to use the dashboard/profile. Passwords use salted
scrypt hashes; sessions expire after eight hours and use HttpOnly, SameSite=Strict
cookies. Accounts live in ignored `backend/accounts.db`, outside the queryable
schema. Logout revokes the current session. Accounts do not isolate the shared
demo tables/history, and the query endpoints remain available without login.

Use either `http://127.0.0.1:5173` or `http://localhost:5173` consistently.
The API defaults to the same hostname on port 8000. Custom frontend origins must
be listed in backend `ALLOWED_ORIGINS`. Deployments using HTTPS require
`COOKIE_SECURE=True`. This is a local demo, not a multi-user production service.
Email verification, password recovery, per-user database permissions, production
hosting and key rotation are outside the implemented demo.

Final checks: `backend/.venv/Scripts/python.exe -m unittest discover -s backend/tests -v`
and `npm.cmd run build` from `frontend`. API tests use isolated temporary databases
and mocked AI responses, without sending project data to a provider. Live Gemini
was verified separately with schema metadata and an approved sample request.
