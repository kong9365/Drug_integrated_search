"""
KD-IRIS — 부서별 워크스페이스 단일 설정

7개 부서(RA · QA/QC · SCM · 영업 · R&D · 식품QA · 경영진)의
관심 카테고리 / KPI / 빠른 액션을 한 곳에서 관리.

# ────────────────────────────────────────────────────────────────────────
# 부서별 활용 API 매핑 (Phase M-5 대비 — 설계 수용성 주석. 실제 뷰 구현은 M-5)
#   같은 공공데이터·enrich/모니터링 엔진을 부서 '뷰'로만 확장한다는 원칙(스펙 §8.3).
#   아래는 각 부서가 향후 연결할 이미 승인된 API 키 목록(로직 변경 없이 참조용):
#     RA(허가·인허가)   → NO 554(재심사) · 556(재평가) · 132(GMP) · 140(허가)
#     법무·특허          → NO 561(특허) · 557(국내소송) · 552(FDA P4) · 562(FDA 오렌지북)
#     SCM·생산관리       → NO 534(공급중단) · 537(공급부족) · 142(국가출하) · 생산실적
#     R&D·BD            → NO 566(임상) · 568(임상기관) · 484(대조약) · 485(생동성) · 483(DMF)
#     약물감시(PV)       → NO 547(안전성서한) · 531/533(DUR) · 이상사례
#     식품QA            → 식품 생산실적 · HACCP(12) · 건기식 GMP(51) · 검사부적합(535) · 식품행정처분(3·5·6)
#   ※ api_extras 의 해당 fetch 함수는 이미 부서 중립(QA 종속 X) → 그대로 재사용.
# ────────────────────────────────────────────────────────────────────────

각 부서는 동일한 동적 템플릿(`app/workspace.html`)으로 렌더되며,
이 파일의 메타데이터에 따라 표시 내용이 달라진다.

스키마:
  id           : URL 슬러그 (예: "ra", "qa", "scm")
  label        : 표시명 (예: "RA — 인허가")
  short_label  : 사이드바 표시명 (짧게)
  accent       : CSS 변수 키 (brand|info|warn|ok|danger|domain-drug|domain-food)
  description  : 1-2줄 설명
  icon_svg     : 24x24 SVG path/shape inner markup
  event_kinds  : 이 부서가 관심 갖는 이벤트 종류 list
                 (recall · safety · sanction · supply · new_permit · inspection · food_recall · gmp · clinical)
  kpi_specs    : KPI 카드 4개 정의 [(label, kind, color_class), ...]
  actions      : 빠른 액션 (label, href) 튜플 리스트
"""

WORKSPACES = [
    {
        "id": "ra",
        "label": "RA — 인허가",
        "short_label": "RA",
        "accent": "brand",
        "description": "신규 허가·변경·재심사·재평가 일정과 안전성서한 반영 현황을 한눈에.",
        "icon_svg": '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
        "event_kinds": ["new_permit", "safety", "sanction", "review"],
        "kpi_specs": [
            {"key": "new_permit", "label": "신규 허가 90일", "kind": "count", "color": "brand"},
            {"key": "safety",     "label": "안전성서한",     "kind": "count", "color": "warn"},
            {"key": "sanction",   "label": "행정처분",      "kind": "count", "color": "warn"},
            {"key": "review",     "label": "재심사",        "kind": "count", "color": "warn"},
        ],
        "actions": [
            {"label": "이번 분기 자사 허가 변경 정리", "href": "/app/copilot"},
            {"label": "재심사 예정 품목 보기",        "href": "/?q=재심사"},
            {"label": "안전성서한 반영 현황",         "href": "/app/timeline"},
        ],
    },
    {
        "id": "qa",
        "label": "QA/QC — 품질",
        "short_label": "QA/QC",
        "accent": "info",
        "description": "자사·동성분 회수, GMP 적합판정, DUR 금기 변동, 검사부적합을 추적.",
        "icon_svg": '<circle cx="12" cy="12" r="10"/><path d="M8 12l3 3 5-7"/>',
        "event_kinds": ["recall", "safety", "gmp", "inspection"],
        "kpi_specs": [
            {"key": "recall",     "label": "회수·판매중지", "kind": "count", "color": "danger"},
            {"key": "safety",     "label": "안전성서한",   "kind": "count", "color": "warn"},
            {"key": "sanction",   "label": "행정처분",     "kind": "count", "color": "warn"},
            {"key": "gmp_status", "label": "자사 GMP",     "kind": "static", "color": "ok",   "value": "정상"},
        ],
        "actions": [
            {"label": "베니톨정 동성분 회수 분석",   "href": "/app/copilot"},
            {"label": "최근 안전성서한",            "href": "/app/timeline"},
            {"label": "DUR 병용금기 점검",          "href": "/?q=베니톨정"},
        ],
    },
    {
        "id": "scm",
        "label": "SCM — 공급망",
        "short_label": "SCM",
        "accent": "warn",
        "description": "공급중단·공급부족·수입 회수와 원재료 부적합을 모니터.",
        "icon_svg": '<path d="M3 9h18M3 15h18M3 3h18v18H3z"/><circle cx="12" cy="12" r="3"/>',
        "event_kinds": ["supply", "supply_lack", "food_recall", "inspection"],
        "kpi_specs": [
            {"key": "supply",     "label": "공급중단",        "kind": "count", "color": "danger"},
            {"key": "supply_lack","label": "공급부족",        "kind": "count", "color": "warn"},
            {"key": "food_recall","label": "수입식품 회수",  "kind": "count", "color": "danger"},
            {"key": "inspection", "label": "검사부적합",     "kind": "count", "color": "warn"},
        ],
        "actions": [
            {"label": "원재료 잔류농약 부적합 추적", "href": "/app/copilot"},
            {"label": "수입식품 회수 보기",          "href": "/?q=수입식품"},
            {"label": "공급중단 의약품 검색",        "href": "/?q=공급중단"},
        ],
    },
    {
        "id": "sales",
        "label": "영업 — 시장 동향",
        "short_label": "영업",
        "accent": "domain-drug",
        "description": "경쟁사 행정처분·신규 허가·회수가 영업 라인에 미치는 영향을 추적.",
        "icon_svg": '<path d="M3 3v18h18"/><path d="M7 14l4-4 4 4 6-6"/>',
        "event_kinds": ["sanction", "new_permit", "recall"],
        "kpi_specs": [
            {"key": "sanction",   "label": "경쟁사 행정처분", "kind": "count", "color": "warn"},
            {"key": "new_permit", "label": "타사 신규 허가",  "kind": "count", "color": "brand"},
            {"key": "recall",     "label": "동성분 회수",     "kind": "count", "color": "danger"},
            {"key": "share",      "label": "자사 점유율",     "kind": "static","color": "ok", "value": "—"},
        ],
        "actions": [
            {"label": "경쟁사 A제약 신규 허가 요약", "href": "/app/copilot"},
            {"label": "이번 분기 행정처분 TOP",      "href": "/app/timeline"},
            {"label": "동아 검색 →",                "href": "/?q=동아"},
        ],
    },
    {
        "id": "rnd",
        "label": "R&D — 개발·BD",
        "short_label": "R&D",
        "accent": "brand",
        "description": "특허·임상시험·대조약·생동성·FDA 오렌지북 등 R&D 인사이트 통합.",
        "icon_svg": '<path d="M9 2v6L4 13a3 3 0 0 0 3 5h10a3 3 0 0 0 3-5L15 8V2"/><path d="M8 2h8"/>',
        "event_kinds": ["clinical", "new_permit", "patent", "bioeq"],
        "kpi_specs": [
            {"key": "clinical",   "label": "임상시험",       "kind": "count", "color": "brand"},
            {"key": "patent",     "label": "특허 등록",     "kind": "count", "color": "warn"},
            {"key": "new_permit", "label": "타사 신규 허가", "kind": "count", "color": "info"},
            {"key": "bioeq",      "label": "생동성 인정",    "kind": "count", "color": "ok"},
        ],
        "actions": [
            {"label": "아세트아미노펜 R&D 인사이트",  "href": "/?q=아세트아미노펜"},
            {"label": "임상시험 현황 (NO 566)",       "href": "/?q=임상"},
            {"label": "FDA 오렌지북 매칭",            "href": "/app/copilot"},
        ],
    },
    {
        "id": "food_qa",
        "label": "식품QA — 식품·건기식",
        "short_label": "식품QA",
        "accent": "domain-food",
        "description": "식품 검사부적합·행정처분·표시기준 위반·HACCP 인증 상태.",
        "icon_svg": '<path d="M6 13.87A4 4 0 0 1 7.41 6a5.11 5.11 0 0 1 1.05-1.54 5 5 0 0 1 7.08 0A5.11 5.11 0 0 1 16.59 6 4 4 0 0 1 18 13.87V21H6z"/><path d="M9 21v-3M15 21v-3"/>',
        "event_kinds": ["inspection", "food_recall", "sanction", "haccp_smart"],
        "kpi_specs": [
            {"key": "inspection", "label": "검사부적합",       "kind": "count", "color": "danger"},
            {"key": "food_recall","label": "수입식품 회수",   "kind": "count", "color": "warn"},
            {"key": "sanction",   "label": "식품 행정처분",   "kind": "count", "color": "warn"},
            {"key": "haccp_smart","label": "스마트HACCP",     "kind": "count", "color": "ok"},
        ],
        "actions": [
            {"label": "비타500 표시기준 처분 사유",   "href": "/app/copilot"},
            {"label": "건기식 GMP 확인",            "href": "/?q=건기식"},
            {"label": "식품 검사부적합 TOP",        "href": "/?q=검사부적합"},
        ],
    },
    {
        "id": "exec",
        "label": "경영진 — 통합 KPI",
        "short_label": "경영진",
        "accent": "domain-drug",
        "description": "전체 도메인 통합 Risk Score·이벤트 총량·부서별 알림 요약.",
        "icon_svg": '<rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>',
        "event_kinds": ["recall", "safety", "sanction", "supply", "inspection"],
        "kpi_specs": [
            {"key": "all_alerts", "label": "전체 알림",     "kind": "count", "color": "danger"},
            {"key": "recall",     "label": "회수·판매중지", "kind": "count", "color": "danger"},
            {"key": "sanction",   "label": "행정처분",     "kind": "count", "color": "warn"},
            {"key": "watchlist",  "label": "워치리스트",    "kind": "watchlist_count", "color": "brand"},
        ],
        "actions": [
            {"label": "이번 주 통합 브리핑 생성",      "href": "/app/copilot"},
            {"label": "리포트 카탈로그",              "href": "/app/reports"},
            {"label": "타임라인 보기",                "href": "/app/timeline"},
        ],
    },
]


def by_id(dept_id: str):
    """슬러그로 부서 메타 조회."""
    for w in WORKSPACES:
        if w["id"] == dept_id:
            return w
    return None
