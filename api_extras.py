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
from .config import API_ENDPOINTS

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
