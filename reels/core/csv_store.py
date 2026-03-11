"""CSV 기반 아이디어 저장소 - CRUD 전담"""
import csv
from datetime import datetime
from pathlib import Path

from reels.config import IDEAS_CSV

CSV_COLUMNS = [
    "id", "title", "topic", "angle", "hook", "caption",
    "thumbnail_text", "status", "batch_id",
    "created_at", "published_at",
    "video_file", "script_file", "voice_file",
]


def init_csv():
    if not IDEAS_CSV.exists():
        IDEAS_CSV.parent.mkdir(parents=True, exist_ok=True)
        with open(IDEAS_CSV, "w", newline="", encoding="utf-8-sig") as f:
            csv.DictWriter(f, fieldnames=CSV_COLUMNS).writeheader()


def get_next_id() -> int:
    init_csv()
    max_id = 0
    with open(IDEAS_CSV, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                max_id = max(max_id, int(row["id"]))
            except (ValueError, KeyError):
                pass
    return max_id + 1


def append_rows(ideas: list[dict], batch_id: str):
    init_csv()
    with open(IDEAS_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        for idea in ideas:
            writer.writerow({
                "id": idea["id"],
                "title": idea["title"],
                "topic": idea["topic"],
                "angle": idea["angle"],
                "hook": idea["hook"],
                "caption": idea.get("caption", ""),
                "thumbnail_text": idea.get("thumbnail_text", ""),
                "status": "pending",
                "batch_id": batch_id,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "published_at": "",
                "video_file": "",
                "script_file": "",
                "voice_file": "",
            })


def load_by_status(status: str) -> list[dict]:
    init_csv()
    with open(IDEAS_CSV, "r", encoding="utf-8-sig") as f:
        return [dict(row) for row in csv.DictReader(f) if row["status"] == status]


def load_all() -> list[dict]:
    init_csv()
    with open(IDEAS_CSV, "r", encoding="utf-8-sig") as f:
        return [dict(row) for row in csv.DictReader(f)]


def update_status(idea_id: int, updates: dict):
    rows = []
    with open(IDEAS_CSV, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if str(row["id"]) == str(idea_id):
                row.update(updates)
            rows.append(row)

    with open(IDEAS_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def existing_ids() -> set[str]:
    init_csv()
    with open(IDEAS_CSV, "r", encoding="utf-8-sig") as f:
        return {str(row["id"]) for row in csv.DictReader(f)}


def count_by_status() -> dict[str, int]:
    init_csv()
    counts = {"pending": 0, "scripted": 0, "voiced": 0, "rendered": 0, "published": 0}
    total = 0
    with open(IDEAS_CSV, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            total += 1
            status = row.get("status", "pending")
            counts[status] = counts.get(status, 0) + 1
    counts["_total"] = total
    return counts
