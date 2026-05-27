"""공공 API 실제 응답 필드명을 확인하는 1회용 프로브 스크립트."""
import json
import sys

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SERVICE_KEY = (
    "REDACTED_KEY"
)

APIS = {
    "disciplinary": (
        "https://apis.data.go.kr/1471000/MdcinExaathrService04/getMdcinExaathrList04",
        {"order": "Y"},
    ),
    "recall": (
        "https://apis.data.go.kr/1471000/MdcinRtrvlSleStpgeInfoService04/getMdcinRtrvlSleStpgeItem03",
        {},
    ),
    "approval": (
        "https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnList07",
        {"item_name": "타이레놀"},
    ),
    "identification": (
        "https://apis.data.go.kr/1471000/MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03",
        {"item_name": "타이레놀"},
    ),
}


def probe(name, url, extra):
    params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": 1,
        "numOfRows": 3,
        "type": "json",
        **extra,
    }
    r = requests.get(url, params=params, timeout=20, verify=False)
    print(f"\n=== {name} [{r.status_code} {r.headers.get('content-type')}] ===")
    try:
        data = r.json()
    except Exception:
        print("RAW (not json):", r.text[:600])
        return

    node = data
    for k in ("response", "body", "items"):
        if isinstance(node, dict) and k in node:
            node = node[k]
    if isinstance(node, dict) and "item" in node:
        node = node["item"]
    if isinstance(node, list) and node:
        sample = node[0]
    elif isinstance(node, dict):
        sample = node
    else:
        print("no items")
        return

    print(f"[field keys, {len(sample)}]:")
    for k, v in sample.items():
        val = str(v)[:100].replace("\n", " ")
        print(f"  {k:22} = {val}")


def main():
    for name, (url, extra) in APIS.items():
        try:
            probe(name, url, extra)
        except Exception as e:
            print(f"\n=== {name} FAILED: {e}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
