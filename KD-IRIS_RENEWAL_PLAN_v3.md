# KD-IRIS — 통합 리뉴얼 전체 명세서 v3.0

> **시스템명**: KD-IRIS (KwangDong Integrated Regulatory Intelligence System)  
> **구 명칭**: RegHub 360 → 전면 리브랜딩  
> **기준 레포**: `https://github.com/kong9365/Drug_integrated_search`  
> **작성 기준일**: 2026-05-27  
> **작성**: 품질관리2팀 AI TF (MISO-52g TF)  
> **API 검증**: 44개 오퍼레이션 전수 검증 완료 (완전 32 + 부분 12 + 실패 0)  
> **v3 변경**: Phase 5 v2 Claude Code 실행 명세 통합, 이미 완료 항목 반영, 작업 단위 세분화

---

## 목차

1. [리뉴얼 목적 및 핵심 원칙](#1-리뉴얼-목적-및-핵심-원칙)
2. [KD-IRIS 리브랜딩 범위](#2-kd-iris-리브랜딩-범위)
3. [전체 공통 변경사항](#3-전체-공통-변경사항)
4. [네비게이션 구조 재편 (7개 메뉴)](#4-네비게이션-구조-재편)
5. [API 검증 결과 및 구현 지침](#5-api-검증-결과-및-구현-지침)
6. [페이지별 상세 명세](#6-페이지별-상세-명세)
7. [신규 API 22개 연동 계획](#7-신규-api-22개-연동-계획)
8. [현재 완료 상태 (Phase 1~4)](#8-현재-완료-상태-phase-1-4)
9. [구현 Phase 로드맵 — Claude Code 실행 기준](#9-구현-phase-로드맵--claude-code-실행-기준)
10. [검증 체크리스트](#10-검증-체크리스트)
11. [비-목표](#11-비-목표)
12. [부록 A — 전체 API 목록 (45개)](#부록-a--전체-api-목록)
13. [부록 B — 작업 순서 권장](#부록-b--작업-순서-권장)

---

## 1. 리뉴얼 목적 및 핵심 원칙

### 1.1 핵심 문제 정의

현재 시스템은 **데이터 나열형** 구조다. API 결과를 그대로 렌더링하여 실무자가 여러 탭을 탐색해야 판단할 수 있다. 개발자용 코드(`API 539`, `NO 547`, `SPCLTY_PBLC` 등)가 화면에 노출되고, 긴급·정보성 이벤트가 동등 나열되어 우선순위 인식이 불가능하다.

### 1.2 전환 방향

| 기존 | 목표 |
|------|------|
| 데이터 나열형 | 의사결정 지원형 |
| API 탭별 분리 조회 | 제품 중심 통합 뷰 |
| 단순 카운트 KPI | 맥락 있는 액션 KPI |
| 개발자 코드 노출 | 실무 언어로 정리 |
| 동등 나열 | 심각도 기반 우선순위 |
| RegHub 360 | KD-IRIS (리브랜딩) |

### 1.3 사용자 페르소나

| 순위 | 팀 | 핵심 질문 |
|------|-----|-----------|
| 1 | **QA/QC** | "지금 당장 대응해야 할 이슈가 있나?" |
| 2 | **RA** | "언제까지 뭘 제출해야 하나?" |
| 3 | **SCM** | "어떤 품목이 공급 위험 상태인가?" |
| 4 | **R&D** | "경쟁사 파이프라인이 어디까지 왔나?" |
| 5 | **식품QA** | "이 원재료, 쓸 수 있는 건가?" |

### 1.4 설계 원칙

- **원칙 1 — 맥락 우선**: 이벤트·결과에 항상 "그래서 뭘 해야 하나"가 보여야 한다.
- **원칙 2 — 심각도 계층**: 🔴 긴급 → 🟡 주의 → 🟢 정보 3단계 일관 적용.
- **원칙 3 — 개발 코드 전면 제거**: `API XXX`, `NO XXX`, `domain_kr`, 필드명 코드 화면 노출 금지.
- **원칙 4 — 제품 중심 통합**: 모든 이벤트는 특정 제품·업체로 드릴다운 가능.
- **원칙 5 — 즉시 행동 가능**: 이벤트 카드에 반드시 "다음 액션 링크"가 있어야 한다.

---

## 2. KD-IRIS 리브랜딩 범위

### 2.1 변경 대상 파일

| 파일 | 변경 내용 |
|------|-----------|
| `templates/_layout.html` | `<title>` + `.logo` 텍스트 "RegHub 360" → "KD-IRIS" |
| `templates/app/*.html` (전체) | `{% block title %}` "광동 RegHub 360" → "광동 KD-IRIS" |
| `app.py` | `print()` 메시지 + healthz 응답 `"service": "KD-IRIS"` |
| `run.py` | print 메시지 교체 |
| `README.md` / `README_RUN.md` / `docs/HANDOFF.md` | 헤더·본문 명칭 교체 |

### 2.2 브랜드 표기 규칙

```
공식 전체명: KD-IRIS
풀네임:      KwangDong Integrated Regulatory Intelligence System
화면 표시:   KD-IRIS
부제 (선택): KwangDong Integrated Regulatory Intelligence System (로고 하단 작은 글씨)
```

### 2.3 완료 검증

```bash
grep -r "RegHub 360" templates/ app.py run.py README.md   # 0건이어야 함
```

---

## 3. 전체 공통 변경사항

### 3.1 즉시 제거할 요소 (전체 템플릿)

```
삭제 대상 패턴:
- {{ ev.api }}          → "API 539", "NO 547" 등 번호 노출
- {{ ev.domain_kr }}    → "의약품" 중복 태그
- event_kinds|join(' · ') → raw key 노출
- 필드명 직접 노출 (SPCLTY_PBLC, ITEM_SEQ 등)
- placeholder "—"       → {% if value and value != "—" %} 조건부 또는 섹션 숨김
- 빈 날짜 렌더링        → "날짜 미확인" 표시
```

검증:
```bash
grep -r "API [0-9]" templates/    # 0건
grep -r "domain_kr" templates/    # 0건
grep -r '"—"' templates/          # 0건
```

### 3.2 공통 심각도(Severity) 체계 — blueprints/severity.py [신규]

```python
# blueprints/severity.py

SEVERITY_MAP = {
    # 🔴 CRITICAL — 즉각 대응 필요
    "recall":          {"level": "CRITICAL", "label": "회수명령",   "color": "danger"},
    "supply_stop":     {"level": "CRITICAL", "label": "판매중지",   "color": "danger"},
    # 🟡 HIGH — 모니터링 필요
    "disciplinary":    {"level": "HIGH",     "label": "행정처분",   "color": "warn"},
    "supply_lack":     {"level": "HIGH",     "label": "공급부족",   "color": "warn"},
    "safety_letter":   {"level": "HIGH",     "label": "안전성서한", "color": "warn"},
    "inspection_fail": {"level": "HIGH",     "label": "검사부적합", "color": "warn"},
    # 🟢 LOW — 인지 및 기회 탐색
    "permit_new":      {"level": "LOW",      "label": "신규허가",   "color": "success"},
    "clinical_new":    {"level": "LOW",      "label": "임상신규",   "color": "info"},
    "patent_new":      {"level": "LOW",      "label": "특허등재",   "color": "info"},
    "review_due":      {"level": "LOW",      "label": "재심사예정", "color": "info"},
    "reeval_done":     {"level": "LOW",      "label": "재평가완료", "color": "info"},
}

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "LOW": 2, "NONE": 3}

def get_severity(event_type: str) -> dict:
    return SEVERITY_MAP.get(event_type, {
        "level": "NONE", "label": event_type, "color": "muted"
    })
```

### 3.3 _normalize_event() 공통 출력 스키마

`blueprints/app_views.py` 및 `blueprints/watchlist_match.py` 양쪽 normalize 함수를 아래 스키마로 통일:

```python
# 모든 _normalize_event() 반환값 — 통일 스키마
{
    "type":           str,   # 내부 키 (recall, disciplinary 등)
    "type_label":     str,   # 화면 한글 (SEVERITY_MAP label)
    "severity_level": str,   # CRITICAL / HIGH / LOW / NONE
    "severity_color": str,   # danger / warn / success / info / muted
    "title":          str,   # 품목명 중심 (60자 truncate)
    "entity":         str,   # 업체명
    "summary":        str,   # 사유/내용 (100자 truncate)
    "date":           str,   # "YYYY-MM-DD" 또는 "" (빈값 → 템플릿에서 "날짜 미확인")
    "is_new":         bool,  # 오늘 날짜 여부
    "product_code":   str,   # ITEM_SEQ (있으면 Product 360 링크)
    "in_watchlist":   bool,  # 워치리스트 매칭 여부
    # 제거: "api", "url", "domain", "domain_kr"
}
```

### 3.4 공통 이벤트 카드 매크로 — templates/_macros.html [신규]

```jinja2
{# templates/_macros.html #}
{% macro event_card(event, show_product_link=True) %}
<div class="event-card event-card--{{ event.severity_color }}"
     data-severity="{{ event.severity_level }}">

  <div class="event-card__header">
    <span class="severity-badge severity-badge--{{ event.severity_color }}">
      {{ event.type_label }}
    </span>
    {% if event.is_new %}<span class="badge badge--new">NEW</span>{% endif %}
    {% if event.in_watchlist %}<span class="badge badge--watch">📌 워치리스트</span>{% endif %}
    <time class="event-card__date">
      {{ event.date if event.date else "날짜 미확인" }}
    </time>
  </div>

  <p class="event-card__title">{{ event.title }}</p>
  <p class="event-card__entity">{{ event.entity }}</p>

  {% if event.summary %}
  <p class="event-card__summary">{{ event.summary }}</p>
  {% endif %}

  <div class="event-card__actions">
    {% if show_product_link and event.product_code %}
    <a href="/app/product/{{ event.product_code }}" class="btn btn--ghost btn--sm">
      제품 상세 →
    </a>
    {% endif %}
  </div>
</div>
{% endmacro %}
```

### 3.5 위험도 신호등 헬퍼 — blueprints/risk.py [신규]

```python
# blueprints/risk.py

def calc_risk_signal(approval_data, disciplinary_items, recall_items,
                     review_due_days=None):
    """
    반환: {level, color, label, reasons[]}
    level: "CRITICAL" | "HIGH" | "LOW" | "NONE"
    """
    reasons = []
    level = "NONE"

    if recall_items:
        level = "CRITICAL"
        reasons.append(f"회수이력 {len(recall_items)}건")

    if disciplinary_items:
        if level != "CRITICAL":
            level = "HIGH"
        reasons.append(f"행정처분 {len(disciplinary_items)}건")

    if review_due_days is not None and review_due_days <= 30:
        if level == "NONE":
            level = "HIGH"
        reasons.append(f"재심사 D-{review_due_days}일")

    if not reasons:
        level = "LOW"
        reasons = ["이상 없음"]

    color_map = {"CRITICAL": "danger", "HIGH": "warn", "LOW": "success", "NONE": "muted"}
    label_map = {"CRITICAL": "위험",   "HIGH": "주의", "LOW": "정상",   "NONE": "정보없음"}

    return {"level": level, "color": color_map[level],
            "label": label_map[level], "reasons": reasons}
```

---

## 4. 네비게이션 구조 재편

### 4.1 현재 vs 리뉴얼 메뉴

```
현재 (5개):                    리뉴얼 (7개 + reports disabled):
────────────────────           ───────────────────────────────
🔍 통합 검색         →        🏠 오늘의 브리핑     [신규 /app/home]
📅 이벤트 타임라인   →        🔍 제품·업체 조회    [명칭 변경 /]
👁 워치리스트        →        🚨 이벤트 모니터     [확장 /app/monitor]
📊 리포트            →        👁 내 워치리스트     [기능 강화]
🤖 AI 코파일럿       →        🏢 워크스페이스      [/app/workspace, 하위 5개]
                               🔬 검사부적합        [/app/inspections]
                               🤖 AI 코파일럿       [/app/copilot]
                               📊 리포트·내보내기   [disabled, Phase R-4]
```

### 4.2 nav_config.py 전체 교체 코드

```python
# blueprints/nav_config.py

NAV_ITEMS = [
    {
        "key": "home", "label": "오늘의 브리핑", "href": "/app/home",
        "icon_svg": '<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>',
        "badge": None, "disabled": False,
    },
    {
        "key": "search", "label": "제품·업체 조회", "href": "/",
        "icon_svg": '<path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>',
        "badge": None, "disabled": False,
    },
    {
        "key": "monitor", "label": "이벤트 모니터", "href": "/app/monitor",
        "icon_svg": '<path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>',
        "badge": None,  # inject_nav()에서 today_critical_count 동적 주입
        "disabled": False,
    },
    {
        "key": "watchlist", "label": "내 워치리스트", "href": "/app/watchlist",
        "icon_svg": '<path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>',
        "badge": None,  # inject_nav()에서 동적 주입
        "disabled": False,
    },
    {
        "key": "workspace", "label": "워크스페이스", "href": "/app/workspace",
        "icon_svg": '<path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>',
        "badge": None, "disabled": False,
        "children": [
            {"key": "ws_ra",      "label": "RA (허가·인허가)", "href": "/app/workspace/ra"},
            {"key": "ws_scm",     "label": "SCM (공급망)",     "href": "/app/workspace/scm"},
            {"key": "ws_rnd",     "label": "R&D",              "href": "/app/workspace/rnd"},
            {"key": "ws_food_qa", "label": "식품QA",           "href": "/app/workspace/food_qa"},
            {"key": "ws_sales",   "label": "영업",             "href": "/app/workspace/sales"},
        ],
    },
    {
        "key": "inspections", "label": "검사부적합", "href": "/app/inspections",
        "icon_svg": '<path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>',
        "badge": None, "disabled": False,
    },
    {
        "key": "copilot", "label": "AI 코파일럿", "href": "/app/copilot",
        "icon_svg": '<path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>',
        "badge": {"kind": "brand", "text": "NEW"}, "disabled": False,
    },
    {
        "key": "reports", "label": "리포트·내보내기", "href": "/app/reports",
        "icon_svg": '<path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>',
        "badge": {"kind": "muted", "text": "Phase 2"}, "disabled": True,
    },
]

USER_INFO = {"initials": "KQ", "name": "김QA", "team": "광동제약 · QA/QC팀"}
```

### 4.3 app.py inject_nav() 확장

```python
@app.context_processor
def inject_nav():
    wl_critical = 0
    wl_total = 0
    monitor_critical = 0

    try:
        wl_total = watchlist_store.count()
        if wl_total > 0:
            entries = watchlist_store.list_entries()
            match_map = watchlist_match.match_for_entries(entries)
            wl_critical = watchlist_match.critical_alert_count(match_map)
    except Exception as e:
        logger.warning(f"inject_nav watchlist 오류: {e}")

    try:
        monitor_critical = watchlist_match.today_critical_count()
    except Exception as e:
        logger.warning(f"inject_nav monitor 오류: {e}")

    items = []
    for it in NAV_ITEMS:
        it = dict(it)
        if it["key"] == "watchlist":
            if wl_critical > 0:
                it["badge"] = {"kind": "danger", "text": str(wl_critical)}
            elif wl_total > 0:
                it["badge"] = {"kind": "brand", "text": str(wl_total)}
        elif it["key"] == "monitor":
            if monitor_critical > 0:
                it["badge"] = {"kind": "danger", "text": str(monitor_critical)}
        items.append(it)

    return {"nav_items": items, "workspaces": WORKSPACES, "user_info": USER_INFO}
```

---

## 5. API 검증 결과 및 구현 지침

> **검증 결과**: 44개 오퍼레이션 — 완전 작동 32 / 부분(필드 수정 필요) 12 / 실패 0

### 5.1 파라미터 케이스 규칙 — API별 혼재 (반드시 준수)

```
snake_case (소문자):    item_name, entp_name, bizrno, edi_code
  → NO 140(허가), 563(낱알), 564(처분), 145(의약외품), 153(수입식품회수)

camelCase:              itemName, entpName, itemSeq
  → NO 248(e약은요), 531(DUR 품목), 269(묶음의약품)

UPPER_CASE:             TITLE, BSSH_NM, FOOD_NM_KR, PRCSCITYPOINT_BSSHNM
  → NO 547(안전성서한), 132(GMP), 1(식품영양DB), 3·5·6(식품행정처분)

⚠️ 특수 케이스:
  NO 140: item_seq 파라미터 무시됨 → edi_code로 검색 필요 (핵심 발견)
  NO 132: BSSH_NM="광동제약" → 1건 정확 조회 확인
```

### 5.2 서버사이드 검색 불가 API 12개 — _filter_items() 메모리 필터 필수

| NO | 서비스 | 전체 건수 | 주의 |
|----|--------|-----------|------|
| 539 | 회수·판매중지 | 950건 | - |
| 534 | 공급중단 | 1,285건 | - |
| 537 | 공급부족 | 733건 | - |
| **561** | **의약품 특허** | **120,525건** | ⚠️ **num_of_rows=50 고정** |
| **554** | **재심사** | **112,554건** | ⚠️ **num_of_rows=50 고정** |
| **556** | **재평가** | **64,827건** | ⚠️ **num_of_rows=50 고정** |
| 566 | 임상시험 | 13,903건 | - |
| 142 | 국가출하승인 | 33,550건 | - |
| 483 | DMF | 8,916건 | - |
| 484 | 대조약 | 3,305건 | - |
| 485 | 생동성 | 12,065건 | - |
| 568 | 임상기관 | 232건 | - |

> 대용량 3개(NO 561·554·556): 워크스페이스 KPI 전용은 `num_of_rows=5` 가능, 이벤트 모니터용은 `num_of_rows=50` 고정.

### 5.3 실제 검증된 응답 필드명 — 기존 코드 수정 필요

| NO | API | ❌ 기존 가정 필드 | ✅ 실제 검증 필드 |
|----|-----|----------------|----------------|
| 140 주성분 | 허가 주성분 | ITEM_NAME, ENTP_NAME | **ENTRPS, PRDUCT, MTRAL_NM, MTRAL_CODE** |
| 547 | 안전성서한 | title, content | **TITLE, SUMRY_CONT, PBANC_CONT, PBANC_YMD, SAFT_LETT_NO** |
| 565 | 희귀의약품 | PRDUCT_NAME | **PRODT_NAME, TARGET_DISEASE, RARITY_DRUG_APPOINT_NO, APPOINT_DATE** |
| 535 | 검사부적합 | PRODUCT | **PRDUCT, IMPROPT_ITM, REGIST_DT, FOOD_TY** |
| 12 | 스마트HACCP | BSSH_NM | **businessnm, company, appointno, sido, ceoname** |
| 1 | 식품영양DB | FOOD_NAME | **FOOD_NM_KR, DB_GRP_NM, DB_CLASS_NM, FOOD_CD** |
| 81 | 희귀필수 | 대부분 | **INGR, MEDCIN_NAME** (24건만 존재) |
| 132 | GMP | BSSH_NM (정상) | BSSH_NM · FCTR_ADDR · KGMP_BGMP_NAME · GMP_INGR_MM_GROUP_NAME · **VLD_PRD_YMD** |

### 5.4 광동제약 자사 데이터 검증 결과

```python
# NO 132 GMP — BSSH_NM="광동제약" 조회 결과 (정확)
{
    "BSSH_NM": "광동제약(주)",
    "FCTR_ADDR": "경기도 평택시 산단로 114",
    "KGMP_BGMP_NAME": "완제의약품",
    "GMP_INGR_MM_GROUP_NAME": "내용고형제(정제, 캡슐제, 과립제, 환제), 내용액제",
    "VLD_PRD_YMD": "2027-03-28",   # ← RA 워크스페이스 D-Day 표시 가능
    "BIZRNO": "1138108888"
}
# NO 564 행정처분: 광동제약 0건 → 처분 이력 없음 (정상)
# NO 539 회수: 베니톨정 0건 → 안전 (정상)
```

### 5.5 데이터 0건 = 정상 케이스 — graceful 처리

```python
# 다음 4종은 API 오류가 아닌 "데이터 없음" → 화면에 "해당 데이터 없음" 표시
NORMAL_EMPTY_CASES = {
    "NO 269 묶음의약품":     "HIRA 처방약 위주, 일반의약품 미등록",
    "NO 531 DUR 병용금기":   "일반의약품은 병용금기 미등록",
    "NO 81 자가치료용마약":  "카테고리 전체 0건 (데이터 자체 희소)",
    "NO 564 행정처분 광동":  "광동제약 처분 이력 없음 (정상)",
}
# → try/except 로 감싸되 결과 빈 배열이면 "해당 데이터 없음" 렌더
```

---

## 6. 페이지별 상세 명세

### P1. 홈 대시보드 (신규) — /app/home

```
[영역 A] CRITICAL 긴급 알림 배너 (조건부 — 1건↑일 때만)
  내용: "🔴 오늘 회수명령 N건 · 판매중지 M건 신규"
  클릭: /app/monitor?severity=CRITICAL

[영역 B] 워치리스트 요약 (등록 품목 있을 때)
  🔴 위험 N개 | 🟡 주의 M개 | 🟢 이상없음 K개
  [내 워치리스트 →]

[영역 C] 오늘의 주요 이벤트 TOP 5 (severity 높은 순)
  event_card 매크로 재사용
  [전체 이벤트 보기 →] /app/monitor

[영역 D] 30일 이내 마감 일정 (데이터 없으면 영역 숨김)
  재심사 D-Day 최대 3건
  광동 GMP 만료: 2027-03-28 (NO 132 실 데이터)

[영역 E] 빠른 검색
  검색창 → 제출 시 /?q= redirect
```

백엔드 요점:
```python
@app_bp.route("/home")
def home():
    # 오늘 CRITICAL 이벤트 recall + disciplinary fetch (num_of_rows=5씩)
    # summarize_by_severity() 호출
    # fetch_drug_review(num_of_rows=50) → D-30 이내 마감 필터
    return render_template("app/home.html", active_page="home", ...)
```

---

### P2. 통합 검색 — /

**제거:**
```
❌ KPI 전체 모수 숫자 ("허가건수 25,354건")
❌ 카테고리 칩 10개 병렬 나열
❌ API 번호 카드 노출
❌ 검색 결과와 전체 이벤트 혼재
```

**추가:**
```
✅ 검색 이력 드롭다운 (localStorage JS, 최근 5건)
✅ 빠른 검색 칩 3개 [광동제약] [아세트아미노펜] [최근 회수품목]
✅ 종합 위험 신호등 카드 (검색 후 상단)
✅ 탭 순서: [허가 정보] → [규제 이력] → [낱알 식별]
✅ 광동 관련 배지 (워치리스트 매칭)
```

허가 정보 탭 표시/제거 필드:
```python
DISPLAY_FIELDS = {
    "ITEM_NAME": "품목명", "ENTP_NAME": "업체명",
    "ITEM_PERMIT_DATE": "허가일자",  # YYYYMMDD → YYYY년 MM월 DD일
    "ETC_OTC_CODE": "전문/일반", "MATERIAL_NAME": "주성분",
    "EDI_CODE": "보험코드",    # 있을 때만
    "VALID_TERM": "유효기간",  # 있을 때만
}
ACCORDION_FIELDS = ["BIZRNO", "ENTP_NO", "ITEM_SEQ"]  # 접어두기
```

---

### P3. 이벤트 모니터 — /app/monitor (기존 /app/timeline 확장)

**제거:**
```
❌ API 번호, domain_kr 태그
❌ 동등 나열 (긴급=정보)
❌ 빈 날짜 렌더링
```

**추가:**
```
✅ 현황 배너: 오늘 N건 · 이번 주 M건 · 광동 관련 K건
✅ 필터 바: 기간(오늘/이번주/이번달/직접입력) + 심각도 + 유형 + Excel 내보내기
✅ 심각도 정렬: CRITICAL → HIGH → LOW
✅ NEW 배지 (오늘 날짜), 워치리스트 매칭 배지 (📌)
✅ 동일 품목 이벤트 2건↑ → 그룹 카드
```

---

### P4. 워치리스트 — /app/watchlist

**제거:**
```
❌ 단순 등록일 표시 → "마지막 이벤트 발생일"로 교체
❌ 카운트 숫자만
❌ 등록 순서 정렬
```

**추가:**
```
✅ 상단 요약: 🔴 N개 / 🟡 M개 / 🟢 K개
✅ [+ 품목 추가] [📎 Excel 일괄 업로드] [📥 전체 내보내기]
✅ 위험도 정렬 (CRITICAL → HIGH → LOW → NONE)
✅ <details><summary> 인라인 미리보기 (Alpine.js 없이)
✅ 이벤트 카운트 8종 표시
```

watchlist_match.py 신규 함수:
```python
def summarize_by_severity(match_map):
    """→ {critical, high, ok, total}"""

def critical_alert_count(match_map):
    """CRITICAL 이벤트 보유 항목 수"""

def today_critical_count():
    """오늘 신규 CRITICAL 건수 (5분 TTL 캐시)"""
```

---

### P5. 제품 상세 (의약품) — /app/product/<code>

**제거:**
```
❌ 낱알 이미지 상단 주요 위치 → 마지막 탭으로
❌ 허가 원문 코드 노출 (SPCLTY_PBLC 등)
❌ 업체 행정 정보 전면 노출 → accordion
```

**추가:**
```
✅ 헤더: 종합 위험 신호등 + reasons + 재심사 D-Day
✅ 헤더: [📌 워치리스트] [📥 내보내기]
✅ 탭 순서: [핵심정보] → [규제이력] → [안전성] → [관련품목] → [제품외형]
✅ 규제이력: 가로 스크롤 타임라인 (허가→재심사→처분→예정)
✅ 안전성 탭: DUR 병용금기·임부금기·노인주의 (NO 531·533)
✅ 관련품목 탭: 동일 성분 유사 품목 최대 8건
✅ GMP 적합판정 상태 (NO 132, 제조사 조회)
```

백엔드 핵심:
```python
@app_bp.route("/product/<code>")
def product_drug(code):
    # 기존 허가·처분·회수·낱알 fetch 유지

    # 신규: 위험도 신호등
    from ..blueprints.risk import calc_risk_signal
    risk_signal = calc_risk_signal(
        approval_data=[approval] if approval else [],
        disciplinary_items=disciplinary_items,
        recall_items=recall_items,
        review_due_days=_get_review_due_days(approval),
    )

    # 신규: 동일 성분 유사 품목 (MATERIAL_NAME으로 재검색)
    similar_items = []

    # 신규: DUR 안전성 (NO 531 itemName camelCase)
    dur_info = {"contraindication": [], "pregnancy": [], "elderly": []}

    return render_template("app/product_drug.html",
                           active_page="search",
                           risk_signal=risk_signal,
                           similar_items=similar_items,
                           dur_info=dur_info, ...)
```

---

### P6. 제품 상세 (의약외품) — /app/product-quasi/<code> [신규]

```
[헤더] 품목명 + 업체명 + 허가일 (NO 145, item_name snake_case)
       위험도 신호등

[탭 5개]
  [핵심정보]   NO 145 허가정보
  [규제이력]   NO 564 처분 + NO 539 의약품외 회수
  [안전성]     NO 547 안전성서한
  [품질이벤트] NO 535 검사부적합 (업체 필터)
  [공급망]     NO 534 공급중단

  제거: R&D(특허·임상·재심사), 낱알식별
```

신규 파일:
- `api_extras.py`: `fetch_quasi_approval(item_name, entp_name)` — NO 145 엔드포인트
- `templates/app/product_quasi.html`: 신규
- `blueprints/app_views.py`: `/app/product-quasi/<code>` 라우트

---

### P7. 워크스페이스 — /app/workspace/<dept>

**공통 수정:**
```
❌ placeholder "—" 전면 제거 (Phase 4 완료)
❌ KPI 숫자만 → 각 KPI에 [바로가기] 링크
```

**RA 워크스페이스 재설계:**

```python
# workspaces_config.py RA 섹션 변경
# kpi_specs → sections 구조
{
    "sections": [
        {
            "type": "deadline_calendar",
            "title": "D-90 이내 마감",
            "api_fn": "fetch_drug_review",  # NO 554, num_of_rows=50
            "window_days": 90,
        },
        {
            "type": "kpi_row",
            "kpis": [
                {"label": "재심사 진행", "api": "fetch_drug_review", "color": "warn"},
                {"label": "재평가 진행", "api": "fetch_drug_reeval", "color": "info"},
            ],
        },
        {
            "type": "static_info",
            "label": "GMP 만료",
            "value": "광동제약(주) 2027-03-28",  # NO 132 실 데이터
        },
    ]
}
```

D-Day 캘린더 화면:
```
┌──────────┬──────────┬──────────┐
│ D-12     │ D-28     │ D-45     │
│ 품목A    │ 품목B    │ 품목C    │
│ 재심사   │ 재심사   │ 재평가   │
│[상세 →]  │[상세 →]  │[상세 →]  │
└──────────┴──────────┴──────────┘
GMP 만료: 광동제약(주) 2027-03-28
```

**R&D 워크스페이스 (대용량 API num_of_rows=50 적용):**
```
임상시험 N건 (NO 566): APPLY_ENTP_NAME, GOODS_NAME, CLINIC_EXAM_TITLE
특허 N건 (NO 561, num_of_rows=50): INGR_ENG_NAME, ITEM_NAME, ENTP_NAME
생동성 N건 (NO 485): ITEM_NAME, ENTP_NAME, BIOEQ_NOTICE_DATE

특허 분쟁 트래커 (R3-9 신규):
  국내소송 (NO 557): INGR_NAME, PRT_NAME, KOR_PAT_NO
  FDA 오렌지북 (NO 562): INGR_NAME, KOR_EXP_DATE, KOR_STATUS
  FDA P4 (NO 552): DRUG_NAME, DOSAGE_FORM, RLD
```

**식품QA 워크스페이스 (R3-8 신규):**
```
식품 행정처분 3종 (NO 3·5·6, PRCSCITYPOINT_BSSHNM):
  수입식품업 N건 · 식품판매업 M건 · 식품제조가공업 K건
  통합 카드 + DSPS_DCSNDT 정렬
```

---

### P8. 검사부적합 트래커 — /app/inspections

**정보 구성 (KPI 우선순위 재배열):**

```
[1순위 KPI — 2칸, 가장 크게]
  🔴 광동 관련 부적합 N건 | 🟡 최근 30일 신규 M건

[2순위 KPI — 4칸]
  잔류농약 N건 | 중금속 M건 | 미생물 K건 | 이물·기타 P건

[필터 바] 기본값: 최근 30일 전체 (빈 화면 방지)
  기간 + 부적합 사유 + 검색 + [Excel 내보내기]

[CSS 가로 바 분류 차트] (JS 없이 순수 CSS width 계산)

[제조소 위험 순위 TOP 5]
  5건↑ → 🔴 배지

[부적합 목록] 광동 매칭 → 빨간 테두리 + 상단 고정
  검증 필드: PRDUCT · ENTRPS · IMPROPT_ITM · REGIST_DT · FOOD_TY
```

분류 헬퍼:
```python
def classify_reason(text):
    if not text: return "이물·기타"
    r = text.lower()
    if "농약" in r or "잔류" in r: return "잔류농약"
    if "중금속" in r or "납" in r: return "중금속"
    if "세균" in r or "대장균" in r: return "미생물"
    return "이물·기타"
```

---

### P9. AI 코파일럿 — /app/copilot

**추가:**
```
✅ 상단 "오늘 시스템 현황" 브리핑 패널 (시스템 프롬프트 자동 주입)
✅ 빠른 질문 템플릿 3카테고리:
   GMP/규제: [회수 품목 부적합 사유 요약] [GMP 실사 체크리스트] [재심사 서류 가이드]
   경쟁사: [신규 허가 경쟁 품목] [아세트아미노펜 시장 현황]
   공급망: [공급부족 품목 대체재 분석]
✅ 대화 결과 [복사] 버튼
```

시스템 프롬프트에 주입할 컨텍스트:
```python
# copilot() 라우트에서 생성
context_summary = f"""
현재 KD-IRIS 시스템 현황:
- 워치리스트 등록: {wl_count}개 (이벤트 있음: {critical}개)
- 오늘 신규 CRITICAL: {today_critical}건
- 광동제약 GMP 만료: 2027-03-28 (평택공장)
- 30일 이내 재심사 마감: {review_count}건
"""
```

---

## 7. 신규 API 22개 연동 계획

### 7.1 DUR 안전성 (P5 안전성 탭) — N-1·N-2

```python
# api_extras.py 신규 함수
# NO 533 DUR 성분정보 — INGR_NAME 파라미터
def fetch_dur_ingredient_contraindication(ingr_name=None, num_of_rows=20):
    # 엔드포인트: DURIrdntInfoService03/getUsjntTabooInfoList02
    # 검증 필드: TYPE_NAME, INGR_CODE, INGR_ENG_NAME, INGR_KOR_NAME, ORI
    pass

# NO 531 DUR 품목정보 — itemName camelCase 파라미터
def fetch_dur_item_pregnancy(item_name=None, num_of_rows=20):
    # 엔드포인트: DURPrdlstInfoService03/getPwnmTabooInfoList03
    # 검증 필드: TYPE_NAME, INGR_CODE, INGR_ENG_NAME, ITEM_SEQ, ITEM_NAME
    pass

def fetch_dur_item_elderly(item_name=None, num_of_rows=20):
    # 엔드포인트: DURPrdlstInfoService03/getOdsnAtentInfoList03
    pass
```

0건 처리: 일반의약품·OTC는 DUR 미등록이 정상 → "해당 데이터 없음" 표시

### 7.2 GMP·출하·업체 (QA/QC 핵심) — N-9·10·11·12

| NO | 서비스명 | 검증 상태 | 활용 위치 |
|----|---------|-----------|----------|
| N-9 | GMP 적합판정서 | ✅ 광동 1건 확인 | P5 규제이력 탭 |
| N-10 | 국가출하승인 | ✅ 33,550건 | P5 규제이력 탭 |
| N-11 | 업체허가현황 | ✅ 2,959건 | 업체 상세 |
| N-12 | 원료의약품 DMF | ✅ 8,916건 | SCM 워크스페이스 |

### 7.3 R&D 특허·임상 (R&D 워크스페이스) — N-5·6·7·8·15

```python
# 모두 클라이언트 필터, 검증 완료
def fetch_fda_orangebook(num_of_rows=20):
    # NO 562: INGR_NAME, PRT_NAME, KOR_PAT_NO, KOR_STATUS, KOR_EXP_DATE
    pass

def fetch_fda_paragraph4(num_of_rows=20):
    # NO 552: DRUG_NAME, DOSAGE_FORM, STRENGTH, RLD
    pass

def fetch_drug_lawsuit(num_of_rows=20):
    # NO 557: INGR_NAME, PRT_NAME, JUDGMENT_KIND, KOR_PAT_NO, SIGN_OF_CASE
    pass
```

### 7.4 소비자 정보 — N-13·14

```
e약은요 (NO 248): itemName camelCase, 검증 완료
  efcyQesitm(효능), useMethodQesitm(사용법), atpnQesitm(주의), seQesitm(부작용)
  ※ 베니톨정 미등록 (일반의약품 일부 소비자 안내 없음) → 정상 처리

묶음의약품 (NO 269): HIRA 처방약 위주, 0건 = 정상
```

### 7.5 식품·건강기능식품 — N-16~N-22

```python
# 식품 행정처분 3종 — PRCSCITYPOINT_BSSHNM UPPER_CASE, 모두 검증 완료
def fetch_food_sanction_import(num_of_rows=20):        # NO 3, 56건
    pass  # DSPS_DCSNDT, DSPS_TYPECD_NM, VILTCN

def fetch_food_sanction_sale(num_of_rows=20):          # NO 5, 686건
    pass

def fetch_food_sanction_manufacture(num_of_rows=20):   # NO 6, 296건
    pass

# 건강기능식품 GMP (NO 51) — 이미 구현됨
# LCNS_NO, BSSH_NM, INDUTY_CD_NM, SITE_ADDR, CLSBIZ_DVS_CD_NM
```

### 7.6 신규 API 구현 우선순위

| 순위 | API (번호) | 이유 |
|------|-----------|------|
| ⭐⭐⭐ | DUR N-1·N-2 | P5 안전성 탭 완성, QA/QC 핵심 |
| ⭐⭐⭐ | GMP N-9 | 광동 조회 검증 완료, 출하 결재 필수 |
| ⭐⭐⭐ | 식품 행정처분 N-22 (3종) | 식품QA 워크스페이스 완성, 모두 작동 |
| ⭐⭐ | FDA 특허 N-5·6·7 | R&D 트래커, 모두 작동 확인 |
| ⭐⭐ | e약은요 N-13 | P5 핵심정보 탭 보강 |
| ⭐⭐ | 건기식 GMP N-20 | 식품QA HACCP 보완, 작동 확인 |
| ⭐ | 희귀의약품 N-4 | 필드명 수정 후 사용 가능 |
| ⭐ | DMF N-12 | SCM 원료 공급망 |

---

## 8. 현재 완료 상태 (Phase 1~4)

> Claude Code 실행 전 확인. 이미 완료된 항목은 재작업 불필요.

### 8.1 완료된 작업 목록

| 항목 | 완료 Phase | 비고 |
|------|-----------|------|
| `templates/_layout.html` 공통 레이아웃 | Phase 1 | Jinja2 상속 구조 |
| `blueprints/nav_config.py` 5개 메뉴 | Phase 1 | → R1-4에서 7개로 확장 필요 |
| 사이드바 활성화 표시 (`active_page`) | Phase 1 | |
| 다크모드 + 모바일 햄버거 | Phase 1 | |
| GitHub push (6 커밋) | Phase 3 | `kong9365/Drug_integrated_search` |
| `config.py` SERVICE_KEY 보안 처리 | Phase 3 | 평문 키 제거 완료 |
| 워크스페이스 KPI placeholder 6개 실 데이터 연결 | Phase 4 | NO 554·537·566·561·485·12 |
| `watchlist_match.py` 8종 매칭 (특허·임상·재심사·재평가 추가) | Phase 4 | |
| 검사부적합 트래커 기본 페이지 (`/app/inspections`) | Phase 4 | → R3-4에서 차트+순위 추가 |
| 이벤트 타임라인 R&D 4종 subtabs 추가 | Phase 4 | → R1-5에서 `/app/monitor`로 통합 |

### 8.2 남아있는 작업 수 요약

| Phase | 작업 수 | 예상 기간 |
|-------|---------|-----------|
| **R-1** | 9개 | 1~2일 |
| **R-2** | 9개 | 3~5일 |
| **R-3** | 9개 | 1~2주 |
| **R-4** (장기) | Phase 2 범위 | 별도 사이클 |

---

## 9. 구현 Phase 로드맵 — Claude Code 실행 기준

> 각 Phase 끝마다 `git commit + push`. 사용자 검토 후 다음 Phase 진행.

### Phase R-1 (즉시, 1~2일 — 9개 작업)

#### R1-0. KD-IRIS 리브랜딩

| 파일 | 변경 |
|------|------|
| `templates/_layout.html` | `<title>` + `.logo` "RegHub 360" → "KD-IRIS" |
| `templates/app/*.html` (전체) | `{% block title %}` "광동 RegHub 360" → "광동 KD-IRIS" |
| `app.py` | `print()` 메시지 + `healthz` 응답 `"service": "KD-IRIS"` |
| `run.py` | print 메시지 |
| `README.md` / `README_RUN.md` / `docs/HANDOFF.md` | 헤더·본문 |
| 로고 부제 (선택) | "KwangDong Integrated Regulatory Intelligence System" 작은 글씨 |

검증: `grep -r "RegHub 360" templates/ app.py run.py README.md` → 0건

#### R1-1. API 코드·도메인 태그 전면 제거

모든 `templates/app/*.html`, `app_views.py`, `_normalize_event()`:
- `{{ ev.api }}` 제거 (timeline.html, watchlist.html, workspace.html, inspections.html)
- `{{ ev.domain_kr }}` 제거
- `event_kinds|join(' · ')` raw key → 한글 라벨 변환
- 필드명 노출 (`product_live.ITEM_SEQ` 등) → accordion 또는 제거
- `"—"` placeholder → `{% if value and value != "—" %}` 조건부

#### R1-2. SEVERITY_MAP + _macros.html 신설

| 파일 | 내용 |
|------|------|
| **신규** `blueprints/severity.py` | §3.2 코드 전체 |
| **신규** `templates/_macros.html` | §3.4 `event_card()` 매크로 전체 |

#### R1-3. _normalize_event() 출력 스키마 통일

`blueprints/app_views.py` + `blueprints/watchlist_match.py` 두 곳:
- §3.3 스키마 적용 (type_label · severity_level · severity_color · is_new · product_code · in_watchlist)
- `api` · `url` · `domain` · `domain_kr` 키 제거
- 빈 `date` → 그대로 유지 (템플릿에서 "날짜 미확인" 렌더)

#### R1-4. nav_config.py 7개 메뉴 확장

§4.2 코드 전체로 `NAV_ITEMS` 교체:
- `home` 신규 최상단
- `search` 라벨 "제품·업체 조회"
- `monitor` 신규 키 `/app/monitor`
- `workspace` 단일 진입점 + `children` 5개
- `reports` `disabled: True` 복귀

#### R1-5. /app/monitor 라우트 신설 + /app/timeline redirect

| 파일 | 변경 |
|------|------|
| `blueprints/app_views.py` | `monitor()` 함수 신설 (§P3 백엔드 명세) |
| `blueprints/app_views.py` | 기존 `timeline()` → `return redirect(url_for("app.monitor"), 301)` |
| **신규** `templates/app/monitor.html` | `timeline.html` 본문 + 현황 배너 + 필터 바 + `event_card` 매크로 교체 |

#### R1-6. /app/workspace 단일 진입 라우트

`blueprints/app_views.py`:
```python
@app_bp.route("/workspace")
def workspace_index():
    return redirect(url_for("app_bp.workspace", dept="ra"))
```

#### R1-7. 의약외품 Product 360 신설

| 파일 | 변경 |
|------|------|
| `api_extras.py` | `fetch_quasi_approval(item_name=None, entp_name=None)` 신설 — NO 145 `QdrgPrdtPrmsnInfoService03`, snake_case 파라미터 |
| **신규** `templates/app/product_quasi.html` | `product_drug.html` 5탭 구조 복제 (R&D·낱알 제거, §P6 명세) |
| `blueprints/app_views.py` | `/app/product-quasi/<code>` 라우트 + 검색 결과 의약외품(`INDUTY == "의약외품"`) 매칭 시 라우팅 분기 |

#### R1-8. blueprints/risk.py 신설

§3.5 `calc_risk_signal()` 함수 전체 구현.

---

### Phase R-2 (단기, 3~5일 — 9개 작업)

#### R2-1. 통합검색 결과 신호등 카드

`templates/app/search.html` + `blueprints/app_views.py` `search()`:
- 검색 후 상단: 종합 위험 신호등 카드 (`calc_risk_signal` 호출)
- "검색 결과 N건 + 관련 이벤트 M건" 헤더
- 검색 전: 검색 이력 드롭다운(localStorage JS) + 빠른 검색 칩 3개

#### R2-2. 제품 상세 헤더 신호등 + 재심사 D-Day

`blueprints/app_views.py` `product_drug()` + `templates/app/product_drug.html`:
- 헤더: 신호등 + reasons 라벨 + 재심사 D-Day
- `_get_review_due_days(approval)` 헬퍼 (데이터 없으면 None → 섹션 숨김)

#### R2-3. 이벤트 모니터 필터 + NEW 배지 + 그룹화

`templates/app/monitor.html` + `monitor()`:
- querystring 필터: `?severity=CRITICAL&type=recall&period=week`
- `is_new` 기반 NEW 배지
- 동일 `ITEM_NAME` 2건↑ → 그룹 카드 묶음

#### R2-4. 워치리스트 위험도 정렬 + 인라인 미리보기

`templates/app/watchlist.html`:
- 카드 정렬: CRITICAL → HIGH → LOW → NONE
- `<details><summary>` 최신 이벤트 접기/펼치기
- 상단 요약 패널: 🔴 N개 / 🟡 M개 / 🟢 K개

#### R2-5. watchlist_match.py 집계 헬퍼 신설

§P4 명세의 3개 함수 구현:
- `summarize_by_severity(match_map)`
- `critical_alert_count(match_map)`
- `today_critical_count()` (5분 TTL `_cached` 활용)

#### R2-6. 홈 대시보드 /app/home 신설

`blueprints/app_views.py` `home()` + **신규** `templates/app/home.html`:
- §P1 영역 A~E 전체 구현
- `inject_nav()` 의 `monitor` 배지 = `today_critical_count` 기반

#### R2-7. inject_nav() CRITICAL 배지 동적 주입

`app.py` §4.3 코드로 교체:
- `monitor` 배지: `today_critical_count`
- `watchlist` 배지: `critical_alert_count` 우선, `wl_total` 폴백

#### R2-8. DUR 안전성 탭 연동 — 신규 API N-1·N-2

| 파일 | 변경 |
|------|------|
| `api_extras.py` | §7.1 3개 함수 구현 (NO 533 INGR_NAME, NO 531 **camelCase** itemName) |
| `templates/app/product_drug.html` | 안전성 탭에 DUR 3종 카드 (0건 시 "해당 데이터 없음") |

#### R2-9. GMP 적합판정 탭 연동 — 신규 API N-9

| 파일 | 변경 |
|------|------|
| `api_extras.py` | `fetch_drug_gmp()` 필드 매핑 검증 (§5.3 기준) |
| `templates/app/product_drug.html` 규제이력 탭 | GMP 상태 카드 (광동 `VLD_PRD_YMD: 2027-03-28` 표시) |

---

### Phase R-3 (중기, 1~2주 — 9개 작업)

#### R3-1. RA 워크스페이스 D-Day 캘린더 재설계

`blueprints/workspaces_config.py` RA 섹션:
- `kpi_specs` → `sections` 구조 (§P7 명세)
- `deadline_calendar` 타입 (D-90 이내 3카드)
- `kpi_row` 타입 (재심사/재평가/신규허가 건수)
- `static_info` 타입 (GMP 만료일 표시)

`templates/app/workspace.html`:
- `{% if workspace.sections %}` 분기 — sections 모드 vs 기존 kpi_specs 모드
- RA 외 부서는 기존 모드 유지

#### R3-2. 제품 상세 규제 타임라인 섹션

`templates/app/product_drug.html`:
- 탭 순서 재배열: 핵심정보 → 규제이력 → 안전성 → 관련품목(신규) → 제품외형
- 규제이력 탭 상단: 가로 스크롤 타임라인 (허가일·재심사·처분·재심사예정)
- 기존 `app.css` alert-row 패턴 재활용

#### R3-3. 동일 성분 유사 품목 조회

`blueprints/app_views.py` `product_drug()`:
- `MATERIAL_NAME` (검증 필드) 기반 재검색 → 최대 8건
- 자기 자신 제외 + 위험도 신호등 함께 표시
- 신규 탭 "관련 품목" (`data-p360-tab="related"`) 패널

#### R3-4. 검사부적합 분류 차트 + 제조소 위험 순위

`blueprints/app_views.py` `inspections()` + `templates/app/inspections.html`:
- `classify_reason()` 헬퍼 (§P8)
- CSS 순수 가로 바 차트 (JS 없이)
- 제조소 TOP 5 테이블 (5건↑ 🔴 배지)
- KPI 1순위 광동 관련 2칸 + 2순위 분류 4칸
- 광동 매칭 항목 상단 고정
- 검증 필드명 사용: `PRDUCT` · `ENTRPS` · `IMPROPT_ITM` · `REGIST_DT`

#### R3-5. 워치리스트 Excel 일괄 업로드

`blueprints/app_views.py` `POST /app/watchlist/upload`:
- multipart `file` → `openpyxl`로 `ITEM_NAME` 컬럼 읽기
- 미리보기 모달 (제출 전 검토)
- `watchlist_store.add_entry()` 일괄 호출

#### R3-6. AI 코파일럿 맥락 자동 주입

`blueprints/app_views.py` `copilot()` + `templates/app/copilot.html`:
- §P9 시스템 프롬프트 컨텍스트 생성 코드
- 상단 "오늘 시스템 현황" 브리핑 패널
- 빠른 질문 템플릿 3카테고리
- MISO `drug_consult_agent` 연동 유지, 시스템 프롬프트만 보강
- 대화 결과 [복사] 버튼

#### R3-7. Excel 내보내기 공통 라우트

`blueprints/app_views.py`:
- `/app/export/<resource>?format=xlsx` — resource ∈ {monitor, watchlist, inspections}
- `openpyxl`로 워크북 생성 → `send_file` 응답
- 각 페이지 톱바 "Excel 내보내기" 버튼 wiring

#### R3-8. 식품 행정처분 3종 연동 — 신규 API N-22

| 파일 | 변경 |
|------|------|
| `api_extras.py` | `fetch_food_sanction_import` (NO 3) · `_sale` (NO 5) · `_manufacture` (NO 6) — `PRCSCITYPOINT_BSSHNM` UPPER_CASE |
| `templates/app/workspace.html` 식품QA | 3종 통합 카드 + `DSPS_DCSNDT` 정렬 |

#### R3-9. FDA 특허 트래커 — 신규 API N-5·N-6·N-7

| 파일 | 변경 |
|------|------|
| `api_extras.py` | §7.3 3개 함수 구현 (모두 클라이언트 필터) |
| `templates/app/workspace.html` R&D | 특허 분쟁 트래커 카드 (국내 소송 + FDA 오렌지북 + FDA P4) |

---

### Phase R-4 (장기 — Phase 2 범위)

- 리포트 실구현 (PDF/Excel 생성)
- Slack 웹훅 알림 연동
- 워크스페이스 하위 메뉴 accordion
- 건강기능식품 허브 신규 페이지 (N-17·18·19·21)
- 검색 이력 서버사이드 저장

---

## 10. 검증 체크리스트

### 10.1 공통 검증

```bash
# 리브랜딩 완료
grep -r "RegHub 360" templates/ app.py run.py README.md   # 0건

# 개발자 코드 제거
grep -r "API [0-9]" templates/    # 0건
grep -r "domain_kr" templates/    # 0건
grep -r '"—"' templates/          # 0건

# 사이드바 7개 메뉴 노출 (브라우저)
# 다크모드 토글 + 새로고침 후 유지
# 모바일(900px↓) 햄버거 버튼 노출 + 슬라이드
```

### 10.2 페이지별 검증

| 페이지 | 핵심 검증 항목 |
|--------|---------------|
| `/app/home` | CRITICAL 배너 조건부, 워치리스트 3숫자, D-Day 캘린더, GMP 만료일 |
| `/` (검색) | 검색 전 안내 배너, 검색 후 신호등 카드, 탭 순서 |
| `/app/monitor` | CRITICAL→HIGH→LOW 정렬, 기간 필터, NEW 배지, 📌 매칭 배지 |
| `/app/watchlist` | 위험도 정렬, `<details>` 미리보기, 요약 3숫자 |
| `/app/product/<code>` | 헤더 신호등, 5탭 순서, DUR 안전성, GMP 상태, 관련품목 탭 |
| `/app/product-quasi/<code>` | 200 OK, 의약외품 5탭, NO 145 데이터 |
| `/app/workspace/ra` | D-Day 캘린더 카드, GMP 만료일 `2027-03-28` |
| `/app/workspace/scm` | 공급부족 테이블, placeholder 0건 |
| `/app/workspace/rnd` | 임상·특허·생동성 실 건수 (대용량 50 제한) |
| `/app/workspace/food_qa` | 식품 행정처분 3종 건수, 건기식 GMP 건수 |
| `/app/inspections` | 광동 KPI 1순위 2칸, CSS 분류 차트, 제조소 순위 |
| `/app/copilot` | 시스템 현황 브리핑, 빠른 질문 3카테고리 |

### 10.3 API 필드 매핑 검증

```python
# api_extras.py 수정 후 확인
assert "PRODT_NAME" in fetch_rare_drug()["items"][0]          # NO 565
assert "TITLE" in fetch_safety_letter(TITLE="주의")           # NO 547 UPPER
assert "BSSH_NM" in fetch_drug_gmp(BSSH_NM="광동")           # NO 132
assert "PRDUCT" in fetch_food_inspect()["items"][0]           # NO 535
assert "company" in fetch_smart_haccp()["items"][0]           # NO 12
assert "VLD_PRD_YMD" in fetch_drug_gmp(BSSH_NM="광동제약")   # 광동 만료일
```

### 10.4 회귀 테스트

```
□ /healthz → {"ok": true, "service": "KD-IRIS"} 200 OK
□ /app/timeline → /app/monitor 301 redirect
□ 워치리스트 CRUD + 8종 매칭 유지
□ 광동 GMP: BSSH_NM="광동제약" → 1건, VLD_PRD_YMD="2027-03-28"
□ 대용량 API (NO 561·554·556) num_of_rows=50 제한 확인
□ 데이터 0건 케이스(NO 269·531·81·564) "해당 데이터 없음" 표시
□ 모든 워크스페이스 200 OK + placeholder "—" 0건
□ API 타임아웃(30초) 시 graceful 에러 처리
```

---

## 11. 비-목표

- HTMX/SPA 라우팅 도입
- 사용자 인증·세션 (USER_INFO 하드코딩 유지)
- Slack 웹훅 실알림 (UI 버튼만, 실 발송 X)
- PDF 리포트 실생성 (Phase R-4)
- 워크스페이스 하위 메뉴 accordion (Phase R-4)
- 건강기능식품 허브 신규 페이지 (Phase R-4)
- 검색 자동완성 서버사이드
- 마약류 통계 대시보드 (NO 81)
- 사용자별 설정 DB 저장
- 외부 LIMS 연동
- 영업 워크스페이스 `share` KPI
- 워치리스트 자동 이메일·Slack 알림 (다음 사이클)
- 새 SERVICE_KEY 발급·기존 키 폐기 (사용자 별도 수행)
- GitHub Actions CI/CD 설정

---

## 부록 A — 전체 API 목록 (45개, 검증 상태 포함)

| NO | 서비스명 | 검증 | 파라미터 케이스 | 서버검색 | num_of_rows 제한 |
|----|---------|------|----------------|---------|-----------------|
| 1 | 식품 영양성분DB | 🟡 | FOOD_NM_KR | ✅ | - |
| 3 | 식품 행정처분(수입) | ✅ | PRCSCITYPOINT_BSSHNM | ✅ | - |
| 5 | 식품 행정처분(판매) | ✅ | PRCSCITYPOINT_BSSHNM | ✅ | - |
| 6 | 식품 행정처분(제조) | ✅ | PRCSCITYPOINT_BSSHNM | ✅ | - |
| 12 | 스마트HACCP | 🟡 | - (전체) | ❌ | - |
| 51 | 건기식 GMP | ✅ | - (전체) | ❌ | - |
| 81 | 희귀필수의약품 | ⚪ | - | ❌ | - |
| 132 | GMP 적합판정서 | ✅ | **BSSH_NM** | ✅ | - |
| 140 | 의약품 허가 | ✅ | **item_name** (**edi_code** 우선) | ✅ | - |
| 142 | 국가출하승인 | ✅ | - (전체) | ❌ | - |
| 144 | 업체허가현황 | ✅ | - (전체) | ❌ | - |
| 145 | 의약외품 허가 | ✅ | **item_name** | ✅ | - |
| 153 | 수입식품 회수 | ✅ | - (전체) | ❌ | - |
| 248 | e약은요 | ✅ | **itemName** (camel) | ✅ | - |
| 269 | 묶음의약품 | ⚪ 0건 정상 | trustItemName | ✅ | - |
| 483 | 원료의약품 DMF | ✅ | - (전체) | ❌ | - |
| 484 | 대조약 | ✅ | - (전체) | ❌ | - |
| 485 | 생동성인정품목 | ✅ | - (전체) | ❌ | - |
| 531 | DUR 품목정보 | 🟡 | **itemName** (camel) | ✅ | - |
| 533 | DUR 성분정보 | ✅ | INGR_NAME | ✅ | - |
| 534 | 공급중단 | 🟡 | - (전체) | ❌ | - |
| 535 | 검사부적합 | ✅ | - (전체) | ❌ | - |
| 537 | 공급부족 | 🟡 | - (전체) | ❌ | - |
| 539 | 의약품 회수 | ✅ | - (전체) | ❌ | - |
| 547 | 안전성서한 | 🟡 | **TITLE** (대문자) | ✅ | - |
| 552 | FDA Paragraph IV | ✅ | - (전체) | ❌ | - |
| 554 | 재심사 | ✅ | - (전체) | ❌ | **⚠️ 50** |
| 556 | 재평가 | ✅ | - (전체) | ❌ | **⚠️ 50** |
| 557 | 국내소송 특허 | ✅ | - (전체) | ❌ | - |
| 561 | 의약품 특허 | ✅ | - (전체) | ❌ | **⚠️ 50** |
| 562 | FDA 오렌지북 | ✅ | - (전체) | ❌ | - |
| 563 | 낱알식별 | ✅ | **item_name** | ✅ | - |
| 564 | 행정처분 | 🟡 | **item_name** | ✅ | - |
| 565 | 희귀의약품 | 🟠 필드 수정 | - (전체) | ❌ | - |
| 566 | 임상시험 | ✅ | - (전체) | ❌ | - |
| 568 | 임상기관 | ✅ | - (전체) | ❌ | - |

---

## 부록 B — 작업 순서 권장

```
Step 1: Phase R-1 (9개 작업)
  git commit -m "feat: KD-IRIS 리브랜딩 + R-1 공통 기반"
  git push origin main

Step 2: 사용자 화면 검토 (브라우저에서 7개 메뉴·리브랜딩 확인)

Step 3: Phase R-2 (9개 작업)
  git commit -m "feat: R-2 의사결정 지원 UI + DUR·GMP 연동"
  git push origin main

Step 4: 사용자 검토 (신호등 카드·홈 대시보드·안전성 탭 확인)

Step 5: Phase R-3 (9개 작업)
  git commit -m "feat: R-3 심화 기능 + 식품처분·FDA 특허 트래커"
  git push origin main

Step 6: 전체 검증 체크리스트 §10 실행
```

---

*문서 끝 — KD-IRIS 통합 리뉴얼 명세서 v3.0*  
*기준: RENEWAL_PLAN v1.0 → v2.0 → v3.0 (Phase 5 v2 Claude Code 실행 명세 통합)*  
*이미 완료 항목(Phase 1~4) 반영, 작업 단위 세분화 (R-1·R-2·R-3 각 9개), API 전수 검증 결과 최종 반영*
