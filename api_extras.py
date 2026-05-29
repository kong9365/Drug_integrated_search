"""
RegHub 360 — 2026-05-27 신규 승인 17개 API 통합 fetch 함수
기존 api_client.py 의 _make_request / _parse_xml_response / _item_to_dict 재사용.
JSON / XML 자동 처리 (HIRA·DUR 일부 API는 JSON 응답).

설계 원칙:
- 단일 _fetch_generic() 헬퍼로 35개 API 모두 동일 패턴 처리
- 응답 변형 차이는 정규화 dict 반환으로 흡수
- 호출 한도 보호: caller가 num_of_rows 명시 (기본 10)
"""
import logging
from typing import Dict, List, Any, Optional

from .api_client import _make_request, _parse_xml_response, _item_to_dict
from .config import (
    API_ENDPOINTS, FOODSAFETY_BASE, FOODSAFETY_SERVICES, FOODSAFETY_KEY_ID,
    REQUEST_TIMEOUT, VERIFY_SSL,
)

logger = logging.getLogger(__name__)


def _fetch_generic(
    endpoint_key: str,
    label: str,
    extra_params: Optional[Dict[str, Any]] = None,
    page_no: int = 1,
    num_of_rows: int = 10,
    response_type: str = "xml",
) -> Dict[str, Any]:
    """범용 fetch 헬퍼 — 모든 신규 API 공통 패턴."""
    endpoint = API_ENDPOINTS.get(endpoint_key)
    if not endpoint:
        return {"success": False, "error": f"endpoint {endpoint_key} 미정의", "items": [], "totalCount": 0}

    params: Dict[str, Any] = {
        "pageNo": str(page_no),
        "numOfRows": str(num_of_rows),
        "type": response_type,
    }
    if extra_params:
        params.update({k: v for k, v in extra_params.items() if v is not None})

    logger.info(f"[{label}] 호출: {endpoint_key} params={params}")
    try:
        response = _make_request(endpoint, params)
        parsed = _parse_xml_response(response.text)
        items = [_item_to_dict(item) for item in parsed["items"]]
        return {
            "success": True,
            "totalCount": parsed["totalCount"],
            "items": items,
            "endpoint_key": endpoint_key,
        }
    except Exception as e:
        logger.error(f"[{label}] 실패: {e}")
        return {
            "success": False,
            "error": str(e),
            "totalCount": 0,
            "items": [],
            "endpoint_key": endpoint_key,
        }


# ────────────────────────────────────────────────────────────────────────────
# 의약품 — 기본정보 & 안전성
# ────────────────────────────────────────────────────────────────────────────

def fetch_drug_easy(item_name=None, entp_name=None, item_seq=None, page_no=1, num_of_rows=10):
    """NO 248 의약품개요정보(e약은요)."""
    return _fetch_generic("drug_easy", "e약은요",
                          {"itemName": item_name, "entpName": entp_name, "itemSeq": item_seq},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_bundle(item_name=None, ingredient=None, atc_code=None, page_no=1, num_of_rows=10):
    """NO 269 묶음의약품정보 (HIRA / ATC 매핑)."""
    return _fetch_generic("drug_bundle", "묶음의약품",
                          {"trustItemName": item_name, "trustMainingr": ingredient, "atcCode": atc_code},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_safety_letter(title=None, page_no=1, num_of_rows=10):
    """NO 547 의약품 안전성서한 — 검증된 파라미터: TITLE (대문자)."""
    return _fetch_generic("safety_letter", "안전성서한", {"TITLE": title},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_quasi_approval(item_name=None, entp_name=None, page_no=1, num_of_rows=10):
    """NO 145 의약외품 제품 허가정보 — snake_case 파라미터 (item_name, entp_name)."""
    return _fetch_generic(
        "quasi_approval", "의약외품 허가",
        {"item_name": item_name, "entp_name": entp_name},
        page_no=page_no, num_of_rows=num_of_rows,
    )


def fetch_drug_review(entp_name=None, item_name=None, item_no=None, page_no=1, num_of_rows=10):
    """NO 554 의약품 재심사 — 명세는 소문자 snake (entp_name, item_name, item_no)."""
    return _fetch_generic("drug_review", "재심사",
                          {"entp_name": entp_name, "item_name": item_name, "item_no": item_no},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_reeval(entp_name=None, item_name=None, page_no=1, num_of_rows=10):
    """NO 556 의약품 재평가."""
    return _fetch_generic("drug_reeval", "재평가",
                          {"ENTP_NAME": entp_name, "ITEM_NAME": item_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_orphan(item_name=None, target_disease=None, page_no=1, num_of_rows=10):
    """NO 565 희귀의약품 정보."""
    return _fetch_generic("drug_orphan", "희귀의약품",
                          {"productName": item_name, "targetDisease": target_disease},
                          page_no=page_no, num_of_rows=num_of_rows)


# ────────────────────────────────────────────────────────────────────────────
# 한약(생약) — 미신청 hook (NO 35 허가 / NO 90 회수)
# config.API_ENDPOINTS 에 herbal_approval / herbal_recall endpoint 추가 시 즉시 작동.
# 신청·승인 전까지는 endpoint 미정의 → graceful (success=False, 미신청 안내).
# ────────────────────────────────────────────────────────────────────────────

def fetch_herbal_approval(item_name=None, entp_name=None, page_no=1, num_of_rows=10):
    """NO 35 한약(생약)제제 허가 기원 — 미신청 hook.
    승인 시 config.API_ENDPOINTS['herbal_approval'] 채우면 자동 작동."""
    if "herbal_approval" not in API_ENDPOINTS:
        logger.info("[NO 35 한약허가] 미신청 — data.go.kr 활용신청 후 config endpoint 등록 필요")
        return {"success": False, "error": "NO 35 미신청 (hook)", "items": [], "totalCount": 0}
    return _fetch_generic("herbal_approval", "한약허가",
                          {"item_name": item_name, "entp_name": entp_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_herbal_recall(item_name=None, entp_name=None, page_no=1, num_of_rows=10):
    """NO 90 한약(생약)제제 회수·판매중지 — 미신청 hook.
    승인 시 config.API_ENDPOINTS['herbal_recall'] 채우면 모니터링 5번째 API로 자동 편입."""
    if "herbal_recall" not in API_ENDPOINTS:
        logger.info("[NO 90 한약회수] 미신청 — data.go.kr 활용신청 후 config endpoint 등록 필요")
        return {"success": False, "error": "NO 90 미신청 (hook)", "items": [], "totalCount": 0}
    return _fetch_generic("herbal_recall", "한약회수",
                          {"item_name": item_name, "entp_name": entp_name},
                          page_no=page_no, num_of_rows=num_of_rows)


# ────────────────────────────────────────────────────────────────────────────
# 의약품 — 품질·규제·공급망
# ────────────────────────────────────────────────────────────────────────────

def fetch_drug_gmp(entp_name=None, page_no=1, num_of_rows=10):
    """NO 132 의약품 GMP 적합판정서 — 검증된 파라미터: BSSH_NM."""
    return _fetch_generic("drug_gmp_jgmt", "GMP적합판정", {"BSSH_NM": entp_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_release(item_name=None, manuf_name=None, page_no=1, num_of_rows=10):
    """NO 142 의약품 국가출하승인 — 명세는 snake_case (goods_name, manuf_entp_name)."""
    return _fetch_generic("drug_natn_shipmnt", "국가출하승인",
                          {"goods_name": item_name, "manuf_entp_name": manuf_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_entity_list(entp_name=None, induty=None, page_no=1, num_of_rows=10):
    """NO 144 의약품 등 업체허가 (목록) — 명세는 Pascal Case (Entrps, Induty)."""
    return _fetch_generic("drug_entity_list", "업체허가목록",
                          {"Entrps": entp_name, "Induty": induty},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_entity_detail(permit_no=None, page_no=1, num_of_rows=10):
    """NO 144 의약품 등 업체허가 (상세). 키 명세 미확정 — Pascal/UPPER 양쪽 시도."""
    return _fetch_generic("drug_entity_detail", "업체허가상세", {"Prmisn_no": permit_no},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_dmf(ingredient=None, entp_name=None, page_no=1, num_of_rows=10):
    """NO 483 원료의약품등록 (DMF) — 명세는 소문자 snake (ingr_kor_name, entp_name)."""
    return _fetch_generic("drug_dmf", "DMF",
                          {"ingr_kor_name": ingredient, "entp_name": entp_name},
                          page_no=page_no, num_of_rows=num_of_rows)


# ────────────────────────────────────────────────────────────────────────────
# 의약품 — R&D / BD (8개)
# ────────────────────────────────────────────────────────────────────────────

def fetch_drug_patent(item_name=None, applicant=None, page_no=1, num_of_rows=10):
    """NO 561 의약품 특허정보."""
    return _fetch_generic("drug_patent", "특허",
                          {"ITEM_NAME": item_name, "applicant": applicant},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_lawsuit(item_name=None, ingr_name=None, page_no=1, num_of_rows=10):
    """NO 557 국내소송 의약품(특허)."""
    return _fetch_generic("drug_lawsuit", "국내소송특허",
                          {"PRT_NAME": item_name, "INGR_NAME": ingr_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_fda_p4(drug_name=None, page_no=1, num_of_rows=10):
    """NO 552 FDA Paragraph IV."""
    return _fetch_generic("drug_fda_p4", "FDA P4", {"DRUG_NAME": drug_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_fda_orangebook(ingredient=None, item_name=None, page_no=1, num_of_rows=10):
    """NO 562 FDA 오렌지북 — 명세는 소문자 snake (ingr_name, prt_name)."""
    return _fetch_generic("drug_fda_orangebook", "FDA오렌지북",
                          {"ingr_name": ingredient, "prt_name": item_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_clinical(item_name=None, sponsor=None, page_no=1, num_of_rows=10):
    """NO 566 의약품 임상시험."""
    return _fetch_generic("drug_clinical", "임상시험",
                          {"GOODS_NAME": item_name, "APPLY_ENTP_NAME": sponsor},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_clinical_org(lab_name=None, page_no=1, num_of_rows=10):
    """NO 568 의약품 임상시험 실시기관 — 명세는 소문자 snake (lab_name)."""
    return _fetch_generic("drug_clinical_org", "임상기관", {"lab_name": lab_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_reference(ingredient=None, item_name=None, page_no=1, num_of_rows=10):
    """NO 484 대조약."""
    return _fetch_generic("drug_reference", "대조약",
                          {"INGR_NAME": ingredient, "ITEM_NAME": item_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_bioeq(item_name=None, page_no=1, num_of_rows=10):
    """NO 485 생동성인정품목 — 명세는 소문자 snake, 단일 파라미터 item_name."""
    return _fetch_generic("drug_bioeq", "생동성",
                          {"item_name": item_name},
                          page_no=page_no, num_of_rows=num_of_rows)


# ────────────────────────────────────────────────────────────────────────────
# 의약품 — DUR 9 + 7 (재호출 인터페이스)
# ────────────────────────────────────────────────────────────────────────────

def fetch_dur_item(category: str = "list", item_name=None, page_no=1, num_of_rows=10):
    """
    NO 531 DUR 품목정보 — 9개 카테고리 중 1개 호출.
    명세는 camelCase (itemName) — 서버는 양쪽 모두 수용하지만 명세 준수.
    category ∈ {combine, elderly, list, age, capacity, period, efficacy, seobang, pregnancy}
    """
    key_map = {
        "combine": "dur_item_combine",
        "elderly": "dur_item_elderly",
        "list": "dur_item_list",
        "age": "dur_item_age",
        "capacity": "dur_item_capacity",
        "period": "dur_item_period",
        "efficacy": "dur_item_efficacy",
        "seobang": "dur_item_seobang",
        "pregnancy": "dur_item_pregnancy",
    }
    key = key_map.get(category, "dur_item_list")
    return _fetch_generic(key, f"DUR 품목/{category}", {"itemName": item_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_dur_ingredient(category: str = "combine", ingr_name=None, page_no=1, num_of_rows=10):
    """
    NO 533 DUR 성분정보 — 7개 카테고리 중 1개 호출.
    category ∈ {combine, age, pregnancy, capacity, period, elderly, efficacy}
    """
    key_map = {
        "combine": "dur_ingr_combine",
        "age": "dur_ingr_age",
        "pregnancy": "dur_ingr_pregnancy",
        "capacity": "dur_ingr_capacity",
        "period": "dur_ingr_period",
        "elderly": "dur_ingr_elderly",
        "efficacy": "dur_ingr_efficacy",
    }
    key = key_map.get(category, "dur_ingr_combine")
    return _fetch_generic(key, f"DUR 성분/{category}", {"INGR_NAME": ingr_name},
                          page_no=page_no, num_of_rows=num_of_rows)


# ────────────────────────────────────────────────────────────────────────────
# 의약품 — 공급망 (재호출 인터페이스)
# ────────────────────────────────────────────────────────────────────────────

def fetch_drug_supply_stop(entp_name=None, item_name=None, page_no=1, num_of_rows=10):
    """NO 534 의약품 생산수입공급중단."""
    return _fetch_generic("supply_stop", "공급중단",
                          {"ENTP_NAME": entp_name, "ITEM_NAME": item_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_drug_supply_lack(entp_name=None, item_name=None, page_no=1, num_of_rows=10):
    """NO 537 의약품 공급부족."""
    return _fetch_generic("supply_lack", "공급부족",
                          {"ENTP_NAME": entp_name, "ITEM_NAME": item_name},
                          page_no=page_no, num_of_rows=num_of_rows)


# ────────────────────────────────────────────────────────────────────────────
# 식품 (5 작동 API)
# ────────────────────────────────────────────────────────────────────────────

def fetch_food_nutrition(food_name=None, manufacturer=None, page_no=1, num_of_rows=10):
    """NO 1 식품 영양성분 DB."""
    return _fetch_generic("food_nutrition", "식품영양",
                          {"FOOD_NM_KR": food_name, "BSSH_NM": manufacturer},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_food_disc(category: str = "mnft", entp_name=None, page_no=1, num_of_rows=10):
    """
    식품 행정처분 — 3종 (Phase 1 작동분).
    category ∈ {import, sale, mnft}
    """
    key_map = {
        "import": "food_disc_import",
        "sale": "food_disc_sale",
        "mnft": "food_disc_mnft",
    }
    key = key_map.get(category, "food_disc_mnft")
    return _fetch_generic(key, f"식품행정처분/{category}",
                          {"PRCSCITYPOINT_BSSHNM": entp_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_food_recall_import(product_name=None, entp_name=None, barcode=None,
                             page_no=1, num_of_rows=10):
    """NO 153 수입식품 회수판매중지 — UPPER_CASE 파라미터 3종 지원."""
    return _fetch_generic("food_recall_import", "수입식품회수",
                          {"PRDT_NM": product_name, "CLNT_BSSH_NM": entp_name,
                           "BRCD_NO": barcode},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_food_inspect(item_name=None, page_no=1, num_of_rows=10):
    """NO 535 식품 검사부적합 (목록)."""
    return _fetch_generic("food_inspect_list", "식품검사부적합",
                          {"PRDUCT": item_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_food_inspect_detail(prsec_no=None, page_no=1, num_of_rows=1):
    """NO 535 식품 검사부적합 (상세) — getPrsecImproptFoodItem02."""
    return _fetch_generic("food_inspect_item", "식품검사부적합상세",
                          {"PRSEC_NO": prsec_no},
                          page_no=page_no, num_of_rows=num_of_rows)


# ────────────────────────────────────────────────────────────────────────────
# 희귀필수의약품 (NO 81 — 5 오퍼레이션)
# ────────────────────────────────────────────────────────────────────────────

def fetch_rare_essential(category: str = "treat", page_no=1, num_of_rows=10):
    """
    NO 81 희귀필수의약품 — 5개 카테고리 중 1개 호출.
    category ∈ {self, treat, unreg, reg, narc}
      - self : 자가치료용 마약류 (getRareNartDrugSelftreat)
      - treat: 치료용 (getRareSelfmdcin)
      - unreg: 긴급도입 보험미등재 (getRareEmerIntdInsurceUnregistMdcin)
      - reg  : 긴급도입 보험등재 (getRareEmerIntdInsurceRegistMdcin)
      - narc : 긴급도입 마약류 (getRareEmerIntdNarticDrug)
    """
    key_map = {
        "self":  "drug_rare_self",
        "treat": "drug_rare_treat",
        "unreg": "drug_rare_unreg",
        "reg":   "drug_rare_reg",
        "narc":  "drug_rare_narc",
    }
    key = key_map.get(category, "drug_rare_treat")
    return _fetch_generic(key, f"희귀필수의약품/{category}", None,
                          page_no=page_no, num_of_rows=num_of_rows)


# ────────────────────────────────────────────────────────────────────────────
# 건강기능식품 + HACCP
# ────────────────────────────────────────────────────────────────────────────

def fetch_hf_gmp(entp_name=None, page_no=1, num_of_rows=10):
    """NO 51 건강기능식품 GMP 지정현황."""
    return _fetch_generic("hf_gmp", "건기식 GMP", {"BSSH_NM": entp_name},
                          page_no=page_no, num_of_rows=num_of_rows)


def fetch_haccp_smart(business_name=None, page_no=1, num_of_rows=10):
    """NO 12 식품 스마트HACCP 인증업체."""
    return _fetch_generic("haccp_smart", "스마트HACCP", {"businessnm": business_name},
                          page_no=page_no, num_of_rows=num_of_rows)


# ────────────────────────────────────────────────────────────────────────────
# 식품안전나라 (foodsafetykorea.go.kr) — 별도 KeyID (FOODSAFETY_KEY_ID)
# URL: http://openapi.foodsafetykorea.go.kr/api/{KEY_ID}/{serviceId}/{type}/{start}/{end}[/{var}={val}&...]
# 응답(JSON): { "{serviceId}": { "total_count": "..", "row": [..], "RESULT": {"CODE":"INFO-000","MSG":".."} } }
# ────────────────────────────────────────────────────────────────────────────

def fetch_foodsafety(
    service_key: str,
    extra_params: Optional[Dict[str, Any]] = None,
    start_idx: int = 1,
    end_idx: int = 10,
    data_type: str = "json",
) -> Dict[str, Any]:
    """
    식품안전나라 OPEN-API 범용 호출.

    Args:
        service_key: FOODSAFETY_SERVICES 의 코드 키 (예: 'food_recall_domestic')
                     또는 serviceId 직접 (예: 'I0490')
        extra_params: 추가 검색 파라미터 (예: {'PRDLST_NM': '홍삼'})
                      — URL 경로에 /{변수}={값}&{변수}={값} 형태로 부착
        start_idx / end_idx: 요청 시작/종료 위치 (1-base, 양끝 포함)
        data_type: 'json' 또는 'xml'

    Returns:
        {success, totalCount, items, service_id}
    """
    # 코드 키 → serviceId 변환 (직접 serviceId 전달도 허용)
    service_id = FOODSAFETY_SERVICES.get(service_key, service_key)

    if not FOODSAFETY_KEY_ID:
        logger.warning(
            f"[식품안전나라/{service_id}] FOODSAFETY_KEY_ID 미설정 — "
            "식품안전나라(foodsafetykorea.go.kr) 회원가입 후 OpenAPI 신청 필요. "
            ".env에 FOODSAFETY_KEY_ID=... 추가."
        )
        return {"success": False, "error": "FOODSAFETY_KEY_ID 미설정",
                "items": [], "totalCount": 0, "service_id": service_id}

    # URL 조립: /api/{KEY}/{serviceId}/{type}/{start}/{end}
    url = f"{FOODSAFETY_BASE}/{FOODSAFETY_KEY_ID}/{service_id}/{data_type}/{start_idx}/{end_idx}"
    # 추가 파라미터: /{변수}={값}&{변수}={값2}  (공식 명세 패턴)
    if extra_params:
        kv = "&".join(f"{k}={v}" for k, v in extra_params.items() if v is not None and v != "")
        if kv:
            url += "/" + kv

    logger.info(f"[식품안전나라/{service_id}] 호출: start={start_idx}, end={end_idx}, params={extra_params}")
    try:
        import requests
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, verify=VERIFY_SSL)
        resp.raise_for_status()

        if data_type == "json":
            data = resp.json()
            # 응답 구조: { serviceId: { total_count, row[], RESULT{CODE,MSG} } }
            block = data.get(service_id, {})
            result = block.get("RESULT", {}) or {}
            code = result.get("CODE", "")
            rows = block.get("row", []) or []
            total = int(block.get("total_count", len(rows)) or 0)
            # INFO-000 = 정상, INFO-200 = 데이터 없음(정상), 그 외 ERROR
            if code and not code.startswith("INFO"):
                return {"success": False, "error": f"{code}: {result.get('MSG','')}",
                        "items": [], "totalCount": 0, "service_id": service_id}
            return {"success": True, "totalCount": total, "items": rows,
                    "service_id": service_id}
        else:
            # XML 응답 — data.go.kr 파서 재사용 (구조 다를 수 있음)
            parsed = _parse_xml_response(resp.text)
            items = [_item_to_dict(it) for it in parsed.get("items", [])]
            return {"success": True, "totalCount": parsed.get("totalCount", len(items)),
                    "items": items, "service_id": service_id}
    except Exception as e:
        logger.error(f"[식품안전나라/{service_id}] 실패: {e}")
        return {"success": False, "error": str(e), "items": [], "totalCount": 0,
                "service_id": service_id}


def fetch_food_recall_domestic(product_name=None, report_no=None, cret_dtm=None,
                               start_idx=1, end_idx=10):
    """NO 339 식품 회수·판매중지 정보 (I0490)."""
    return fetch_foodsafety("food_recall_domestic",
                            {"PRDLST_REPORT_NO": report_no, "CRET_DTM": cret_dtm},
                            start_idx=start_idx, end_idx=end_idx)


def fetch_food_recall_overseas(st_cret_dtm=None, end_cret_dtm=None,
                               start_idx=1, end_idx=10):
    """NO 225 해외 위해식품 회수정보 (I2810). 날짜 범위 검색만 지원."""
    return fetch_foodsafety("food_recall_overseas",
                            {"ST_CRET_DTM": st_cret_dtm, "END_CRET_DTM": end_cret_dtm},
                            start_idx=start_idx, end_idx=end_idx)


def fetch_food_disc_service(chng_dt=None, dsps_dcsndt=None, lcns_no=None,
                            start_idx=1, end_idx=10):
    """NO 477 행정처분결과(식품접객업) (I2630)."""
    return fetch_foodsafety("food_disc_service",
                            {"CHNG_DT": chng_dt, "DSPS_DCSNDT": dsps_dcsndt, "LCNS_NO": lcns_no},
                            start_idx=start_idx, end_idx=end_idx)


def fetch_food_report(product_name=None, entp_name=None, report_no=None,
                      lcns_no=None, chng_dt=None, start_idx=1, end_idx=10):
    """NO 444 식품(첨가물) 품목제조보고 (I1250)."""
    return fetch_foodsafety("food_report",
                            {"PRDLST_NM": product_name, "BSSH_NM": entp_name,
                             "PRDLST_REPORT_NO": report_no, "LCNS_NO": lcns_no,
                             "CHNG_DT": chng_dt},
                            start_idx=start_idx, end_idx=end_idx)


def fetch_food_report_raw(product_name=None, entp_name=None, rawmtrl_name=None,
                          report_no=None, lcns_no=None, start_idx=1, end_idx=10):
    """NO 470 식품(첨가물) 품목제조보고(원재료) (C002). 원재료명(RAWMTRL_NM) 검색 지원."""
    return fetch_foodsafety("food_report_raw",
                            {"PRDLST_NM": product_name, "BSSH_NM": entp_name,
                             "RAWMTRL_NM": rawmtrl_name, "PRDLST_REPORT_NO": report_no,
                             "LCNS_NO": lcns_no},
                            start_idx=start_idx, end_idx=end_idx)


# ────────────────────────────────────────────────────────────────────────────
# 건강기능식품 · 식품공전 (식품안전나라, FOODSAFETY_KEY_ID 사용)
# ────────────────────────────────────────────────────────────────────────────

def fetch_hf_individual(material_name=None, start_idx=1, end_idx=10):
    """
    건강기능식품 개별인정형 정보 (I-0050).
    응답: HF_FNCLTY_MTRAL_RCOGN_NO(원료인정번호), RAWMTRL_NM(원재료명),
          PRIMARY_FNCLTY(주된 기능성), DAY_INTK_HIGHLIMIT/LOWLIMIT(1일 섭취량 상/하한),
          IFTKN_ATNT_MATR_CN(섭취시 주의사항), WT_UNIT(중량단위)
    ※ 서버 검색 파라미터 미보장 → 결과에서 material_name 클라이언트 필터.
    """
    resp = fetch_foodsafety("hf_individual", None, start_idx=start_idx, end_idx=end_idx)
    if material_name and resp.get("items"):
        n = material_name.strip().lower()
        resp["items"] = [it for it in resp["items"]
                         if n in str(it.get("RAWMTRL_NM", "")).lower()]
    return resp


def fetch_hf_nutrition(name=None, start_idx=1, end_idx=10):
    """건강기능식품 영양DB 분류체계 (I0760). 추가 파라미터: HELT_ITM_GRP_NM(명칭)."""
    return fetch_foodsafety("hf_nutrition",
                            {"HELT_ITM_GRP_NM": name},
                            start_idx=start_idx, end_idx=end_idx)


def fetch_hf_report(start_idx=1, end_idx=10):
    """건강기능식품 품목제조 신고사항 현황 (I0030)."""
    return fetch_foodsafety("hf_report", None, start_idx=start_idx, end_idx=end_idx)


def fetch_food_code(product_name=None, last_updt=None, start_idx=1, end_idx=10):
    """
    식품공전 기준규격 (I0930). 추가 파라미터: PRDLST_NM(품목명), LAST_UPDT_DTM(YYYYMMDD).
    응답: PRDLST_NM(품목명), T_KOR_NM(시험항목), SPEC_VAL(기준규격값),
          SPEC_VAL_SUMUP(규격값요약), VALD_BEGN_DT/VALD_END_DT(유효기간)
    """
    return fetch_foodsafety("food_code",
                            {"PRDLST_NM": product_name, "LAST_UPDT_DTM": last_updt},
                            start_idx=start_idx, end_idx=end_idx)


# ────────────────────────────────────────────────────────────────────────────
# 카운트 전용 헬퍼 (랜딩 데모용 — 빠른 응답)
# ────────────────────────────────────────────────────────────────────────────

def get_count_only(fetch_fn, **kwargs) -> int:
    """fetch 함수의 totalCount만 빠르게 추출. num_of_rows=1 로 최소 호출."""
    try:
        kwargs.setdefault("num_of_rows", 1)
        result = fetch_fn(**kwargs)
        return int(result.get("totalCount", 0)) if result.get("success") else 0
    except Exception as e:
        logger.warning(f"count 추출 실패 ({fetch_fn.__name__}): {e}")
        return 0
