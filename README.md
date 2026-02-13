# 🕸️ 동료평가 네트워크 분석기 (Network Analyzer)

> 조직 내 동료평가 관계를 네트워크로 시각화하고,  
> 조직/개인 수준의 네트워크 건전성 지표를 분석하는 대시보드입니다.

---

## 📁 프로젝트 구조

```
network-analyzer/
│
├── backend/                     ← Python 백엔드 (데이터 처리 + 분석)
│   ├── main.py                  # FastAPI 서버 진입점 (uvicorn으로 실행)
│   ├── config.py                # 설정값 (데이터 경로, 색상 등)
│   ├── requirements.txt         # Python 패키지 목록
│   ├── services/                # 핵심 비즈니스 로직
│   │   ├── data_loader.py       # 엑셀/HR 데이터 로딩 (서버 시작 시 1회)
│   │   ├── network_builder.py   # NetworkX 그래프 생성 + 필터링
│   │   └── metrics_calculator.py# 조직/개인 네트워크 지표 계산
│   └── routers/                 # API 엔드포인트 정의
│       └── network.py           # /api/filter, /api/metrics 등
│
├── frontend/                    ← 브라우저 UI (HTML + JS + CSS)
│   ├── index.html               # 메인 페이지 (대시보드 레이아웃)
│   ├── css/
│   │   └── style.css            # 스타일 (다크 테마, 카드 레이아웃)
│   └── js/
│       ├── app.js               # 앱 초기화 및 이벤트 조율
│       ├── api.js               # 백엔드 API 호출 함수 모음
│       ├── network-graph.js     # Vis.js 네트워크 그래프 렌더링
│       ├── metrics-display.js   # 지표 카드/테이블 렌더링
│       └── filters.js           # 필터 UI 생성 및 상태 관리
│
└── README.md                    ← 이 파일
```

---

## 🚀 시작하기

### 1. 백엔드 실행

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

→ `http://localhost:8000` 에서 API 서버가 실행됩니다.  
→ `http://localhost:8000/docs` 에서 API 문서를 확인할 수 있습니다.

### 2. 프론트엔드 실행

```bash
cd frontend
python -m http.server 3000
```

→ `http://localhost:3000` 에서 대시보드를 확인할 수 있습니다.

---

## 🔄 동작 흐름 (이전 Streamlit과의 차이)

### Before (Streamlit)
```
필터 변경 → 전체 스크립트 재실행 → 데이터 로딩 → 분석 → 시각화 → 느림 + 메모리 에러
```

### After (Frontend + Backend 분리)
```
서버 시작 시 → 데이터 1회 로딩 (메모리 상주)

필터 변경 → API 호출 (필터링 결과만 요청) → JSON 응답 → 화면 부분 업데이트
            ≈ 1~3초                              화면 깜빡임 없음
```

---

## 🛠️ 기술 스택

| 구분 | 기술 | 역할 |
|------|------|------|
| 백엔드 서버 | **FastAPI** + **Uvicorn** | REST API, 데이터 처리 |
| 데이터 분석 | **pandas** + **networkx** | 그래프 생성, 지표 계산 |
| 프론트엔드 | **Vanilla JS** + **HTML/CSS** | UI, 사용자 인터랙션 |
| 네트워크 시각화 | **Vis.js** (CDN) | 브라우저에서 직접 그래프 렌더링 |
| 차트 | **Chart.js** (CDN) | 지표 시각화 |

---

## 📡 API 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/filter-options` | 필터 선택지 (연도, 조직, 직군, 직급) |
| POST | `/api/network` | 필터 적용된 네트워크 데이터 (노드 + 엣지) |
| POST | `/api/metrics/organization` | 조직 수준 네트워크 지표 |
| POST | `/api/metrics/individual` | 개인 수준 중심성 지표 (Top 10%) |
| POST | `/api/metrics/subgroup` | 하위 조직별 비교 지표 |
