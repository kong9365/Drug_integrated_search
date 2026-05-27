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
from ..api_extras import fetch_drug_safety_letter, fetch_drug_supply_stop

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
    "recalls":   ["PRDUCT", "ENTRPS", "ITEM_NAME", "ENTP_NAME"],
    "safety":    ["TITLE", "SUMRY_CONT", "SUMMARY", "DETAIL_CN", "TBL_CN"],
    "sanctions": ["ENTP_NAME", "ITEM_NAME", "ENTRPS_NAME", "VIOLATION_DETAIL"],
    "supply":    ["ENTP_NAME", "ITEM_NAME", "PRDUCT", "ENTRPS_NAME"],
}


def _normalize_event(kind: str, raw: Dict) -> Dict:
    """API별 필드명 차이를 흡수해서 템플릿이 공통 키로 접근 가능하게."""
    if kind == "recall":
        return {
            "kind": "recall", "kind_kr": "회수·판매중지", "severity": "HIGH",
            "title": (raw.get("PRDUCT") or "(품목 미상)")[:60],
            "meta": (raw.get("RTRVL_RESN") or "")[:80] + (" · " + raw.get("ENTRPS") if raw.get("ENTRPS") else ""),
            "date": (raw.get("RECALL_COMMAND_DATE") or "")[:10],
            "api": "NO 539",
        }
    if kind == "safety":
        return {
            "kind": "safety", "kind_kr": "안전성서한", "severity": "MED",
            "title": (raw.get("TITLE") or "")[:60],
            "meta": (raw.get("SUMRY_CONT") or "")[:80],
            "date": (raw.get("PBANC_YMD") or "")[:10],
            "api": "NO 547",
        }
    if kind == "sanction":
        return {
            "kind": "sanction", "kind_kr": "행정처분", "severity": "MED",
            "title": (raw.get("ENTP_NAME") or "(업체 미상)")[:60],
            "meta": (raw.get("VIOLATION_DETAIL") or raw.get("VIOLATION_LAW") or "")[:80],
            "date": (raw.get("DSPS_DCSNDT") or "")[:10],
            "api": "NO 564",
        }
    if kind == "supply":
        return {
            "kind": "supply", "kind_kr": "공급중단", "severity": "HIGH",
            "title": (raw.get("ITEM_NAME") or "(품목 미상)")[:60],
            "meta": (raw.get("ENTP_NAME") or "") + " · " + (raw.get("REPORT_PGS_CODE") or ""),
            "date": "",
            "api": "NO 534",
        }
    return {"kind": kind, "title": "(미상)", "meta": "", "date": "", "api": ""}


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
    if not entries:
        return {}

    # 글로벌 API 4종을 한 번만 fetch (캐시 적용)
    recalls   = _cached("recall",    fetch_recall,             num_of_rows=200)
    safety    = _cached("safety",    fetch_drug_safety_letter, num_of_rows=200)
    sanctions = _cached("sanction",  fetch_disciplinary,       num_of_rows=200)
    supply    = _cached("supply",    fetch_drug_supply_stop,   num_of_rows=200)

    out: Dict[str, Dict] = {}
    for e in entries:
        q = (e.get("query") or "").strip()
        if not q:
            out[e["id"]] = {
                "recalls": [], "safety": [], "sanctions": [], "supply": [],
                "events": [],
                "counts": {"recall": 0, "safety": 0, "sanction": 0, "supply": 0, "total": 0},
            }
            continue

        r_hits = _filter(recalls,   q, _FIELDS["recalls"])
        s_hits = _filter(safety,    q, _FIELDS["safety"])
        d_hits = _filter(sanctions, q, _FIELDS["sanctions"])
        u_hits = _filter(supply,    q, _FIELDS["supply"])

        # 정규화 + 최신 3건만 (날짜 내림차순)
        events = (
            [_normalize_event("recall",   r) for r in r_hits[:5]] +
            [_normalize_event("safety",   s) for s in s_hits[:5]] +
            [_normalize_event("sanction", d) for d in d_hits[:5]] +
            [_normalize_event("supply",   u) for u in u_hits[:5]]
        )
        events.sort(key=lambda x: x.get("date", ""), reverse=True)
        events = events[:3]

        out[e["id"]] = {
            "recalls": r_hits[:10], "safety": s_hits[:10],
            "sanctions": d_hits[:10], "supply": u_hits[:10],
            "events": events,
            "counts": {
                "recall":   len(r_hits),
                "safety":   len(s_hits),
                "sanction": len(d_hits),
                "supply":   len(u_hits),
                "total":    len(r_hits) + len(s_hits) + len(d_hits) + len(u_hits),
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
