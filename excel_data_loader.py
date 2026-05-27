"""
의약품 통합 조회 시스템 - 엑셀 데이터 로더
의약품안전나라에서 제공하는 엑셀 파일을 다운로드하고 파싱하는 모듈
"""
import logging
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import urllib3

from .config import BASE_DIR, VERIFY_SSL

# SSL 경고 비활성화
if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# 엑셀 파일 다운로드 URL
EXCEL_DOWNLOAD_URL = "https://nedrug.mfds.go.kr/cmn/xls/down/OpenData_ItemPermitDetail"

# 캐시 디렉토리
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)
EXCEL_CACHE_FILE = CACHE_DIR / "approval_data.xlsx"
CACHE_METADATA_FILE = CACHE_DIR / "cache_metadata.json"

# 캐시 유효기간 (24시간 = 1일)
# 엑셀 파일은 매일 04:00 AM에 업데이트되므로 1일 1회 다운로드
CACHE_VALID_HOURS = 24


def download_excel_file(force_download: bool = False) -> Path:
    """
    엑셀 파일 다운로드
    
    Args:
        force_download: 강제 다운로드 여부
    
    Returns:
        다운로드된 파일 경로
    """
    import json
    
    # 캐시 확인 (1일 1회 다운로드)
    if not force_download and EXCEL_CACHE_FILE.exists():
        try:
            if CACHE_METADATA_FILE.exists():
                with open(CACHE_METADATA_FILE, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    cache_time = datetime.fromisoformat(metadata.get('download_time', ''))
                    cache_date = cache_time.date()
                    current_date = datetime.now().date()
                    
                    # 같은 날짜면 캐시 사용 (1일 1회 다운로드)
                    if cache_date == current_date:
                        logger.info(f"캐시된 엑셀 파일 사용 (다운로드: {cache_time.strftime('%Y-%m-%d %H:%M:%S')}): {EXCEL_CACHE_FILE}")
                        return EXCEL_CACHE_FILE
                    else:
                        logger.info(f"캐시 만료 (다운로드: {cache_date}, 현재: {current_date}). 새로 다운로드합니다.")
        except Exception as e:
            logger.warning(f"캐시 메타데이터 읽기 실패: {e}")
    
    # 엑셀 파일 다운로드
    logger.info(f"엑셀 파일 다운로드 중: {EXCEL_DOWNLOAD_URL}")
    try:
        response = requests.get(
            EXCEL_DOWNLOAD_URL,
            timeout=300,  # 5분 타임아웃 (큰 파일)
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        
        # 파일 저장
        with open(EXCEL_CACHE_FILE, 'wb') as f:
            f.write(response.content)
        
        # 메타데이터 저장
        metadata = {
            'download_time': datetime.now().isoformat(),
            'file_size': len(response.content),
            'url': EXCEL_DOWNLOAD_URL
        }
        with open(CACHE_METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"엑셀 파일 다운로드 완료: {len(response.content):,} bytes")
        return EXCEL_CACHE_FILE
        
    except Exception as e:
        logger.error(f"엑셀 파일 다운로드 실패: {e}")
        if EXCEL_CACHE_FILE.exists():
            logger.warning("기존 캐시 파일 사용")
            return EXCEL_CACHE_FILE
        raise


def load_excel_data(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    엑셀 파일 로드 및 DataFrame 반환
    
    Args:
        file_path: 엑셀 파일 경로 (None이면 캐시 파일 사용)
    
    Returns:
        pandas DataFrame
    """
    if file_path is None:
        file_path = EXCEL_CACHE_FILE
    
    if not file_path.exists():
        raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {file_path}")
    
    logger.info(f"엑셀 파일 로드 중: {file_path}")
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(file_path, engine='openpyxl')
        logger.info(f"엑셀 파일 로드 완료: {len(df):,}건")
        return df
    except Exception as e:
        logger.error(f"엑셀 파일 로드 실패: {e}")
        raise


def search_excel_data(
    df: pd.DataFrame,
    item_name: Optional[str] = None,
    entp_name: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    엑셀 데이터에서 검색
    
    Args:
        df: pandas DataFrame
        item_name: 품목명
        entp_name: 업체명
        limit: 최대 결과 수
    
    Returns:
        검색 결과 리스트
    """
    result_df = df.copy()
    
    # 품목명 검색
    if item_name:
        result_df = result_df[
            result_df['품목명'].astype(str).str.contains(item_name, case=False, na=False)
        ]
    
    # 업체명 검색
    if entp_name:
        result_df = result_df[
            result_df['업체명'].astype(str).str.contains(entp_name, case=False, na=False)
        ]
    
    # 결과 제한
    result_df = result_df.head(limit)
    
    # 날짜 형식 변환 함수
    def format_date(value):
        """날짜 값을 YYYYMMDD 형식으로 변환"""
        if pd.isna(value) or value is None:
            return None
        # pandas Timestamp인 경우
        if isinstance(value, pd.Timestamp):
            return value.strftime('%Y%m%d')
        # datetime 객체인 경우
        if isinstance(value, datetime):
            return value.strftime('%Y%m%d')
        # 숫자 형식 (엑셀 날짜 번호)인 경우
        if isinstance(value, (int, float)):
            try:
                date_value = pd.to_datetime(value, origin='1899-12-30', unit='D')
                return date_value.strftime('%Y%m%d')
            except:
                # 이미 YYYYMMDD 형식의 숫자일 수 있음
                if len(str(int(value))) == 8:
                    return str(int(value))
                return None
        # 문자열인 경우
        if isinstance(value, str):
            # 이미 YYYYMMDD 형식인지 확인
            if len(value) == 8 and value.isdigit():
                return value
            # 다른 형식 시도
            try:
                date_obj = pd.to_datetime(value)
                return date_obj.strftime('%Y%m%d')
            except:
                return value
        return str(value) if value else None
    
    # 컬럼명을 API 필드명으로 매핑
    col_mapping = {
        '품목명': 'ITEM_NAME',
        '품목 영문명': 'ITEM_ENG_NAME',
        '품목일련번호': 'ITEM_SEQ',
        '허가/신고구분': 'PERMIT_TYPE',
        '취소상태': 'CANCEL_STATUS',
        '취소일자': 'CANCEL_DATE',
        '변경일자': 'CHANGE_DATE',
        '업체명': 'ENTP_NAME',
        '업체 영문명': 'ENTP_ENG_NAME',
        '허가일자': 'ITEM_PERMIT_DATE',
        '업체허가번호': 'ENTP_NO',
        '전문일반': 'ETC_OTC_NAME',
        '성상': 'CHART',
        '표준코드': 'STD_CD',
        '원료성분': 'RAW_MATERIAL',
        '영문성분명': 'INGR_ENG_NAME',
        '효능효과': 'EE_DOC_DATA',
        '용법용량': 'NB_DOC_DATA',
        '주의사항': 'UD_DOC_DATA',
        '첨부문서': 'ATTACH_FILE',
        '저장방법': 'STORAGE_METHOD',
        '유효기간': 'VALID_TERM',
        '재심사대상': 'RE_EXAM_TARGET',
        '재심사기간': 'RE_EXAM_PERIOD',
        '포장단위': 'PACK_UNIT',
        ' 보험코드': 'EDI_CODE',  # 앞에 공백 있음
        '보험코드': 'EDI_CODE',
        '마약류분류': 'NARCOTIC_CLASS',
        '완제원료구분': 'FINISHED_PRODUCT',
        '신약여부': 'NEW_DRUG_YN',
        '업종 구분': 'INDUTY_TYPE',
        '업종구분': 'INDUTY_TYPE',
        '변경내용': 'CHANGE_CONTENT',
        '총량': 'TOTAL_AMOUNT',
        '주성분명': 'MAIN_ITEM_INGR',
        '첨가제 명': 'ADDITIVE_NAME',
        '첨가제명': 'ADDITIVE_NAME',
        'ATC코드': 'ATC_CODE',
        '사업자번호': 'BIZRNO',
        '희귀 의약품여부': 'RARE_DRUG_YN',
        '희귀의약품여부': 'RARE_DRUG_YN',
        '위탁제조업체': 'CONTRACT_MFG_YN'
    }
    
    # 날짜 필드 목록
    date_fields = ['CANCEL_DATE', 'CHANGE_DATE', 'ITEM_PERMIT_DATE']
    
    # 딕셔너리 리스트로 변환
    results = []
    for _, row in result_df.iterrows():
        item_dict = {}
        for col in df.columns:
            value = row[col]
            
            # 컬럼명 정규화 (앞뒤 공백 제거)
            col_normalized = col.strip()
            
            # NaN 값을 None으로 변환
            if pd.isna(value):
                value = None
            else:
                # 날짜 필드인 경우 형식 변환
                api_field_name = col_mapping.get(col_normalized, col_normalized.upper().replace(' ', '_'))
                if api_field_name in date_fields:
                    value = format_date(value)
                # 숫자 타입 처리
                elif isinstance(value, (int, float)):
                    # 정수로 변환 가능한 경우
                    if isinstance(value, float) and value.is_integer():
                        value = str(int(value))
                    else:
                        value = str(value)
                else:
                    value = str(value) if value else None
            
            # API 필드명으로 저장
            api_field_name = col_mapping.get(col_normalized, col_normalized.upper().replace(' ', '_'))
            item_dict[api_field_name] = value
            # 원본 컬럼명도 유지
            item_dict[col] = value
        
        results.append(item_dict)
    
    return results


def find_excel_item_by_seq(
    df: pd.DataFrame,
    item_seq: Optional[str] = None,
    item_name: Optional[str] = None,
    entp_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    엑셀 데이터에서 특정 항목 찾기 (품목일련번호 우선)
    
    Args:
        df: pandas DataFrame
        item_seq: 품목일련번호
        item_name: 품목명
        entp_name: 업체명
    
    Returns:
        찾은 항목 딕셔너리 또는 None
    """
    result_df = df.copy()
    
    # 품목일련번호로 먼저 검색 (가장 빠름)
    if item_seq:
        result_df = result_df[
            result_df['품목일련번호'].astype(str).str.strip() == str(item_seq).strip()
        ]
        if len(result_df) > 0:
            row = result_df.iloc[0]
            return _row_to_dict(row, df.columns)
    
    # 품목명과 업체명으로 검색
    if item_name and entp_name:
        result_df = df.copy()
        result_df = result_df[
            (result_df['품목명'].astype(str).str.strip() == str(item_name).strip()) &
            (result_df['업체명'].astype(str).str.strip() == str(entp_name).strip())
        ]
        if len(result_df) > 0:
            row = result_df.iloc[0]
            return _row_to_dict(row, df.columns)
    
    return None


def _row_to_dict(row: pd.Series, columns: pd.Index) -> Dict[str, Any]:
    """DataFrame 행을 딕셔너리로 변환"""
    from datetime import datetime
    
    def format_date(value):
        """날짜 값을 YYYYMMDD 형식으로 변환"""
        if pd.isna(value) or value is None:
            return None
        if isinstance(value, pd.Timestamp):
            return value.strftime('%Y%m%d')
        if isinstance(value, datetime):
            return value.strftime('%Y%m%d')
        if isinstance(value, (int, float)):
            try:
                date_value = pd.to_datetime(value, origin='1899-12-30', unit='D')
                return date_value.strftime('%Y%m%d')
            except:
                if len(str(int(value))) == 8:
                    return str(int(value))
                return None
        if isinstance(value, str):
            if len(value) == 8 and value.isdigit():
                return value
            try:
                date_obj = pd.to_datetime(value)
                return date_obj.strftime('%Y%m%d')
            except:
                return value
        return str(value) if value else None
    
    col_mapping = {
        '품목명': 'ITEM_NAME',
        '품목 영문명': 'ITEM_ENG_NAME',
        '품목일련번호': 'ITEM_SEQ',
        '허가/신고구분': 'PERMIT_TYPE',
        '취소상태': 'CANCEL_STATUS',
        '취소일자': 'CANCEL_DATE',
        '변경일자': 'CHANGE_DATE',
        '업체명': 'ENTP_NAME',
        '업체 영문명': 'ENTP_ENG_NAME',
        '허가일자': 'ITEM_PERMIT_DATE',
        '업체허가번호': 'ENTP_NO',
        '전문일반': 'ETC_OTC_NAME',
        '성상': 'CHART',
        '표준코드': 'STD_CD',
        '원료성분': 'RAW_MATERIAL',
        '영문성분명': 'INGR_ENG_NAME',
        '효능효과': 'EE_DOC_DATA',
        '용법용량': 'NB_DOC_DATA',
        '주의사항': 'UD_DOC_DATA',
        '첨부문서': 'ATTACH_FILE',
        '저장방법': 'STORAGE_METHOD',
        '유효기간': 'VALID_TERM',
        '재심사대상': 'RE_EXAM_TARGET',
        '재심사기간': 'RE_EXAM_PERIOD',
        '포장단위': 'PACK_UNIT',
        ' 보험코드': 'EDI_CODE',
        '보험코드': 'EDI_CODE',
        '마약류분류': 'NARCOTIC_CLASS',
        '완제원료구분': 'FINISHED_PRODUCT',
        '신약여부': 'NEW_DRUG_YN',
        '업종 구분': 'INDUTY_TYPE',
        '업종구분': 'INDUTY_TYPE',
        '변경내용': 'CHANGE_CONTENT',
        '총량': 'TOTAL_AMOUNT',
        '주성분명': 'MAIN_ITEM_INGR',
        '첨가제 명': 'ADDITIVE_NAME',
        '첨가제명': 'ADDITIVE_NAME',
        'ATC코드': 'ATC_CODE',
        '사업자번호': 'BIZRNO',
        '희귀 의약품여부': 'RARE_DRUG_YN',
        '희귀의약품여부': 'RARE_DRUG_YN',
        '위탁제조업체': 'CONTRACT_MFG_YN'
    }
    
    date_fields = ['CANCEL_DATE', 'CHANGE_DATE', 'ITEM_PERMIT_DATE']
    
    item_dict = {}
    for col in columns:
        value = row[col]
        col_normalized = col.strip()
        
        if pd.isna(value):
            value = None
        else:
            api_field_name = col_mapping.get(col_normalized, col_normalized.upper().replace(' ', '_'))
            if api_field_name in date_fields:
                value = format_date(value)
            elif isinstance(value, (int, float)):
                if isinstance(value, float) and value.is_integer():
                    value = str(int(value))
                else:
                    value = str(value)
            else:
                value = str(value) if value else None
        
        api_field_name = col_mapping.get(col_normalized, col_normalized.upper().replace(' ', '_'))
        item_dict[api_field_name] = value
    
    return item_dict


def fetch_approval_from_excel(
    item_name: Optional[str] = None,
    entp_name: Optional[str] = None,
    page_no: int = 1,
    num_of_rows: int = 10,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    엑셀 파일에서 허가정보 조회
    
    Args:
        item_name: 품목명
        entp_name: 업체명
        page_no: 페이지 번호
        num_of_rows: 페이지당 데이터 수
        use_cache: 캐시 사용 여부
    
    Returns:
        API 응답 형식과 동일한 딕셔너리
    """
    try:
        # 엑셀 파일 다운로드 (필요시)
        excel_file = download_excel_file(force_download=not use_cache)
        
        # 엑셀 데이터 로드
        df = load_excel_data(excel_file)
        
        # 검색
        all_results = search_excel_data(df, item_name, entp_name, limit=10000)
        
        # 페이지네이션
        start_idx = (page_no - 1) * num_of_rows
        end_idx = start_idx + num_of_rows
        paginated_results = all_results[start_idx:end_idx]
        
        return {
            "success": True,
            "totalCount": len(all_results),
            "items": paginated_results
        }
        
    except Exception as e:
        logger.error(f"엑셀 데이터 조회 실패: {e}")
        return {
            "success": False,
            "error": str(e),
            "totalCount": 0,
            "items": []
        }

