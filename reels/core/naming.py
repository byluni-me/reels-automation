"""파일명 생성 유틸 - 중복 제거"""


def safe_title(title: str, max_len: int = 30) -> str:
    return "".join(c for c in title if c.isalnum() or c in " _-").strip()[:max_len]


def build_filename(idea_id: int, title: str, ext: str = ".json") -> str:
    return f"{int(idea_id):03d}_{safe_title(title)}{ext}"
