"""
RegHub 360 — 메인 진입 Blueprint
/ : 통합 검색 페이지 (이미지와 동일 — 사이드바 + KPI 8종 + 대표 품목 + 안전성 이벤트)
/docs/handoff : 개발자 핸드오프 문서
"""
from pathlib import Path
from flask import Blueprint, render_template, send_from_directory, abort

from ..config import BASE_DIR

landing_bp = Blueprint("landing", __name__)


@landing_bp.route("/")
def index():
    """메인 진입 — 통합 검색 페이지 (app_views.search 로직 그대로)."""
    # Avoid circular import — lazy import
    from .app_views import search as app_search
    return app_search()


@landing_bp.route("/docs/handoff")
def handoff():
    """개발자 핸드오프 문서 (Markdown 원문 그대로 제공)."""
    docs_dir = BASE_DIR / "docs"
    if not (docs_dir / "HANDOFF.md").exists():
        abort(404)
    return send_from_directory(str(docs_dir), "HANDOFF.md", mimetype="text/markdown; charset=utf-8")
