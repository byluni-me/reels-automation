"""2단계: 스크립트 관리 (수동 JSON 입력)"""
import json
from pathlib import Path

from reels.config import SCRIPTS_OUTPUT, BASE_DIR
from reels.core.csv_store import update_status
from reels.core.naming import build_filename


def import_json(json_path: str, idea_ids: list[int] = None) -> list[dict]:
    """외부 JSON -> 02-scripts/output 등록"""
    src = Path(json_path)
    if not src.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {json_path}")

    with open(src, "r", encoding="utf-8") as f:
        scripts = json.load(f)

    if not isinstance(scripts, list):
        scripts = [scripts]

    for s in scripts:
        for field in ["idea_id", "title", "full_script"]:
            if field not in s:
                raise ValueError(f"필수 필드 누락: {field} (idea_id: {s.get('idea_id', '?')})")

    if idea_ids:
        scripts = [s for s in scripts if int(s["idea_id"]) in idea_ids]

    if not scripts:
        return []

    results = []
    for script in scripts:
        filename = build_filename(script["idea_id"], script["title"])
        output_path = SCRIPTS_OUTPUT / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)

        update_status(script["idea_id"], {
            "status": "scripted",
            "script_file": str(output_path.relative_to(BASE_DIR)),
        })
        results.append(script)

    return results
