"""
KD-IRIS — 사이드바 메뉴 / 사용자 정보 단일 설정

모든 페이지가 _layout.html을 통해 동일한 사이드바를 렌더하므로
메뉴를 바꾸려면 이 파일만 수정.

7개 메뉴 (업무 맥락 중심):
  🏠 오늘의 브리핑   /app/home
  🔍 제품·업체 조회   /
  🚨 이벤트 모니터    /app/monitor
  👁 내 워치리스트    /app/watchlist
  🏢 워크스페이스    /app/workspace (children 5개)
  🔬 검사부적합      /app/inspections
  🤖 AI 코파일럿     /app/copilot
  📊 리포트·내보내기 /app/reports (Phase 2, disabled)
"""

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
        # inject_nav() 에서 today_critical_count 동적 주입 (R2-7)
        "badge": None,
        "disabled": False,
    },
    {
        "key": "watchlist",
        "label": "내 워치리스트",
        "href": "/app/watchlist",
        "icon_svg": '<path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>',
        "badge": None,  # inject_nav() 동적
        "disabled": False,
    },
    {
        "key": "workspace",
        "label": "워크스페이스",
        "href": "/app/workspace",
        "icon_svg": '<path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>',
        "badge": None,
        "disabled": False,
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
        "key": "copilot",
        "label": "AI 코파일럿",
        "href": "/app/copilot",
        "icon_svg": '<path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>',
        "badge": {"kind": "brand", "text": "NEW"},
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
]

USER_INFO = {
    "initials": "KQ",
    "name": "김QA",
    "team": "광동제약 · QA/QC팀",
}
