"""
KD-IRIS — 자사 마스터 대조 헬퍼 (기능재설계 v2 §2 S1)

"조회 결과를 항상 자사 마스터와 대조" — 검색/Product360 에서
해당 품목이 자사 품목인지 + enrichment 상태 + 관련 QA 이벤트를 조회.

Flask 비의존 (db.py 만 사용) → 어느 라우트에서나 import 가능.
"""
import logging
from typing import Dict, List, Optional

from . import db as qadb

logger = logging.getLogger(__name__)


def match_own_product(item_seq: Optional[str] = None,
                      edi_code: Optional[str] = None,
                      item_name: Optional[str] = None) -> Optional[Dict]:
    """
    조회 품목이 자사 마스터에 있는지 대조.
    우선순위: item_seq → edi_code → item_name(정확) → item_name(부분).
    반환: master_item row(dict) 또는 None.
    """
    try:
        if item_seq:
            row = qadb.query_one(
                "SELECT * FROM master_item WHERE item_seq=? AND active=1 LIMIT 1", (item_seq,))
            if row:
                return row
        if edi_code:
            row = qadb.query_one(
                "SELECT * FROM master_item WHERE edi_code=? AND active=1 LIMIT 1", (edi_code,))
            if row:
                return row
        if item_name:
            nm = item_name.split("(")[0].strip()
            row = qadb.query_one(
                "SELECT * FROM master_item WHERE item_name=? AND active=1 LIMIT 1", (item_name,))
            if row:
                return row
            # 부분일치 (접두)
            row = qadb.query_one(
                "SELECT * FROM master_item WHERE item_name LIKE ? AND active=1 LIMIT 1", (nm + "%",))
            if row:
                return row
    except Exception as e:
        logger.debug(f"match_own_product 실패(QA DB 미초기화 가능): {e}")
    return None


def events_for_item(item_code: str, limit: int = 10) -> List[Dict]:
    """해당 자사 품목코드에 매칭된 QA 이벤트 (최신순)."""
    if not item_code:
        return []
    try:
        rows = qadb.query(
            """SELECT event_id, event_date, event_type, severity, impact_level, title, entity, status
               FROM event
               WHERE matched_item_codes LIKE ?
               ORDER BY detected_at DESC LIMIT ?""",
            (f'%"{item_code}"%', limit))
        return rows
    except Exception as e:
        logger.debug(f"events_for_item 실패: {e}")
        return []


def own_summary() -> Dict:
    """코파일럿/홈 브리핑용 자사 현황 요약."""
    try:
        total = qadb.query_one("SELECT COUNT(*) n FROM master_item WHERE active=1")["n"]
        matched = qadb.query_one(
            "SELECT COUNT(*) n FROM master_item WHERE active=1 AND enrich_status='matched'")["n"]
        critical = qadb.query_one(
            "SELECT COUNT(*) n FROM event WHERE status!='closed' AND severity='CRITICAL'")["n"]
        unconfirmed = qadb.query_one("SELECT COUNT(*) n FROM event WHERE status='new'")["n"]
        # 90일 이내 재심사 마감
        import datetime
        d90 = (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y%m%d")
        today = datetime.date.today().strftime("%Y%m%d")
        review_due = qadb.query_one(
            """SELECT COUNT(*) n FROM master_item WHERE active=1
               AND reexam_date IS NOT NULL AND reexam_date BETWEEN ? AND ?""", (today, d90))["n"]
        return {"total": total, "matched": matched, "critical": critical,
                "unconfirmed": unconfirmed, "review_due_90": review_due}
    except Exception as e:
        logger.debug(f"own_summary 실패: {e}")
        return {"total": 0, "matched": 0, "critical": 0, "unconfirmed": 0, "review_due_90": 0}
