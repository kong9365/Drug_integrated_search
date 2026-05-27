"""Validation script for MISO DSL workflow YAMLs. Not part of MISO runtime."""
import glob
import re
import sys

import yaml

EXPECTED_ENDPOINTS = {
    "DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07",
    "MdcinExaathrService04/getMdcinExaathrList04",
    "MdcinRtrvlSleStpgeInfoService04/getMdcinRtrvlSleStpgeItem03",
    "MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03",
}


def _validate_agent_chat(f: str, data: dict) -> bool:
    """Validate agent-chat app (model_config based, no workflow graph)."""
    mc = data.get("model_config")
    if not isinstance(mc, dict):
        print(f"[AGENT FAIL] {f}: model_config 없음")
        return False
    agent_mode = mc.get("agent_mode", {})
    if not agent_mode.get("enabled"):
        print(f"[AGENT FAIL] {f}: agent_mode.enabled != true")
        return False
    tools = agent_mode.get("tools", [])
    pre_prompt = mc.get("pre_prompt", "")
    print(
        f"[OK agent-chat] {f}: tools={len(tools)}, "
        f"pre_prompt_chars={len(pre_prompt)}"
    )
    return True


def main() -> int:
    files = sorted(glob.glob("drug_integrated_search/miso_workflows/*.yml"))
    all_ok = True
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        mode = data.get("app", {}).get("mode", "")
        if mode == "agent-chat":
            if not _validate_agent_chat(f, data):
                all_ok = False
            continue
        wf = data["workflow"]
        nodes = wf["graph"]["nodes"]
        edges = wf["graph"]["edges"]
        node_ids = {n["id"] for n in nodes}

        bad_edges = [
            e for e in edges
            if e["source"] not in node_ids or e["target"] not in node_ids
        ]
        if bad_edges:
            all_ok = False
            pairs = [(e["source"], e["target"]) for e in bad_edges]
            print(f"[EDGE FAIL] {f}: {pairs}")

        env_names = {e["name"] for e in wf["environment_variables"]}
        if env_names != {"DATA_GO_KR_BASE", "SERVICE_KEY"}:
            all_ok = False
            print(f"[ENV FAIL] {f}: {env_names}")

        urls = [
            n["data"].get("url", "")
            for n in nodes
            if n["data"].get("type") == "http-request"
        ]
        for u in urls:
            m = re.search(r"1471000/([^?{}\s]+)", u)
            if m and m.group(1) not in EXPECTED_ENDPOINTS:
                all_ok = False
                print(f"[URL FAIL] {f}: {m.group(1)}")

        refd = set()
        for e in edges:
            refd.add(e["source"])
            refd.add(e["target"])
        unused = node_ids - refd
        if unused:
            print(f"[WARN unused nodes] {f}: {unused}")

        print(
            f"[OK integrity] {f}: nodes={len(nodes)}, "
            f"edges={len(edges)}, http_urls={len(urls)}"
        )

    print()
    print("ALL OK" if all_ok else "FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
