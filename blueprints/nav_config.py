"""
RegHub 360 — 사이드바 메뉴 / 사용자 정보 단일 설정
모든 페이지가 _layout.html을 통해 동일한 사이드바를 렌더하므로
메뉴를 바꾸려면 이 파일만 수정.
"""

# 사이드바 메뉴 항목.
# - key       : 활성 표시 매칭용 (active_page 컨텍스트와 비교)
# - label     : 표시 텍스트
# - href      : 링크 (disabled 면 None)
# - icon_svg  : 사이드바에 들어가는 SVG path/shape 마크업 (24x24 viewBox)
# - badge     : {"kind": "danger|brand|muted", "text": "..."} 또는 None
# - disabled  : 비활성(클릭 불가) 표시
NAV_ITEMS = [
    {
        "key": "search",
        "label": "통합 검색",
        "href": "/",
        "icon_svg": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
        "badge": None,
        "disabled": False,
    },
    {
        "key": "timeline",
        "label": "이벤트 타임라인",
        "href": "/app/timeline",
        "icon_svg": '<path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0zM12 7v5l3 2"/>',
        "badge": {"kind": "danger", "text": "7"},
        "disabled": False,
    },
    {
        "key": "watchlist",
        "label": "워치리스트",
        "href": "/app/watchlist",
        "icon_svg": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
        "badge": None,
        "disabled": False,
    },
    {
        "key": "reports",
        "label": "리포트",
        "href": "/app/reports",
        "icon_svg": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>',
        "badge": None,
        "disabled": False,
    },
    {
        "key": "copilot",
        "label": "AI 코파일럿",
        "href": "/app/copilot",
        "icon_svg": '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>',
        "badge": {"kind": "brand", "text": "NEW"},
        "disabled": False,
    },
]

USER_INFO = {
    "initials": "KQ",
    "name": "김QA",
    "team": "광동제약 · QA/QC팀",
}
