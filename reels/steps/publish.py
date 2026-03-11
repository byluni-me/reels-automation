"""6단계: 영상 정리 + publish 폴더 생성 (API 호출 없음)"""
import json
import shutil
from datetime import datetime
from pathlib import Path

from reels.config import BASE_DIR, CAPTIONS_OUTPUT, PUBLISH_DIR
from reels.core.csv_store import load_by_status, update_status
from reels.core.naming import safe_title


def _load_caption_data(idea_id: int) -> dict | None:
    for f in CAPTIONS_OUTPUT.glob(f"{int(idea_id):03d}_*.json"):
        with open(f, "r", encoding="utf-8") as fp:
            return json.load(fp)
    return None


def organize_one(idea: dict) -> Path | None:
    video_path = BASE_DIR / idea.get("video_file", "")
    if not video_path.exists():
        return None

    folder_name = f"{int(idea['id']):03d}_{safe_title(idea['title'], max_len=20)}"
    publish_folder = PUBLISH_DIR / folder_name
    publish_folder.mkdir(parents=True, exist_ok=True)

    shutil.copy2(video_path, publish_folder / "video.mp4")

    caption_data = _load_caption_data(idea["id"])
    if not caption_data:
        return publish_folder

    # caption.txt
    caption_text = caption_data.get("caption", "")
    hashtags = caption_data.get("hashtags", [])
    full_caption = caption_text + "\n\n" + " ".join(hashtags)
    (publish_folder / "caption.txt").write_text(full_caption, encoding="utf-8")

    # thumbnail.txt
    thumb = caption_data.get("thumbnail_text", {})
    (publish_folder / "thumbnail.txt").write_text(
        f"메인: {thumb.get('main_text', '')}\n"
        f"서브: {thumb.get('sub_text', '')}\n"
        f"이모지: {thumb.get('emoji', '')}\n"
        f"색상: {thumb.get('color_scheme', '')}\n",
        encoding="utf-8",
    )

    # meta.json
    meta = {
        "id": idea["id"],
        "title": idea["title"],
        "topic": idea.get("topic", ""),
        "caption": full_caption,
        "thumbnail": thumb,
        "hashtags": hashtags,
        "best_posting_time": caption_data.get("best_posting_time", ""),
        "hook_preview": caption_data.get("hook_preview", ""),
        "video_file": "video.mp4",
        "created_at": idea.get("created_at", ""),
        "organized_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    with open(publish_folder / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return publish_folder


def publish_batch(limit: int = None) -> list[Path]:
    ideas = load_by_status("rendered")
    if limit and limit > 0:
        ideas = ideas[:limit]

    results = []
    for idea in ideas:
        result = organize_one(idea)
        if result:
            results.append(result)
    return results


def mark_published(idea_ids: list[int]):
    for idea_id in idea_ids:
        update_status(idea_id, {
            "status": "published",
            "published_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
