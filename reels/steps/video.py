"""4단계: 영상 생성 (ffmpeg + Pexels 스톡)"""
import json
import subprocess
import tempfile
from pathlib import Path

from reels.config import (
    BASE_DIR, PEXELS_API_KEY,
    VIDEO_OUTPUT, VIDEO_STOCK,
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    SUBTITLE_FONT, SUBTITLE_FONTSIZE, SUBTITLE_OUTLINE,
)
from reels.core.csv_store import load_by_status, update_status
from reels.core.naming import build_filename


# ─── Pexels ──────────────────────────────────────────────────

KEYWORD_MAP = {
    "재테크": "money finance",
    "부동산": "real estate building",
    "자산관리": "investment saving",
    "주식": "stock market trading",
    "ETF": "stock market chart",
    "저축": "piggy bank saving",
    "대출": "bank loan",
    "연금": "retirement pension",
    "보험": "insurance protection",
    "전세": "apartment house",
    "월세": "apartment rent",
}


def _query_for_script(script: dict) -> str:
    title = script.get("title", "")
    topic = script.get("topic", "")
    for keyword, query in KEYWORD_MAP.items():
        if keyword in title or keyword in topic:
            return query
    return "money finance business"


def search_pexels_video(query: str) -> str | None:
    import requests

    if not PEXELS_API_KEY:
        return None

    resp = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": PEXELS_API_KEY},
        params={"query": query, "orientation": "portrait", "size": "medium", "per_page": 5},
        timeout=30,
    )
    if resp.status_code != 200:
        return None

    videos = resp.json().get("videos", [])
    if not videos:
        return None

    video = videos[0]
    best_file = None
    for vf in video.get("video_files", []):
        if vf.get("height", 0) >= vf.get("width", 0) and vf.get("height", 0) >= 720:
            best_file = vf
            break
    if not best_file:
        best_file = video["video_files"][0] if video["video_files"] else None
    if not best_file:
        return None

    stock_path = VIDEO_STOCK / f"pexels_{video['id']}.mp4"
    if stock_path.exists():
        return str(stock_path)

    dl_resp = requests.get(best_file["link"], timeout=120)
    if dl_resp.status_code == 200:
        with open(stock_path, "wb") as f:
            f.write(dl_resp.content)
        return str(stock_path)
    return None


# ─── ffmpeg ──────────────────────────────────────────────────

def _get_audio_duration(audio_path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def _seconds_to_ass(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _generate_ass(subtitles: list[dict]) -> str:
    header = f"""[Script Info]
Title: Reels Subtitle
ScriptType: v4.00+
PlayResX: {VIDEO_WIDTH}
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{SUBTITLE_FONT},{SUBTITLE_FONTSIZE},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{SUBTITLE_OUTLINE},2,2,40,40,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for sub in subtitles:
        start = _seconds_to_ass(sub["start"])
        end = _seconds_to_ass(sub["end"])
        text = sub["text"].replace("\n", "\\N")
        events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")
    return header + "\n".join(events) + "\n"


def _create_bg_video(duration: float, output_path: str):
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c=0x1a1a2e:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d={duration}:r={VIDEO_FPS}",
        "-vf", "drawbox=x=0:y=0:w=iw:h=ih/3:color=0x16213e@0.5:t=fill,"
               "drawbox=x=0:y=ih*2/3:w=iw:h=ih/3:color=0x0f3460@0.5:t=fill",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", output_path,
    ], capture_output=True, text=True)


def _prepare_pexels_bg(stock_path: str, duration: float, output_path: str):
    subprocess.run([
        "ffmpeg", "-y", "-i", stock_path, "-t", str(duration),
        "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
               f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},eq=brightness=-0.1:saturation=0.8",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast", "-r", str(VIDEO_FPS), output_path,
    ], capture_output=True, text=True)


# ─── 메인 ────────────────────────────────────────────────────

def generate_video(script: dict, audio_path: str, use_pexels: bool = False,
                   pexels_query: str = None) -> str:
    duration = _get_audio_duration(audio_path)
    filename = build_filename(script.get("idea_id", 0), script["title"], ext=".mp4")
    output_path = VIDEO_OUTPUT / filename

    with tempfile.TemporaryDirectory() as tmpdir:
        bg_path = f"{tmpdir}/bg.mp4"

        if use_pexels:
            query = pexels_query or _query_for_script(script)
            stock = search_pexels_video(query)
            if stock:
                _prepare_pexels_bg(stock, duration + 1, bg_path)
            else:
                _create_bg_video(duration + 1, bg_path)
        else:
            _create_bg_video(duration + 1, bg_path)

        subtitles = script.get("subtitles", [])
        ass_path = f"{tmpdir}/subtitles.ass"
        if subtitles:
            with open(ass_path, "w", encoding="utf-8") as f:
                f.write(_generate_ass(subtitles))

        title_text = script["title"].replace("'", "'\\''")
        vf = [
            f"drawtext=text='{title_text}':fontsize=70:fontcolor=white"
            f":x=(w-text_w)/2:y=h/4:enable='between(t,0,{min(duration, 5)})'"
            f":borderw=3:bordercolor=black"
        ]
        if subtitles:
            vf.append(f"ass={ass_path.replace(':', '\\:')}")

        cmd = [
            "ffmpeg", "-y", "-i", bg_path, "-i", audio_path,
            "-vf", ",".join(vf),
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p", "-preset", "fast", "-shortest",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            subprocess.run([
                "ffmpeg", "-y", "-i", bg_path, "-i", audio_path,
                "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p", "-preset", "fast", "-shortest",
                str(output_path),
            ], capture_output=True, text=True)

    update_status(script["idea_id"], {
        "status": "rendered",
        "video_file": str(output_path.relative_to(BASE_DIR)),
    })
    return str(output_path)


def load_voiced_pairs() -> list[tuple[dict, str]]:
    ideas = load_by_status("voiced")
    pairs = []
    for idea in ideas:
        script_path = BASE_DIR / idea.get("script_file", "")
        voice_path = BASE_DIR / idea.get("voice_file", "")
        if script_path.exists() and voice_path.exists():
            with open(script_path, "r", encoding="utf-8") as f:
                pairs.append((json.load(f), str(voice_path)))
    return pairs
