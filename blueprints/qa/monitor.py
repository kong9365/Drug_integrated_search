"""
KD-IRIS 1차 빌드 — 일일 스냅샷 + diff 모니터링 (기능재설계 v2 §11.5)

모니터링 4종 (한약 NO 90 은 hook):
  NO 539 회수·판매중지 / NO 564 행정처분 / NO 547 안전성서한 / NO 132 GMP

흐름:
  1. 각 API 최근 윈도우 호출 → snapshot(snap_date, api_id, natural_key, payload) UPSERT
  2. 오늘 natural_key − 어제 natural_key = 신규 → event 적재
  3. 자사 매칭 4차원(직접/동성분/제조소/경쟁사) → impact_level → severity
  4. GMP 는 diff 아닌 자사 만료 D-90/D-30 계산

CLI: python -m drug_integrated_search.blueprints.qa.monitor
"""
import datetime
import logging
import re
from typing import Dict, List, Set

from ...api_client import fetch_recall, fetch_disciplinary
from ...api_extras import fetch_drug_safety_letter, fetch_drug_gmp
from ...config import COMPANY_NAME
from ..severity import get_severity
from . import db as qadb

logger = logging.getLogger(__name__)

WINDOW = {"NO539": 100, "NO564": 100, "NO547": 50, "NO132": 50}


# ────────────────────────────────────────────────────────────────────────────
# 자사 매칭 컨텍스트
# ────────────────────────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", (s or "")).lower()


def _load_master_ctx() -> Dict:
    """매칭용 자사 키 집합 로드."""
    items = qadb.query("SELECT item_code, item_name, item_seq, entp_name FROM master_item WHERE active=1")
    seqs = {it["item_seq"]: it["item_code"] for it in items if it.get("item_seq")}
    names = {_norm(it["item_name"]): it["item_code"] for it in items if it.get("item_name")}
    ings = qadb.query("SELECT DISTINCT item_code, ingr_name FROM master_ingredient")
    ingr_map: Dict[str, List[str]] = {}
    for r in ings:
        if r["ingr_name"]:
            ingr_map.setdefault(_norm(r["ingr_name"]), []).append(r["item_code"])
    return {"seqs": seqs, "names": names, "ingr_map": ingr_map}


def _match(payload: Dict, ctx: Dict, fields_text: List[str]) -> Dict:
    """
    이벤트 payload → 자사 매칭 4차원 평가.
    반환: {impact_level, item_codes[], ingredients[]}
    """
    item_codes: Set[str] = set()
    ingredients: Set[str] = set()
    impact = None

    # 직접: ITEM_SEQ 일치
    seq = payload.get("ITEM_SEQ")
    if seq and seq in ctx["seqs"]:
        item_codes.add(ctx["seqs"][seq])
        impact = "direct"

    # 직접(보조): 품목명 정규화 일치
    pname = _norm(payload.get("PRDUCT") or payload.get("ITEM_NAME") or "")
    if pname and pname in ctx["names"]:
        item_codes.add(ctx["names"][pname])
        impact = impact or "direct"

    # 제조소: 업체명에 자사명 포함
    entp_blob = (payload.get("ENTRPS") or payload.get("ENTP_NAME") or payload.get("BSSH_NM") or "")
    if COMPANY_NAME in entp_blob:
        impact = impact or "manufacturer"

    # 동성분: 텍스트 필드에서 자사 성분명 검색
    blob = _norm(" ".join(str(payload.get(f) or "") for f in fields_text))
    if blob:
        for ing_norm, codes in ctx["ingr_map"].items():
            if len(ing_norm) >= 3 and ing_norm in blob:
                ingredients.add(ing_norm)
                for c in codes:
                    item_codes.add(c)
                impact = impact or "same_ingredient"

    if impact is None:
        impact = "competitor"
    return {"impact_level": impact, "item_codes": sorted(item_codes), "ingredients": sorted(ingredients)}


# ────────────────────────────────────────────────────────────────────────────
# 스냅샷 + diff
# ────────────────────────────────────────────────────────────────────────────
def _natural_key(api_id: str, p: Dict) -> str:
    if api_id == "NO539":
        return f"{p.get('STD_CD') or p.get('ITEM_SEQ') or ''}|{p.get('PRDUCT') or ''}|{p.get('ENTRPS') or ''}"
    if api_id == "NO564":
        return f"{p.get('ENTP_NAME') or ''}|{p.get('LAST_SETTLE_DATE') or ''}|{p.get('ITEM_NAME') or ''}"
    if api_id == "NO547":
        return p.get("SAFT_LETT_NO") or f"{p.get('TITLE') or ''}|{p.get('PBANC_YMD') or ''}"
    if api_id == "NO132":
        return f"{p.get('BSSH_NM') or ''}|{p.get('FCTR_ADDR') or ''}"
    return str(p)


def _fetch_window(api_id: str) -> List[Dict]:
    n = WINDOW.get(api_id, 50)
    try:
        if api_id == "NO539":
            return fetch_recall(num_of_rows=n).get("items", [])
        if api_id == "NO564":
            return fetch_disciplinary(num_of_rows=n).get("items", [])
        if api_id == "NO547":
            return fetch_drug_safety_letter(num_of_rows=n).get("items", [])
        if api_id == "NO132":
            # GMP 는 자사로 좁힘
            return fetch_drug_gmp(entp_name=COMPANY_NAME, num_of_rows=n).get("items", [])
    except Exception as e:
        logger.warning(f"[{api_id}] fetch 실패: {e}")
    return []


def _save_snapshot(api_id: str, items: List[Dict], snap_date: str) -> int:
    rows = []
    for p in items:
        nk = _natural_key(api_id, p)
        rows.append((snap_date, api_id, nk, qadb.jdump(p)))
    if rows:
        conn = qadb.get_conn()
        try:
            conn.executemany(
                "INSERT OR REPLACE INTO snapshot (snap_date, api_id, natural_key, payload) VALUES (?,?,?,?)",
                rows)
            conn.commit()
        finally:
            conn.close()
    return len(rows)


def _yesterday_keys(api_id: str, today: str) -> Set[str]:
    rows = qadb.query(
        "SELECT DISTINCT natural_key FROM snapshot WHERE api_id=? AND snap_date < ? ORDER BY snap_date DESC",
        (api_id, today))
    return {r["natural_key"] for r in rows}


# 이벤트 타입 매핑
_EVENT_TYPE = {"NO539": "recall", "NO564": "disciplinary", "NO547": "safety_letter", "NO132": "gmp_expiry"}
_TEXT_FIELDS = {
    "NO539": ["PRDUCT", "RTRVL_RESN", "ENTRPS"],
    "NO564": ["ITEM_NAME", "EXPOSE_CONT", "ENTP_NAME", "BEF_APPLY_LAW"],
    "NO547": ["TITLE", "SUMRY_CONT", "PBANC_CONT"],
    "NO132": ["BSSH_NM", "FCTR_ADDR"],
}


def _severity_for(event_type: str, impact: str) -> str:
    """§11.5 룰셋 — impact 에 따라 severity 조정."""
    base = get_severity(event_type)["level"]
    if event_type == "recall":
        return "CRITICAL" if impact == "direct" else "HIGH"
    if event_type == "disciplinary":
        return "CRITICAL" if impact == "direct" else ("HIGH" if impact == "manufacturer" else "LOW")
    if event_type == "safety_letter":
        return "HIGH" if impact in ("direct", "same_ingredient") else "LOW"
    return base


def _insert_event(api_id, event_type, severity, m, p, event_date, title, entity, summary):
    qadb.execute(
        """INSERT OR IGNORE INTO event
           (event_date, api_id, event_type, severity, impact_level, title, entity, summary,
            matched_item_codes, matched_ingredients, raw_payload, status)
           VALUES (?,?,?,?,?,?,?,?,?,?,?, 'new')""",
        (event_date, api_id, event_type, severity, m["impact_level"], title, entity, summary,
         qadb.jdump(m["item_codes"]), qadb.jdump(m["ingredients"]), qadb.jdump(p)))


def _process_diff(api_id: str, items: List[Dict], today: str, ctx: Dict) -> int:
    """539/564/547 — diff 기반 신규 이벤트."""
    prev = _yesterday_keys(api_id, today)
    first_run = len(prev) == 0
    new_cnt = 0
    etype = _EVENT_TYPE[api_id]
    for p in items:
        nk = _natural_key(api_id, p)
        # 최초 실행이면 자사 매칭된 것만 이벤트화 (전체 노이즈 방지), 이후엔 신규 키만
        m = _match(p, ctx, _TEXT_FIELDS[api_id])
        is_new = nk not in prev
        relevant = m["impact_level"] != "competitor"
        if (first_run and relevant) or (not first_run and is_new):
            sev = _severity_for(etype, m["impact_level"])
            title = p.get("PRDUCT") or p.get("ITEM_NAME") or p.get("TITLE") or "(제목 없음)"
            entity = p.get("ENTRPS") or p.get("ENTP_NAME") or ""
            summary = (p.get("RTRVL_RESN") or p.get("EXPOSE_CONT") or p.get("SUMRY_CONT") or "")[:200]
            edate = (p.get("RECALL_COMMAND_DATE") or p.get("LAST_SETTLE_DATE") or p.get("PBANC_YMD") or "")[:8]
            _insert_event(api_id, etype, sev, m, p, edate, title[:120], entity[:80], summary)
            new_cnt += 1
    return new_cnt


def _process_gmp(items: List[Dict], today: str, ctx: Dict) -> int:
    """NO 132 — 자사 GMP 만료 D-90/D-30 (diff 아님)."""
    cnt = 0
    today_dt = datetime.date.today()
    for p in items:
        if COMPANY_NAME not in (p.get("BSSH_NM") or ""):
            continue
        vld = (p.get("VLD_PRD_YMD") or "").replace("-", "")[:8]
        if len(vld) != 8:
            continue
        try:
            exp = datetime.date(int(vld[:4]), int(vld[4:6]), int(vld[6:8]))
        except ValueError:
            continue
        dday = (exp - today_dt).days
        if dday < 0 or dday > 90:
            continue  # 만료 지났거나 D-90 밖
        sev = "CRITICAL" if dday <= 30 else "HIGH"
        m = {"impact_level": "direct", "item_codes": [], "ingredients": []}
        title = f"{p.get('BSSH_NM')} GMP 만료 D-{dday}"
        summary = f"{p.get('FCTR_ADDR') or ''} · {p.get('KGMP_BGMP_NAME') or ''} · 만료 {vld}"
        _insert_event("NO132", "gmp_expiry", sev, m, p, vld, title[:120],
                      p.get("BSSH_NM", "")[:80], summary[:200])
        cnt += 1
    return cnt


def run_monitor() -> Dict:
    """전체 모니터링 1회 실행 → 스냅샷 저장 + diff 이벤트 적재."""
    qadb.init_db()
    today = datetime.date.today().isoformat()
    ctx = _load_master_ctx()
    stats = {"snapshots": {}, "new_events": 0}
    for api_id in ("NO539", "NO564", "NO547", "NO132"):
        items = _fetch_window(api_id)
        saved = _save_snapshot(api_id, items, today)
        stats["snapshots"][api_id] = saved
        if api_id == "NO132":
            stats["new_events"] += _process_gmp(items, today, ctx)
        else:
            stats["new_events"] += _process_diff(api_id, items, today, ctx)
    # 신규 이벤트 → 알람 디스패치 (Slack dry-run 포함)
    try:
        from . import alerts
        stats["alerts"] = alerts.dispatch_new_events()
    except Exception as e:
        logger.warning(f"알람 디스패치 실패: {e}")
    # Phase M-2 — 정형화 품목마스터(product_master) 품목기준 모니터링 동반 실행
    try:
        stats["product_monitoring"] = run_monitoring()
    except Exception as e:
        logger.warning(f"품목기준 모니터링 실패: {e}")
    logger.info(f"모니터링 완료: {stats}")
    return stats


# ════════════════════════════════════════════════════════════════════════════
# Phase M-2 — 품목기준 규제 모니터링 (product_master → product_reg_event)
# ════════════════════════════════════════════════════════════════════════════
def _base(s: str) -> str:
    return re.sub(r"\([^)]*\)", "", s or "").split("_")[0]


def _product_hit(payload: Dict, seq: str, name_norm: str, base_norm: str,
                 fields: List[str]) -> bool:
    """이벤트 payload 가 이 품목(seq/품목명)과 매칭되는지."""
    if seq and payload.get("ITEM_SEQ") and str(payload.get("ITEM_SEQ")) == str(seq):
        return True
    if not name_norm or len(base_norm) < 2:
        return False
    blob = _norm(" ".join(str(payload.get(f) or "") for f in fields))
    return bool(blob) and (base_norm in blob or name_norm in blob)


def _upsert_reg_event(item_seq, etype, sev, title, summary, edate, source_api) -> int:
    """product_reg_event UPSERT (UNIQUE 로 멱등). 신규 1 / 중복 0."""
    n = qadb.execute(
        """INSERT OR IGNORE INTO product_reg_event
             (item_seq, event_type, severity, title, summary, event_date, source_api)
           VALUES (?,?,?,?,?,?,?)""",
        (item_seq, etype, sev, (title or "")[:160], (summary or "")[:300],
         (edate or "")[:8], source_api))
    return 1 if n else 0


# (api_id, event_type, severity, title_fields, summary_field, date_field, match_fields)
_PROD_SOURCES = [
    ("NO539", "recall",        "CRITICAL", ["PRDUCT", "ITEM_NAME"], "RTRVL_RESN",  "RECALL_COMMAND_DATE", ["PRDUCT", "ITEM_NAME"]),
    ("NO564", "disciplinary",  "HIGH",     ["ITEM_NAME", "ENTP_NAME"], "EXPOSE_CONT", "LAST_SETTLE_DATE", ["ITEM_NAME", "ENTP_NAME"]),
    ("NO547", "safety_letter", "HIGH",     ["TITLE"], "SUMRY_CONT", "PBANC_YMD", ["TITLE", "SUMRY_CONT"]),
    ("NO554", "review_due",    "LOW",      ["ITEM_NAME"], "ENTP_NAME", "REEXAM_DATE", ["ITEM_NAME"]),
    ("NO556", "reeval_done",   "LOW",      ["ITEM_NAME"], "ENTP_NAME", "REVAL_DT", ["ITEM_NAME"]),
    ("NO534", "supplier_closure", "HIGH",  ["ITEM_NAME"], "ENTP_NAME", "", ["ITEM_NAME"]),
]


def _fetch_prod_window() -> Dict[str, List[Dict]]:
    """품목기준 모니터링용 API 윈도우 1회 fetch (대용량 554/556 num_of_rows=50)."""
    from ...api_extras import (fetch_drug_safety_letter, fetch_drug_review,
                               fetch_drug_reeval, fetch_drug_supply_stop)
    out = {}
    try: out["NO539"] = fetch_recall(num_of_rows=100).get("items", [])
    except Exception: out["NO539"] = []
    try: out["NO564"] = fetch_disciplinary(num_of_rows=100).get("items", [])
    except Exception: out["NO564"] = []
    try: out["NO547"] = fetch_drug_safety_letter(num_of_rows=50).get("items", [])
    except Exception: out["NO547"] = []
    try: out["NO554"] = fetch_drug_review(num_of_rows=50).get("items", [])
    except Exception: out["NO554"] = []
    try: out["NO556"] = fetch_drug_reeval(num_of_rows=50).get("items", [])
    except Exception: out["NO556"] = []
    try: out["NO534"] = fetch_drug_supply_stop(num_of_rows=50).get("items", [])
    except Exception: out["NO534"] = []
    return out


def get_all_master_products() -> List[Dict]:
    return qadb.query("SELECT item_seq, product_name, material_name FROM product_master")


def run_monitoring() -> Dict:
    """product_master 전 품목 → 규제 API 매칭 → product_reg_event 적재 (멱등)."""
    qadb.init_db()
    products = get_all_master_products()
    if not products:
        return {"products": 0, "new_events": 0}
    windows = _fetch_prod_window()
    new_cnt = 0
    for p in products:
        seq = p["item_seq"]
        name_norm = _norm(p.get("product_name"))
        base_norm = _norm(_base(p.get("product_name")))
        for api_id, etype, sev, title_fields, sum_field, date_field, match_fields in _PROD_SOURCES:
            for item in windows.get(api_id, []):
                if _product_hit(item, seq, name_norm, base_norm, match_fields):
                    title = next((item.get(f) for f in title_fields if item.get(f)), etype)
                    edate = (item.get(date_field) or "")[:8] if date_field else ""
                    new_cnt += _upsert_reg_event(seq, etype, sev, title,
                                                 item.get(sum_field), edate, api_id)
    logger.info(f"품목기준 모니터링: {len(products)}품목 → 신규 {new_cnt}건")
    return {"products": len(products), "new_events": new_cnt}


def product_critical_count() -> int:
    """미확인(acknowledged=0) CRITICAL product_reg_event 수 (자사 품목 배지용)."""
    try:
        return qadb.query_one(
            "SELECT COUNT(*) n FROM product_reg_event WHERE acknowledged=0 AND severity='CRITICAL'")["n"]
    except Exception:
        return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    s = run_monitor()
    print("=" * 50)
    print(f"스냅샷: {s['snapshots']}")
    print(f"신규 이벤트: {s['new_events']}건")
