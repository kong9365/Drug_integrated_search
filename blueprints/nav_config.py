"""
KD-IRIS — 사이드바 메뉴 / 사용자 정보 단일 설정

품목마스터 중심 재설계 (Phase M-nav): 메뉴를 3개 그룹으로 재편.
  ■ 품질관리 (core)  : 오늘의 브리핑 · 품목마스터 · 연간품질평가(APQR) · 규제 모니터링
  ■ 조회 도구 (tools): 제품·업체 조회 · 내 워치리스트 · AI 코파일럿
  ■ PoC (poc)        : 워크스페이스 · 검사부적합 · 리포트  (타 부서 시범 — 로직 동결)

각 항목의 "group" 키로 _layout.html 사이드바에서 그룹 헤더와 함께 렌더한다.
"""

NAV_ITEMS = [
    # ── 품질관리 (core) ───────────────────────────────────────────────
    {
        "key": "home", "group": "core",
        "label": "오늘의 브리핑", "href": "/app/home",
        "icon_svg": '<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>',
        "badge": None, "disabled": False,
    },
    {
        "key": "qa", "group": "core",
        "label": "품목마스터", "href": "/app/qa/master",
        "icon_svg": '<path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>',
        # inject_nav() 에서 오늘 신규 CRITICAL 건수 동적 주입
        "badge": None, "disabled": False,
    },
    {
        "key": "official", "group": "core",
        "label": "광동 허가 현황", "href": "/app/qa/official",
        "icon_svg": '<path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>',
        "badge": None, "disabled": False,
    },
    {
        "key": "apqr", "group": "core",
        "label": "연간품질평가", "href": "/app/qa/apqr",
        "icon_svg": '<path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>',
        "badge": {"kind": "brand", "text": "NEW"}, "disabled": False,
    },
    {
        "key": "monitor", "group": "core",
        "label": "규제 모니터링", "href": "/app/monitor",
        "icon_svg": '<path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>',
        # inject_nav() 에서 today_critical_count 동적 주입
        "badge": None, "disabled": False,
    },

    # ── 조회 도구 (tools) ─────────────────────────────────────────────
    {
        "key": "search", "group": "tools",
        "label": "제품·업체 조회", "href": "/",
        "icon_svg": '<path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>',
        "badge": None, "disabled": False,
    },
    {
        "key": "watchlist", "group": "tools",
        "label": "내 워치리스트", "href": "/app/watchlist",
        "icon_svg": '<path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>',
        "badge": None, "disabled": False,
    },
    {
        "key": "copilot", "group": "tools",
        "label": "AI 코파일럿", "href": "/app/copilot",
        "icon_svg": '<path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>',
        "badge": None, "disabled": False,
    },

    # ── PoC · 타 부서 시범 (poc) — 로직 동결, 메뉴 PoC 배지만 ────────────
    {
        "key": "workspace", "group": "poc",
        "label": "워크스페이스", "href": "/app/workspace",
        "icon_svg": '<path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>',
        "badge": {"kind": "muted", "text": "PoC"}, "disabled": False,
        "children": [
            {"key": "ws_ra",      "label": "RA (허가·인허가)", "href": "/app/workspace/ra"},
            {"key": "ws_scm",     "label": "SCM (공급망)",     "href": "/app/workspace/scm"},
            {"key": "ws_rnd",     "label": "R&D",              "href": "/app/workspace/rnd"},
            {"key": "ws_food_qa", "label": "식품QA",           "href": "/app/workspace/food_qa"},
            {"key": "ws_sales",   "label": "영업",             "href": "/app/workspace/sales"},
        ],
    },
    {
        "key": "inspections", "group": "poc",
        "label": "검사부적합", "href": "/app/inspections",
        "icon_svg": '<path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>',
        "badge": {"kind": "muted", "text": "PoC"}, "disabled": False,
    },
    {
        "key": "reports", "group": "poc",
        "label": "리포트·내보내기", "href": "/app/reports",
        "icon_svg": '<path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>',
        "badge": {"kind": "muted", "text": "PoC"}, "disabled": False,
    },
]

# 사이드바 그룹 헤더 (순서·라벨) — _layout.html 에서 사용
NAV_GROUPS = [
    ("core", "품질관리"),
    ("tools", "조회 도구"),
    ("poc", "PoC · 타 부서 시범"),
]

USER_INFO = {
    "initials": "KQ",
    "name": "김QA",
    "team": "광동제약 · QA/QC팀",
}
