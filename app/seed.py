
import json
from pathlib import Path
from .db_models import Student
SEED_PATH=Path(__file__).resolve().parent.parent/"data"/"seed_students.json"
def seed_students(db):
    if db.query(Student).count()>0: return
    for row in json.loads(SEED_PATH.read_text(encoding="utf-8")):
        db.add(Student(**row))
    db.commit()
