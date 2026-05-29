"""
KD-IRIS 1차 빌드 — SQLite 연결 헬퍼 (기능재설계 v2 §11.3)

- 요청마다 connection (Flask 스레드 안전)
- row_factory=sqlite3.Row → dict-like 접근
- init_db(): db/schema.sql 멱등 실행 + WAL 모드
"""
import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional

from ...config import DB_PATH, SCHEMA_PATH

logger = logging.getLogger(__name__)


def get_conn() -> sqlite3.Connection:
    """새 SQLite connection 반환 (요청/작업 단위로 열고 닫기)."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    # 외래키 + WAL (읽기/쓰기 락 경합 완화)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db() -> None:
    """db/schema.sql 실행 — 모든 CREATE는 IF NOT EXISTS (멱등)."""
    if not SCHEMA_PATH.exists():
        logger.error(f"스키마 파일 없음: {SCHEMA_PATH}")
        return
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = get_conn()
    try:
        conn.executescript(sql)
        conn.commit()
        logger.info(f"SQLite init_db 완료: {DB_PATH}")
    except Exception as e:
        logger.error(f"init_db 실패: {e}")
        raise
    finally:
        conn.close()


# ────────────────────────────────────────────────────────────────────────────
# 편의 쿼리 헬퍼
# ────────────────────────────────────────────────────────────────────────────

def query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """SELECT → list[dict]."""
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def query_one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """SELECT 단일 행 → dict 또는 None."""
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def execute(sql: str, params: tuple = ()) -> int:
    """INSERT/UPDATE/DELETE → lastrowid (또는 rowcount)."""
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid if cur.lastrowid else cur.rowcount
    finally:
        conn.close()


def executemany(sql: str, seq_params: list) -> int:
    """대량 INSERT/UPSERT → 영향 행수."""
    conn = get_conn()
    try:
        cur = conn.executemany(sql, seq_params)
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def jdump(obj: Any) -> str:
    """JSON 컬럼 직렬화 (한글 유지)."""
    return json.dumps(obj, ensure_ascii=False, default=str)


def jload(s: Optional[str], default=None):
    """JSON 컬럼 역직렬화 (실패 시 default)."""
    if not s:
        return default
    try:
        return json.loads(s)
    except Exception:
        return default
