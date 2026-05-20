import os
from dotenv import load_dotenv
import sqlite3
from datetime import date, datetime, timedelta
from functools import wraps
import json
import bcrypt
from flask import Flask, jsonify, request, session,blueprints
from flask_cors import CORS
import re
from model.predict_model import model_predict
from groq import Groq
from tables import tables_bp


app = Flask(__name__, template_folder="template")
app.register_blueprint(tables_bp)
app.secret_key="yayyy123"
CORS(app,supports_credentials=True) # test this later when all has been done and dealt with

load_dotenv()

api_key = os.getenv("AI_API_KEY")
CLIENT = Groq(api_key=api_key)



def getdb():
    db = sqlite3.connect("./users.db")
    db.row_factory = sqlite3.Row
    return db

def login_required(view_function):
	@wraps(view_function)
	def wrapped_view(*args, **kwargs):
		if "user_id" not in session:
			return jsonify({"error":"Unauthorized"}), 401
		return view_function(*args, **kwargs)

	return wrapped_view

def chkpwd(userpwd,storedpwd):
	if storedpwd.startswith("$2a$") or storedpwd.startswith("$2b$") or storedpwd.startswith("$2y$"):
		return bcrypt.checkpw(userpwd.encode("utf-8"), storedpwd.encode("utf-8"))
	return userpwd==storedpwd
def pwdhash(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


@app.get("/")
def home():
    return jsonify({"message": "Flask API running YAYYY"})


@app.get("/api/me")
def me():
    if "user_id" not in session:
        return jsonify({"authenticated": False})
    return jsonify({"authenticated": True, "user_name": session.get("user_name")})


@app.post("/api/login")
def handlelogin():
	data = request.get_json()
	email = data.get("email")
	password = data.get("password")
	db = getdb()
	query = """
    SELECT id,full_name,email,password from users
	where email = ?
    """
	res = db.execute(query,(email,)).fetchone()
	if not res or not chkpwd( password,res["password"]):
		return jsonify({"error":"Invalid credentials"}), 401
	if not (res["password"].startswith("$2a$") or res["password"].startswith("$2b$") or res["password"].startswith("$2y$")):
		db.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (pwdhash(password), res["id"]),
            )
	session["user_id"] = int(res["id"])
	session["user_name"] = res["full_name"]
	return jsonify({"message": "Login successful", "user_name": res["full_name"]})

@app.post("/api/signup")
def handlesignup():
	data = request.get_json()
	full_name = data.get("full_name")
	email = data.get("email")
	password = data.get("password")
	if not password or not email:
		return jsonify({"error":"EMAIL OR PASSWORD CANT BE EMPTY"}), 400
	if not full_name:
		return jsonify({"error":"Full name is required"}), 400
	if "@" not in email or "." not in email:
		return jsonify({"error":"Invalid Email"}), 400
	if len(password) < 4:
		return jsonify({"error":"Password must be atleast 4 characters"}), 400
	hashedpwd = pwdhash(password)
	db = getdb()
	query="INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)"
	try:
		db.execute(query,(full_name,email,hashedpwd)) # unique id pwd handle garne ni banaunu parxa 
		db.commit()
	except sqlite3.IntegrityError:
		return jsonify({"error":"User already exists"}), 400
	return jsonify({"message":"SIGNUP SUCCESSFUL"})
@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

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
        return jsonify({"error":"All datatypes must be numbers"}), 400
    if study_hours < 0 or study_hours > 24:
        return jsonify({"error":"study hours must be between 0 and 24"}), 400
    if focus_score < 0 or focus_score > 100:
        return jsonify({"error":"foucs score must be between 1 and 100"}), 400
    if sleep_hours < 0 or sleep_hours > 24:
        return jsonify({"error":"sleep hours must be between 0 and 24 hours"}), 400
    if phone_usage_hours < 0 or phone_usage_hours > 24:
        return jsonify({"error":"phone usage hours must be between 0 and 24"}), 400
    if phone_usage_hours+sleep_hours+study_hours>24:
        return jsonify({"error":"FUN FACT: there are only 24 hours in a day"}), 400

    input_values = [study_hours, focus_score, sleep_hours, phone_usage_hours]
    score = float(model_predict(input_values))

    db = getdb()
    query = """
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
            """
    db.execute(query,(
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

def _fetch_series(user_id, days=None):
    where = "WHERE user_id=?"
    params = [user_id]
    if days is not None:
        days= int(days)
        cutoff = (date.today() - timedelta(days=days - 1)).isoformat()
        where += " AND activity_date >= ?"
        params.append(cutoff)

    with getdb() as conn:
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

@app.get("/api/dashboard")
@login_required
def dashboard():
    days= request.args.get("days")
    rows = _fetch_series(session["user_id"], days=days)
    if rows:
        latest_score = float(rows[-1]["score"])
    else:
        latest_score = 0.0

    return jsonify(
          {
        "score": round(latest_score, 2),
        "dates": [r["activity_date"] for r in rows],
        "study_hours": [float(r["study_hours"]) for r in rows],
        "focus_scores": [int(r["focus_score"]) for r in rows],
        "sleep_hours": [float(r["sleep_hours"]) for r in rows],
        "phone_usage_hours": [float(r["phone_usage_hours"]) for r in rows],
        "scores": [float(r["score"]) for r in rows],
    }
    )


def get_insights(sysprompt,userprompt):
    response = CLIENT.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": sysprompt},
            {"role": "user", "content": userprompt}
        ]
    )
    content = response.choices[0].message.content
    match = re.search(r'\[.*\]', content, re.DOTALL)
    return json.loads(match.group()) if match else []


def _mean(nums: list[float]) -> float:
    return sum(nums) / len(nums) if nums else 0.0


def _personal_recommendations(rows):
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
    best_idx = max(range(n), key=lambda i: float(rows[i]["score"]))
    best = rows[best_idx]
    SYSTEM_PROMPT = """
    You are a student productivity coach. Analyze the student's data and give only necessary recommendations.
    If everything looks fine, say so and give fewer tips.

    Respond in JSON only, no extra text. Format:
    [
    {
        "title": "short title",
        "detail": "actionable advice",
        "priority": "high/medium/low",
        "category": "sleep/study/focus/phone/habits"
    }
    ]
    """
    USER_PROMPT = f"""
    Period: {n} days

    Averages:
    - Study: {avg_study:.1f}h
    - Focus: {avg_focus:.1f}/100
    - Sleep: {avg_sleep:.1f}h
    - Phone: {avg_phone:.1f}h

    Latest day:
    - Study: {ls}h, Focus: {lf}, Sleep: {lz}h, Phone: {lp}h

    Best day: {best['activity_date']} with score {float(best['score']):.1f}
    - Study: {float(best['study_hours'])}h, Sleep: {float(best['sleep_hours'])}h, Phone: {float(best['phone_usage_hours'])}h

    Only flag real issues. If data looks healthy return 1-2 encouragement tips max. Max 5 recommendations.
    """
    return get_insights(SYSTEM_PROMPT,USER_PROMPT)



@app.get("/api/insights")
@login_required
def insights():
    days = request.args.get("days")
    
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
app.run(debug=True)