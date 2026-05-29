"""
KD-IRIS — SAP / EDMS 연동 인터페이스 (Phase M-4 스텁)

⚠️ 이번 범위는 **진입점(인터페이스) 정의만**. 실제 연동 코드·인증은 작성하지 않음.
APQR 8~12번 섹션이 이 함수들을 호출하되, 빈 결과면 "연동 대기"로 표시한다.
향후 실연동 시 이 함수 본문만 채우면 APQR 대기 섹션이 자동 활성화된다.
"""
import logging
from typing import Dict, List

from . import db as qadb

logger = logging.getLogger(__name__)


def fetch_sap_batches(item_seq: str, year: int) -> List[Dict]:
    """[SAP 연동 예정] 제조번호·제조/시험 결과 조회.
    현재는 product_batch 테이블(빈 상태)을 반환. TODO: SAP RFC/OData 연동."""
    try:
        return qadb.query(
            "SELECT lot_no, mfg_date, test_result, oos_yn FROM product_batch WHERE item_seq=?",
            (item_seq,))
    except Exception:
        return []


def fetch_edms_documents(item_seq: str, doc_types: List[str]) -> List[Dict]:
    """[EDMS 연동 예정] 제품표준서·일탈·CAPA·변경관리 문서 조회.
    현재는 product_document 테이블(빈 상태)을 반환. TODO: EDMS API 연동."""
    try:
        return qadb.query(
            "SELECT doc_type, doc_no, title FROM product_document WHERE item_seq=?",
            (item_seq,))
    except Exception:
        return []


def integration_status() -> Dict[str, str]:
    """연동 상태 요약 (대시보드/APQR 안내용)."""
    return {"SAP": "연동 대기 (인터페이스 준비됨)", "EDMS": "연동 대기 (인터페이스 준비됨)",
            "LIMS": "연동 대기 (Phase M-4 이후)"}
