# 계절별 인기 축제 탐색 - React + FastAPI 통합 완료

Tour_Trend_WordCloud 기능을 React 프론트엔드에 성공적으로 통합했습니다.

## ✅ 완료 사항

### Backend (FastAPI)

#### 1. API 엔드포인트 추가
**파일**: `api_server.py`

```python
# 계절별 트렌드 분석 엔드포인트
GET /api/seasonal/analyze?season={봄|여름|가을|겨울}

# 응답 데이터:
{
  "status": "분석 완료",
  "season": "봄",
  "wordcloud_url": "/images/wordcloud_봄_xxx.png",
  "timeline_url": "/images/timeline_봄_xxx.png",
  "top_festivals": [...],  # 상위 10개 축제 테이블 데이터
  "festival_names": [...]  # 드롭다운용 축제명 리스트
}
```

```python
# 개별 축제 트렌드 조회 엔드포인트
GET /api/seasonal/festival-trend?festival_name={축제명}&season={계절}

# 응답 데이터:
{
  "status": "조회 완료",
  "festival_name": "강릉커피축제",
  "trend_graph_url": "/images/festival_trend_xxx.png"
}
```

#### 2. 분석 로직 모듈
**파일**: `src/application/seasonal_analysis.py`

- `get_festival_frequency_dict()` - 워드클라우드용 데이터
- `create_timeline_graph()` - 타임라인 그래프 생성
- `get_table_data()` - 테이블 데이터
- `get_festival_names_for_season()` - 드롭다운 데이터
- `create_individual_festival_trend_graph()` - 개별 축제 트렌드 그래프

#### 3. 워드클라우드 생성 모듈
**파일**: `src/infrastructure/reporting/seasonal_wordcloud.py`

- `create_wordcloud_for_gradio()` - 계절별 색상 팔레트 적용

### Frontend (React + TypeScript)

#### 1. API 클라이언트 함수
**파일**: `frontend/src/lib/api.ts`

```typescript
export const getSeasonalTrends = async (season: string)
export const getFestivalTrend = async (festivalName: string, season?: string)
```

#### 2. 계절별 트렌드 페이지
**파일**: `frontend/src/pages/SeasonalTrendPage.tsx`

**주요 기능**:
- 4개 계절 버튼 (봄/여름/가을/겨울) - 아이콘과 색상으로 구분
- 워드클라우드 표시
- 타임라인 그래프 표시
- 상위 10개 축제 테이블
- 개별 축제 트렌드 그래프 조회
- 직접 검색 페이지로 유도하는 안내 메시지

#### 3. 라우팅 추가
**파일**: `frontend/src/App.tsx`

```tsx
<Route path="seasonal" element={<SeasonalTrendPage />} />
```

#### 4. 네비게이션 추가
**파일**: `frontend/src/components/layout/Layout.tsx`

헤더에 "계절별" 링크 추가 (FaCloudSun 아이콘)

---

## 🚀 실행 방법

### 1. 샘플 데이터 확인 (이미 완료됨)

```bash
# 100개 샘플 데이터 수집 완료
# 파일 위치: database/festival_trends_summary.csv
# 계절별 분포: 가을 38개, 봄 25개, 여름 25개, 겨울 12개
```

### 2. 백엔드 서버 실행

```bash
cd C:\Users\SBA\github\GradioNaverSentiment
python api_server.py
```

서버 주소: `http://localhost:8001`
Swagger UI: `http://localhost:8001/docs`

### 3. 프론트엔드 개발 서버 실행

```bash
cd C:\Users\SBA\github\GradioNaverSentiment\frontend
npm run dev
```

프론트엔드 주소: `http://localhost:5173`

### 4. 앱 사용

1. 브라우저에서 `http://localhost:5173` 접속
2. 헤더에서 **"계절별"** 클릭
3. 원하는 계절 선택 (봄/여름/가을/겨울)
4. 워드클라우드, 타임라인, 테이블 확인
5. 흥미로운 축제를 드롭다운에서 선택
6. **"이 축제 트렌드 보기"** 클릭
7. 더 자세한 분석이 필요하면 → **"검색"** 메뉴로 이동하여 해당 축제명 검색

---

## 📊 기능 설명

### 계절별 분류 기준

- **봄**: 3월, 4월, 5월 시작 축제
- **여름**: 6월, 7월, 8월 시작 축제
- **가을**: 9월, 10월, 11월 시작 축제
- **겨울**: 12월, 1월, 2월 시작 축제

### 검색량 기반 순위

- 네이버 트렌드 API에서 가져온 `max_ratio` (최대 검색량) 기준
- 높을수록 검색 인기도가 높음

### 워드클라우드

- 상위 120개 축제를 검색량에 비례하는 크기로 표시
- 계절별 색상 팔레트 적용:
  - 봄: 핑크/연두 계열
  - 여름: 파랑/노랑 계열
  - 가을: 갈색/주황 계열
  - 겨울: 파랑/검정 계열

### 타임라인 그래프

- 상위 10개 축제의 행사 기간을 막대로 표시
- 각 축제의 검색량을 숫자로 표시
- 계절별 색상 적용

### 개별 축제 트렌드

- 네이버 트렌드 API 실시간 호출
- 행사 전후 30일간의 검색량 변화 그래프
- 행사 기간은 강조 표시 (반투명 배경)

---

## 🔗 사용자 흐름

```
1. 홈페이지
   ↓
2. "계절별" 메뉴 클릭
   ↓
3. 계절 선택 (예: 가을)
   ↓
4. 워드클라우드/타임라인/테이블 확인
   ↓
5. 흥미로운 축제 선택 (예: 지리산남원정령제)
   ↓
6. "이 축제 트렌드 보기" 클릭
   ↓
7. 트렌드 그래프 확인
   ↓
8. (선택) "검색" 메뉴로 이동
   ↓
9. 축제명 입력하여 심층 분석 (블로그 감성 분석, LLM 요약 등)
```

---

## 🛠️ 기술 스택

### Backend
- FastAPI
- Pandas, Matplotlib
- WordCloud
- 네이버 트렌드 API

### Frontend
- React 18 + TypeScript
- TanStack Query (React Query) - 데이터 페칭
- React Router - 라우팅
- TailwindCSS - 스타일링
- React Icons - 아이콘

---

## 📁 주요 파일 구조

```
GradioNaverSentiment/
├── api_server.py                              # FastAPI 서버 (엔드포인트 추가됨)
├── database/
│   └── festival_trends_summary.csv            # 축제 트렌드 데이터 (100개 샘플)
├── src/
│   ├── application/
│   │   └── seasonal_analysis.py               # 계절별 분석 로직
│   └── infrastructure/reporting/
│       └── seasonal_wordcloud.py              # 워드클라우드 생성
└── frontend/
    ├── src/
    │   ├── App.tsx                            # 라우팅 (seasonal 추가)
    │   ├── lib/
    │   │   └── api.ts                         # API 함수 (seasonal 추가)
    │   ├── pages/
    │   │   └── SeasonalTrendPage.tsx          # 계절별 트렌드 페이지 (신규)
    │   └── components/layout/
    │       └── Layout.tsx                     # 네비게이션 (계절별 링크 추가)
```

---

## ⚠️ 참고사항

### 1. 데이터 수집

현재는 샘플 100개로 테스트 중입니다. 전체 1,377개 축제 데이터를 수집하려면:

```bash
python scripts/collect_all_trends.py
```

약 1-2시간 소요되며, 중간 저장 기능이 있어 중단 시에도 이어서 수집 가능합니다.

### 2. API 호출 제한

네이버 트렌드 API는 호출 제한이 있으므로:
- 개별 축제 트렌드 조회는 실시간 API 호출
- 과도한 요청 시 429 에러 발생 가능
- 적절한 간격(1.2초)으로 호출

### 3. 이미지 캐싱

생성된 이미지는 `temp_images/` 폴더에 저장되며:
- UUID로 고유한 파일명 생성
- 주기적으로 정리 필요 (향후 개선 가능)

---

## ✨ 통합 완료!

Tour_Trend_WordCloud의 계절별 인기 축제 탐색 기능이 React + FastAPI 아키텍처에 성공적으로 통합되었습니다.

사용자는 이제:
1. **계절별로 인기 축제 파악** (워드클라우드)
2. **상위 축제 타임라인 확인** (행사 기간 + 검색량)
3. **개별 축제 트렌드 분석** (검색량 변화 그래프)
4. **심층 분석으로 자연스럽게 연결** (직접 검색 → 블로그 감성 분석)

이 흐름을 통해 축제 기획자는 트렌드를 파악하고, 경쟁 축제를 분석하며, 데이터 기반 의사결정을 할 수 있습니다! 🎉

---

**제작**: Claude Code
**날짜**: 2025-11-14
**아키텍처**: React + FastAPI
**기반**: Tour_Trend_WordCloud + GradioNaverSentiment
