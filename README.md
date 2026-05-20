## Student Productivity Dashboard 

### What this is
- **Frontend**: React dashboard with charts + sortable history table
- **Backend**: Flask API with sessions + SQLite + ML model inference

### Quick start (development)

#### 1) Backend (Flask)
From repo root:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
set FLASK_DEBUG=1
set FLASK_SECRET_KEY=change-me
python backend\main.py
```

Backend runs at `http://localhost:5000`.

#### 2) Frontend (React)
From repo root:

```bash
cd frontend
npm install
set REACT_APP_API_BASE_URL=http://localhost:5000
npm start
```

Frontend runs at `http://localhost:3000`.

### Environment variables (recommended)
- **`FLASK_SECRET_KEY`**: required for secure sessions in production
- **`DATABASE_PATH`**: optional (defaults to `backend/users.db`)
- **`CORS_ORIGINS`**: comma-separated allowed frontend origins (default `http://localhost:3000`)
- **`REACT_APP_API_BASE_URL`**: API base URL for frontend (default `http://localhost:5000`)

### Production notes
- Set `FLASK_SECRET_KEY` to a strong value
- Set `CORS_ORIGINS` to your deployed frontend origin
- Run Flask behind a real WSGI server (e.g. gunicorn on Linux) and HTTPS

