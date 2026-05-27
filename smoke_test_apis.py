"""
RegHub 360 — 18개 승인 API smoke test
2026-05-26 공공데이터포털 발급 SERVICE_KEY 작동 확인용

실행: python smoke_test_apis.py
출력: 각 API 호출 결과 (HTTP 상태, resultCode, totalCount, 샘플 필드)
"""
import sys
import io
import json
import time
import urllib3
import requests
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from pathlib import Path

# Windows 콘솔 UTF-8 출력
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 패키지 import 가능하도록 부모 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from drug_integrated_search.config import (
    API_ENDPOINTS, SERVICE_KEY, FOODSAFETY_BASE, FOODSAFETY_SERVICES,
    FOODSAFETY_KEY_ID, REQUEST_TIMEOUT, VERIFY_SSL
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# 헬퍼
# ============================================================================
def call_data_go_kr(endpoint: str, extra_params: dict = None, num_rows: int = 3):
    """data.go.kr 공통 호출 (XML 응답 우선)"""
    key = SERVICE_KEY.strip()
    # URL 인코딩 해제 (퍼센트 이스케이프 들어온 경우)
    if "%2" in key.lower() or "%25" in key:
        key = unquote(key)

    params = {
        "serviceKey": key,
        "pageNo": "1",
        "numOfRows": str(num_rows),
        "type": "xml",
    }
    if extra_params:
        params.update(extra_params)

    try:
        r = requests.get(endpoint, params=params, timeout=REQUEST_TIMEOUT, verify=VERIFY_SSL)
        return _parse_data_go_kr(r, endpoint)
    except requests.exceptions.HTTPError as e:
        return {"ok": False, "http": e.response.status_code if e.response else "?",
                "error": str(e), "totalCount": 0, "sample_keys": []}
    except Exception as e:
        return {"ok": False, "http": "EXC", "error": str(e), "totalCount": 0, "sample_keys": []}


def _parse_data_go_kr(r: requests.Response, endpoint: str) -> dict:
    http = r.status_code
    if http != 200:
        return {"ok": False, "http": http, "error": f"HTTP {http}", "totalCount": 0,
                "sample_keys": [], "snippet": r.text[:200]}
    try:
        root = ET.fromstring(r.text)
        rcode = root.findtext(".//resultCode", "") or ""
        rmsg = root.findtext(".//resultMsg", "") or ""
        total = root.findtext(".//totalCount", "0") or "0"
        items = root.findall(".//item")
        sample_keys = []
        if items:
            sample_keys = [c.tag for c in items[0]][:8]
        # 성공 코드: 00 또는 빈 문자열(일부 API)
        ok = (rcode in ("00", "")) and (rmsg.lower() in ("normal service.", "정상", "ok", ""))
        return {
            "ok": ok if ok else (int(total) > 0 if total.isdigit() else False),
            "http": http,
            "resultCode": rcode, "resultMsg": rmsg,
            "totalCount": int(total) if total.isdigit() else 0,
            "sample_keys": sample_keys,
            "n_items": len(items),
        }
    except ET.ParseError as e:
        return {"ok": False, "http": http, "error": f"XML parse: {e}", "totalCount": 0,
                "sample_keys": [], "snippet": r.text[:200]}


def call_foodsafety(service_id: str, num_rows: int = 3):
    """식품안전나라 호출 (KEY_ID 발급 시에만 유효)"""
    if not FOODSAFETY_KEY_ID:
        return {"ok": False, "http": "NO_KEY",
                "error": "FOODSAFETY_KEY_ID 미설정 — 식품안전나라 별도 신청 필요",
                "totalCount": 0, "sample_keys": []}
    url = f"{FOODSAFETY_BASE}/{FOODSAFETY_KEY_ID}/{service_id}/json/1/{num_rows}"
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT, verify=VERIFY_SSL)
        if r.status_code != 200:
            return {"ok": False, "http": r.status_code, "error": f"HTTP {r.status_code}",
                    "totalCount": 0, "sample_keys": []}
        data = r.json()
        root = data.get(service_id, {})
        total = int(root.get("total_count", 0))
        rows = root.get("row", [])
        return {
            "ok": total > 0 or len(rows) > 0,
            "http": 200,
            "resultCode": root.get("RESULT", {}).get("CODE", ""),
            "resultMsg": root.get("RESULT", {}).get("MSG", ""),
            "totalCount": total,
            "sample_keys": list(rows[0].keys())[:8] if rows else [],
            "n_items": len(rows),
        }
    except Exception as e:
        return {"ok": False, "http": "EXC", "error": str(e),
                "totalCount": 0, "sample_keys": []}


# ============================================================================
# 18개 API 테스트 케이스
# ============================================================================
DATA_GO_KR_TESTS = [
    # (라벨, NO, API_ENDPOINTS 키, 추가 파라미터)
    ("의약품 허가정보 (목록)",        140, "approval",            {"item_name": "타이레놀"}),
    ("의약품 허가정보 (상세)",        140, "approval_detail",     {"item_name": "타이레놀"}),
    ("의약품 허가정보 (주성분)",      140, "approval_ingr",       {"item_name": "타이레놀"}),
    ("의약품 행정처분",              564, "disciplinary",        {"order": "Y"}),
    ("의약품 회수·판매중지 (목록)",   539, "recall",              {}),
    ("의약품 회수·판매중지 (상세)",   539, "recall_detail",       {}),
    ("의약품외 회수·판매중지 (목록)", 539, "recall_etc",          {}),
    ("의약품 낱알식별",              563, "identification",      {"item_name": "타이레놀"}),
    ("의약품 안전성서한",            547, "safety_letter",       {}),
    ("의약품 생산수입공급중단",       534, "supply_stop",         {}),
    ("의약품 공급부족",              537, "supply_lack",         {}),
    ("DUR 품목 (병용금기)",          531, "dur_item_combine",    {}),
    ("DUR 품목 (DUR 목록)",          531, "dur_item_list",       {}),
    ("DUR 성분 (병용금기)",          533, "dur_ingr_combine",    {}),
    ("DUR 성분 (임부금기)",          533, "dur_ingr_pregnancy",  {}),
    ("의약외품 허가정보",            145, "quasi_approval",      {}),
    ("식품 영양성분 DB",             1,   "food_nutrition",      {}),
    ("식품 행정처분 (수입식품업)",   3,   "food_disc_import",    {}),
    ("식품 행정처분 (식품판매업)",   5,   "food_disc_sale",      {}),
    ("식품 행정처분 (식품제조가공업)",6,  "food_disc_mnft",      {}),
    ("수입식품 회수판매중지",        153, "food_recall_import",  {}),

    # ─── 2026-05-27 신규 승인 17개 ────────────────────────────────────────────
    ("의약품 e약은요",               248, "drug_easy",           {}),
    ("의약품 묶음의약품(HIRA/ATC)",  269, "drug_bundle",         {}),
    ("의약품 GMP 적합판정서",        132, "drug_gmp_jgmt",       {}),
    ("의약품 국가출하승인",          142, "drug_natn_shipmnt",   {}),
    ("의약품 업체허가 (목록)",       144, "drug_entity_list",    {}),
    ("의약품 업체허가 (상세)",       144, "drug_entity_detail",  {}),
    ("의약품 원료등록(DMF)",         483, "drug_dmf",            {}),
    ("의약품 특허정보",              561, "drug_patent",         {}),
    ("의약품 국내소송 특허",         557, "drug_lawsuit",        {}),
    ("의약품 FDA P4",                552, "drug_fda_p4",         {}),
    ("의약품 FDA 오렌지북",          562, "drug_fda_orangebook", {}),
    ("의약품 임상시험",              566, "drug_clinical",       {}),
    ("의약품 임상기관",              568, "drug_clinical_org",   {}),
    ("의약품 대조약",                484, "drug_reference",      {}),
    ("의약품 생동성인정품목",        485, "drug_bioeq",          {}),
    ("의약품 재심사",                554, "drug_review",         {}),
    ("의약품 재평가",                556, "drug_reeval",         {}),
    ("의약품 희귀의약품",            565, "drug_orphan",         {}),
    ("의약품 희귀필수(자가치료용)",  81,  "drug_rare_self",      {}),
    ("의약품 희귀필수(치료용)",      81,  "drug_rare_treat",     {}),
    ("식품 검사부적합 (목록)",       535, "food_inspect_list",   {}),
    ("식품 검사부적합 (상세)",       535, "food_inspect_item",   {}),
    ("건강기능식품 GMP",             51,  "hf_gmp",              {}),
    ("식품 스마트HACCP (B553748)",   12,  "haccp_smart",         {}),
]

FOODSAFETY_TESTS = [
    ("식품 회수·판매중지 (국내·식품안전나라 폴백)", 339, "food_recall_domestic"),
]


# ============================================================================
# 2026-05-26 추가 승인 5개 API — End Point 자동 탐색
# (마이페이지에서 정확한 명세를 확인하기 전까지 후보 URL 다중 시도)
# 동일 SERVICE_KEY 사용 확인됨
# ============================================================================
PROBE_TARGETS = [
    {
        "label": "식품 회수·판매중지 (국내)",
        "no": 339,
        "candidates": [
            "FoodRcalSleStpgeService/getFoodRcalSleStpgeList",
            "FoodReclSaleStopPrdtStusService/getFoodReclSaleStopPrdtStusInq",
            "FoodReclSaleStopService/getFoodReclSaleStopList",
            "FoodRtrvlSleStpgeInfoService/getFoodRtrvlSleStpgelList",
        ],
    },
    {
        "label": "해외 위해식품 회수정보",
        "no": 225,
        "candidates": [
            "OvrsHzrdFoodReclService/getOvrsHzrdFoodReclList",
            "OvsHrmflFoodReclService/getOvsHrmflFoodReclInq",
            "OvrsHrmFoodReclInfoService/getOvrsHrmFoodReclList",
            "WrldRiskFoodReclService/getWrldRiskFoodReclInq",
            "OvrsHrmflFoodRcalService/getOvrsHrmflFoodRcalList",
        ],
    },
    {
        "label": "식품(첨가물) 품목제조보고",
        "no": 444,
        "candidates": [
            "FoodMnftRptService/getFoodMnftRptList",
            "FoodPrdlstRprtService/getFoodPrdlstRprtInq",
            "FoodPrdlstMnftRptInfoService/getFoodPrdlstMnftRptList",
            "FoodIngrdtPrdlstService/getFoodIngrdtPrdlstList",
        ],
    },
    {
        "label": "식품(첨가물) 품목제조보고(원재료)",
        "no": 470,
        "candidates": [
            "FoodMnftRptRawmtrlService/getFoodMnftRptRawmtrlList",
            "FoodPrdlstRprtRawmtrlService/getFoodPrdlstRprtRawmtrlInq",
            "FoodRawmtrlService/getFoodRawmtrlList",
            "FoodIngrdtRawmtrlService/getFoodIngrdtRawmtrlList",
        ],
    },
    {
        "label": "행정처분(식품접객업)",
        "no": 477,
        "candidates": [
            "AdmmRsltFoodSrvcService/getAdmmRsltFoodSrvcBssh",
            "AdmmRsltFoodSrvtService/getAdmmRsltFoodSrvtBssh",
            "AdmmRsltFoodEntrtnService/getAdmmRsltFoodEntrtnBssh",
            "AdmmRsltFoodRcptnService/getAdmmRsltFoodRcptnBssh",
            "AdmmRsltFoodWlfrService/getAdmmRsltFoodWlfrBssh",
        ],
    },
]


def probe_endpoint_candidates():
    """추가 승인 5개 API의 End Point 자동 탐색"""
    base = "https://apis.data.go.kr/1471000"
    discovered = {}
    print("\n[3] 신규 승인 5개 API — End Point 탐색 (후보 URL 다중 시도)")
    print("-" * 90)
    for target in PROBE_TARGETS:
        label = target["label"]
        no = target["no"]
        print(f"\n▶ NO {no} {label}")
        for i, path in enumerate(target["candidates"], 1):
            endpoint = f"{base}/{path}"
            res = call_data_go_kr(endpoint, {}, num_rows=1)
            http = res.get("http")
            rcode = res.get("resultCode", "")
            ok = res.get("ok")
            if ok and http == 200 and rcode == "00":
                print(f"   ✅ [{i}/{len(target['candidates'])}] {path} → total={res.get('totalCount')} fields={res.get('sample_keys')[:4]}")
                discovered[no] = {"label": label, "endpoint": endpoint, "result": res}
                break
            else:
                err = res.get("error", "") or res.get("resultMsg", "") or f"HTTP {http}"
                print(f"   ❌ [{i}/{len(target['candidates'])}] {path} → {err[:60]}")
            time.sleep(0.3)
        else:
            print(f"   ⚠️  자동 탐색 실패 — 마이페이지에서 정확한 End Point 확인 필요")
    return discovered

# ============================================================================
# 실행
# ============================================================================
def main():
    print("=" * 90)
    print(" RegHub 360 — 18개 승인 API smoke test")
    print(f" SERVICE_KEY: {SERVICE_KEY[:24]}...{SERVICE_KEY[-12:]}")
    print(f" FOODSAFETY_KEY_ID: {'설정됨' if FOODSAFETY_KEY_ID else '미설정 (별도 신청 필요)'}")
    print("=" * 90)

    results = []

    print("\n[1] data.go.kr 계열 (서비스키 인증)")
    print("-" * 90)
    print(f"{'#':<3}{'라벨':<35}{'NO':>5}  {'HTTP':>5} {'rCode':>6} {'total':>8}  {'필드샘플':<30}")
    print("-" * 90)
    for i, (label, no, key, extra) in enumerate(DATA_GO_KR_TESTS, 1):
        endpoint = API_ENDPOINTS.get(key)
        if not endpoint:
            print(f"{i:<3}{label:<35}{no:>5}  {'SKIP':>5} (endpoint 미정의: {key})")
            results.append({"label": label, "no": no, "key": key, "ok": False, "reason": "endpoint_missing"})
            continue
        res = call_data_go_kr(endpoint, extra)
        ok_mark = "✅" if res.get("ok") else "❌"
        sample = ", ".join(res.get("sample_keys", [])[:4]) or res.get("error", "")[:30]
        print(f"{i:<3}{label:<35}{no:>5}  {str(res.get('http')):>5} {str(res.get('resultCode','')):>6} {res.get('totalCount',0):>8}  {ok_mark} {sample}")
        results.append({"label": label, "no": no, "key": key, **res})
        time.sleep(0.3)  # 호출 한도 여유

    # 추가 승인 5개 API End Point 탐색
    discovered = probe_endpoint_candidates()

    print("\n[2] foodsafetykorea.go.kr 계열 (KeyID 인증) — 폴백용 (NO 339 data.go.kr 탐색 실패시만)")
    print("-" * 90)
    for i, (label, no, sid_key) in enumerate(FOODSAFETY_TESTS, 1):
        sid = FOODSAFETY_SERVICES.get(sid_key)
        if not sid:
            print(f"{i:<3}{label:<35}{no:>5}  SKIP (service_id 미정의)")
            continue
        res = call_foodsafety(sid)
        ok_mark = "✅" if res.get("ok") else "❌"
        sample = ", ".join(res.get("sample_keys", [])[:4]) or res.get("error", "")[:60]
        print(f"{i:<3}{label:<35}{no:>5}  {str(res.get('http')):>5} {str(res.get('resultCode','')):>6} {res.get('totalCount',0):>8}  {ok_mark} {sample}")
        results.append({"label": label, "no": no, "service_id": sid, **res})

    # 요약
    print("\n" + "=" * 90)
    ok_n = sum(1 for r in results if r.get("ok"))
    print(f" 결과 요약: 성공 {ok_n} / 전체 {len(results)}")
    fail = [r for r in results if not r.get("ok")]
    if fail:
        print("\n 실패 / 확인 필요:")
        for r in fail:
            print(f"  - [{r.get('no')}] {r.get('label')} → HTTP={r.get('http')}, "
                  f"reason={r.get('error') or r.get('resultMsg') or r.get('reason') or '?'}")
    print("=" * 90)

    # 탐색 결과 요약
    if discovered:
        print("\n 🎯 추가 승인 5개 중 자동 탐색 성공:")
        for no, info in discovered.items():
            print(f"   - NO {no} {info['label']} → {info['endpoint']}")

    # JSON 결과 파일 저장 (디버깅용)
    out_path = Path(__file__).parent / "smoke_test_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"verified": results, "discovered": {
            str(no): {"label": info["label"], "endpoint": info["endpoint"]}
            for no, info in discovered.items()
        }}, f, ensure_ascii=False, indent=2)
    print(f"\n 상세 결과: {out_path}")


if __name__ == "__main__":
    main()
