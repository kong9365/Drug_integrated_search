"""
RegHub 360 — 35개 API 파라미터 정확도 검증 (베니톨정 기준)
4가지 입력값으로 호출하여 어떤 파라미터가 진짜 필터링되는지 매트릭스 출력.

베니톨정 메타 (NO 140 응답):
  ITEM_SEQ        = 199401695
  ITEM_NAME       = 베니톨정(미세정제플라보노이드분획물)
  ENTP_NAME       = 광동제약(주)
  ENTP_SEQ        = 19920004
  BIZRNO          = 1138108888
  EDI_CODE        = 641801640
  ITEM_INGR_NAME  = Purified and Micronized Flavonoid Fraction
"""
import sys
import io
import ssl
import urllib.request
import urllib.parse
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, "..")
from drug_integrated_search.config import SERVICE_KEY, API_ENDPOINTS

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def call(endpoint, extra_params=None):
    """API 호출 → totalCount 추출."""
    params = {"serviceKey": SERVICE_KEY, "type": "xml", "pageNo": "1", "numOfRows": "1"}
    if extra_params:
        params.update(extra_params)
    url = endpoint + "?" + urllib.parse.urlencode(params)
    try:
        body = urllib.request.urlopen(url, timeout=30, context=CTX).read().decode("utf-8", errors="replace")
        m = re.search(r"<totalCount>(\d+)</totalCount>", body)
        return int(m.group(1)) if m else -1
    except Exception as e:
        return f"ERR:{str(e)[:30]}"


# (라벨, NO, 엔드포인트 키, 파라미터 후보 dict[label]=params_dict)
TARGETS = [
    # 1. 의약품 허가 — 기준 (이미 작동 확인)
    ("의약품 허가", 140, "approval", {
        "베이스": {},
        "item_name=베니톨": {"item_name": "베니톨"},
        "item_name=베니톨정": {"item_name": "베니톨정"},
        "entp_name=광동제약": {"entp_name": "광동제약"},
        "item_seq=199401695": {"item_seq": "199401695"},
        "bizrno": {"bizrno": "1138108888"},
        "edi_code": {"edi_code": "641801640"},
    }),
    # 2. e약은요 — 카멜케이스
    ("e약은요", 248, "drug_easy", {
        "베이스": {},
        "itemName=베니톨": {"itemName": "베니톨"},
        "itemName=베니톨정": {"itemName": "베니톨정"},
        "entpName=광동제약": {"entpName": "광동제약"},
        "itemSeq=199401695": {"itemSeq": "199401695"},
    }),
    # 3. 낱알식별 (NO 563)
    ("낱알식별", 563, "identification", {
        "베이스": {},
        "item_name=베니톨": {"item_name": "베니톨"},
        "item_name=베니톨정": {"item_name": "베니톨정"},
        "entp_name=광동제약": {"entp_name": "광동제약"},
        "item_seq=199401695": {"item_seq": "199401695"},
    }),
    # 4. 행정처분 (NO 564)
    ("행정처분", 564, "disciplinary", {
        "베이스": {},
        "item_name=베니톨": {"item_name": "베니톨"},
        "entp_name=광동제약": {"entp_name": "광동제약"},
        "order=Y": {"order": "Y"},
    }),
    # 5. 회수·판매중지 (NO 539)
    ("회수·판매중지", 539, "recall", {
        "베이스": {},
        "item_name": {"item_name": "베니톨"},
        "PRDUCT": {"PRDUCT": "베니톨"},
        "entp_name": {"entp_name": "광동제약"},
        "ENTRPS": {"ENTRPS": "광동제약"},
    }),
    # 6. 안전성서한 (NO 547)
    ("안전성서한", 547, "safety_letter", {
        "베이스": {},
        "title": {"title": "베니톨"},
        "TITLE": {"TITLE": "베니톨"},
    }),
    # 7. 공급중단 (NO 534)
    ("공급중단", 534, "supply_stop", {
        "베이스": {},
        "ENTP_NAME": {"ENTP_NAME": "광동제약"},
        "ITEM_NAME": {"ITEM_NAME": "베니톨"},
        "entp_name": {"entp_name": "광동제약"},
        "item_name": {"item_name": "베니톨"},
    }),
    # 8. 공급부족 (NO 537)
    ("공급부족", 537, "supply_lack", {
        "베이스": {},
        "ENTP_NAME": {"ENTP_NAME": "광동제약"},
        "ITEM_NAME": {"ITEM_NAME": "베니톨"},
    }),
    # 9. DUR 품목 (NO 531) - 병용금기 1개 오퍼레이션만 테스트
    ("DUR 품목 병용금기", 531, "dur_item_combine", {
        "베이스": {},
        "ITEM_NAME": {"ITEM_NAME": "베니톨"},
        "itemName": {"itemName": "베니톨"},
        "INGR_NAME": {"INGR_NAME": "Flavonoid"},
    }),
    # 10. 묶음의약품 (NO 269)
    ("묶음의약품", 269, "drug_bundle", {
        "베이스": {},
        "trustItemName": {"trustItemName": "베니톨"},
        "trustMainingr": {"trustMainingr": "Flavonoid"},
        "atcCode": {"atcCode": "C05CA"},
    }),
    # 11. GMP 적합판정 (NO 132)
    ("GMP 적합판정", 132, "drug_gmp_jgmt", {
        "베이스": {},
        "BSSH_NM": {"BSSH_NM": "광동제약"},
        "bssh_nm": {"bssh_nm": "광동제약"},
    }),
    # 12. 국가출하승인 (NO 142)
    ("국가출하승인", 142, "drug_natn_shipmnt", {
        "베이스": {},
        "goodsName": {"goodsName": "베니톨"},
        "GOODS_NAME": {"GOODS_NAME": "베니톨"},
        "manufEntpName": {"manufEntpName": "광동제약"},
    }),
    # 13. 업체허가 목록 (NO 144)
    ("업체허가 목록", 144, "drug_entity_list", {
        "베이스": {},
        "ENTRPS": {"ENTRPS": "광동제약"},
        "entrps": {"entrps": "광동제약"},
        "INDUTY": {"INDUTY": "의약품"},
    }),
    # 14. 원료의약품 DMF (NO 483)
    ("원료의약품 DMF", 483, "drug_dmf", {
        "베이스": {},
        "ENTP_NAME": {"ENTP_NAME": "광동제약"},
        "INGR_KOR_NAME": {"INGR_KOR_NAME": "플라보노이드"},
    }),
    # 15. 특허 (NO 561)
    ("의약품 특허", 561, "drug_patent", {
        "베이스": {},
        "ITEM_NAME": {"ITEM_NAME": "베니톨"},
        "applicant": {"applicant": "광동제약"},
    }),
    # 16. 임상시험 (NO 566)
    ("임상시험", 566, "drug_clinical", {
        "베이스": {},
        "GOODS_NAME": {"GOODS_NAME": "베니톨"},
        "APPLY_ENTP_NAME": {"APPLY_ENTP_NAME": "광동제약"},
    }),
    # 17. 임상기관 (NO 568)
    ("임상기관", 568, "drug_clinical_org", {
        "베이스": {},
        "LAB_NAME": {"LAB_NAME": "광동"},
    }),
    # 18. 희귀의약품 (NO 565)
    ("희귀의약품", 565, "drug_orphan", {
        "베이스": {},
        "productName": {"productName": "베니톨"},
        "applyName": {"applyName": "광동제약"},
    }),
    # 19. 재심사 (NO 554)
    ("재심사", 554, "drug_review", {
        "베이스": {},
        "ENTP_NAME": {"ENTP_NAME": "광동제약"},
        "ITEM_NAME": {"ITEM_NAME": "베니톨"},
    }),
    # 20. 재평가 (NO 556)
    ("재평가", 556, "drug_reeval", {
        "베이스": {},
        "ENTP_NAME": {"ENTP_NAME": "광동제약"},
        "ITEM_NAME": {"ITEM_NAME": "베니톨"},
    }),
    # 21. 대조약 (NO 484)
    ("대조약", 484, "drug_reference", {
        "베이스": {},
        "ITEM_NAME": {"ITEM_NAME": "베니톨"},
        "INGR_NAME": {"INGR_NAME": "Flavonoid"},
    }),
    # 22. 생동성 (NO 485)
    ("생동성", 485, "drug_bioeq", {
        "베이스": {},
        "ITEM_NAME": {"ITEM_NAME": "베니톨"},
        "INGR_KOR_NAME": {"INGR_KOR_NAME": "플라보노이드"},
    }),
    # 23. 의약외품 허가 (NO 145)
    ("의약외품 허가", 145, "quasi_approval", {
        "베이스": {},
        "item_name": {"item_name": "마스크"},
        "entp_name": {"entp_name": "광동제약"},
    }),
]


def main():
    print("=" * 110)
    print(f" RegHub 360 — 35개 API 파라미터 정확도 매트릭스 (베니톨정 기준)")
    print(f" 베니톨정 메타: ITEM_SEQ=199401695, ENTP_NAME=광동제약(주)")
    print("=" * 110)

    findings = []
    for label, no, ep_key, variants in TARGETS:
        endpoint = API_ENDPOINTS.get(ep_key)
        if not endpoint:
            print(f"\n● NO {no:3d} {label}: 엔드포인트 미정의 (key={ep_key})")
            continue
        print(f"\n● NO {no:3d} {label}")
        print(f"  endpoint: {endpoint}")
        baseline = None
        for vlabel, params in variants.items():
            total = call(endpoint, params)
            if vlabel == "베이스":
                baseline = total
                print(f"    {vlabel:30s} → total={total}  (베이스라인)")
            else:
                if isinstance(total, int) and isinstance(baseline, int):
                    if total < baseline:
                        print(f"    {vlabel:30s} → total={total:>6}  ✓ 필터링 작동 ({baseline}→{total})")
                        findings.append((no, label, vlabel, "works"))
                    elif total == baseline:
                        print(f"    {vlabel:30s} → total={total:>6}  ✗ 파라미터 무시 (전체와 동일)")
                    else:
                        print(f"    {vlabel:30s} → total={total:>6}  ? 더 큰 값?!")
                else:
                    print(f"    {vlabel:30s} → {total}")

    print()
    print("=" * 110)
    print(" 작동 확인된 파라미터 요약:")
    print("=" * 110)
    for no, label, p, _ in findings:
        print(f"  ✓ NO {no:3d} {label:20s} ← {p}")


if __name__ == "__main__":
    main()
