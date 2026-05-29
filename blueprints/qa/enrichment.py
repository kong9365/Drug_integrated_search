"""
KD-IRIS 1차 빌드 — Enrichment 파이프라인 (기능재설계 v2 §11.4)

자사 마스터 품목명 → 공공데이터(NO 140 목록·상세·주성분 + NO 145 폴백)로
허가번호·ITEM_SEQ·성분·재심사일·ATC·EDI·바코드 자동 채움.

설계 (검토 반영):
- NO 140은 item_seq·entp_name 파라미터 무시 → item_name 으로만 조회 후
  결과에서 ENTP_NAME 에 '광동'(COMPANY_NAME) 포함 행을 코드 필터.
- ThreadPoolExecutor(max_workers=10) 병렬 → 880품목 벽시계 2~3분.
- CLI: python -m drug_integrated_search.blueprints.qa.enrichment
- 웹: run_enrichment_async() → 백그라운드 스레드 + _PROGRESS 폴링.

confidence:
  HIGH   — 정규화 완전일치 + ENTP 광동 1건
  MEDIUM — 후보 다수 중 품목명2/포장규격으로 1건 좁힘
  LOW    — 부분일치 다수 → review 큐 (enrich_candidates 저장)
"""
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from ...api_client import fetch_approval, fetch_approval_detail
from ...api_extras import fetch_quasi_approval
from ...config import COMPANY_NAME
from . import db as qadb

logger = logging.getLogger(__name__)

# 백그라운드 진행 상태 (웹 폴링용)
_PROGRESS: Dict = {"running": False, "total": 0, "done": 0, "matched": 0,
                   "review": 0, "unmatched": 0, "started_at": None, "finished_at": None}
_LOCK = threading.Lock()


# ────────────────────────────────────────────────────────────────────────────
# 정규화
# ────────────────────────────────────────────────────────────────────────────
def normalize_name(name: str) -> str:
    """품목명 정규화: 괄호/공백/특수문자 제거, 한글·영숫자만."""
    if not name:
        return ""
    s = re.sub(r"\([^)]*\)", "", name)          # 괄호 안 제거
    s = re.sub(r"[^0-9A-Za-z가-힣]", "", s)       # 한글/영숫자만
    return s.strip().lower()


def _company_match(items: List[Dict]) -> List[Dict]:
    """결과 중 ENTP_NAME 에 자사명(광동) 포함 행만."""
    return [it for it in items if COMPANY_NAME in (it.get("ENTP_NAME") or "")]


def _base_name(raw: str) -> str:
    """검색용 기본명: '_반제품' 등 언더스코어 접미 제거 + 괄호 제거."""
    if not raw:
        return ""
    s = raw.split("_")[0]                 # _반제품 / _원료 등 제거
    s = re.sub(r"\([^)]*\)", "", s)        # 괄호 제거
    return s.strip()


def _convert_units(s: str) -> str:
    """영문 단위 → 허가 표기 한글 (mg→밀리그램 등). mcg/ml 먼저, mg 다음."""
    s = re.sub(r"(?i)mcg|㎍|ug", "마이크로그램", s)
    s = re.sub(r"(?i)mg", "밀리그램", s)
    s = re.sub(r"(?i)ml", "밀리리터", s)
    return s


def _digits(s: str) -> List[str]:
    return re.findall(r"\d+", s or "")


_FORM_SUFFIX = re.compile(
    r"(연질캡슐|경질캡슐|장용정|서방정|주사액|점안액|점비액|시럽|현탁액|"
    r"정제|정|캡슐|과립|산|환|액|주|크림|연고|겔|패치|좌제|분말|밀리그램|밀리리터)+$")


def _search_variants(raw: str) -> List[str]:
    """NO 140 검색 시도 순서: 단위변환 → 원형 → 숫자/단위 제거 → 제형접미까지 제거."""
    base = _base_name(raw)
    conv = _convert_units(base)
    nodose = re.sub(r"\d+\s*(?:밀리그램|마이크로그램|밀리리터|그램|mg|mcg|ml|g|%|퍼센트)?",
                    "", base, flags=re.IGNORECASE).strip()
    noform = _FORM_SUFFIX.sub("", nodose).strip()
    out = []
    for v in (conv, base, nodose, noform):
        v = (v or "").strip()
        if v and len(v) >= 2 and v not in out:  # 2글자 미만 검색어는 노이즈 과다 → 제외
            out.append(v)
    return out


def _pick_best(cands: List[Dict], base: str, result: Dict):
    """광동 후보 중 최적 선택 + confidence. 못 고르면 review/unmatched 설정 후 (None,None)."""
    if not cands:
        return None, None
    if len(cands) == 1:
        return cands[0], "high"
    norm_base = normalize_name(base)
    digits = _digits(base)
    # 1) 용량 숫자로 disambiguation
    if digits:
        dose_hit = [c for c in cands if all(d in (c.get("ITEM_NAME") or "") for d in digits)]
        if len(dose_hit) == 1:
            return dose_hit[0], "high"
        if len(dose_hit) > 1:
            cands = dose_hit  # 좁혀서 아래 진행
    # 2) 정규화 base 완전일치
    exact = [c for c in cands if normalize_name(_base_name(c.get("ITEM_NAME", ""))) == norm_base]
    if len(exact) == 1:
        return exact[0], "high"
    if len(exact) > 1:
        return exact[0], "medium"
    # 3) 후보 다수 → review 큐
    result["enrich_status"] = "review"
    result["enrich_confidence"] = "low"
    result["candidates"] = [
        {"ITEM_SEQ": c.get("ITEM_SEQ"), "ITEM_NAME": c.get("ITEM_NAME"),
         "ENTP_NAME": c.get("ENTP_NAME"), "PRDUCT_PRMISN_NO": c.get("PRDUCT_PRMISN_NO")}
        for c in cands[:3]
    ]
    return None, None


# ────────────────────────────────────────────────────────────────────────────
# 단일 품목 enrichment
# ────────────────────────────────────────────────────────────────────────────
def enrich_one(item: Dict) -> Dict:
    """
    master_item 1행(dict) → enrichment 결과 dict.
    반환: {item_code, enrich_status, enrich_confidence, source_api, item_seq,
           permit_no, permit_date, reexam_date, entp_name, atc_code, edi_code,
           bar_code, chart, storage_method, material_name, ingredients[], candidates[]}
    """
    item_code = item["item_code"]
    raw_name = item["item_name"]
    base = _base_name(raw_name)
    result = {"item_code": item_code, "enrich_status": "unmatched",
              "enrich_confidence": None, "source_api": "unmatched",
              "ingredients": [], "candidates": []}

    # 1) NO 140 목록 조회 — 검색어 변형(단위변환/접미제거/용량제거) 순차 시도 → 광동 필터
    #    merge_excel=False: 43K행 Excel 반복 로드 회피 (대량 enrichment 성능 핵심)
    try:
        cands: List[Dict] = []
        for term in _search_variants(raw_name):
            ap = fetch_approval(item_name=term, num_of_rows=20, merge_excel=False)
            cands = _company_match(ap.get("items", []))
            if cands:
                break

        chosen, confidence = _pick_best(cands, base, result)
        if not chosen and result["enrich_status"] == "review":
            return result  # review 큐 (후보 다수)

        if chosen:
            result.update(_from_list(chosen))
            result["enrich_status"] = "matched"
            result["enrich_confidence"] = confidence
            result["source_api"] = "NO140"
            item_seq = chosen.get("ITEM_SEQ")
            # 2) NO 140 상세 → MATERIAL_NAME 에서 성분 파싱
            #    (주성분 API getDrugPrdtMcpnDtlInq07 은 item_name 무시 + 전체 풀 반환이라
            #     per-품목 매핑 불가 → 상세의 MATERIAL_NAME 을 파싱하는 것이 정확)
            if item_seq:
                try:
                    dr = fetch_approval_detail(item_seq=item_seq, num_of_rows=1)
                    if dr.get("items"):
                        d = dr["items"][0]
                        result.update(_from_detail(d))
                        result["ingredients"] = _parse_material(d.get("MATERIAL_NAME"))
                except Exception as e:
                    logger.debug(f"[{item_code}] 상세 실패: {e}")
            return result
    except Exception as e:
        logger.warning(f"[{item_code}] NO140 조회 실패: {e}")

    # 4) NO 145 의약외품 폴백
    try:
        q = fetch_quasi_approval(item_name=raw_name.split("(")[0], num_of_rows=10)
        qc = _company_match(q.get("items", []))
        if qc:
            result.update(_from_list(qc[0]))
            result["enrich_status"] = "matched"
            result["enrich_confidence"] = "medium"
            result["source_api"] = "NO145"
            return result
    except Exception as e:
        logger.debug(f"[{item_code}] NO145 폴백 실패: {e}")

    # 5) [hook] NO 35 한약 폴백 — 미신청 (endpoint 채워지면 활성)
    # try:
    #     h = fetch_herbal_approval(item_name=raw_name); ... source_api='NO35'
    # except Exception: pass

    return result  # unmatched


def _from_list(it: Dict) -> Dict:
    return {
        "item_seq": it.get("ITEM_SEQ"),
        "permit_no": it.get("PRDUCT_PRMISN_NO"),
        "permit_date": it.get("ITEM_PERMIT_DATE"),
        "entp_name": it.get("ENTP_NAME"),
    }


def _from_detail(d: Dict) -> Dict:
    return {
        "reexam_date": d.get("REEXAM_DATE") or None,
        "atc_code": d.get("ATC_CODE") or None,
        "edi_code": d.get("EDI_CODE") or None,
        "bar_code": d.get("BAR_CODE") or None,
        "chart": d.get("CHART") or None,
        "storage_method": d.get("STORAGE_METHOD") or None,
        "material_name": d.get("MATERIAL_NAME") or None,
    }


def _parse_material(material_name: Optional[str]) -> List[Dict]:
    """
    NO 140 상세 MATERIAL_NAME 파싱 → 성분 리스트.
    형식(파이프 구분, 다성분 시 성분명 블록 반복):
      "총량 : 1정(약 127.9밀리그램) 중|성분명 : 알프라졸람|분량 : 0.5|단위 : 밀리그램|규격 : USP|...|성분명 : B|분량 : ..|단위 : .."
    """
    if not material_name:
        return []
    out: List[Dict] = []
    cur: Dict = {}
    for part in material_name.split("|"):
        if ":" not in part:
            continue
        k, _, v = part.partition(":")
        k, v = k.strip(), v.strip()
        if k == "성분명":
            if cur.get("ingr_name"):
                out.append(cur)
                cur = {}
            cur["ingr_name"] = v
        elif k == "분량":
            cur["qty"] = v
        elif k == "단위":
            cur["unit"] = v
    if cur.get("ingr_name"):
        out.append(cur)
    # ingr_code 는 MATERIAL_NAME 에 없음 → None
    for o in out:
        o.setdefault("ingr_code", None)
    return out


# ────────────────────────────────────────────────────────────────────────────
# DB 반영
# ────────────────────────────────────────────────────────────────────────────
_UPDATE = """
UPDATE master_item SET
  item_seq=:item_seq, permit_no=:permit_no, permit_date=:permit_date,
  reexam_date=:reexam_date, entp_name=:entp_name, atc_code=:atc_code,
  edi_code=:edi_code, bar_code=:bar_code, chart=:chart,
  storage_method=:storage_method, material_name=:material_name,
  source_api=:source_api, enrich_status=:enrich_status,
  enrich_confidence=:enrich_confidence, enrich_candidates=:enrich_candidates,
  enriched_at=CURRENT_TIMESTAMP
WHERE item_code=:item_code
"""


def _persist(res: Dict) -> None:
    conn = qadb.get_conn()
    try:
        params = {
            "item_code": res["item_code"],
            "item_seq": res.get("item_seq"), "permit_no": res.get("permit_no"),
            "permit_date": res.get("permit_date"), "reexam_date": res.get("reexam_date"),
            "entp_name": res.get("entp_name"), "atc_code": res.get("atc_code"),
            "edi_code": res.get("edi_code"), "bar_code": res.get("bar_code"),
            "chart": res.get("chart"), "storage_method": res.get("storage_method"),
            "material_name": res.get("material_name"),
            "source_api": res.get("source_api"), "enrich_status": res.get("enrich_status"),
            "enrich_confidence": res.get("enrich_confidence"),
            "enrich_candidates": qadb.jdump(res["candidates"]) if res.get("candidates") else None,
        }
        conn.execute(_UPDATE, params)
        # 성분 재적재 (idempotent: 기존 삭제 후 삽입)
        conn.execute("DELETE FROM master_ingredient WHERE item_code=?", (res["item_code"],))
        for ing in res.get("ingredients", []):
            conn.execute(
                "INSERT INTO master_ingredient (item_code, ingr_name, ingr_code, qty, unit) VALUES (?,?,?,?,?)",
                (res["item_code"], ing["ingr_name"], ing.get("ingr_code"), ing.get("qty"), ing.get("unit")),
            )
        conn.commit()
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════════════════════
# Phase M1-3 — product_master(item_seq 기준) 단일 품목 enrich
#   기존 master_item(item_code) enrichment 와 별개. 스크린샷 9탭 마스터용.
# ════════════════════════════════════════════════════════════════════════════
def enrich_product(item_seq: str, edi_code: Optional[str] = None,
                   product_name: Optional[str] = None) -> Dict:
    """
    품목기준코드(item_seq)로 규제 API 조회 → product_master/product_ingredient 보강.
    NO 140(허가 목록·상세, edi_code 우선) + NO 563(낱알) 사용.
    반환: 보강된 info dict (enrich_status: matched|unmatched).
    """
    from ...api_client import fetch_approval, fetch_approval_detail, fetch_identification

    info: Dict = {"item_seq": item_seq, "product_name": product_name,
                  "edi_code": edi_code, "enrich_status": "unmatched"}

    # 1) NO 140 목록 — edi_code 우선, item_name 폴백 (API_REFERENCE §5.1)
    appr: Dict = {}
    try:
        if edi_code:
            r = fetch_approval(edi_code=edi_code, num_of_rows=1, merge_excel=False)
            if r.get("items"):
                appr = r["items"][0]
        if not appr and product_name:
            r = fetch_approval(item_name=product_name.split("(")[0], num_of_rows=5, merge_excel=False)
            cands = _company_match(r.get("items", [])) or r.get("items", [])
            for c in cands:
                if c.get("ITEM_SEQ") == item_seq:
                    appr = c
                    break
            if not appr and cands:
                appr = cands[0]
    except Exception as e:
        logger.warning(f"enrich_product[{item_seq}] NO140 목록 실패: {e}")

    if appr:
        info["enrich_status"] = "matched"
        info["item_seq"] = appr.get("ITEM_SEQ") or item_seq
        info["product_name"] = appr.get("ITEM_NAME") or product_name
        info["etc_otc"] = appr.get("SPCLTY_PBLC") or appr.get("ETC_OTC_CODE")
        info["permit_type"] = appr.get("PERMIT_KIND_CODE")
        info["permit_date"] = appr.get("ITEM_PERMIT_DATE")
        info["permit_holder"] = appr.get("ENTP_NAME")
        info["permit_no"] = appr.get("PRDUCT_PRMISN_NO")
        info["form_type"] = appr.get("PRDUCT_TYPE")
        info["pill_image_url"] = appr.get("BIG_PRDT_IMG_URL")
        if appr.get("EDI_CODE"):
            info["edi_code"] = appr["EDI_CODE"].split(",")[0]

    # 2) NO 140 상세 — REEXAM_DATE·ATC·CHART·STORAGE·MATERIAL_NAME
    seq = info.get("item_seq") or item_seq
    detail: Dict = {}
    try:
        dr = fetch_approval_detail(item_seq=seq, num_of_rows=1)
        if not dr.get("items") and edi_code:
            dr = fetch_approval_detail(edi_code=edi_code, num_of_rows=1)
        if dr.get("items"):
            detail = dr["items"][0]
    except Exception as e:
        logger.warning(f"enrich_product[{item_seq}] NO140 상세 실패: {e}")
    if detail:
        info["enrich_status"] = "matched"
        info["appearance"] = detail.get("CHART") or info.get("appearance")
        info["storage_temp"] = detail.get("STORAGE_METHOD")
        info["shelf_life_dom"] = detail.get("VALID_TERM")
        info["atc_code"] = detail.get("ATC_CODE")
        info["reexam_date"] = detail.get("REEXAM_DATE")
        info["material_name"] = detail.get("MATERIAL_NAME")
        if not info.get("edi_code") and detail.get("EDI_CODE"):
            info["edi_code"] = detail["EDI_CODE"].split(",")[0]
        if not info.get("permit_date"):
            info["permit_date"] = detail.get("ITEM_PERMIT_DATE")
        if not info.get("permit_holder"):
            info["permit_holder"] = detail.get("ENTP_NAME")

    # 3) NO 563 낱알식별 → pill_image_url
    if not info.get("pill_image_url"):
        try:
            pname = (info.get("product_name") or product_name or "").split("(")[0]
            if pname:
                idr = fetch_identification(item_name=pname, num_of_rows=1)
                if idr.get("items"):
                    info["pill_image_url"] = idr["items"][0].get("ITEM_IMAGE")
        except Exception as e:
            logger.debug(f"enrich_product[{item_seq}] 낱알 실패: {e}")

    # 4) product_master UPSERT
    _upsert_product_master(info, fallback_name=product_name)

    # 5) 원약분량 — MATERIAL_NAME 파싱 → product_ingredient
    ings = _parse_material(info.get("material_name"))
    final_seq = info.get("item_seq") or item_seq
    if ings:
        qadb.execute("DELETE FROM product_ingredient WHERE item_seq=?", (final_seq,))
        for ing in ings:
            qadb.execute(
                """INSERT INTO product_ingredient
                   (item_seq, ingr_name, permit_qty, unit, purpose) VALUES (?,?,?,?,?)""",
                (final_seq, ing.get("ingr_name"), ing.get("qty"), ing.get("unit"), "주성분"))
    info["ingredients"] = ings
    return info


def _upsert_product_master(info: Dict, fallback_name: Optional[str] = None) -> None:
    seq = info.get("item_seq")
    name = info.get("product_name") or fallback_name or seq
    qadb.execute(
        """INSERT INTO product_master
             (item_seq, product_name, appearance, form_type, etc_otc, permit_type, permit_date,
              permit_holder, permit_no, storage_temp, shelf_life_dom, storage_cont, edi_code,
              atc_code, reexam_date, material_name, pill_image_url, enrich_status, enriched_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))
           ON CONFLICT(item_seq) DO UPDATE SET
             product_name=excluded.product_name, appearance=excluded.appearance,
             form_type=excluded.form_type, etc_otc=excluded.etc_otc, permit_type=excluded.permit_type,
             permit_date=excluded.permit_date, permit_holder=excluded.permit_holder, permit_no=excluded.permit_no,
             storage_temp=excluded.storage_temp, shelf_life_dom=excluded.shelf_life_dom,
             edi_code=excluded.edi_code, atc_code=excluded.atc_code, reexam_date=excluded.reexam_date,
             material_name=excluded.material_name, pill_image_url=excluded.pill_image_url,
             enrich_status=excluded.enrich_status, enriched_at=datetime('now'), updated_at=datetime('now')""",
        (seq, name, info.get("appearance"), info.get("form_type"), info.get("etc_otc"),
         info.get("permit_type"), info.get("permit_date"), info.get("permit_holder"),
         info.get("permit_no"), info.get("storage_temp"), info.get("shelf_life_dom"),
         info.get("storage_cont"), info.get("edi_code"), info.get("atc_code"),
         info.get("reexam_date"), info.get("material_name"), info.get("pill_image_url"),
         info.get("enrich_status", "unmatched")))


# ────────────────────────────────────────────────────────────────────────────
# 배치 실행 (CLI + 백그라운드)
# ────────────────────────────────────────────────────────────────────────────
def _target_items(only_pending: bool = True, limit: Optional[int] = None) -> List[Dict]:
    sql = "SELECT * FROM master_item WHERE active=1"
    if only_pending:
        sql += " AND enrich_status IN ('pending','review','unmatched')"
    sql += " ORDER BY item_code"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return qadb.query(sql)


def run_enrichment(only_pending: bool = True, limit: Optional[int] = None,
                   max_workers: int = 10) -> Dict:
    """동기 배치 실행 (CLI/백그라운드 스레드 공용)."""
    import datetime
    items = _target_items(only_pending=only_pending, limit=limit)
    with _LOCK:
        _PROGRESS.update({"running": True, "total": len(items), "done": 0,
                          "matched": 0, "review": 0, "unmatched": 0,
                          "started_at": datetime.datetime.now().isoformat(),
                          "finished_at": None})
    logger.info(f"Enrichment 시작: {len(items)}품목 (workers={max_workers})")

    def _work(it):
        res = enrich_one(it)
        _persist(res)
        return res["enrich_status"]

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_work, it): it for it in items}
        for fut in as_completed(futs):
            try:
                status = fut.result()
            except Exception as e:
                logger.warning(f"enrich 작업 실패: {e}")
                status = "unmatched"
            with _LOCK:
                _PROGRESS["done"] += 1
                if status == "matched":
                    _PROGRESS["matched"] += 1
                elif status == "review":
                    _PROGRESS["review"] += 1
                else:
                    _PROGRESS["unmatched"] += 1

    with _LOCK:
        _PROGRESS["running"] = False
        _PROGRESS["finished_at"] = datetime.datetime.now().isoformat()
        snapshot = dict(_PROGRESS)
    logger.info(f"Enrichment 완료: {snapshot}")
    return snapshot


def run_enrichment_async(only_pending: bool = True, limit: Optional[int] = None) -> bool:
    """백그라운드 스레드로 실행. 이미 실행 중이면 False."""
    with _LOCK:
        if _PROGRESS.get("running"):
            return False
    t = threading.Thread(target=run_enrichment,
                         kwargs={"only_pending": only_pending, "limit": limit},
                         daemon=True)
    t.start()
    return True


def get_progress() -> Dict:
    with _LOCK:
        return dict(_PROGRESS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    import sys
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    s = run_enrichment(only_pending=True, limit=lim)
    total = s["total"] or 1
    print("=" * 50)
    print(f"대상 {s['total']} → matched {s['matched']} / review {s['review']} / unmatched {s['unmatched']}")
    print(f"matched 비율: {s['matched'] / total * 100:.1f}%")
