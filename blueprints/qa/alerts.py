"""
KD-IRIS 1차 빌드 — Slack 알람 추상화 (기능재설계 v2 §5.4)

룰 → 채널 매핑은 환경변수(`SLACK_CHANNEL_{TEAM}`).
채널 미설정 시 dry-run: 콘솔 로그 + alert_log 테이블 적재.
채널 설정 시 slack-sdk 로 실발송 (slack-sdk 미설치여도 graceful).

post_alert(team, severity, payload) — 단일 진입점.
post_event_alerts(event) — event dict 받아 팀 라우팅 + post_alert 호출.
"""
import logging
import os

from . import db as qadb

logger = logging.getLogger(__name__)

# severity → 색상 (Slack attachment)
_SEV_COLOR = {"CRITICAL": "#e53935", "HIGH": "#fb8c00", "LOW": "#43a047"}

# 이벤트 타입 → 담당 팀 (1차는 의약품QA 단일, 추후 RA/구매/생산 확장)
_EVENT_TEAM = {
    "recall": "DRUG_QA",
    "disciplinary": "DRUG_QA",
    "safety_letter": "DRUG_QA",
    "gmp_expiry": "DRUG_QA",
}


def _slack_client():
    """slack-sdk WebClient (토큰 있을 때만). 미설치/미설정 시 None."""
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        return None
    try:
        from slack_sdk import WebClient
        return WebClient(token=token)
    except ImportError:
        logger.warning("slack-sdk 미설치 — dry-run 으로 폴백 (pip install slack-sdk)")
        return None


def _render_text(severity: str, payload: dict) -> str:
    """알람 메시지 텍스트 (severity 헤더 + 자사품목 + 사유 + 권장액션 + deep link)."""
    head = {"CRITICAL": "🔴 긴급", "HIGH": "🟡 주의", "LOW": "🟢 정보"}.get(severity, severity)
    lines = [
        f"*{head}* — {payload.get('title', '(제목 없음)')}",
        f"업체: {payload.get('entity', '-')}",
    ]
    if payload.get("matched_items"):
        lines.append(f"자사 품목: {', '.join(payload['matched_items'][:5])}")
    if payload.get("summary"):
        lines.append(f"내용: {payload['summary'][:150]}")
    if payload.get("action"):
        lines.append(f"권장액션: {payload['action']}")
    if payload.get("deep_link"):
        lines.append(f"<{payload['deep_link']}|상세 보기>")
    return "\n".join(lines)


def post_alert(team: str, severity: str, payload: dict, event_id: int = None) -> dict:
    """
    단일 알람 발송. 채널 env(SLACK_CHANNEL_{TEAM}) 없으면 dry-run.
    반환: {channel, dry_run, ok}
    """
    channel = os.getenv(f"SLACK_CHANNEL_{team.upper()}")
    text = _render_text(severity, payload)
    client = _slack_client()

    if not channel or client is None:
        # dry-run — 콘솔 + alert_log
        logger.info(f"[ALERT DRY-RUN] team={team} sev={severity}\n{text}")
        _log_alert(event_id, team, "DRY_RUN", payload)
        return {"channel": "DRY_RUN", "dry_run": True, "ok": True}

    try:
        client.chat_postMessage(
            channel=channel, text=text,
            attachments=[{"color": _SEV_COLOR.get(severity, "#999"), "text": text}])
        _log_alert(event_id, team, channel, payload)
        return {"channel": channel, "dry_run": False, "ok": True}
    except Exception as e:
        logger.error(f"Slack 발송 실패: {e}")
        _log_alert(event_id, team, f"FAILED:{channel}", payload)
        return {"channel": channel, "dry_run": False, "ok": False, "error": str(e)}


def _log_alert(event_id, team, channel, payload):
    try:
        qadb.execute(
            "INSERT INTO alert_log (event_id, team, channel, payload) VALUES (?,?,?,?)",
            (event_id, team, channel, qadb.jdump(payload)))
    except Exception as e:
        logger.warning(f"alert_log 적재 실패: {e}")


def post_event_alerts(event: dict) -> dict:
    """
    event dict → 팀 라우팅 + 알람 발송.
    CRITICAL/HIGH 만 발송 (LOW 는 일 다이제스트 — 1차 미구현).
    """
    if event.get("severity") not in ("CRITICAL", "HIGH"):
        return {"skipped": True}
    team = _EVENT_TEAM.get(event.get("event_type"), "DRUG_QA")
    payload = {
        "title": event.get("title"),
        "entity": event.get("entity"),
        "summary": event.get("summary"),
        "matched_items": event.get("matched_item_codes") or [],
        "action": {"recall": "자사 영향 평가 → 라벨 검토 → 회수 공문",
                   "gmp_expiry": "GMP 갱신 일정 확인",
                   "disciplinary": "처분 내용·자사 위반여부 점검"}.get(event.get("event_type"), "영향 평가"),
        "deep_link": f"/app/qa/event/{event.get('event_id')}" if event.get("event_id") else None,
    }
    return post_alert(team, event["severity"], payload, event_id=event.get("event_id"))


def dispatch_new_events() -> dict:
    """미발송(new, CRITICAL/HIGH) 이벤트 일괄 알람. monitor 후 호출."""
    rows = qadb.query(
        """SELECT e.* FROM event e
           WHERE e.status='new' AND e.severity IN ('CRITICAL','HIGH')
             AND NOT EXISTS (SELECT 1 FROM alert_log a WHERE a.event_id = e.event_id)""")
    sent = 0
    for ev in rows:
        ev["matched_item_codes"] = qadb.jload(ev.get("matched_item_codes"), [])
        r = post_event_alerts(ev)
        if r.get("ok"):
            sent += 1
    logger.info(f"이벤트 알람 디스패치: {sent}/{len(rows)}건")
    return {"candidates": len(rows), "sent": sent}
