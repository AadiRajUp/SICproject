import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any
from uuid import uuid4

import bcrypt
from flask import Flask, jsonify, request, session
from flask_cors import CORS

from model.predict_model import model_predict


@dataclass(frozen=True)
class AppConfig:
    secret_key: str
    database_path: Path
    cors_origins: list[str]
    debug: bool


def load_config() -> AppConfig:
    secret = os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY") or "dev-insecure-secret"
    db = Path(os.environ.get("DATABASE_PATH") or Path(__file__).with_name("users.db"))
    origins_raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
    origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
    debug = (os.environ.get("FLASK_DEBUG") == "1") or (os.environ.get("DEBUG") == "1")
    return AppConfig(secret_key=secret, database_path=db, cors_origins=origins, debug=debug)


CONFIG = load_config()

logging.basicConfig(
    level=logging.DEBUG if CONFIG.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

app = Flask(__name__)
app.secret_key = CONFIG.secret_key

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=not CONFIG.debug,
)

CORS(
    app,
    supports_credentials=True,
    origins=CONFIG.cors_origins,
)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(CONFIG.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def json_error(message: str, status: int = 400, *, code: str | None = None):
    payload: dict[str, Any] = {"error": message}
    if code:
        payload["code"] = code
    return jsonify(payload), status


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return json_error("Unauthorized", 401, code="UNAUTHORIZED")
        return func(*args, **kwargs)

    return wrapper


@app.get("/")
def home():
    return jsonify({"message": "Flask API running"})


@app.get("/api/me")
def me():
    if "user_id" not in session:
        return jsonify({"authenticated": False})
    return jsonify({"authenticated": True, "user_name": session.get("user_name")})


def _hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def _check_password(stored: str, candidate: str) -> bool:
    if stored.startswith("$2a$") or stored.startswith("$2b$") or stored.startswith("$2y$"):
        return bcrypt.checkpw(candidate.encode("utf-8"), stored.encode("utf-8"))
    return stored == candidate


@app.post("/api/signup")
def signup():
    data = request.get_json(silent=True) or {}

    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "")

    if not full_name:
        return json_error("Full name is required")
    if "@" not in email or "." not in email:
        return json_error("Valid email is required")
    if len(password) < 4:
        return json_error("Password must be at least 4 characters")

    uid = f"USR-{uuid4().hex[:12].upper()}"
    password_hash = _hash_password(password)

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (uid, full_name, email, password) VALUES (?, ?, ?, ?)",
                (uid, full_name, email, password_hash),
            )
    except sqlite3.IntegrityError:
        return json_error("User already exists", 400, code="USER_EXISTS")

    return jsonify({"message": "Signup successful"})


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return json_error("Email and password are required")

    with get_db() as conn:
        user = conn.execute(
            "SELECT id, full_name, password FROM users WHERE email = ?",
            (email,),
        ).fetchone()

        if not user or not _check_password(user["password"], password):
            return json_error("Invalid credentials", 401, code="INVALID_CREDENTIALS")

        if not (user["password"].startswith("$2a$") or user["password"].startswith("$2b$") or user["password"].startswith("$2y$")):
            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (_hash_password(password), user["id"]),
            )

    session["user_id"] = int(user["id"])
    session["user_name"] = user["full_name"]

    return jsonify({"message": "Login successful", "user_name": user["full_name"]})


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


def _parse_days_param(value: str | None) -> int | None:
    if value is None or value == "" or value.lower() == "all":
        return None
    try:
        days = int(value)
    except ValueError:
        return -1
    if days <= 0 or days > 3650:
        return -1
    return days


@app.post("/api/today-data")
@login_required
def today_data():
    data = request.get_json(silent=True) or {}
    activity_date = datetime.now().date().isoformat()

    try:
        study_hours = float(data.get("study_hours"))
        focus_score = int(data.get("focus_score"))
        sleep_hours = float(data.get("sleep_hours"))
        phone_usage_hours = float(data.get("phone_usage_hours"))
    except (TypeError, ValueError):
        return json_error("Invalid payload: numbers required for all fields")

    if study_hours < 0 or study_hours > 24:
        return json_error("Study hours must be between 0 and 24")
    if focus_score < 0 or focus_score > 100:
        return json_error("Focus score must be between 0 and 100")
    if sleep_hours < 0 or sleep_hours > 24:
        return json_error("Sleep hours must be between 0 and 24")
    if phone_usage_hours < 0 or phone_usage_hours > 24:
        return json_error("Phone usage must be between 0 and 24")

    input_values = [study_hours, focus_score, sleep_hours, phone_usage_hours]
    score = float(model_predict(input_values))

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO daily_productivity (
                user_id, activity_date,
                study_hours, focus_score,
                sleep_hours, phone_usage_hours, score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, activity_date)
            DO UPDATE SET
                study_hours=excluded.study_hours,
                focus_score=excluded.focus_score,
                sleep_hours=excluded.sleep_hours,
                phone_usage_hours=excluded.phone_usage_hours,
                score=excluded.score
            """,
            (
                session["user_id"],
                activity_date,
                study_hours,
                focus_score,
                sleep_hours,
                phone_usage_hours,
                score,
            ),
        )

    return jsonify({"message": "Data saved successfully", "score": round(score, 2)})


def _fetch_series(user_id: int, *, days: int | None):
    where = "WHERE user_id=?"
    params: list[Any] = [user_id]
    if days is not None:
        cutoff = (date.today() - timedelta(days=days - 1)).isoformat()
        where += " AND activity_date >= ?"
        params.append(cutoff)

    with get_db() as conn:
        rows = conn.execute(
            f"""
            SELECT activity_date,
                   study_hours,
                   focus_score,
                   sleep_hours,
                   phone_usage_hours,
                   score
            FROM daily_productivity
            {where}
            ORDER BY activity_date ASC
            """,
            tuple(params),
        ).fetchall()

    return rows


def _mean(nums: list[float]) -> float:
    return sum(nums) / len(nums) if nums else 0.0


def _personal_recommendations(rows: list) -> list[dict[str, Any]]:
    """
    Rule-based + one optional model hint from the user's own logged series.
    Each item: id, title, detail, priority (high|medium|low), category.
    """
    if not rows:
        return []

    study = [float(r["study_hours"]) for r in rows]
    focus = [float(r["focus_score"]) for r in rows]
    sleep = [float(r["sleep_hours"]) for r in rows]
    phone = [float(r["phone_usage_hours"]) for r in rows]
    scores = [float(r["score"]) for r in rows]

    n = len(rows)
    avg_study = _mean(study)
    avg_focus = _mean(focus)
    avg_sleep = _mean(sleep)
    avg_phone = _mean(phone)

    last = rows[-1]
    ls = float(last["study_hours"])
    lf = int(last["focus_score"])
    lz = float(last["sleep_hours"])
    lp = float(last["phone_usage_hours"])

    recs: list[tuple[int, dict[str, Any]]] = []

    def add(score: int, item: dict[str, Any]) -> None:
        recs.append((score, item))

    if avg_sleep < 6.5:
        add(
            90,
            {
                "id": "sleep_low_avg",
                "title": "Protect your sleep",
                "detail": f"Your average sleep is about {avg_sleep:.1f}h in this period. Most people sustain focus better with roughly 7–9 hours. Try a fixed bedtime for two weeks.",
                "priority": "high",
                "category": "sleep",
            },
        )
    elif lz < 6.0:
        add(
            85,
            {
                "id": "sleep_last_short",
                "title": "Last night looked short",
                "detail": f"You logged {lz:.1f}h sleep on your latest day. Prioritizing sleep tonight can lift tomorrow's focus and score.",
                "priority": "high",
                "category": "sleep",
            },
        )

    if avg_phone >= 3.5 or lp >= 4.0:
        add(
            88,
            {
                "id": "phone_high",
                "title": "Reduce phone screen time",
                "detail": "High phone usage often competes with deep work. Try app limits, grayscale after a set hour, or leaving the phone in another room during study blocks.",
                "priority": "high",
                "category": "phone",
            },
        )

    if avg_study > 0 and avg_phone / max(avg_study, 0.25) > 0.55:
        add(
            82,
            {
                "id": "phone_vs_study",
                "title": "Balance phone vs study",
                "detail": "Phone time is high relative to study hours in your logs. Shifting even 30–60 minutes from scrolling to focused study usually moves the needle.",
                "priority": "medium",
                "category": "phone",
            },
        )

    if avg_focus < 58:
        add(
            75,
            {
                "id": "focus_low",
                "title": "Train deeper focus",
                "detail": "Your average focus score is on the lower side. Try 25-minute Pomodoros, one task at a time, and a distraction-free desk setup.",
                "priority": "medium",
                "category": "focus",
            },
        )

    if n >= 2 and lf < avg_focus - 12:
        add(
            70,
            {
                "id": "focus_dip",
                "title": "Recent focus dip",
                "detail": "Latest focus is well below your recent average—consider a lighter schedule today, a short walk, or splitting work into smaller wins.",
                "priority": "medium",
                "category": "focus",
            },
        )

    if avg_study < 2.5 and _mean(scores) < 75:
        add(
            68,
            {
                "id": "study_build",
                "title": "Build study volume gradually",
                "detail": "Study hours are modest compared to your goals. Add small, repeatable blocks (e.g. +45 min/day) rather than big unsustainable spikes.",
                "priority": "medium",
                "category": "study",
            },
        )

    best_idx = max(range(n), key=lambda i: float(rows[i]["score"]))
    best = rows[best_idx]
    bs = float(best["study_hours"])
    if bs > avg_study + 1.0 and n >= 5:
        add(
            65,
            {
                "id": "copy_best_day",
                "title": "Repeat what worked on your best day",
                "detail": f"On {best['activity_date']} you scored higher with about {bs:.1f}h study. Aim for that pattern on 2–3 days this week.",
                "priority": "medium",
                "category": "habits",
            },
        )

    if n >= 14:
        mid = n // 2
        first_half = _mean([float(r["score"]) for r in rows[:mid]])
        second_half = _mean([float(r["score"]) for r in rows[mid:]])
        if second_half < first_half - 3:
            add(
                72,
                {
                    "id": "trend_down",
                    "title": "Score trend softened",
                    "detail": "Later days in this window score lower than earlier ones. Review sleep, phone use, and consistency—small fixes often reverse the trend.",
                    "priority": "medium",
                    "category": "habits",
                },
            )

    # Model-informed tip: holding today’s other inputs fixed, less phone may raise predicted score.
    if lp >= 1.0:
        try:
            s_now = float(model_predict([ls, lf, lz, lp]))
            s_less = float(model_predict([ls, lf, lz, max(0.0, lp - 1.0)]))
            if s_less > s_now + 0.3:
                add(
                    86,
                    {
                        "id": "model_phone_down",
                        "title": "Your model suggests cutting phone time helps",
                        "detail": f"With today’s other metrics fixed, about 1 hour less phone is associated with a higher predicted score in your model (roughly +{s_less - s_now:.1f} points). Treat this as guidance, not a guarantee.",
                        "priority": "medium",
                        "category": "phone",
                    },
                )
        except Exception:
            pass

    # De-duplicate by id, keep highest score
    best_by_id: dict[str, tuple[int, dict[str, Any]]] = {}
    for score, item in recs:
        prev = best_by_id.get(item["id"])
        if prev is None or score > prev[0]:
            best_by_id[item["id"]] = (score, item)

    ranked = sorted(best_by_id.values(), key=lambda x: -x[0])
    out = [x[1] for x in ranked[:8]]
    if not out:
        out = [
            {
                "id": "steady_progress",
                "title": "Stay consistent",
                "detail": "No strong red flags in this window. Keep logging daily, change one habit at a time, and watch which days score highest.",
                "priority": "low",
                "category": "habits",
            }
        ]
    return out


@app.get("/api/dashboard")
@login_required
def dashboard():
    days = _parse_days_param(request.args.get("days"))
    if days == -1:
        return json_error("Invalid 'days' query param (use 7/30/90/all)")

    rows = _fetch_series(session["user_id"], days=days)

    if rows:
        latest_score = float(rows[-1]["score"])
    else:
        latest_score = 0.0

    payload = {
        "score": round(latest_score, 2),
        "dates": [r["activity_date"] for r in rows],
        "study_hours": [float(r["study_hours"]) for r in rows],
        "focus_scores": [int(r["focus_score"]) for r in rows],
        "sleep_hours": [float(r["sleep_hours"]) for r in rows],
        "phone_usage_hours": [float(r["phone_usage_hours"]) for r in rows],
        "scores": [float(r["score"]) for r in rows],
    }
    return jsonify(payload)


@app.get("/api/insights")
@login_required
def insights():
    days = _parse_days_param(request.args.get("days"))
    if days == -1:
        return json_error("Invalid 'days' query param (use 7/30/90/all)")

    rows = _fetch_series(session["user_id"], days=days)
    if not rows:
        return jsonify(
            {
                "avg_score": 0,
                "best_day": None,
                "streak_days": 0,
                "recommendations": [],
            }
        )

    scores = [float(r["score"]) for r in rows]
    avg_score = sum(scores) / len(scores)

    best_idx = max(range(len(rows)), key=lambda i: float(rows[i]["score"]))
    best_day = {"date": rows[best_idx]["activity_date"], "score": float(rows[best_idx]["score"])}

    dates = [date.fromisoformat(r["activity_date"]) for r in rows]
    present = set(dates)
    streak = 0
    d = date.today()
    while d in present:
        streak += 1
        d = d - timedelta(days=1)

    recommendations = _personal_recommendations(rows)

    return jsonify(
        {
            "avg_score": round(avg_score, 2),
            "best_day": best_day,
            "streak_days": streak,
            "recommendations": recommendations,
        }
    )


if __name__ == "__main__": 
    app.run(debug=CONFIG.debug)