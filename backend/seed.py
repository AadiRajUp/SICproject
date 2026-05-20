import sqlite3
import random
from datetime import date, timedelta
from model.predict_model import model_predict

db = sqlite3.connect("./users.db")
for uid in range(1,23):

    user_id = uid  # change to your actual user id
    start = date.today() - timedelta(days=100)

    for i in range(100):
        d = start + timedelta(days=i)
        study = round(random.uniform(1, 8), 1)
        focus = random.randint(40, 95)
        sleep = round(random.uniform(5, 9), 1)
        phone = round(random.uniform(1, 5), 1)
        input_values = [study, focus, sleep, phone]
        score = model_predict(input_values)
        
        db.execute("""
            INSERT OR REPLACE INTO daily_productivity 
            (user_id, activity_date, study_hours, focus_score, sleep_hours, phone_usage_hours, score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, d.isoformat(), study, focus, sleep, phone, score))

    db.commit()
print("done")