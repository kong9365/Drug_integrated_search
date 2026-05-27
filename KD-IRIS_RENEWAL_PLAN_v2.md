# KD-IRIS — 통합 리뉴얼 전체 명세서 v2.0

> **시스템명**: KD-IRIS (KwangDong Integrated Regulatory Intelligence System)  
> **구 명칭**: RegHub 360 → 전면 리브랜딩  
> **기준 레포**: `https://github.com/kong9365/Drug_integrated_search`  
> **작성 기준일**: 2026-05-27  
> **작성**: 품질관리2팀 AI TF (MISO-52g TF)  
> **API 검증**: 44개 오퍼레이션 전수 검증 완료 (완전 작동 32 + 부분 12 + 실패 0)

---

## 목차

1. [리뉴얼 목적 및 핵심 원칙](#1-리뉴얼-목적-및-핵심-원칙)
2. [KD-IRIS 리브랜딩 범위](#2-kd-iris-리브랜딩-범위)
3. [전체 공통 변경사항](#3-전체-공통-변경사항)
4. [네비게이션 구조 재편 (7개 메뉴)](#4-네비게이션-구조-재편)
5. [API 검증 결과 및 구현 지침](#5-api-검증-결과-및-구현-지침)
6. [페이지별 상세 명세](#6-페이지별-상세-명세)
7. [신규 API 22개 연동 계획](#7-신규-api-22개-연동-계획)
8. [구현 Phase 로드맵](#8-구현-phase-로드맵)
9. [검증 체크리스트](#9-검증-체크리스트)
10. [비-목표](#10-비-목표)

---

## 1. 리뉴얼 목적 및 핵심 원칙

### 1.1 핵심 문제 정의

현재 시스템은 **데이터 나열형** 구조다. API 결과를 그대로 렌더링하여 실무자가 "지금 당장 무엇을 해야 하나"를 파악하기 위해 여러 탭을 탐색해야 한다. 개발자용 코드(`API 539`, `NO 547`, `SPCLTY_PBLC` 등)가 화면에 그대로 노출되고, 긴급·정보성 이벤트가 동등 나열되어 우선순위 인식이 불가능하다.

### 1.2 리뉴얼 방향

| 기존 | 목표 |
|------|------|
| 데이터 나열형 | 의사결정 지원형 |
| API 탭별 분리 조회 | 제품 중심 통합 뷰 |
| 단순 카운트 KPI | 맥락 있는 액션 KPI |
| 개발자 코드 노출 | 실무 언어로 정리 |
| 동등 나열 | 심각도 기반 우선순위 |
| RegHub 360 | KD-IRIS (리브랜딩) |

### 1.3 사용자 페르소나

| 순위 | 팀 | 주요 관심사 | 핵심 질문 |
|------|-----|-------------|-----------|
| 1 | **QA/QC** | 회수·처분·GMP | "지금 당장 대응해야 할 이슈가 있나?" |
| 2 | **RA** | 재심사·변경허가 마감 | "언제까지 뭘 제출해야 하나?" |
| 3 | **SCM** | 공급부족·회수 영향 | "어떤 품목이 공급 위험 상태인가?" |
| 4 | **R&D** | 임상·특허·경쟁사 | "경쟁사 파이프라인이 어디까지 왔나?" |
| 5 | **식품QA** | 검사부적합·HACCP | "이 원재료, 쓸 수 있는 건가?" |

### 1.4 설계 원칙

- **원칙 1 — 맥락 우선**: 검색 결과·이벤트에 항상 "그래서 뭘 해야 하나"가 보여야 한다.
- **원칙 2 — 심각도 계층**: 🔴 긴급 → 🟡 주의 → 🟢 정보 3단계를 일관되게 적용한다.
- **원칙 3 — 개발 코드 전면 제거**: `API XXX`, `NO XXX`, `domain_kr`, 필드명 코드 일체 화면 노출 금지.
- **원칙 4 — 제품 중심 통합**: 모든 이벤트는 특정 제품·업체로 드릴다운 가능해야 한다.
- **원칙 5 — 즉시 행동 가능**: 이벤트 카드에 반드시 "다음 액션 링크"가 있어야 한다.

---

## 2. KD-IRIS 리브랜딩 범위

### 2.1 변경 대상 파일 전체 목록

| 파일 | 변경 내용 |
|------|-----------|
| `templates/_layout.html` | `<title>` 기본값 + `.logo` 텍스트 "RegHub 360" → "KD-IRIS" |
| `templates/app/*.html` (전체) | `{% block title %}` 의 "RegHub 360" / "광동 RegHub 360" → "KD-IRIS" / "광동 KD-IRIS" |
| `app.py` | `print()` 메시지 제품명 교체 |
| `run.py` | print 메시지 교체 |
| `README.md` | 헤더·본문 제품명 교체 |
| `README_RUN.md` | 헤더 교체 |
| `docs/HANDOFF.md` (있을 경우) | 헤더 교체 |

### 2.2 브랜드 표기 규칙

```
공식 전체명: KD-IRIS
풀네임: KwangDong Integrated Regulatory Intelligence System
화면 표시: KD-IRIS
부제 (로고 하단 선택): KwangDong Integrated Regulatory Intelligence System
내부 코드명: kd_iris (snake_case)
```

### 2.3 리브랜딩 완성도 검증

```bash
# 리브랜딩 완료 확인
grep -r "RegHub 360" templates/ app.py run.py README.md
# 결과: 0건이어야 함
```

---

## 3. 전체 공통 변경사항

### 3.1 즉시 제거할 요소 (전체 템플릿)

아래 항목들은 **모든 페이지·카드·테이블에서 전면 삭제**한다.

```
삭제 대상:
- "API 539", "API 547", "NO 554" 등 API 번호 표시 → {{ ev.api }} 렌더링 제거
- "domain: drug", "domain_kr: 의약품" 중복 태그 → {{ ev.domain_kr }} 제거
- 필드명 코드 원문 노출 (SPCLTY_PBLC, ITEM_SEQ 등) → 한글 라벨로 교체 또는 accordion
- "api:" 키로 렌더링되는 모든 출처 표시
- placeholder "—" → 데이터 없으면 섹션 자체 숨김 ({% if value and value != "—" %})
- 빈 날짜 필드 → "날짜 미확인" 표시
- event_kinds raw key 노출 (예: "recall · disciplinary") → 한글 라벨 변환
```

**검증 명령:**
```bash
grep -r "API [0-9]" templates/    # 0건
grep -r "domain_kr" templates/    # 0건
grep -r '"—"' templates/          # 0건
```

### 3.2 공통 심각도(Severity) 체계

신규 `blueprints/severity.py` 파일 생성:

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

### 3.3 _normalize_event() 확장 (공통 출력 스키마)

`blueprints/app_views.py` 및 `blueprints/watchlist_match.py` 양쪽 normalize 함수를 아래 스키마로 통일:

```python
# 모든 _normalize_event()의 반환값 스키마
{
    "type":           str,   # 내부 키 (recall, disciplinary 등)
    "type_label":     str,   # 화면 표시 한글 (SEVERITY_MAP의 label)
    "severity_level": str,   # CRITICAL / HIGH / LOW / NONE
    "severity_color": str,   # danger / warn / success / info / muted
    "title":          str,   # 품목명 중심 제목 (60자 truncate)
    "entity":         str,   # 업체명
    "summary":        str,   # 사유/내용 요약 (100자 truncate)
    "date":           str,   # "YYYY-MM-DD" 또는 "" (빈값 → 템플릿에서 "날짜 미확인")
    "is_new":         bool,  # 오늘 날짜 여부
    "product_code":   str,   # ITEM_SEQ (있으면 Product 360 링크 활성화)
    "in_watchlist":   bool,  # 워치리스트 매칭 여부 (배지 표시용)
    # 제거: "api", "url", "domain", "domain_kr"
}
```

### 3.4 공통 이벤트 카드 매크로 (templates/_macros.html 신규)

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

### 3.5 위험도 신호등 헬퍼 (blueprints/risk.py 신규)

```python
# blueprints/risk.py

def calc_risk_signal(approval_data, disciplinary_items, recall_items,
                     review_due_days=None):
    """
    반환값:
    {
      "level":   "CRITICAL" | "HIGH" | "LOW" | "NONE",
      "color":   "danger" | "warn" | "success" | "muted",
      "label":   "위험" | "주의" | "정상" | "정보없음",
      "reasons": ["회수이력 1건", "재심사 D-45일"]
    }
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

    return {
        "level":   level,
        "color":   color_map[level],
        "label":   label_map[level],
        "reasons": reasons,
    }
```

---

## 4. 네비게이션 구조 재편

### 4.1 현재 vs 리뉴얼 사이드바

```
현재 (5개, 기능 중심):           리뉴얼 (7개, 업무 맥락 중심):
────────────────────             ──────────────────────────────
🔍 통합 검색           →        🏠 오늘의 브리핑      [신규 /app/home]
📅 이벤트 타임라인     →        🔍 제품·업체 조회     [명칭 변경 /]
👁 워치리스트          →        🚨 이벤트 모니터      [확장 /app/monitor]
📊 리포트              →        👁 내 워치리스트      [기능 강화 /app/watchlist]
🤖 AI 코파일럿         →        🏢 워크스페이스       [/app/workspace]
                                 🔬 검사부적합         [/app/inspections]
                                 🤖 AI 코파일럿        [/app/copilot]
                                 📊 리포트·내보내기    [disabled, Phase 2]
```

### 4.2 nav_config.py 전체 교체 명세

```python
# blueprints/nav_config.py

NAV_ITEMS = [
    {
        "key": "home",
        "label": "오늘의 브리핑",
        "href": "/app/home",
        "icon_svg": '<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>',
        "badge": None, "disabled": False,
    },
    {
        "key": "search",
        "label": "제품·업체 조회",
        "href": "/",
        "icon_svg": '<path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>',
        "badge": None, "disabled": False,
    },
    {
        "key": "monitor",
        "label": "이벤트 모니터",
        "href": "/app/monitor",
        "icon_svg": '<path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>',
        "badge": None,  # inject_nav()에서 오늘 CRITICAL 건수 동적 주입
        "disabled": False,
    },
    {
        "key": "watchlist",
        "label": "내 워치리스트",
        "href": "/app/watchlist",
        "icon_svg": '<path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>',
        "badge": None,  # inject_nav()에서 동적 주입
        "disabled": False,
    },
    {
        "key": "workspace",
        "label": "워크스페이스",
        "href": "/app/workspace",
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
        "key": "inspections",
        "label": "검사부적합",
        "href": "/app/inspections",
        "icon_svg": '<path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>',
        "badge": None, "disabled": False,
    },
    {
        "key": "copilot",
        "label": "AI 코파일럿",
        "href": "/app/copilot",
        "icon_svg": '<path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>',
        "badge": {"kind": "brand", "text": "NEW"}, "disabled": False,
    },
    {
        "key": "reports",
        "label": "리포트·내보내기",
        "href": "/app/reports",
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

> **검증일**: 2026-05-27 | **검증 범위**: 44개 오퍼레이션 | **결과**: 완전 작동 32 + 부분 12 + 실패 0

### 5.1 파라미터 케이스 규칙 — API별 혼재 (반드시 준수)

```
snake_case (소문자):    item_name, entp_name, bizrno, edi_code
  적용 API: NO 140(허가), 563(낱알식별), 564(처분), 145(의약외품), 153(수입식품회수)

camelCase:              itemName, entpName, itemSeq
  적용 API: NO 248(e약은요), 531(DUR 품목), 269(묶음의약품)

UPPER_CASE:             TITLE, BSSH_NM, FOOD_NM_KR, PRCSCITYPOINT_BSSHNM
  적용 API: NO 547(안전성서한), 132(GMP), 1(식품영양DB), 3·5·6(식품행정처분)

⚠️ 특수 케이스:
  NO 140: item_seq 파라미터 무시됨 → edi_code로 검색 (핵심 발견)
  NO 132: BSSH_NM="광동제약" → 1건 정확 조회 확인
```

### 5.2 서버사이드 검색 불가 API — 클라이언트 필터링 필수

아래 12개 API는 검색 파라미터를 보내도 **전체 데이터를 반환**한다. `_filter_items()` 헬퍼로 메모리 필터링 적용.

| NO | 서비스 | 전체 건수 | 주의사항 |
|----|--------|-----------|----------|
| 539 | 회수·판매중지 | 950건 | - |
| 534 | 공급중단 | 1,285건 | - |
| 537 | 공급부족 | 733건 | - |
| **561** | **의약품 특허** | **120,525건** | ⚠️ 대용량 — num_of_rows=50 제한 |
| **554** | **재심사** | **112,554건** | ⚠️ 대용량 — num_of_rows=50 제한 |
| **556** | **재평가** | **64,827건** | ⚠️ 대용량 — num_of_rows=50 제한 |
| 566 | 임상시험 | 13,903건 | - |
| 142 | 국가출하승인 | 33,550건 | - |
| 483 | DMF | 8,916건 | - |
| 484 | 대조약 | 3,305건 | - |
| 485 | 생동성 | 12,065건 | - |
| 568 | 임상기관 | 232건 | - |

> 대용량 3개(특허·재심사·재평가)는 `num_of_rows=50`으로 고정 후 메모리 필터. 워크스페이스 KPI 용도로만 사용 시 `num_of_rows=5` 가능.

### 5.3 실제 검증된 응답 필드명 — 기존 코드 대비 수정 필요

| NO | API | ❌ 기존 가정 필드 | ✅ 실제 검증 필드 |
|----|-----|----------------|----------------|
| 140 | 허가 주성분 | ITEM_NAME, ENTP_NAME | **ENTRPS, PRDUCT, MTRAL_NM, MTRAL_CODE** |
| 547 | 안전성서한 | title, content | **TITLE, SUMRY_CONT, PBANC_CONT, PBANC_YMD, SAFT_LETT_NO** |
| 565 | 희귀의약품 | PRDUCT_NAME | **PRODT_NAME, TARGET_DISEASE, RARITY_DRUG_APPOINT_NO, APPOINT_DATE** |
| 535 | 검사부적합 | PRODUCT | **PRDUCT, IMPROPT_ITM, REGIST_DT, FOOD_TY** |
| 12 | 스마트HACCP | BSSH_NM | **businessnm, company, appointno, sido, ceoname** |
| 1 | 식품영양DB | FOOD_NAME | **FOOD_NM_KR, DB_GRP_NM, DB_CLASS_NM, FOOD_CD** |
| 81 | 희귀필수 | 대부분 | **INGR, MEDCIN_NAME** (데이터 24건만 존재) |
| 132 | GMP | BSSH_NM (O) | BSSH_NM, FCTR_ADDR, KGMP_BGMP_NAME, GMP_INGR_MM_GROUP_NAME, VLD_PRD_YMD ✅ |

### 5.4 광동제약 자사 데이터 검증 결과

```python
# NO 132 GMP 검증 결과 (BSSH_NM="광동제약")
{
    "BSSH_NM": "광동제약(주)",
    "FCTR_ADDR": "경기도 평택시 산단로 114",
    "KGMP_BGMP_NAME": "완제의약품",
    "GMP_INGR_MM_GROUP_NAME": "내용고형제(정제, 캡슐제, 과립제, 환제), 내용액제",
    "VLD_PRD_YMD": "2027-03-28",   # ← RA팀 핵심 정보
    "BIZRNO": "1138108888"
}

# NO 564 행정처분: 광동제약 0건 → 처분 이력 없음 (정상)
# NO 539 회수판매중지: 베니톨정 0건 → 안전 (정상)
# NO 531 DUR 병용금기: 타이레놀 0건 → 일반의약품이라 미등록 (정상)
```

### 5.5 데이터 0건 = 정상 케이스 — 에러 처리 주의

```python
# 아래는 API 오류가 아닌 "데이터 없음"이므로 정상 처리
# 화면: "해당 데이터 없음" 표시 (에러 메시지 X)

NORMAL_EMPTY_CASES = {
    "NO 269 묶음의약품":    "HIRA 처방의약품 위주, 일반의약품 미등록",
    "NO 531 DUR 병용금기":  "일반의약품은 병용금기 미등록",
    "NO 81 자가치료용마약": "카테고리 전체 0건 (데이터 자체 희소)",
    "NO 564 행정처분 광동": "광동제약 처분 이력 없음 (정상)",
}
```

### 5.6 api_extras.py 수정 사항 요약

```python
# 이미 수정 완료된 항목 (Phase 4에서 처리)
# NO 547: title → TITLE (대문자)
# NO 132: bssh_nm → BSSH_NM

# 추가 수정 필요
# NO 140 주성분: ITEM_NAME → ENTRPS, PRDUCT, MTRAL_NM
# NO 565 희귀의약품: PRDUCT_NAME → PRODT_NAME
# NO 12 HACCP: BSSH_NM → company, businessnm

# 필터링 전략 (클라이언트 필터링 API)
def _filter_items(items, query, fields):
    """대소문자 무관 포함 검색 — 서버사이드 미지원 API 공통 사용"""
    q = query.lower()
    return [it for it in items
            if any(q in str(it.get(f, "")).lower() for f in fields)]
```

---

## 6. 페이지별 상세 명세

---

### P1. 홈 대시보드 (신규) — `/app/home`

**신설 목적**: 시스템 진입 시 "지금 당장 봐야 할 것"을 즉시 브리핑. 기존 통합 검색(`/`)이 "검색하러 오는 곳"이라면, 홈은 "모닝 브리핑 페이지"다.

#### 정보 구성 요소 (위→아래)

```
[영역 A] CRITICAL 긴급 알림 배너
  표시 조건: CRITICAL 이벤트 1건 이상일 때만
  내용: "🔴 오늘 회수명령 N건 · 판매중지 M건 신규 발생"
  클릭: /app/monitor?severity=CRITICAL

[영역 B] 워치리스트 요약 패널 (등록 품목 있을 때)
  🔴 위험 N개 | 🟡 주의 M개 | 🟢 이상없음 K개
  [내 워치리스트 →]

[영역 C] 오늘의 주요 이벤트 TOP 5 (severity 높은 순)
  → event_card 매크로 재사용
  [전체 이벤트 보기 →] /app/monitor

[영역 D] 30일 이내 마감 일정
  재심사 D-Day 최대 3건 (데이터 없으면 영역 자체 숨김)

[영역 E] 빠른 검색 진입
  검색창 1개 → 제출 시 /?q= redirect
```

#### 백엔드 라우트

```python
@app_bp.route("/home")
def home():
    from ..api_extras import fetch_drug_recall, fetch_drug_disciplinary
    from ..blueprints import watchlist_store, watchlist_match

    # 오늘 CRITICAL 이벤트 수집
    critical_events = []
    for fetch_fn, etype in [
        (fetch_drug_recall, "recall"),
        (fetch_drug_disciplinary, "disciplinary"),
    ]:
        try:
            items = fetch_fn(num_of_rows=5).get("items", [])
            for it in items[:3]:
                ev = _normalize_event(etype, it)
                critical_events.append(ev)
        except Exception:
            pass

    from .severity import SEVERITY_ORDER
    critical_events.sort(key=lambda e: SEVERITY_ORDER.get(e.get("severity_level", "LOW"), 3))
    critical_events = critical_events[:5]

    # 워치리스트 요약
    wl_summary = {"critical": 0, "high": 0, "ok": 0, "total": 0}
    try:
        if watchlist_store.count() > 0:
            entries = watchlist_store.list_entries()
            match_map = watchlist_match.match_for_entries(entries)
            wl_summary = watchlist_match.summarize_by_severity(match_map)
    except Exception:
        pass

    # 재심사 D-30 이내 마감
    upcoming_deadlines = []
    try:
        from ..api_extras import fetch_drug_review
        items = fetch_drug_review(num_of_rows=50).get("items", [])
        for it in items:
            d = _parse_deadline(it)
            if d and d <= 30:
                upcoming_deadlines.append({
                    "item_name": it.get("ITEM_NAME", ""),
                    "deadline_days": d,
                    "type": "재심사",
                })
        upcoming_deadlines = sorted(upcoming_deadlines, key=lambda x: x["deadline_days"])[:3]
    except Exception:
        pass

    return render_template("app/home.html",
                           active_page="home",
                           critical_events=critical_events,
                           wl_summary=wl_summary,
                           upcoming_deadlines=upcoming_deadlines)
```

---

### P2. 통합 검색 — `/`

#### 제거할 정보

```
❌ KPI 전체 모수 숫자 ("허가건수 25,354건" 등)
❌ 카테고리 칩 10개 병렬 나열 → 빠른 검색 칩 3개로 교체
❌ API 번호 카드 노출
❌ 검색 결과와 전체 이벤트 혼재
```

#### 추가할 정보

```
✅ 검색 이력 드롭다운 (localStorage JS, 최근 5건)
✅ 빠른 검색 칩: [광동제약] [아세트아미노펜] [최근 회수품목]
✅ 종합 위험 신호등 카드 (검색 후 상단)
✅ 탭 순서 재배열: [허가 정보] → [규제 이력] → [낱알 식별]
✅ 광동 관련 배지 (워치리스트 매칭 품목)
```

#### 허가 정보 탭 — 표시/제거 필드

```python
# 표시 (한글 라벨 매핑)
DISPLAY_FIELDS = {
    "ITEM_NAME":        "품목명",
    "ENTP_NAME":        "업체명",
    "ITEM_PERMIT_DATE": "허가일자",    # 포맷: YYYYMMDD → YYYY년 MM월 DD일
    "ETC_OTC_CODE":     "전문/일반",   # "전문의약품" / "일반의약품"
    "MATERIAL_NAME":    "주성분",
    "EDI_CODE":         "보험코드",    # 있을 때만
    "VALID_TERM":       "유효기간",    # 있을 때만
}

# 제거 (accordion 또는 완전 삭제)
HIDDEN_FIELDS = ["ITEM_SEQ", "ENTP_SEQ", "ENTP_NO", "BIZRNO"]

# accordion (접어두기)
ACCORDION_FIELDS = ["BIZRNO", "ENTP_NO", "ITEM_SEQ"]
```

#### 백엔드 수정

```python
@app_bp.route("/")
def search():
    q = (request.args.get("q") or "").strip()
    results = {"approval": [], "disciplinary": [], "recall": [],
               "identification": [], "risk_signal": None}

    if q:
        # 기존 API 호출 유지
        # ...

        # 신규: 위험도 신호등
        from ..blueprints.risk import calc_risk_signal
        results["risk_signal"] = calc_risk_signal(
            approval_data=results["approval"],
            disciplinary_items=results["disciplinary"],
            recall_items=results["recall"],
        )

    return render_template("app/search.html",
                           active_page="search",
                           query=q,
                           results=results)
```

---

### P3. 이벤트 모니터 — `/app/monitor`

> **기존 `/app/timeline` → `/app/monitor` 확장 재설계**. 기존 라우트는 301 redirect.

#### 제거할 정보

```
❌ API 번호 카드 노출 → 전면 삭제
❌ domain_kr 중복 태그
❌ 동등 나열 (긴급=정보)
❌ 빈 날짜 렌더링
```

#### 추가할 정보

```
✅ 상단 현황 배너: 오늘 N건 / 이번 주 M건 / 광동 관련 K건
✅ 필터 바: 기간(오늘/이번주/이번달/직접입력) + 심각도 + 이벤트 유형 + Excel 내보내기
✅ 심각도 기반 정렬: CRITICAL → HIGH → LOW
✅ NEW 배지 (오늘 날짜 이벤트)
✅ 워치리스트 매칭 배지 (📌 워치리스트)
✅ 동일 품목 이벤트 그룹화 (2건↑ 시 그룹 카드)
```

#### 백엔드 라우트

```python
@app_bp.route("/monitor")
def monitor():
    severity_filter = request.args.get("severity", "ALL")
    type_filter = request.args.get("type", "ALL")
    period = request.args.get("period", "week")

    all_events = _collect_all_events()  # 기존 함수 재사용

    # 심각도 정렬
    from .severity import SEVERITY_ORDER
    all_events.sort(key=lambda e: SEVERITY_ORDER.get(e.get("severity_level", "LOW"), 3))

    # 워치리스트 매칭 표시
    try:
        wl_names = {e["name"].lower() for e in watchlist_store.list_entries()}
        for ev in all_events:
            ev["in_watchlist"] = any(n in (ev.get("title") or "").lower() for n in wl_names)
    except Exception:
        pass

    # 필터 적용
    if severity_filter != "ALL":
        all_events = [e for e in all_events if e.get("severity_level") == severity_filter]
    if type_filter != "ALL":
        all_events = [e for e in all_events if e.get("type") == type_filter]

    from collections import Counter
    type_counts = Counter(e.get("type", "unknown") for e in all_events)
    today_count = sum(1 for e in all_events if e.get("is_new"))
    kwangdong_count = sum(1 for e in all_events if e.get("in_watchlist"))

    return render_template("app/monitor.html",
                           active_page="monitor",
                           events=all_events,
                           type_counts=dict(type_counts),
                           today_count=today_count,
                           kwangdong_count=kwangdong_count,
                           severity_filter=severity_filter,
                           type_filter=type_filter)

# 기존 timeline → redirect
@app_bp.route("/timeline")
def timeline():
    return redirect(url_for("app_bp.monitor"), 301)
```

---

### P4. 워치리스트 — `/app/watchlist`

#### 제거할 정보

```
❌ 단순 등록일 표시 → "마지막 이벤트 발생일"로 교체
❌ 카운트 숫자만 표시 → 인라인 미리보기 추가
❌ 등록 순서 정렬 → 위험도 정렬로 변경
```

#### 추가할 정보

```
✅ 상단 요약: 🔴 N개 / 🟡 M개 / 🟢 K개
✅ [+ 품목 추가] [📎 Excel 일괄 업로드] [📥 전체 내보내기]
✅ 위험도 정렬 (CRITICAL → HIGH → LOW → NONE)
✅ 이벤트 인라인 미리보기 (<details><summary> HTML 기본 요소)
✅ 사용자 태그 (QC관리·원료·완제품 등)
✅ 워치리스트 카운트 8종 (회수·안전성·처분·공급·특허·임상·재심사·재평가)
```

#### watchlist_match.py 신규 함수

```python
def summarize_by_severity(match_map: dict) -> dict:
    """match_map → {critical, high, ok, total}"""
    result = {"critical": 0, "high": 0, "ok": 0, "total": len(match_map)}
    for entry_name, counts in match_map.items():
        total = sum(counts.values())
        if counts.get("recalls", 0) > 0 or counts.get("supply_stop", 0) > 0:
            result["critical"] += 1
        elif total > 0:
            result["high"] += 1
        else:
            result["ok"] += 1
    return result

def critical_alert_count(match_map: dict) -> int:
    return sum(1 for c in match_map.values()
               if c.get("recalls", 0) > 0 or c.get("supply_stop", 0) > 0)

def today_critical_count() -> int:
    """오늘 신규 CRITICAL 이벤트 건수 (5분 캐시)"""
    # recall + supply_stop 중 오늘 날짜인 것
    pass  # 구현 필요
```

---

### P5. 제품 상세 (의약품) — `/app/product/<code>`

#### 제거할 정보

```
❌ 낱알 이미지 상단 주요 위치 → 마지막 탭으로 이동
❌ 허가 원문 코드 노출 (SPCLTY_PBLC 등) → 한글 라벨
❌ 업체 행정 정보 전면 노출 → accordion 처리
```

#### 추가할 정보

```
✅ 헤더: 종합 위험 신호등 + reasons 목록
✅ 헤더: 재심사 D-Day (데이터 있을 때만)
✅ 헤더: [📌 워치리스트 추가] [📥 정보 내보내기]
✅ 탭 순서: [핵심정보] → [규제이력] → [안전성] → [관련품목] → [제품외형]
✅ 규제이력 탭: 가로 스크롤 타임라인 (허가→재심사→처분→재심사예정)
✅ 안전성 탭: DUR 정보 (병용금기·임부금기·노인주의 — NO 531·533)
✅ 관련품목 탭: 동일 성분(MAIN_ITEM_INGR) 유사 품목 최대 8건
✅ GMP 적합판정 상태 (NO 132 — 제조사 기준 조회)
```

#### 탭 구성 상세

```
[핵심정보 탭]
  표시: 품목명, 업체명, 허가일, 전문/일반, 주성분, 보험코드(있을때), 유효기간(있을때)
  accordion: 사업자번호, 업체허가번호, 품목기준코드

[규제이력 탭] ← 신규 핵심 섹션
  상단: 규제 타임라인 가로 스크롤
  목록: 행정처분 (처분명·처분일·사유) + 회수·판매중지 (회수명·회수일·사유·조치기한)
  RA 정보: 재심사 만료일 / D-Day / 재심사 결과

[안전성 탭]
  DUR 품목 병용금기 (NO 531)
  DUR 품목 임부금기 (NO 531)
  DUR 품목 노인주의 (NO 531)
  안전성서한 (NO 547)
  ※ 각 항목 0건이면 "해당 데이터 없음" 표시

[관련품목 탭] ← 신규
  동일 성분 유사 품목 최대 8건
  컬럼: 품목명 · 업체명 · 허가일 · 위험도 신호등
  클릭 → 해당 제품 상세 이동

[제품외형 탭] (기존 낱알식별)
  이미지 (없으면 "이미지 없음")
  모양 · 색상 · 각인 앞면·뒷면 · 크기
```

#### 백엔드 수정 핵심

```python
@app_bp.route("/product/<code>")
def product_drug(code):
    # 기존 fetch 유지

    # 신규: 위험도 신호등
    from ..blueprints.risk import calc_risk_signal
    risk_signal = calc_risk_signal(
        approval_data=[approval] if approval else [],
        disciplinary_items=disciplinary_items,
        recall_items=recall_items,
        review_due_days=_get_review_due_days(approval),
    )

    # 신규: 동일 성분 유사 품목
    similar_items = []
    if approval and approval.get("MATERIAL_NAME"):  # 검증된 필드명 사용
        try:
            # MAIN_ITEM_INGR 파라미터로 재검색
            similar_resp = fetch_drug_approval(
                item_ingr_name=_extract_ingr(approval["MATERIAL_NAME"]),
                num_of_rows=10
            )
            similar_items = [
                i for i in (similar_resp.get("items") or [])
                if i.get("ITEM_NAME") != approval.get("ITEM_NAME")
            ][:8]
        except Exception:
            pass

    # 신규: DUR 정보 (NO 531)
    dur_info = {"contraindication": [], "pregnancy": [], "elderly": []}
    try:
        from ..api_extras import fetch_dur_item
        if approval:
            dur_items = fetch_dur_item(itemName=approval.get("ITEM_NAME", ""),
                                       num_of_rows=20).get("items", [])
            for d in dur_items:
                t = d.get("TYPE_NAME", "")
                if "병용금기" in t:    dur_info["contraindication"].append(d)
                elif "임부금기" in t:  dur_info["pregnancy"].append(d)
                elif "노인주의" in t:  dur_info["elderly"].append(d)
    except Exception:
        pass

    return render_template("app/product_drug.html",
                           active_page="search",
                           approval=approval,
                           disciplinary_items=disciplinary_items,
                           recall_items=recall_items,
                           identification=identification,
                           risk_signal=risk_signal,
                           similar_items=similar_items,
                           dur_info=dur_info)
```

---

### P6. 제품 상세 (의약외품) — `/app/product-quasi/<code>` [신규]

> 사용자 추가 요구. `product_drug.html` 구조 복제 후 의약외품 특화 수정.

#### 정보 구성

```
[헤더]
  품목명 + 업체명 + 허가일 (NO 145 — item_name, entp_name 파라미터)
  위험도 신호등 (처분 이력 기반)

[탭 구성 — 5개]
  [핵심정보]   허가정보 (NO 145)
  [규제이력]   행정처분 (NO 564) + 회수 (NO 539 의약품외 회수)
  [안전성]     안전성서한 (NO 547)
  [품질이벤트] 검사부적합 (NO 535, 해당 업체 필터)
  [공급망]     공급중단 (NO 534)

  제거 탭: R&D(특허·임상·재심사), 낱알식별
```

#### 신규 파일 목록

| 파일 | 작업 |
|------|------|
| `api_extras.py` | `fetch_quasi_approval(item_name, entp_name)` 신설 (NO 145 엔드포인트) |
| `templates/app/product_quasi.html` | 신규 생성 |
| `blueprints/app_views.py` | `/app/product-quasi/<code>` 라우트 신설 |

---

### P7. 워크스페이스 (부서별) — `/app/workspace/<dept>`

#### 공통 수정사항

```
❌ placeholder "—" 6개 전면 제거 (Phase 4에서 완료 예정)
❌ KPI 숫자만, 액션 없음 → 각 KPI에 [바로가기] 링크 추가
```

#### RA 워크스페이스 — D-Day 캘린더 재설계

```python
# workspaces_config.py RA 섹션 변경
RA_WORKSPACE = {
    "key": "ra",
    "label": "RA (허가·인허가)",
    "sections": [
        {
            "type": "deadline_calendar",
            "title": "D-90 이내 마감",
            "api_fn": "fetch_drug_review",   # NO 554
            "deadline_field": "REEXAM_CODE_NM",
            "window_days": 90,
        },
        {
            "type": "kpi_row",
            "kpis": [
                {"label": "재심사 진행", "api": "fetch_drug_review",  "color": "warn"},
                {"label": "재평가 진행", "api": "fetch_drug_reeval",  "color": "info"},
                {"label": "신규허가(월)", "api": "fetch_drug_permit", "color": "success"},
            ],
        },
    ],
}
```

**화면 구성:**

```
┌──────────┬──────────┬──────────┐
│ D-12     │ D-28     │ D-45     │
│ 품목A    │ 품목B    │ 품목C    │
│ 재심사   │ 재심사   │ 재평가   │
│[상세 →]  │[상세 →]  │[상세 →]  │
└──────────┴──────────┴──────────┘
GMP 만료: 광동제약(주) 2027-03-28  ← NO 132 실 데이터
```

#### SCM 워크스페이스 신규 섹션

```
공급부족 품목 테이블 (NO 537):
  컬럼: 품목명 | 부족 사유 | 공급재개 예정일 | 워치리스트 여부

공급중단 현황 (NO 534):
  최근 30일 목록 + [이벤트 모니터 →] 링크
```

#### R&D 워크스페이스 실 데이터 연결

```
임상시험 신규 N건 (NO 566) — 수정된 필드명 사용:
  APPLY_ENTP_NAME, GOODS_NAME, CLINIC_EXAM_TITLE, CLINIC_STEP_NAME

특허 신규 N건 (NO 561) — 클라이언트 필터 num_of_rows=50:
  INGR_ENG_NAME, ITEM_NAME, ENTP_NAME, CLASS_NO

생동성 N건 (NO 485):
  ITEM_NAME, ENTP_NAME, BIOEQ_NOTICE_DATE
```

---

### P8. 검사부적합 트래커 — `/app/inspections`

#### 정보 구성 (KPI 우선순위 재배열)

```
[1순위 KPI — 2칸 배치, 가장 크게]
  🔴 광동 관련 부적합: N건  [워치리스트 매칭 상세 →]
  🟡 최근 30일 신규: M건   [전체 목록 →]

[2순위 KPI — 4칸 배치]
  잔류농약 N건 | 중금속 M건 | 미생물 K건 | 이물·기타 P건

[필터 바]
  기본값: 최근 30일 전체 표시 (빈 화면 방지)
  기간: [최근 30일 ▼] / [최근 90일] / [직접 입력]
  부적합 사유: [전체 ▼] / [잔류농약] / [중금속] / [미생물] / [이물]
  검색: 제품명 또는 제조소명
  [Excel 내보내기]

[부적합 사유 분류 차트]
  CSS 가로 바 차트 (JavaScript 없이 순수 CSS width 계산)

[제조소 위험 순위 TOP 5]
  컬럼: 제조소명 | 부적합 건수 | 최근 부적합일
  5건↑ 시 🔴 배지

[부적합 목록]
  광동 매칭 → 빨간 테두리 + 상단 고정
  컬럼: 제품명(PRDUCT) · 업체(ENTRPS) · 부적합 사유(IMPROPT_ITM) · 검사일(REGIST_DT)
```

#### 백엔드 라우트 (검증된 필드명 적용)

```python
@app_bp.route("/inspections")
def inspections():
    from ..api_extras import fetch_food_inspect
    from collections import Counter

    q = (request.args.get("q") or "").strip()
    all_items = fetch_food_inspect(num_of_rows=100).get("items", [])

    # 검증된 필드명: PRDUCT, ENTRPS, IMPROPT_ITM, FOOD_TY, REGIST_DT
    def classify_reason(text):
        if not text: return "이물·기타"
        r = text.lower()
        if "농약" in r or "잔류" in r: return "잔류농약"
        if "중금속" in r or "납" in r: return "중금속"
        if "세균" in r or "대장균" in r: return "미생물"
        return "이물·기타"

    reason_counts = Counter(classify_reason(it.get("IMPROPT_ITM", "")) for it in all_items)
    factory_counts = Counter(it.get("ENTRPS", "미상") for it in all_items)
    factory_rank = [{"name": k, "count": v} for k, v in factory_counts.most_common(5)]

    # 광동 관련 (워치리스트 매칭)
    kwangdong_items = []
    try:
        wl_names = {e["name"].lower() for e in watchlist_store.list_entries()}
        kwangdong_items = [
            it for it in all_items
            if any(n in (it.get("PRDUCT") or "").lower() for n in wl_names)
        ]
    except Exception:
        pass

    if q:
        all_items = _filter_items(all_items, q, ["PRDUCT", "ENTRPS", "IMPROPT_ITM"])

    sorted_items = kwangdong_items + [i for i in all_items if i not in kwangdong_items]

    return render_template("app/inspections.html",
                           active_page="inspections",
                           query=q,
                           items=sorted_items[:30],
                           kwangdong_count=len(kwangdong_items),
                           total_count=len(all_items),
                           reason_counts=dict(reason_counts),
                           factory_rank=factory_rank)
```

---

### P9. AI 코파일럿 — `/app/copilot`

#### 추가할 정보

```
[맥락 브리핑 패널 — 자동 주입]
  오늘 시스템 현황 (시스템 프롬프트 자동 포함):
    · 워치리스트 이벤트 N건
    · 이번 주 회수명령 M건
    · 재심사 D-30 이내 K건

[빠른 질문 템플릿]
  GMP/규제: [이번 주 회수 품목 부적합 사유 요약] [GMP 실사 체크리스트] [재심사 서류 가이드]
  경쟁사: [신규 허가 경쟁 품목] [아세트아미노펜 시장 현황]
  공급망: [공급부족 품목 대체재 분석]

[대화 결과]
  [복사] 버튼 추가
```

#### 시스템 프롬프트 자동 구성

```python
@app_bp.route("/copilot")
def copilot():
    context_summary = ""
    try:
        wl_count = watchlist_store.count()
        critical = watchlist_match.critical_alert_count(
            watchlist_match.match_for_entries(watchlist_store.list_entries())
        ) if wl_count > 0 else 0
        context_summary = f"""
현재 KD-IRIS 시스템 현황:
- 워치리스트 등록 품목: {wl_count}개 (이벤트 있음: {critical}개)
- 오늘 신규 CRITICAL 이벤트: {watchlist_match.today_critical_count()}건
- 광동제약 GMP 만료: 2027-03-28 (평택공장)
"""
    except Exception:
        pass

    return render_template("app/copilot.html",
                           active_page="copilot",
                           context_summary=context_summary)
```

---

### P10. 리포트 — `/app/reports` (Phase 2)

현재 `disabled: True`. 설계만 확정.

```
리포트 유형 (향후 구현):
  A. 경영진 요약 (1페이지) — 이번 달 이슈 Top 5 + 광동 관련 + 마감 일정
  B. QMR 보고용 데이터 시트 — 회수·처분 월별 건수
  C. GMP 실사 대비 리포트 — 자사 3년 이력 + 업계 비교

현재 화면: "준비 중" 표시 (기존 placeholder 유지)
```

---

## 7. 신규 API 22개 연동 계획

> 2026-05-27 신규 신청·승인된 API. 기존 시스템에 미연동 상태.

### 7.1 DUR 안전성 정보 (의약품 상세 안전성 탭 강화)

| NO | 서비스명 | 엔드포인트 | 활용 위치 |
|----|---------|-----------|----------|
| N-1 | **DUR 성분정보 (7기능)** | `DURIrdntInfoService03` | P5 안전성 탭 |
| N-2 | **DUR 품목정보 (9기능)** | `DURPrdlstInfoService03` | P5 안전성 탭 |

```python
# api_extras.py 신규 함수 (N-1, N-2)
# 파라미터: INGR_NAME (성분정보), itemName (품목정보) — camelCase 주의

def fetch_dur_ingredient_contraindication(ingr_name=None, num_of_rows=20):
    """DUR 성분 병용금기 (NO 533)"""
    # 엔드포인트: DURIrdntInfoService03/getUsjntTabooInfoList02
    pass

def fetch_dur_item_pregnancy(item_name=None, num_of_rows=20):
    """DUR 품목 임부금기 (NO 531 — itemName camelCase)"""
    # 엔드포인트: DURPrdlstInfoService03/getPwnmTabooInfoList03
    pass

def fetch_dur_item_elderly(item_name=None, num_of_rows=20):
    """DUR 품목 노인주의 (NO 531)"""
    pass

# 응답 필드 (검증됨): TYPE_NAME, MIX_TYPE, INGR_CODE, INGR_ENG_NAME, ITEM_SEQ, ITEM_NAME
```

### 7.2 GMP·출하·업체 정보 (QA/QC팀 핵심)

| NO | 서비스명 | 엔드포인트 | 활용 위치 | 검증 상태 |
|----|---------|-----------|----------|-----------|
| N-9 | **GMP 적합판정서** | `DrugGmpStbltJgmtIssuStusService` | P5 규제이력 탭 | ✅ 완전 작동 (광동 1건 확인) |
| N-10 | **국가출하승인** | `DrugNatnShipmntAprvInfoService` | P5 규제이력 탭 | ✅ 33,550건 |
| N-11 | **업체허가현황** | `DrugEtcBsshBspmStusService` | 업체 상세 | ✅ 2,959건 |
| N-12 | **원료의약품 DMF** | `MdcDmfInfoService01` | SCM 워크스페이스 | ✅ 8,916건 |

```python
# api_extras.py 신규 함수

def fetch_drug_gmp(bssh_nm=None, num_of_rows=20):
    """GMP 적합판정서 (NO 132 — BSSH_NM UPPER_CASE 파라미터)
    검증 필드: BSSH_NM, FCTR_ADDR, KGMP_BGMP_NAME, GMP_INGR_MM_GROUP_NAME, VLD_PRD_YMD
    """
    pass  # 이미 구현됨, 필드 매핑 확인 필요

def fetch_national_release(goods_name=None, num_of_rows=20):
    """국가출하승인 (NO 142 — 클라이언트 필터)
    검증 필드: MANUF_ENTP_NAME, MAKE_NO, RESULT_TIME, PROVT_UNIT, VALID_TERM
    """
    pass

def fetch_drug_dmf(num_of_rows=20):
    """원료의약품 DMF (NO 483 — 클라이언트 필터)
    검증 필드: DMF_PERMIT_NO, INGR_KOR_NAME, ENTP_NAME, MNFCTR_NAME, MANUF_COUNTRY_CODE_NM
    """
    pass
```

### 7.3 R&D 특허·임상 정보 (R&D 워크스페이스 강화)

| NO | 서비스명 | 엔드포인트 | 활용 위치 | 건수 |
|----|---------|-----------|----------|------|
| N-5 | **FDA 오렌지북 특허** | `FdaOrngbkPatentInfoService01` | R&D 워크스페이스 | 5,771건 |
| N-6 | **FDA Paragraph IV** | `ParagraphIVTrgetMdcinService02` | R&D 워크스페이스 | 1,568건 |
| N-7 | **국내소송 의약품** | `DmstcLwstMdcinInfoService02` | R&D 워크스페이스 | 10,568건 |
| N-8 | **대조약 정보** | `MdcCompDrugInfoService04` | R&D 워크스페이스 | 3,305건 ✅ |
| N-15 | **임상시험 실시기관** | `ClinicTestOprtnInsttInfoService01` | R&D 워크스페이스 | 232건 ✅ |

```python
# R&D 워크스페이스 특허 분쟁 트래커 섹션 구성
"""
[특허 분쟁 현황 — 3개 API 통합]
  국내 특허 소송 (NO 557): INGR_NAME, JUDGMENT_KIND, KOR_PAT_NO, SIGN_OF_CASE
  FDA 오렌지북 (NO 562): INGR_NAME, PRT_NAME, KOR_PAT_NO, KOR_STATUS, KOR_EXP_DATE
  FDA Paragraph IV (NO 552): DRUG_NAME, DOSAGE_FORM, STRENGTH, RLD
"""

def fetch_fda_orangebook(num_of_rows=20):
    """검증 필드: INGR_NAME, PRT_NAME, KOR_PAT_NO, KOR_STATUS, KOR_EXP_DATE"""
    pass

def fetch_fda_paragraph4(num_of_rows=20):
    """검증 필드: DRUG_NAME, DOSAGE_FORM, STRENGTH, RLD"""
    pass

def fetch_drug_lawsuit(num_of_rows=20):
    """검증 필드: INGR_NAME, PRT_NAME, JUDGMENT_KIND, KOR_PAT_NO, SIGN_OF_CASE"""
    pass
```

### 7.4 소비자 정보 (제품 상세 보강)

| NO | 서비스명 | 엔드포인트 | 활용 위치 | 건수 |
|----|---------|-----------|----------|------|
| N-13 | **e약은요 개요정보** | `DrbEasyDrugInfoService` | P5 핵심정보 탭 | ✅ 완전 작동 |
| N-14 | **묶음의약품** | `DrbBundleInfoService02` | P5 관련품목 탭 | ⚪ HIRA 처방약 위주 |

```python
# e약은요 (NO 248) — 이미 구현됨, 파라미터 camelCase 확인
# itemName, entpName → camelCase
# 검증 필드: efcyQesitm(효능), useMethodQesitm(사용법), atpnWarnQesitm(경고),
#             intrcQesitm(상호작용), seQesitm(부작용), depositMethodQesitm(보관법)
# ※ 베니톨정은 e약은요 미등록 (일반의약품이지만 소비자 안내 등록 없음) → 정상 처리
```

### 7.5 식품·건강기능식품 신규 API (식품QA 워크스페이스 + P6 강화)

| NO | 서비스명 | 엔드포인트 | 활용 위치 |
|----|---------|-----------|----------|
| N-16 | **식품영양성분DB** | `FoodNtrCpntDbInfo02` | 식품 제품 상세 |
| N-17 | **건강기능식품 개별인정형** | (신청, 엔드포인트 확인 필요) | 건기식 허브 (Phase R-4) |
| N-18 | **건강기능식품 영양DB** | (신청) | 건기식 허브 |
| N-19 | **건강기능식품 품목제조신고** | (신청) | 건기식 허브 |
| N-20 | **건강기능식품 GMP** | `FoodGmpStbltCompInfo` | 식품QA 워크스페이스 ✅ 471건 |
| N-21 | **식품공전** | (신청) | 식품 검색 참조 |
| N-22 | **식품 행정처분 3종** | 수입식품업·판매업·제조가공업 | 식품QA 워크스페이스 ✅ |

```python
# 식품 행정처분 3종 (NO 3·5·6) — 모두 정상 작동 확인
# 파라미터: PRCSCITYPOINT_BSSHNM (UPPER_CASE)
# 검증 필드: PRCSCITYPOINT_BSSHNM(업체명), INDUTY_CD_NM(업종),
#            DSPS_DCSNDT(처분결정일), DSPS_TYPECD_NM(처분유형), VILTCN(위반내용)

def fetch_food_sanction_import(num_of_rows=20):
    """수입식품업 행정처분 (NO 3)"""
    pass

def fetch_food_sanction_sale(num_of_rows=20):
    """식품판매업 행정처분 (NO 5)"""
    pass

def fetch_food_sanction_manufacture(num_of_rows=20):
    """식품제조가공업 행정처분 (NO 6)"""
    pass

# 건강기능식품 GMP (NO 51) — 검증됨
# 파라미터: 전체 fetch (클라이언트 필터)
# 검증 필드: LCNS_NO, BSSH_NM, INDUTY_CD_NM, SITE_ADDR, CLSBIZ_DVS_CD_NM(정상/폐업)
def fetch_hf_gmp(num_of_rows=100):
    """건강기능식품 GMP 지정현황 (NO 51) — 이미 구현됨"""
    pass
```

### 7.6 희귀의약품 정보 (R&D + QA 보조)

| NO | 서비스명 | 건수 | 상태 |
|----|---------|------|------|
| N-3 | **희귀필수의약품** | 24건 (치료용) | 🟡 필드명 단순화 필요 |
| N-4 | **희귀의약품** | 468건 | 🟠 필드명 수정 필요 |

```python
# NO 565 희귀의약품 — 필드명 수정 필요
# ❌ 기존: PRDUCT_NAME
# ✅ 실제: PRODT_NAME, TARGET_DISEASE, RARITY_DRUG_APPOINT_NO, APPOINT_DATE, DEVSTEP_YN

def fetch_rare_drug(num_of_rows=20):
    """희귀의약품 (NO 565) — PRODT_NAME 필드 사용"""
    pass

# NO 81 희귀필수의약품
# 자가치료용: 0건 (정상)
# 치료용: 24건 — INGR, MEDCIN_NAME 만 존재 (단순 목록)
```

### 7.7 신규 API 구현 우선순위

| 우선순위 | API | 이유 |
|---------|-----|------|
| ⭐⭐⭐ | DUR 성분·품목 (N-1, N-2) | P5 안전성 탭 완성, QA/QC 핵심 수요 |
| ⭐⭐⭐ | GMP 적합판정 (N-9) | QA 출하결재 핵심, 광동 조회 검증 완료 |
| ⭐⭐⭐ | 식품 행정처분 3종 (N-22) | 식품QA 워크스페이스 완성, 모두 작동 확인 |
| ⭐⭐ | FDA 특허 3종 (N-5·6·7) | R&D 특허 분쟁 트래커, 모두 작동 확인 |
| ⭐⭐ | e약은요 (N-13) | P5 핵심정보 탭 보강, 이미 일부 구현 |
| ⭐⭐ | 건기식 GMP (N-20) | 식품QA 워크스페이스 HACCP 보완, 작동 확인 |
| ⭐ | 희귀의약품 (N-4) | R&D 보조, 필드명 수정 후 사용 가능 |
| ⭐ | DMF 원료의약품 (N-12) | SCM 원료 공급망 추적 |

---

## 8. 구현 Phase 로드맵

### Phase R-1 (즉시, 1~2일)

> 코드 변경 최소, 임팩트 최대. 기존 기능 깨지지 않음.

| # | 작업 | 파일 | 난이도 |
|---|------|------|--------|
| R1-0 | **KD-IRIS 리브랜딩** | `_layout.html`, 모든 템플릿, `app.py`, `README.md` | 🟢 |
| R1-1 | **전체 API 코드·도메인 태그 제거** | 모든 `.html`, `_normalize_event()` | 🟢 |
| R1-2 | **SEVERITY_MAP + _macros.html 신설** | `blueprints/severity.py`, `templates/_macros.html` | 🟢 |
| R1-3 | **_normalize_event() 확장** | `app_views.py`, `watchlist_match.py` | 🟡 |
| R1-4 | **nav_config 7개 메뉴 확장** | `nav_config.py` | 🟢 |
| R1-5 | **/app/monitor 라우트 + timeline redirect** | `app_views.py`, `monitor.html` | 🟡 |
| R1-6 | **/app/workspace 단일 진입 라우트** | `app_views.py` | 🟢 |
| R1-7 | **의약외품 Product 360 신설** | `api_extras.py`, `product_quasi.html`, `app_views.py` | 🟡 |
| R1-8 | **risk.py 신설** | `blueprints/risk.py` | 🟢 |

### Phase R-2 (단기, 3~5일)

| # | 작업 | 파일 | 난이도 |
|---|------|------|--------|
| R2-1 | **통합검색 결과 신호등 카드** | `search.html`, `app_views.py` | 🟡 |
| R2-2 | **제품 상세 헤더 신호등 + D-Day** | `product_drug.html`, `app_views.py` | 🟡 |
| R2-3 | **이벤트 모니터 필터 + NEW 배지 + 그룹화** | `monitor.html`, `app_views.py` | 🟡 |
| R2-4 | **워치리스트 위험도 정렬 + 인라인 미리보기** | `watchlist.html` | 🟡 |
| R2-5 | **watchlist_match 집계 헬퍼 신설** | `watchlist_match.py` | 🟡 |
| R2-6 | **홈 대시보드 /app/home 신설** | `home.html`, `app_views.py` | 🟡 |
| R2-7 | **inject_nav() CRITICAL 배지 동적 주입 확장** | `app.py` | 🟢 |
| R2-8 | **DUR 안전성 탭 (N-1·N-2) 연동** | `api_extras.py`, `product_drug.html` | 🟡 |
| R2-9 | **GMP 적합판정 탭 (N-9) 연동** | `api_extras.py`, `product_drug.html` | 🟢 |

### Phase R-3 (중기, 1~2주)

| # | 작업 | 파일 | 난이도 |
|---|------|------|--------|
| R3-1 | **RA 워크스페이스 D-Day 캘린더 재설계** | `workspaces_config.py`, `workspace.html` | 🔴 |
| R3-2 | **제품 상세 규제 타임라인 섹션** | `product_drug.html` | 🔴 |
| R3-3 | **동일 성분 유사 품목 조회** | `app_views.py` | 🔴 |
| R3-4 | **검사부적합 분류 차트 + 제조소 위험 순위** | `inspections.html`, `app_views.py` | 🔴 |
| R3-5 | **워치리스트 Excel 일괄 업로드** | `app_views.py`, `watchlist.html` | 🔴 |
| R3-6 | **AI 코파일럿 맥락 자동 주입** | `copilot.html`, `app_views.py` | 🔴 |
| R3-7 | **Excel 내보내기 공통 라우트** | `app_views.py` | 🔴 |
| R3-8 | **식품 행정처분 3종 연동 (N-22)** | `api_extras.py`, `workspace.html` | 🟡 |
| R3-9 | **FDA 특허 트래커 (N-5·6·7)** | `api_extras.py`, `workspace.html` | 🟡 |

### Phase R-4 (장기, Phase 2 범위)

- 리포트 페이지 실구현 (PDF/Excel 생성)
- Slack 웹훅 알림 연동 (인프라 기존 보유)
- 워크스페이스 하위 메뉴 accordion 사이드바
- 건강기능식품 허브 신규 페이지 (N-17·18·19·21)
- 검색 이력 서버사이드 저장 (DB 필요)

---

## 9. 검증 체크리스트

### 9.1 공통 검증 (전 Phase)

```bash
# 리브랜딩 완료
grep -r "RegHub 360" templates/ app.py run.py README.md   # 0건

# 개발자 코드 제거
grep -r "API [0-9]" templates/    # 0건
grep -r "domain_kr" templates/    # 0건
grep -r '"—"' templates/          # 0건

# 사이드바 7개 메뉴
# 브라우저에서 메뉴 수 확인: 오늘의브리핑·제품조회·이벤트모니터·워치리스트·워크스페이스·검사부적합·코파일럿

# 다크모드
# 사이드바 달/해 아이콘 → 토큰 기반 테마 전환, 새로고침 후 유지

# 모바일
# 900px 이하: 사이드바 숨김 + 톱바 햄버거 노출 → 클릭 시 슬라이드
```

### 9.2 페이지별 검증

| 페이지 | 핵심 검증 항목 |
|--------|---------------|
| `/app/home` | CRITICAL 배너 조건부 표시, 워치리스트 3종 숫자, D-Day 캘린더 |
| `/` (검색) | 검색 전 빈 화면 이벤트 유도, 검색 후 신호등 카드, 탭 순서 |
| `/app/monitor` | CRITICAL→HIGH→LOW 정렬, 기간 필터, NEW 배지, 워치리스트 매칭 배지 |
| `/app/watchlist` | 위험도 정렬, 인라인 미리보기(details/summary), 요약 3숫자 |
| `/app/product/<code>` | 헤더 신호등, 탭 5개(핵심→규제→안전→관련→외형), 동일 성분 품목 |
| `/app/product-quasi/<code>` | 200 OK, 5탭 동작, 의약외품 데이터 표시 |
| `/app/workspace/ra` | D-Day 캘린더 카드, placeholder 0건, GMP 만료일 표시 |
| `/app/workspace/scm` | 공급부족 테이블, placeholder 0건 |
| `/app/workspace/rnd` | 임상·특허·생동성 실 건수, placeholder 0건 |
| `/app/workspace/food_qa` | 식품 행정처분 3종 건수, 건기식 GMP 건수 |
| `/app/inspections` | 광동 관련 KPI 1순위(2칸), 분류 차트, 제조소 위험 순위, 광동 매칭 상단 고정 |
| `/app/copilot` | 시스템 현황 브리핑 패널, 빠른 질문 칩 3카테고리 |

### 9.3 API 필드 매핑 검증

```python
# 수정된 필드명 적용 확인 (api_extras.py)
assert "PRODT_NAME" in fetch_rare_drug()["items"][0]       # NO 565
assert "TITLE" in fetch_safety_letter(TITLE="주의")        # NO 547 UPPER_CASE
assert "BSSH_NM" in fetch_drug_gmp(BSSH_NM="광동")        # NO 132
assert "PRDUCT" in fetch_food_inspect()["items"][0]        # NO 535
assert "company" in fetch_smart_haccp()["items"][0]        # NO 12
```

### 9.4 회귀 테스트

```
□ /healthz → {"ok": true, "service": "KD-IRIS"} 200 OK
□ /app/timeline → /app/monitor 301 redirect 확인
□ 워치리스트 CRUD (추가·제거·8종 매칭) 동작
□ 모든 워크스페이스 200 OK + KPI placeholder 0건
□ 광동 GMP: BSSH_NM="광동제약" → 1건, VLD_PRD_YMD="2027-03-28"
□ API 타임아웃(30초) 시 graceful 처리 (에러 메시지 표시)
□ 대용량 API (NO 561·554·556) num_of_rows=50 제한 적용 확인
```

---

## 10. 비-목표

> 이번 리뉴얼(R-1~R-3) 범위에 **포함하지 않는** 항목.

- HTMX/SPA 라우팅 도입
- 사용자 인증·세션 (USER_INFO 하드코딩 유지)
- Slack 웹훅 실알림 연동 (UI 버튼만, 실 발송 X)
- PDF 리포트 실생성 (Phase R-4)
- 워크스페이스 하위 메뉴 accordion (Phase R-4)
- 건강기능식품 허브 신규 페이지 (Phase R-4)
- 검색 자동완성 서버사이드
- 마약류 통계 대시보드 (NO 81)
- 사용자별 설정 DB 저장
- 외부 LIMS 연동
- 영업 워크스페이스 `share` KPI (자사 점유율)
- 워치리스트 자동 이메일·Slack 알림 (다음 사이클)
- 새 SERVICE_KEY 발급·기존 키 폐기 (사용자 별도 수행)
- GitHub Actions CI/CD 설정

---

## 부록 A — 전체 API 목록 (45개, 검증 상태 포함)

| NO | 서비스명 | 엔드포인트 | 검증 | 파라미터 케이스 | 서버검색 |
|----|---------|-----------|------|----------------|---------|
| 1 | 식품 영양성분DB | FoodNtrCpntDbInfo02 | 🟡 | FOOD_NM_KR | ✅ |
| 3 | 식품 행정처분(수입) | AdmmRsltIprtFoodService | ✅ | PRCSCITYPOINT_BSSHNM | ✅ |
| 5 | 식품 행정처분(판매) | AdmmRsltFoodSaleService | ✅ | PRCSCITYPOINT_BSSHNM | ✅ |
| 6 | 식품 행정처분(제조) | AdmmRsltFoodMnftPrcsService | ✅ | PRCSCITYPOINT_BSSHNM | ✅ |
| 12 | 스마트HACCP | SmartCertFoodListService | 🟡 | - (전체) | ❌ |
| 51 | 건기식 GMP | FoodGmpStbltCompInfo | ✅ | - (전체) | ❌ |
| 81 | 희귀필수의약품 | RareEsentMdcin | ⚪ | - | ❌ |
| 132 | GMP 적합판정서 | DrugGmpStbltJgmtIssuStusService | ✅ | **BSSH_NM** | ✅ |
| 140 | 의약품 허가 | DrugPrdtPrmsnInfoService07 | ✅ | **item_name** | ✅ |
| 142 | 국가출하승인 | DrugNatnShipmntAprvInfoService | ✅ | - (전체) | ❌ |
| 144 | 업체허가현황 | DrugEtcBsshBspmStusService | ✅ | - (전체) | ❌ |
| 145 | 의약외품 허가 | QdrgPrdtPrmsnInfoService03 | ✅ | **item_name** | ✅ |
| 153 | 수입식품 회수 | IprtFoodReclSaleStopPrdtStusService | ✅ | - (전체) | ❌ |
| 248 | e약은요 | DrbEasyDrugInfoService | ✅ | **itemName** (camel) | ✅ |
| 269 | 묶음의약품 | DrbBundleInfoService02 | ⚪ | trustItemName | ✅ |
| 483 | 원료의약품 DMF | MdcDmfInfoService01 | ✅ | - (전체) | ❌ |
| 484 | 대조약 | MdcCompDrugInfoService04 | ✅ | - (전체) | ❌ |
| 485 | 생동성인정품목 | MdcBioEqInfoService01 | ✅ | - (전체) | ❌ |
| 531 | DUR 품목정보 | DURPrdlstInfoService03 | 🟡 | **itemName** (camel) | ✅ |
| 533 | DUR 성분정보 | DURIrdntInfoService03 | ✅ | INGR_NAME | ✅ |
| 534 | 공급중단 | MdcinPrdctnIncmeSuplyService2 | 🟡 | - (전체) | ❌ |
| 535 | 검사부적합 | PrsecImproptFoodInfoService03 | ✅ | - (전체) | ❌ |
| 537 | 공급부족 | MdcinSuplyLackService03 | 🟡 | - (전체) | ❌ |
| 539 | 의약품 회수 | MdcinRtrvlSleStpgeInfoService04 | ✅ | - (전체) | ❌ |
| 547 | 안전성서한 | DrugSafeLetterService02 | 🟡 | **TITLE** (대문자) | ✅ |
| 552 | FDA Paragraph IV | ParagraphIVTrgetMdcinService02 | ✅ | - (전체) | ❌ |
| 554 | 재심사 | MdcinRejdgeService01 | ✅ | - (전체, ⚠️ 112K건) | ❌ |
| 556 | 재평가 | MdcinRevalService02 | ✅ | - (전체, ⚠️ 64K건) | ❌ |
| 557 | 국내소송 특허 | DmstcLwstMdcinInfoService02 | ✅ | - (전체) | ❌ |
| 561 | 의약품 특허 | MdcinPatentInfoService2 | ✅ | - (전체, ⚠️ 120K건) | ❌ |
| 562 | FDA 오렌지북 | FdaOrngbkPatentInfoService01 | ✅ | - (전체) | ❌ |
| 563 | 낱알식별 | MdcinGrnIdntfcInfoService03 | ✅ | **item_name** | ✅ |
| 564 | 행정처분 | MdcinExaathrService04 | 🟡 | **item_name** | ✅ |
| 565 | 희귀의약품 | RareMdcinInfoService02 | 🟠 | - (전체) | ❌ |
| 566 | 임상시험 | MdcinClincTestInfoService02 | ✅ | - (전체) | ❌ |
| 568 | 임상기관 | ClinicTestOprtnInsttInfoService01 | ✅ | - (전체) | ❌ |

---

## 부록 B — 작업 순서 권장

```
1. Phase R-1 (리브랜딩 + API 코드 제거 + Severity + 의약외품)
   → git commit: "feat: KD-IRIS 리브랜딩 + R-1 공통 기반"

2. 사용자 확인 (화면 검토)

3. Phase R-2 (신호등 + 홈 + 모니터 강화 + DUR·GMP 연동)
   → git commit: "feat: R-2 의사결정 지원 UI"

4. 사용자 확인

5. Phase R-3 (RA 캘린더 + 규제 타임라인 + Excel 업로드·내보내기 + 식품처분 3종)
   → git commit: "feat: R-3 심화 기능 완성"

6. git push origin main (GitHub 동기화)
```

---

*문서 끝 — KD-IRIS 통합 리뉴얼 명세서 v2.0*  
*기준: RENEWAL_PLAN v1.0 + Phase 5 KD-IRIS 구현 명세 + API 전수 검증 결과 + OpenAPI 신청 목록 분석*
