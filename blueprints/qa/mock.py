"""
KD-IRIS — MOCK(테스트/데모) 데이터 명시 원칙 (사용자 지침)

원칙: 어떤 테스트/데모 데이터도 반드시 mock 으로 명시·표시한다.
  - event.is_mock = 1
  - title 앞에 "[MOCK] " 접두
  - UI(대시보드·이벤트상세)에서 🧪 MOCK 배지 표시
  - purge_mocks() 로 언제든 일괄 삭제 → 실데이터와 영구 분리

실 모니터링(monitor.py)·enrichment 는 절대 이 모듈을 쓰지 않는다 (실데이터는 is_mock=0).
"""
import logging

from . import db as qadb

logger = logging.getLogger(__name__)

MOCK_PREFIX = "[MOCK] "


def inject_mock_event(event_type: str, severity: str, title: str,
                      entity: str = "", summary: str = "",
                      impact_level: str = "direct", event_date: str = "",
                      matched_item_codes=None, raw_payload=None) -> int:
    """
    명시적 mock 이벤트 1건 주입. 항상 is_mock=1 + [MOCK] 접두.
    데모/테스트 외 용도 금지. 반환: event_id.
    """
    title = title if title.startswith(MOCK_PREFIX) else MOCK_PREFIX + title
    eid = qadb.execute(
        """INSERT INTO event
           (event_date, api_id, event_type, severity, impact_level, title, entity, summary,
            matched_item_codes, matched_ingredients, raw_payload, status, is_mock)
           VALUES (?,?,?,?,?,?,?,?,?,?,?, 'new', 1)""",
        (event_date, "MOCK", event_type, severity, impact_level, title, entity, summary,
         qadb.jdump(matched_item_codes or []), qadb.jdump([]),
         qadb.jdump(raw_payload or {"_mock": True})))
    logger.info(f"[MOCK] 이벤트 주입: #{eid} {title}")
    return eid


def inject_demo_gmp(dday: int = 25) -> int:
    """데모용 GMP 만료 D-Day 이벤트 (명시적 MOCK). D-90 알림 로직 시연용."""
    import datetime
    exp = (datetime.date.today() + datetime.timedelta(days=dday)).strftime("%Y%m%d")
    sev = "CRITICAL" if dday <= 30 else "HIGH"
    return inject_mock_event(
        "gmp_expiry", sev, f"광동제약(주) GMP 만료 D-{dday} (데모)",
        entity="광동제약(주)", summary="GMP D-90 알림 로직 시연용 가상 데이터",
        event_date=exp, raw_payload={"_mock": True, "VLD_PRD_YMD": exp})


def purge_mocks() -> int:
    """모든 mock 데이터 일괄 삭제 (event.is_mock=1 + 관련 alert_log)."""
    ids = [r["event_id"] for r in qadb.query("SELECT event_id FROM event WHERE is_mock=1")]
    for eid in ids:
        qadb.execute("DELETE FROM alert_log WHERE event_id=?", (eid,))
    n = qadb.execute("DELETE FROM event WHERE is_mock=1")
    logger.info(f"[MOCK] 일괄 삭제: 이벤트 {len(ids)}건")
    return len(ids)


def count_mocks() -> int:
    try:
        return qadb.query_one("SELECT COUNT(*) n FROM event WHERE is_mock=1")["n"]
    except Exception:
        return 0
