import os
import uuid
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
INGEST_DIR = DATA_DIR / "ingests"
INGEST_DIR.mkdir(parents=True, exist_ok=True)

def make_ingestion_id() -> str:
    return uuid.uuid4().hex

def save_uploaded_file(upload_file, ingestion_id: str) -> str:
    dest_dir = INGEST_DIR / ingestion_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / upload_file.filename
    with dest_path.open("wb") as f:
        f.write(upload_file.file.read())
    return str(dest_path)

def save_text_as_file(text: str, ingestion_id: str, filename="text_input.txt"):
    dest_dir = INGEST_DIR / ingestion_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / filename
    path.write_text(text, encoding="utf-8")
    return str(path)

def read_file_text(path):
    return Path(path).read_text(encoding="utf-8")
