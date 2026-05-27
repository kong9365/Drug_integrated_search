"""
KD-IRIS — 이벤트 심각도(Severity) 단일 분류

모든 이벤트(회수·처분·안전성·공급·임상·특허·재심사·재평가 등)를
🔴 CRITICAL / 🟡 HIGH / 🟢 LOW 3단계로 통일 분류.

`_normalize_event()` 와 `event_card` 매크로가 이 매핑을 단일 소스로 사용한다.
"""

SEVERITY_MAP = {
    # 🔴 CRITICAL — 즉각 대응 필요
    "recall":          {"level": "CRITICAL", "label": "회수명령",   "color": "danger"},
    "supply_stop":     {"level": "CRITICAL", "label": "판매중지",   "color": "danger"},

    # 🟡 HIGH — 모니터링 필요
    "disciplinary":    {"level": "HIGH",     "label": "행정처분",   "color": "warn"},
    "supply_lack":     {"level": "HIGH",     "label": "공급부족",   "color": "warn"},
    "safety_letter":   {"level": "HIGH",     "label": "안전성서한", "color": "warn"},
    "inspection_fail": {"level": "HIGH",     "label": "검사부적합", "color": "warn"},

    # 🟢 LOW — 인지 및 기회 탐색
    "permit_new":      {"level": "LOW",      "label": "신규허가",   "color": "success"},
    "clinical_new":    {"level": "LOW",      "label": "임상신규",   "color": "info"},
    "patent_new":      {"level": "LOW",      "label": "특허등재",   "color": "info"},
    "review_due":      {"level": "LOW",      "label": "재심사예정", "color": "info"},
    "reeval_done":     {"level": "LOW",      "label": "재평가완료", "color": "info"},
}

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "LOW": 2, "NONE": 3}


def get_severity(event_type: str) -> dict:
    """이벤트 타입 키 → {level, label, color} 매핑. 미지정 키는 NONE/muted."""
    return SEVERITY_MAP.get(event_type, {
        "level": "NONE", "label": event_type or "기타", "color": "muted"
    })
