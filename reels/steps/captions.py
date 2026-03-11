"""5단계: 캡션 + 해시태그 + 썸네일 관리 (수동 JSON 입력)"""
import json
from pathlib import Path

from reels.config import CAPTIONS_OUTPUT
from reels.core.naming import build_filename


def import_json(json_path: str, idea_ids: list[int] = None) -> list[dict]:
    src = Path(json_path)
    if not src.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {json_path}")

    with open(src, "r", encoding="utf-8") as f:
        captions = json.load(f)

    if not isinstance(captions, list):
        captions = [captions]

    for cap in captions:
        for field in ["id", "title", "caption"]:
            if field not in cap:
                raise ValueError(f"필수 필드 누락: {field} (id: {cap.get('id', '?')})")

    if idea_ids:
        captions = [c for c in captions if int(c["id"]) in idea_ids]

    if not captions:
        return []

    results = []
    for cap in captions:
        cap.setdefault("topic", "")
        cap.setdefault("hashtags", [])
        cap.setdefault("thumbnail_text", {})

        filename = build_filename(cap["id"], cap["title"])
        output_path = CAPTIONS_OUTPUT / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cap, f, ensure_ascii=False, indent=2)

        results.append(cap)
    return results
