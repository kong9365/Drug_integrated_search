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
    """QA 대시보드 (P1) — KPI 4종 + 오늘 이벤트 피드 + 다가오는 마감."""
    stats = _master_stats()
    ev_stats = _event_stats()
    # 미확인(new) 이벤트 — severity 정렬
    events = qadb.query(
        "SELECT * FROM event WHERE status != 'closed' ORDER BY detected_at DESC LIMIT 30")
    for e in events:
        e["matched_item_codes"] = qadb.jload(e.get("matched_item_codes"), [])
        e["sev"] = get_severity(e["event_type"])
    events.sort(key=lambda e: SEVERITY_ORDER.get(e["severity"], 3))
    # 다가오는 재심사 마감 (D-365 이내, 가까운 순)
    today = datetime.date.today().strftime("%Y%m%d")
    deadlines = qadb.query(
        """SELECT item_code, item_name, reexam_date FROM master_item
           WHERE active=1 AND reexam_date IS NOT NULL AND reexam_date >= ?
           ORDER BY reexam_date LIMIT 8""", (today,))
    from . import scheduler
    return render_template("app/qa/home.html", active_page="qa",
                           stats=stats, ev=ev_stats, events=events[:10], deadlines=deadlines,
                           sched=scheduler.get_status())


@qa_bp.route("/master")
def master():
    """마스터 검토 페이지 (P2)."""
    q = (request.args.get("q") or "").strip()
    f_cat = (request.args.get("cat") or "").strip()
    f_status = (request.args.get("status") or "").strip()
    tab = (request.args.get("tab") or "all").strip()  # all | review

    where = ["active=1"]
    params = []
    if q:
        where.append("(item_name LIKE ? OR item_code LIKE ? OR item_name_alt LIKE ?)")
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if f_cat:
        where.append("category = ?")
        params.append(f_cat)
    if f_status:
        where.append("enrich_status = ?")
        params.append(f_status)
    if tab == "review":
        where.append("enrich_status = 'review'")

    sql = f"""SELECT item_code, item_name, item_name_alt, category, sub_category,
                     gubun, self_or_consign, is_herbal, item_seq, permit_no,
                     reexam_date, atc_code, edi_code, source_api,
                     enrich_status, enrich_confidence, enrich_candidates
              FROM master_item WHERE {' AND '.join(where)}
              ORDER BY enrich_status='review' DESC, item_code LIMIT 1000"""
    items = qadb.query(sql, tuple(params))
    for it in items:
        it["candidates"] = qadb.jload(it.get("enrich_candidates"), [])

    return render_template(
        "app/qa/master.html",
        active_page="qa",
        items=items,
        stats=_master_stats(),
        categories=_FINISHED_CATS,
        q=q, f_cat=f_cat, f_status=f_status, tab=tab,
        progress=enr.get_progress(),
    )


@qa_bp.route("/master/<code>")
def master_detail(code):
    """품목 상세 — 사내 입력 vs 공공 enrichment 비교."""
    item = qadb.query_one("SELECT * FROM master_item WHERE item_code=?", (code,))
    if not item:
        return jsonify({"error": "품목 없음"}), 404
    item["candidates"] = qadb.jload(item.get("enrich_candidates"), [])
    ingredients = qadb.query(
        "SELECT ingr_name, ingr_code, qty, unit FROM master_ingredient WHERE item_code=?", (code,))
    return render_template("app/qa/master_detail.html", active_page="qa",
                           item=item, ingredients=ingredients)


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
# Phase M-1 — 정형화 품목마스터 (product_master, item_seq 9탭)
#   기존 master_item(item_code) 검토 흐름과 별개. 스크린샷 9탭 + APQR 소스.
# ════════════════════════════════════════════════════════════════════════
# 테스트 시드: 베니톨정 (광동제약 자사 일반의약품)
_SEED_PRODUCT = {"item_seq": "199401695", "edi_code": "641801640", "product_name": "베니톨정"}

# 9탭 정의 — 데이터 탭 + 연동대기 placeholder 탭
_PM_TABS = [
    ("ingredient", "원약분량", "data"),
    ("packaging", "포장", "data"),
    ("reg_event", "규제 이벤트", "data"),
    ("std_doc", "제품표준서", "pending"),
    ("equipment", "설비", "pending"),
    ("finished", "완제품", "pending"),
    ("pv", "PV현황", "pending"),
    ("cv", "CV현황", "pending"),
    ("consign", "수탁제품", "pending"),
]


@qa_bp.route("/product")
def product_list():
    """정형화 품목마스터 목록 (product_master)."""
    rows = qadb.query(
        """SELECT item_seq, product_name, etc_otc, permit_holder, permit_date,
                  reexam_date, enrich_status, enriched_at
           FROM product_master ORDER BY updated_at DESC, item_seq""")
    return render_template("app/qa/product_list.html", active_page="qa",
                           products=rows, seed=_SEED_PRODUCT,
                           flash_msg=request.args.get("msg") or "")


@qa_bp.route("/product/register", methods=["POST"])
def product_register():
    """품목기준코드(+보험코드)로 등록 → 즉시 규제 API enrich."""
    item_seq = (request.form.get("item_seq") or "").strip()
    edi_code = (request.form.get("edi_code") or "").strip() or None
    product_name = (request.form.get("product_name") or "").strip() or None
    if not item_seq:
        return redirect(url_for("qa.product_list") + "?msg=품목기준코드_필요")
    try:
        enr.enrich_product(item_seq, edi_code=edi_code, product_name=product_name)
    except Exception as e:
        logger.warning(f"product_register[{item_seq}] 실패: {e}")
        return redirect(url_for("qa.product_list") + "?msg=enrich_실패")
    return redirect(url_for("qa.product_detail", item_seq=item_seq) + "?msg=등록·보강_완료")


@qa_bp.route("/product/<item_seq>")
def product_detail(item_seq):
    """정형화 품목마스터 상세 — 9탭 + 규제 이벤트 타임라인 + 위험 신호등."""
    p = qadb.query_one("SELECT * FROM product_master WHERE item_seq=?", (item_seq,))
    if not p:
        return redirect(url_for("qa.product_list") + "?msg=품목없음")
    ingredients = qadb.query("SELECT * FROM product_ingredient WHERE item_seq=? ORDER BY id", (item_seq,))
    packaging = qadb.query("SELECT * FROM product_packaging WHERE item_seq=? ORDER BY id", (item_seq,))
    reg_events = qadb.query(
        "SELECT * FROM product_reg_event WHERE item_seq=? ORDER BY event_date DESC, id DESC", (item_seq,))
    # 위험 신호등 (risk.py 재사용)
    signal = None
    try:
        from ..risk import calc_risk_signal
        recalls = [e for e in reg_events if e["event_type"] == "recall"]
        discs = [e for e in reg_events if e["event_type"] == "disciplinary"]
        signal = calc_risk_signal(approval_data=[p], disciplinary_items=discs,
                                  recall_items=recalls, review_due_days=None)
    except Exception as e:
        logger.debug(f"product 위험 신호등 실패: {e}")
    return render_template("app/qa/product_detail.html", active_page="qa",
                           p=p, ingredients=ingredients, packaging=packaging,
                           reg_events=reg_events, signal=signal, tabs=_PM_TABS,
                           flash_msg=request.args.get("msg") or "")


# ════════════════════════════════════════════════════════════════════════
# Phase M-3 — APQR(연간제품품질평가) 초안 자동작성
# ════════════════════════════════════════════════════════════════════════
def _apqr_years():
    y = datetime.date.today().year
    return [y, y - 1, y - 2]


@qa_bp.route("/apqr")
def apqr_home():
    """APQR 품목·연도 선택 화면."""
    products = qadb.query("SELECT item_seq, product_name FROM product_master ORDER BY product_name")
    years = _apqr_years()
    return render_template("app/qa/apqr.html", active_page="apqr",
                           products=products, years=years, doc=None,
                           sel_seq=None, sel_year=years[0],
                           flash_msg=request.args.get("msg") or "")


@qa_bp.route("/apqr/<item_seq>")
def apqr_detail(item_seq):
    """APQR 초안 미리보기 (13섹션 아코디언)."""
    from . import apqr as apqr_mod
    year = request.args.get("year")
    try:
        year = int(year) if year else datetime.date.today().year
    except ValueError:
        year = datetime.date.today().year
    doc = apqr_mod.build_apqr(item_seq, year)
    if not doc:
        return redirect(url_for("qa.apqr_home") + "?msg=품목없음")
    products = qadb.query("SELECT item_seq, product_name FROM product_master ORDER BY product_name")
    return render_template("app/qa/apqr.html", active_page="apqr",
                           products=products, years=_apqr_years(), doc=doc,
                           sel_seq=item_seq, sel_year=year,
                           flash_msg=request.args.get("msg") or "")


@qa_bp.route("/apqr/export/<item_seq>")
def apqr_export(item_seq):
    """APQR 초안 Word(.docx) 다운로드."""
    from flask import send_file
    from . import apqr as apqr_mod
    year = request.args.get("year")
    try:
        year = int(year) if year else datetime.date.today().year
    except ValueError:
        year = datetime.date.today().year
    buf = apqr_mod.export_apqr_docx(item_seq, year)
    if not buf:
        return redirect(url_for("qa.apqr_home") + "?msg=생성실패")
    return send_file(buf, as_attachment=True,
                     download_name=f"APQR_{item_seq}_{year}.docx",
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
