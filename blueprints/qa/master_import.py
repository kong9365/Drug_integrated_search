"""
KD-IRIS 1차 빌드 — 자사 품목 마스터 import (기능재설계 v2 §11.4)

C:\\Temp 의 품목 마스터 xlsx → SQLite master_item.
- 2단 헤더(1행=밴드, 2행=컬럼명, 데이터 3행~)
- 완제품 필터: 품목구분 ∈ {포장제품, 제조제품, 의약외품, 상품} AND 사용여부 ≠ 사용중지
- item_code PK UPSERT (멱등)
- 한약(생약) 추정 플래그 (품목명/품목분류 키워드)

CLI: python -m drug_integrated_search.blueprints.qa.master_import
"""
import logging
from typing import Dict, List, Optional

from ...config import MASTER_XLSX_PATH
from . import db as qadb

logger = logging.getLogger(__name__)

# 완제품으로 간주할 품목구분
FINISHED_GUBUN = {"포장제품", "제조제품", "의약외품", "상품"}

# 한약(생약) 추정 키워드 — 품목명/품목분류에 포함되면 is_herbal=1
HERBAL_KEYWORDS = (
    "탕", "환", "산", "생약", "한약", "쌍화", "우황", "청심", "보골", "공진",
    "경옥", "십전", "위령선", "갈근", "당귀", "인삼", "홍삼", "감초",
)

# xlsx 2행 컬럼명 → master_item 컬럼 매핑 (검증된 헤더 기준)
COL_MAP = {
    "품목코드": "item_code",
    "품목명": "item_name",
    "품목명2": "item_name_alt",
    "전문분류": "category",
    "품목분류": "sub_category",
    "품목구분": "gubun",
    "포장규격": "pack_spec",
    "배치사이즈": "batch_size",
    "위탁처": "consign_maker",
    "자사/위탁": "self_or_consign",
}


def _norm(v) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s and s not in ("None", "nan") else None


def _to_int(v) -> Optional[int]:
    s = _norm(v)
    if not s:
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def _is_herbal(item_name: str, sub_category: str) -> int:
    blob = f"{item_name or ''} {sub_category or ''}"
    return 1 if any(k in blob for k in HERBAL_KEYWORDS) else 0


def load_rows(xlsx_path: str = None) -> List[Dict]:
    """xlsx → 완제품 dict 리스트 (필터 적용)."""
    import openpyxl
    path = xlsx_path or MASTER_XLSX_PATH
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    allrows = list(ws.iter_rows(values_only=True))
    wb.close()
    if len(allrows) < 3:
        logger.error(f"마스터 xlsx 행 부족: {len(allrows)}")
        return []

    # 2행(index 1)이 실제 컬럼명
    headers = [str(c) if c is not None else "" for c in allrows[1]]
    idx = {h: i for i, h in enumerate(headers)}

    def cell(row, colname):
        i = idx.get(colname)
        return row[i] if (i is not None and i < len(row)) else None

    out = []
    for row in allrows[2:]:
        gubun = _norm(cell(row, "품목구분"))
        item_code = _norm(cell(row, "품목코드"))
        item_name = _norm(cell(row, "품목명"))
        use_yn = _norm(cell(row, "사용여부"))
        # 필터: 완제품 + 코드/명 존재 + 사용중지 아님
        if not item_code or not item_name:
            continue
        if gubun not in FINISHED_GUBUN:
            continue
        if use_yn and ("중지" in use_yn or "Unchecked" in use_yn):
            continue
        sub_cat = _norm(cell(row, "품목분류"))
        rec = {
            "item_code": item_code,
            "item_name": item_name,
            "item_name_alt": _norm(cell(row, "품목명2")),
            "category": _norm(cell(row, "전문분류")),
            "sub_category": sub_cat,
            "gubun": gubun,
            "shelf_life_mo": _to_int(cell(row, "유효기간")),
            "pack_spec": _norm(cell(row, "포장규격")),
            "batch_size": _norm(cell(row, "배치사이즈")),
            "consign_maker": _norm(cell(row, "위탁처")),
            "self_or_consign": _norm(cell(row, "자사/위탁")),
            "is_herbal": _is_herbal(item_name, sub_cat),
            "active": 1,
        }
        out.append(rec)
    return out


_UPSERT = """
INSERT INTO master_item
  (item_code, item_name, item_name_alt, category, sub_category, gubun,
   shelf_life_mo, pack_spec, batch_size, consign_maker, self_or_consign,
   is_herbal, active, enrich_status)
VALUES
  (:item_code, :item_name, :item_name_alt, :category, :sub_category, :gubun,
   :shelf_life_mo, :pack_spec, :batch_size, :consign_maker, :self_or_consign,
   :is_herbal, :active, 'pending')
ON CONFLICT(item_code) DO UPDATE SET
  item_name=excluded.item_name, item_name_alt=excluded.item_name_alt,
  category=excluded.category, sub_category=excluded.sub_category,
  gubun=excluded.gubun, shelf_life_mo=excluded.shelf_life_mo,
  pack_spec=excluded.pack_spec, batch_size=excluded.batch_size,
  consign_maker=excluded.consign_maker, self_or_consign=excluded.self_or_consign,
  is_herbal=excluded.is_herbal, active=excluded.active
"""


def import_master(xlsx_path: str = None) -> Dict:
    """xlsx 적재 → master_item UPSERT. 통계 dict 반환."""
    qadb.init_db()
    rows = load_rows(xlsx_path)
    if not rows:
        return {"imported": 0, "error": "행 없음 또는 파일 오류"}

    conn = qadb.get_conn()
    try:
        conn.executemany(_UPSERT, rows)
        conn.commit()
    finally:
        conn.close()

    # 통계
    herbal = sum(r["is_herbal"] for r in rows)
    by_gubun: Dict[str, int] = {}
    by_cat: Dict[str, int] = {}
    for r in rows:
        by_gubun[r["gubun"]] = by_gubun.get(r["gubun"], 0) + 1
        c = r["category"] or "(미분류)"
        by_cat[c] = by_cat.get(c, 0) + 1

    stats = {
        "imported": len(rows),
        "herbal_est": herbal,
        "non_herbal": len(rows) - herbal,
        "by_gubun": by_gubun,
        "by_category": by_cat,
    }
    logger.info(f"마스터 import 완료: {stats}")
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    import sys
    s = import_master()
    print("=" * 50)
    print(f"적재: {s.get('imported')}건 (한약추정 {s.get('herbal_est')} / 비한약 {s.get('non_herbal')})")
    print(f"품목구분: {s.get('by_gubun')}")
    print(f"전문분류: {s.get('by_category')}")
