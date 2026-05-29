"""
KD-IRIS — 모니터링 야간 배치 스케줄러 (의존성 없는 daemon thread)

DAILY_BATCH_HOUR(기본 새벽 3시)에 monitor.run_monitor() 자동 실행.
외부 라이브러리(APScheduler 등) 없이 표준 threading 만 사용.

- start_scheduler(): 서빙 진입점(run.py/app.py __main__)에서 1회 호출.
  CLI·테스트 import 시에는 자동 시작 안 함 (의도치 않은 배치 방지).
- get_status(): 대시보드 노출용 (last_run / next_run / running).
"""
import datetime
import logging
import threading
import time

from ...config import DAILY_BATCH_HOUR

logger = logging.getLogger(__name__)

_STATE = {"started": False, "last_run": None, "next_run": None,
          "last_result": None, "running": False}
_LOCK = threading.Lock()


def _seconds_until(hour: int) -> float:
    now = datetime.datetime.now()
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return (target - now).total_seconds()


def _loop():
    while True:
        wait = _seconds_until(DAILY_BATCH_HOUR)
        with _LOCK:
            _STATE["next_run"] = (datetime.datetime.now()
                                  + datetime.timedelta(seconds=wait)).isoformat(timespec="minutes")
        # 길게 한 번에 자지 않고 분 단위로 깨어 시계 변경(절전/시간보정)에 견고
        slept = 0.0
        while slept < wait:
            chunk = min(300.0, wait - slept)
            time.sleep(chunk)
            slept += chunk
        # 실행
        try:
            with _LOCK:
                _STATE["running"] = True
            from . import monitor
            result = monitor.run_monitor()
            with _LOCK:
                _STATE["last_run"] = datetime.datetime.now().isoformat(timespec="minutes")
                _STATE["last_result"] = result
            logger.info(f"[scheduler] 야간 모니터링 완료: {result.get('new_events')} 이벤트")
        except Exception as e:
            logger.error(f"[scheduler] 야간 배치 실패: {e}")
        finally:
            with _LOCK:
                _STATE["running"] = False


def start_scheduler():
    """daemon 스레드 1회 기동 (멱등)."""
    with _LOCK:
        if _STATE["started"]:
            return
        _STATE["started"] = True
    t = threading.Thread(target=_loop, name="kdiris-monitor-scheduler", daemon=True)
    t.start()
    logger.info(f"[scheduler] 모니터링 야간 배치 스케줄러 시작 (매일 {DAILY_BATCH_HOUR:02d}:00)")


def get_status() -> dict:
    with _LOCK:
        return dict(_STATE)
