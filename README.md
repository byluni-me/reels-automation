# Instagram Reels 자동화 파이프라인

월 100개 인스타그램 릴스를 자동으로 생산하는 파이프라인입니다.
Docker만 있으면 바로 실행 가능합니다.

## 주제

- 재테크
- 부동산 공부
- 30대 직장인 자산관리

## 실행 (Docker)

```bash
# 원클릭 배포
./deploy.sh

# 또는 수동
cp .env.example .env        # 설정 파일 생성
docker compose up -d --build # 빌드 + 실행
```

브라우저에서 `http://localhost:7860` 접속

## 관리

```bash
docker compose logs -f       # 로그 실시간
docker compose restart       # 재시작
docker compose down          # 중지
```

## GUI 탭 구성

| 탭 | 기능 |
|---|---|
| 대시보드 | 전체 현황 (상태별 개수, 아이디어 목록) |
| 1. 아이디어 | CSV 업로드 또는 수동 입력 -> ideas_master.csv 등록 |
| 2. 스크립트 | JSON 업로드 또는 에디터에서 직접 입력 |
| 3. 음성 | edge-tts 음성 선택 (9종), 속도 조절, 생성 (무료) |
| 4. 영상 | 기본 배경 또는 Pexels 스톡 영상 배경 (무료) |
| 5. 캡션 | JSON 업로드 또는 에디터에서 직접 입력 |
| 6. Publish | publish 폴더 정리 + published 상태 변경 |

## 파이프라인 흐름

```
[1단계] 아이디어 CSV 입력 → ideas_master.csv 등록
  ↓
[2단계] 스크립트 JSON 입력 (Hook 3초 + 핵심 20초 + CTA 7초)
  ↓
[3단계] 스크립트 → AI 음성 (edge-tts, 무료)
  ↓
[4단계] 음성 + 자막 → 세로형 영상 (ffmpeg, 1080x1920)
        배경: 기본 그라디언트 또는 Pexels 스톡 영상
  ↓
[5단계] 캡션 + 해시태그 + 썸네일 텍스트 JSON 입력
  ↓
[6단계] publish/ 폴더로 정리 (video.mp4 + caption.txt + thumbnail.txt)
```

## 프로젝트 구조

```
reels-automation/
├── Dockerfile             # Docker 이미지 정의
├── docker-compose.yml     # 컨테이너 실행 설정
├── deploy.sh              # 원클릭 배포 스크립트
├── .env.example           # 환경변수 예시
├── app.py                 # Gradio GUI 메인
├── config.py              # 설정
├── publish.py             # 영상 정리 + publish 폴더
│
├── 01-reels/              # 1단계: 아이디어
│   ├── run.py
│   ├── ideas_example.csv  # 입력 CSV 예시
│   └── output/
│
├── 02-scripts/            # 2단계: 스크립트
│   ├── run.py
│   ├── script_template.json  # 입력 JSON 템플릿
│   └── output/
│
├── 03-voice/              # 3단계: 음성 (edge-tts)
│   ├── run.py
│   └── output/
│
├── 04-video/              # 4단계: 영상 (ffmpeg + Pexels)
│   ├── run.py
│   ├── output/
│   └── stock/             # Pexels 다운로드 캐시
│
├── 05-captions/           # 5단계: 캡션
│   ├── run.py
│   ├── captions_example.json  # 입력 JSON 예시
│   └── output/
│
└── data/                  # Docker 볼륨 (영속 데이터)
    ├── csv/               # ideas_master.csv
    ├── 01-reels-output/
    ├── 02-scripts-output/
    ├── 03-voice-output/
    ├── 04-video-output/
    ├── 04-video-stock/
    ├── 05-captions-output/
    └── publish/           # 최종 업로드용
```

## CSV 기반 상태 관리

```
pending → scripted → voiced → rendered → published
 1단계      2단계      3단계     4단계      업로드 후
```

| 상태 | 설명 |
|---|---|
| `pending` | 아이디어 등록 완료, 스크립트 대기 |
| `scripted` | 스크립트 등록 완료, 음성 대기 |
| `voiced` | 음성 생성 완료, 영상 대기 |
| `rendered` | 영상 생성 완료, 업로드 대기 |
| `published` | 인스타그램 게시 완료 |

## 환경변수

| 변수 | 설명 | 기본값 |
|---|---|---|
| `PEXELS_API_KEY` | Pexels 스톡 영상 API 키 (무료, 선택) | - |
| `PORT` | 서버 포트 | 7860 |

## 비용

**전부 무료**

| 구성요소 | 비용 |
|---|---|
| edge-tts 음성 | 무료 |
| ffmpeg 영상 | 무료 |
| Pexels 스톡 영상 | 무료 (월 20,000 요청) |
| 아이디어/스크립트/캡션 | 수동 입력 |

## 업로드 워크플로우

1. GUI에서 1~6단계 순서대로 진행
2. `data/publish/` 폴더 확인
3. 각 폴더의 `caption.txt`를 인스타에 복사-붙여넣기
4. `thumbnail.txt`로 썸네일 커버 제작
5. GUI 6번 탭에서 Published 처리
