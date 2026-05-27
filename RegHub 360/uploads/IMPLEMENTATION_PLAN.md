# RegHub 360 — 의약품·의약외품·식품 통합 규제정보 허브 구현 계획

> **프로젝트명**: RegHub 360
> **한 줄 설명**: 식약처 공공 API를 의약품·의약외품·식품 실무자의 업무 질문 기준으로 통합 조회하는 SaaS급 규제정보 플랫폼
> **문서 버전**: v1.0 (2026-05-26)
> **관련 문서**: [API_APPLICATION_LIST.md](API_APPLICATION_LIST.md) · [README.md](README.md) · [API_STATUS.md](API_STATUS.md)

---

## 목차
1. [배경 및 문제 정의](#1-배경-및-문제-정의)
2. [대상 사용자와 워크스페이스](#2-대상-사용자와-워크스페이스)
3. [통합 검색 (6개 기준)](#3-통합-검색-6개-기준)
4. [Product 360 상세 화면](#4-product-360-상세-화면)
5. [통합 이벤트 타임라인](#5-통합-이벤트-타임라인-핵심-기능)
6. [리스크 점수 산정 로직](#6-리스크-점수-산정-로직)
7. [MVP API 카탈로그](#7-mvp-api-카탈로그-12개-축)
8. [데이터 표준화 3-Layer](#8-데이터-표준화-3-layer)
9. [업체명·제품명 정규화](#9-업체명제품명-정규화-전략)
10. [통합 데이터 모델](#10-통합-데이터-모델)
11. [시스템 아키텍처](#11-시스템-아키텍처)
12. [주요 기능 정의서](#12-주요-기능-정의서)
13. [부서별 활용 시나리오](#13-부서별-활용-시나리오)
14. [디렉토리·코드 변경 단위](#14-디렉토리코드-변경-단위)
15. [데이터 품질·신뢰성 장치](#15-데이터-품질신뢰성-장치)
16. [구현 로드맵](#16-구현-로드맵)
17. [검증 방법](#17-검증-방법)
18. [발표용 메시지](#18-발표용-메시지)
19. [미해결 항목](#19-미해결후속-검증-필요-항목)

---

## 1. 배경 및 문제 정의

### 1-1. 문제
의약품·의약외품·식품 제조·수입·유통 회사의 실무자는 식약처, 공공데이터포털, 식품안전나라, 심평원, 식의약 데이터포털을 부서별로 따로 매일 수동 조회한다.

- **RA**: 허가·갱신·임상·특허
- **QA/QC**: 회수·행정처분·GMP·검사부적합
- **영업**: 경쟁사 제품·행정처분
- **SCM**: 공급중단·공급부족

회수·행정처분·안전성서한·공급중단을 놓치면 실손해가 크다.

### 1-2. 차별점
기존 서비스가 "API별 조회"라면 RegHub 360은 **실무 질문 기준 조회**다.

사용자가 `타이레놀`, `아세트아미노펜`, `광동제약`, `마스크`, `홍삼`, `원료명`을 입력하면 다음을 자동으로 묶어 보여준다:
- 허가·회수·행정처분·안전성·DUR·공급중단
- GMP·HACCP·임상·특허
- 마약류 통계·식품 원재료·영양·푸드QR
- 검사부적합·해외 위해식품

### 1-3. 기존 자산
| 자산 | 위치 | 상태 |
|---|---|---|
| Flask 웹앱 | [app.py](app.py) | 4개 API 연동 (허가/처분/회수/낱알) |
| API 클라이언트 | [api_client.py](api_client.py) | 재시도·SSL 폴백 로직 |
| 엑셀 캐시 | [excel_data_loader.py](excel_data_loader.py) | 허가정보 API 404 우회 |
| MISO 워크플로우 | [miso_workflows/](miso_workflows/) | 일일 회수/처분 리포트, 통합검색, 컨설팅 에이전트 |
| API 카탈로그 | [공공데이터 목록.xlsx](공공데이터%20목록.xlsx) | 총 603건 (식품 279·의약품 99·의료기기 84·바이오 44·기타 97) |

### 1-4. 기술 결정 (확정)
1. **프론트엔드**: Flask 유지 + Tailwind+Alpine.js+HTMX로 점진 현대화
2. **API 범위**: MVP 12개 축 + 확장 API 카탈로그
3. **MVP 기능**: 부서별 워크스페이스 + 워치리스트 알림 + 엑셀/PDF + AI 자연어 검색
4. **데이터**: PostgreSQL + 일일 배치 + Redis 캐시
5. **로드맵**: 1단계 해커톤 MVP → 2단계 실무형 PoC → 3단계 상용 SaaS

---

## 2. 대상 사용자와 워크스페이스

로그인 시 사용자 부서에 맞춰 초기 대시보드·탭·필터가 달라지는 **Role-based Workspace** 구조. Product 360 상세 화면은 부서 무관 공통.

| 부서 | 주요 니즈 | 워크스페이스 위젯 |
|---|---|---|
| **RA / 허가** | 허가, 갱신, 재심사, 재평가, 임상, 특허, 안전성서한 | 허가 갱신 D-30 캘린더, 신규 안전성서한, 재심사 임박 |
| **QA/QC** | 회수, 판매중지, 행정처분, GMP, 검사부적합, DUR | 자사·동성분 회수 24h, 행정처분 7d, GMP 만료 임박 |
| **SCM / 구매** | 공급중단, 공급부족, 원료 DMF, 국가출하, 수입식품 리스크 | 공급중단 알림, 원료 DMF 변경, 국가출하 지연 |
| **영업 / 마케팅** | 경쟁사 제품, 행정처분, 회수 이력, 묶음의약품 | 경쟁사 행정처분, 묶음의약품(HIRA/ATC), 신규 허가 |
| **R&D / BD** | 임상, 특허, 생동성, 대조약, 희귀, 마약류 시장통계 | 특허 만료 D-365, FDA 오렌지북, 임상 단계 변동 |
| **식품 QA / RA** | 품목제조보고, 원재료, 영양, 푸드QR, 회수, 행정처분, HACCP | 자사·동종 식품 회수·처분, 검사부적합, 해외 위해식품 |
| **경영진 / 관리자** | 자사·경쟁사 리스크, 일일 리포트 | 통합 리스크 대시보드 + 일일 메일 |

---

## 3. 통합 검색 (6개 기준)

| 검색 기준 | 예시 | 내부 매핑 |
|---|---|---|
| 제품명 | 타이레놀, 활명수, 홍삼정 | `canonical_product.name` |
| 업체명 | 광동제약, CJ제일제당 | `canonical_company.name` (정규화) |
| 성분명 | 아세트아미노펜, 이부프로펜, 카페인 | `canonical_ingredient.name` |
| 원재료명 | 감초, 홍삼, 우유, 대두 | `canonical_ingredient.raw_material` |
| 품목기준코드 / 인허가번호 | 의약품 품목코드, 식품 인허가번호 | 공공 API PK |
| 바코드 / 푸드QR / 표준코드 | 식품 QR, 의약품 표준코드 | 코드 매핑 테이블 |

PostgreSQL `pg_trgm`(한글 trigram) + 별도 alias 테이블로 동의어·약칭·영문표기 흡수.

---

## 4. Product 360 상세 화면

### 4-1. 의약품/의약외품 Product 360 (8개 섹션)
1. **기본정보** — 제품명, 업체명, 품목기준코드, 허가번호/일자, 전문/일반, 제형, 저장방법
2. **허가·변경 이력** — 허가정보, 갱신 필요 여부, 재심사·재평가, 희귀·필수의약품
3. **안전성 정보** — 안전성서한, DUR, e약은요, 장애인 안전사용 정보(음성·수어)
4. **품질·규제 이벤트** — 회수·판매중지, 행정처분, 마스크 회수, 마스크 행정처분
5. **공급망 정보** — 생산수입공급중단, 공급부족, 생산·수입실적, 원료 DMF
6. **개발·BD 정보** — 임상시험, 특허, 국내소송, FDA 오렌지북, Paragraph IV, 생동성, 대조약
7. **마약류 분석** — 품목허가, 제조·수입·수출, 성분별 처방, 지역별 취급자
8. **낱알식별·이미지** — 모양, 색상, 식별문자, 이미지(기존 [static/images/](static/images/) 자산 재사용)

### 4-2. 식품 Product 360 (6개 섹션)
1. **기본정보** — 제품명, 업체명, 식품유형, 품목제조보고번호, 인허가번호
2. **표시·원재료** — 푸드QR, 원재료, 알레르기, 보관방법, 용기·포장재질
3. **영양성분** — 열량/탄/단/지/나트륨 등 표시 비교
4. **위해 이벤트** — 국내 회수, 수입식품 회수, 해외 위해식품 회수, 검사부적합
5. **행정처분** — 식품제조가공업/식품판매업/수입식품업/식품접객업 통합
6. **인증·관리** — HACCP, 스마트 HACCP, 건기식 GMP, 이력추적

### 4-3. 출처 표시 정책
모든 카드에 **"출처: ○○ API · 동기화 N분 전"** 배지 표시.
식의약 데이터포털 안내(인허가 진행중·폐기·취하 데이터 누락 가능성)도 푸터에 노출 → 사용자 신뢰성 확보.

---

## 5. 통합 이벤트 타임라인 (핵심 기능)

의약품·의약외품·식품의 모든 위험·규제 이벤트를 **단일 포맷으로 평면화**해 한 화면에서 본다.

### 5-1. 포함 이벤트
| 이벤트 구분 | 포함 데이터 |
|---|---|
| 회수 | 의약품 회수, 마스크 회수, 식품 회수, 수입식품 회수, 해외 위해식품 회수 |
| 판매중지 | 의약품 판매중지, 식품 판매중지 |
| 행정처분 | 의약품 행정처분, 마스크 행정처분, 식품 4종 행정처분 |
| 안전성 | 안전성서한, DUR, 장애인 안전사용 정보 |
| 공급망 | 공급중단, 공급부족, 생산수입실적 급감 |
| 검사부적합 | 국내 식품·농산물·수입식품 부적합 |
| 인증 리스크 | GMP/HACCP 만료·취소·변경 |

### 5-2. 표준 스키마 `event_timeline`
```
event_id              PK
domain                drug | quasi_drug | food | health_functional_food
event_type            recall | sales_stop | disciplinary | safety_letter
                     | supply_shortage | inspection_fail | permit_change
severity              critical | high | medium | low
product_name
company_name
canonical_product_id  FK → canonical_product
canonical_company_id  FK → canonical_company
ingredient_or_raw     FK → canonical_ingredient (null 허용)
event_date
source_api            발신 API명
source_url            원본 레코드 링크
summary               단문 요약
action_required       조치 권장사항
department_tags[]     [RA, QA, QC, SCM, Sales, R&D, FoodQA]
raw_record_id         FK → raw_api_response (감사용)
```

### 5-3. 표시 예시
```
[HIGH] 의약품 회수
제품명: ○○정 / 업체명: △△제약
사유: 품질 부적합
영향부서: QA, RA, 영업
권장조치: 자사 동일성분 품목 확인 → 공급처 재고 확인 → 고객사 안내
```

---

## 6. 리스크 점수 산정 로직

각 제품·업체별로 자동 산정해 대시보드 KPI·정렬 기준으로 사용.

```
Risk Score = Σ(이벤트별 가중치) × 최근성 보정 × 반복발생 보정
```

| 이벤트 | 점수 |
|---|---|
| 최근 30일 회수 | +40 |
| 최근 90일 행정처분 | +30 |
| 검사부적합 | +25 |
| 안전성서한 | +20 |
| 공급중단·공급부족 | +20 |
| 동일 업체 반복 발생 | +10 |
| 동일 성분/원재료 반복 발생 | +10 |

| 점수 | 등급 | 의미 |
|---|---|---|
| 80 이상 | Critical | 즉시 검토 |
| 60~79 | High | 부서 알림 |
| 40~59 | Medium | 모니터링 |
| 20~39 | Low | 참고 |
| 0~19 | Normal | 특이사항 없음 |

산정 로직은 `services/risk_scoring.py`에 분리, 가중치는 `services/risk_weights.yml`로 운영자 편집 가능.

---

## 7. MVP API 카탈로그 (12개 축)

> 각 API의 신청 URL은 [API_APPLICATION_LIST.md](API_APPLICATION_LIST.md) 참고.

### 7-1. 의약품 (5종)
| API | 목적 | 엑셀 NO |
|---|---|---|
| 의약품 제품 허가정보 | 제품 마스터 | 140 |
| 의약품 회수·판매중지 | 품질 이벤트 (기존 연동) | 539 |
| 의약품 행정처분 | 규제 이벤트 (기존 연동) | 564 |
| 의약품 안전성서한 + DUR 품목/성분 | 안전성 이벤트 | 547, 531, 533 |
| 의약품 생산수입공급중단 + 공급부족 | 공급망 이벤트 | 534, 537 |

### 7-2. 의약외품 (3종)
| API | 목적 | 엑셀 NO |
|---|---|---|
| 의약외품 제품 허가정보 | 의약외품 마스터 | 145, 518 |
| 마스크 회수 제품 정보 | 의약외품 회수 | 172 |
| 마스크 관련 업체 행정처분 | 의약외품 처분 | 162 |

### 7-3. 식품 (4종)
| API | 목적 | 엑셀 NO |
|---|---|---|
| 식품 회수 및 판매중지 (+수입식품+해외 위해식품) | 식품 안전 이벤트 | 339, 153, 225 |
| 식품 행정처분 (4업종 통합) | 식품 규제 이벤트 | 6, 5, 3, 477 |
| 식품(첨가물) 품목제조보고 + 원재료 | 식품 제품 상세 | 444, 470 |
| 푸드QR + 식품 영양성분 | 표시·소비자 정보 | (푸드QR) + 555, 1 |

### 7-4. MVP 화면 (7종)
1. 통합 검색 화면
2. Product 360 상세 화면 (의약품/의약외품/식품)
3. 통합 이벤트 타임라인
4. 부서별 워크스페이스 (6종)
5. 워치리스트 등록
6. 일일 리스크 리포트 (엑셀/PDF)
7. AI 질의 요약 화면

### 7-5. 확장 API 카탈로그 (Phase 2~3)
- **의약품 추가**: e약은요(248), 묶음의약품/HIRA(269), GMP(132), 국가출하(142), 업체허가(144), DMF(483), 특허(561·557·552·562), 임상(566·568), 대조약·생동성(484·485), 재심사·재평가(554·556), 희귀(565·81), 안전상비(134), 마약류 통계 시리즈
- **식품 추가**: 검사부적합(469·535), 유해물질 기준규격(491), 허위·과대광고(538), HACCP(12·13·128), 수입식품 원료·표시·방사능
- **건기식**: 품목제조 신고(478), GMP(51), 영양DB(203), 개별인정형(334), 이상사례

---

## 8. 데이터 표준화 (3-Layer)

### 8-1. Raw Layer — API 원문 그대로 저장
```
raw_api_response
  id, source_api, request_url, request_params,
  response_json_or_xml, fetched_at, status, hash
```
**목적**: API 스키마 변경·데이터 누락·재처리 가능성 확보. 감사 추적.

### 8-2. Standard Layer — 공통 필드로 정규화
```
standard_product, standard_company, standard_ingredient,
standard_event, standard_permit, standard_food_label,
standard_clinical, standard_patent
```

### 8-3. Service Layer — 화면 조회용 재가공
```
product_360_view, company_360_view, event_timeline_view,
watchlist_alert_view, department_dashboard_view,
risk_score_view
```
PostgreSQL 머티리얼라이즈드 뷰 + Redis 캐시(1h TTL).

---

## 9. 업체명·제품명 정규화 전략

업체명은 공백·"주식회사"·괄호·영문표기 차이로 매칭 오류가 빈번하다.

**예시 동일 업체:**
- 광동제약
- 광동제약(주)
- 주식회사 광동제약
- KWANGDONG PHARMACEUTICAL

### 정규화 파이프라인 (`api_client/normalizer.py`)
1. "주식회사", "(주)", "㈜", "Co., Ltd." 토큰 제거
2. 공백·특수문자 제거
3. 영문 대문자화 + 한영 동의어 사전 적용
4. **사업자등록번호가 있으면 사업자번호 우선 매칭** (가장 신뢰)
5. 주소 유사도(jaro_winkler) + 업체명 유사도 가중 평균
6. 신뢰도 0.85 이상이면 동일 entity로 병합, 0.6~0.85는 검토 큐로

성분명·원재료명도 동일 패턴: 표준성분명 사전 + 영문/한글/이명 alias 테이블.

---

## 10. 통합 데이터 모델

### 10-1. Canonical 마스터 (4종)
| 테이블 | 키 형식 |
|---|---|
| `canonical_product` | `drug:{품목기준코드}` / `quasi:{허가번호}` / `food:{품목제조보고번호 or 인허가번호}` |
| `canonical_company` | `company:{사업자등록번호}` 또는 `company:hash({업체명}+{주소})` |
| `canonical_ingredient` | `ingredient:{표준성분명}` 또는 `raw:{원재료표준명}` |
| `canonical_code` | 바코드·푸드QR·표준코드 → canonical_product 매핑 |

### 10-2. 도메인 팩트 테이블
`drug_permit`, `quasi_permit`, `food_report`, `food_qr`, `drug_safety`, `drug_supply`, `drug_clinical`, `drug_patent`, `narcotic_statistics`

### 10-3. 통합 운영 테이블
`event_timeline`, `watchlist`, `alert_outbox`, `sync_log`, `raw_api_response`, `risk_score_history`

### 10-4. 사용자·조직
`user`, `org`(멀티테넌트), `role`(RBAC), `department_preset`(부서별 위젯 프리셋)

---

## 11. 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────────┐
│  사용자 브라우저 (Tailwind + Alpine.js + HTMX)               │
│  통합검색 / 워크스페이스 / Product 360 / 알림 / 리포트 / AI   │
└──────────────────────────────────────────────────────────────┘
              │ HTTP
┌──────────────────────────────────────────────────────────────┐
│  Flask Backend                                                │
│  Blueprints: auth · search · product · event · watchlist ·   │
│              alerts · reports · copilot · admin · api(JSON)  │
│  Auth: Flask-Login + RBAC (조직·부서 권한)                   │
└──────────────────────────────────────────────────────────────┘
              │
┌──────────────────────────────────────────────────────────────┐
│  Service Layer                                                │
│  - Product Matching   - Company Matching                     │
│  - Event Normalizer   - Risk Scoring Engine                  │
│  - Report Generator   - AI Summary Agent (MISO 프록시)        │
└──────────────────────────────────────────────────────────────┘
              │
┌──────────────────────────────────────────────────────────────┐
│  Data Layer                                                   │
│  PostgreSQL (3-layer)  ·  Redis Cache  ·  Sync Log            │
└──────────────────────────────────────────────────────────────┘
              ▲ 야간 배치
┌──────────────────────────────────────────────────────────────┐
│  Collectors (APScheduler + 기존 api_client.py 확장)           │
│  - API별 fetch_*() · 증분 파라미터(updateDe·CHNG_DT)          │
│  - Raw 저장 → 정규화 → diff 감지 → event_timeline INSERT      │
│  - INSERT 트리거 → 워치리스트 매칭 → alert_outbox enqueue     │
└──────────────────────────────────────────────────────────────┘
              │
┌──────────────────────────────────────────────────────────────┐
│  External APIs                                                │
│  식약처 의약품·의약외품·식품 / 식품안전나라·HACCP·건기식     │
│  / 마약류 통계 / 푸드QR / (확장) HIRA                         │
└──────────────────────────────────────────────────────────────┘
              │
┌──────────────────────────────────────────────────────────────┐
│  Notifier  (이메일 / 슬랙 / 카카오워크 / 일일 리포트 메일)    │
└──────────────────────────────────────────────────────────────┘
```

---

## 12. 주요 기능 정의서

| ID | 기능 | 입력 | 처리 | 출력 | 우선순위 |
|---|---|---|---|---|---|
| F-001 | 통합 검색 | 6개 기준 | 전체 API 후보 검색 | 그룹별 결과 | MVP 필수 |
| F-002 | Product 360 상세 | canonical_product_id | 8섹션(의약품)/6섹션(식품) 병합 | 탭 기반 상세 | MVP 필수 |
| F-003 | 통합 이벤트 타임라인 | 제품/업체/성분/원재료, 기간, 유형 | 7개 이벤트 통합 | 중요도별 카드+날짜 타임라인 | MVP 필수 |
| F-004 | 부서별 워크스페이스 | 로그인 부서 | 부서 프리셋 적용 | 위젯 대시보드 | MVP 필수 |
| F-005 | 워치리스트 알림 | 제품·업체·성분·원재료·식품유형 | event_timeline INSERT 시 매칭 | 이메일/슬랙/카카오워크 | MVP 권장 |
| F-006 | AI 자연어 검색 | 자연어 질문 | MISO 에이전트 + 공식 API 결과 요약 | 답변 + 근거 카드 + 원문 링크 | MVP 권장 |
| F-007 | 일일 리스크 리포트 | 부서/조직/기간 | event_timeline 집계 + 리스크 점수 | 엑셀/PDF | MVP 권장 |
| F-008 | 리스크 스코어 대시보드 | 자사·경쟁사 업체 | risk_score 산정 | 등급별 카드+추이 차트 | MVP 권장 |

---

## 13. 부서별 활용 시나리오

| 부서 | 시나리오 |
|---|---|
| **RA** | 자사 제품명 입력 → 허가, 재심사, 재평가, 안전성서한, 임상, 특허 한 화면 확인 → 변경 필요사항 리포트 저장 |
| **QA/QC** | 자사 업체명 입력 → 회수·행정처분·검사부적합·GMP 확인 → **동일 성분/원재료 제품까지 확장 검색** |
| **SCM** | 주요 성분·원재료 등록 → 공급중단·공급부족·수입식품 리스크 발생 시 자동 알림 |
| **영업** | 경쟁사 업체명 입력 → 최근 행정처분·회수·신규 허가 확인 → 거래처 대응자료 자동 생성 |
| **R&D/BD** | 성분명 입력 → 임상·특허만료·생동성·대조약·마약류 시장통계 확인 → 개발 후보 검토 |
| **식품 QA** | 제품명/원재료명 입력 → 품목제조보고·원재료·영양·푸드QR·회수·행정처분·검사부적합 통합 확인 |
| **경영진** | 자사·경쟁사 리스크 점수 대시보드 + 일일 메일 |

---

## 14. 디렉토리·코드 변경 단위

### 14-1. 재활용·확장 대상
| 파일 | 변경 방향 |
|---|---|
| [api_client.py](api_client.py) | `_make_request`, SSL 폴백, 재시도 로직 유지. `api_client/` 패키지로 분할 |
| [excel_data_loader.py](excel_data_loader.py) | 허가정보 API 폴백으로 유지. 캐시 메타데이터 패턴 재사용 |
| [config.py](config.py) | `API_ENDPOINTS` 12→30+로 확장. **SERVICE_KEY 하드코딩 fallback 제거 + ENV 강제** (상용화 필수) |
| [miso_workflows/drug_daily_recall_report.yml](miso_workflows/drug_daily_recall_report.yml) | F-007 일일 리포트 본문 생성기 |
| [miso_workflows/drug_daily_disciplinary_report.yml](miso_workflows/drug_daily_disciplinary_report.yml) | F-007 처분 다이제스트 |
| [miso_workflows/drug_consult_agent.yml](miso_workflows/drug_consult_agent.yml) | F-006 AI 코파일럿 백엔드 |
| [_probe_fields.py](miso_workflows/_probe_fields.py), [_test_parse.py](miso_workflows/_test_parse.py), [_validate.py](miso_workflows/_validate.py) | 신규 API 필드 검증·정규화 회귀 테스트 |
| [templates/index.html](templates/index.html) | #E31E24 액센트 컬러·낱알식별 탭 디자인 자산 보존 → partial로 분해 |
| [static/images/](static/images/) | 의약품 이미지 자산 그대로 사용 |

### 14-2. 신규 디렉토리 구조
```
drug_integrated_search/
├── app.py                       # Blueprint 등록
├── config.py                    # ENV 기반 시크릿 + 30+ 엔드포인트
├── api_client/                  # API 호출 (3개 파일로 분할)
│   ├── __init__.py
│   ├── _base.py                 # 기존 _make_request 이전
│   ├── drug.py                  # 의약품 24종
│   ├── quasi.py                 # 의약외품 3종
│   ├── food.py                  # 식품 5종 + 건기식 1종
│   ├── narcotic.py              # 마약류 (Phase 2)
│   └── normalizer.py            # 응답 → 정규화 dict 변환
├── db/
│   ├── __init__.py              # SQLAlchemy
│   ├── models.py                # 3-layer 스키마 ORM
│   ├── migrations/              # Alembic
│   └── views.sql                # event_timeline 등 머티리얼라이즈드 뷰
├── services/
│   ├── product_matcher.py       # 6장 정규화 매칭
│   ├── company_matcher.py
│   ├── event_normalizer.py
│   ├── risk_scoring.py          # 6장 가중치 로직
│   ├── risk_weights.yml         # 운영자 편집 가능
│   ├── report_generator.py      # F-007
│   └── ai_summary.py            # MISO 에이전트 프록시
├── collectors/
│   ├── scheduler.py             # APScheduler 정의
│   ├── jobs.py                  # API별 야간 잡 (증분 파라미터)
│   └── diff.py                  # 변경분 감지 → 알림 큐 enqueue
├── blueprints/
│   ├── auth.py
│   ├── search.py                # /search + HTMX 부분 갱신
│   ├── product.py               # /product/{canonical_id} + /entity/{id}
│   ├── event.py                 # 이벤트 타임라인
│   ├── watchlist.py
│   ├── alerts.py
│   ├── reports.py               # 엑셀(openpyxl) / PDF(WeasyPrint)
│   ├── copilot.py               # MISO 에이전트 프록시
│   ├── admin.py
│   └── api.py                   # JSON API (외부 연동용)
├── templates/
│   ├── _layout.html             # 사이드바 + 상단 nav
│   ├── _components/             # 카드/배지/테이블 partial
│   ├── workspace/{ra,qa,scm,sales,rnd,food,exec}.html
│   ├── product/{drug,food}_360.html
│   └── event/timeline.html
├── static/
│   ├── tailwind.css             # CDN → 빌드 산출물
│   ├── app.js                   # Alpine.js + HTMX 진입점
│   └── images/                  # 기존 자산 유지
├── notifier/
│   ├── matcher.py               # 워치리스트 ↔ event_timeline 매칭
│   ├── email.py                 # SMTP
│   ├── slack.py                 # webhook
│   └── kakaowork.py
├── reports/
│   ├── templates/               # RA 월간/QA 주간/SCM 영향/영업 경쟁사 4종
│   └── builder.py
└── tests/
    ├── test_api_client.py
    ├── test_normalizer.py
    └── test_e2e.py              # Flask test client
```

---

## 15. 데이터 품질·신뢰성 장치

1. **증분 동기화**: 모든 API의 `CHNG_DT`/`updateDe`/`개정일자` 우선. 첫 적재만 풀 스캔. [_probe_fields.py](miso_workflows/_probe_fields.py) 패턴으로 신규 API 필드 사전 검증.
2. **변경 감지 + 감사 로그**: `event_timeline` 테이블 INSERT/UPDATE 트리거 → `alert_outbox` 자동 enqueue. 모든 변경은 `(record_hash, fetched_at, raw_json_url)` 함께 보관 → 출처 추적 가능.
3. **이중 폴백**: 허가정보 API 404 같은 장애 시 [excel_data_loader.py](excel_data_loader.py) 식 엑셀 정기 다운로드를 보조 경로로 유지.
4. **출처 명확성**: 모든 화면 카드에 "출처: ○○ API · 동기화 N분 전" 배지 + 식의약 데이터포털 안내(인허가 진행중·폐기·취하 데이터 누락 가능성) 푸터 노출.
5. **호출 한도 관리**: 각 API 10,000/일 가정 → 야간 배치 3,000회 + 사용자 실시간 4,000회 + 여유 3,000회. 캐시 미스 시 Redis 1h TTL.
6. **개인정보 보호**: 행정처분의 업체주소·대표자명·전화번호는 기본 마스킹, 권한 있는 사용자만 풀 노출. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 패턴 확장.
7. **시크릿 관리**: SERVICE_KEY/SECRET_KEY/SMTP 비번 ENV 강제. [config.py:14](config.py) 의 평문 fallback 제거 — 상용 출시 전 차단 항목.
8. **AI 안전장치**: 자연어 답변에 근거 카드 없으면 "확인 불가" 강제 응답 → hallucination 차단.

---

## 16. 구현 로드맵

### 16-1. 1단계 — 해커톤 MVP (4~6주)
- 12개 API 축 연동 (의약품 5 + 의약외품 3 + 식품 4)
- 통합 검색 + Product 360 + 이벤트 타임라인 + 리스크 점수
- 부서별 워크스페이스 6종 + 워치리스트 + 일일 리포트
- AI 자연어 검색 (MISO 에이전트)

### 16-2. 2단계 — 실무형 PoC
- 부서별 위젯 프리셋 편집기
- 엑셀/PDF 리포트 4종 템플릿 완성
- 마약류 통계 대시보드 (월별 제조·수입·수출·처방 시리즈)
- 임상·특허·생동성 확장
- HACCP·건기식 GMP 연동

### 16-3. 3단계 — 상용 SaaS
- 멀티테넌트 조직 관리
- 자사 품목 자동 등록 (사업자번호 기반)
- 일일 리스크 메일 자동 발송
- 업체·성분·원재료별 정교한 알림 룰
- API 장애 대응 캐시 강화
- 감사 추적 로그 + 사용자 행위 분석

### 16-4. 주차별 마일스톤 (1단계 가정, 1~2인 개발)
| 주차 | 산출물 |
|---|---|
| **W1** | DB 스키마 확정 + Alembic 마이그레이션 + Tailwind 디자인 토큰 + 레이아웃 partial. 의약품 5개 API 수집기 완성, DB 적재 동작. |
| **W2** | 나머지 의약품·의약외품 7개 API 수집기 완성. `event_timeline` 머티리얼라이즈드 뷰. 검색 API + Product 360 화면. |
| **W3** | 식품 4개 API 수집기. 식품 워크스페이스 + 통합 검색 도메인 필터. |
| **W4** | 부서별 워크스페이스 6종 + 워치리스트 + 알림 매처 + 이메일·슬랙 발송. MISO 워크플로우 4종 wiring. |
| **W5** | 엑셀/PDF 리포트 4종 템플릿 + `/copilot` (MISO drug_consult_agent 프록시). 관리자 화면. |
| **W6** | 통합 테스트 + 부하 테스트 + 보안 점검 + 데모 시나리오 검증. |

---

## 17. 검증 방법

1. **API 단위**: 30개 API 각각 [_test_parse.py](miso_workflows/_test_parse.py) 패턴으로 정규화 dict 필드 일치 검증.
2. **정합성**: 야간 배치 후 sync_log ALL=success + event_timeline 카운트가 source 합과 일치.
3. **업체 매칭**: "광동제약/광동제약(주)/주식회사 광동제약" 입력 시 동일 canonical_company_id 반환.
4. **이벤트 타임라인**: 자사 품목 등록 → 회수 발생 시뮬레이션 → 워치리스트 매칭 → alert_outbox enqueue → 메일 수신.
5. **리스크 점수**: 임의 업체 10개 점수 산정 → 가중치 yaml 수정 후 재산정 일관성 확인.
6. **부서 데모 6종**: 13장 시나리오대로 각 부서 화면 전환 시연.
7. **AI 코파일럿**: 4종 질문 예시(자사 회수, 성분 안전성, 원재료 회수, 경쟁사 처분) → 답변+근거 카드 검증.
8. **로컬 구동**: `python run.py` → `http://localhost:5005` 기존 포트 유지로 전체 시나리오 시연.

---

## 18. 발표용 메시지

> **RegHub 360은 식약처 공공 API를 단순히 나열하지 않고, 의약품·의약외품·식품 실무자가 실제로 묻는 질문 기준으로 허가·회수·행정처분·안전성·공급망·식품표시 정보를 통합해 주는 업무형 규제정보 플랫폼입니다.**

- **문제**: 제약·식품 실무자는 매일 여러 포털을 따로 조회
- **해결**: 제품명 하나로 허가·회수·행정처분·안전성·식품표시·공급망 통합
- **차별점**: API별 조회가 아니라 RA·QA·SCM·영업·R&D 업무별 조회
- **핵심 기능**: 통합 이벤트 타임라인 + 워치리스트 알림으로 놓치는 리스크 차단
- **확장성**: API 카탈로그 603건 중 MVP 12개 축 → 의약품·의약외품·식품·의료기기·바이오까지 확장

---

## 19. 미해결·후속 검증 필요 항목

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 의 의약품 허가정보 API 404 — 식약처 043-719-1626 문의 또는 엑셀 폴백 운영.
- 푸드QR API 정확한 엔드포인트·필드 — [_probe_fields.py](miso_workflows/_probe_fields.py) 1회 실행으로 사전 점검.
- 마약류 통계 시리즈 다수(처방·취급자·제조·수입·수출) — MVP에는 1개, 2단계에서 전체.
- 업체명 정규화의 동음이의 대응(예: "동아", "한미") — 사업자번호 보조 매칭 필수.
- 리스크 점수 가중치는 도메인 전문가 검토 후 1차 튜닝 필요.
- 상용 배포 시 시크릿 매니저(AWS Secrets Manager 또는 ansible-vault) 도입.

---

## 부록

### A. 관련 문서
- [README.md](README.md) — 프로젝트 개요
- [README_RUN.md](README_RUN.md) — 실행 방법
- [API_SPEC.md](API_SPEC.md) — 기존 API 명세
- [API_STATUS.md](API_STATUS.md) — API 작동 현황
- [API_APPLICATION_LIST.md](API_APPLICATION_LIST.md) — 신청 필요 API 목록 + 신청 URL
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — 문제 해결
- [deep-research-report (2).md](deep-research-report%20(2).md) — 초기 리서치 보고서
- [공공데이터 목록.xlsx](공공데이터%20목록.xlsx) — 전체 API 카탈로그 603건

### B. 기존 MISO 워크플로우
- [drug_integrated_search_workflow.yml](miso_workflows/drug_integrated_search_workflow.yml) — 통합 검색 워크플로우
- [drug_integrated_search_agent.yml](miso_workflows/drug_integrated_search_agent.yml) — 에이전트형 통합 검색
- [drug_daily_recall_report.yml](miso_workflows/drug_daily_recall_report.yml) — 일일 회수 리포트
- [drug_daily_disciplinary_report.yml](miso_workflows/drug_daily_disciplinary_report.yml) — 일일 행정처분 리포트
- [drug_consult_agent.yml](miso_workflows/drug_consult_agent.yml) — AI 컨설팅 에이전트

### C. 기술 스택 요약
| 영역 | 기술 |
|---|---|
| 백엔드 | Flask 2.3+ · Flask-Login · SQLAlchemy · Alembic · APScheduler |
| 프론트엔드 | Jinja2 · Tailwind CSS · Alpine.js · HTMX |
| DB | PostgreSQL 15+ · pg_trgm 한글 검색 |
| 캐시·큐 | Redis 7+ |
| 리포트 | openpyxl (엑셀) · WeasyPrint (PDF) |
| AI | MISO 에이전트 (기존 [drug_consult_agent.yml](miso_workflows/drug_consult_agent.yml)) |
| 알림 | SMTP · Slack Webhook · 카카오워크 Webhook |
| 배포 | (선택) Docker · Gunicorn · Nginx |

### D. 변경 이력
| 버전 | 일자 | 변경 내용 |
|---|---|---|
| v1.0 | 2026-05-26 | 초안 작성 — Role-based Workspace + 통합 이벤트 타임라인 + 리스크 점수 + MVP 12축 |
