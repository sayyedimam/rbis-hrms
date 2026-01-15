import re
from app.core.database import SessionLocal
from app.models.models import Attendance

def to_min(ts):
    if not ts or ':' not in str(ts): return 0
    try:
        clean_ts = re.sub(r'\(.*?\)', '', str(ts)).strip()
        parts = clean_ts.split(':')
        h = int(parts[0])
        m = int(parts[1])
        return h * 60 + m
    except: return 0

def update_durations():
    db = SessionLocal()
    try:
        records = db.query(Attendance).all()
        count = 0
        for rec in records:
            if rec.first_in and rec.last_out and rec.first_in != "--:--" and rec.last_out != "--:--":
                span_min = to_min(rec.last_out) - to_min(rec.first_in)
                if span_min >= 0:
                    new_total = f"{span_min // 60:02d}:{span_min % 60:02d}"
                    if rec.total_duration != new_total:
                        rec.total_duration = new_total
                        count += 1
        db.commit()
        print(f"Updated {count} records with new Gross Duration.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_durations()
