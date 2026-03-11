"""3단계: 음성 생성 (edge-tts, 무료)"""
import asyncio
import json
from pathlib import Path

from reels.config import VOICE_OUTPUT, BASE_DIR
from reels.core.csv_store import load_by_status, update_status
from reels.core.naming import build_filename

DEFAULT_VOICE = "ko-KR-SunHiNeural"
DEFAULT_RATE = "+5%"


async def _generate_one(script: dict, voice: str, rate: str) -> str:
    import edge_tts

    filename = build_filename(script.get("idea_id", 0), script["title"], ext=".mp3")
    output_path = VOICE_OUTPUT / filename

    communicate = edge_tts.Communicate(
        text=script["full_script"],
        voice=voice,
        rate=rate,
    )
    await communicate.save(str(output_path))
    return str(output_path)


def generate_voice(script: dict, voice: str = None, rate: str = None) -> str:
    voice = voice or DEFAULT_VOICE
    rate = rate or DEFAULT_RATE

    # Gradio는 이미 이벤트 루프가 있으므로 분기 처리
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            path = loop.run_in_executor(
                pool, lambda: asyncio.run(_generate_one(script, voice, rate))
            )
            # synchronous context에서 호출된 경우
            return asyncio.run(_generate_one(script, voice, rate))
    except RuntimeError:
        return asyncio.run(_generate_one(script, voice, rate))


def generate_batch(voice: str = None, rate: str = None, limit: int = None) -> list[str]:
    scripts = load_scripted_scripts()
    if limit and limit > 0:
        scripts = scripts[:limit]

    paths = []
    for script in scripts:
        path = generate_voice(script, voice=voice, rate=rate)
        paths.append(path)
        update_status(script["idea_id"], {
            "status": "voiced",
            "voice_file": str(Path(path).relative_to(BASE_DIR)),
        })
    return paths


def load_scripted_scripts() -> list[dict]:
    ideas = load_by_status("scripted")
    scripts = []
    for idea in ideas:
        script_path = BASE_DIR / idea.get("script_file", "")
        if script_path.exists():
            with open(script_path, "r", encoding="utf-8") as f:
                scripts.append(json.load(f))
    return scripts


async def list_korean_voices() -> list[dict]:
    import edge_tts
    voices = await edge_tts.list_voices()
    return [v for v in voices if v["Locale"].startswith("ko-KR")]
