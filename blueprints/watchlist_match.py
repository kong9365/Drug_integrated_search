"""
RegHub 360 — 워치리스트 ↔ 식약처 이벤트 매칭 엔진

각 워치리스트 항목의 `query` 키워드를 기준으로
회수(NO 539) / 안전성서한(NO 547) / 행정처분(NO 564) / 공급중단(NO 534)
4개 글로벌 API 결과를 한 번만 받고 클라이언트 측에서 부분일치 필터링.

In-memory TTL 캐시(기본 300초)로 같은 페이지를 새로 고침해도 API 재호출 없음.
프로세스 재시작 시 캐시는 비워짐.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import List, Dict, Tuple

from ..api_client import fetch_recall, fetch_disciplinary
from ..api_extras import (
    fetch_drug_safety_letter, fetch_drug_supply_stop,
    fetch_drug_patent, fetch_drug_clinical,
    fetch_drug_review, fetch_drug_reeval,
)

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# In-memory TTL cache for global API responses
# ────────────────────────────────────────────────────────────────────────────
_CACHE_TTL_SEC = 300  # 5분
_CACHE_LOCK = threading.Lock()
_CACHE: Dict[str, Tuple[float, List[Dict]]] = {}


def _cached(key: str, fetcher, num_of_rows: int = 200) -> List[Dict]:
    now = time.time()
    with _CACHE_LOCK:
        ent = _CACHE.get(key)
        if ent and (now - ent[0]) < _CACHE_TTL_SEC:
            return ent[1]
    # 락 밖에서 fetch
    try:
        resp = fetcher(num_of_rows=num_of_rows)
        items = resp.get("items", []) or []
    except Exception as e:
        logger.warning(f"watchlist_match {key} fetch 실패: {e}")
        items = []
    with _CACHE_LOCK:
        _CACHE[key] = (now, items)
    return items


def _filter(items: List[Dict], needle: str, fields: List[str]) -> List[Dict]:
    if not needle:
        return []
    n = needle.lower()
    out = []
    for it in items:
        for f in fields:
            v = it.get(f)
            if v and n in str(v).lower():
                out.append(it)
                break
    return out


# 필드 매핑 — 각 API의 응답 필드명이 다르므로 명시
_FIELDS = {
    # 기존 4종 (NO 539·547·564·534)
    "recalls":   ["PRDUCT", "ENTRPS", "ITEM_NAME", "ENTP_NAME"],
    "safety":    ["TITLE", "SUMRY_CONT", "SUMMARY", "DETAIL_CN", "TBL_CN"],
    "sanctions": ["ENTP_NAME", "ITEM_NAME", "ENTRPS_NAME", "VIOLATION_DETAIL"],
    "supply":    ["ENTP_NAME", "ITEM_NAME", "PRDUCT", "ENTRPS_NAME"],
    # 추가 R&D 4종 (NO 561·566·554·556)
    "patent":    ["ITEM_NAME", "INGR_NAME", "ENTP_NAME"],
    "clinical":  ["GOODS_NAME", "APPLY_ENTP_NAME", "CLINIC_EXAM_TITLE"],
    "review":    ["ITEM_NAME", "ENTP_NAME"],
    "reeval":    ["ITEM_NAME", "ENTP_NAME"],
}


def _normalize_event(kind: str, raw: Dict) -> Dict:
    """
    API별 필드명 차이를 흡수해 템플릿 공통 스키마로 반환.

    공통 출력 키 (KD-IRIS v3 §3.3):
      type / type_label / severity_level / severity_color
      title / entity / summary / date / is_new / product_code / in_watchlist
    """
    from datetime import date as _date
    from .severity import get_severity

    # severity 라벨/색상은 단일 SEVERITY_MAP에서
    # 내부 kind 키 매핑 (legacy 호환)
    _kind_map = {
        "recall":   "recall",
        "safety":   "safety_letter",
        "sanction": "disciplinary",
        "supply":   "supply_stop",
        "patent":   "patent_new",
        "clinical": "clinical_new",
        "review":   "review_due",
        "reeval":   "reeval_done",
    }
    canonical = _kind_map.get(kind, kind)
    sev = get_severity(canonical)

    today = _date.today().isoformat()

    # 필드별 raw 추출
    if kind == "recall":
        title  = (raw.get("PRDUCT") or "(품목 미상)")[:60]
        entity = raw.get("ENTRPS") or ""
        summary= (raw.get("RTRVL_RESN") or "")[:100]
        date   = (raw.get("RECALL_COMMAND_DATE") or "")[:10]
        code   = raw.get("ITEM_SEQ") or ""
    elif kind == "safety":
        title  = (raw.get("TITLE") or "")[:60]
        entity = raw.get("PBANC_DIVS_NM") or ""
        summary= (raw.get("SUMRY_CONT") or "")[:100]
        date   = (raw.get("PBANC_YMD") or "")[:10]
        code   = raw.get("ITEM_SEQ") or ""
    elif kind == "sanction":
        title  = (raw.get("ENTP_NAME") or raw.get("ENTRPS_NAME") or "(업체 미상)")[:60]
        entity = raw.get("ENTP_NAME") or raw.get("ENTRPS_NAME") or ""
        summary= (raw.get("VIOLATION_DETAIL") or raw.get("VIOLATION_LAW") or "")[:100]
        date   = (raw.get("DSPS_DCSNDT") or "")[:10]
        code   = ""
    elif kind == "supply":
        title  = (raw.get("ITEM_NAME") or "(품목 미상)")[:60]
        entity = raw.get("ENTP_NAME") or ""
        summary= (raw.get("REPORT_PGS_CODE") or "") + (" · " + raw.get("SUSPEND_REPORT_FLAG") if raw.get("SUSPEND_REPORT_FLAG") else "")
        date   = ""
        code   = raw.get("ITEM_SEQ") or ""
    elif kind == "patent":
        title  = (raw.get("ITEM_NAME") or raw.get("PAT_NO") or "(특허 미상)")[:60]
        entity = raw.get("ENTP_NAME") or ""
        summary= (raw.get("INGR_NAME") or "")[:100]
        date   = (raw.get("EXPIRE_DATE") or "")[:10]
        code   = ""
    elif kind == "clinical":
        title  = (raw.get("GOODS_NAME") or "(임상 미상)")[:60]
        entity = raw.get("APPLY_ENTP_NAME") or ""
        summary= (raw.get("CLINIC_EXAM_TITLE") or "")[:100]
        date   = ""
        code   = ""
    elif kind == "review":
        title  = (raw.get("ITEM_NAME") or "(품목 미상)")[:60]
        entity = raw.get("ENTP_NAME") or ""
        summary= "재심사 일정"
        date   = (raw.get("REJDGE_DT") or "")[:10]
        code   = raw.get("ITEM_SEQ") or ""
    elif kind == "reeval":
        title  = (raw.get("ITEM_NAME") or "(품목 미상)")[:60]
        entity = raw.get("ENTP_NAME") or ""
        summary= "재평가 결과"
        date   = (raw.get("REVAL_DT") or "")[:10]
        code   = raw.get("ITEM_SEQ") or ""
    else:
        title, entity, summary, date, code = "(미상)", "", "", "", ""

    return {
        "type":           canonical,
        "type_label":     sev["label"],
        "severity_level": sev["level"],
        "severity_color": sev["color"],
        "title":          title,
        "entity":         entity,
        "summary":        summary,
        "date":           date,
        "is_new":         bool(date) and date == today,
        "product_code":   code,
        "in_watchlist":   False,
    }


def match_for_entries(entries: List[Dict]) -> Dict[str, Dict]:
    """
    워치리스트 항목들에 대한 식약처 이벤트 매칭을 한 번에 수행.

    Returns:
        {entry_id: {
            "recalls": [...], "safety": [...], "sanctions": [...], "supply": [...],
            "events": [정규화된 이벤트 최신순 top 3],
            "counts": {"recall": N, "safety": N, "sanction": N, "supply": N, "total": N},
        }}
    """
    empty_result = {
        "recalls": [], "safety": [], "sanctions": [], "supply": [],
        "patent": [], "clinical": [], "review": [], "reeval": [],
        "events": [],
        "counts": {
            "recall": 0, "safety": 0, "sanction": 0, "supply": 0,
            "patent": 0, "clinical": 0, "review": 0, "reeval": 0,
            "total": 0,
        },
    }

    if not entries:
        return {}

    # 글로벌 API 8종을 한 번만 fetch (캐시 적용)
    recalls    = _cached("recall",     fetch_recall,             num_of_rows=200)
    safety     = _cached("safety",     fetch_drug_safety_letter, num_of_rows=200)
    sanctions  = _cached("sanction",   fetch_disciplinary,       num_of_rows=200)
    supply     = _cached("supply",     fetch_drug_supply_stop,   num_of_rows=200)
    patent     = _cached("patent",     fetch_drug_patent,        num_of_rows=200)
    clinical   = _cached("clinical",   fetch_drug_clinical,      num_of_rows=200)
    review     = _cached("review",     fetch_drug_review,        num_of_rows=200)
    reeval     = _cached("reeval",     fetch_drug_reeval,        num_of_rows=200)

    out: Dict[str, Dict] = {}
    for e in entries:
        q = (e.get("query") or "").strip()
        if not q:
            out[e["id"]] = dict(empty_result)
            continue

        r_hits = _filter(recalls,   q, _FIELDS["recalls"])
        s_hits = _filter(safety,    q, _FIELDS["safety"])
        d_hits = _filter(sanctions, q, _FIELDS["sanctions"])
        u_hits = _filter(supply,    q, _FIELDS["supply"])
        p_hits = _filter(patent,    q, _FIELDS["patent"])
        c_hits = _filter(clinical,  q, _FIELDS["clinical"])
        rv_hits = _filter(review,   q, _FIELDS["review"])
        re_hits = _filter(reeval,   q, _FIELDS["reeval"])

        # 정규화 + 최신 3건만 (날짜 내림차순) — 8종 통합
        events = (
            [_normalize_event("recall",   r) for r in r_hits[:5]] +
            [_normalize_event("safety",   s) for s in s_hits[:5]] +
            [_normalize_event("sanction", d) for d in d_hits[:5]] +
            [_normalize_event("supply",   u) for u in u_hits[:5]] +
            [_normalize_event("patent",   p) for p in p_hits[:5]] +
            [_normalize_event("clinical", c) for c in c_hits[:5]] +
            [_normalize_event("review",   v) for v in rv_hits[:5]] +
            [_normalize_event("reeval",   e2) for e2 in re_hits[:5]]
        )
        events.sort(key=lambda x: x.get("date", ""), reverse=True)
        events = events[:3]

        out[e["id"]] = {
            "recalls": r_hits[:10], "safety": s_hits[:10],
            "sanctions": d_hits[:10], "supply": u_hits[:10],
            "patent": p_hits[:10], "clinical": c_hits[:10],
            "review": rv_hits[:10], "reeval": re_hits[:10],
            "events": events,
            "counts": {
                "recall":   len(r_hits),
                "safety":   len(s_hits),
                "sanction": len(d_hits),
                "supply":   len(u_hits),
                "patent":   len(p_hits),
                "clinical": len(c_hits),
                "review":   len(rv_hits),
                "reeval":   len(re_hits),
                "total":    (len(r_hits) + len(s_hits) + len(d_hits) + len(u_hits)
                             + len(p_hits) + len(c_hits) + len(rv_hits) + len(re_hits)),
            },
        }
    return out


def total_alert_count(match_map: Dict[str, Dict]) -> int:
    """모든 항목의 매칭 이벤트 총합."""
    return sum(m["counts"]["total"] for m in match_map.values())


def invalidate_cache() -> None:
    """캐시 비우기 — 디버깅/테스트용."""
    with _CACHE_LOCK:
        _CACHE.clear()
