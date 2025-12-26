
### 📄 `README.md`


# 🔗 URL Shortener – Python FastAPI Interview Task

This is a simple, scalable URL shortening service built with **FastAPI**, **SQLModel**, and **Alembic**.

This project is part of a technical interview process and is designed to showcase:
- Clean architecture & maintainable code
- Performance & scalability considerations
- Logging and observability practices
- Experience with SQLAlchemy / SQLModel, Alembic, and REST APIs

---

## 🧩 Features

- Create short URLs (`POST /shorten`)
- Redirect to original URL (`GET /{short_code}`)
- Track and view visit statistics (`GET /stats/{short_code}`)
- Custom logging with middleware
- Modular and scalable codebase structure

---

## 🚀 Getting Started

### Quick Setup (Recommended)

For automated setup, activate your virtual environment and run:

```bash
pyenv activate Shorakka  # or: source venv/bin/activate
bash scripts/local_setup.sh
```

This will:
1. Install all dependencies
2. Create `.env` from `sample.env` (if needed)
3. Verify configuration and database connectivity
4. Run database migrations

---

### Manual Setup

### 1. Clone the repo

```bash
git clone https://github.com/mahdimmr/url-shortener.git
cd url-shortener
```

### 2. Activate virtual environment & install dependencies

If using `pyenv`:
```bash
pyenv activate Shorakka
pip install -r requirements.txt
```

Or create a new virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Setup environment variables

Copy `sample.env` to `.env` and configure for your local setup:

```bash
cp sample.env .env
```

Example `.env` configuration for local development:
```env
ENV_SETTING=dev
PG_DSN=postgresql+asyncpg://root:abcd%401234@127.0.0.1:5432/Shoraka
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_PRE_PING=true
DB_POOL_RECYCLE=3600
DB_ECHO=true
```

**Important Notes:**
- Use `postgresql+asyncpg://` driver for async operations
- URL-encode special characters in password (e.g., `@` → `%40`, `#` → `%23`)
- Ensure your PostgreSQL database exists before running migrations

### 4. Verify your setup (Bootstrap Check)

Run the automated bootstrap verification script to ensure everything is configured correctly:

```bash
python scripts/bootstrap_check.py
```

This will check:
- ✓ Settings configuration loads properly
- ✓ FastAPI app imports successfully
- ✓ Database connectivity works

**Expected output when successful:**
```
✓ All checks passed! Environment is ready.
  You can now run: uvicorn app.main:app --reload
```

If any checks fail, the script will provide troubleshooting guidance.

### 5. Run database migrations

Create initial migration:
```bash
alembic revision --autogenerate -m "init"
```

Apply migrations:
```bash
alembic upgrade head
```

### 6. Run the app

```bash
uvicorn app.main:app --reload
```

Open your browser at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Running Tests

```bash
pytest
```

---

## 📁 Project Structure

```
app/
├── api/           # FastAPI routers
├── core/          # Configuration, shared utilities
├── db/            # Models, session, CRUD, migrations
├── middleware/    # Logging or custom middleware
├── main.py        # FastAPI app entrypoint
```

---

## 📌 Notes for Interviewers

- The implementation is scoped to take ~1 working day.
- Logging is implemented using a custom middleware.
- Visit tracking is minimal; can be extended to store timestamps/user-agent/etc.
- Add any modules, files, or dependencies you find necessary.
- In short: you’re free to treat this as a real project.
- For production: add rate limiting, background jobs for analytics, async DB access, etc.
- We're more interested in how you think and structure your work than in having one "correct" answer. Good luck, and
  enjoy the process!

---

## 🧠 Bonus Ideas (if you have time)

- Custom short code support
- Expiration time for URLs
- Admin dashboard to view top URLs
- Dockerfile & deployment configs

---
