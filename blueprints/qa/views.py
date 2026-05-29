"""
KD-IRIS 1차 빌드 — 의약품QA 라우트 (기능재설계 v2 §11.6)

라우트:
  /app/qa/home              — QA 대시보드 (S2-2에서 완성, 현재 마스터로 redirect)
  /app/qa/master            — 마스터 검토 (P2) : 검색·필터·enrich 결과
  /app/qa/master/<code>     — 품목 상세 (사내 vs 공공)
  POST /app/qa/master/enrich       — Enrichment 백그라운드 실행
  GET  /app/qa/master/enrich/status — 진행률 폴링 (JSON)
  POST /app/qa/master/confirm      — review 후보 confirm/reject
  /app/qa/healthz           — 모듈 헬스
"""
import datetime
import logging

from flask import (jsonify, redirect, render_template, request, url_for)

from . import qa_bp
from . import db as qadb
from . import enrichment as enr
from ..severity import get_severity, SEVERITY_ORDER

logger = logging.getLogger(__name__)

_FINISHED_CATS = ["전문의약품", "일반의약품", "의약외품", "향정신성의약품", "식품", "기타"]


# ────────────────────────────────────────────────────────────────────────────
@qa_bp.route("/home")
def qa_home():
    """품목마스터 랜딩 = 목록(master)로 redirect. (KPI 대시보드는 '오늘의 브리핑'이 담당)"""
    return redirect(url_for("qa.master"))


@qa_bp.route("/master")
def master():
    """마스터 검토 페이지 (P2)."""
    q = (request.args.get("q") or "").strip()
    f_cat = (request.args.get("cat") or "").strip()
    f_status = (request.args.get("status") or "").strip()
    f_herbal = (request.args.get("herbal") or "").strip()  # '' | '1'(한약) | '0'(비한약)
    tab = (request.args.get("tab") or "all").strip()  # all | review

    where = ["active=1"]
    params = []
    if q:
        where.append("(item_name LIKE ? OR item_code LIKE ? OR item_name_alt LIKE ? OR item_seq LIKE ?)")
        params += [f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"]
    if f_cat:
        where.append("category = ?")
        params.append(f_cat)
    if f_status:
        where.append("enrich_status = ?")
        params.append(f_status)
    if f_herbal in ("0", "1"):
        where.append("is_herbal = ?")
        params.append(int(f_herbal))
    if tab == "review":
        where.append("enrich_status = 'review'")

    sql = f"""SELECT item_code, item_name, item_name_alt, category, sub_category,
                     gubun, self_or_consign, is_herbal, item_seq, permit_no, permit_date,
                     reexam_date, atc_code, edi_code, source_api,
                     enrich_status, enrich_confidence, enrich_candidates
              FROM master_item WHERE {' AND '.join(where)}
              ORDER BY enrich_status='review' DESC, item_code LIMIT 1000"""
    items = qadb.query(sql, tuple(params))
    for it in items:
        it["candidates"] = qadb.jload(it.get("enrich_candidates"), [])

    # 위험도 맵 (1회 쿼리) — event.matched_item_codes JSON → item_code별 최고 severity
    sev_rank = {"CRITICAL": 0, "HIGH": 1, "LOW": 2}
    event_map = {}
    try:
        for ev in qadb.query("SELECT severity, matched_item_codes FROM event WHERE status!='closed'"):
            for code in (qadb.jload(ev.get("matched_item_codes"), []) or []):
                cur = event_map.get(code)
                if cur is None or sev_rank.get(ev["severity"], 3) < sev_rank.get(cur, 3):
                    event_map[code] = ev["severity"]
    except Exception as e:
        logger.debug(f"master event_map 실패: {e}")

    return render_template(
        "app/qa/master.html",
        active_page="qa",
        items=items,
        stats=_master_stats(),
        categories=_FINISHED_CATS,
        event_map=event_map,
        q=q, f_cat=f_cat, f_status=f_status, f_herbal=f_herbal, tab=tab,
        progress=enr.get_progress(),
    )


# 9탭 정의 (품목마스터 상세) — 데이터 탭 + SAP/EDMS 연동대기 placeholder
_PM_TABS = [
    ("ingredient", "원약분량", "data"),
    ("approval_detail", "허가상세", "data"),
    ("packaging", "포장단위", "data"),
    ("pkg_material", "포장자재", "pending"),
    ("reg_event", "규제 이벤트", "data"),
    ("related", "관련 품목", "data"),
    ("std_doc", "제품표준서", "pending"),
    ("equipment", "설비", "pending"),
    ("finished", "완제품", "pending"),
    ("pv", "PV현황", "pending"),
    ("cv", "CV현황", "pending"),
    ("consign", "수탁제품", "pending"),
]


@qa_bp.route("/master/<code>")
def master_detail(code):
    """품목마스터 9탭 상세 — 헤더+원약분량+포장+규제이벤트+관련품목+위험신호등+enrich confirm."""
    item = qadb.query_one("SELECT * FROM master_item WHERE item_code=?", (code,))
    if not item:
        return jsonify({"error": "품목 없음"}), 404
    item["candidates"] = qadb.jload(item.get("enrich_candidates"), [])
    ingredients = qadb.query("SELECT * FROM master_ingredient WHERE item_code=?", (code,))
    packaging = qadb.query("SELECT * FROM master_packaging WHERE item_code=?", (code,))
    # 규제 이벤트 / 관련 품목 (lookup 재사용 — event.matched_item_codes 기반)
    reg_events, related = [], []
    try:
        from . import lookup as qa_lookup
        reg_events = qa_lookup.events_for_item(code, limit=30)
        related = qa_lookup.same_ingredient_products(code, limit=8)
    except Exception as e:
        logger.debug(f"master_detail lookup 실패: {e}")
    # 위험 신호등 (risk.py 재사용)
    signal = None
    try:
        from ..risk import calc_risk_signal
        recalls = [e for e in reg_events if e.get("event_type") == "recall"]
        discs = [e for e in reg_events if e.get("event_type") == "disciplinary"]
        signal = calc_risk_signal(approval_data=[item], disciplinary_items=discs,
                                  recall_items=recalls, review_due_days=None)
    except Exception as e:
        logger.debug(f"master_detail 신호등 실패: {e}")
    # 허가상세 (NO 140 상세, getDrugPrdtPrmsnDtlInq06) — 효능효과·용법용량·주의사항·42필드
    # best-effort 라이브 조회 (item_seq 우선, 폴백 edi_code). 실패 시 None → 템플릿이 안내문 표시.
    detail = None
    try:
        from ...api_client import fetch_approval_detail
        if item.get("item_seq"):
            dr = fetch_approval_detail(item_seq=item["item_seq"], num_of_rows=1)
        elif item.get("edi_code"):
            dr = fetch_approval_detail(edi_code=item["edi_code"], num_of_rows=1)
        else:
            dr = None
        if dr and dr.get("items"):
            detail = dr["items"][0]
    except Exception as e:
        logger.debug(f"master_detail NO140 상세 조회 실패: {e}")
    # 낱알 이미지 (best-effort, matched 품목만)
    pill = None
    try:
        from ...api_client import fetch_identification
        nm = (item.get("item_name") or "").split("(")[0]
        if nm and item.get("enrich_status") == "matched":
            idr = fetch_identification(item_name=nm, num_of_rows=1)
            if idr.get("items"):
                pill = idr["items"][0].get("ITEM_IMAGE")
    except Exception:
        pass
    return render_template("app/qa/master_detail.html", active_page="qa",
                           item=item, ingredients=ingredients, packaging=packaging,
                           reg_events=reg_events, related=related, signal=signal,
                           detail=detail, pill_image_url=pill, tabs=_PM_TABS,
                           can_apqr=(item.get("enrich_status") == "matched"),
                           flash_msg=request.args.get("msg") or "")


@qa_bp.route("/master/enrich", methods=["POST"])
def master_enrich():
    """Enrichment 백그라운드 실행 (전체 pending/review/unmatched)."""
    only_pending = request.form.get("scope", "pending") != "all"
    started = enr.run_enrichment_async(only_pending=only_pending)
    if not started:
        return redirect(url_for("qa.master") + "?msg=already_running")
    return redirect(url_for("qa.master") + "?msg=started")


@qa_bp.route("/master/enrich/status")
def master_enrich_status():
    """진행률 폴링 (JSON)."""
    return jsonify(enr.get_progress())


@qa_bp.route("/master/confirm", methods=["POST"])
def master_confirm():
    """review 후보 confirm(특정 ITEM_SEQ 선택) 또는 reject(unmatched 확정)."""
    code = request.form.get("item_code")
    action = request.form.get("action")  # 'confirm' | 'reject'
    item_seq = request.form.get("item_seq")

    if not code:
        return jsonify({"ok": False, "error": "item_code 필요"}), 400

    if action == "reject":
        qadb.execute(
            "UPDATE master_item SET enrich_status='unmatched', enrich_confidence='manual' WHERE item_code=?",
            (code,))
    elif action == "confirm" and item_seq:
        # 선택한 ITEM_SEQ로 상세 재조회 후 확정
        from ...api_client import fetch_approval_detail
        dr = fetch_approval_detail(item_seq=item_seq, num_of_rows=1)
        d = dr["items"][0] if dr.get("items") else {}
        qadb.execute(
            """UPDATE master_item SET item_seq=?, permit_no=?, permit_date=?,
                 reexam_date=?, entp_name=?, atc_code=?, edi_code=?, bar_code=?,
                 chart=?, storage_method=?, material_name=?,
                 source_api='NO140', enrich_status='matched',
                 enrich_confidence='manual', enriched_at=CURRENT_TIMESTAMP
               WHERE item_code=?""",
            (item_seq, d.get("PRDUCT_PRMISN_NO"), d.get("ITEM_PERMIT_DATE"),
             d.get("REEXAM_DATE"), d.get("ENTP_NAME"), d.get("ATC_CODE"),
             d.get("EDI_CODE"), d.get("BAR_CODE"), d.get("CHART"),
             d.get("STORAGE_METHOD"), d.get("MATERIAL_NAME"), code))
        # 성분 재적재
        ings = enr._parse_material(d.get("MATERIAL_NAME"))
        qadb.execute("DELETE FROM master_ingredient WHERE item_code=?", (code,))
        for ing in ings:
            qadb.execute(
                "INSERT INTO master_ingredient (item_code, ingr_name, ingr_code, qty, unit) VALUES (?,?,?,?,?)",
                (code, ing["ingr_name"], ing.get("ingr_code"), ing.get("qty"), ing.get("unit")))
    else:
        return jsonify({"ok": False, "error": "잘못된 action"}), 400

    return redirect(url_for("qa.master", tab="review"))


# ════════════════════════════════════════════════════════════════════════
# Phase M-3 — APQR(연간제품품질평가) 초안 자동작성
# ════════════════════════════════════════════════════════════════════════
def _apqr_years():
    y = datetime.date.today().year
    return [y, y - 1, y - 2]


def _apqr_products():
    """APQR 선택 가능 품목 = enrich 완료(matched) master_item만 (item_seq·허가정보 보유)."""
    return qadb.query(
        """SELECT item_code, item_name, item_seq FROM master_item
           WHERE active=1 AND enrich_status='matched' ORDER BY item_name LIMIT 2000""")


@qa_bp.route("/apqr")
def apqr_home():
    """APQR 품목·연도 선택 화면 (matched 품목만)."""
    products = _apqr_products()
    years = _apqr_years()
    return render_template("app/qa/apqr.html", active_page="apqr",
                           products=products, years=years, doc=None,
                           sel_seq=None, sel_year=years[0],
                           flash_msg=request.args.get("msg") or "")


@qa_bp.route("/apqr/<item_code>")
def apqr_detail(item_code):
    """APQR 초안 미리보기 (13섹션 아코디언) — 사내 품목코드 기준."""
    from . import apqr as apqr_mod
    year = request.args.get("year")
    try:
        year = int(year) if year else datetime.date.today().year
    except ValueError:
        year = datetime.date.today().year
    doc = apqr_mod.build_apqr(item_code, year)
    if not doc:
        return redirect(url_for("qa.apqr_home") + "?msg=품목없음")
    return render_template("app/qa/apqr.html", active_page="apqr",
                           products=_apqr_products(), years=_apqr_years(), doc=doc,
                           sel_seq=item_code, sel_year=year,
                           flash_msg=request.args.get("msg") or "")


@qa_bp.route("/apqr/export/<item_code>")
def apqr_export(item_code):
    """APQR 초안 Word(.docx) 다운로드 — 사내 품목코드 기준."""
    from flask import send_file
    from . import apqr as apqr_mod
    year = request.args.get("year")
    try:
        year = int(year) if year else datetime.date.today().year
    except ValueError:
        year = datetime.date.today().year
    buf = apqr_mod.export_apqr_docx(item_code, year)
    if not buf:
        return redirect(url_for("qa.apqr_home") + "?msg=생성실패")
    return send_file(buf, as_attachment=True,
                     download_name=f"APQR_{item_code}_{year}.docx",
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@qa_bp.route("/run-monitor", methods=["POST", "GET"])
def run_monitor_route():
    """모니터링 배치 수동 트리거 (스냅샷+diff). S2 — 스케줄러 대신 수동/외부 cron."""
    from . import monitor
    stats = monitor.run_monitor()
    if request.method == "GET":
        return jsonify({"ok": True, **stats})
    return redirect(url_for("qa.qa_home") + "?msg=monitor_done")


@qa_bp.route("/scheduler/status")
def scheduler_status():
    """야간 배치 스케줄러 상태 (JSON)."""
    from . import scheduler
    return jsonify(scheduler.get_status())


@qa_bp.route("/mock/demo-gmp", methods=["POST", "GET"])
def mock_demo_gmp():
    """데모용 [MOCK] GMP D-25 이벤트 주입 (D-90 로직 시연). is_mock=1 명시."""
    from . import mock
    eid = mock.inject_demo_gmp(25)
    if request.method == "GET":
        return jsonify({"ok": True, "event_id": eid, "is_mock": True})
    return redirect(url_for("qa.qa_home") + "?msg=mock_injected")


@qa_bp.route("/mock/purge", methods=["POST", "GET"])
def mock_purge():
    """모든 [MOCK] 데이터 일괄 삭제."""
    from . import mock
    n = mock.purge_mocks()
    if request.method == "GET":
        return jsonify({"ok": True, "purged": n})
    return redirect(url_for("qa.qa_home") + f"?msg=mock_purged_{n}")


@qa_bp.route("/event/<int:event_id>")
def event_detail(event_id):
    """이벤트 상세 (P3) — severity·자사매칭·원시 payload·권장액션·상태."""
    ev = qadb.query_one("SELECT * FROM event WHERE event_id=?", (event_id,))
    if not ev:
        return jsonify({"error": "이벤트 없음"}), 404
    ev["matched_item_codes"] = qadb.jload(ev.get("matched_item_codes"), [])
    ev["matched_ingredients"] = qadb.jload(ev.get("matched_ingredients"), [])
    ev["raw_payload"] = qadb.jload(ev.get("raw_payload"), {})
    # 매칭된 자사 품목 상세
    matched = []
    for code in ev["matched_item_codes"]:
        mi = qadb.query_one("SELECT item_code, item_name, permit_no, reexam_date FROM master_item WHERE item_code=?", (code,))
        if mi:
            matched.append(mi)
    sev = get_severity(ev["event_type"])
    alerts = qadb.query("SELECT * FROM alert_log WHERE event_id=? ORDER BY sent_at DESC", (event_id,))
    return render_template("app/qa/event.html", active_page="qa",
                           ev=ev, sev=sev, matched=matched, alerts=alerts)


@qa_bp.route("/event/<int:event_id>/status", methods=["POST"])
def event_status(event_id):
    """이벤트 상태 변경 (new→reviewing→closed) + 메모."""
    new_status = request.form.get("status")
    note = request.form.get("note")
    if new_status in ("new", "reviewing", "closed"):
        qadb.execute("UPDATE event SET status=?, note=? WHERE event_id=?",
                     (new_status, note, event_id))
    return redirect(url_for("qa.event_detail", event_id=event_id))


@qa_bp.route("/healthz")
def qa_health():
    try:
        return jsonify({"ok": True, "module": "qa", **_master_stats()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ────────────────────────────────────────────────────────────────────────────
def _master_stats() -> dict:
    """마스터 요약 통계 (KPI용)."""
    total = qadb.query_one("SELECT COUNT(*) n FROM master_item WHERE active=1")["n"]
    non_herbal = qadb.query_one("SELECT COUNT(*) n FROM master_item WHERE active=1 AND is_herbal=0")["n"]
    matched = qadb.query_one("SELECT COUNT(*) n FROM master_item WHERE active=1 AND enrich_status='matched'")["n"]
    matched_nh = qadb.query_one(
        "SELECT COUNT(*) n FROM master_item WHERE active=1 AND is_herbal=0 AND enrich_status='matched'")["n"]
    review = qadb.query_one("SELECT COUNT(*) n FROM master_item WHERE active=1 AND enrich_status='review'")["n"]
    unmatched = qadb.query_one("SELECT COUNT(*) n FROM master_item WHERE active=1 AND enrich_status IN ('unmatched','pending')")["n"]
    herbal = total - non_herbal
    return {
        "total": total, "herbal": herbal, "non_herbal": non_herbal,
        "matched": matched, "matched_nh": matched_nh,
        "review": review, "unmatched": unmatched,
        "match_pct": round(matched / total * 100, 1) if total else 0,
        "match_pct_nh": round(matched_nh / non_herbal * 100, 1) if non_herbal else 0,
    }


def _event_stats() -> dict:
    """이벤트 요약 (KPI용) — 오늘 신규 / 미확인 / CRITICAL."""
    today = datetime.date.today().isoformat()
    today_new = qadb.query_one(
        "SELECT COUNT(*) n FROM event WHERE date(detected_at)=?", (today,))["n"]
    unconfirmed = qadb.query_one("SELECT COUNT(*) n FROM event WHERE status='new'")["n"]
    critical = qadb.query_one(
        "SELECT COUNT(*) n FROM event WHERE status!='closed' AND severity='CRITICAL'")["n"]
    return {"today_new": today_new, "unconfirmed": unconfirmed, "critical": critical}


def today_critical_count() -> int:
    """사이드바 배지용 — 미확인 CRITICAL 이벤트 수 (inject_nav 에서 호출)."""
    try:
        return qadb.query_one(
            "SELECT COUNT(*) n FROM event WHERE status!='closed' AND severity='CRITICAL'")["n"]
    except Exception:
        return 0
