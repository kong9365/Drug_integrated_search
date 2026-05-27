# RegHub 360 — 정보 구성 리뉴얼 전체 명세서

> **문서 목적:** Claude Code가 RegHub 360의 각 페이지·기능을 리뉴얼 구현하기 위한 상세 명세.  
> **기준 레포:** `https://github.com/kong9365/Drug_integrated_search`  
> **작성 기준일:** 2026-05-27  
> **우선 읽을 파일:** `app.py`, `blueprints/nav_config.py`, `blueprints/app_views.py`, `blueprints/workspaces_config.py`, `blueprints/watchlist_match.py`, `api_extras.py`, `templates/` 전체

---

## 목차

1. [리뉴얼 목적 및 핵심 원칙](#1-리뉴얼-목적-및-핵심-원칙)
2. [전체 공통 변경사항](#2-전체-공통-변경사항)
3. [네비게이션 구조 재편](#3-네비게이션-구조-재편)
4. [페이지별 상세 명세](#4-페이지별-상세-명세)
   - [P1. 홈 대시보드 (신규)](#p1-홈-대시보드-신규--앱홈)
   - [P2. 통합 검색](#p2-통합-검색--앱검색)
   - [P3. 이벤트 모니터](#p3-이벤트-모니터--앱timeline)
   - [P4. 워치리스트](#p4-워치리스트--앱watchlist)
   - [P5. 제품 상세 (의약품)](#p5-제품-상세-의약품--앱productcode)
   - [P6. 제품 상세 (식품)](#p6-제품-상세-식품--앱product-foodcode)
   - [P7. 워크스페이스 (부서별)](#p7-워크스페이스-부서별--앱workspacedept)
   - [P8. 검사부적합 트래커](#p8-검사부적합-트래커--앱inspections)
   - [P9. AI 코파일럿](#p9-ai-코파일럿--앱copilot)
   - [P10. 리포트](#p10-리포트--앱reports)
5. [구현 우선순위 로드맵](#5-구현-우선순위-로드맵)
6. [검증 체크리스트](#6-검증-체크리스트)
7. [비-목표 (이번 리뉴얼 범위 외)](#7-비-목표)

---

## 1. 리뉴얼 목적 및 핵심 원칙

### 1.1 핵심 문제 정의

현재 RegHub 360은 **데이터 나열형** 구조다. 실무자가 정보를 보기 위해 여러 탭을 직접 탐색해야 하며, 같은 제품에 관한 여러 규제 이벤트가 흩어져 있어 종합 판단이 불가능하다. 내부 개발 코드(API 번호, 필드 코드명)가 화면에 그대로 노출되고, 긴급·정보성 이벤트가 동등하게 나열되어 우선순위 인식이 어렵다.

### 1.2 리뉴얼 방향

| 기존 | 목표 |
|------|------|
| 데이터 나열형 | 의사결정 지원형 |
| API 탭별 분리 조회 | 제품 중심 통합 뷰 |
| 단순 카운트 KPI | 맥락 있는 액션 KPI |
| 개발자 코드 노출 | 실무 언어로 정리 |
| 동등 나열 | 심각도 기반 우선순위 |

### 1.3 사용자 페르소나 (우선순위 순)

| 순위 | 팀 | 주요 관심사 | 핵심 질문 |
|------|-----|-------------|-----------|
| 1 | **QA/QC** | 회수·처분·GMP | "지금 당장 대응해야 할 이슈가 있나?" |
| 2 | **RA** | 재심사·변경허가 마감 | "언제까지 뭘 제출해야 하나?" |
| 3 | **SCM** | 공급부족·회수 영향 | "어떤 품목이 공급 위험 상태인가?" |
| 4 | **R&D** | 임상·특허·경쟁사 | "경쟁사 파이프라인이 어디까지 왔나?" |
| 5 | **식품QA** | 검사부적합·HACCP | "이 원재료, 쓸 수 있는 건가?" |

### 1.4 설계 원칙

- **원칙 1 — 맥락 우선:** 검색 결과·이벤트에 항상 "그래서 뭘 해야 하나"가 보여야 한다.
- **원칙 2 — 심각도 계층:** 🔴 긴급(회수·판매중지) → 🟡 주의(처분·공급부족) → 🟢 정보(신규허가·재심사예정) 3단계를 일관되게 적용한다.
- **원칙 3 — 개발 코드 전면 제거:** `API 539`, `NO 547`, `domain_kr`, 필드명 코드 등 일체 화면 노출 금지.
- **원칙 4 — 제품 중심 통합:** 모든 이벤트는 특정 제품·업체로 드릴다운 가능해야 한다.
- **원칙 5 — 즉시 행동 가능:** 이벤트 카드에 반드시 "다음 액션 링크"가 있어야 한다.

---

## 2. 전체 공통 변경사항

### 2.1 즉시 제거할 요소 (전체 템플릿)

아래 항목들은 **모든 페이지·카드·테이블에서 전면 삭제**한다.

```
삭제 대상:
- "API 539", "API 547", "NO 554" 등 API 번호 표시
- "domain: drug", "domain_kr: 의약품" 중복 태그
- 필드명 코드 원문 노출 (예: "SPCLTY_PBLC", "ITEM_SEQ" 등)
- "api:" 키로 렌더링되는 모든 출처 표시
- placeholder "—" (데이터 없음은 "정보 없음" 또는 섹션 자체 숨김)
- 빈 날짜 필드 렌더링 (date가 빈 문자열이면 "날짜 미확인"으로 처리)
```

**수정 위치:** `templates/app/timeline.html`, `templates/app/watchlist.html`, 이벤트 카드 공통 매크로, `blueprints/app_views.py`의 `_normalize_event()` 함수

### 2.2 공통 심각도(severity) 체계 정의

`blueprints/watchlist_match.py` 및 `app_views.py`의 `_normalize_event()`에 아래 맵핑을 적용한다.

```python
SEVERITY_MAP = {
    # 🔴 긴급 — 즉각 대응 필요
    "recall":         {"level": "CRITICAL", "label": "회수명령",    "color": "danger"},
    "supply_stop":    {"level": "CRITICAL", "label": "판매중지",    "color": "danger"},

    # 🟡 주의 — 모니터링 필요
    "disciplinary":   {"level": "HIGH",     "label": "행정처분",    "color": "warn"},
    "supply_lack":    {"level": "HIGH",     "label": "공급부족",    "color": "warn"},
    "safety_letter":  {"level": "HIGH",     "label": "안전성서한",  "color": "warn"},
    "inspection_fail":{"level": "HIGH",     "label": "검사부적합",  "color": "warn"},

    # 🟢 정보 — 인지 및 기회 탐색
    "permit_new":     {"level": "LOW",      "label": "신규허가",    "color": "success"},
    "clinical_new":   {"level": "LOW",      "label": "임상신규",    "color": "info"},
    "patent_new":     {"level": "LOW",      "label": "특허등재",    "color": "info"},
    "review_due":     {"level": "LOW",      "label": "재심사예정",  "color": "info"},
    "reeval_done":    {"level": "LOW",      "label": "재평가완료",  "color": "info"},
}
```

### 2.3 공통 이벤트 카드 컴포넌트 (Jinja2 매크로)

`templates/_macros.html`에 아래 매크로를 신설하고, timeline·watchlist·홈 대시보드 등 모든 이벤트 카드에서 재사용한다.

```jinja2
{% macro event_card(event, show_product_link=True) %}
<div class="event-card event-card--{{ event.severity_color }}" 
     data-severity="{{ event.severity_level }}">
  
  {# 심각도 배지 + NEW 표시 #}
  <div class="event-card__header">
    <span class="severity-badge severity-badge--{{ event.severity_color }}">
      {{ event.type_label }}
    </span>
    {% if event.is_new %}<span class="badge badge--new">NEW</span>{% endif %}
    <time class="event-card__date">
      {{ event.date if event.date else "날짜 미확인" }}
    </time>
  </div>

  {# 제목 + 업체 #}
  <p class="event-card__title">{{ event.title }}</p>
  <p class="event-card__entity">{{ event.entity }}</p>

  {# 요약 (있을 때만) #}
  {% if event.summary %}
  <p class="event-card__summary">{{ event.summary }}</p>
  {% endif %}

  {# 액션 링크 #}
  <div class="event-card__actions">
    {% if show_product_link and event.product_code %}
    <a href="/app/product/{{ event.product_code }}" class="btn btn--ghost btn--sm">
      제품 상세 →
    </a>
    {% endif %}
    {% if event.ext_url %}
    <a href="{{ event.ext_url }}" target="_blank" class="btn btn--ghost btn--sm">
      원문 보기 ↗
    </a>
    {% endif %}
  </div>

</div>
{% endmacro %}
```

### 2.4 공통 위험도 신호등 컴포넌트

제품 검색 결과 카드, 제품 상세 헤더, 워치리스트 카드에 공통 적용.

```python
# app_views.py 헬퍼 함수 신설
def calc_risk_signal(approval_data, disciplinary_items, recall_items, review_due_days=None):
    """
    반환값: {
      "level": "CRITICAL" | "HIGH" | "LOW" | "NONE",
      "color": "danger" | "warn" | "success" | "muted",
      "label": "위험" | "주의" | "정상" | "정보없음",
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

    if review_due_days and review_due_days <= 30:
        if level == "NONE":
            level = "HIGH"
        reasons.append(f"재심사 D-{review_due_days}일")
    
    if not reasons:
        level = "LOW"
        reasons = ["이상 없음"]

    color_map = {"CRITICAL": "danger", "HIGH": "warn", "LOW": "success", "NONE": "muted"}
    label_map = {"CRITICAL": "위험", "HIGH": "주의", "LOW": "정상", "NONE": "정보없음"}

    return {
        "level": level,
        "color": color_map[level],
        "label": label_map[level],
        "reasons": reasons
    }
```

---

## 3. 네비게이션 구조 재편

### 3.1 현재 vs 리뉴얼 사이드바 메뉴

```
현재 (5개, 기능 중심):        리뉴얼 (7개, 업무 맥락 중심):
─────────────────────        ──────────────────────────────
🔍 통합 검색           →    🏠 오늘의 브리핑     [신규]
📅 이벤트 타임라인     →    🔍 제품·업체 조회    [명칭 변경]
👁 워치리스트          →    🚨 이벤트 모니터     [범위 확장]
📊 리포트              →    👁 내 워치리스트     [기능 강화]
🤖 AI 코파일럿         →    🏢 워크스페이스      [하위메뉴]
                             📊 리포트·내보내기   [기존]
                             🤖 AI 코파일럿       [맥락 강화]
```

### 3.2 `blueprints/nav_config.py` 변경 명세

```python
NAV_ITEMS = [
    {
        "key": "home",
        "label": "오늘의 브리핑",
        "href": "/app/home",
        "icon_svg": '<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>',
        "badge": None,
        "disabled": False,
    },
    {
        "key": "search",
        "label": "제품·업체 조회",
        "href": "/",
        "icon_svg": '<path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>',
        "badge": None,
        "disabled": False,
    },
    {
        "key": "monitor",
        "label": "이벤트 모니터",
        "href": "/app/monitor",
        "icon_svg": '<path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>',
        # badge는 inject_nav()에서 동적으로 CRITICAL 건수 주입
        "badge": None,
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
        "badge": None,
        "disabled": False,
        # 하위 메뉴 (템플릿에서 accordion 처리)
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
        "badge": None,
        "disabled": False,
    },
    {
        "key": "reports",
        "label": "리포트·내보내기",
        "href": "/app/reports",
        "icon_svg": '<path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>',
        "badge": {"kind": "muted", "text": "Phase 2"},
        "disabled": True,
    },
    {
        "key": "copilot",
        "label": "AI 코파일럿",
        "href": "/app/copilot",
        "icon_svg": '<path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>',
        "badge": {"kind": "brand", "text": "NEW"},
        "disabled": False,
    },
]
```

### 3.3 `app.py` — `inject_nav()` 확장

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
            alert_count = watchlist_match.total_alert_count(match_map)
            # CRITICAL 건수만 별도 집계 (severity=CRITICAL인 이벤트)
            wl_critical = watchlist_match.critical_alert_count(match_map)
    except Exception as e:
        logger.warning(f"inject_nav watchlist 계산 실패: {e}")

    try:
        # 오늘 신규 CRITICAL 이벤트 건수 (이벤트 모니터 배지용)
        monitor_critical = watchlist_match.today_critical_count()
    except Exception as e:
        logger.warning(f"inject_nav monitor 계산 실패: {e}")

    items = []
    for it in NAV_ITEMS:
        it = dict(it)  # 원본 불변 유지
        if it["key"] == "watchlist":
            if wl_critical > 0:
                it["badge"] = {"kind": "danger", "text": str(wl_critical)}
            elif wl_total > 0:
                it["badge"] = {"kind": "brand", "text": str(wl_total)}
        elif it["key"] == "monitor":
            if monitor_critical > 0:
                it["badge"] = {"kind": "danger", "text": str(monitor_critical)}
        items.append(it)

    return {
        "nav_items": items,
        "workspaces": WORKSPACES,
        "user_info": USER_INFO,
    }
```

---

## 4. 페이지별 상세 명세

---

### P1. 홈 대시보드 (신규) — `/app/home`

#### 4.1.1 신설 목적

사용자가 시스템에 진입했을 때 **"지금 당장 봐야 할 것"** 을 즉시 확인할 수 있는 브리핑 페이지. 기존 통합 검색(`/`)이 "검색하러 오는 곳"이라면, 홈은 "모닝 브리핑을 받는 곳"이다.

#### 4.1.2 정보 구성 요소 (위→아래 순서)

```
[영역 A] 오늘 날짜 + 긴급 알림 배너
  - 표시 조건: CRITICAL 이벤트가 1건 이상일 때만 노출
  - 내용: "🔴 오늘 회수명령 N건 · 판매중지 M건 신규 발생"
  - 클릭: /app/monitor?severity=CRITICAL

[영역 B] 워치리스트 요약 패널 (등록 품목이 있을 때)
  - 위험 N건 / 주의 M건 / 이상없음 K건 (3개 숫자 카드)
  - "자세히 보기 →" → /app/watchlist

[영역 C] 오늘의 주요 이벤트 TOP 5 (severity 높은 순)
  - event_card 매크로 재사용
  - "전체 보기 →" → /app/monitor

[영역 D] 30일 이내 마감 일정 (RA 데이터)
  - D-Day 형식으로 최대 3건
  - 데이터 없으면 영역 자체 숨김

[영역 E] 빠른 검색 진입
  - 검색창 1개 + "제품·업체 조회로 이동 →"
  - 홈에서도 검색 가능하게 (결과는 /search로 redirect)
```

#### 4.1.3 신규 파일 목록

| 파일 | 작업 |
|------|------|
| `templates/app/home.html` | 신규 생성, `_layout.html` 상속 |
| `blueprints/app_views.py` | `/app/home` 라우트 신설 |

#### 4.1.4 백엔드 라우트 명세

```python
@app_bp.route("/home")
def home():
    """오늘의 브리핑 홈 대시보드."""
    from ..api_extras import (
        fetch_drug_recall, fetch_drug_disciplinary, fetch_drug_supply_stop
    )
    from ..blueprints import watchlist_store, watchlist_match

    # 오늘 CRITICAL 이벤트 수집 (최대 5건)
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

    # severity 정렬 (CRITICAL > HIGH > LOW)
    sev_order = {"CRITICAL": 0, "HIGH": 1, "LOW": 2}
    critical_events.sort(key=lambda e: sev_order.get(e.get("severity_level", "LOW"), 2))
    critical_events = critical_events[:5]

    # 워치리스트 요약
    wl_summary = {"critical": 0, "high": 0, "ok": 0, "total": 0}
    try:
        wl_total = watchlist_store.count()
        if wl_total > 0:
            entries = watchlist_store.list_entries()
            match_map = watchlist_match.match_for_entries(entries)
            wl_summary = watchlist_match.summarize_by_severity(match_map)
    except Exception:
        pass

    # 30일 이내 RA 마감 (재심사)
    upcoming_deadlines = []
    try:
        from ..api_extras import fetch_drug_review
        items = fetch_drug_review(num_of_rows=20).get("items", [])
        for it in items:
            deadline = _parse_deadline(it)  # D-Day 계산 헬퍼
            if deadline and deadline <= 30:
                upcoming_deadlines.append({
                    "item_name": it.get("ITEM_NAME", ""),
                    "deadline_days": deadline,
                    "type": "재심사",
                })
        upcoming_deadlines = sorted(upcoming_deadlines, key=lambda x: x["deadline_days"])[:3]
    except Exception:
        pass

    return render_template(
        "app/home.html",
        active_page="home",
        critical_events=critical_events,
        wl_summary=wl_summary,
        upcoming_deadlines=upcoming_deadlines,
    )
```

---

### P2. 통합 검색 — `/`

#### 4.2.1 현재 문제점

| 구분 | 문제 | 삭제 여부 |
|------|------|-----------|
| KPI 전체 모수 숫자 | "허가건수 25,354건" 등 판단에 불필요 | ✅ 삭제 |
| 카테고리 칩 10개 병렬 나열 | 사용 빈도 낮고 맥락 불명확 | ✅ 삭제 후 재설계 |
| API 번호 카드 노출 | 개발자 정보 | ✅ 삭제 |
| 검색 결과와 전체 이벤트 혼재 | 검색 맥락 흐림 | ✅ 분리 |
| 탭별로만 위험 판단 가능 | 종합 위험도 불가 | ⚠️ 신규 추가 |
| 광동 관련 표시 없음 | 자사·경쟁사 구분 불가 | ⚠️ 신규 추가 |
| 검색 이력 없음 | 반복 검색 필요 | ⚠️ 신규 추가 |

#### 4.2.2 검색 전 상태 — 정보 구성 요소

```
[검색 히어로 영역]
  - 검색창 (placeholder: "제품명 또는 업체명으로 검색")
  - 검색 이력 드롭다운 (localStorage 기반, 최근 5건)
  - 빠른 검색 칩: [광동제약] [아세트아미노펜] [이부프로펜] [최근 회수품목]
    → 칩 클릭 시 해당 검색어로 즉시 검색

[안내 섹션 — 홈 대시보드로 유도]
  - "지금 주목해야 할 이벤트가 있습니다 → 오늘의 브리핑 보기"
  - 표시 조건: CRITICAL 이벤트 1건 이상일 때만
```

#### 4.2.3 검색 후 상태 — 정보 구성 요소

```
[결과 헤더]
  - 검색어 표시: '"타이레놀정" 검색 결과'
  - 결과 건수: "허가 정보 N건 · 관련 이벤트 M건"
  - 정렬: [최신순 ▼] [위험도순] [업체명순]

[종합 위험 신호등 카드] ← 신규 핵심 섹션
  - 제품명 + 업체명
  - 신호등: 🔴 위험 / 🟡 주의 / 🟢 정상
  - 이유 목록: "행정처분 1건", "재심사 D-45일" 등
  - 클릭: /app/product/{code}

[탭 구성 — 기존 유지, 순서 재배열]
  [허가 정보] [규제 이력] [낱알 식별]
   ↑ "규제 이력" 탭을 두 번째로 승격 (현재는 마지막)

[허가 정보 탭 — 표시 필드 명세]
  표시:
    - 품목명 (ITEM_NAME)
    - 업체명 (ENTP_NAME)
    - 허가일자 (ITEM_PERMIT_DATE) → "YYYY년 MM월 DD일" 포맷
    - 전문/일반 구분 (SPCLTY_PBLC) → "전문의약품" / "일반의약품"
    - 주성분 (MAIN_ITEM_INGR)
    - 보험코드 (EDI_CODE) — 있을 때만
    - 유효기간 (VALID_TERM) — 있을 때만
  
  제거:
    - ITEM_SEQ (품목기준코드 숫자값 — 내부 코드)
    - BIZRNO (사업자등록번호 — 필요 시 접어두기 처리)
    - ENTP_SEQ, ENTP_NO (업체 내부 코드)
    - 주소, 전화번호 등 행정 정보 → [상세 정보 펼치기] accordion

[규제 이력 탭 — 신규 통합]
  - 행정처분 목록 (처분명 + 처분일 + 사유)
  - 회수 목록 (회수명 + 회수일 + 사유)
  - 안전성서한 (있을 때만)
  - 각 항목에 심각도 배지 적용

[낱알 식별 탭]
  - 이미지 (있을 때만)
  - 모양, 색상, 각인, 크기
  - 분류 정보 (의약품 분류)
```

#### 4.2.4 백엔드 변경 명세

```python
# app_views.py — search() 함수 수정

@app_bp.route("/")  # 또는 현재 구조에 맞는 라우트
def search():
    q = (request.args.get("q") or "").strip()
    
    results = {
        "approval": [],
        "disciplinary": [],
        "recall": [],
        "identification": [],
        "risk_signal": None,  # ← 신규
    }

    if q:
        # 기존 API 호출 유지
        # ...

        # 신규: 위험도 신호등 계산
        results["risk_signal"] = calc_risk_signal(
            approval_data=results["approval"],
            disciplinary_items=results["disciplinary"],
            recall_items=results["recall"],
        )

    return render_template(
        "search.html",  # 또는 app/search.html
        active_page="search",
        query=q,
        results=results,
        # 신규 컨텍스트
        recent_searches=_get_recent_searches(request),  # localStorage는 JS에서 처리
    )
```

---

### P3. 이벤트 모니터 — `/app/monitor`

> **기존 `/app/timeline`을 `/app/monitor`로 확장 재설계.** 기존 라우트는 redirect 처리.

#### 4.3.1 현재 문제점

| 구분 | 문제 | 처리 |
|------|------|------|
| API 번호 카드 노출 | "API 566" 등 | ✅ 전면 삭제 |
| domain_kr 태그 중복 | "의약품" 탭 안에서 또 "의약품" | ✅ 삭제 |
| 동등 나열 (긴급=정보) | 우선순위 파악 불가 | ✅ 심각도 정렬 |
| 기간 필터 없음 | 시계열 탐색 불가 | ⚠️ 신규 |
| 이벤트 연관관계 없음 | 같은 제품 이벤트 연결 안 됨 | ⚠️ 신규 (그룹화) |
| 읽음/안읽음 없음 | 매번 전체 재확인 | ⚠️ 신규 |
| 날짜 빈값 렌더링 | 신뢰도 저하 | ✅ "날짜 미확인"으로 |

#### 4.3.2 정보 구성 요소

```
[상단 현황 배너]
  - "오늘 신규 N건 · 이번 주 M건 · 광동 관련 K건"
  - 광동 관련 건수: CRITICAL+HIGH 이벤트 중 watchlist 매칭된 것

[필터 바 — 1줄]
  - 기간: [오늘] [이번 주] [이번 달] [직접 입력: YYYY-MM-DD ~ YYYY-MM-DD]
  - 심각도: [전체] [🔴 긴급만] [🟡 주의] [🟢 정보]
  - 이벤트 유형: [전체] [회수] [처분] [안전성서한] [공급중단] [부적합] [신규허가] [임상] [특허] [재심사]
  - [Excel 내보내기] 버튼

[이벤트 목록 — 심각도 기반 정렬]
  정렬 순서:
    1. CRITICAL (회수·판매중지) — 빨간 좌측 보더
    2. HIGH (처분·공급부족·안전성서한·부적합) — 노란 좌측 보더
    3. LOW (신규허가·임상·특허·재심사) — 초록 좌측 보더

  카드 내 표시 필드:
    - 심각도 배지 (예: "회수명령")
    - NEW 배지 (오늘 신규 이벤트)
    - 제목 (품목명 중심)
    - 업체명
    - 날짜 (없으면 "날짜 미확인")
    - 요약 (사유/내용 1~2줄)
    - 액션 링크: [제품 상세 →] [원문 보기 ↗]
    - 워치리스트 매칭 배지: 내 워치리스트 품목이면 "📌 워치리스트" 표시

  카드 내 제거 필드:
    - API 번호, domain, domain_kr, url (원문 링크로 대체)

[같은 품목 이벤트 그룹화]
  - 동일 ITEM_NAME의 이벤트가 2건 이상이면 그룹 카드로 묶음
  - 예: "타이레놀정 — 이벤트 3건" → 펼쳐서 확인
```

#### 4.3.3 백엔드 변경 명세

```python
# app_views.py

@app_bp.route("/monitor")
def monitor():
    """이벤트 모니터 (기존 timeline 확장)."""
    severity_filter = request.args.get("severity", "ALL")
    type_filter = request.args.get("type", "ALL")
    period = request.args.get("period", "week")  # today/week/month

    # 기존 이벤트 수집 로직 유지 (6종)
    # + 신규 4종 (임상/특허/재심사/재평가)
    all_events = _collect_all_events()  # 기존 함수 재사용

    # 심각도 정렬
    sev_order = {"CRITICAL": 0, "HIGH": 1, "LOW": 2}
    all_events.sort(key=lambda e: (
        sev_order.get(e.get("severity_level", "LOW"), 2),
        e.get("date", "") or ""
    ), reverse=False)

    # 워치리스트 매칭 표시
    try:
        wl_entries = watchlist_store.list_entries()
        wl_names = {e["name"].lower() for e in wl_entries}
        for ev in all_events:
            title_lower = (ev.get("title") or "").lower()
            ev["in_watchlist"] = any(name in title_lower for name in wl_names)
    except Exception:
        pass

    # 필터 적용
    if severity_filter != "ALL":
        all_events = [e for e in all_events if e.get("severity_level") == severity_filter]
    if type_filter != "ALL":
        all_events = [e for e in all_events if e.get("type") == type_filter]

    # type별 카운트 (subtab용)
    from collections import Counter
    type_counts = Counter(e.get("type", "unknown") for e in all_events)

    # 오늘 신규 건수, 광동 관련 건수
    today_count = sum(1 for e in all_events if _is_today(e.get("date")))
    kwangdong_count = sum(1 for e in all_events if e.get("in_watchlist"))

    return render_template(
        "app/monitor.html",
        active_page="monitor",
        events=all_events,
        type_counts=dict(type_counts),
        today_count=today_count,
        kwangdong_count=kwangdong_count,
        severity_filter=severity_filter,
        type_filter=type_filter,
        period=period,
    )

# 기존 /app/timeline은 redirect
@app_bp.route("/timeline")
def timeline():
    return redirect(url_for("app_bp.monitor"), 301)
```

---

### P4. 워치리스트 — `/app/watchlist`

#### 4.4.1 현재 문제점

| 구분 | 문제 | 처리 |
|------|------|------|
| 등록일만 표시 | "마지막 이벤트 발생일"이 더 중요 | ✅ 교체 |
| 카운트 숫자만 (상세 불가) | 카드 내 이벤트 내용 안 보임 | ⚠️ 인라인 미리보기 추가 |
| 등록 순서 정렬 | 위험도 높은 것이 아래 있을 수 있음 | ✅ 위험도 정렬로 변경 |
| 1건씩 수동 등록 | 대량 등록 불가 | ⚠️ 일괄 업로드 추가 |
| 그룹/태그 없음 | 20개 이상 관리 불가 | ⚠️ 태그 기능 추가 |
| 모니터링 히스토리 없음 | 이력 파악 불가 | ⚠️ 신규 |

#### 4.4.2 정보 구성 요소

```
[상단 요약 패널]
  - 전체 N개 등록
  - 🔴 조치 필요 N개 / 🟡 모니터링 M개 / 🟢 이상없음 K개
  - [+ 품목 추가] [📎 Excel 일괄 업로드] [📥 전체 내보내기]

[품목 카드 목록 — 위험도 정렬]

  카드 구성:
    ┌──────────────────────────────────────────┐
    │ 🔴 [품목명] · [업체명]        [태그: 원료의약품] │
    │ 최신 이벤트: 회수명령 (2025-05-27, 3일 전)    │
    │                                          │
    │ ▼ 이벤트 인라인 미리보기 (접기/펼치기)           │
    │   사유: 함량 기준 부적합                    │
    │   조치기한: 2025-06-15                    │
    │                                          │
    │ 이벤트 카운트: 회수 1 | 처분 0 | 공급 0        │
    │ [전체 이력 보기] [제품 상세 →] [워치리스트 제거] │
    └──────────────────────────────────────────┘

  카드 내 표시 필드:
    - 품목명 + 업체명
    - 심각도 배지 (이벤트 있을 때)
    - 최신 이벤트 날짜 + 경과일
    - 이벤트 인라인 미리보기 (최신 1건, 접기/펼치기)
    - 이벤트 유형별 카운트 (8종: 회수·안전성·처분·공급·특허·임상·재심사·재평가)
    - 사용자 태그 (QC관리·원료·완제품 등)
    - 등록일 → "마지막 확인" 날짜로 교체

  카드 내 제거 필드:
    - 단순 등록일
    - API 번호

[일괄 업로드 모달]
  - Excel/CSV 업로드 (ITEM_NAME 컬럼 필수, ENTP_NAME 선택)
  - 미리보기 테이블 → 확인 후 일괄 등록

[모니터링 히스토리 패널 (품목별)]
  - 등록 이후 발생한 이벤트 시계열 목록
  - "이 품목 등록 후 총 N건의 이벤트 발생"
```

#### 4.4.3 백엔드 변경 명세

```python
# watchlist_match.py 신규 함수 추가

def summarize_by_severity(match_map: dict) -> dict:
    """
    match_map을 severity 기준으로 집계.
    반환: {"critical": N, "high": M, "ok": K, "total": T}
    """
    result = {"critical": 0, "high": 0, "ok": 0, "total": len(match_map)}
    for entry_name, counts in match_map.items():
        total_events = sum(counts.values())
        if counts.get("recalls", 0) > 0 or counts.get("supply_stop", 0) > 0:
            result["critical"] += 1
        elif total_events > 0:
            result["high"] += 1
        else:
            result["ok"] += 1
    return result

def critical_alert_count(match_map: dict) -> int:
    """CRITICAL 이벤트(회수·판매중지)가 있는 항목 수."""
    return sum(
        1 for counts in match_map.values()
        if counts.get("recalls", 0) > 0 or counts.get("supply_stop", 0) > 0
    )

def today_critical_count() -> int:
    """오늘 신규 CRITICAL 이벤트 건수 (5분 캐시)."""
    # recall + supply_stop 중 오늘 날짜인 것
    # 구현: _cached로 fetch 후 날짜 필터
    pass
```

---

### P5. 제품 상세 (의약품) — `/app/product/<code>`

#### 4.5.1 현재 문제점

| 구분 | 문제 | 처리 |
|------|------|------|
| 낱알 이미지가 상단 주요 위치 | 외형보다 규제이력이 중요 | ✅ 하단으로 이동 |
| 허가 원문 코드 노출 | SPCLTY_PBLC 등 필드명 노출 | ✅ 한글화 |
| 업체 행정 정보 전면 노출 | 사업자번호 등 불필요 | ✅ accordion 처리 |
| 탭별 분리 조회 | 종합 위험 판단 불가 | ✅ 헤더에 신호등 추가 |
| 제품 규제 타임라인 없음 | 이력 흐름 파악 불가 | ⚠️ 신규 핵심 섹션 |
| 재심사/재평가 일정 없음 | RA 핵심 정보 누락 | ⚠️ 신규 |
| 동일 성분 유사 품목 없음 | 대체품 탐색 불가 | ⚠️ 신규 |
| GMP 적합 판정 없음 | 출하 결재 시 필요 정보 누락 | ⚠️ 신규 (가능한 범위) |

#### 4.5.2 정보 구성 요소

```
[제품 헤더 — 종합 요약]
  ┌──────────────────────────────────────────────────┐
  │ 타이레놀정 500mg                                  │
  │ 한국얀센  |  전문의약품  |  허가: 1995-03-15       │
  │                                                  │
  │ 종합 위험 신호등: 🟡 주의 필요                     │
  │   ✅ 허가 유효   ⚠️ 행정처분 1건   ✅ 회수이력 없음 │
  │   📅 재심사 마감: D-45일 (2025-07-11)             │
  │                                                  │
  │ [📌 워치리스트 추가] [📥 정보 내보내기]            │
  └──────────────────────────────────────────────────┘

[탭 구성 — 순서 재배열]
  [핵심 정보] [규제 이력] [안전성] [관련 품목] [제품 외형]
   ↑ 기존에서 "규제 이력" 승격, "낱알식별"을 마지막으로

[탭 1: 핵심 정보]
  표시 필드 (한글 라벨로):
    - 품목명 / 업체명 / 허가일자 / 전문·일반 구분 / 주성분
    - 보험코드 (있을 때만)
    - 유효기간 (있을 때만)
    - ATC 코드 → "치료 분류: [ATC명]"으로 변환
    - 희귀의약품 여부 (있을 때만 뱃지)
  
  접어두기(accordion) 처리:
    - 사업자등록번호, 업체 허가번호, 품목기준코드 등 행정 코드

[탭 2: 규제 이력 — 핵심 신규 섹션]
  
  제품 규제 타임라인 (가로 스크롤):
    허가(1995) ──── 재심사(2005) ──── 처분(2023-08) ──── 재심사예정(2025-07) →
  
  상세 목록:
    - 행정처분 목록 (처분명 · 처분일 · 처분기관 · 사유)
    - 회수·판매중지 목록 (회수명 · 회수일 · 사유 · 조치기한)
    - 안전성서한 목록 (있을 때만)
  
  RA 일정:
    - 재심사 만료일 / 남은 일수 / 재심사 결과 (통과/조건부 등)
    - 재평가 예정일 (있을 때만)

[탭 3: 안전성]
  - 안전성서한 (safety_letter) 목록
  - 부작용 보고 요약 (해당 API 연동 가능 시)

[탭 4: 관련 품목 — 신규]
  동일 성분(MAIN_ITEM_INGR) 유사 품목 목록:
    - 최대 10건
    - 품목명 · 업체명 · 허가일 · 위험도 신호등
    - 클릭 → 해당 제품 상세로 이동
  
  표시 조건: 허가 정보 조회 시 동일 성분으로 재검색

[탭 5: 제품 외형 (기존 낱알식별)]
  - 이미지 (있을 때만, 오류 시 "이미지 없음" 처리)
  - 모양 / 색상 / 각인 앞면·뒷면 / 크기(장축·단축·두께)
  - 의약품 분류
```

#### 4.5.3 백엔드 변경 명세

```python
# app_views.py — product_drug() 함수 수정

@app_bp.route("/product/<code>")
def product_drug(code):
    # 기존 허가정보·처분·회수·낱알식별 fetch 유지
    # ...

    # 신규: 위험도 신호등 계산
    risk_signal = calc_risk_signal(
        approval_data=[approval] if approval else [],
        disciplinary_items=disciplinary_items,
        recall_items=recall_items,
        review_due_days=_get_review_due_days(approval),  # 재심사 D-Day
    )

    # 신규: 동일 성분 유사 품목 조회
    similar_items = []
    if approval and approval.get("MAIN_ITEM_INGR"):
        try:
            from ..api_client import fetch_drug_approval
            similar_resp = fetch_drug_approval(
                item_ingr_name=approval["MAIN_ITEM_INGR"],
                num_of_rows=10
            )
            similar_items = [
                i for i in (similar_resp.get("items") or [])
                if i.get("ITEM_NAME") != approval.get("ITEM_NAME")
            ][:8]
        except Exception:
            pass

    return render_template(
        "app/product_drug.html",
        active_page="search",
        approval=approval,
        disciplinary_items=disciplinary_items,
        recall_items=recall_items,
        identification=identification,
        risk_signal=risk_signal,        # 신규
        similar_items=similar_items,    # 신규
    )

def _get_review_due_days(approval: dict) -> int | None:
    """재심사 만료일까지 남은 일수 계산. 정보 없으면 None."""
    if not approval:
        return None
    # VALID_TERM 또는 별도 재심사 API 데이터 활용
    # 구현 상세는 API 응답 구조에 따라 조정
    pass
```

---

### P6. 제품 상세 (식품) — `/app/product-food/<code>`

#### 4.6.1 현재 문제점 및 리뉴얼 방향

의약품 제품 상세(P5)와 동일한 원칙 적용. 식품 특화 차이점만 명세.

```
[헤더]
  - 품목명 + 제조업체 + 식품 유형
  - 종합 상태: HACCP 인증 여부 + 검사부적합 이력 + 회수 이력

[탭 구성]
  [핵심 정보] [검사·안전 이력] [HACCP 현황] [관련 부적합]

[탭 2: 검사·안전 이력 — 신규]
  - 식품 회수 목록 (food_recall API)
  - 검사부적합 목록 (NO 535, 해당 업체/품목 필터)
  - 각 항목에 심각도 배지

[탭 3: HACCP 현황]
  - HACCP 인증 상태 (스마트 HACCP NO 12 연동)
  - 인증 유형 / 인증일 / 만료일
  - 인증 없음이면 명확히 "미인증" 표시
```

---

### P7. 워크스페이스 (부서별) — `/app/workspace/<dept>`

#### 4.7.1 공통 문제점

| 구분 | 문제 | 처리 |
|------|------|------|
| placeholder "—" 6개 | 실 데이터 있음에도 미연결 | ✅ 전면 연결 |
| KPI 숫자만, 액션 없음 | "7건"인데 뭘 해야 할지 모름 | ✅ 각 KPI에 [바로가기] 추가 |
| 모든 워크스페이스 동일 레이아웃 | 팀별 업무 맥락 무시 | ✅ 팀별 특화 레이아웃 |

#### 4.7.2 RA 워크스페이스 — `/app/workspace/ra`

```
[핵심 변경] KPI 숫자 카드 → D-Day 마감 캘린더 카드

[30일 이내 마감 캘린더]
  ┌──────────┬──────────┬──────────┐
  │ D-12     │ D-28     │ D-45     │
  │ 게피린정  │ 타이레놀정│ 가스디알  │
  │ 재심사    │ 재심사    │ 재평가    │
  │ 서류제출  │ 결과제출  │ 결과제출  │
  │[상세 →]  │[상세 →]  │[상세 →]  │
  └──────────┴──────────┴──────────┘
  표시 조건: D-90일 이내 항목만, 없으면 "마감 임박 항목 없음"

[진행 현황 KPI — 기존 교체]
  - 재심사: 진행 중 N건 / 완료 M건 / D-30 이내 K건
  - 재평가: 진행 중 N건 / 완료 M건
  - 변경허가: 이번 달 신청 N건

[최근 규제 변화]
  - 최근 신규 허가 (permit_new) 5건 목록
  - 각 항목: 품목명 + 허가일 + [상세 →]
```

```python
# workspaces_config.py — RA 섹션 변경
# "kind": "static" → "kind": "deadline_calendar"로 교체

RA_WORKSPACE = {
    "key": "ra",
    "label": "RA (허가·인허가)",
    "sections": [
        {
            "type": "deadline_calendar",
            "title": "30일 이내 마감",
            "api_fn": "fetch_drug_review",    # NO 554
            "deadline_field": "REVIEW_DATE",  # 실제 필드명으로 교체
            "window_days": 90,
        },
        {
            "type": "kpi_row",
            "kpis": [
                {"key": "review",   "label": "재심사 진행", "api": "fetch_drug_review",  "color": "warn"},
                {"key": "reeval",   "label": "재평가 진행", "api": "fetch_drug_reeval",  "color": "info"},
                {"key": "permit_new","label": "신규허가(월)", "api": "fetch_drug_permit","color": "success"},
            ],
        },
    ],
}
```

#### 4.7.3 SCM 워크스페이스 — `/app/workspace/scm`

```
[핵심 추가] 공급부족 영향도 테이블

[공급 리스크 현황 — 기존 KPI 교체]
  - 공급부족: N건 (바로가기: 이벤트 모니터 → type=supply_lack)
  - 판매중지: M건 (바로가기: 이벤트 모니터 → type=supply_stop)
  - 회수 진행: K건 (바로가기: 이벤트 모니터 → type=recall)

[공급부족 품목 상세 테이블 — 신규]
  컬럼: 품목명 | 부족 사유 | 공급 재개 예정일 | 대체 가능 품목 수 | 워치리스트 여부
  - "대체 가능 품목 수"는 동일 성분 품목 수로 계산
  - "워치리스트 여부"는 내 워치리스트와 매칭

[회수 현황 — 기존 유지, 레이아웃 개선]
  - 최근 30일 회수 목록
  - 품목명 · 사유 · 조치기한 · [제품 상세 →]
```

#### 4.7.4 R&D 워크스페이스 — `/app/workspace/rnd`

```
[핵심 추가] 파이프라인 현황 대시보드

[임상시험 현황 — 기존 "—" 교체]
  - 신규 임상 (이번 달): N건
  - 성분별 TOP 3 (클릭 → 이벤트 모니터 → type=clinical_new)
  - 최근 임상 목록 5건: 품목명 · 적응증 · 신청업체 · 신청일

[특허 현황]
  - 이번 달 신규 특허: N건
  - D-365 이내 만료 특허: M건 (클릭 → 상세 목록)

[생동성시험 현황 — 기존 "—" 교체]
  - 진행 중: N건
  - 성분 TOP 3
```

#### 4.7.5 식품QA 워크스페이스 — `/app/workspace/food_qa`

```
[핵심 추가] 부적합 원인 분류 대시보드

[부적합 원인 분류 차트 — 신규]
  도넛 차트 (CSS/SVG 기반, 라이브러리 없이):
    - 잔류농약 N건 (X%)
    - 중금속 M건 (Y%)
    - 미생물 K건 (Z%)
    - 이물·기타 P건 (W%)
  
  데이터 소스: fetch_food_inspect() (NO 535) 결과를 IMPROPT_ITM 필드로 분류

[HACCP 현황 — 기존 "—" 교체]
  - 스마트 HACCP 인증 업체 건수 (NO 12)
  - 광동 협력업체 HACCP 현황 (워치리스트 매칭)

[최근 부적합 목록]
  - 5건, 카드 형태
  - [검사부적합 트래커 전체 보기 →] → /app/inspections
```

---

### P8. 검사부적합 트래커 — `/app/inspections`

#### 4.8.1 계획안 문제점 (Phase 4 계획 보완)

| 구분 | 기존 계획 문제 | 수정 방향 |
|------|--------------|-----------|
| 검색 폼 4개가 첫 화면 | 빈 화면 → 막막함 | 기본값으로 최근 30일 전체 표시 |
| KPI 4종 동등 배치 | "광동 관련"이 핵심인데 묻힘 | 광동 관련 KPI를 1번 위치·2배 크기 |
| 부적합 사유 분류 없음 | 패턴 파악 불가 | 분류 차트 추가 |
| 제조소별 누적 위험도 없음 | 공급업체 재검토 판단 불가 | 제조소 위험 순위 추가 |

#### 4.8.2 정보 구성 요소

```
[1순위 KPI 배너 — 2칸 배치]
  ┌──────────────────────────┬──────────────────────┐
  │ 🔴 광동 관련 부적합        │ 🟡 최근 30일 신규     │
  │      3건 감지              │      47건            │
  │ [워치리스트 매칭 상세 →]  │ [전체 목록 →]         │
  └──────────────────────────┴──────────────────────┘

[2순위 KPI — 4칸 배치]
  ┌──────────┬──────────┬──────────┬──────────┐
  │ 잔류농약  │ 중금속    │ 미생물    │ 이물·기타 │
  │  18건    │  12건    │   9건    │   8건    │
  └──────────┴──────────┴──────────┴──────────┘

[필터 바 — 기본값: 최근 30일 전체]
  - 기간: [최근 30일 ▼] / [최근 90일] / [직접 입력]
  - 부적합 사유: [전체 ▼] / [잔류농약] / [중금속] / [미생물] / [이물]
  - 검색: [제품명 또는 제조소명 검색...]
  - [Excel 내보내기]

[부적합 사유 분류 차트 — 신규]
  - 도넛 또는 가로 바 차트 (JavaScript 최소 구현)
  - 클릭 시 해당 유형 필터 적용

[제조소 위험 순위 — 신규]
  - 제조소명 | 부적합 건수 | 최근 부적합일 | 주요 사유
  - 상위 5개 테이블
  - "이 제조소에서 5건 이상 발생" 시 🔴 배지

[부적합 목록]
  - 광동 관련(워치리스트 매칭) → 빨간 테두리 + 상단 고정
  - 컬럼: 제품명 | 원재료 | 부적합 사유 | 제조소 | 검사일 | [상세]
  - 페이지당 20건, 더보기 방식
```

#### 4.8.3 백엔드 변경 명세

```python
# app_views.py — inspections() 함수 (기존 Phase 4 계획 보완)

@app_bp.route("/inspections")
def inspections():
    from ..api_extras import fetch_food_inspect
    from collections import Counter

    q = (request.args.get("q") or "").strip()
    period = request.args.get("period", "30")  # 기본 30일

    # 전체 데이터 fetch (최대 100건)
    all_items = fetch_food_inspect(num_of_rows=100).get("items", [])

    # 부적합 사유 분류 (IMPROPT_ITM 필드 파싱)
    def classify_reason(reason_text: str) -> str:
        if not reason_text:
            return "기타"
        r = reason_text.lower()
        if "농약" in r or "잔류" in r:
            return "잔류농약"
        if "중금속" in r or "납" in r or "카드뮴" in r:
            return "중금속"
        if "세균" in r or "대장균" in r or "살모넬라" in r:
            return "미생물"
        return "이물·기타"

    reason_counts = Counter(classify_reason(it.get("IMPROPT_ITM", "")) for it in all_items)

    # 제조소별 위험 순위
    factory_counts = Counter(it.get("ENTRPS", "미상") for it in all_items)
    factory_rank = [{"name": k, "count": v} for k, v in factory_counts.most_common(5)]

    # 광동 관련 (워치리스트 매칭)
    kwangdong_items = []
    try:
        wl_entries = watchlist_store.list_entries()
        wl_names = {e["name"].lower() for e in wl_entries}
        kwangdong_items = [
            it for it in all_items
            if any(name in (it.get("PRDUCT") or "").lower() for name in wl_names)
        ]
    except Exception:
        pass

    # 검색 필터 적용
    if q:
        all_items = _filter_items(all_items, q, ["PRDUCT", "ENTRPS", "IMPROPT_ITM", "RAWMTRL_NM"])

    # 광동 관련 상단 고정
    sorted_items = kwangdong_items + [i for i in all_items if i not in kwangdong_items]

    return render_template(
        "app/inspections.html",
        active_page="inspections",
        query=q,
        items=sorted_items[:30],
        kwangdong_count=len(kwangdong_items),
        total_count=len(all_items),
        reason_counts=dict(reason_counts),
        factory_rank=factory_rank,
        recent_30_count=len(all_items),  # 기간 필터 구현 시 교체
    )
```

---

### P9. AI 코파일럿 — `/app/copilot`

#### 4.9.1 현재 문제점

| 구분 | 문제 | 처리 |
|------|------|------|
| 일반 챗봇과 차별점 없음 | 무엇을 물어야 할지 모름 | ✅ 빠른 질문 템플릿 |
| 시스템 맥락 미주입 | RegHub 데이터 모르고 답변 | ✅ 맥락 자동 주입 |
| 대화 결과 저장 불가 | 공유·기록 불가 | ⚠️ 복사 버튼 |

#### 4.9.2 정보 구성 요소

```
[맥락 브리핑 패널 — 자동 주입]
  오늘 시스템 현황:
    · 워치리스트 이벤트 N건
    · 이번 주 회수명령 M건 신규
    · 재심사 D-30일 이내 K건
  → 이 정보가 AI 시스템 프롬프트에 자동으로 포함됨

[빠른 질문 템플릿 — 카테고리별]
  GMP/규제:
    [이번 주 회수 품목 부적합 사유 요약]
    [MFDS GMP 실사 체크리스트 준비사항]
    [재심사 서류 준비 가이드]
  
  경쟁사/시장:
    [최근 신규 허가 경쟁 품목 정리]
    [아세트아미노펜 계열 시장 현황]
  
  공급망:
    [현재 공급부족 품목의 대체재 분석]

[대화창]
  - 입력 → AI 응답 (Anthropic API 연동, MISO 워크플로우 연계)
  - 응답에 [복사] [Slack 공유] 버튼

[시스템 프롬프트 — 백엔드에서 자동 구성]
  "당신은 광동제약 QA/QC팀을 위한 규제정보 전문 어시스턴트입니다.
   현재 시스템 현황:
   - 워치리스트 등록 품목: N개 (이벤트 있음: M개)
   - 오늘 신규 CRITICAL 이벤트: K건
   - 30일 이내 재심사 마감: P건
   
   사용자 질문에 답변 시, 위 맥락을 참고하고 
   식약처 규제 및 GMP 관련 전문 용어를 정확히 사용하세요."
```

---

### P10. 리포트 — `/app/reports`

> Phase 2 예정이지만 정보 구성 설계를 선제적으로 확정.

#### 4.10.1 정보 구성 요소 (상세 구현은 Phase 2)

```
[리포트 유형 선택]
  A. 경영진 요약 리포트 (1페이지)
     - 이번 달 주요 이슈 Top 5
     - 광동 관련 이벤트 건수 추이 (전월 대비)
     - 다음 달 주요 마감 일정

  B. QMR 보고용 데이터 시트
     - 회수·처분·OOS 월별 건수 테이블
     - 동종 업계 대비 현황

  C. GMP 실사 대비 현황 리포트
     - 최근 3년 자사 관련 이벤트 이력
     - 동종 업계 처분 사례 비교

[리포트 생성]
  - 기간 선택 → [미리보기] → [Excel 다운로드] [PDF 다운로드]
  - Phase 2 완료 전까지: "준비 중" 상태 표시 (현재 placeholder 유지)
```

---

## 5. 구현 우선순위 로드맵

### Phase R-1 (즉시 구현 — 1~2일)

> 코드 변경 최소, 임팩트 최대. 기존 기능 깨지지 않음.

| # | 작업 | 파일 | 난이도 |
|---|------|------|--------|
| R1-1 | 전체 템플릿에서 API 번호·domain 태그 제거 | 모든 `.html` 템플릿 | 🟢 |
| R1-2 | 공통 심각도 체계 정의 (`SEVERITY_MAP`) | `watchlist_match.py` | 🟢 |
| R1-3 | 공통 이벤트 카드 매크로 신설 (`_macros.html`) | `templates/_macros.html` | 🟢 |
| R1-4 | 이벤트 날짜 빈값 → "날짜 미확인" 처리 | `app_views.py` `_normalize_event()` | 🟢 |
| R1-5 | 사이드바 메뉴 7개로 확장 (`nav_config.py`) | `nav_config.py` | 🟢 |
| R1-6 | `/app/timeline` → `/app/monitor` 라우트 신설 + redirect | `app_views.py` | 🟢 |
| R1-7 | 이벤트 심각도 정렬 적용 | `app_views.py` `monitor()` | 🟢 |

### Phase R-2 (단기 구현 — 3~5일)

| # | 작업 | 파일 | 난이도 |
|---|------|------|--------|
| R2-1 | `calc_risk_signal()` 헬퍼 함수 신설 | `app_views.py` | 🟡 |
| R2-2 | 통합검색 결과에 위험도 신호등 카드 추가 | `search.html` + `app_views.py` | 🟡 |
| R2-3 | 제품 상세 헤더에 신호등 + 재심사 D-Day 추가 | `product_drug.html` + `app_views.py` | 🟡 |
| R2-4 | 이벤트 모니터에 기간 필터 + NEW 배지 추가 | `monitor.html` + `app_views.py` | 🟡 |
| R2-5 | 워치리스트 위험도 정렬 + 이벤트 인라인 미리보기 | `watchlist.html` + `app_views.py` | 🟡 |
| R2-6 | `summarize_by_severity()` 등 신규 집계 함수 | `watchlist_match.py` | 🟡 |
| R2-7 | 홈 대시보드 신규 페이지 (`/app/home`) | `home.html` + `app_views.py` | 🟡 |
| R2-8 | 워크스페이스 placeholder 6개 실 데이터 연결 | `workspaces_config.py` + `app_views.py` | 🟡 |

### Phase R-3 (중기 구현 — 1~2주)

| # | 작업 | 파일 | 난이도 |
|---|------|------|--------|
| R3-1 | RA 워크스페이스 D-Day 캘린더 재설계 | `workspace.html` + `workspaces_config.py` | 🔴 |
| R3-2 | 제품 상세 — 규제 타임라인 섹션 신설 | `product_drug.html` | 🔴 |
| R3-3 | 제품 상세 — 동일 성분 유사 품목 조회 | `app_views.py` `product_drug()` | 🔴 |
| R3-4 | 검사부적합 트래커 — 부적합 분류 차트 | `inspections.html` + `app_views.py` | 🔴 |
| R3-5 | 워치리스트 Excel 일괄 업로드 | `watchlist.html` + `app_views.py` | 🔴 |
| R3-6 | AI 코파일럿 — 맥락 자동 주입 시스템 프롬프트 | `copilot.html` + `app_views.py` | 🔴 |
| R3-7 | Excel 내보내기 공통 기능 | `app_views.py` + `excel_data_loader.py` | 🔴 |

### Phase R-4 (장기 구현 — Phase 2 범위)

- 리포트 페이지 실구현 (PDF/Excel 생성)
- Slack 웹훅 알림 연동
- 검색 이력 서버사이드 저장
- 워크스페이스 하위 메뉴 accordion 사이드바

---

## 6. 검증 체크리스트

### 6.1 공통 검증

```
□ 전체 페이지에서 "API XXX", "NO XXX" 문자열 검색 → 0건
□ 전체 페이지에서 "domain_kr" 렌더링 → 0건
□ 날짜 빈값 카드에서 "날짜 미확인" 표시 확인
□ 심각도 배지 색상 일관성: 🔴=danger, 🟡=warn, 🟢=success
□ 사이드바 7개 메뉴 전부 표시
□ 모바일(900px 이하) 사이드바 동작 정상
□ 다크모드 토글 후 새로고침 → 유지
```

### 6.2 페이지별 검증

| 페이지 | 검증 항목 |
|--------|-----------|
| **홈** `/app/home` | CRITICAL 이벤트 배너 조건부 표시, 워치리스트 요약 3종 숫자, 마감 일정 D-Day 정확성 |
| **검색** `/` | 검색 전 빈 화면에 이벤트 유도 배너, 검색 후 신호등 카드 표시, 탭 순서 (핵심→규제→외형) |
| **모니터** `/app/monitor` | CRITICAL→HIGH→LOW 순서 정렬, 기간 필터 동작, NEW 배지 오늘 이벤트, 워치리스트 매칭 배지 |
| **워치리스트** `/app/watchlist` | 위험도 정렬, 이벤트 인라인 미리보기 접기/펼치기, 요약 패널 3종 숫자 |
| **제품상세** `/app/product/<code>` | 헤더 신호등, 탭 순서 (핵심→규제→안전→관련→외형), 동일 성분 품목 표시 |
| **RA 워크스페이스** | D-Day 캘린더 표시, placeholder "—" 0건 |
| **SCM 워크스페이스** | 공급부족 테이블, placeholder "—" 0건 |
| **R&D 워크스페이스** | 임상·특허·생동성 실 건수 표시, placeholder "—" 0건 |
| **식품QA 워크스페이스** | 부적합 분류 차트, HACCP 건수 표시 |
| **검사부적합** `/app/inspections` | 광동 관련 KPI 1번 위치, 분류 차트 표시, 광동 매칭 항목 상단 고정 |
| **AI 코파일럿** | 시스템 현황 브리핑 패널 표시, 빠른 질문 템플릿 동작 |

### 6.3 회귀 테스트

```
□ 기존 검색 기능 동작 확인: /?q=광동제약
□ /app/timeline → /app/monitor 301 redirect 확인
□ /app/watchlist 품목 추가·제거 동작
□ /app/copilot 대화 동작
□ /healthz → {"ok": true} 200 OK
□ 404 페이지 에러 핸들러 동작
□ API 타임아웃(30초) 시 graceful 처리 (에러 메시지 표시)
```

---

## 7. 비-목표

> 이번 리뉴얼 범위에 **포함하지 않는** 항목. 별도 Phase로 처리.

- HTMX/SPA 라우팅 도입
- 사용자 인증·세션 (user_info는 nav_config.py 하드코딩 유지)
- Slack 웹훅 실알림 연동 (UI 버튼만, 실발송은 다음 사이클)
- PDF/Excel 리포트 실생성 (Phase 2)
- 워크스페이스 하위 메뉴 accordion (Phase 2)
- 검색 자동완성 (서버사이드 API 추가 필요)
- 마약류 통계 대시보드 (NO 81)
- 사용자별 설정 저장 (DB 필요)
- 외부 LIMS 연동

---

*문서 끝 — RegHub 360 리뉴얼 명세서 v1.0*  
*작성: 품질관리2팀 AI TF (MISO-52g TF)*
