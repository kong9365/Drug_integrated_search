"""
RegHub 360 — /api/landing-demo, /api/copilot/message 등 신규 API.
랜딩 Live Demo의 실 데이터 공급 + AI 코파일럿 백엔드.
"""
import logging
import time
import threading
from typing import Dict, Any
from flask import Blueprint, request, jsonify

from ..api_client import fetch_approval, fetch_disciplinary, fetch_recall
from ..api_extras import (
    get_count_only,
    fetch_drug_easy, fetch_drug_bundle, fetch_drug_safety_letter,
    fetch_drug_supply_stop, fetch_drug_supply_lack,
    fetch_food_nutrition, fetch_food_disc, fetch_food_recall_import, fetch_food_inspect,
    fetch_drug_orphan, fetch_drug_patent, fetch_drug_clinical,
    fetch_drug_gmp, fetch_drug_release, fetch_drug_entity_list,
    fetch_drug_dmf, fetch_drug_review, fetch_drug_reeval,
    fetch_drug_reference, fetch_drug_bioeq,
    fetch_drug_lawsuit, fetch_drug_fda_p4, fetch_drug_fda_orangebook,
    fetch_drug_clinical_org, fetch_hf_gmp,
)

logger = logging.getLogger(__name__)

api_demo_bp = Blueprint("api_demo", __name__, url_prefix="/api")

# ────────────────────────────────────────────────────────────────────────────
# 메모리 캐시 (Redis 대안 — 단일 프로세스 환경용)
# ────────────────────────────────────────────────────────────────────────────
_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_LOCK = threading.Lock()
DEMO_CACHE_TTL = 1800  # 30분


def _cache_get(key: str):
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if entry and entry["expires_at"] > time.time():
            return entry["value"]
        return None


def _cache_set(key: str, value: Any, ttl: int = DEMO_CACHE_TTL):
    with _CACHE_LOCK:
        _CACHE[key] = {"value": value, "expires_at": time.time() + ttl}


# ────────────────────────────────────────────────────────────────────────────
# /api/landing-demo — 6 KPI 카운트 집계
# ────────────────────────────────────────────────────────────────────────────

def _classify_query(q: str) -> str:
    """검색어를 4가지 종류로 분류 — 업체/제품/성분/기타."""
    q = q.strip()
    if not q:
        return "기타"
    # 휴리스틱: 끝에 '제약/약품/주식회사' 포함 → 업체
    if any(suffix in q for suffix in ("제약", "약품", "(주)", "주식회사", "Pharma", "Co", "광동", "동아", "한미", "유한")):
        return "업체"
    # 영문 또는 성분명 특징 (한글 끝에 정/캡슐/시럽 없으면 성분으로)
    if any(t in q for t in ("산", "노펜", "프로펜", "아민", "신", "ein", "amol", "fen", "조정", "잔틴", "카페")):
        return "성분"
    # 끝에 정/캡슐/시럽/액/주 → 의약품
    if any(suffix in q for suffix in ("정", "캡슐", "시럽", "주", "액", "연질", "환", "산제")):
        return "의약품"
    # 숫자 포함 + 음료 패턴 → 식품
    if any(t in q for t in ("100", "200", "500", "차", "음료", "주스", "탄산")):
        return "식품"
    return "제품"


@api_demo_bp.route("/landing-demo", methods=["GET"])
def landing_demo():
    """
    랜딩 Live Demo — 사용자가 입력한 검색어로 6 KPI 카운트 반환.
    제품·업체·성분 어떤 종류든 실 API 집계.
    """
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"success": False, "error": "검색어를 입력하세요."}), 400

    # 캐시
    cached = _cache_get(f"demo:{q}")
    if cached:
        cached["cached"] = True
        return jsonify(cached)

    # 동시 호출 패턴 — 실 API 6종 카운트만 빠르게 (numOfRows=1)
    # 검색어 종류 자동 판별
    kind = _classify_query(q)

    # ────────────────────────────────────────────────────────────────────
    # 6 KPI 집계
    # ────────────────────────────────────────────────────────────────────
    counts: Dict[str, int] = {}
    try:
        # 1. 허가 정보 — NO 140 의약품 허가정보 (e약은요는 일반의약품 위주라 누락 많음)
        if kind == "업체":
            counts["drug"] = get_count_only(fetch_approval, entp_name=q)
        else:
            counts["drug"] = get_count_only(fetch_approval, item_name=q)
    except Exception as e:
        logger.warning(f"drug count 실패: {e}")
        counts["drug"] = 0

    # 회수·행정처분은 검색 파라미터 미지원 → 응답 본문 클라이언트 필터링
    needle = q.lower()
    try:
        r = fetch_recall(num_of_rows=200)
        items = r.get("items", []) if r.get("success") else []
        counts["recall"] = sum(
            1 for it in items
            if any(needle in str(it.get(f, "")).lower()
                   for f in ("PRDUCT", "ENTRPS", "ITEM_NAME", "ENTP_NAME"))
        )
    except Exception as e:
        logger.warning(f"recall count 실패: {e}")
        counts["recall"] = 0

    try:
        r = fetch_disciplinary(num_of_rows=200)
        items = r.get("items", []) if r.get("success") else []
        counts["sanction"] = sum(
            1 for it in items
            if any(needle in str(it.get(f, "")).lower()
                   for f in ("ENTP_NAME", "ITEM_NAME", "ENTRPS_NAME", "VIOLATION_DETAIL"))
        )
    except Exception as e:
        logger.warning(f"sanction count 실패: {e}")
        counts["sanction"] = 0

    try:
        # 4. 안전성서한 — 제목 + 요약 + 상세 필드에서 키워드 필터링
        r = fetch_drug_safety_letter(num_of_rows=200)
        items = r.get("items", []) if r.get("success") else []
        counts["safety"] = sum(
            1 for it in items
            if any(needle in str(it.get(f, "")).lower()
                   for f in ("TITLE", "SUMMARY", "DETAIL_CN", "TBL_CN"))
        )
    except Exception as e:
        logger.warning(f"safety count 실패: {e}")
        counts["safety"] = 0

    try:
        # 5. 공급중단·공급부족 합산 (클라이언트 필터링)
        stop = fetch_drug_supply_stop(num_of_rows=200)
        lack = fetch_drug_supply_lack(num_of_rows=200)
        all_items = (stop.get("items", []) if stop.get("success") else []) + \
                    (lack.get("items", []) if lack.get("success") else [])
        counts["supply"] = sum(
            1 for it in all_items
            if any(needle in str(it.get(f, "")).lower()
                   for f in ("ENTP_NAME", "ITEM_NAME", "PRDUCT", "ENTRPS_NAME"))
        )
    except Exception as e:
        logger.warning(f"supply count 실패: {e}")
        counts["supply"] = 0

    try:
        # 6. 식품·의약외품 — 영양DB + 식품제조가공업 처분 (클라이언트 필터링)
        r = fetch_food_nutrition(num_of_rows=200)
        items = r.get("items", []) if r.get("success") else []
        nutri = sum(
            1 for it in items
            if any(needle in str(it.get(f, "")).lower()
                   for f in ("FOOD_NM_KR", "BSSH_NM", "MANUFACTURE", "INDUTY_CD_NM"))
        )

        r2 = fetch_food_disc(category="mnft", num_of_rows=200)
        items2 = r2.get("items", []) if r2.get("success") else []
        disc = sum(
            1 for it in items2
            if any(needle in str(it.get(f, "")).lower()
                   for f in ("PRCSCITYPOINT_BSSHNM", "ENTP_NAME", "ITEM_NAME"))
        )
        counts["food"] = nutri + disc
    except Exception as e:
        logger.warning(f"food count 실패: {e}")
        counts["food"] = 0

    result = {
        "success": True,
        "query": q,
        "kind": kind,
        "counts": counts,
        "summary": f"6개 API 동시 집계 완료 · {kind} 기준",
        "cached": False,
    }
    _cache_set(f"demo:{q}", result)
    return jsonify(result)


# ────────────────────────────────────────────────────────────────────────────
# /api/copilot/message — AI 코파일럿 (MISO 미연결 시 mock)
# ────────────────────────────────────────────────────────────────────────────

@api_demo_bp.route("/copilot/message", methods=["POST"])
def copilot_message():
    """
    AI 코파일럿 — handoff.md §7 명세 준수.
    환각 차단: citations 0건이면 강제 안내 메시지.
    MISO 미연결 환경에서는 mock 응답 + 실 API 카운트 조합.
    """
    body = request.get_json(silent=True) or {}
    message = (body.get("message") or "").strip()
    thread_id = body.get("threadId") or "default"

    if not message:
        return jsonify({"success": False, "error": "질문을 입력하세요."}), 400

    # 실 API에서 근거 자료 카운트 → citations 생성
    citations = []
    suggestions = []

    # 휴리스틱: 메시지에서 키워드 추출
    is_recall = any(k in message for k in ("회수", "판매중지", "리콜"))
    is_sanction = any(k in message for k in ("행정처분", "처분", "위반"))
    is_safety = any(k in message for k in ("안전성서한", "안전성", "주의"))

    # 첫 명사 추출 (간단 휴리스틱)
    company_match = next((w for w in message.split() if any(s in w for s in ("제약", "약품"))), None)
    product_match = next((w for w in message.split() if any(s in w for s in ("정", "캡슐", "시럽"))), None)

    try:
        if is_recall:
            r = fetch_recall(item_name=product_match, entp_name=company_match, num_of_rows=2)
            for i, item in enumerate(r.get("items", [])[:2]):
                citations.append({
                    "marker": len(citations) + 1,
                    "apiNumber": "API 539",
                    "title": item.get("PRDUCT", "(제품명 미상)") + " — " + (item.get("RTRVL_RESN") or "회수"),
                    "url": "https://www.data.go.kr/data/15059114/openapi.do",
                    "syncedAt": "동기화 직후",
                })
    except Exception:
        pass

    try:
        if is_sanction:
            r = fetch_disciplinary(item_name=product_match, entp_name=company_match, num_of_rows=2)
            for item in r.get("items", [])[:2]:
                citations.append({
                    "marker": len(citations) + 1,
                    "apiNumber": "API 564",
                    "title": item.get("ENTP_NAME", "(업체)") + " — " + (item.get("VIOLATION_DETAIL") or "행정처분"),
                    "url": "https://www.data.go.kr/data/15058457/openapi.do",
                    "syncedAt": "동기화 직후",
                })
    except Exception:
        pass

    try:
        if is_safety:
            r = fetch_drug_safety_letter(title=product_match or message[:20], num_of_rows=2)
            for item in r.get("items", [])[:2]:
                citations.append({
                    "marker": len(citations) + 1,
                    "apiNumber": "API 547",
                    "title": item.get("TITLE", "(제목 미상)"),
                    "url": "https://www.data.go.kr/data/15059182/openapi.do",
                    "syncedAt": "동기화 직후",
                })
    except Exception:
        pass

    # 환각 차단 가드 (handoff.md §7 명세)
    if not citations:
        text = "확인 가능한 공식 데이터가 없습니다. 검색어를 더 구체적으로 입력해 주세요. (예: 업체명+제품명, 회수/행정처분 등 키워드 포함)"
        suggestions = [
            "광동제약 최근 1년 행정처분 알려줘",
            "아세트아미노펜 안전성서한 정리해줘",
            "베니톨정 회수 이력 보여줘",
        ]
    else:
        # 인용 마커가 포함된 텍스트 조립
        markers = "".join(f"[{c['marker']}]" for c in citations[:3])
        text = (
            f"질문 '{message}' 관련 공식 API에서 {len(citations)}건 근거를 확인했습니다{markers}.\n\n"
            "각 근거 카드를 클릭하면 원본 식약처 데이터로 이동합니다. "
            "MISO drug_consult_agent 연동 후에는 더 상세한 자연어 분석이 제공됩니다."
        )
        suggestions = [
            f"{citations[0].get('title','')[:20]}... 의 상세 영향 분석",
            "자사 동성분 품목 비교",
            "월간 트렌드 리포트 생성",
        ]

    return jsonify({
        "success": True,
        "threadId": thread_id,
        "text": text,
        "citations": citations,
        "suggestions": suggestions,
        "model": "RegHub Copilot (mock · MISO 미연결)",
    })
