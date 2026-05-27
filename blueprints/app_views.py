"""
RegHub 360 — 앱 페이지 Blueprint (MVP 6개 화면)
  /app/search              통합 검색
  /app/product/<code>      의약품 Product 360
  /app/product-food/<code> 식품 Product 360 (자리 표시자 + NO 1·153 부분)
  /app/timeline            통합 이벤트 타임라인 (회수+처분+안전성서한+공급)
  /app/copilot             AI 코파일럿

  ※ /app/(overview), /app/workspace, /app/watchlist, /app/reports
    Phase 2로 미루어 라우트 제거 (사이드바에서는 비활성 표시).
"""
import logging
from flask import Blueprint, render_template, request, redirect

from ..api_client import fetch_approval, fetch_disciplinary, fetch_recall, fetch_identification
from ..api_extras import (
    # 핵심 11
    fetch_drug_easy, fetch_drug_bundle, fetch_drug_safety_letter,
    fetch_drug_supply_stop, fetch_drug_supply_lack,
    fetch_drug_gmp, fetch_dur_item, fetch_dur_ingredient,
    fetch_food_nutrition,
    # 확장 R&D 8개
    fetch_drug_patent, fetch_drug_lawsuit, fetch_drug_fda_p4, fetch_drug_fda_orangebook,
    fetch_drug_clinical, fetch_drug_clinical_org, fetch_drug_reference, fetch_drug_bioeq,
    # 확장 품질·인증 3개
    fetch_drug_release, fetch_drug_entity_list, fetch_drug_dmf,
    # 확장 재심사·희귀 3개
    fetch_drug_review, fetch_drug_reeval, fetch_drug_orphan,
    # 확장 식품·건기식 2개
    fetch_food_inspect, fetch_hf_gmp,
)


def _client_filter(api_fn, fields, q, n=50, **kwargs):
    """fetch 함수 호출 + 클라이언트 사이드 필터링.
    검색 파라미터 미지원 API용. needle 이 fields 중 하나라도 포함되면 통과.
    """
    if not q:
        return []
    try:
        kwargs.setdefault("num_of_rows", n)
        r = api_fn(**kwargs)
        needle = q.lower()
        return [it for it in (r.get("items") or [])
                if any(needle in str(it.get(f, "")).lower() for f in fields)]
    except Exception as e:
        logger.warning(f"_client_filter {api_fn.__name__} 실패: {e}")
        return []


def _parallel_filter(jobs, max_workers=8):
    """여러 _client_filter 호출을 병렬 실행 — 응답 시간 단축.
    jobs: list of (label, api_fn, fields, q, n) tuples
    return: dict[label] = filtered_items
    """
    from concurrent.futures import ThreadPoolExecutor
    results = {}
    def _run(label, fn, fields, q, n):
        return label, _client_filter(fn, fields, q, n=n)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_run, *j) for j in jobs]
        for fut in futs:
            try:
                label, items = fut.result(timeout=20)
                results[label] = items
            except Exception as e:
                logger.warning(f"_parallel_filter 실패: {e}")
    return results


def _filter_items(items, q, fields):
    """클라이언트 사이드 필터링 — 응답에 검색 파라미터가 없을 때 사용.
    fields 리스트 중 하나라도 query 부분일치하면 통과."""
    if not q:
        return items
    needle = q.strip().lower()
    out = []
    for it in items:
        for f in fields:
            v = it.get(f)
            if v and needle in str(v).lower():
                out.append(it)
                break
    return out

logger = logging.getLogger(__name__)

app_bp = Blueprint("app", __name__, url_prefix="/app")


# ────────────────────────────────────────────────────────────────────────────
# Search (호환 리다이렉트 — / 가 메인이므로)
# ────────────────────────────────────────────────────────────────────────────

@app_bp.route("/")
def index():
    """앱 진입 — / 로 리다이렉트 (메인 검색 페이지)."""
    return redirect("/", code=302)


def _is_company(q: str) -> bool:
    """업체명 여부 휴리스틱."""
    if not q:
        return False
    return any(s in q for s in ("제약", "약품", "(주)", "주식회사", "Pharma", "광동", "동아", "한미", "유한", "제일"))


def _is_drug_name(q: str) -> bool:
    """의약품 제품명 여부 휴리스틱."""
    if not q:
        return False
    return any(suffix in q for suffix in ("정", "캡슐", "시럽", "주", "액", "연질", "환", "산제", "패치"))


@app_bp.route("/search")
def search():
    """
    통합 검색 화면 — q 파라미터가 있으면 실 API 호출 결과를 컨텍스트에 주입.
    템플릿은 search_results (없으면 디자인 mock 데이터 그대로 표시).
    """
    q = (request.args.get("q") or "").strip()
    ctx = {"query": q, "search_results": None, "active_page": "search"}

    if q:
        is_company = _is_company(q)
        is_drug = _is_drug_name(q)
        kind = "업체" if is_company else ("의약품" if is_drug else "제품")

        # 핵심 API 다중 호출 — NO 140 허가정보 + e약은요 + 회수 + 행정처분 + 안전성 + 공급 + 식품
        results = {"kind": kind}
        try:
            if is_company:
                results["approval"] = fetch_approval(entp_name=q, num_of_rows=10)
                results["drug_easy"] = fetch_drug_easy(entp_name=q, num_of_rows=6)
            else:
                results["approval"] = fetch_approval(item_name=q, num_of_rows=10)
                results["drug_easy"] = fetch_drug_easy(item_name=q, num_of_rows=6)
            # 회수·처분·안전성·공급·식품 = 검색 파라미터 미지원 → 충분히 큰 numOfRows로 받고 필터
            results["recall_raw"] = fetch_recall(num_of_rows=200)
            results["disc_raw"] = fetch_disciplinary(num_of_rows=200)
            results["safety"] = fetch_drug_safety_letter(num_of_rows=200)
            results["supply"] = fetch_drug_supply_stop(num_of_rows=200)
            results["food"] = fetch_food_nutrition(num_of_rows=200)
        except Exception as e:
            logger.error(f"search 데이터 수집 실패: {e}")

        # 회수·행정처분·안전성·공급·식품 모두 클라이언트 사이드 필터
        recalls_filtered = _filter_items(
            results.get("recall_raw", {}).get("items", []),
            q,
            fields=["PRDUCT", "ENTRPS", "ITEM_NAME", "ENTP_NAME"],
        )
        sanctions_filtered = _filter_items(
            results.get("disc_raw", {}).get("items", []),
            q,
            fields=["ENTP_NAME", "ITEM_NAME", "ENTRPS_NAME", "VIOLATION_DETAIL"],
        )
        safety_filtered = _filter_items(
            results.get("safety", {}).get("items", []),
            q,
            fields=["TITLE", "SUMMARY", "DETAIL_CN", "TBL_CN"],
        )
        supply_filtered = _filter_items(
            results.get("supply", {}).get("items", []),
            q,
            fields=["ENTP_NAME", "ITEM_NAME", "PRDUCT", "ENTRPS_NAME"],
        )
        food_filtered = _filter_items(
            results.get("food", {}).get("items", []),
            q,
            fields=["FOOD_NM_KR", "BSSH_NM", "MANUFACTURE"],
        )

        # 허가정보 = 가장 신뢰성 높은 제품 매칭 (NO 140)
        approval_items = results.get("approval", {}).get("items", [])

        # KPI 카운트 — 모두 정밀 필터링된 카운트
        counts = {
            "drug": results.get("approval", {}).get("totalCount", 0),
            "recall": len(recalls_filtered),
            "sanction": len(sanctions_filtered),
            "safety": len(safety_filtered),
            "supply": len(supply_filtered),
            "food": len(food_filtered),
        }

        # 표시용 products = 허가정보(우선) + e약은요(보조)
        products = approval_items[:6] if approval_items else \
                   results.get("drug_easy", {}).get("items", [])[:6]

        # top_products — 의약품 허가 결과 + Risk Score 정렬 (회수/처분 매칭 품목 우선)
        recalls_by_product = {}
        for r in recalls_filtered:
            key = (r.get("PRDUCT") or "").lower()
            if key:
                recalls_by_product[key] = recalls_by_product.get(key, 0) + 1
        sanctions_by_entity = {}
        for s in sanctions_filtered:
            key = (s.get("ENTP_NAME") or "").lower()
            if key:
                sanctions_by_entity[key] = sanctions_by_entity.get(key, 0) + 1

        scored_products = []
        for p in approval_items[:15]:
            name = (p.get("ITEM_NAME") or "").lower()
            entp = (p.get("ENTP_NAME") or "").lower()
            score = 0
            for k, v in recalls_by_product.items():
                if k and (k in name or name in k):
                    score += v * 40
            for k, v in sanctions_by_entity.items():
                if k and (k in entp or entp in k):
                    score += v * 30
            scored_products.append((score, p))
        scored_products.sort(key=lambda t: t[0], reverse=True)
        top_products = [
            {**p, "_risk": s, "_grade": "High" if s >= 60 else "Medium" if s >= 30 else "Low" if s > 0 else "Normal"}
            for s, p in scored_products[:6]
        ]

        # watch_events — 회수 + 처분 + 안전성서한 + 공급중단 통합 평면화 (시간순)
        watch_events = []
        for r in recalls_filtered[:8]:
            watch_events.append({
                "type": "회수",
                "severity": "HIGH",
                "title": (r.get("PRDUCT") or "(제품 미상)")[:50],
                "meta": (r.get("RTRVL_RESN") or "")[:60] + " · " + (r.get("ENTRPS") or ""),
                "date": (r.get("RECALL_COMMAND_DATE") or "")[:10],
                "api": "API 539",
            })
        for s in sanctions_filtered[:5]:
            watch_events.append({
                "type": "행정처분",
                "severity": "MED",
                "title": (s.get("ENTP_NAME") or "(업체 미상)")[:50],
                "meta": (s.get("VIOLATION_DETAIL") or s.get("VIOLATION_LAW") or "")[:60],
                "date": (s.get("DSPS_DCSNDT") or "")[:10],
                "api": "API 564",
            })
        for sl in (results.get("safety", {}).get("items", []) or [])[:3]:
            # 안전성서한 필터링 — 검색어 포함만
            title = sl.get("TITLE") or ""
            if q.lower() in title.lower() or q.lower() in (sl.get("SUMRY_CONT") or "").lower():
                watch_events.append({
                    "type": "안전성서한",
                    "severity": "MED",
                    "title": title[:50],
                    "meta": (sl.get("SUMRY_CONT") or "")[:60],
                    "date": (sl.get("PBANC_YMD") or "")[:10],
                    "api": "API 547",
                })
        watch_events.sort(key=lambda e: e["date"], reverse=True)

        # ────────────────────────────────────────────────────────────────────
        # 확장 17개 API — 클라이언트 사이드 필터링 (검색어 매칭만)
        # ────────────────────────────────────────────────────────────────────
        rnd_items = {"patent": [], "lawsuit": [], "fda_p4": [], "orangebook": [],
                     "clinical": [], "reference": [], "bioeq": []}
        quality_items = {"gmp": [], "shipment": [], "entity": [], "dmf": []}
        review_items = {"review": [], "reeval": [], "orphan": []}
        inspection_items = []
        hf_gmp_items = []

        if q:
            # 모든 확장 API 병렬 호출 — 응답 시간 30초+ → 5~8초로 단축
            jobs = [
                ("rnd_patent",     fetch_drug_patent,        ["ITEM_NAME", "INGR_NAME", "ENTP_NAME"], q, 50),
                ("rnd_lawsuit",    fetch_drug_lawsuit,       ["PRT_NAME", "INGR_NAME"],             q, 30),
                ("rnd_fda_p4",     fetch_drug_fda_p4,        ["DRUG_NAME", "RLD"],                  q, 30),
                ("rnd_orangebook", fetch_drug_fda_orangebook,["PRT_NAME", "INGR_NAME"],             q, 30),
                ("rnd_clinical",   fetch_drug_clinical,      ["GOODS_NAME", "APPLY_ENTP_NAME", "CLINIC_EXAM_TITLE"], q, 50),
                ("rnd_reference",  fetch_drug_reference,     ["ITEM_NAME", "INGR_NAME", "ENTP_NAME"], q, 30),
                ("rnd_bioeq",      fetch_drug_bioeq,         ["ITEM_NAME", "INGR_KOR_NAME", "ENTP_NAME"], q, 30),
                ("q_shipment",     fetch_drug_release,       ["MANUF_ENTP_NAME", "GOODS_NAME"],     q, 30),
                ("q_entity",       fetch_drug_entity_list,   ["ENTRPS", "RPRSNTV"],                 q, 30),
                ("q_dmf",          fetch_drug_dmf,           ["ENTP_NAME", "MNFCTR_NAME", "INGR_KOR_NAME"], q, 30),
                ("rv_review",      fetch_drug_review,        ["ENTP_NAME", "ITEM_NAME"],            q, 30),
                ("rv_reeval",      fetch_drug_reeval,        ["ENTP_NAME", "ITEM_NAME"],            q, 30),
                ("rv_orphan",      fetch_drug_orphan,        ["PRDT_NAME", "PRODT_NAME", "TARGET_DISEASE"], q, 30),
                ("inspection",     fetch_food_inspect,       ["PRDUCT", "ENTRPS", "IMPROPT_ITM"],   q, 30),
                ("hf_gmp",         fetch_hf_gmp,             ["BSSH_NM", "PRSDNT_NM"],              q, 20),
            ]
            par = _parallel_filter(jobs, max_workers=10)
            # 결과 분배
            rnd_items["patent"]     = par.get("rnd_patent", [])
            rnd_items["lawsuit"]    = par.get("rnd_lawsuit", [])
            rnd_items["fda_p4"]     = par.get("rnd_fda_p4", [])
            rnd_items["orangebook"] = par.get("rnd_orangebook", [])
            rnd_items["clinical"]   = par.get("rnd_clinical", [])
            rnd_items["reference"]  = par.get("rnd_reference", [])
            rnd_items["bioeq"]      = par.get("rnd_bioeq", [])
            quality_items["shipment"] = par.get("q_shipment", [])
            quality_items["entity"]   = par.get("q_entity", [])
            quality_items["dmf"]      = par.get("q_dmf", [])
            review_items["review"] = par.get("rv_review", [])
            review_items["reeval"] = par.get("rv_reeval", [])
            review_items["orphan"] = par.get("rv_orphan", [])
            inspection_items = par.get("inspection", [])
            hf_gmp_items = par.get("hf_gmp", [])

        # 합계 카운트
        rnd_total = sum(len(v) for v in rnd_items.values())
        quality_total = sum(len(v) for v in quality_items.values())
        review_total = sum(len(v) for v in review_items.values())

        # 확장 카운트 통합
        counts.update({
            "rnd_total": rnd_total,
            "rnd": {k: len(v) for k, v in rnd_items.items()},
            "quality_total": quality_total,
            "quality": {k: len(v) for k, v in quality_items.items()},
            "review_total": review_total,
            "review": {k: len(v) for k, v in review_items.items()},
            "inspection": len(inspection_items),
            "hf_gmp": len(hf_gmp_items),
        })

        ctx["search_results"] = {
            "kind": kind,
            "counts": counts,
            "api_count": 28,  # 11 핵심 + 17 확장
            "products": products,
            "top_products": top_products,
            "watch_events": watch_events[:6],
            "recalls": recalls_filtered[:3],
            "sanctions": sanctions_filtered[:3],
            # 확장 신규 카드 데이터
            "rnd_items": rnd_items,
            "quality_items": quality_items,
            "review_items": review_items,
            "inspection_items": inspection_items[:3],
            "hf_gmp_items": hf_gmp_items[:3],
        }

    return render_template("app/search.html", **ctx)


# ────────────────────────────────────────────────────────────────────────────
# Product 360 (의약품 / 식품 / 향후 의약외품·건강기능식품)
# ────────────────────────────────────────────────────────────────────────────

@app_bp.route("/product/<code>")
def product_drug(code):
    """
    의약품 Product 360 — 8개 탭.
    NO 140(허가) + 248(e약은요) + 563(낱알식별) + 539(회수) + 547(안전성서한)
    + 269(묶음의약품/HIRA·ATC) + 531(DUR 품목) + 534(공급중단) 실 데이터 주입.
    """
    product = None
    drug_easy = None
    identification = None
    related_recalls = []
    safety_letters = []
    bundle = None
    dur_items = []
    supply_stops = []
    ingredient_kr = None  # 한글 주성분명
    # 확장 R&D / 품질 / 재심사 데이터
    p_patents = []
    p_lawsuits = []
    p_fda_p4 = []
    p_orangebook = []
    p_clinical = []
    p_reference = []
    p_bioeq = []
    p_release = []
    p_dmf = []
    p_review = []
    p_reeval = []
    p_orphan = []

    try:
        # 1. NO 140 의약품 허가정보 — code 는 edi_code(보험코드) / item_name 순서로 시도
        # ※ item_seq 파라미터는 NO 140에서 작동하지 않음 (전수 검증 완료)
        ap = fetch_approval(edi_code=code, num_of_rows=1)
        if ap.get("totalCount", 0) == 0 or len(ap.get("items", [])) == 0:
            # edi_code 매칭 실패 → item_name 매칭 시도
            ap = fetch_approval(item_name=code, num_of_rows=1)
        items = ap.get("items", [])
        if items:
            product = items[0]
            item_name = product.get("ITEM_NAME") or ""
            entp_name = product.get("ENTP_NAME") or ""
            ingr_name = product.get("ITEM_INGR_NAME") or ""

            # 2. NO 248 e약은요 — itemSeq 카멜케이스 (작동 확인)
            try:
                ed = fetch_drug_easy(item_seq=code, num_of_rows=1)
                if ed.get("items"):
                    drug_easy = ed["items"][0]
            except Exception:
                pass

            # 3. NO 563 낱알식별 — item_name (검증된 파라미터)
            try:
                idr = fetch_identification(item_name=item_name.split('(')[0], num_of_rows=1)
                if idr.get("items"):
                    identification = idr["items"][0]
            except Exception:
                pass

            # 3-1. 한글 주성분명 추출 — ITEM_NAME 안 괄호 내용 우선 사용
            #   "베니톨정(미세정제플라보노이드분획물)" → "미세정제플라보노이드분획물"
            import re as _re
            m_ingr = _re.search(r'\(([^()]+)\)', item_name or '')
            if m_ingr:
                ingredient_kr = m_ingr.group(1).strip()

            # 4. NO 539 회수 — 파라미터 무시되므로 클라이언트 필터
            try:
                rr = fetch_recall(num_of_rows=200)
                needle_n = item_name.split('(')[0].lower() if item_name else ""
                needle_e = entp_name.lower()
                related_recalls = [
                    it for it in rr.get("items", [])
                    if (needle_n and needle_n in str(it.get("PRDUCT", "")).lower())
                    or (needle_e and needle_e in str(it.get("ENTRPS", "")).lower())
                ][:5]
            except Exception:
                pass

            # 5. NO 547 안전성서한 — TITLE (대문자) 검증 완료
            try:
                sl = fetch_drug_safety_letter(title=item_name.split('(')[0], num_of_rows=3)
                safety_letters = sl.get("items", [])
            except Exception:
                pass

            # 6. NO 269 묶음의약품 — trustItemName 검증 완료
            try:
                bd = fetch_drug_bundle(item_name=item_name.split('(')[0], num_of_rows=1)
                if bd.get("items"):
                    bundle = bd["items"][0]
            except Exception:
                pass

            # 7. NO 531 DUR 품목 (병용금기) — itemName 카멜케이스 검증
            try:
                from ..api_extras import fetch_dur_item
                du = fetch_dur_item(category="combine", item_name=item_name.split('(')[0], num_of_rows=3)
                dur_items = du.get("items", [])
            except Exception:
                pass

            # 8. NO 534 공급중단 — 클라이언트 필터
            try:
                ss = fetch_drug_supply_stop(num_of_rows=200)
                supply_stops = [
                    it for it in ss.get("items", [])
                    if (item_name.split('(')[0].lower() in str(it.get("ITEM_NAME", "")).lower())
                    or (entp_name.lower() in str(it.get("ENTP_NAME", "")).lower())
                ][:3]
            except Exception:
                pass

            # ────────────────────────────────────────────────────────────
            # 확장 R&D / 품질 / 재심사 — 제품명/성분명 기반 클라이언트 필터링
            # ────────────────────────────────────────────────────────────
            name_short = item_name.split('(')[0]
            try:
                p_patents = _client_filter(
                    fetch_drug_patent, ["ITEM_NAME", "INGR_NAME", "ENTP_NAME"], name_short, n=50
                )[:5]
            except Exception: pass
            try:
                p_lawsuits = _client_filter(
                    fetch_drug_lawsuit, ["PRT_NAME", "INGR_NAME"], name_short, n=30
                )[:3]
            except Exception: pass
            try:
                if ingredient_kr or product.get("ITEM_INGR_NAME"):
                    ingr_q = ingredient_kr or product.get("ITEM_INGR_NAME", "")
                    p_fda_p4 = _client_filter(
                        fetch_drug_fda_p4, ["DRUG_NAME"], ingr_q.split()[0] if ingr_q else "", n=30
                    )[:3]
                    p_orangebook = _client_filter(
                        fetch_drug_fda_orangebook, ["INGR_NAME", "PRT_NAME"], ingr_q.split()[0] if ingr_q else "", n=30
                    )[:3]
            except Exception: pass
            try:
                p_clinical = _client_filter(
                    fetch_drug_clinical, ["GOODS_NAME", "APPLY_ENTP_NAME"], name_short, n=50
                )[:5]
            except Exception: pass
            try:
                p_reference = _client_filter(
                    fetch_drug_reference, ["ITEM_NAME", "INGR_NAME", "ENTP_NAME"], name_short, n=30
                )[:3]
            except Exception: pass
            try:
                p_bioeq = _client_filter(
                    fetch_drug_bioeq, ["ITEM_NAME", "INGR_KOR_NAME", "ENTP_NAME"], name_short, n=30
                )[:3]
            except Exception: pass
            try:
                p_release = _client_filter(
                    fetch_drug_release, ["GOODS_NAME", "MANUF_ENTP_NAME"], name_short, n=30
                )[:3]
            except Exception: pass
            try:
                p_dmf = _client_filter(
                    fetch_drug_dmf, ["INGR_KOR_NAME", "ENTP_NAME", "MNFCTR_NAME"],
                    ingredient_kr or entp_name, n=30
                )[:3]
            except Exception: pass
            try:
                p_review = _client_filter(
                    fetch_drug_review, ["ITEM_NAME", "ENTP_NAME"], name_short, n=30
                )[:3]
            except Exception: pass
            try:
                p_reeval = _client_filter(
                    fetch_drug_reeval, ["ITEM_NAME", "ENTP_NAME"], name_short, n=30
                )[:3]
            except Exception: pass
            try:
                p_orphan = _client_filter(
                    fetch_drug_orphan, ["PRDT_NAME", "PRODT_NAME"], name_short, n=30
                )[:3]
            except Exception: pass
    except Exception as e:
        logger.warning(f"Product 360 데이터 수집 실패 (code={code}): {e}")

    return render_template(
        "app/product_drug.html",
        active_page="search",
        product_code=code,
        product_live=product,
        drug_easy=drug_easy,
        identification=identification,
        related_recalls=related_recalls,
        safety_letters=safety_letters,
        bundle=bundle,
        dur_items=dur_items,
        supply_stops=supply_stops,
        ingredient_kr=ingredient_kr,
        # 확장 R&D / 품질 / 재심사
        p_patents=p_patents,
        p_lawsuits=p_lawsuits,
        p_fda_p4=p_fda_p4,
        p_orangebook=p_orangebook,
        p_clinical=p_clinical,
        p_reference=p_reference,
        p_bioeq=p_bioeq,
        p_release=p_release,
        p_dmf=p_dmf,
        p_review=p_review,
        p_reeval=p_reeval,
        p_orphan=p_orphan,
    )


@app_bp.route("/product-food/<code>")
def product_food(code):
    """식품 Product 360 — 자리 표시자 (식품 API 5개 명세 대기)."""
    food_nutrition = None
    food_recall_import = None
    try:
        from ..api_extras import fetch_food_nutrition, fetch_food_recall_import
        # NO 1 영양 DB 검색
        nutri_r = fetch_food_nutrition(food_name=code, num_of_rows=1)
        if nutri_r.get("items"):
            food_nutrition = nutri_r["items"][0]
        # NO 153 수입식품 회수
        recall_r = fetch_food_recall_import(product_name=code, num_of_rows=1)
        if recall_r.get("items"):
            food_recall_import = recall_r["items"][0]
    except Exception as e:
        logger.warning(f"Product-food 데이터 수집 실패: {e}")

    return render_template(
        "app/product_food.html",
        active_page="search",
        product_code=code,
        food_nutrition=food_nutrition,
        food_recall_import=food_recall_import,
    )


# ────────────────────────────────────────────────────────────────────────────
# 통합 기능 페이지 (MVP 유지: timeline · copilot)
# ────────────────────────────────────────────────────────────────────────────

@app_bp.route("/timeline")
def timeline():
    """통합 이벤트 타임라인 — 회수+처분+안전성서한+공급중단 통합 평면화."""
    events = []
    try:
        # 회수 (NO 539)
        rr = fetch_recall(num_of_rows=30)
        for r in rr.get("items", [])[:15]:
            events.append({
                "type": "recall",
                "type_kr": "회수·판매중지",
                "severity": "HIGH",
                "domain": "drug",
                "domain_kr": "의약품",
                "title": (r.get("PRDUCT") or "(제품 미상)")[:60],
                "summary": (r.get("RTRVL_RESN") or "")[:100],
                "entity": r.get("ENTRPS") or "",
                "date": (r.get("RECALL_COMMAND_DATE") or r.get("ENFRC_YN") or "")[:10],
                "api": "API 539",
                "url": "https://www.data.go.kr/data/15059114/openapi.do",
            })
    except Exception as e:
        logger.warning(f"timeline recall 수집 실패: {e}")
    try:
        # 행정처분 (NO 564)
        dr = fetch_disciplinary(num_of_rows=20)
        for d in dr.get("items", [])[:10]:
            events.append({
                "type": "disciplinary",
                "type_kr": "행정처분",
                "severity": "MED",
                "domain": "drug",
                "domain_kr": "의약품",
                "title": (d.get("ENTP_NAME") or "(업체 미상)")[:60],
                "summary": (d.get("VIOLATION_DETAIL") or d.get("VIOLATION_LAW") or "")[:100],
                "entity": d.get("ENTP_NAME") or "",
                "date": (d.get("DSPS_DCSNDT") or "")[:10],
                "api": "API 564",
                "url": "https://www.data.go.kr/data/15058457/openapi.do",
            })
    except Exception as e:
        logger.warning(f"timeline disc 수집 실패: {e}")
    try:
        # 안전성서한 (NO 547)
        sl = fetch_drug_safety_letter(num_of_rows=15)
        for s in sl.get("items", [])[:8]:
            events.append({
                "type": "safety_letter",
                "type_kr": "안전성서한",
                "severity": "MED",
                "domain": "drug",
                "domain_kr": "의약품",
                "title": (s.get("TITLE") or "")[:60],
                "summary": (s.get("SUMRY_CONT") or "")[:100],
                "entity": s.get("PBANC_DIVS_NM") or "",
                "date": (s.get("PBANC_YMD") or "")[:10],
                "api": "API 547",
                "url": "https://www.data.go.kr/data/15059182/openapi.do",
            })
    except Exception as e:
        logger.warning(f"timeline safety 수집 실패: {e}")
    try:
        # 공급중단 (NO 534)
        ss = fetch_drug_supply_stop(num_of_rows=10)
        for s in ss.get("items", [])[:5]:
            events.append({
                "type": "supply_stop",
                "type_kr": "공급중단",
                "severity": "HIGH",
                "domain": "drug",
                "domain_kr": "의약품",
                "title": (s.get("ITEM_NAME") or "(품목 미상)")[:60],
                "summary": (s.get("REPORT_PGS_CODE") or "") + " · " + (s.get("SUSPEND_REPORT_FLAG") or ""),
                "entity": s.get("ENTP_NAME") or "",
                "date": "",  # 응답에 날짜 필드명 불명확
                "api": "API 534",
                "url": "https://www.data.go.kr/data/15057899/openapi.do",
            })
    except Exception as e:
        logger.warning(f"timeline supply 수집 실패: {e}")
    try:
        # 검사부적합 (NO 535)
        from ..api_extras import fetch_food_inspect
        fi = fetch_food_inspect(num_of_rows=15)
        for item in fi.get("items", [])[:8]:
            events.append({
                "type": "inspection_fail",
                "type_kr": "검사부적합",
                "severity": "MED",
                "domain": "food",
                "domain_kr": "식품",
                "title": (item.get("PRDUCT") or "(품목 미상)")[:60],
                "summary": (item.get("IMPROPT_ITM") or "")[:100],
                "entity": item.get("ENTRPS") or "",
                "date": (item.get("REGIST_DT") or "")[:10],
                "api": "API 535",
                "url": "https://www.data.go.kr/data/15056516/openapi.do",
            })
    except Exception as e:
        logger.warning(f"timeline inspection 수집 실패: {e}")
    try:
        # 신규 허가 (NO 140) — 최신 등재 의약품 5건
        ap = fetch_approval(num_of_rows=5)
        for item in ap.get("items", [])[:5]:
            events.append({
                "type": "permit_new",
                "type_kr": "신규 허가",
                "severity": "LOW",
                "domain": "drug",
                "domain_kr": "의약품",
                "title": (item.get("ITEM_NAME") or "(품목 미상)")[:60],
                "summary": (item.get("SPCLTY_PBLC") or "") + " · " + (item.get("PRDUCT_TYPE") or ""),
                "entity": item.get("ENTP_NAME") or "",
                "date": (item.get("ITEM_PERMIT_DATE") or "")[:8],
                "api": "API 140",
                "url": "https://www.data.go.kr/data/15095677/openapi.do",
            })
    except Exception as e:
        logger.warning(f"timeline permit_new 수집 실패: {e}")

    # 시간순 정렬
    events.sort(key=lambda e: e["date"], reverse=True)

    # severity 카운트
    severity_counts = {
        "high": sum(1 for e in events if e["severity"] == "HIGH"),
        "med": sum(1 for e in events if e["severity"] == "MED"),
        "low": sum(1 for e in events if e["severity"] == "LOW"),
    }
    type_counts = {}
    for e in events:
        type_counts[e["type"]] = type_counts.get(e["type"], 0) + 1

    return render_template(
        "app/timeline.html",
        active_page="timeline",
        events=events[:30],
        total_count=len(events),
        severity_counts=severity_counts,
        type_counts=type_counts,
    )


@app_bp.route("/copilot")
def copilot():
    """AI 코파일럿 — MISO drug_consult_agent 프록시."""
    return render_template("app/copilot.html", active_page="copilot")


# ────────────────────────────────────────────────────────────────────────────
# 워치리스트 — 사용자 등록 항목 (JSON 영속화)
# ────────────────────────────────────────────────────────────────────────────

@app_bp.route("/watchlist")
def watchlist():
    """워치리스트 페이지 — 등록 항목 목록 + 식약처 이벤트 매칭."""
    from . import watchlist_store
    from . import watchlist_match
    entries = watchlist_store.list_entries()
    # 항목별 식약처 이벤트 매칭 (캐시 5분 TTL — 같은 페이지 새로고침 시 API 재호출 안 함)
    matches = watchlist_match.match_for_entries(entries)
    alert_total = watchlist_match.total_alert_count(matches)
    return render_template(
        "app/watchlist.html",
        active_page="watchlist",
        entries=entries,
        matches=matches,
        alert_total=alert_total,
        flash_msg=request.args.get("msg") or "",
    )


@app_bp.route("/watchlist/add", methods=["POST"])
def watchlist_add():
    """워치리스트 항목 추가."""
    from . import watchlist_store
    query = (request.form.get("query") or "").strip()
    label = (request.form.get("label") or "").strip() or query
    kind = (request.form.get("kind") or "product").strip()
    note = (request.form.get("note") or "").strip()
    redirect_to = request.form.get("next") or "/app/watchlist"
    if not query:
        return redirect(redirect_to + ("?msg=쿼리를_입력하세요" if "?" not in redirect_to else "&msg=쿼리를_입력하세요"))
    watchlist_store.add_entry(query=query, label=label, kind=kind, note=note)
    sep = "&" if "?" in redirect_to else "?"
    return redirect(f"{redirect_to}{sep}msg=추가됨")


@app_bp.route("/watchlist/<entry_id>/delete", methods=["POST"])
def watchlist_delete(entry_id):
    """워치리스트 항목 삭제."""
    from . import watchlist_store
    watchlist_store.delete_entry(entry_id)
    return redirect("/app/watchlist?msg=삭제됨")


# ────────────────────────────────────────────────────────────────────────────
# 리포트 — 사전 정의 리포트 카탈로그
# ────────────────────────────────────────────────────────────────────────────

# 카드 그리드에 표시할 사전 정의 리포트 5개.
# 실제 PDF/Excel 다운로드는 Phase 2.5 — 현재는 카드 클릭 시 안내 페이지로 폴백.
_REPORT_CATALOG = [
    {
        "id": "monthly-recall",
        "title": "월간 회수·판매중지 동향",
        "summary": "지난 30일간 식약처 NO 539 회수 데이터를 도메인·사유별로 집계. 자사 영향 가능성 라벨 포함.",
        "kind": "회수",
        "kind_class": "danger",
        "cadence": "월간",
        "last_updated": "2026-05-25",
        "pages": 12,
        "data_sources": ["NO 539", "NO 547"],
    },
    {
        "id": "quarterly-rnd",
        "title": "분기 R&D 인사이트",
        "summary": "특허·임상시험·대조약·생동성 7개 API 매칭 결과를 성분군별로 정리. 경쟁사 파이프라인 변동 포함.",
        "kind": "R&D",
        "kind_class": "brand",
        "cadence": "분기",
        "last_updated": "2026-04-30",
        "pages": 28,
        "data_sources": ["NO 561", "NO 566", "NO 484", "NO 485", "NO 552", "NO 562", "NO 557"],
    },
    {
        "id": "company-safety",
        "title": "자사 안전성 이벤트 요약",
        "summary": "광동제약 자사 품목에 대한 안전성서한·DUR·회수·공급중단 통합 타임라인. RA·QA 공유용.",
        "kind": "안전성",
        "kind_class": "warn",
        "cadence": "주간",
        "last_updated": "2026-05-26",
        "pages": 8,
        "data_sources": ["NO 547", "NO 531", "NO 539", "NO 534"],
    },
    {
        "id": "gmp-status",
        "title": "GMP · 심사 상태 리포트",
        "summary": "자사 제조소 GMP 적합판정·재심사·재평가·DMF 일정과 만료 위험 품목. 매월 1일 갱신.",
        "kind": "품질",
        "kind_class": "ok",
        "cadence": "월간",
        "last_updated": "2026-05-01",
        "pages": 6,
        "data_sources": ["NO 132", "NO 142", "NO 483", "NO 554", "NO 556"],
    },
    {
        "id": "competitor-sanction",
        "title": "경쟁사 행정처분 동향",
        "summary": "한미·동아·유한·제일 등 주요 경쟁사 행정처분(NO 564) 90일 추적. 영업 인사이트 카드 포함.",
        "kind": "행정처분",
        "kind_class": "warn",
        "cadence": "분기",
        "last_updated": "2026-05-20",
        "pages": 14,
        "data_sources": ["NO 564", "NO 539"],
    },
]


@app_bp.route("/reports")
def reports():
    """리포트 카탈로그 페이지."""
    return render_template(
        "app/reports.html",
        active_page="reports",
        reports=_REPORT_CATALOG,
    )
