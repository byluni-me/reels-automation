"""Gradio 이벤트 핸들러 - steps/ 호출 + 결과 포맷팅"""
import json
import traceback
from pathlib import Path

from reels.config import BASE_DIR, MONTHLY_TARGET, PUBLISH_DIR, CAPTIONS_OUTPUT, TEMPLATES_DIR
from reels.core.csv_store import (
    count_by_status, get_next_id, load_all, existing_ids, init_csv,
)
from reels.steps import ideas, scripts, voice, video, captions, publish


# ─── 공통 유틸 ────────────────────────────────────────────────

def load_ideas_table() -> list[list]:
    return [
        [r["id"], r["title"], r["topic"], r["angle"], r["hook"], r["status"], r["created_at"]]
        for r in load_all()
    ]


def get_status_summary() -> str:
    counts = count_by_status()
    total = counts.pop("_total", 0)
    remaining = max(0, MONTHLY_TARGET - counts["rendered"] - counts["published"])

    publish_lines = []
    if PUBLISH_DIR.exists():
        for folder in sorted(PUBLISH_DIR.iterdir()):
            if folder.is_dir():
                v = "O" if (folder / "video.mp4").exists() else "X"
                c = "O" if (folder / "caption.txt").exists() else "X"
                t = "O" if (folder / "thumbnail.txt").exists() else "X"
                publish_lines.append(f"  {folder.name}  [영상:{v}] [캡션:{c}] [썸네일:{t}]")

    text = f"""═══════════════════════════════════════
  콘텐츠 현황
═══════════════════════════════════════
  전체:       {total}개

  ● 대기중   (pending):    {counts['pending']}개
  ● 스크립트 (scripted):   {counts['scripted']}개
  ● 음성완료 (voiced):     {counts['voiced']}개
  ● 렌더완료 (rendered):   {counts['rendered']}개
  ● 게시완료 (published):  {counts['published']}개

  월간 목표: {MONTHLY_TARGET}개 | 남은: {remaining}개
═══════════════════════════════════════
  publish/ 폴더: {len(publish_lines)}개 준비됨
═══════════════════════════════════════"""

    if publish_lines:
        text += "\n" + "\n".join(publish_lines[:15])
    return text


# ─── 1단계: 아이디어 ──────────────────────────────────────────

def handle_import_csv(file):
    if file is None:
        return "파일을 선택하세요.", load_ideas_table()
    try:
        result = ideas.import_csv(file.name)
        if not result:
            return "새로 등록할 아이디어가 없습니다. (중복 ID)", load_ideas_table()
        lines = "\n".join(f"  #{int(i['id']):>3} | {i['title']}" for i in result)
        return f"{len(result)}개 등록 완료!\n{lines}", load_ideas_table()
    except Exception as e:
        return f"오류: {e}", load_ideas_table()


def handle_add_idea(id_val, title, topic, angle, hook):
    if not all([id_val, title, topic, angle, hook]):
        return "모든 필드를 입력하세요.", load_ideas_table()
    try:
        idea = ideas.add_one(int(id_val), title, topic, angle, hook)
        return f"등록: #{idea['id']} {title}", load_ideas_table()
    except Exception as e:
        return f"오류: {e}", load_ideas_table()


def handle_next_id():
    return get_next_id()


# ─── 2단계: 스크립트 ─────────────────────────────────────────

def handle_import_scripts_file(file):
    if file is None:
        return "파일을 선택하세요."
    try:
        result = scripts.import_json(file.name)
        if not result:
            return "등록할 스크립트가 없습니다."
        lines = "\n".join(f"  #{int(s['idea_id']):>3} | {s['title']}" for s in result)
        return f"{len(result)}개 등록 완료!\n{lines}"
    except Exception as e:
        return f"오류: {e}"


def handle_import_scripts_text(json_text):
    if not json_text.strip():
        return "JSON을 입력하세요."
    try:
        data = json.loads(json_text)
        tmp = TEMPLATES_DIR / "_tmp_script.json"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data if isinstance(data, list) else [data], f, ensure_ascii=False)
        result = scripts.import_json(str(tmp))
        tmp.unlink(missing_ok=True)
        if not result:
            return "등록할 스크립트가 없습니다."
        lines = "\n".join(f"  #{int(s['idea_id']):>3} | {s['title']}" for s in result)
        return f"{len(result)}개 등록 완료!\n{lines}"
    except json.JSONDecodeError as e:
        return f"JSON 파싱 오류: {e}"
    except Exception as e:
        return f"오류: {e}"


# ─── 3단계: 음성 ─────────────────────────────────────────────

def handle_generate_voices(voice_choice, rate_choice, limit):
    voice_name = voice_choice.split(" ")[0] if voice_choice else voice.DEFAULT_VOICE
    rate = rate_choice.split(" ")[0] if rate_choice else voice.DEFAULT_RATE

    script_list = voice.load_scripted_scripts()
    if not script_list:
        return "처리할 scripted 스크립트가 없습니다.", []

    if limit and limit > 0:
        script_list = script_list[:int(limit)]

    log = [f"음성 생성: {len(script_list)}개 ({voice_name}, {rate})"]
    paths = []
    for i, s in enumerate(script_list):
        try:
            log.append(f"  [{i+1}/{len(script_list)}] {s.get('title', '?')}...")
            path = voice.generate_voice(s, voice=voice_name, rate=rate)
            paths.append(path)
            from reels.core.csv_store import update_status
            update_status(s["idea_id"], {
                "status": "voiced",
                "voice_file": str(Path(path).relative_to(BASE_DIR)),
            })
            log.append(f"    -> {Path(path).name}")
        except Exception as e:
            log.append(f"    -> 오류: {e}")

    log.append(f"\n완료! {len(paths)}개 생성")
    return "\n".join(log), [p for p in paths if Path(p).exists()]


# ─── 4단계: 영상 ─────────────────────────────────────────────

def handle_generate_videos(use_pexels, pexels_query, limit):
    pairs = video.load_voiced_pairs()
    if not pairs:
        return "처리할 voiced 아이디어가 없습니다.", []

    if limit and limit > 0:
        pairs = pairs[:int(limit)]

    bg = "Pexels 스톡" if use_pexels else "기본 배경"
    log = [f"영상 생성: {len(pairs)}개 (배경: {bg})"]
    paths = []
    for i, (script, audio) in enumerate(pairs):
        try:
            log.append(f"  [{i+1}/{len(pairs)}] {script.get('title', '?')}...")
            path = video.generate_video(
                script, audio,
                use_pexels=use_pexels,
                pexels_query=pexels_query or None,
            )
            paths.append(path)
            log.append(f"    -> {Path(path).name}")
        except Exception as e:
            log.append(f"    -> 오류: {e}")

    log.append(f"\n완료! {len(paths)}개 생성")
    return "\n".join(log), [p for p in paths if Path(p).exists()]


# ─── 5단계: 캡션 ─────────────────────────────────────────────

def handle_import_captions_file(file):
    if file is None:
        return "파일을 선택하세요."
    try:
        result = captions.import_json(file.name)
        if not result:
            return "등록할 캡션이 없습니다."
        lines = "\n".join(f"  #{int(c['id']):>3} | {c['title']}" for c in result)
        return f"{len(result)}개 등록 완료!\n{lines}"
    except Exception as e:
        return f"오류: {e}"


def handle_import_captions_text(json_text):
    if not json_text.strip():
        return "JSON을 입력하세요."
    try:
        data = json.loads(json_text)
        tmp = TEMPLATES_DIR / "_tmp_caption.json"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data if isinstance(data, list) else [data], f, ensure_ascii=False)
        result = captions.import_json(str(tmp))
        tmp.unlink(missing_ok=True)
        if not result:
            return "등록할 캡션이 없습니다."
        lines = "\n".join(f"  #{int(c['id']):>3} | {c['title']}" for c in result)
        return f"{len(result)}개 등록 완료!\n{lines}"
    except json.JSONDecodeError as e:
        return f"JSON 파싱 오류: {e}"
    except Exception as e:
        return f"오류: {e}"


# ─── 6단계: Publish ──────────────────────────────────────────

def handle_publish(limit):
    results = publish.publish_batch(limit=int(limit) if limit and limit > 0 else None)
    if not results:
        return "정리할 rendered 영상이 없습니다.", get_status_summary()
    return f"{len(results)}개 정리 완료 -> publish/", get_status_summary()


def handle_mark_published(ids_text):
    if not ids_text.strip():
        return "ID를 입력하세요. (예: 1 2 3)", get_status_summary()
    try:
        ids = [int(x.strip()) for x in ids_text.replace(",", " ").split() if x.strip()]
        publish.mark_published(ids)
        return f"ID {ids} -> published 완료", get_status_summary()
    except Exception as e:
        return f"오류: {e}", get_status_summary()
