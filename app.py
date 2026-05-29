"""
KD-IRIS — Flask 메인 애플리케이션 (KwangDong Integrated Regulatory Intelligence System)
의약품·의약외품·식품 통합 규제정보 허브

Blueprint 구조:
  - landing_bp : / (랜딩) , /docs/handoff
  - app_bp     : /app/* (9개 화면)
  - api_bp     : /api/* (기존 검색·허가·식별 API + 신규 추가 예정)
"""
import logging
from flask import Flask, jsonify, request

from .config import BASE_DIR, STATIC_FOLDER, LOG_DIR, SECRET_KEY
from .blueprints import landing_bp, app_bp, api_bp, api_demo_bp
from .blueprints.qa import qa_bp
from .blueprints.qa import db as qa_db
from .blueprints.nav_config import NAV_ITEMS, USER_INFO
from .blueprints.workspaces_config import WORKSPACES
from .blueprints import watchlist_store, watchlist_match

# ────────────────────────────────────────────────────────────────────────────
# 로깅
# ────────────────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────
# Flask 앱 생성 + Blueprint 등록
# ────────────────────────────────────────────────────────────────────────────
TEMPLATE_FOLDER = BASE_DIR / "templates"

app = Flask(
    __name__,
    static_folder=str(STATIC_FOLDER),
    template_folder=str(TEMPLATE_FOLDER),
)
app.config["SECRET_KEY"] = SECRET_KEY

# Blueprint 등록
app.register_blueprint(landing_bp)
app.register_blueprint(app_bp)
app.register_blueprint(api_bp)
app.register_blueprint(api_demo_bp)
app.register_blueprint(qa_bp)  # KD-IRIS 1차 빌드 — 의약품QA (/app/qa/*)

# SQLite 스키마 초기화 (멱등 — 부팅 시 1회)
try:
    qa_db.init_db()
except Exception as _e:
    logger.warning(f"QA DB init 실패(앱은 계속): {_e}")


# ────────────────────────────────────────────────────────────────────────────
# 공통 컨텍스트 — 모든 템플릿(_layout.html 포함)에 nav_items / user_info 주입
# ────────────────────────────────────────────────────────────────────────────
@app.context_processor
def inject_nav():
    # 워치리스트 등록·매칭 카운트를 사이드바 배지에 동적으로 반영.
    # 매칭 API 결과는 watchlist_match 모듈 안에서 5분 TTL 캐시됨 → 페이지마다 추가 호출 거의 없음.
    wl_count = 0
    wl_critical = 0      # CRITICAL 이벤트 보유 워치리스트 항목 수 (v3 R2-7)
    monitor_critical = 0  # 오늘 신규 CRITICAL(공공 회수) 건수 (v3 R2-7)
    try:
        wl_count = watchlist_store.count()
        if wl_count > 0:
            entries = watchlist_store.list_entries()
            match_map = watchlist_match.match_for_entries(entries)
            wl_critical = watchlist_match.critical_alert_count(match_map)
    except Exception as e:
        logger.warning(f"inject_nav 워치리스트 카운트 계산 실패: {e}")

    try:
        monitor_critical = watchlist_match.today_critical_count()
    except Exception as e:
        logger.debug(f"inject_nav monitor critical 계산 실패: {e}")

    # 의약품QA — 미확인 CRITICAL 이벤트 수 배지 (v2 백본, SQLite 기준)
    qa_critical = 0
    try:
        from .blueprints.qa.views import today_critical_count
        qa_critical = today_critical_count()
    except Exception as e:
        logger.debug(f"QA critical count 계산 실패: {e}")

    items = []
    for it in NAV_ITEMS:
        if it["key"] == "watchlist":
            if wl_critical > 0:
                # CRITICAL 이벤트 보유 항목이 있으면 danger 배지로 알림
                it = {**it, "badge": {"kind": "danger", "text": str(wl_critical)}}
            elif wl_count > 0:
                # 등록만 되어 있으면 brand 배지로 건수 표시
                it = {**it, "badge": {"kind": "brand", "text": str(wl_count)}}
        elif it["key"] == "monitor" and monitor_critical > 0:
            # 오늘 신규 CRITICAL 회수가 있으면 danger 배지
            it = {**it, "badge": {"kind": "danger", "text": str(monitor_critical)}}
        elif it["key"] == "qa" and qa_critical > 0:
            # 미확인 CRITICAL 이벤트가 있으면 danger 배지
            it = {**it, "badge": {"kind": "danger", "text": str(qa_critical)}}
        items.append(it)
    return {
        "nav_items": items,
        "workspaces": WORKSPACES,
        "user_info": USER_INFO,
    }


# ────────────────────────────────────────────────────────────────────────────
# 에러 핸들러
# ────────────────────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(error):
    # API 경로는 JSON, 그 외는 랜딩 페이지로 폴백
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "엔드포인트를 찾을 수 없습니다."}), 404
    return jsonify({"success": False, "error": "페이지를 찾을 수 없습니다.",
                    "hint": "URL을 확인하거나 / (랜딩) 또는 /app 으로 이동하세요."}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"서버 오류: {error}")
    return jsonify({"success": False, "error": "서버 오류가 발생했습니다."}), 500


# ────────────────────────────────────────────────────────────────────────────
# 헬스 체크
# ────────────────────────────────────────────────────────────────────────────
@app.route("/healthz")
def health():
    return jsonify({"ok": True, "service": "KD-IRIS", "version": "1.0.0-mvp"})


# ────────────────────────────────────────────────────────────────────────────
# 직접 실행
# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, io
    # Windows 콘솔 UTF-8 강제 (cp949 인코딩 회피)
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    print("=" * 60)
    print("KD-IRIS - 광동 의약품/식품 통합 규제정보 허브")
    print("=" * 60)
    print("서버 시작...")
    print("브라우저에서 http://localhost:5005 을 열어주세요.")
    print("=" * 60)
    # 모니터링 야간 배치 스케줄러 (서빙 진입점에서만 기동)
    try:
        from .blueprints.qa.scheduler import start_scheduler
        start_scheduler()
    except Exception as _e:
        logger.warning(f"스케줄러 기동 실패(앱은 계속): {_e}")
    app.run(debug=True, host="0.0.0.0", port=5005, use_reloader=False)
