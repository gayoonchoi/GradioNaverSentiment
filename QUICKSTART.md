# 🚀 FestInsight 빠른 시작 가이드

## 5분 안에 시작하기

### 1️⃣ 백엔드 실행 (터미널 1)

```bash
# 1. 프로젝트 폴더로 이동
cd C:\Users\SBA\github\GradioNaverSentiment

# 2. 가상환경 활성화 (이미 설치되어 있다면)
venv\Scripts\activate

# 3. 의존성 설치 (처음 한 번만)
pip install -r requirements.txt

# 4. 백엔드 서버 실행
python api_server.py
```

**✅ 성공 확인:**
- 콘솔에 "🚀 GradioNaverSentiment API Server Starting..." 메시지
- http://localhost:8001/docs 접속 시 Swagger UI 표시

---

### 2️⃣ 프론트엔드 실행 (터미널 2)

```bash
# 1. 프론트엔드 폴더로 이동
cd C:\Users\SBA\github\GradioNaverSentiment\frontend

# 2. 의존성 설치 (처음 한 번만)
npm install

# 3. 개발 서버 실행
npm run dev
```

**✅ 성공 확인:**
- 콘솔에 "Local: http://localhost:5173/" 메시지
- 브라우저에서 http://localhost:5173 접속 시 FestInsight 홈페이지 표시

---

### 3️⃣ 첫 번째 분석 실행

1. **브라우저에서 http://localhost:5173 접속**

2. **"지금 시작하기" 버튼 클릭**

3. **직접 검색 탭에서:**
   - 축제명: `강릉커피축제` 입력
   - 리뷰 수: `10개` 선택
   - "분석 시작" 클릭

4. **2-3분 대기**
   - 로딩 스피너와 함께 "분석 중..." 메시지 표시
   - 네이버 블로그 크롤링 + AI 감성 분석 진행

5. **결과 확인:**
   - ✅ 도넛 차트 (긍정/부정 비율)
   - ✅ 만족도 5단계 막대 차트
   - ✅ 절대 점수 분포 그래프
   - ✅ 이상치 BoxPlot
   - ✅ LLM 해석 텍스트
   - ✅ 계절별 분석
   - ✅ 개별 블로그 테이블

---

## 🎯 주요 기능 테스트

### 카테고리 분석

1. **검색 페이지에서 "카테고리별 검색" 선택**
2. **대분류 > 중분류 > 소분류 순서로 선택**
   - 예: `계절과_자연` > `꽃` > `벚꽃축제`
3. **"카테고리 분석 시작" 클릭**
4. **결과:**
   - 해당 카테고리의 모든 축제 일괄 분석
   - 축제별 비교 표시

### 축제 비교

1. **상단 네비게이션에서 "비교" 클릭**
2. **두 축제명 입력:**
   - 축제 A: `강릉커피축제`
   - 축제 B: `보령머드축제`
3. **"비교 분석 시작" 클릭**
4. **결과:**
   - 나란히 비교 (VS 형식)
   - AI 비교 분석 텍스트
   - 각 축제별 차트

---

## ⚠️ 문제 해결

### 백엔드 서버가 시작되지 않을 때

**문제:** `ModuleNotFoundError: No module named 'fastapi'`

**해결:**
```bash
pip install fastapi uvicorn
```

**문제:** `.env 파일을 찾을 수 없습니다`

**해결:**
```bash
# 프로젝트 루트에 .env 파일 생성
GOOGLE_API_KEY=your_api_key_here
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
```

### 프론트엔드가 시작되지 않을 때

**문제:** `npm: command not found`

**해결:**
1. Node.js 설치 (https://nodejs.org/)
2. 터미널 재시작
3. `npm install` 다시 실행

**문제:** `CORS 에러`

**해결:**
- 백엔드 서버가 http://localhost:8001에서 실행 중인지 확인
- 브라우저 콘솔에서 에러 메시지 확인

### 분석이 실패할 때

**문제:** `400: 블로그를 찾을 수 없습니다`

**원인:** 축제명이 정확하지 않거나 네이버에 리뷰가 없음

**해결:**
- 축제명을 정확히 입력 (예: "강릉커피축제" ✅, "커피축제" ❌)
- 유명한 축제로 먼저 테스트

**문제:** `500: Internal Server Error`

**원인:** API 키 문제 또는 WebDriver 오류

**해결:**
1. .env 파일의 API 키 확인
2. Chrome 브라우저 설치 확인
3. 백엔드 콘솔에서 상세 에러 메시지 확인

---

## 📁 프로젝트 구조 참고

```
GradioNaverSentiment/
├── api_server.py              ← 백엔드 서버 (FastAPI)
├── src/                       ← Python 백엔드 코드
│   ├── application/
│   ├── infrastructure/
│   └── presentation/
├── frontend/                  ← React 프론트엔드
│   ├── src/
│   │   ├── pages/            ← 페이지 컴포넌트
│   │   ├── components/       ← 재사용 컴포넌트
│   │   └── lib/api.ts        ← API 클라이언트
│   └── package.json
└── .env                       ← API 키 설정
```

---

## 🎉 성공적인 설치 확인

**모든 것이 정상이라면:**

1. ✅ 백엔드: http://localhost:8001/docs 접속 시 Swagger UI
2. ✅ 프론트엔드: http://localhost:5173 접속 시 FestInsight 홈페이지
3. ✅ 분석 테스트: "강릉커피축제" 분석 시 차트 및 결과 표시

**축하합니다! 이제 FestInsight를 사용할 준비가 완료되었습니다! 🎊**

---

## 💡 다음 단계

1. **다양한 축제 분석해보기**
2. **카테고리 분석으로 트렌드 파악**
3. **축제 비교로 경쟁 분석**
4. **결과를 CSV로 다운로드하여 보고서 작성**

---

## 📞 도움이 필요하신가요?

- **README_REACT.md** - 상세 설명서
- **Swagger UI** (http://localhost:8001/docs) - API 문서
- **GitHub Issues** - 버그 리포트 및 기능 요청

즐거운 분석 되세요! 🎈
