"""GUI 상수 + 템플릿 로드"""
from reels.config import TEMPLATES_DIR

VOICE_CHOICES = [
    "ko-KR-SunHiNeural (여성, 기본)",
    "ko-KR-InJoonNeural (남성)",
    "ko-KR-HyunsuNeural (남성)",
    "ko-KR-BongJinNeural (남성)",
    "ko-KR-GookMinNeural (남성)",
    "ko-KR-JiMinNeural (여성)",
    "ko-KR-SeoHyeonNeural (여성)",
    "ko-KR-SoonBokNeural (여성)",
    "ko-KR-YuJinNeural (여성)",
]

RATE_CHOICES = [
    "-20% (느리게)",
    "-10%",
    "+0% (보통)",
    "+5% (기본, 약간 빠르게)",
    "+10%",
    "+20% (빠르게)",
]


def _load_template(filename: str) -> str:
    path = TEMPLATES_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


SCRIPT_TEMPLATE = _load_template("script_template.json")
CAPTION_TEMPLATE = _load_template("captions_example.json")
