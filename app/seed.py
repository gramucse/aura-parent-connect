\
import json
from pathlib import Path
from sqlalchemy.orm import Session

from .db_models import Student

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_students.json"

def seed_students(db: Session):
    if db.query(Student).count() > 0:
        return
    rows = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    for row in rows:
        db.add(Student(**row))
    db.commit()
