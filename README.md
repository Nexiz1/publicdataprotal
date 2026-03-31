# ☂️ SkyCast: Intelligent Weather Insights & Smart Calendar Sync

SkyCast는 기상청 단기예보(Open API) 데이터를 분석하여, **"오늘 또는 내일 비가 올 확률이 높은지"** 지능적으로 판단하고 구글 캘린더에 **자동으로 우산 알림 일정을 등록/삭제**해 주는 스마트 웹 애플리케이션입니다. 

---

## ✨ 핵심 기능 (Key Features)

- **📍 인터랙티브 위치 기반 검색**
  - **도로명 주소 검색 (지오코딩):** "강남역", "제주도청" 등 자연어 주소를 치면 즉시 위/경도로 변환합니다.
  - **지도 클릭:** 내장된 Folium 지도를 클릭만 해도 원하는 위치의 기상 예보를 즉시 로드하고, 좌표를 도로명 주소(Reverse Geocoding)로 예쁘게 역변환하여 상단에 띄워줍니다.
  
- **⛅ 똑똑한 강수 확률 분석 (Smart KMA Analysis)**
  - 기상청 단기 예보를 파싱하여, 단순 숫자가 아닌 "오후 3시에 70% 확률로 비가 오니 우산을 챙기세요" 형태로 사유(Reason)를 직접 만들어냅니다.
  - **글래스모피즘(Glassmorphism)** 테마가 적용된 미려한 프리미엄 UI로 브리핑을 받아보세요.

- **📅 다중 사용자 구글 캘린더 동기화 (SaaS OAuth)**
  - 데스크탑 전용이 아닌 웹 친화적인 **OAuth 2.0 Web Flow**를 사용하여 누구나 자신의 구글 계정으로 손쉽게 로그인할 수 있습니다.
  - 만약 예보가 "비가 오지 않음(맑음)"으로 극적으로 바뀌면, 똑똑하게 이를 인지하고 **기존에 등록했던 우산 알림을 캘린더에서 찾아서 자동으로 삭제(Delete)** 하는 지능적인 Upsert 기능을 포함합니다.

- **🤖 매일 오전 6시 자동 백그라운드 봇 (APScheduler)**
  - 로그인 후 브라우저를 꺼도 걱정 없습니다! 내부의 백그라운드 스케줄러가 매일 아침 6시마다 가상환경에서 깨어나, 어제 저장해둔 내 위치의 최신 예보를 체크합니다.
  - 비가 오면 알아서 캘린더에 꽂아주고, **"설정"** 메뉴에서 이 자동 관리 봇을 언제든 **ON/OFF** 토글할 수 있습니다 (기본값: OFF).

---

## 🛠️ 기술 스택 (Tech Stack)

- **Frontend:** Streamlit, Folium, Custom HTML/CSS (Glassmorphism)
- **Backend:** FastAPI, Python (uv environment), APScheduler
- **Database:** SQLite (경량화된 사용자 토큰 및 위치 세션 영구 보관용)
- **API integrations:** 
  - KMA (한국 기상청 단기예보 API)
  - Google Calendar API (v3) & Google OAuth 2.0
  - Nominatim (OpenStreetMap 기반 지오코딩/역지오코딩)
- **Deployment:** Docker & Docker Compose 🐳

---

## 🚀 빠른 시작 가이드 (Quick Start)

### 1. 사전 준비 (Prerequisites)
1. **Google Cloud Console:** `OAuth 2.0 클라이언트 ID/비밀번호` 발급 (허용된 리디렉션 URI에 `http://localhost:8501` 추가 필수) 및 `Google Calendar API` 활성화.
2. **공공데이터포털:** 기상청 단기예보 Open API 신청 후 디코딩된 승인(API) 키 발급.

### 2. 환경 변수 세팅 (`.env`)
프로젝트 최상단 루트 디렉토리에 `.env` 파일을 만들고 아래 내용을 채워주세요.
```env
WEATHER_API_KEY="본인의_기상청_API_인증키"
GOOGLE_CLIENT_ID="본인의_구글_OAuth_클라이언트_ID.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="본인의_구글_OAuth_클라이언트_시크릿_비밀번호"
```

### 3. 도커 엔진으로 한 방에 실행하기 (Docker Compose)
이 프로젝트는 Docker 기반 오케스트레이션을 지원하므로, 터미널 명령줄을 여러 개 띄우고 설치할 필요가 없습니다. Docker Desktop이 켜져 있는 상태에서 아래 명령어 하나만 입력하세요.

```bash
docker compose up --build
```

- 도커가 자동으로 파이썬 패키지를 설치하고 Fast API 백엔드와 Streamlit UI 서버를 동시에 묶어서 구동시켜줍니다.
- 콘솔에 초록색 로그가 모두 올라오면, 브라우저에서 **`http://localhost:8501`** 로 접속하시면 끝입니다! 🎉

> **참고:** SQLite DB 파일(`skycast.db`)은 로컬 볼륨 마운트가 되어 있어 도커 컨테이너를 종료하거나 삭제하더라도 유저의 기존 정보가 안전하게 보존됩니다.

---

## 🧑‍💻 프로젝트 폴더 구조

```text
📁 SkyCast
 ├── 📄 docker-compose.yml     # 통합 서비스 실행 스크립트
 ├── 📄 Dockerfile.api         # FastAPI 백엔드 전용 컨테이너 명세서
 ├── 📄 Dockerfile.ui          # Streamlit 웹 전용 컨테이너 명세서
 ├── 📄 .env                   # API Key 및 토큰 보관소 (Git에 올라가지 않음)
 ├── 📁 api
 │   ├── 📄 main.py            # FastAPI 백엔드 엔드포인트 및 스케줄러 봇 로직
 │   └── 📄 schemas.py         # Pydantic 기반 입출력 데이터 검증 모델
 ├── 📁 core
 │   ├── 📄 database.py        # SQLite 유저 정보, 토큰, 토글 상태 저장/조회 모듈
 │   ├── 📄 google_calendar.py # 구글 캘린더 OAuth 토큰 검증 및 Upsert/Delete 모듈
 │   └── 📄 weather_analyzer.py# 기상청 강수 리스트를 똑똑하게 분석하는 코어 로직
 └── 📁 ui
     └── 📄 app.py             # 사용자가 보는 화면 (Streamlit, 지도, OAuth 플로우)
```
