# FestInsight - 축제 감성 분석 플랫폼 (React Edition)

## 🎯 프로젝트 개요

**FestInsight**는 축제 기획자를 위한 데이터 기반 의사결정 플랫폼입니다.
네이버 블로그 리뷰를 LLM과 규칙 기반 감성 분석으로 처리하여 관람객의 만족도, 불만 사항, 계절별 트렌드를 제공합니다.

**주요 특징:**
- ✅ **만족도 5단계 분류** - IQR 기반 통계 분류로 정량적 평가
- ✅ **이상치 탐지 (BoxPlot)** - 극단적 의견 및 스팸 리뷰 식별
- ✅ **LLM 해석 텍스트** - Google Gemini가 분포를 자연어로 설명
- ✅ **계절별 분석** - 봄/여름/가을/겨울 워드클라우드 & 차트
- ✅ **카테고리 비교** - 최대 4개 그룹 자유 비교 분석

---

## 🏗️ 기술 스택

### Backend
- **FastAPI** - 고성능 Python 웹 프레임워크
- **LangGraph** - Multi-agent 워크플로우 오케스트레이션
- **Google Gemini 2.5 Pro** - LLM 기반 감성 분석
- **Selenium + BeautifulSoup** - 네이버 블로그 크롤링
- **Matplotlib + WordCloud** - 차트 및 워드클라우드 생성
- **SQLite** - 축제 마스터 데이터 저장

### Frontend
- **React 18 + TypeScript** - 모던 UI 프레임워크
- **Vite** - 빠른 개발 서버 & 빌드 도구
- **TailwindCSS** - 유틸리티 기반 스타일링
- **Recharts** - 리액트 차트 라이브러리
- **TanStack React Query** - 서버 상태 관리 & 캐싱
- **Framer Motion** - 애니메이션

---

## 📦 설치 및 실행

### 1️⃣ 사전 준비

**필수 요구사항:**
- Python 3.9+
- Node.js 18+
- Chrome 브라우저 (Selenium용)

**API 키 준비:**
```bash
# .env 파일 생성
GOOGLE_API_KEY=your_gemini_api_key
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
NAVER_TREND_CLIENT_ID=your_trend_client_id
NAVER_TREND_CLIENT_SECRET=your_trend_client_secret
```

### 2️⃣ 백엔드 설치 및 실행

```bash
# 1. Python 가상환경 생성
cd C:\Users\SBA\github\GradioNaverSentiment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 2. 의존성 설치
pip install -r requirements.txt

# 3. FastAPI 서버 실행
python api_server.py
```

**서버 실행 확인:**
- Backend API: http://localhost:8001
- Swagger UI: http://localhost:8001/docs

### 3️⃣ 프론트엔드 설치 및 실행

```bash
# 1. 프론트엔드 폴더로 이동
cd frontend

# 2. 의존성 설치
npm install

# 3. 개발 서버 실행
npm run dev
```

**프론트엔드 접속:**
- React App: http://localhost:5173

---

## 🚀 사용 방법

### 단일 키워드 분석
1. 홈페이지에서 "축제 검색하기" 클릭
2. 축제명 입력 (예: 강릉커피축제)
3. 분석할 리뷰 수 선택 (5~50개)
4. "분석 시작" 버튼 클릭
5. 2-3분 대기 후 결과 확인

**제공 차트:**
- 도넛 차트 (긍정/부정 비율)
- 만족도 5단계 막대 차트
- 절대 점수 분포 꺾은선 그래프
- 이상치 BoxPlot

### 카테고리 분석
1. "카테고리별 검색" 선택
2. 대분류 → 중분류 → 소분류 순서로 선택
3. 해당 카테고리의 모든 축제 일괄 분석
4. 축제별 비교 및 카테고리 평균 확인

---

## 📊 새로운 기능 (tour_agent에서 이전)

### 1. 만족도 5단계 분류
- **통계 기반 경계값:** IQR(Interquartile Range) 방식으로 이상치 제거 후 평균±표준편차 계산
- **분류 기준:**
  - 매우 불만족: < mean - 1.5*std
  - 불만족: < mean - 0.5*std
  - 보통: < mean + 0.5*std
  - 만족: < mean + 1.5*std
  - 매우 만족: >= mean + 1.5*std

### 2. 이상치 탐지 (BoxPlot)
- **IQR 방식:** Q1 - 1.5*IQR ~ Q3 + 1.5*IQR 범위 밖의 값을 이상치로 판정
- **활용:** 스팸 리뷰, 극단적 의견, 통계적 이상 데이터 식별

### 3. LLM 분포 해석
- **Google Gemini 활용:** 만족도 분포를 자연어로 해석
- **예시:** "만족 구간이 45%로 가장 많으며, 전반적으로 긍정적인 평가를 받았습니다. 다만 매우 불만족 비율이 5%로 일부 개선이 필요합니다."

---

## 🎨 프로젝트 구조

```
GradioNaverSentiment/
├── api_server.py                 # FastAPI 백엔드 서버 (NEW)
├── app_llm.py                    # Gradio UI (Legacy)
├── requirements.txt
├── .env
│
├── src/                          # Python 백엔드 코드 (Clean Architecture)
│   ├── domain/                   # 도메인 계층
│   │   ├── knowledge_base.py
│   │   └── state.py
│   ├── application/              # 애플리케이션 계층
│   │   ├── agents/
│   │   ├── graph.py
│   │   ├── analysis_logic.py     # 만족도 분석 추가 (MODIFIED)
│   │   ├── result_packager.py    # 차트 생성 추가 (MODIFIED)
│   │   └── utils.py              # 만족도 함수 추가 (MODIFIED)
│   ├── infrastructure/           # 인프라 계층
│   │   ├── reporting/
│   │   │   └── charts.py         # 3개 차트 추가 (MODIFIED)
│   │   ├── web/
│   │   └── database/
│   └── presentation/             # Gradio UI (Legacy)
│
├── frontend/                     # React 프론트엔드 (NEW)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── SearchPage.tsx
│   │   │   └── AnalysisPage.tsx
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   └── Layout.tsx
│   │   │   └── charts/
│   │   │       ├── DonutChart.tsx
│   │   │       ├── SatisfactionChart.tsx
│   │   │       ├── AbsoluteScoreChart.tsx
│   │   │       └── OutlierChart.tsx
│   │   ├── lib/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── dic/                          # 감성 사전 (CSV)
├── festivals/                    # 축제 카테고리 (JSON)
└── database/                     # 축제 마스터 데이터
```

---

## 🔧 내일 해야 할 작업 (미완성 부분)

### 우선순위 1: 추가 페이지
- [ ] **CategoryAnalysisPage** - 카테고리 분석 결과 표시
- [ ] **ComparisonPage** - 2개 축제 비교 페이지
- [ ] **FreeGroupPage** - 자유 그룹 비교 페이지 (최대 4그룹)

### 우선순위 2: 계절별 분석
- [ ] **SeasonalAnalysis 컴포넌트** - 봄/여름/가을/겨울 탭
- [ ] **WordCloud 이미지 표시** - 백엔드에서 생성된 워드클라우드 표시
- [ ] **계절별 막대 차트** - Stacked bar chart 추가

### 우선순위 3: UX 개선
- [ ] **로딩 상태 개선** - Skeleton UI, Progress bar
- [ ] **에러 처리** - 친화적인 에러 메시지
- [ ] **반응형 디자인** - 모바일 최적화
- [ ] **다크 모드** - 선택적

### 우선순위 4: 성능 최적화
- [ ] **무한 스크롤** - 블로그 테이블에 페이지네이션 추가
- [ ] **차트 지연 로딩** - Lazy loading으로 초기 렌더링 속도 개선
- [ ] **결과 캐싱** - React Query의 staleTime 조정

---

## 🐛 알려진 이슈

1. **긴 분석 시간** - 10개 리뷰 분석 시 약 2-3분 소요 (백엔드 병렬 처리 필요)
2. **WebDriver 메모리** - 장시간 실행 시 Selenium 메모리 누수 가능 (주기적 재시작 필요)
3. **API 키 제한** - Naver API 일일 호출 제한 (25,000회/일)

---

## 📝 변경 이력

### v2.0.0 (2025-01-XX) - React 전환
- ✅ FastAPI 백엔드 서버 추가
- ✅ React + TypeScript 프론트엔드 구축
- ✅ 만족도 5단계 분류 시스템 추가 (from tour_agent)
- ✅ 이상치 BoxPlot 분석 추가 (from tour_agent)
- ✅ LLM 분포 해석 텍스트 추가 (from tour_agent)
- ✅ Recharts 기반 인터랙티브 차트
- 🚧 계절별 분석 (진행 중)
- 🚧 카테고리 비교 (진행 중)

### v1.0.0 (2024-XX-XX) - Gradio 버전
- Gradio 기반 UI
- 단일 키워드 분석
- 계절별 워드클라우드
- Naver 트렌드 분석

---

## 👨‍💻 개발자

- **Backend & Analysis:** Python, LangGraph, Gemini LLM
- **Frontend:** React, TypeScript, TailwindCSS
- **Migration:** tour_agent → GradioNaverSentiment 기능 통합

---

## 📄 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다.

---

## 🙏 감사의 말

- **Google Gemini LLM** - 강력한 감성 분석
- **Naver API** - 블로그 및 트렌드 데이터 제공
- **LangGraph** - Multi-agent 워크플로우 프레임워크
- **tour_agent 프로젝트** - 고급 분석 기능 참고

---

**문의:** 이슈 또는 PR 환영합니다! 🎉
