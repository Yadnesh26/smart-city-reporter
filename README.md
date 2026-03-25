# Smart City Reporter

A civic issue reporting platform built with **FastAPI** and **SQLite**. Citizens can report local problems, upvote issues, and track resolution status — all through a clean web interface.

---

## Features

- **Public Feed** — Browse and search reported civic issues by area or status
- **Issue Submission** — Submit issues with title, description, area, optional photo, and GPS location
- **Upvoting** — Citizens can upvote issues to highlight urgency (session-based, no login needed)
- **Stats Dashboard** — Visual analytics with monthly trends, area breakdown, and KPIs
- **Admin Panel** — Secure login to manage, update, and resolve reported issues
- **Duplicate Detection** — Warns citizens before submitting a potentially duplicate issue
- **Auto Cleanup** — Resolved issues older than 60 days are automatically deleted on startup

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| Templating | Jinja2 |
| Database | SQLite |
| File Uploads | python-multipart |
| Sessions | itsdangerous (Starlette SessionMiddleware) |
| Container | Docker + Docker Compose |

---

## Getting Started

### Option 1 — Docker Compose (Recommended)

```bash
# Build and start
docker compose up --build

# Run in background
docker compose up --build -d

# Stop
docker compose down
```

### Option 2 — Run Locally

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload
```

App will be available at **http://localhost:8000**

---

## Project Structure

```
smart_city_reporter_sys/
├── main.py              # FastAPI app, all routes
├── crud.py              # Database queries (Create, Read, Update, Delete)
├── database.py          # DB connection and initialization
├── models.py            # Data models
├── analytics.py         # Analytics/stats helpers
├── schema.sql           # Database schema
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container build instructions
├── docker-compose.yml   # Multi-container orchestration
├── static/              # CSS, JS, uploaded images
└── templates/           # Jinja2 HTML templates
```

---

## Admin Access

| Field | Value |
|---|---|
| URL | `/login` |
| Username | `admin` |
| Password | `password` |

> **Note:** For viewing and demo purposes the credentials are provided.

---

## Data Persistence (Docker)

Docker volumes ensure your data survives container restarts:

- `civic_db` — SQLite database
- `civic_uploads` — User-uploaded images

---

## 🚀 Future Updates

Planned improvements for upcoming versions:

- **Smarter Duplicate Detection** — Move beyond keyword matching to semantic/NLP-based similarity checks for more accurate duplicate identification
- **Duplicate Image Detection** — Use image hashing or AI-based visual similarity to detect issues submitted with identical or near-identical photos
- **PostgreSQL Migration** — Replace SQLite with PostgreSQL for better scalability, concurrent access, and production-readiness
- **Separate DB & App Containers** — Restructure `docker-compose.yml` to run the app and database in separate containers for cleaner architecture and independent scaling
- **User Authentication** — Replace session-based anonymous voting with proper user accounts and role management
- **Email / SMS Notifications** — Notify citizens when their reported issue status changes
- **Mobile-Responsive UI** — Further optimize the interface for mobile devices
- **Issue Category Tags** — Add structured tags (e.g., Roads, Water, Electricity) for better filtering and reporting
- **Admin Analytics Export** — Allow admins to export stats and issue data as CSV/PDF reports
- **And many more...**

---

