"""
RegHub 360 — 35개 API 전수 개별 검증
각 API에 적절한 임의 검색어 입력 → 응답 필드 + 의미성 확인.

검증 항목:
1. HTTP 상태 / totalCount
2. items[0]의 핵심 필드 추출
3. 응답에서 실무자에게 유용한 정보 확인
"""
import sys
import io
import ssl
import urllib.request
import urllib.parse
import re
from typing import Dict, List

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, "..")
from drug_integrated_search.config import SERVICE_KEY, API_ENDPOINTS

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# (라벨, NO, 엔드포인트 키, 추가 파라미터, 핵심 필드 추출 후 사용 가능성 평가)
CASES = [
    # ────────────── 의약품 핵심 (NO 140 3개 오퍼레이션) ──────────────
    ("의약품 허가 (목록)", 140, "approval",
     {"item_name": "타이레놀"},
     ["ITEM_NAME", "ENTP_NAME", "ITEM_PERMIT_DATE", "SPCLTY_PBLC", "ITEM_INGR_NAME", "EDI_CODE"]),
    ("의약품 허가 (상세)", 140, "approval_detail",
     {"item_name": "타이레놀"},
     ["ITEM_NAME", "ENTP_NAME", "STORAGE_METHOD", "VALID_TERM", "EE_DOC_DATA"]),
    ("의약품 허가 (주성분)", 140, "approval_ingr",
     {"item_name": "타이레놀"},
     ["ENTRPS", "PRDUCT", "MTRAL_NM", "MTRAL_CODE", "QNT", "INGD_UNIT_CD"]),

    # ────────────── e약은요 / DUR / 묶음의약품 ──────────────
    ("e약은요", 248, "drug_easy",
     {"itemName": "타이레놀"},
     ["itemName", "entpName", "efcyQesitm", "useMethodQesitm", "atpnQesitm", "depositMethodQesitm"]),
    ("묶음의약품 (HIRA/ATC)", 269, "drug_bundle",
     {"trustItemName": "베니톨정"},
     ["trustItemName", "trustMainingr", "trustItemSeq", "consignItemName"]),
    ("DUR 품목 - 병용금기", 531, "dur_item_combine",
     {"itemName": "타이레놀"},
     ["ITEM_NAME", "TYPE_NAME", "MIX_INGR", "MIX_TYPE", "PROHBT_CONTENT"]),
    ("DUR 품목 - 임부금기", 531, "dur_item_pregnancy",
     {"itemName": "이부프로펜"},
     ["ITEM_NAME", "TYPE_NAME", "PROHBT_CONTENT", "GRADE"]),
    ("DUR 성분 - 병용금기", 533, "dur_ingr_combine",
     {},
     ["INGR_NAME", "TYPE_NAME", "MIX_TYPE", "PROHBT_CONTENT"]),

    # ────────────── 안전성 / 회수 / 행정처분 / 낱알 ──────────────
    ("안전성서한", 547, "safety_letter",
     {"TITLE": "주의"},
     ["TITLE", "PBANC_DATE", "PBANC_DIVS_NM", "SUMMARY", "ACTN_MATR"]),
    ("의약품 회수목록", 539, "recall",
     {},
     ["PRDUCT", "ENTRPS", "RTRVL_RESN", "ENFRC_YN", "RECALL_COMMAND_DATE", "STD_CD", "BIZRNO"]),
    ("의약품 회수상세", 539, "recall_detail",
     {},
     ["PRDUCT", "ENTRPS", "ENTRPS_ADRES", "RTRVL_RESN", "USGPD", "PACKNG_UNIT"]),
    ("의약품외 회수", 539, "recall_etc",
     {},
     ["PRDUCT", "ENTRPS", "ENFRC_YN", "RTRVL_CMMND_DT", "BIZRNO"]),
    ("의약품 행정처분", 564, "disciplinary",
     {"entp_name": "광동제약"},
     ["ENTP_NAME", "ADDR", "EXPOSE_CONT", "ADM_DISPS_NAME", "LAST_SETTLE_DATE", "BEF_APPLY_LAW"]),
    ("낱알식별", 563, "identification",
     {"item_name": "타이레놀"},
     ["ITEM_NAME", "ENTP_NAME", "DRUG_SHAPE", "COLOR_CLASS1", "PRINT_FRONT", "BIG_PRDT_IMG_URL"]),

    # ────────────── 공급망 ──────────────
    ("공급중단", 534, "supply_stop",
     {},
     ["ENTP_NAME", "ITEM_NAME", "EDI_CODE", "SUSPEND_DATE", "SUSPEND_REASON", "INV_QTY", "SUPPLY_PLAN"]),
    ("공급부족", 537, "supply_lack",
     {},
     ["ENTP_NAME", "ITEM_NAME", "EDI_CODE", "SHORT_SUPPLY_EXPT_DATE", "SHORT_SUPPLY_REASON", "INV_QTY", "TREATMENT_INFU"]),
    ("국가출하승인", 142, "drug_natn_shipmnt",
     {},
     ["RECEIPT_NO", "SAMPLE_TYPE", "GOODS_NAME", "MANUF_ENTP_NAME", "RESULT_DATE", "VALID_TERM"]),
    ("GMP 적합판정", 132, "drug_gmp_jgmt",
     {"BSSH_NM": "광동제약"},
     ["BSSH_NM", "FCTR_ADDR", "KGMP_BGMP_NAME", "GMP_INGR_MM_GROUP_NAME", "VLD_PRD_YMD"]),

    # ────────────── 업체 / DMF ──────────────
    ("업체허가 목록", 144, "drug_entity_list",
     {},
     ["ENTRPS", "RPRSNTV", "INDUTY", "PRMISN_NO", "PRMISN_DT", "BIZRNO"]),
    ("업체허가 상세", 144, "drug_entity_detail",
     {},
     ["ENTRPS", "INDUTY", "PRMISN_NO", "RPRSNTV", "ADDR"]),
    ("원료의약품 DMF", 483, "drug_dmf",
     {},
     ["DMF_PERMIT_NO", "INGR_KOR_NAME", "ENTP_NAME", "MNFCTR_NAME", "REGIST_DT"]),

    # ────────────── R&D 8개 ──────────────
    ("의약품 특허", 561, "drug_patent",
     {},
     ["INGR_NAME", "ITEM_NAME", "ENTP_NAME", "PAT_NO", "EXPIRE_DATE"]),
    ("국내소송 특허", 557, "drug_lawsuit",
     {},
     ["INGR_NAME", "PRT_NAME", "JUDGMENT_KIND", "KOR_PAT_NO", "JUDGE_DATE"]),
    ("FDA Paragraph IV", 552, "drug_fda_p4",
     {},
     ["DRUG_NAME", "DOSAGE_FORM", "STRENGTH", "RLD", "DATE_OF_SUBMISSION"]),
    ("FDA 오렌지북", 562, "drug_fda_orangebook",
     {},
     ["INGR_NAME", "PRT_NAME", "KOR_APPLY_NO", "KOR_PAT_NO", "USA_PAT_NO"]),
    ("임상시험 정보", 566, "drug_clinical",
     {},
     ["APPLY_ENTP_NAME", "APPROVAL_TIME", "LAB_NAME", "GOODS_NAME", "PHASE"]),
    ("임상시험 실시기관", 568, "drug_clinical_org",
     {},
     ["LAB_SEQ", "LAB_NAME", "BOSS_NAME", "APPOINT_DATE", "ADDR"]),
    ("대조약", 484, "drug_reference",
     {},
     ["INGR_NAME", "ITEM_NAME", "ENTP_NAME", "COMP_DRUG_GB_KOR", "BIO_AVAIL_DATE"]),
    ("생동성인정품목", 485, "drug_bioeq",
     {},
     ["ITEM_NAME", "ENTP_NAME", "INGR_KOR_NAME", "DOSAGE_FORM", "QNT"]),

    # ────────────── 재심사·재평가·희귀 ──────────────
    ("재심사", 554, "drug_review",
     {},
     ["ENTP_NAME", "FACTORY_ADDR", "BOSS_NAME", "ITEM_NAME", "PERMIT_DATE", "ANNUAL_KIND"]),
    ("재평가", 556, "drug_reeval",
     {},
     ["ENTP_NAME", "ENTP_NO", "BOSS_NAME", "ITEM_NAME", "REVAL_DATE"]),
    ("희귀의약품", 565, "drug_orphan",
     {},
     ["RARITY_DRUG_APPOINT_NO", "PRODT_NAME", "TARGET_DISEASE", "APPOINT_DATE", "DEVSTEP_YN"]),
    ("희귀필수 - 자가치료용", 81, "drug_rare_self",
     {},
     ["INGR", "MEDCIN_NAME", "EFFICACY", "MATERIAL_QNT"]),
    ("희귀필수 - 치료용", 81, "drug_rare_treat",
     {},
     ["INGR", "MEDCIN_NAME", "EFFICACY", "MATERIAL_QNT", "REQUEST_DIVS"]),

    # ────────────── 의약외품 ──────────────
    ("의약외품 허가", 145, "quasi_approval",
     {"item_name": "마스크"},
     ["ITEM_NAME", "ENTP_NAME", "ITEM_PERMIT_DATE", "PRODUCT_TYPE", "ITEM_INGR_NAME"]),

    # ────────────── 식품 ──────────────
    ("식품 영양 DB", 1, "food_nutrition",
     {"FOOD_NM_KR": "김치"},
     ["FOOD_CD", "FOOD_NM_KR", "DB_GROUP", "MAKER_NAME", "AMT_NUM1", "NUTR_CONT1"]),
    ("식품 행정처분 - 수입식품업", 3, "food_disc_import",
     {},
     ["PRCSCITYPOINT_BSSHNM", "INDUTY_CD_NM", "LCNS_NO", "DSPS_DCSNDT", "VIOL_CN"]),
    ("식품 행정처분 - 식품판매업", 5, "food_disc_sale",
     {},
     ["PRCSCITYPOINT_BSSHNM", "INDUTY_CD_NM", "LCNS_NO", "DSPS_DCSNDT", "VIOL_CN"]),
    ("식품 행정처분 - 식품제조가공업", 6, "food_disc_mnft",
     {},
     ["PRCSCITYPOINT_BSSHNM", "INDUTY_CD_NM", "LCNS_NO", "DSPS_DCSNDT", "VIOL_CN"]),
    ("수입식품 회수판매중지", 153, "food_recall_import",
     {},
     ["PRDT_NM", "CLNT_BSSH_NM", "MNFT_YMD_RLAT_CONT", "CIRC_PRD", "RECL_REASON"]),
    ("검사부적합 목록", 535, "food_inspect_list",
     {},
     ["PRDUCT", "ENTRPS", "IMPROPT_ITM", "STANDARD", "REGIST_DT"]),
    ("검사부적합 상세", 535, "food_inspect_item",
     {},
     ["PRDUCT", "FOOD_TY", "ENTRPS", "ADRES1", "IMPROPT_RESN"]),
    ("건강기능식품 GMP", 51, "hf_gmp",
     {},
     ["LCNS_NO", "BSSH_NM", "INDUTY_CD_NM", "PRSDNT_NM", "ADDR"]),
    ("식품 스마트HACCP", 12, "haccp_smart",
     {},
     ["appointno", "businessnm", "presidentnm", "address", "industryname", "businessitem"]),
]


def call(endpoint, extra_params=None):
    """API 호출 → totalCount + items 추출."""
    params = {"serviceKey": SERVICE_KEY, "type": "xml", "pageNo": "1", "numOfRows": "2"}
    if extra_params:
        params.update(extra_params)
    url = endpoint + "?" + urllib.parse.urlencode(params)
    try:
        body = urllib.request.urlopen(url, timeout=30, context=CTX).read().decode("utf-8", errors="replace")
        # totalCount 추출
        m = re.search(r"<totalCount>(\d+)</totalCount>", body)
        total = int(m.group(1)) if m else -1
        # items 추출 — 첫 item 의 모든 필드
        first_item_match = re.search(r"<item>(.*?)</item>", body, re.S)
        first_item = {}
        if first_item_match:
            for k, v in re.findall(r"<(\w+)>([^<]*)</\w+>", first_item_match.group(1)):
                first_item[k] = v.strip()
        # resultMsg
        rmsg = re.search(r"<resultMsg>([^<]*)</resultMsg>", body)
        return {"total": total, "first": first_item, "msg": rmsg.group(1) if rmsg else ""}
    except Exception as e:
        return {"total": -2, "first": {}, "msg": f"ERR: {str(e)[:50]}"}


def main():
    print("=" * 120)
    print(f" RegHub 360 — 35+ API 전수 검증 (각 API에 임의 값 + 핵심 필드 추출)")
    print("=" * 120)

    success = 0
    partial = 0
    failed = 0

    for label, no, ep_key, params, expected_fields in CASES:
        endpoint = API_ENDPOINTS.get(ep_key)
        if not endpoint:
            print(f"\n[SKIP] NO {no:3d} {label} — 엔드포인트 미정의")
            failed += 1
            continue

        result = call(endpoint, params)
        total = result["total"]
        first = result["first"]
        msg = result["msg"]

        # 핵심 필드 매칭 평가
        present_fields = [f for f in expected_fields if f in first and first[f]]
        coverage = len(present_fields) / max(len(expected_fields), 1) * 100

        if total < 0:
            status = "❌ FAIL"
            failed += 1
        elif total == 0:
            status = "⚪ 데이터 0건"
            partial += 1
        elif coverage >= 60:
            status = f"✅ 완전 ({coverage:.0f}%)"
            success += 1
        elif coverage >= 30:
            status = f"🟡 부분 ({coverage:.0f}%)"
            partial += 1
        else:
            status = f"🟠 필드 불일치 ({coverage:.0f}%)"
            partial += 1

        print(f"\n● [NO {no:3d}] {label}  {status}")
        print(f"    파라미터: {params or '(없음)'}")
        print(f"    응답: total={total}, msg={msg[:40]}")
        if first:
            # 첫 item의 주요 필드 5개 출력
            key_items = list(first.items())[:8]
            for k, v in key_items:
                if v:
                    val_short = v[:55].replace("\n", " ")
                    print(f"      {k}: {val_short}")
        else:
            print(f"      (items 비어있음)")

    print()
    print("=" * 120)
    print(f" 종합: 완전 작동 {success}, 부분/0건 {partial}, 실패 {failed}, 전체 {len(CASES)}")
    print("=" * 120)


if __name__ == "__main__":
    main()
