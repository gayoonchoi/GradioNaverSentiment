# 🎪 FestInsight - AI 기반 축제 감성 분석 플랫폼

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18%2B-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.2%2B-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5.0%2B-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind-3.0%2B-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

**데이터가 말해주는 진짜 축제 평가**
사전 관심도(트렌드) × 사후 만족도(블로그 리뷰) × AI 감성 분석

[🚀 빠른 시작](#-설치-및-빠른-시작) · [✨ 주요 기능](#-주요-기능) · [🏗️ 핵심 아키텍처](#️-핵심-아키텍처) · [🏆 모델 성과](#-모델-성과-및-개선-방향) · [🚀 향후 계획](#-향후-계획-roadmap)

</div>

---

## 📋 목차

- [🌟 프로젝트 소개](#-프로젝트-소개)
- [💡 기획 의도 및 배경](#-기획-의도-및-배경)
- [👥 타겟 사용자](#-타겟-사용자)
- [✨ 주요 기능](#-주요-기능)
- [📊 주요 지표 상세](#-주요-지표-상세)
- [🏗️ 핵심 아키텍처](#️-핵심-아키텍처)
- [🏆 모델 성과 및 개선 방향](#-모델-성과-및-개선-방향)
- [🚀 향후 계획 (Roadmap)](#-향후-계획-roadmap)
- [📚 활용 사례](#-활용-사례)
- [🎯 기대 효과](#-기대-효과)
- [🛠️ 기술 스택](#️-기술-스택)
- [🚀 설치 및 빠른 시작](#-설치-및-빠른-시작)
- [📁 프로젝트 구조](#-프로젝트-구조)
- [🎬 시연 영상](#-시연-영상)
- [⚠️ 문제 해결](#️-문제-해결)
- [🤝 기여하기](#-기여하기)
- [📄 라이선스](#-라이선스)

---

## 🌟 프로젝트 소개

**FestInsight**는 축제 기획자, 지자체 담당자, 마케터를 위한 **데이터 기반 의사결정 지원 플랫폼**입니다.

네이버 트렌드 API로 측정한 **사전 관심도(검색량)**와 네이버 블로그 리뷰를 AI 에이전트로 심층 분석한 **사후 만족도(감성 점수)**를 융합하여, 축제의 성과를 객관적으로 평가하고 마케팅 효율 인사이트를 도출합니다.

### 💎 핵심 가치

- **📊 데이터 기반 의사결정**: "방문객 수"라는 단편적 지표를 넘어, "방문객의 실제 경험"을 데이터로 정량화합니다.
- **🤖 AI 주체-감성 분석**: "축제가 좋았다/나빴다"를 넘어, "왜" 좋았는지(예: 음식, 포토존)와 "왜" 나빴는지(예: 주차장, 대기줄)를 **'주체(Aspect)'** 기반으로 분석합니다.
- **⚡ 시간 절약**: 수작업으로 수십 시간이 걸릴 리뷰 수백 건의 분석 및 요약 작업을 단 몇 분 만에 완료합니다.
- **🎯 실행 가능한 제안**: 단순 분석을 넘어, 사용자가 입력한 '지역'과 '계절'에 맞춘 구체적인 AI 기획 방향을 제시합니다.

---

## 💡 기획 의도 및 배경

### 문제 인식: 지방 소멸 위기와 축제 산업의 한계

- **거시적 문제**: 대한민국은 수도권 인구 집중과 지방 인구 소멸 위기에 직면해 있습니다. 이에 정부는 '생활인구' 유입을 통한 지역 경제 활성화를 핵심 과제로 삼고 있습니다.
- **핵심 수단**: **문화 관광산업(축제)**은 지역 활성화의 가장 강력한 수단입니다. 실제로 국내 지역 축제의 95.1%가 인구 감소 또는 소멸 위기 지역에서 개최되고 있습니다.
- **데이터의 한계**:
  - **평가 부재**: 축제 성과를 '단순 방문객 수'로만 판단하여, 방문객의 **'진짜 만족도(Real 만족도)'**를 정량화할 평가 체계가 없었습니다.
  - **파편화**: 수백 개의 축제 정보, 시즌별 트렌드, 방문객 후기가 모두 파편화되어 있어 종합적인 인사이트를 얻기 어려웠습니다.
  - **주관적 기획**: 데이터가 아닌 담당자의 직관과 경험에 의존한 기획이 반복되었습니다.

### 솔루션: FestInsight

**FestInsight**는 '축제별 마케팅 효율 인사이트'를 도출하여, **데이터 기반 의사결정(DDDM)**을 지원하는 Research Tool입니다.

- **수집**: 네이버 블로그(Selenium), 네이버 트렌드(Trend API), 축제 정보(Local SQLite DB)를 융합합니다.
- **분석**: '자가 교정' 기능이 탑재된 **AI 에이전트(LangGraph)**가 블로그 리뷰의 '주체-감성 쌍'을 추출합니다.
- **학습**: '동적 학습' 스코어러가 사전에 없는 신조어를 실시간으로 학습하여 감성 사전을 스스로 업데이트합니다.
- **제공**: 통계 차트, 주체 기반 워드클라우드, AI 요약 리포트, 맞춤형 기획 제안을 대시보드로 제공합니다.

---

## 👥 타겟 사용자

### 🏛️ 주요 타겟: 관공서 축제 기획 담당자

시/군/구청 문화관광과, 축제추진위원회, 지역 문화재단 소속 담당자

#### 활용 시나리오

**1. 신규 축제 기획 단계**
- **카테고리 분석**: 유사 카테고리의 성공 축제 벤치마킹.
- **계절별 트렌드**: 우리 지역과 계절에 맞는 축제 유형 선정.
- **AI 추천**: "서울, 봄" 조건 입력으로 성공 가능성 사전 검증.

**2. 기존 축제 개선 단계**
- **단일 축제 분석**: AI 불만 사항 요약으로 "주차", "대기줄" 등 핵심 문제 파악.
- **비교 분석**: 타 지역 유사 축제와 강/약점 비교.
- **주체-감성 워드클라우드**: 개선 우선순위 결정.

**3. 예산 심의 및 보고 단계**
- 트렌드 지수, 만족도 변화 등 정량적 지표로 성과 보고서 작성.
- 상세 블로그 테이블: 실제 리뷰를 근거로 예산 증액 설득.

### 🎯 부가 타겟

- **이벤트/마케팅 기획사**: 클라이언트를 위한 축제 기획 시 데이터 분석
- **관광 연구기관**: 지역 축제 트렌드 연구 및 정책 제안
- **대학교 연구자**: 관광학, 데이터 분석 연구 자료
- **개인 블로거/유튜버**: 축제 콘텐츠 제작 시 인사이트 확보

---

## ✨ 주요 기능

### 🔍 1. 단일 축제 분석 (AnalysisPage)

특정 축제명(예: 강릉커피축제)을 입력하여 심층 분석 대시보드를 생성합니다.

- **📊 종합 지표**: 긍정/부정 문장 수, 평균 만족도 (5점 척도)
- **📋 상세 정보**: 축제 주소, 기간, 종합 감성 점수(100점), 트렌드 지수, 만족도 변화
- **🤖 AI 리포트**:
  - **AI 종합 평가**: LLM이 모든 지표를 분석해 생성하는 최종 평가 (강점/개선점 포함).
  - **AI 분석 해석**: 6가지 핵심 차트(만족도, 이상치 등)의 분포를 자연어로 해석.
  - **AI 주요 불만 사항**: 모든 '부정' 문장만 따로 모아 LLM이 핵심 불만 사항을 요약.
- **📈 만족도 차트 (Recharts)**:
  - **만족도 5단계 분포**: IQR 통계 기법으로 리뷰를 5등급('매우 불만족' ~ '매우 만족')으로 분류.
  - **절대 점수 분포**: 실제 감성 점수(-2.0 ~ +2.0)의 히스토그램.
  - **이상치 분석 (BoxPlot)**: 극단적 의견 및 스팸성 리뷰 식별.
- **☁️ 계절별 주체-감성 워드클라우드**:
  - **핵심 기능**: 단순 빈도수가 아닌, 블로그 본문에서 추출한 **'주체(Aspect)'** 기반 워드클라우드.
  - **긍정**: "음식", "포토존" 등 만족 요인 시각화.
  - **부정**: "주차장", "대기줄" 등 불만 요인 시각화.
- **📈 트렌드 그래프 (Matplotlib)**:
  - **전체 트렌드 (1년)**: 1년간 검색량 추이.
  - **집중 트렌드 (±30일)**: 축제 기간 전후 검색량 집중 분석.
- **📑 개별 블로그 결과 테이블**:
  - 분석에 사용된 모든 블로그 리뷰의 상세 정보 (페이지네이션 지원).
  - **행 클릭 시**: 해당 블로그의 문장별 상세 점수 및 LLM이 마킹한 **\*\*하이라이트\*\*** 구문 확인.

### 🗂️ 2. 카테고리 분석 (CategoryAnalysisPage)

3단계 계층 구조(예: 계절과 자연 > 꽃 > 매화)로 카테고리를 선택하여 해당 카테고리의 모든 축제를 종합 분석합니다.

- **🎯 카테고리 종합 지표**: 전체 축제 수, 분석 완료 축제 수, 카테고리 평균 만족도.
- **📊 통합 대시보드**: 카테고리 전체에 대한 통합 만족도 차트, AI 요약 리포트, 주체-감성 워드클라우드 제공.
- **📋 개별 축제 요약 리스트**: 카테고리 내 각 축제의 요약 정보(감성 점수, 트렌드 지수 등)를 리스트로 제공하며, 클릭 시 해당 축제의 '단일 축제 분석' 페이지로 이동합니다.

### ⚖️ 3. 비교 분석 (ComparisonPage)

두 개의 대상(단일 축제 또는 카테고리)을 선택하여 모든 지표를 나란히 비교 분석합니다.

- **📊 A vs B 병렬 차트**: 만족도 분포, 긍정/부정 비율 등을 좌우로 배치하여 시각적 비교.
- **🤖 AI 비교 요약**: LLM이 두 대상의 강점과 약점을 비교 설명.
- **⚡ 병렬 처리**: 카테고리 비교 시, 두 카테고리를 동시에 분석하여 시간 절약 (FastAPI 비동기 활용).

### 📅 4. 계절별 인기 축제 탐색 (SeasonalTrendPage)

네이버 트렌드 검색량 데이터를 기반으로 계절별 인기 축제를 탐색합니다.

- **☁️ 트렌드 워드클라우드**: 해당 계절에 **'검색량'**이 가장 높았던 축제 시각화.
- **📈 타임라인 그래프**: 계절별 상위 10개 축제의 개최 시기와 검색량 피크를 시각화.
- **🏆 상위 축제 테이블**: 순위, 축제명, 검색량, 행사 기간, 카테고리 정보 제공.
- **🔄 분석 연동**: 테이블에서 축제명 클릭 시, 해당 축제의 키워드와 카테고리 정보가 '검색 페이지'로 자동 전달되어 즉시 상세 분석 가능.

### 🤖 5. AI 총합 분석 추천 (공통 기능)

모든 분석 결과 페이지 하단에 제공되며, 사용자가 **'지역'**과 **'계절'**을 입력하면 LLM이 맞춤형 기획 리포트를 생성합니다.

- **단일 분석 추천**: 성공 가능성 평가, 핵심 기획 방향, 지역/계절 특화 전략, 예상 리스크 및 대응 방안.
- **비교 분석 추천**: 종합 비교, 우수 사례, 지역/계절별 추천 순위, 최종 기획 방향 제안.

---

## 📊 주요 지표 상세

| 변수명 | 산출 방법 | 사용 모델 / 알고리즘 | 설명 |
|--------|-----------|---------------------|------|
| `avg_satisfaction` | 5단계로 분류된 모든 문장의 만족도 Level의 산술 평균 | numpy.mean + 5단계 분류 로직 | 5점 기준 최종 평균 만족도 점수. |
| `satisfaction_counts` | 1~5점으로 매핑된 문장을 5단계로 그룹화 | collections.Counter | 만족도 5단계 막대 차트의 핵심 데이터. |
| `sentiment_score` | (강한 긍정 문장 수 - 강한 부정 문장 수) / 전체 감성 문장 수 * 50 + 50 | LangGraph Agent + Rule Scorer | 100점 만점의 종합 감성 점수 (50점=중립). |
| `trend_index` | (행사 기간 평균 검색량 / 행사 전 30일 평균 검색량) * 100 | Time Series Analysis (Naver Trend) | 행사 전 대비 행사 중 관심도(화제성) 변화. |
| `satisfaction_delta` | (종합 감성 점수 - 50) / (트렌드 지수 / 100) | Sentiment Flow Analysis | **(핵심 지표)** 화제성 대비 실제 만족도. (예: "소문난 잔치" vs "숨은 보석") |
| `negative_summary` | 모든 '부정' 문장을 수집하여 LLM이 요약 | LLM Summary Agent (utils.py) | "주차", "대기" 등 구체적인 불만 요인 리포트. |
| `overall_summary` | 모든 핵심 지표를 LLM에 전달 | LLM Summary Agent (utils.py) | AI가 생성하는 최종 종합 평가 리포트 (강점/개선점). |
| `new_emotion_terms` | 사전에 없는 표현을 LLM이 추론 | LLM Dynamic Scorer (dynamic_scorer.py) | **(핵심 기술)** 신조어를 자동 학습해 감성 사전을 확장. |

---

## 🏗️ 핵심 아키텍처

**FestInsight**는 단순한 스크립트가 아닌, **'자가 교정'**과 **'동적 학습'** 기능을 갖춘 AI 에이전트 시스템을 기반으로 합니다.

### 1. 자가 교정 피드백 루프 (AI 에이전트)

**LangGraph**(graph.py)를 활용하여 LLM의 창의성과 규칙 기반 시스템의 안정성을 결합했습니다.

```mermaid
graph TD
    A[블로그 본문] --> B(Agent 1: Content Validator);
    B --> C{주제 관련성?};
    C -- 관련 없음 --> D[분석 중단];
    C -- 관련 있음 --> E(Agent 2: LLM Aspect Extractor);
    E --"요약문, (주체,감성)쌍"--> F(Agent 3: Rule Scorer);
    F --> G{점수-감성 일치?};
    G -- No --> H[피드백과 함께 재추출 요청 (최대 3회)];
    H --> E;
    G -- Yes --> I(분석 결과 확정);
```

- **Content Validator**: 관련 없는 광고성 블로그를 1차 필터링합니다.
- **LLM Aspect Extractor**: Gemini가 본문을 요약하고, 감성 표현에 **\*\*마킹**을 하며, '주체-감성 쌍'을 추출합니다.
- **Rule Scorer**: KnowledgeBase를 기반으로 마킹된 요약문의 점수를 계산합니다.
- **Feedback Loop (자가 교정)**: 만약 LLM이 '긍정적'으로 요약했는데 점수가 '음수'(-1.5)로 나오면, LLM에게 피드백을 보내 스스로 재요약 및 수정을 하도록 요청합니다.

### 2. 동적 학습 감성 사전 (Dynamic Scorer)

이 시스템의 가장 독창적인 핵심 기술로, 앱이 **스스로 학습하고 진화**합니다.

```mermaid
graph TD
    A(Rule Scorer) --> B{신규 감성 단어?};
    B -- No --> C(기존 점수 사용);
    B -- Yes --> D(Dynamic Scorer 호출);
    D --"문맥 + '새 단어'"--> E(Gemini LLM);
    E --"추론된 점수 (예: 1.8)"--> D;
    D --> F[KnowledgeBase (.csv)에 자동 추가];
    F --> C;
```

1. **Rule Scorer**가 KnowledgeBase에 없는 신조어(예: "역대급이다")를 발견합니다.
2. **Dynamic Scorer**(dynamic_scorer.py)가 해당 문맥과 단어를 Gemini LLM에게 전달하여 실시간으로 감성 점수를 추론합니다.
3. 추론된 새 단어와 점수(예: 역대급이다, 1.8)를 `adjectives.csv` 같은 **로컬 사전 파일에 자동으로 추가(append)**합니다.
4. **결과**: "학습 루프"가 형성되어, 앱을 사용할수록 감성 사전이 스스로 최신 언어 트렌드를 학습하며 분석 정확도가 지속적으로 향상됩니다.

---

## 🏆 모델 성과 및 개선 방향

### 1. 모델 성과

#### ① 자가 교정 피드백 루프 구축
LangGraph를 활용, LLM(요약)과 규칙(점수화)을 결합했습니다. LLM의 잘못된 분류를 시스템 스스로 방지하여 분석 결과의 일관성과 신뢰도를 확보했습니다.

#### ② 동적 감성 사전 구현 (핵심 성과)
Dynamic Scorer가 사전에 없는 신조어를 발견 시, 실시간으로 LLM을 호출해 점수를 추론하고 사전에 자동 추가합니다. **앱을 사용할수록 감성 사전이 스스로 진화**합니다.

#### ③ 주체-감성 기반(Aspect-Based) 상세 분석
단순 '긍/부정'을 넘어, "왜" 좋았는지(예: 음식)와 "왜" 나빴는지(예: 주차장)를 정량적으로 식별하여 **실행 가능한(actionable)** 인사이트를 도출했습니다.

### 2. 개선 방향

#### ① 멀티모달(Multimodal) 분석 도입
**(Phase 2 연계)** 현재는 **'텍스트'**만 분석하나, 향후 Gemini Vision을 활용하여 블로그의 '이미지'(인파, 음식 비주얼, 포토존)를 함께 분석하여 정확도를 고도화합니다.

#### ② 데이터 소스 확장
'네이버 블로그' 외에 인스타그램, X(트위터), 카카오맵/네이버지도 리뷰 등 다양한 SNS로 데이터 소스를 확장하여 **편향 없는(unbiased)** 여론을 수집합니다.

#### ③ 동적 감성 사전의 DB화
현재 .csv 파일에 추가(append)하는 방식을 SQLite 또는 NoSQL DB로 이전하여, 동시성 문제를 해결하고 대규모 트래픽에도 안정적인 확장성을 확보합니다.

---

## 🚀 향후 계획 (Roadmap)

본 프로젝트는 **3단계의 연속 발전형 계획**을 가지고 있습니다.

### Phase 1: Festival Insight (현재)
- **타겟**: 지자체, 축제 기획자 (B2B)
- **기능**: 텍스트 기반 감성 분석 및 정량적 리포트 제공
- **목표**: 데이터 레시피 공모전 출품, 데이터 기반 의사결정 툴 제공

### Phase 2: Festival Moment (미래)
- **타겟**: 일반 사용자 (B2C)
- **기능**: 멀티모달(텍스트+이미지) AI를 활용한 개인화 축제 추천 (예: "포토존 예쁘고 대기 적은 축제 추천해줘")
- **목표**: 서울 새싹 해커톤 출품, B2C 서비스로 확장

### Phase 3: Festival Geography (최종)
- **타겟**: 글로벌 사용자, 관광 정책 기관
- **기능**: Meta Graph API, Google Maps API 등을 활용한 글로벌 축제 감성 지도 플랫폼 구축
- **목표**: 다국어 지원 및 글로벌 해커톤 출품

---

## 📚 활용 사례

### 사례 1️⃣: 신규 꽃 축제 기획

**배경**: A 시청에서 봄철 매화 축제 개최를 검토 중

**FestInsight 활용**:
- **카테고리 분석**: 계절과 자연 > 꽃 > 매화 카테고리 전체 분석
- **비교 분석**: 성공적인 타 지역 매화 축제 2개 비교
- **AI 추천**: "A시, 봄" 조건으로 AI 기획 방향 도출

**결과**:
- ✅ '주차 공간 부족'이 주요 불만임을 발견 → 사전에 셔틀버스 운행 계획 수립
- ✅ '주체-감성 워드클라우드'에서 '포토존' 만족도가 높음을 확인 → SNS 이벤트 기획
- ✅ AI 추천으로 지역 특산물과 연계한 체험 프로그램 아이디어 확보

### 사례 2️⃣: 기존 축제 개선

**배경**: B 군청의 전통 음식 축제가 3년째 방문객 감소

**FestInsight 활용**:
- **단일 축제 분석**: 자체 축제의 리뷰 감성 분석
- **불만 사항 확인**: AI 불만 사항 요약에서 핵심 문제 파악
- **벤치마킹**: 유사한 성공 축제와 비교 분석

**결과**:
- ⚠️ "음식 가격이 비싸다", "대기 시간이 길다"는 반복적 불만 발견
- ✅ 가격 조정 및 사전 예약제 도입으로 만족도 향상
- ✅ 성공 축제의 "체험 프로그램" 벤치마킹하여 새로운 콘텐츠 도입

---

## 🎯 기대 효과

### 🏛️ 관공서 및 지자체

| 항목 | 기존 방식 | FestInsight 도입 후 |
|------|-----------|---------------------|
| **분석 시간** | 수작업 (수십 시간) | 자동화 (수 분) |
| **분석 대상** | 샘플링 / 주관적 | 블로그 리뷰 전수 (객관적) |
| **핵심 인사이트** | "방문객 OOO명" | "주차장 불만 -1.5점, 음식 만족 +2.0점" |
| **의사결정** | 담당자 경험/감각 | 데이터 기반 (DDDM) |
| **기획 방향** | 타 지역 답사 | AI 맞춤형 기획안 추천 |

### 💼 기대되는 구체적 효과

- **성과 중심의 예산 배분**: "정량화 지표"로 성과 중심의 우선순위 결정 및 예산 효율성 향상
- **구체적인 운영 개선**: "주차 불편" 등 주요 불만 사항을 명확히 파악하여 현장 운영 효율화
- **타깃 맞춤형 홍보 전략**: 트렌드 지수와 감성 데이터를 결합하여 시기별/타깃별 홍보 전략 수립

---

## 🛠️ 기술 스택

### 🖥️ Backend

| 분류 | 기술 | 역할 |
|------|------|------|
| **Framework** | FastAPI, Uvicorn | REST API 서버, 비동기(Async) 스트리밍 처리 |
| **Language** | Python 3.11 | 백엔드 핵심 언어 |
| **AI/ML** | LangGraph | 자가 교정 및 동적 학습 AI 에이전트 워크플로우 |
| | Google Gemini 2.5 Pro | LLM 감성 분석, 요약, AI 추천 |
| | LangChain | LLM 프롬프트 관리 |
| **Data Processing** | Pandas, NumPy | 데이터 전처리 및 통계 분석 |
| **Web Scraping** | Selenium, BeautifulSoup4 | 네이버 블로그 스마트에디터 크롤링 |
| **NLP** | KoNLPy (Okt) | 한국어 형태소 분석 (감성 사전 매칭용) |
| **Visualization** | Matplotlib, WordCloud | 트렌드 그래프, 워드클라우드 이미지 생성 |
| **Storage** | SQLite | 축제 마스터 데이터베이스 (tour_data.db) |
| **Caching** | JSON (File Cache) | 분석 결과 캐시 (API 응답 속도 향상) |

### 🎨 Frontend

| 분류 | 기술 | 역할 |
|------|------|------|
| **Framework** | React 18 | UI 프레임워크 |
| **Language** | TypeScript | 타입 안전성 |
| **Build Tool** | Vite 5 | 초고속 빌드 및 HMR |
| **Styling** | TailwindCSS 3 | 유틸리티 기반 CSS |
| **State Management** | TanStack Query (React Query) | 서버 상태 관리, API 캐싱 (localStorage 연동) |
| | Zustand | 경량 클라이언트 상태 관리 |
| **Charting** | Recharts | 인터랙티브 동적 차트 라이브러리 |
| **Routing** | React Router DOM 6 | SPA 라우팅 |
| **Markdown** | React Markdown | AI 분석 결과 렌더링 (GFM, HTML 포함) |
| | remark-gfm, rehype-raw | Markdown 테이블 및 HTML 렌더링 플러그인 |
| **UI/UX** | Framer Motion | 페이지 전환 애니메이션 |

### 🔗 External APIs

- **Naver Search API**: 블로그 검색
- **Naver Trend API**: 검색량 트렌드 데이터
- **Google Gemini API**: LLM 분석 및 요약

---

## 🚀 설치 및 빠른 시작

### 📋 사전 준비

#### 1. 시스템 요구사항

- **Python**: 3.11 이상 권장
- **Node.js**: 18 이상
- **Chrome 브라우저**: 최신 버전 (Selenium 크롤링용)

#### 2. API 키 발급

필수 API 키 3개:

- **Google Gemini API Key**
  - [Google AI Studio](https://aistudio.google.com/)에서 발급
- **Naver Search API**
  - [Naver Developers](https://developers.naver.com/)에서 "검색" API 선택 → Client ID, Secret 발급
- **Naver Trend API**
  - [Naver Developers](https://developers.naver.com/)에서 별도 앱 등록, "데이터랩(검색어 트렌드)" API 선택

#### 3. `.env` 파일 생성

프로젝트 루트(`GradioNaverSentiment/`)에 `.env` 파일을 생성하고 아래 내용을 채웁니다:

```bash
# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here

# Naver Search API (블로그 검색)
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here

# Naver Trend API (검색량 트렌드)
NAVER_TREND_CLIENT_ID=your_trend_client_id_here
NAVER_TREND_CLIENT_SECRET=your_trend_client_secret_here
```

---

### 💻 설치 가이드

#### Step 1: 프로젝트 클론

```bash
git clone https://github.com/yourusername/GradioNaverSentiment.git
cd GradioNaverSentiment
```

#### Step 2: 백엔드 설정 (터미널 1)

```bash
# 1. 가상환경 생성
python -m venv venv

# 2. 가상환경 활성화
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 백엔드 서버 실행
python api_server.py
```

**확인**: 터미널에 `[START] GradioNaverSentiment API Server Starting...` 메시지가 표시되고, `http://localhost:8001/docs` 접속 시 FastAPI Swagger UI가 보이면 성공입니다.

#### Step 3: 프론트엔드 설정 (터미널 2)

새로운 터미널을 열어서 아래 명령어를 실행합니다:

```bash
# 1. 프론트엔드 폴더로 이동
cd frontend

# 2. 의존성 설치 (package.json + 누락된 플러그인)
npm install
npm install -D @tailwindcss/typography
npm install rehype-raw

# 3. 개발 서버 실행
npm run dev
```

**확인**: 터미널에 `Local: http://localhost:5173/` 메시지가 표시되고, 브라우저에서 해당 주소 접속 시 FestInsight 홈페이지가 보이면 성공입니다.

---

### 🎯 첫 분석 실행하기

1. **홈페이지 접속**: 브라우저에서 `http://localhost:5173` 로 이동합니다.
2. **검색 페이지 이동**: 상단 네비게이션바에서 **"검색"**을 클릭합니다.
3. **축제 분석 실행**:
   - 축제명(예: 강릉커피축제)을 입력하고 "분석 시작" 버튼을 클릭합니다.
4. **결과 확인**:
   - 실시간 스트리밍으로 진행률이 표시됩니다.
   - 약 1-2분 후, 분석 대시보드가 나타납니다.
5. **AI 추천 받기**:
   - 페이지 하단으로 스크롤하여 "AI 총합 분석 추천" 섹션으로 이동합니다.
   - 지역(예: 서울)과 계절(예: 가을)을 선택하고 "AI 추천 분석 시작" 버튼을 클릭합니다.
   - 약 10-20초 후 AI가 생성한 맞춤형 기획 리포트를 확인합니다.

---

## 📁 프로젝트 구조

```
GradioNaverSentiment/
│
├── 📄 api_server.py                  # 🚀 FastAPI 백엔드 서버 (API 엔드포인트)
├── 📄 requirements.txt               # 🐍 Python 의존성
├── 📄 .env                           # 🔑 API 키 (Git 무시)
├── 📄 2025년 새싹 해커톤 AI 서비스 기획서 양식_최종.docx  # 📝 새싹 해커톤 신청서
│
├── 📂 src/                           # 📦 Python 백엔드 소스
│   ├── 📂 application/
│   │   ├── analysis_logic.py        # 🧠 (핵심) 축제/카테고리 분석 오케스트레이터
│   │   ├── seasonal_analysis.py     # 📅 (핵심) 계절별 트렌드 분석
│   │   ├── utils.py                 # 🤖 (핵심) AI 요약/추천, 캐시 관리
│   │   └── 📂 agents/
│   │       ├── content_validator.py # Agent 1: 관련성 검증
│   │       ├── llm_summarizer.py    # Agent 2: 주체-감성 추출 (****)
│   │       └── rule_scorer.py       # Agent 3: 점수화 및 피드백
│   │
│   ├── 📂 domain/
│   │   ├── knowledge_base.py        # 📚 감성 사전(.csv) 로드
│   │   └── state.py                 # 📌 LangGraph 상태 객체
│   │
│   ├── 📂 infrastructure/
│   │   ├── dynamic_scorer.py        # 💡 (핵심) 동적 학습 스코어러
│   │   ├── llm_client.py            # 🌐 Gemini 클라이언트
│   │   ├── 📂 database/
│   │   │   ├── db_manager.py        # 🗄️ SQLite 스키마
│   │   │   ├── festival_repository.py # 🗄️ DB 조회 로직 (@lru_cache)
│   │   │   └── csv_importer.py      # 🗄️ CSV to DB 임포터
│   │   ├── 📂 web/
│   │   │   ├── scraper.py           # 🕷️ Selenium 크롤러
│   │   │   ├── naver_api.py         # 🛰️ Naver 검색 API
│   │   │   ├── naver_trend_api.py   # 🛰️ Naver 트렌드 API
│   │   │   └── tour_api_client.py   # 🛰️ (실제론 DB 조회)
│   │   └── 📂 reporting/
│   │       ├── wordclouds.py        # ☁️ 주체-감성 워드클라우드
│   │       └── seasonal_wordcloud.py # ☁️ 트렌드 워드클라우드
│   │
│   └── 📄 config.py                 # ⚙️ 설정 및 .env 로더
│
├── 📂 frontend/                      # 🎨 React 프론트엔드
│   ├── 📂 src/
│   │   ├── 📂 pages/
│   │   │   ├── HomePage.tsx         # 🏠 메인 페이지
│   │   │   ├── SearchPage.tsx       # 🔍 검색 페이지
│   │   │   ├── AnalysisPage.tsx     # 📊 단일 분석 결과
│   │   │   ├── CategoryAnalysisPage.tsx  # 🗂️ 카테고리 분석
│   │   │   ├── ComparisonPage.tsx   # ⚖️ 비교 분석
│   │   │   └── SeasonalTrendPage.tsx # 📅 계절별 트렌드
│   │   │
│   │   ├── 📂 components/
│   │   │   ├── 📂 charts/           # 📈 (Recharts) 동적 차트
│   │   │   ├── BlogTable.tsx        # 📑 상세 블로그 테이블 (**** 하이라이트)
│   │   │   ├── ExplanationToggle.tsx # 💡 도움말 토글
│   │   │   ├── Layout.tsx           # 뼈대 (Nav, Footer)
│   │   │   └── SeasonalTabs.tsx     # 🌸 계절 탭
│   │   │
│   │   ├── 📂 lib/
│   │   │   ├── api.ts               # 📡 (핵심) API/스트리밍 클라이언트
│   │   │   └── explanations.ts      # 📖 지표 설명 텍스트
│   │   │
│   │   ├── 📂 types/
│   │   │   └── index.ts             # 🇹🇸 TypeScript 타입
│   │   │
│   │   ├── App.tsx                  # 🛣️ React Router 설정
│   │   ├── main.tsx                 # ⚛️ React DOM + TanStack Query (캐시)
│   │   └── index.css                # 💅 (Tailwind)
│   │
│   ├── 📄 package.json              # 📦 Node.js 의존성
│   ├── 📄 vite.config.ts            # ⚡ Vite 설정 (프록시)
│   └── 📄 tailwind.config.js       # 🎨 Tailwind 설정
│
├── 📂 database/                      # 💾 데이터
│   ├── tour_data.db                 # SQLite DB 파일
│   └── (원본 CSV 파일들)
│
├── 📂 festivals/                     # 🗂️ 축제 카테고리 (JSON)
│   └── (8개 테마 JSON 파일)
│
├── 📂 dic/                           # 📚 감성 사전 (Dynamic Scorer가 수정)
│   ├── adjectives.csv, adverbs.csv, ... (7종)
│
├── 📂 assets/                        # 🖼️ 정적 자산
│   └── mask_*.png                   # 워드클라우드 마스크
│
├── 📂 cache/                         # 💽 백엔드 캐시
│   └── *.json                       # 분석 결과 캐시
│
└── 📂 temp_images/                   # 🌄 생성된 이미지 (차트, 워드클라우드)
    └── *.png
```

---

## 🎬 시연 영상

<div align="center">

### FestInsight 전체 기능 시연

<p align="center">
<img src="videos/시연영상.gif" alt="FestInsight 시연 영상" width="100%">
</p>

**주요 기능**: 검색, 단일/카테고리 분석, 비교 분석, 계절별 트렌드, AI 추천

</div>

---

## ⚠️ 문제 해결

### 🔧 자주 발생하는 문제

#### 1. ModuleNotFoundError: No module named 'XXX'

**원인**: Python 패키지가 설치되지 않음
**해결**:

```bash
# 가상환경 활성화 확인
.\venv\Scripts\Activate.ps1  # Windows
# 또는
source venv/bin/activate  # macOS/Linux

# 의존성 재설치
pip install -r requirements.txt
```

#### 2. 프론트엔드가 실행되지 않음

**원인**: Node.js 패키지 미설치 (특히 `@tailwindcss/typography` 또는 `rehype-raw`)
**해결**:

```bash
cd frontend
npm install
npm install -D @tailwindcss/typography
npm install rehype-raw
npm run dev
```

#### 3. CORS policy 에러 (프론트 로딩 실패)

**원인**: 백엔드 서버가 실행되지 않음 (프록시 대상이 없음)
**해결**:
- 터미널 1에서 `python api_server.py`가 실행 중인지 확인합니다.
- 백엔드를 먼저 실행한 후 프론트엔드(`npm run dev`)를 실행합니다.

#### 4. API Key Error 발생

**원인**: `.env` 파일의 API 키가 잘못됨
**해결**:
- `.env` 파일 확인 (프로젝트 루트에 위치)
- API 키가 올바르게 입력되었는지 확인
- Google Gemini API 할당량 확인

#### 5. AttributeError: 'NoneType' object has no attribute '...'

**원인**: `create_driver()` 실패 (Selenium/Chrome)
**해결**:
- PC에 Chrome 브라우저가 설치되어 있는지 확인합니다.
- `webdriver-manager`가 ChromeDriver를 올바르게 설치했는지 확인합니다.

---

## 🤝 기여하기

**FestInsight**는 오픈소스 프로젝트입니다. 기여를 환영합니다!

### 기여 방법

1. 이 저장소를 Fork합니다
2. 새로운 기능 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

### 개선 아이디어

- [ ] 추가 차트 타입 (히트맵, 산점도 등)
- [ ] 엑셀/PDF 리포트 자동 생성
- [ ] 실시간 알림 (새로운 리뷰 감지)
- [ ] 다국어 지원
- [ ] 모바일 앱 개발

---

## 📄 라이선스

이 프로젝트는 **교육 및 연구 목적**으로 제작되었습니다.

### 사용 제한

- ❌ **상업적 사용 금지**: 본 소프트웨어를 판매하거나 유료 서비스로 제공할 수 없습니다
- ❌ **라이선스 제거 금지**: 본 README의 출처 표시를 제거할 수 없습니다

### 허용 사항

- ✅ **개인 학습 및 연구**: 자유롭게 사용 가능
- ✅ **수정 및 배포**: Fork하여 개선하고 공유 가능 (출처 명시 필수)
- ✅ **관공서/비영리 사용**: 공익 목적의 무료 사용 가능

### 데이터 출처

- **네이버 블로그 데이터**: Naver Search API
- **검색량 트렌드**: Naver DataLab API
- **축제 정보**: TourAPI (한국관광공사)

---

## 📞 문의 및 지원

### 버그 리포트 및 기능 제안

GitHub Issues를 통해 문의해주세요:
👉 [Issue 등록하기](https://github.com/yourusername/GradioNaverSentiment/issues)

### 이메일 문의

📧 ericyum9196@gmail.com

---

<div align="center">

**Made with ❤️ for Festival Planners**

⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요!

[⬆️ 맨 위로 돌아가기](#-festinsight---ai-기반-축제-감성-분석-플랫폼)

</div>
