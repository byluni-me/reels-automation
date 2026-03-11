"""1단계: 아이디어 관리 (수동 CSV 입력)"""
import csv
import json
from datetime import datetime
from pathlib import Path

from reels.config import IDEAS_OUTPUT
from reels.core.csv_store import append_rows, existing_ids, init_csv


def import_csv(csv_path: str) -> list[dict]:
    """외부 CSV -> ideas_master.csv 등록. 필수 컬럼: id, title, topic, angle, hook"""
    src = Path(csv_path)
    if not src.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {csv_path}")

    ideas = []
    with open(src, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            for col in ["id", "title", "topic", "angle", "hook"]:
                if col not in row or not row[col].strip():
                    raise ValueError(f"필수 컬럼 누락: {col} (행: {row})")
            ideas.append(dict(row))

    if not ideas:
        raise ValueError("CSV에 데이터가 없습니다.")

    # 중복 제외
    existing = existing_ids()
    new_ideas = [i for i in ideas if str(i["id"]) not in existing]

    if not new_ideas:
        return []

    batch_id = datetime.now().strftime("B%Y%m%d_%H%M")
    append_rows(new_ideas, batch_id)

    # JSON 백업
    output_path = IDEAS_OUTPUT / f"ideas_{batch_id}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(new_ideas, f, ensure_ascii=False, indent=2)

    return new_ideas


def add_one(idea_id: int, title: str, topic: str, angle: str, hook: str) -> dict:
    """아이디어 1개 수동 추가"""
    if str(idea_id) in existing_ids():
        raise ValueError(f"ID {idea_id}는 이미 존재합니다.")

    idea = {"id": idea_id, "title": title, "topic": topic, "angle": angle, "hook": hook}
    batch_id = datetime.now().strftime("B%Y%m%d_%H%M")
    append_rows([idea], batch_id)
    return idea
