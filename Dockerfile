FROM python:3.12-slim

# 시스템 패키지: ffmpeg + 한글 폰트
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        fonts-nanum \
        fonts-nanum-coding \
        fontconfig \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 비root 사용자 생성
RUN groupadd -r reels && useradd -r -g reels -m reels

WORKDIR /app

# 의존성 먼저 설치 (캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY reels/ reels/
COPY templates/ templates/
COPY app.py .

# 출력 폴더 생성 + 권한
RUN mkdir -p output/{ideas,scripts,voice,video,video_stock,captions,publish} csv \
    && chown -R reels:reels /app

USER reels

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7860/')" || exit 1

CMD ["python", "app.py", "--port", "7860"]
