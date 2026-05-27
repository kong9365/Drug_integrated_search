"""
KD-IRIS — 위험도 신호등 헬퍼

검색 결과·제품 상세 헤더·워치리스트 카드에서 공통으로 사용하는
종합 위험도 계산 함수.

반환 형식 (KD-IRIS v3 §3.5):
  {
    "level":   "CRITICAL" | "HIGH" | "LOW" | "NONE",
    "color":   "danger"   | "warn" | "success" | "muted",
    "label":   "위험"      | "주의" | "정상"     | "정보없음",
    "reasons": ["회수이력 1건", "재심사 D-45일"]
  }
"""
from typing import Optional, Dict, List, Any


def calc_risk_signal(
    approval_data: Optional[List[Any]] = None,
    disciplinary_items: Optional[List[Any]] = None,
    recall_items: Optional[List[Any]] = None,
    review_due_days: Optional[int] = None,
) -> Dict[str, Any]:
    """
    종합 위험도 신호등 계산.

    우선순위:
      1. 회수 이력 1건 이상 → CRITICAL
      2. 행정처분 1건 이상 → HIGH (회수 없을 때)
      3. 재심사 D-30 이하 → HIGH (회수·처분 없을 때)
      4. 그 외 → LOW (이상 없음)
      5. 데이터 자체 없음 → NONE

    매개변수:
      approval_data:      허가 정보 항목 list (현재 위험도엔 직접 영향 없음, 신호 자체 의미)
      disciplinary_items: 행정처분 항목 list
      recall_items:       회수·판매중지 항목 list
      review_due_days:    재심사 만료까지 남은 일수 (없으면 None)
    """
    reasons: List[str] = []
    level = "NONE"

    if recall_items:
        level = "CRITICAL"
        reasons.append(f"회수이력 {len(recall_items)}건")

    if disciplinary_items:
        if level != "CRITICAL":
            level = "HIGH"
        reasons.append(f"행정처분 {len(disciplinary_items)}건")

    if review_due_days is not None and review_due_days <= 30:
        if level == "NONE":
            level = "HIGH"
        reasons.append(f"재심사 D-{review_due_days}일")

    if not reasons:
        level = "LOW"
        reasons = ["이상 없음"]

    color_map = {"CRITICAL": "danger", "HIGH": "warn", "LOW": "success", "NONE": "muted"}
    label_map = {"CRITICAL": "위험",   "HIGH": "주의", "LOW": "정상",   "NONE": "정보없음"}

    return {
        "level":   level,
        "color":   color_map[level],
        "label":   label_map[level],
        "reasons": reasons,
    }
