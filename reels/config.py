"""설정 파일 - 경로, API 키, 영상 스펙"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ─── API Keys ───────────────────────────────────────────────
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# ─── Batch 설정 ─────────────────────────────────────────────
MONTHLY_TARGET = 100
BATCH_SIZE = 10

# ─── 영상 설정 ──────────────────────────────────────────────
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30

# ─── 자막 설정 ──────────────────────────────────────────────
SUBTITLE_FONT = "NanumGothicBold"
SUBTITLE_FONTSIZE = 55
SUBTITLE_OUTLINE = 3

# ─── 경로 ───────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "output"
IDEAS_OUTPUT = OUTPUT_DIR / "ideas"
SCRIPTS_OUTPUT = OUTPUT_DIR / "scripts"
VOICE_OUTPUT = OUTPUT_DIR / "voice"
VIDEO_OUTPUT = OUTPUT_DIR / "video"
VIDEO_STOCK = OUTPUT_DIR / "video_stock"
CAPTIONS_OUTPUT = OUTPUT_DIR / "captions"
PUBLISH_DIR = OUTPUT_DIR / "publish"

TEMPLATES_DIR = BASE_DIR / "templates"

# CSV 경로 (Docker에서는 환경변수로 오버라이드)
_csv_dir = os.getenv("IDEAS_CSV_DIR", "")
if _csv_dir:
    IDEAS_CSV = Path(_csv_dir) / "ideas_master.csv"
else:
    IDEAS_CSV = BASE_DIR / "ideas_master.csv"

# 출력 폴더 자동 생성
for d in [
    IDEAS_OUTPUT,
    SCRIPTS_OUTPUT,
    VOICE_OUTPUT,
    VIDEO_OUTPUT,
    VIDEO_STOCK,
    CAPTIONS_OUTPUT,
    PUBLISH_DIR,
]:
    d.mkdir(parents=True, exist_ok=True)
