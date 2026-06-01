"""
KD-IRIS — 광동 허가 백본 동기화 (Phase HYB · 공공 기준 역방향)

식약처 NO140을 entp_name='광동제약' 으로 통째 조회 → official_approval 미러에 적재.
"수동 업데이트" 클릭 시 재조회(upsert) + 사내 master_item 재링크.

핵심 (실측 2026-06-01):
- fetch_approval(entp_name='광동제약') 서버 필터 작동 → totalCount=338, 전부 광동제약(주).
- 페이지네이션 지원 → 전체 수집 후 상세(getDrugPrdtPrmsnDtlInq06) 병렬 보강.

재링크(reverse matching) — 이름 추측 검색 없이 로컬 매칭:
- master_item.item_seq 가 official 에 있으면 → 허가필드 최신화(refresh).
- master_item 미매칭(item_seq 없음) 인데 정규화 품목명이 official 과 "유일 일치" → 자동 matched.
  (다성분/다용량으로 정규화명이 겹치면 모호 → 건너뜀: 기존 review/unmatched 유지)

웹: run_sync_async() → 백그라운드 스레드 + _PROGRESS 폴링.
"""
import datetime
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from ...api_client import fetch_approval, fetch_approval_detail
from ...config import COMPANY_NAME
from . import db as qadb
from . import enrichment as enr

logger = logging.getLogger(__name__)

# 동기화 대상 허가권자명 (서버 필터). COMPANY_NAME='광동' 보다 좁은 '광동제약'을 기본값으로
# (광동제약(주) 명의 의약품 허가 = QA 마스터 대상). 필요 시 인자로 변경.
DEFAULT_ENTP = "광동제약"

_PROGRESS: Dict = {"running": False, "phase": "", "total": 0, "done": 0,
                   "official": 0, "linked": 0, "relinked": 0,
                   "started_at": None, "finished_at": None, "error": None}
_LOCK = threading.Lock()


# ────────────────────────────────────────────────────────────────────────────
# 수집
# ────────────────────────────────────────────────────────────────────────────
def fetch_company_approvals(entp: str = DEFAULT_ENTP, with_detail: bool = True,
                            max_workers: int = 10) -> List[Dict]:
    """entp_name 으로 NO140 전체 페이지 수집 → (옵션) 상세 병렬 보강 → row dict 리스트."""
    # 1) 목록 페이지네이션
    rows: List[Dict] = []
    page = 1
    total = None
    while True:
        ap = fetch_approval(entp_name=entp, num_of_rows=100, page_no=page, merge_excel=False)
        items = ap.get("items", []) or []
        if total is None:
            total = ap.get("totalCount") or 0
        rows.extend(items)
        if len(rows) >= (total or 0) or not items or page > 50:
            break
        page += 1
    # 자사명 안전 필터 (서버 필터 신뢰하되 이중 확인)
    rows = [r for r in rows if COMPANY_NAME in (r.get("ENTP_NAME") or "")]
    logger.info(f"광동 허가 목록 수집: {len(rows)}건 (entp={entp}, totalCount={total})")

    with _LOCK:
        _PROGRESS["official"] = len(rows)

    if not with_detail:
        return [_row_from_list(r) for r in rows]

    # 2) 상세 병렬 보강 (item_seq 기준)
    out: List[Dict] = []

    def _work(r):
        base = _row_from_list(r)
        seq = base.get("item_seq")
        if seq:
            try:
                dr = fetch_approval_detail(item_seq=seq, num_of_rows=1)
                if dr.get("items"):
                    base.update(_row_from_detail(dr["items"][0]))
            except Exception as e:
                logger.debug(f"[{seq}] 상세 보강 실패: {e}")
        return base

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_work, r) for r in rows]
        for fut in as_completed(futs):
            try:
                out.append(fut.result())
            except Exception as e:
                logger.debug(f"상세 작업 실패: {e}")
            with _LOCK:
                _PROGRESS["done"] += 1
    return out


def _row_from_list(it: Dict) -> Dict:
    name = it.get("ITEM_NAME") or ""
    return {
        "item_seq": it.get("ITEM_SEQ"),
        "item_name": name,
        "entp_name": it.get("ENTP_NAME"),
        "permit_no": it.get("PRDUCT_PRMISN_NO"),
        "permit_date": it.get("ITEM_PERMIT_DATE"),
        "cancel_date": it.get("CANCEL_DATE"),
        "cancel_name": it.get("CANCEL_NAME"),
        "etc_otc": it.get("ETC_OTC_CODE") or it.get("SPCLTY_PBLC"),
        "norm_name": enr.normalize_name(enr._base_name(name)),
    }


def _row_from_detail(d: Dict) -> Dict:
    return {k: v for k, v in {
        "reexam_date": d.get("REEXAM_DATE") or None,
        "atc_code": d.get("ATC_CODE") or None,
        "edi_code": d.get("EDI_CODE") or None,
        "bar_code": d.get("BAR_CODE") or None,
        "chart": d.get("CHART") or None,
        "storage_method": d.get("STORAGE_METHOD") or None,
        "material_name": d.get("MATERIAL_NAME") or None,
        "cancel_date": d.get("CANCEL_DATE") or None,
        "cancel_name": d.get("CANCEL_NAME") or None,
        "etc_otc": d.get("ETC_OTC_CODE") or None,
    }.items() if v is not None}


# ────────────────────────────────────────────────────────────────────────────
# 적재 + 재링크
# ────────────────────────────────────────────────────────────────────────────
_OA_UPSERT = """
INSERT INTO official_approval
  (item_seq, item_name, entp_name, permit_no, permit_date, cancel_date, cancel_name,
   reexam_date, atc_code, edi_code, bar_code, chart, storage_method, material_name,
   etc_otc, norm_name, synced_at)
VALUES
  (:item_seq, :item_name, :entp_name, :permit_no, :permit_date, :cancel_date, :cancel_name,
   :reexam_date, :atc_code, :edi_code, :bar_code, :chart, :storage_method, :material_name,
   :etc_otc, :norm_name, :synced_at)
ON CONFLICT(item_seq) DO UPDATE SET
  item_name=excluded.item_name, entp_name=excluded.entp_name,
  permit_no=excluded.permit_no, permit_date=excluded.permit_date,
  cancel_date=excluded.cancel_date, cancel_name=excluded.cancel_name,
  reexam_date=excluded.reexam_date, atc_code=excluded.atc_code,
  edi_code=excluded.edi_code, bar_code=excluded.bar_code, chart=excluded.chart,
  storage_method=excluded.storage_method, material_name=excluded.material_name,
  etc_otc=excluded.etc_otc, norm_name=excluded.norm_name, synced_at=excluded.synced_at
"""

# refresh 시 사내 빈 칸만 보강(덮어쓰지 않음): COALESCE(기존, 신규)
_MI_REFRESH = """
UPDATE master_item SET
  permit_no=COALESCE(permit_no, :permit_no),
  permit_date=COALESCE(permit_date, :permit_date),
  reexam_date=COALESCE(reexam_date, :reexam_date),
  entp_name=COALESCE(entp_name, :entp_name),
  atc_code=COALESCE(atc_code, :atc_code),
  edi_code=COALESCE(edi_code, :edi_code),
  bar_code=COALESCE(bar_code, :bar_code),
  chart=COALESCE(chart, :chart),
  storage_method=COALESCE(storage_method, :storage_method),
  material_name=COALESCE(material_name, :material_name)
WHERE item_seq=:item_seq
"""

# 미매칭 → 자동 링크(허가필드 채움 + matched 확정)
_MI_LINK = """
UPDATE master_item SET
  item_seq=:item_seq, permit_no=:permit_no, permit_date=:permit_date,
  reexam_date=:reexam_date, entp_name=:entp_name, atc_code=:atc_code,
  edi_code=:edi_code, bar_code=:bar_code, chart=:chart,
  storage_method=:storage_method, material_name=:material_name,
  source_api='NO140_OFFICIAL', enrich_status='matched',
  enrich_confidence='high', enrich_candidates=NULL, enriched_at=CURRENT_TIMESTAMP
WHERE item_code=:item_code
"""


def sync_official(entp: str = DEFAULT_ENTP, with_detail: bool = True) -> Dict:
    """광동 허가 수집 → official_approval upsert → 사내 master_item 재링크. 통계 반환."""
    qadb.init_db()
    now = datetime.datetime.now().isoformat()
    rows = fetch_company_approvals(entp=entp, with_detail=with_detail)
    if not rows:
        return {"official": 0, "error": "수집 0건 (API 응답 없음)"}

    with _LOCK:
        _PROGRESS["phase"] = "적재"

    # 1) official_approval upsert
    conn = qadb.get_conn()
    try:
        for r in rows:
            r.setdefault("synced_at", now)
            r["synced_at"] = now
            params = {k: r.get(k) for k in (
                "item_seq", "item_name", "entp_name", "permit_no", "permit_date",
                "cancel_date", "cancel_name", "reexam_date", "atc_code", "edi_code",
                "bar_code", "chart", "storage_method", "material_name", "etc_otc",
                "norm_name", "synced_at")}
            conn.execute(_OA_UPSERT, params)
        conn.commit()
    finally:
        conn.close()

    # 2) 사내 재링크
    with _LOCK:
        _PROGRESS["phase"] = "사내 재링크"
    by_seq = {r["item_seq"]: r for r in rows if r.get("item_seq")}
    norm_map: Dict[str, List[str]] = {}
    for r in rows:
        nm = r.get("norm_name")
        if nm:
            norm_map.setdefault(nm, []).append(r["item_seq"])

    linked = relinked = 0
    conn = qadb.get_conn()
    try:
        masters = [dict(x) for x in conn.execute(
            "SELECT item_code, item_name, item_seq, enrich_status FROM master_item WHERE active=1").fetchall()]
        for mi in masters:
            seq = mi.get("item_seq")
            # (a) 이미 연결됨 → 빈 칸 보강
            if seq and seq in by_seq:
                rr = by_seq[seq]
                conn.execute(_MI_REFRESH, {k: rr.get(k) for k in (
                    "permit_no", "permit_date", "reexam_date", "entp_name", "atc_code",
                    "edi_code", "bar_code", "chart", "storage_method", "material_name", "item_seq")})
                linked += 1
                continue
            # (b) 미연결 → 정규화 이름 유일 일치 시 자동 링크
            if not seq and mi.get("enrich_status") in ("pending", "unmatched", "review", None):
                nm = enr.normalize_name(enr._base_name(mi.get("item_name") or ""))
                cand_seqs = norm_map.get(nm, [])
                if len(cand_seqs) == 1:
                    r = by_seq[cand_seqs[0]]
                    p = dict(r)
                    p["item_code"] = mi["item_code"]
                    conn.execute(_MI_LINK, {k: p.get(k) for k in (
                        "item_code", "item_seq", "permit_no", "permit_date", "reexam_date",
                        "entp_name", "atc_code", "edi_code", "bar_code", "chart",
                        "storage_method", "material_name")})
                    # 성분 재적재
                    ings = enr._parse_material(r.get("material_name"))
                    conn.execute("DELETE FROM master_ingredient WHERE item_code=?", (mi["item_code"],))
                    for ing in ings:
                        conn.execute(
                            "INSERT INTO master_ingredient (item_code, ingr_name, ingr_code, qty, unit) VALUES (?,?,?,?,?)",
                            (mi["item_code"], ing["ingr_name"], ing.get("ingr_code"), ing.get("qty"), ing.get("unit")))
                    linked += 1
                    relinked += 1
        conn.commit()
    finally:
        conn.close()

    # 3) 통계
    new_unlinked = sum(1 for r in rows if not _has_internal(r["item_seq"]))
    canceled = sum(1 for r in rows if (r.get("cancel_name") and "정상" not in (r.get("cancel_name") or "")) or r.get("cancel_date"))
    stats = {"official": len(rows), "linked": linked, "relinked_now": relinked,
             "new_unlinked": new_unlinked, "canceled": canceled, "synced_at": now}
    with _LOCK:
        _PROGRESS.update({"linked": linked, "relinked": relinked})
    logger.info(f"광동 허가 동기화 완료: {stats}")
    return stats


def _has_internal(item_seq: str) -> bool:
    """이 허가(item_seq)에 연결된 사내 품목이 있나."""
    if not item_seq:
        return False
    r = qadb.query_one("SELECT 1 n FROM master_item WHERE item_seq=? AND active=1 LIMIT 1", (item_seq,))
    return bool(r)


# ────────────────────────────────────────────────────────────────────────────
# 백그라운드 + 통계 조회
# ────────────────────────────────────────────────────────────────────────────
def run_sync_async(entp: str = DEFAULT_ENTP) -> bool:
    with _LOCK:
        if _PROGRESS.get("running"):
            return False
        _PROGRESS.update({"running": True, "phase": "수집", "total": 0, "done": 0,
                          "official": 0, "linked": 0, "relinked": 0,
                          "started_at": datetime.datetime.now().isoformat(),
                          "finished_at": None, "error": None})

    def _run():
        try:
            sync_official(entp=entp)
        except Exception as e:
            logger.error(f"광동 허가 동기화 실패: {e}")
            with _LOCK:
                _PROGRESS["error"] = str(e)
        finally:
            with _LOCK:
                _PROGRESS["running"] = False
                _PROGRESS["finished_at"] = datetime.datetime.now().isoformat()

    threading.Thread(target=_run, daemon=True).start()
    return True


def get_progress() -> Dict:
    with _LOCK:
        return dict(_PROGRESS)


def official_stats() -> Dict:
    """official_approval 요약 (KPI)."""
    def n(sql, p=()):
        r = qadb.query_one(sql, p)
        return r["n"] if r else 0
    total = n("SELECT COUNT(*) n FROM official_approval")
    linked = n("""SELECT COUNT(DISTINCT o.item_seq) n FROM official_approval o
                  JOIN master_item m ON m.item_seq=o.item_seq AND m.active=1""")
    canceled = n("SELECT COUNT(*) n FROM official_approval WHERE cancel_date IS NOT NULL AND cancel_date!=''")
    last = qadb.query_one("SELECT MAX(synced_at) s FROM official_approval")
    return {"total": total, "linked": linked, "new_unlinked": total - linked,
            "canceled": canceled, "synced_at": (last or {}).get("s")}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    s = sync_official()
    print("=" * 50)
    print(f"광동 허가: {s.get('official')}건 / 사내연결 {s.get('linked')} "
          f"(이번 자동링크 {s.get('relinked_now')}) / 신규 {s.get('new_unlinked')} / 취하 {s.get('canceled')}")
