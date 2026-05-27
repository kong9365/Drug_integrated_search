"""
RegHub 360 — 워치리스트 저장소 (JSON 영속화)

단일 사용자(김QA · QA/QC팀) 기준의 가벼운 저장소.
프로세스 재시작 후에도 유지되도록 data/watchlist.json 에 직렬화.

엔트리 스키마:
  {
    "id": str        # 고유 ID (timestamp 기반)
    "query": str     # 검색 시 사용할 키워드 (예: "베니톨정", "광동제약")
    "label": str     # 표시명 (예: "베니톨정 / 광동제약")
    "kind": str      # "product" | "company" | "ingredient" | "other"
    "note": str      # 메모(선택)
    "added_at": str  # ISO 포맷 timestamp
  }
"""
from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from ..config import BASE_DIR

logger = logging.getLogger(__name__)

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
WATCHLIST_PATH = DATA_DIR / "watchlist.json"

# 동시 쓰기 방지 — Flask debug 서버는 단일 스레드지만, 운영 시 멀티스레드 가능
_LOCK = threading.Lock()

_ALLOWED_KINDS = {"product", "company", "ingredient", "other"}


def _read_raw() -> List[Dict]:
    if not WATCHLIST_PATH.exists():
        return []
    try:
        with WATCHLIST_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.warning(f"watchlist.json 읽기 실패: {e} — 빈 리스트로 폴백")
        return []


def _write_raw(items: List[Dict]) -> None:
    tmp = WATCHLIST_PATH.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    tmp.replace(WATCHLIST_PATH)


def list_entries() -> List[Dict]:
    """추가된 워치리스트 항목을 최신순으로 반환."""
    with _LOCK:
        items = _read_raw()
    # added_at 내림차순(가장 최근이 위로)
    items.sort(key=lambda e: e.get("added_at", ""), reverse=True)
    return items


def add_entry(query: str, label: str = "", kind: str = "product", note: str = "") -> Optional[Dict]:
    """새 항목 추가. query 가 비어있으면 None 반환.
    동일 query+kind 가 이미 있으면 중복 추가 안 함(기존 그대로)."""
    query = (query or "").strip()
    if not query:
        return None
    kind = kind if kind in _ALLOWED_KINDS else "other"
    label = (label or query).strip()
    note = (note or "").strip()
    entry = {
        "id": f"w{int(time.time() * 1000)}",
        "query": query,
        "label": label,
        "kind": kind,
        "note": note,
        "added_at": datetime.now().isoformat(timespec="seconds"),
    }
    with _LOCK:
        items = _read_raw()
        # 중복 검사 (대소문자 무시)
        norm = (query.lower(), kind)
        for it in items:
            if (it.get("query", "").lower(), it.get("kind")) == norm:
                return it  # 기존 항목 반환
        items.append(entry)
        _write_raw(items)
    logger.info(f"워치리스트 추가: {label} ({kind})")
    return entry


def delete_entry(entry_id: str) -> bool:
    """ID 기준 삭제. 성공 시 True."""
    if not entry_id:
        return False
    with _LOCK:
        items = _read_raw()
        new_items = [it for it in items if it.get("id") != entry_id]
        if len(new_items) == len(items):
            return False
        _write_raw(new_items)
    logger.info(f"워치리스트 삭제: {entry_id}")
    return True


def count() -> int:
    """현재 등록 항목 수."""
    with _LOCK:
        return len(_read_raw())
