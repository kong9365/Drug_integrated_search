"""수정된 Parse 노드 코드를 실제 API 응답으로 end-to-end 테스트.

4개 YAML 의 Parse/Merge 코드 블록을 추출해 실제 API 응답을 넣어 실행한다.
"""
import json
import re
import sys
from pathlib import Path

import requests
import urllib3
import yaml

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding="utf-8")

KEY = "REDACTED_KEY"
BASE = "https://apis.data.go.kr/1471000"

ROOT = Path(__file__).parent


def fetch(path: str, extra: dict | None = None):
    params = {
        "serviceKey": KEY,
        "pageNo": 1,
        "numOfRows": 10,
        "type": "json",
        **(extra or {}),
    }
    r = requests.get(f"{BASE}/{path}", params=params, timeout=20, verify=False)
    return r.json()


def load_code_from_yaml(yaml_path: Path, node_title: str) -> str:
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    nodes = data["workflow"]["graph"]["nodes"]
    for n in nodes:
        d = n["data"]
        if d.get("type") == "code" and d.get("title") == node_title:
            return d["code"]
    raise RuntimeError(f"{yaml_path} 에서 {node_title} 노드를 찾지 못함")


def run_code(code: str, call_expr: str):
    ns: dict = {}
    exec(code, ns)
    return eval(call_expr, ns)


def test_disciplinary():
    print("\n=== [TEST] 행정처분 ParseDisc ===")
    body = fetch("MdcinExaathrService04/getMdcinExaathrList04",
                 {"order": "Y"})
    code = load_code_from_yaml(ROOT / "drug_daily_disciplinary_report.yml",
                               "ParseDisc")
    result = run_code(
        code,
        'main(body, "2026-01-01", "2026-12-31", "", 5)',
    ).copy() if False else None
    ns: dict = {"body": body}
    exec(code, ns)
    result = ns["main"](body, "2026-01-01", "2026-12-31", "", 5)
    print(f"count={result['count']}")
    print(result["summary_text"])
    assert result["count"] > 0, "행정처분 0건 = 파싱 실패"
    # 날짜 비어있지 않은 항목이 최소 1개는 있어야 함
    non_empty_dates = [it for it in result["raw_items"] if it["date"]]
    assert non_empty_dates, "날짜가 모두 비어있음 = 필드명 미스매치"
    print("[PASS] 행정처분 파싱 정상")


def test_recall():
    print("\n=== [TEST] 회수·판매중지 ParseRecall ===")
    body = fetch("MdcinRtrvlSleStpgeInfoService04/getMdcinRtrvlSleStpgeItem03")
    code = load_code_from_yaml(ROOT / "drug_daily_recall_report.yml",
                               "ParseRecall")
    ns: dict = {}
    exec(code, ns)
    result = ns["main"](body, "2026-01-01", "2026-12-31", "", 5)
    print(f"count={result['count']}")
    print(result["summary_text"])
    assert result["count"] > 0, "회수 0건 = 파싱 실패"
    non_empty_dates = [it for it in result["raw_items"] if it["date"]]
    non_empty_names = [it for it in result["raw_items"] if it["item_name"]]
    non_empty_companies = [it for it in result["raw_items"] if it["company"]]
    assert non_empty_dates, "회수: 날짜 전부 비어있음"
    assert non_empty_names, "회수: 품목명 전부 비어있음"
    assert non_empty_companies, "회수: 업체 전부 비어있음"
    print("[PASS] 회수 파싱 정상")


def test_merge():
    print("\n=== [TEST] 통합 워크플로우 MergeResults ===")
    approval = fetch("DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07",
                     {"item_name": "타이레놀"})
    recall = fetch("MdcinRtrvlSleStpgeInfoService04/getMdcinRtrvlSleStpgeItem03")
    disc = fetch("MdcinExaathrService04/getMdcinExaathrList04", {"order": "Y"})
    ident = fetch("MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03",
                  {"item_name": "타이레놀"})
    code = load_code_from_yaml(ROOT / "drug_integrated_search_workflow.yml",
                               "MergeResults")
    ns: dict = {}
    exec(code, ns)
    result = ns["main"](approval, recall, disc, ident, "타이레놀", "")
    print("summary_text:")
    print(result["summary_text"])
    print(f"\napproval={len(result['approval_items'])}, "
          f"recall={len(result['recall_items'])}, "
          f"disc={len(result['disciplinary_items'])}, "
          f"ident={len(result['identification_items'])}, "
          f"has_risk={result['has_risk']}")
    assert result["approval_items"], "허가정보 0건 = 파싱/엔드포인트 실패"
    assert result["identification_items"], "낱알식별 0건 = 파싱 실패"
    first_appr = result["approval_items"][0]
    assert first_appr["item_name"], "허가정보 item_name 비어있음"
    assert first_appr["permit_date"], "허가정보 permit_date 비어있음"
    first_disc = result["disciplinary_items"][0]
    assert first_disc["date"], "행정처분 date 비어있음"
    first_recall = result["recall_items"][0]
    assert first_recall["item_name"], "회수 item_name 비어있음"
    print("[PASS] 통합 워크플로우 파싱 정상")


def test_agent_merge():
    print("\n=== [TEST] 에이전트 MergeResults ===")
    approval = fetch("DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07",
                     {"item_name": "타이레놀"})
    recall = fetch("MdcinRtrvlSleStpgeInfoService04/getMdcinRtrvlSleStpgeItem03")
    disc = fetch("MdcinExaathrService04/getMdcinExaathrList04", {"order": "Y"})
    ident = fetch("MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03",
                  {"item_name": "타이레놀"})
    code = load_code_from_yaml(ROOT / "drug_integrated_search_agent.yml",
                               "MergeResults")
    ns: dict = {}
    exec(code, ns)
    result = ns["main"](approval, recall, disc, ident, "타이레놀", "")
    print("summary_text (앞 800자):")
    print(result["summary_text"][:800])
    assert result["approval_count"] > 0
    assert "타이레놀" in result["summary_text"]
    print(f"counts: approval={result['approval_count']}, "
          f"recall={result['recall_count']}, "
          f"disc={result['disciplinary_count']}, "
          f"ident={result['identification_count']}")
    print("[PASS] 에이전트 파싱 정상")


def main() -> int:
    try:
        test_disciplinary()
        test_recall()
        test_merge()
        test_agent_merge()
        print("\n>>> ALL TESTS PASSED <<<")
        return 0
    except AssertionError as e:
        print(f"\n!!! TEST FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
