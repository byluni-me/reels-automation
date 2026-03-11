#!/bin/bash
set -e

echo "=========================================="
echo "  Reels 자동화 - Docker 배포"
echo "=========================================="

# .env 파일 확인
if [ ! -f .env ]; then
    echo "[설정] .env 파일 생성 중..."
    cp .env.example .env
    echo "  -> .env 파일이 생성되었습니다."
    echo "  -> Pexels API 키를 사용하려면 .env 파일을 수정하세요."
fi

# data 폴더 생성
echo "[준비] 데이터 폴더 생성..."
mkdir -p data/{ideas,scripts,voice,video,video_stock,captions,publish,csv}

# Docker 빌드 + 실행
echo "[빌드] Docker 이미지 빌드 중..."
docker compose build

echo "[실행] 컨테이너 시작..."
docker compose up -d

echo ""
echo "=========================================="
echo "  배포 완료!"
echo ""
echo "  접속: http://localhost:${PORT:-7860}"
echo ""
echo "  로그:    docker compose logs -f"
echo "  중지:    docker compose down"
echo "  재시작:  docker compose restart"
echo "=========================================="
