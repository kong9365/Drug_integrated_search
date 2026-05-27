# 광동 KD-IRIS — Claude Code 핸드오프

> **이 문서는 디자인 산출물을 실제 동작하는 웹 애플리케이션으로 구현하기 위한 개발자 가이드입니다.**
> 디자인 파일은 `index.html` (마케팅 랜딩) + `app/*.html` (제품 UI 3종) 정적 HTML로 작성되어 있습니다.
> 모든 색상·간격·컴포넌트는 `styles/` 내 CSS 토큰을 기준으로 합니다.

---

## 0. TL;DR — 만들어야 할 것

1. **마케팅 랜딩 페이지** (`/`) — Hero · Features · Live Demo · Use Cases · CTA
2. **제품 SPA** (`/app/*`) — 통합 검색, Product 360, 부서별 워크스페이스
3. 라이트/다크 테마 지원, 풀 반응형 (모바일 320px ~ 데스크탑 1920px)
4. 식약처 공공 API 12개 축 연동 (Phase 1 MVP)
5. AI 코파일럿 (자연어 검색 + 근거 카드)

**기술 스택 권장:**
- 프론트엔드: Next.js 14 (App Router) + TypeScript + Tailwind CSS 또는 CSS Modules
- 백엔드: 별도 — IMPLEMENTATION_PLAN.md 참조 (Flask · PostgreSQL · Redis)
- 폰트: Pretendard Variable + JetBrains Mono
- 아이콘: Lucide React (디자인의 인라인 SVG와 동일 스타일)

---

## 1. 디자인 파일 구조

```
/
├── index.html                  ★ 마케팅 랜딩 페이지
├── app/
│   ├── search.html             ★ 통합 검색 홈 (제품 메인)
│   ├── product.html            ★ Product 360 — 베니톨정 상세
│   └── workspace.html          ★ QA/QC 워크스페이스 대시보드
├── styles/
│   ├── tokens.css              디자인 토큰 (라이트/다크 두 테마 모두 정의)
│   ├── components.css          공용 컴포넌트 (버튼·뱃지·카드·nav·logo)
│   ├── landing.css             랜딩 페이지 전용
│   └── app.css                 제품 UI 전용 (sidebar shell · KPI · alert row …)
├── scripts/
│   ├── theme.js                테마 토글, 모바일 nav, reveal, 탭, 라이브 데모
│   └── app.js                  앱 사이드바, Product 360 탭
└── handoff.md                  이 문서
```

각 HTML 파일을 직접 브라우저에서 열면 동작합니다 (CDN 외부 의존성: Pretendard, JetBrains Mono).

---

## 2. 디자인 시스템

### 2.1 디자인 토큰 (`styles/tokens.css`)

CSS Custom Properties로 정의. `:root` (light) ↔ `[data-theme="dark"]` 두 셋트.

#### 컬러
| 토큰 | 라이트 | 다크 | 용도 |
|---|---|---|---|
| `--brand` | `#4F46E5` | `#818CF8` | 1차 강조 (버튼, 링크, focus) |
| `--brand-hover` | `#4338CA` | `#A5B4FC` | hover 상태 |
| `--brand-pressed` | `#3730A3` | `#C7D2FE` | active 상태 |
| `--brand-soft` | `#EEF0FF` | `rgba(129,140,248,0.14)` | 배경, badge |
| `--bg` | `#FFFFFF` | `#07070B` | 페이지 배경 |
| `--bg-elevated` | `#FFFFFF` | `#0E0E16` | 카드, 다이얼로그 |
| `--bg-subtle` | `#F8F9FB` | `#0B0B12` | section, app content |
| `--bg-muted` | `#F1F3F7` | `#16171F` | hover, input bg |
| `--ink-1` | `#0B0B14` | `#F4F4F6` | primary text |
| `--ink-2` | `#2A2D35` | `#D5D7DC` | secondary text |
| `--ink-3` | `#5B5F6B` | `#9498A1` | muted text |
| `--ink-4` | `#9498A1` | `#6E727B` | hint text |
| `--ink-5` | `#C7CAD1` | `#4A4D55` | placeholders |
| `--line-1` | `#E7E9EE` | `#1F2029` | borders |
| `--line-2` | `#EFF1F4` | `#15161E` | subtle dividers |
| `--line-strong` | `#D3D6DC` | `#2D2F39` | input borders, btn--secondary |

#### 시맨틱 컬러
| 토큰 | 용도 | 라이트 |
|---|---|---|
| `--ok` / `--ok-soft` | 정상, 완료, 안전 | `#0F9D58` / `#E5F4EB` |
| `--warn` / `--warn-soft` | 주의, MED severity | `#C2700A` / `#FCEFD5` |
| `--danger` / `--danger-soft` | 위험, HIGH severity | `#C92A2A` / `#FBE5E5` |
| `--crit` / `--crit-soft` | 치명, CRITICAL severity | `#7F1D1D` / `#F1D7D7` |
| `--info` / `--info-soft` | 정보, LOW severity | `#1E40AF` / `#EAF1FE` |

#### 도메인 강조
| 토큰 | 도메인 | 라이트 |
|---|---|---|
| `--domain-drug` / `--domain-drug-soft` | 의약품 | `#1E40AF` / `#EAF1FE` |
| `--domain-quasi` / `--domain-quasi-soft` | 의약외품 | `#5B21B6` / `#F3EAFE` |
| `--domain-food` / `--domain-food-soft` | 식품 | `#9A3412` / `#FDEFE5` |

#### 그림자
| 토큰 | 용도 |
|---|---|
| `--shadow-xs` | 미세 (input 등) |
| `--shadow-sm` | 1단 카드 |
| `--shadow-md` | 떠 있는 카드 |
| `--shadow-lg` | 모달, 데모 셸 |
| `--shadow-brand` | 강조 CTA |

### 2.2 타이포그래피

- **본문/UI**: `'Pretendard Variable', Pretendard, system-ui, sans-serif`
- **숫자/코드**: `'JetBrains Mono', ui-monospace, monospace`
- **숫자는 `font-variant-numeric: tabular-nums` 필수** — 정렬된 KPI/통계용
- `letter-spacing: -0.011em` 기본, 헤드라인은 `-0.02 ~ -0.04em`
- `font-feature-settings: "ss01", "tnum", "kern"`

#### 스케일 (`.t-*` 유틸리티)
| 클래스 | 크기 (clamp) | weight | 용도 |
|---|---|---|---|
| `.t-display` | 48-96px | 700 | 히어로 타이틀 |
| `.t-h1` | 36-64px | 700 | 섹션 타이틀 |
| `.t-h2` | 28-44px | 700 | 서브 섹션 |
| `.t-h3` | 22-28px | 600 | 카드 타이틀 |
| `.t-lead` | 17-21px | 400 | lead paragraph |
| `.t-body` | 16px | 400 | 본문 |
| `.t-small` | 14px | 400 | 메타 |
| `.t-caption` | 12px | 600 uppercase | 라벨 |
| `.t-eyebrow` | 13px | 600 uppercase letter-spacing 0.14em | 섹션 뱃지 |

### 2.3 간격·반경

- **베이스 단위**: 4px
- **컨테이너 패딩**: 32px desktop / 20px mobile
- **카드 패딩**: 20-28px
- **반경**: 8 (작은 컨트롤) / 10 (input·alert-row) / 12-14 (input · 카드) / 16 (큰 카드) / 20 (섹션 셸)
- 세부 값은 `tokens.css` 참조

### 2.4 반응형 브레이크포인트

| 너비 | 동작 |
|---|---|
| `≥1200` | full layout |
| `≤900` | 사이드바 collapse, 2열 grid, mobile nav |
| `≤768` | hero 패딩 축소, 카드 1열, 푸터 2열 |
| `≤540` | 모든 grid 1열, footer 1열 |

---

## 3. 페이지별 라우트 & 동작

### 3.1 마케팅 랜딩 (`/` → `index.html`)

| 섹션 | data-screen-label | 핵심 동작 |
|---|---|---|
| Topbar | `Landing · Topbar` | sticky · backdrop-blur · 테마 토글 · 햄버거 |
| Hero | `Landing · Hero` | 그리드 + 라디얼 글로우 · scroll reveal · 제품 mock preview |
| Trust band | `Landing · Trust band` | 정적 |
| Stats | `Landing · Stats` | 4-cell, mobile 1열 |
| Features | `Landing · Features` | 4개 row alternating, mock visual |
| Live demo | `Landing · Live demo` | ★ **인터랙티브**: 입력 → 가짜 데이터 매칭 → 6개 stat 즉시 업데이트 |
| Use cases | `Landing · Use cases` | ★ **탭 6개**: QA · RA · SCM · 영업 · R&D · 식품 |
| CTA | `Landing · CTA` | 그라디언트 카드, 2개 버튼 |
| Footer | `Landing · Footer` | 4열 grid → 2열 → 1열 |

**라이브 데모 데이터** — `scripts/theme.js` 내 `DATA` 객체 참조. 실제 구현 시 backend API 호출로 대체:
```ts
GET /api/search?q=광동제약
→ { kind: '업체', drug: 312, recall: 4, sanction: 2, safety: 1, supply: 0, food: 87 }
```

### 3.2 통합 검색 (`/app/search` → `app/search.html`)

라우트: `/app/search`, `/app/search?q={query}`

- 검색 입력 + 6가지 chip 필터 (도메인 3 + 검색기준 6)
- 검색어가 업체로 식별되면: KPI 4종 + 대표 품목 리스트
- 검색어가 제품이면: 즉시 Product 360으로 redirect
- 사이드바: workspace 7개 + menu 5개

### 3.3 Product 360 (`/app/product/[id]` → `app/product.html`)

라우트: `/app/product/[productCode]` (예: `/app/product/200305423`)

- 8개 탭 (기본정보 · 허가이력 · 안전성 · 품질·규제 · 공급망 · 개발·BD · 마약류 · 낱알식별)
- Hero: 낱알식별 이미지, 분류 뱃지, 코드 메타, Risk Score
- 각 카드에 "출처 API · 동기화 N분 전" 배지 의무
- 식품/의약외품은 동일 컴포넌트 · 다른 탭 구성

### 3.4 QA 워크스페이스 (`/app/workspace/qa` → `app/workspace.html`)

라우트: `/app/workspace/[department]` (qa, ra, scm, sales, rnd, food, exec)

- 부서별 위젯 프리셋 (KPI 4 + 위젯 N개)
- 위젯 드래그 편집 (Phase 2)
- 일일 리포트 다운로드

---

## 4. 공용 컴포넌트 명세

### 4.1 Button — `.btn`
```html
<button class="btn btn--primary btn--lg">텍스트</button>
```
modifiers: `--primary` / `--secondary` / `--ghost` / `--lg` / `--sm` / `--icon`
- height: 44px (default), 56px (lg), 36px (sm)
- transitions: 180ms ease

### 4.2 Badge — `.badge`
```html
<span class="badge badge--brand badge--dot">v1.0 · MVP</span>
```
variants: `--brand` / `--ok` / `--warn` / `--danger` / `--crit` / `--info` / `--lg` / `--dot` (앞에 6px 컬러 dot)

### 4.3 Card — `.card`, `.app-card`, `.kpi-card`
- 모두 `--bg-elevated` + `--line-1` border
- `.card--interactive` hover: shadow + translateY(-2px)
- `.kpi-card__pulse` = 우상단 펄스 dot (CRITICAL alert)

### 4.4 Alert row — `.alert-row`
타임라인 / 알림 리스트의 핵심 단위. severity bar 4px 너비.
```html
<div class="alert-row">
  <div class="alert-row__bar" style="background: var(--danger)"></div>
  <span class="alert-row__time">14:32</span>
  <div class="flex-1">
    <div class="alert-row__title">제목</div>
    <div class="alert-row__meta">메타</div>
  </div>
  <span class="badge badge--danger">HIGH</span>
</div>
```

### 4.5 Logo
- 28px 박스 + 안쪽 회전된 사각형 = 브랜드 마크
- `.logo--sm` 22px (사이드바, 푸터)

---

## 5. 인터랙티브 동작

### 5.1 테마 토글 (라이트/다크)

- `<html data-theme="light|dark">` 속성으로 제어
- `localStorage.getItem('reghub.theme')`로 영속화
- 첫 페인트 전 인라인 스크립트로 적용 (FOUC 방지) — 모든 페이지 `<head>` 최상단에 있음
- prefers-color-scheme 존중

```ts
// 시스템 테마 우선, localStorage 덮어쓰기
function getInitialTheme(): 'light' | 'dark' {
  const stored = localStorage.getItem('reghub.theme')
  if (stored === 'light' || stored === 'dark') return stored
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}
```

### 5.2 모바일 사이드바

`[data-app-sidebar]`에 `is-open` 클래스 토글.
backdrop click → close. nav item click → close.

### 5.3 Product 360 탭

`[data-p360-tab="info"]` 클릭 → 같은 값 가진 `[data-p360-panel="info"]`에 `.is-active`.

### 5.4 Use case 탭 (랜딩)

`[data-tabs]` 컨테이너 안 `[data-tab]` ↔ `[data-panel]`.

### 5.5 Live demo 검색

input 이벤트마다 prefix-match → DATA에서 lookup → DOM `[data-result-*]` 갱신. 실제 구현 시 debounced API 호출로 대체.

### 5.6 Scroll reveal

`[data-reveal]` 요소가 viewport 진입 시 `.is-visible` 추가.
`prefers-reduced-motion`이면 즉시 visible.

---

## 6. API 통합 (Phase 1 — 12개 축)

`uploads/IMPLEMENTATION_PLAN.md` 참조. 디자인이 가정하는 API 매핑:

| 화면 영역 | API 번호 | 설명 |
|---|---|---|
| 의약품 허가 | 140 | 의약품 제품 허가정보 |
| 회수·판매중지 | 539 | 의약품 회수/판매중지 정보 |
| 행정처분 (의약품) | 4 | 의약품 행정처분 |
| 안전성서한 | 547 | 안전성서한 정보 |
| DUR (병용·연령·임부금기) | 531, 533 | 의약품안전사용 |
| 공급중단 | 534, 537 | 공급중단·공급부족 |
| 의약외품 허가 | 518 | 의약외품 허가정보 |
| 마스크 회수/처분 | 539, 4 | 의약외품 회수·행정처분 |
| 식품 회수 | 339 | 식품 회수정보 |
| 식품 행정처분 | 6 | 식품 행정처분 |
| 품목제조보고 | 5 | 식품등의 품목제조보고 |
| 푸드QR·영양성분 | 1, 444, 470, 555 | 식품영양·표시기준 |

각 카드의 "출처 API · 동기화 N분 전" 배지는 `lastSyncedAt`을 백엔드에서 받아 표시.

---

## 7. AI 코파일럿 (F-006)

- **자연어 입력 → 백엔드 LLM 호출 → 근거 카드와 함께 응답**
- 환각 차단: 근거 카드(공식 API 결과) 0건 → "확인 가능한 공식 데이터가 없습니다"로 강제
- 응답 메시지에 `[1][2]` 인용 마커 → 하단 근거 카드와 연결
- 기존 `drug_consult_agent.yml` 자산 재활용 (IMPLEMENTATION_PLAN.md 참조)

API:
```ts
POST /api/copilot/message
Body: { threadId, message, context: { productCode?, companyId? } }
Response: {
  text: string,             // [1][2] 마커 포함
  citations: Citation[],    // 각 [N]에 해당
  suggestions: string[]     // follow-up 추천 질문
}

interface Citation {
  marker: number            // [1], [2] …
  apiNumber: string         // "API 539"
  title: string             // "○○정 함량 부적합"
  url: string               // 식약처 공식 URL
  syncedAt: string          // ISO 8601
}
```

---

## 8. 데이터 모델 핵심

```ts
interface Product {
  productCode: string         // 식약처 품목기준코드
  name: string
  manufacturer: Company
  domain: 'drug' | 'quasi-drug' | 'food'
  classification: string      // 일반의약품 · 혼합음료 …
  ingredients: Ingredient[]
  riskScore: number           // 0-100
  riskLevel: 'normal' | 'low' | 'medium' | 'high' | 'critical'
  lastSyncedAt: string
  // domain-specific 필드는 분리된 인터페이스 (Drug, Food, …)
}

interface Event {
  id: string
  type: 'recall' | 'sanction' | 'safety-letter' | 'dur' | 'inspection-fail' | 'supply-stop' | 'license-change'
  severity: 'critical' | 'high' | 'medium' | 'low'
  occurredAt: string
  productCodes: string[]      // 영향 받는 자사 제품
  affectedDepartments: ('ra'|'qa'|'scm'|'sales'|'rnd'|'food-qa'|'exec')[]
  apiSource: string           // "API 539"
  title: string
  detail: string
}

interface RiskScore {
  productCode: string
  total: number               // 0-100
  breakdown: { factor: string, weight: number }[]
  // Σ(이벤트 가중치) × 최근성 보정 × 반복발생 보정
}
```

상세는 IMPLEMENTATION_PLAN.md 4장 (데이터 스키마) 참조.

---

## 9. 접근성 (a11y) 체크리스트

- [x] 모든 인터랙티브 요소 키보드 포커스 가능
- [x] 색상 대비 WCAG AA (라이트·다크 모두)
- [x] `aria-label` 아이콘 버튼 (theme-toggle, hamburger, app-topbar__icon-btn)
- [x] `prefers-reduced-motion` 존중 (reveal 즉시 보이게)
- [ ] 스크린 리더용 alert 영역 (CRITICAL 이벤트 발생 시 `aria-live="assertive"`)
- [ ] focus-visible 스타일 추가 (현재 디자인은 의도적으로 minimum, 구현 시 link/button에 outline 명시 권장)
- [ ] 데이터 테이블 caption + scope 속성

---

## 10. 성능 가이드

- 폰트: Pretendard CDN dynamic subset (한글 자동 서브셋) — variable font로 weight 단일 파일
- 이미지: 낱알식별 이미지는 placeholder. 실제는 식약처 이미지 URL + lazy loading
- 코드 splitting: Product 360 탭 패널은 각각 lazy import 추천
- API: Redis 캐시 5분 TTL (IMPLEMENTATION_PLAN.md 참조)
- 클라이언트 검색: 자동완성용 prefix tree 또는 Algolia/Meilisearch

---

## 11. 빌드/구현 시 주의사항

1. **인라인 스타일이 많은 이유** — 디자인 단계에서 빠른 iteration용. 구현 시 `Tailwind @apply` 또는 CSS Modules로 정리. **토큰 이름(`var(--brand)` 등)은 그대로 유지** — 디자이너와의 공통 어휘.
2. **숫자는 항상 `tabular-nums`** — KPI, alert time, 표 등 정렬되어 보여야 함.
3. **severity 색상은 의미가 고정** — 임의로 매핑 변경 금지. CRITICAL=crit(어두운 빨강), HIGH=danger, MED=warn, LOW=info.
4. **도메인 색상은 부드러운 톤** — 의약품=파랑, 의약외품=보라, 식품=주황. badge 배경/텍스트 페어 사용.
5. **출처 API 배지는 의무** — 모든 데이터 카드에 "API XXX · 동기화 N분 전" 노출. 신뢰성 핵심.
6. **다크 모드는 반드시** — 야간 근무·심야 회수 모니터링 시나리오. 색상은 라이트 토큰의 의미를 유지하되 채도 낮춤.
7. **AI 응답은 근거 카드 없이 절대 표시 금지** — `citations.length === 0` 이면 안내 메시지로 대체.

---

## 12. Phase 1 → Phase 2 → Phase 3

자세한 일정은 IMPLEMENTATION_PLAN.md 5장 참조.

| Phase | 기간 | 포함 |
|---|---|---|
| **MVP** | 4-6주 | 12개 API · Product 360 · 타임라인 · 워크스페이스 6 · 코파일럿 |
| **PoC** | +2-3개월 | 위젯 편집기 · 리포트 4종 · 마약류 · 임상 · HACCP |
| **상용** | +6개월 | 멀티테넌트 · 사업자번호 자동등록 · 일일 메일 · 감사 로그 |

---

## 13. 디자인 변경 요청 시

이 디자인을 직접 수정하지 마시고, 변경 사항을 정리해 디자이너(=원본 HTML 생성자)에게 전달해주세요. 토큰 변경 사항이라면 `styles/tokens.css` 단일 파일만 수정해도 전체에 반영됩니다.

피드백 채널: `reghub@kwangdong.io`

---

**문서 버전**: v1.0 · 2026.05.26
**작성**: 광동제약 KD-IRIS 디자인 팀
