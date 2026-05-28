"""
의약품 통합 조회 시스템 - API 클라이언트 모듈
4개 API를 통합하여 호출하는 함수들
"""
import logging
import time
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from urllib.parse import unquote
from pathlib import Path
import urllib3

from .config import (
    API_ENDPOINTS,
    SERVICE_KEY,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    VERIFY_SSL,
    IMAGES_FOLDER
)

# SSL 경고 비활성화 (테스트 환경용)
if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# 엑셀 데이터 로더 (선택적 import)
try:
    from .excel_data_loader import fetch_approval_from_excel
    EXCEL_LOADER_AVAILABLE = True
except ImportError:
    EXCEL_LOADER_AVAILABLE = False
    logger.warning("엑셀 데이터 로더를 사용할 수 없습니다. pandas와 openpyxl이 설치되어 있는지 확인하세요.")


def _clean_service_key(raw_key: str) -> str:
    """서비스 키 정규화"""
    key = raw_key.strip()
    if "%25" in key:
        key = unquote(key)
    if "%2" in key.lower():
        key = unquote(key)
    return key


def _make_request(url: str, params: Dict[str, Any]) -> requests.Response:
    """API 요청 실행 (재시도 로직 포함)"""
    service_key = _clean_service_key(SERVICE_KEY)
    params["serviceKey"] = service_key
    
    # SSL 검증 설정 로그
    if not VERIFY_SSL:
        logger.info("SSL 인증서 검증을 건너뜁니다. (테스트 환경)")
    
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            logger.debug(f"API 요청 시도 {attempt + 1}/{MAX_RETRIES}: {url}")
            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
                verify=VERIFY_SSL
            )
            response.raise_for_status()
            logger.info(f"API 요청 성공: {url}")
            return response
        except requests.exceptions.SSLError as e:
            last_error = f"SSL 인증서 오류: {str(e)}. SSL 검증을 비활성화하려면 config.py에서 VERIFY_SSL=False로 설정하세요."
            logger.error(last_error)
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"재시도 중... (시도 {attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                # SSL 오류인 경우 verify=False로 재시도
                try:
                    logger.warning("SSL 검증 없이 재시도합니다...")
                    response = requests.get(
                        url,
                        params=params,
                        timeout=REQUEST_TIMEOUT,
                        verify=False
                    )
                    response.raise_for_status()
                    logger.info("SSL 검증 없이 API 요청 성공")
                    return response
                except Exception as retry_error:
                    raise Exception(f"{last_error}\n재시도도 실패: {str(retry_error)}")
        except requests.exceptions.Timeout as e:
            last_error = f"요청 시간 초과: {REQUEST_TIMEOUT}초 내에 응답을 받지 못했습니다."
            logger.warning(f"{last_error} (시도 {attempt + 1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise Exception(last_error)
        except requests.exceptions.ConnectionError as e:
            last_error = f"네트워크 연결 오류: 인터넷 연결을 확인하거나 서버가 응답하지 않습니다. ({str(e)})"
            logger.warning(f"{last_error} (시도 {attempt + 1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise Exception(last_error)
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else "알 수 없음"
            last_error = f"HTTP 오류 {status_code}: {str(e)}"
            logger.error(f"{last_error} (시도 {attempt + 1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise Exception(last_error)
        except requests.RequestException as e:
            last_error = f"요청 오류: {str(e)}"
            logger.warning(f"{last_error} (시도 {attempt + 1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise Exception(last_error)
        except Exception as e:
            last_error = f"예상치 못한 오류: {str(e)}"
            logger.error(last_error)
            raise Exception(last_error)
    
    raise Exception(f"API 요청 실패: {last_error or '알 수 없는 오류'}")


def _parse_xml_response(xml_text: str) -> Dict[str, Any]:
    """XML 응답 파싱"""
    try:
        root = ET.fromstring(xml_text)
        
        # 에러 체크
        result_code = root.findtext(".//resultCode", "")
        result_msg = root.findtext(".//resultMsg", "")
        
        if result_code and result_code != "00":
            error_msg = f"API 오류: {result_msg or result_code}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # 데이터 추출
        items = root.findall(".//item")
        total_count = root.findtext(".//totalCount", "0")
        
        return {
            "items": [item for item in items],
            "totalCount": int(total_count) if total_count.isdigit() else 0
        }
    except ET.ParseError as e:
        logger.error(f"XML 파싱 오류: {str(e)}")
        raise Exception("응답 데이터를 읽을 수 없습니다")


def _item_to_dict(item: ET.Element) -> Dict[str, str]:
    """XML item 요소를 딕셔너리로 변환"""
    result = {}
    for child in item:
        result[child.tag] = child.text or ""
    return result


def merge_api_with_excel_data(
    api_items: List[Dict[str, Any]],
    item_name: Optional[str] = None,
    entp_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    API 데이터와 엑셀 데이터를 병합
    API에 없는 필드는 엑셀 데이터로 채움
    
    Args:
        api_items: API에서 가져온 항목 리스트
        item_name: 품목명 (검색용)
        entp_name: 업체명 (검색용)
    
    Returns:
        병합된 항목 리스트
    """
    if not EXCEL_LOADER_AVAILABLE or not api_items:
        return api_items
    
    try:
        # 엑셀 데이터 로드 (병합 시에는 필요한 항목만 찾기 위해 전체 로드 필요)
        from .excel_data_loader import download_excel_file, load_excel_data, find_excel_item_by_seq
        
        excel_file = download_excel_file(force_download=False)
        
        # 병합된 결과
        merged_items = []
        
        # 엑셀 파일을 한 번만 로드 (캐시 활용)
        df_cache = None
        
        for api_item in api_items:
            merged_item = api_item.copy()
            
            # 엑셀 데이터에서 매칭되는 항목 찾기
            api_item_seq = api_item.get('ITEM_SEQ') or api_item.get('item_seq')
            api_item_name = api_item.get('ITEM_NAME') or api_item.get('PRDUCT')
            api_entp_name = api_item.get('ENTP_NAME') or api_item.get('Entrps')
            
            # 엑셀 파일을 지연 로드 (필요할 때만)
            if df_cache is None:
                logger.info("엑셀 파일 로드 중 (병합용)...")
                df_cache = load_excel_data(excel_file)
                logger.info(f"엑셀 파일 로드 완료: {len(df_cache):,}건")
            
            # 품목일련번호로 직접 검색 (가장 빠름)
            matched_excel_item = find_excel_item_by_seq(
                df_cache,
                item_seq=str(api_item_seq) if api_item_seq else None,
                item_name=api_item_name,
                entp_name=api_entp_name
            )
            
            # 엑셀 데이터로 누락된 필드 채우기
            if matched_excel_item:
                for key, value in matched_excel_item.items():
                    # 원본 컬럼명은 제외 (API 필드명만 사용)
                    if key in ['품목명', '품목 영문명', '품목일련번호', '허가/신고구분', '취소상태', 
                              '취소일자', '변경일자', '업체명', '업체 영문명', '허가일자', '업체허가번호',
                              '전문일반', '성상', '표준코드', '원료성분', '영문성분명', '효능효과', 
                              '용법용량', '주의사항', '첨부문서', '저장방법', '유효기간', '재심사대상',
                              '재심사기간', '포장단위', ' 보험코드', '보험코드', '마약류분류', '완제원료구분',
                              '신약여부', '업종 구분', '업종구분', '변경내용', '총량', '주성분명',
                              '첨가제 명', '첨가제명', 'ATC코드', '사업자번호', '희귀 의약품여부',
                              '희귀의약품여부', '위탁제조업체']:
                        continue
                    
                    # 값이 유효한지 확인
                    if not value or value == 'None' or value == 'nan' or not str(value).strip():
                        continue
                    
                    value_str = str(value).strip()
                    
                    # API에 없는 필드이거나 API 값이 비어있는 경우 엑셀 값으로 채움
                    if key not in merged_item:
                        merged_item[key] = value_str
                    elif not merged_item.get(key) or merged_item.get(key) == '':
                        merged_item[key] = value_str
                    # API 값이 있지만 엑셀 값이 더 상세한 경우 (예: URL이 아닌 실제 내용)
                    elif key in ['EE_DOC_DATA', 'NB_DOC_DATA', 'UD_DOC_DATA']:
                        # API는 URL만 있고 엑셀은 URL 또는 내용이 있을 수 있음
                        if value_str.startswith('http'):
                            merged_item[key] = value_str
                    # API 값이 있지만 엑셀 값이 더 긴 경우 (더 상세한 정보)
                    elif len(value_str) > len(str(merged_item.get(key, ''))):
                        merged_item[key] = value_str
            
            merged_items.append(merged_item)
        
        return merged_items
        
    except Exception as e:
        logger.error(f"API와 엑셀 데이터 병합 실패: {e}")
        return api_items


def fetch_approval(
    item_name: Optional[str] = None,
    entp_name: Optional[str] = None,
    page_no: int = 1,
    num_of_rows: int = 10,
    response_type: str = "xml",
    # 추가 파라미터 (공공데이터포털 API 명세서 기준)
    induty: Optional[str] = None,  # 업종
    spclty_pblc: Optional[str] = None,  # 전문/일반구분
    prdlst_stdr_code: Optional[str] = None,  # 품목일련번호
    prduct_prmisn_no: Optional[str] = None,  # 품목허가번호
    entp_seq: Optional[str] = None,  # 업일련번호
    entp_no: Optional[str] = None,  # 업허가번호
    edi_code: Optional[str] = None,  # 보험코드
    item_ingr_name: Optional[str] = None,  # 주성분
    bizrno: Optional[str] = None,  # 사업자등록번호
    item_permit_date: Optional[str] = None,  # 허가일자 (YYYYMMDD 형식)
    bar_code: Optional[str] = None,  # 표준코드
    item_seq: Optional[str] = None,  # 품목기준코드
    start_change_date: Optional[str] = None,  # 변경일자 시작 (YYYYMMDD)
    end_change_date: Optional[str] = None,  # 변경일자 종료 (YYYYMMDD)
    atc_code: Optional[str] = None,  # ATC코드
    rare_drug_yn: Optional[str] = None,  # 희귀의약품여부
    main_item_ingr: Optional[str] = None  # 유효성분
) -> Dict[str, Any]:
    """
    의약품 허가정보 조회
    
    Args:
        item_name: 품목명
        entp_name: 업체명
        page_no: 페이지 번호
        num_of_rows: 페이지당 데이터 수
        response_type: 응답 형식 (xml/json)
        induty: 업종
        spclty_pblc: 전문/일반구분
        prdlst_stdr_code: 품목일련번호
        prduct_prmisn_no: 품목허가번호
        entp_seq: 업일련번호
        entp_no: 업허가번호
        edi_code: 보험코드
        item_ingr_name: 주성분
        bizrno: 사업자등록번호
        item_permit_date: 허가일자 (YYYYMMDD)
        bar_code: 표준코드
        item_seq: 품목기준코드
        start_change_date: 변경일자 시작 (YYYYMMDD)
        end_change_date: 변경일자 종료 (YYYYMMDD)
        atc_code: ATC코드
        rare_drug_yn: 희귀의약품여부
        main_item_ingr: 유효성분
    
    Returns:
        API 응답 데이터
    """
    params = {
        "pageNo": str(page_no),
        "numOfRows": str(num_of_rows),
        "type": response_type
    }
    
    # 기본 검색 파라미터
    if item_seq:
        params["item_seq"] = item_seq
    if item_name:
        params["item_name"] = item_name
    if entp_name:
        params["entp_name"] = entp_name
    
    # 추가 검색 파라미터
    if induty:
        params["induty"] = induty
    if spclty_pblc:
        params["spclty_pblc"] = spclty_pblc
    if prdlst_stdr_code:
        params["prdlst_Stdr_code"] = prdlst_stdr_code  # 대소문자 주의
    if prduct_prmisn_no:
        params["prduct_prmisn_no"] = prduct_prmisn_no
    if entp_seq:
        params["entp_seq"] = entp_seq
    if entp_no:
        params["entp_no"] = entp_no
    if edi_code:
        params["edi_code"] = edi_code
    if item_ingr_name:
        params["item_ingr_name"] = item_ingr_name
    if bizrno:
        params["bizrno"] = bizrno
    if item_permit_date:
        params["item_permit_date"] = item_permit_date
    if bar_code:
        params["bar_code"] = bar_code
    if start_change_date:
        params["start_change_date"] = start_change_date
    if end_change_date:
        params["end_change_date"] = end_change_date
    if atc_code:
        params["atc_code"] = atc_code
    if rare_drug_yn:
        params["rare_drug_yn"] = rare_drug_yn
    if main_item_ingr:
        params["main_item_ingr"] = main_item_ingr
    
    logger.info(f"허가정보 조회 요청: {params}")
    
    # 여러 엔드포인트 시도 — 2026-05-26 공공데이터포털 공식 명세 기준
    # Base URL: https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07
    # 정식 함수명: getDrugPrdtPrmsnInq07 (목록) / getDrugPrdtPrmsnDtlInq06 (상세)
    # — 이전 List07은 잘못된 함수명으로 404 발생 원인이었음
    endpoints_to_try = [
        API_ENDPOINTS.get("approval"),         # 목록 조회 (getDrugPrdtPrmsnInq07) ★정식
        API_ENDPOINTS.get("approval_detail"),  # 상세정보 조회 (getDrugPrdtPrmsnDtlInq06)
        API_ENDPOINTS.get("approval_alt"),     # Service06 폴백
    ]
    # None 값 제거
    endpoints_to_try = [e for e in endpoints_to_try if e]
    
    last_error = None
    for endpoint in endpoints_to_try:
        try:
            response = _make_request(endpoint, params)
            parsed = _parse_xml_response(response.text)
            
            items = [_item_to_dict(item) for item in parsed["items"]]
            
            # 엑셀 데이터와 병합 (API에 없는 정보는 엑셀 데이터로 채움)
            if EXCEL_LOADER_AVAILABLE:
                try:
                    items = merge_api_with_excel_data(items, item_name, entp_name)
                    logger.info(f"API 데이터와 엑셀 데이터 병합 완료: {len(items)}건")
                except Exception as merge_error:
                    logger.warning(f"엑셀 데이터 병합 실패 (API 데이터만 사용): {merge_error}")
            
            logger.info(f"허가정보 조회 성공: {len(items)}건")
            return {
                "success": True,
                "totalCount": parsed["totalCount"],
                "items": items
            }
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response and e.response.status_code == 404:
                last_error = f"엔드포인트를 찾을 수 없습니다 (404): {endpoint}"
                logger.warning(f"{last_error} - 대체 엔드포인트 시도 중...")
                if endpoint != endpoints_to_try[-1]:  # 마지막 엔드포인트가 아니면 계속 시도
                    continue
            else:
                last_error = f"HTTP 오류: {str(e)}"
                logger.error(f"허가정보 조회 실패: {last_error}")
                break
        except Exception as e:
            last_error = str(e)
            logger.error(f"허가정보 조회 실패: {last_error}")
            # 404가 아닌 다른 오류는 즉시 반환
            if "404" not in str(e):
                break
    
    # 모든 API 시도 실패 - 엑셀 데이터로 대체 시도
    error_msg = last_error or "알 수 없는 오류"
    logger.warning(f"허가정보 API 조회 실패: {error_msg}")
    
    if EXCEL_LOADER_AVAILABLE:
        logger.info("엑셀 데이터 소스로 대체 시도 중...")
        try:
            excel_result = fetch_approval_from_excel(
                item_name=item_name,
                entp_name=entp_name,
                page_no=page_no,
                num_of_rows=num_of_rows,
                use_cache=True
            )
            if excel_result.get("success") and excel_result.get("items"):
                logger.info(f"엑셀 데이터 조회 성공: {excel_result.get('totalCount', 0)}건")
                return excel_result
            else:
                logger.warning("엑셀 데이터 조회 결과가 비어있습니다.")
        except Exception as excel_error:
            logger.error(f"엑셀 데이터 조회 실패: {excel_error}")
    
    # 모든 소스 실패
    logger.error(f"허가정보 조회 최종 실패: {error_msg}")
    return {
        "success": False,
        "error": f"허가정보 API가 현재 사용할 수 없습니다. ({error_msg}) 엑셀 데이터 소스도 사용할 수 없습니다. 공공데이터포털(https://www.data.go.kr)에서 '의약품 허가정보'를 검색하여 최신 API를 확인해주세요.",
        "totalCount": 0,
        "items": []
    }


def fetch_approval_detail(
    item_name: Optional[str] = None,
    entp_name: Optional[str] = None,
    item_seq: Optional[str] = None,
    edi_code: Optional[str] = None,
    bar_code: Optional[str] = None,
    item_permit_date: Optional[str] = None,
    entp_no: Optional[str] = None,
    bizrno: Optional[str] = None,
    atc_code: Optional[str] = None,
    rare_drug_yn: Optional[str] = None,
    page_no: int = 1,
    num_of_rows: int = 5,
    response_type: str = "xml",
) -> Dict[str, Any]:
    """
    NO 140 의약품 제품 허가 상세정보 (getDrugPrdtPrmsnDtlInq06).

    목록 API(fetch_approval) 와 별개로 상세 필드를 받음:
      MATERIAL_NAME(주성분), VALID_TERM(유효기간), REEXAM_DATE(재심사일),
      ATC_CODE(ATC), BAR_CODE(표준코드), CHART(성상), PACK_UNIT(포장단위),
      STORAGE_METHOD(저장법), RARE_DRUG_YN(희귀의약품), NARCOTIC_KIND_CODE,
      EE_DOC_DATA(효능효과), UD_DOC_DATA(용법용량), NB_DOC_DATA(주의사항)
    """
    endpoint = API_ENDPOINTS.get("approval_detail")
    if not endpoint:
        return {"success": False, "error": "approval_detail endpoint 미정의",
                "items": [], "totalCount": 0}

    params = {
        "pageNo": str(page_no),
        "numOfRows": str(num_of_rows),
        "type": response_type,
    }
    # 검색 파라미터 (모두 snake_case)
    for k, v in {
        "item_name": item_name, "entp_name": entp_name, "item_seq": item_seq,
        "edi_code": edi_code, "bar_code": bar_code,
        "item_permit_date": item_permit_date, "entp_no": entp_no,
        "bizrno": bizrno, "atc_code": atc_code, "rare_drug_yn": rare_drug_yn,
    }.items():
        if v:
            params[k] = v

    logger.info(f"허가 상세정보 조회: {params}")
    try:
        response = _make_request(endpoint, params)
        parsed = _parse_xml_response(response.text)
        items = [_item_to_dict(item) for item in parsed["items"]]
        return {
            "success": True,
            "totalCount": parsed.get("totalCount", len(items)),
            "items": items,
        }
    except Exception as e:
        logger.warning(f"허가 상세정보 조회 실패: {e}")
        return {"success": False, "error": str(e), "items": [], "totalCount": 0}


def fetch_disciplinary(
    entp_name: Optional[str] = None,
    item_name: Optional[str] = None,
    order: str = "Y",
    page_no: int = 1,
    num_of_rows: int = 10,
    response_type: str = "xml"
) -> Dict[str, Any]:
    """
    의약품 행정처분정보 조회
    
    Args:
        entp_name: 업체명
        item_name: 제품명
        order: 최신순 정렬 (Y 권장)
        page_no: 페이지 번호
        num_of_rows: 페이지당 수량
        response_type: 응답 형식
    
    Returns:
        API 응답 데이터
    """
    params = {
        "order": order,
        "pageNo": str(page_no),
        "numOfRows": str(num_of_rows),
        "type": response_type
    }
    
    if entp_name:
        params["entp_name"] = entp_name
    if item_name:
        params["item_name"] = item_name
    
    logger.info(f"행정처분정보 조회 요청: {params}")
    
    try:
        response = _make_request(API_ENDPOINTS["disciplinary"], params)
        parsed = _parse_xml_response(response.text)
        
        items = [_item_to_dict(item) for item in parsed["items"]]
        
        return {
            "success": True,
            "totalCount": parsed["totalCount"],
            "items": items
        }
    except Exception as e:
        logger.error(f"행정처분정보 조회 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "totalCount": 0,
            "items": []
        }


def fetch_recall(
    item_name: Optional[str] = None,
    entp_name: Optional[str] = None,
    page_no: int = 1,
    num_of_rows: int = 10,
    response_type: str = "xml"
) -> Dict[str, Any]:
    """
    의약품 회수·판매중지정보 조회
    
    Args:
        item_name: 품목명
        entp_name: 업체명
        page_no: 페이지 번호
        num_of_rows: 페이지당 수량
        response_type: 응답 형식
    
    Returns:
        API 응답 데이터
    """
    params = {
        "pageNo": str(page_no),
        "numOfRows": str(num_of_rows),
        "type": response_type
    }
    
    if item_name:
        params["item_name"] = item_name
    if entp_name:
        params["entp_name"] = entp_name
    
    logger.info(f"회수·판매중지정보 조회 요청: {params}")
    
    try:
        response = _make_request(API_ENDPOINTS["recall"], params)
        parsed = _parse_xml_response(response.text)
        
        items = [_item_to_dict(item) for item in parsed["items"]]
        
        return {
            "success": True,
            "totalCount": parsed["totalCount"],
            "items": items
        }
    except Exception as e:
        logger.error(f"회수·판매중지정보 조회 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "totalCount": 0,
            "items": []
        }


def download_image(image_url: str, item_name: str) -> Optional[str]:
    """
    의약품 이미지 다운로드
    
    Args:
        image_url: 이미지 URL
        item_name: 제품명 (파일명으로 사용)
    
    Returns:
        저장된 파일 경로 또는 None
    """
    if not image_url:
        return None
    
    try:
        # 파일명 생성 (특수문자 제거)
        safe_name = "".join(c for c in item_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        filename = f"{safe_name}.jpg"
        filepath = IMAGES_FOLDER / filename
        
        # 이미 다운로드된 경우 스킵
        if filepath.exists():
            logger.info(f"이미지 이미 존재: {filename}")
            return f"/static/images/{filename}"
        
        # 이미지 다운로드
        response = requests.get(image_url, timeout=REQUEST_TIMEOUT, verify=VERIFY_SSL)
        response.raise_for_status()
        
        # 파일 저장
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"이미지 다운로드 완료: {filename}")
        return f"/static/images/{filename}"
    except Exception as e:
        logger.warning(f"이미지 다운로드 실패 ({item_name}): {str(e)}")
        return None


def fetch_identification(
    item_name: Optional[str] = None,
    entp_name: Optional[str] = None,
    page_no: int = 1,
    num_of_rows: int = 10,
    response_type: str = "xml",
    download_images: bool = True
) -> Dict[str, Any]:
    """
    의약품 낱알식별정보 조회
    
    Args:
        item_name: 제품명
        entp_name: 제조사명
        page_no: 페이지 번호
        num_of_rows: 페이지당 데이터 수
        response_type: 응답 형식
        download_images: 이미지 자동 다운로드 여부
    
    Returns:
        API 응답 데이터
    """
    params = {
        "pageNo": str(page_no),
        "numOfRows": str(num_of_rows),
        "type": response_type
    }
    
    if item_name:
        params["item_name"] = item_name
    if entp_name:
        params["entp_name"] = entp_name
    
    logger.info(f"낱알식별정보 조회 요청: {params}")
    
    try:
        response = _make_request(API_ENDPOINTS["identification"], params)
        parsed = _parse_xml_response(response.text)
        
        items = []
        for item in parsed["items"]:
            item_dict = _item_to_dict(item)
            
            # 이미지 다운로드
            if download_images and item_dict.get("ITEM_IMAGE"):
                image_path = download_image(
                    item_dict["ITEM_IMAGE"],
                    item_dict.get("ITEM_NAME", "unknown")
                )
                if image_path:
                    item_dict["LOCAL_IMAGE"] = image_path
                else:
                    item_dict["LOCAL_IMAGE"] = None
            
            items.append(item_dict)
        
        return {
            "success": True,
            "totalCount": parsed["totalCount"],
            "items": items
        }
    except Exception as e:
        logger.error(f"낱알식별정보 조회 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "totalCount": 0,
            "items": []
        }


def search_all(
    item_seq: Optional[str] = None,
    item_name: Optional[str] = None,
    entp_name: Optional[str] = None,
    download_images: bool = True
) -> Dict[str, Any]:
    """
    통합 검색 - 2개 API 병렬 호출 (허가정보, 낱알식별)
    
    Args:
        item_seq: 품목기준코드
        item_name: 제품명
        entp_name: 업체명
        download_images: 이미지 자동 다운로드 여부
    
    Returns:
        통합 검색 결과
    """
    import concurrent.futures
    
    logger.info(f"통합 검색 시작: item_seq={item_seq}, item_name={item_name}, entp_name={entp_name}")
    
    # item_seq가 있으면 item_name으로 변환하여 검색
    if item_seq and not item_name:
        # 품목기준코드로 검색 시 item_seq를 item_name으로도 사용
        item_name = item_seq
    
    results = {
        "approval": {"success": False, "items": [], "totalCount": 0},
        "identification": {"success": False, "items": [], "totalCount": 0}
    }
    
    # 병렬 호출
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # fetch_approval에 item_seq 전달 (item_seq 파라미터 위치 확인 필요)
        approval_kwargs = {
            'item_name': item_name,
            'entp_name': entp_name,
            'page_no': 1,
            'num_of_rows': 10,
            'item_seq': item_seq
        }
        futures = {
            "approval": executor.submit(fetch_approval, **approval_kwargs),
            "identification": executor.submit(fetch_identification, item_name, entp_name, 1, 10, "xml", download_images)
        }
        
        for key, future in futures.items():
            try:
                # 엑셀 파일 로드를 고려하여 타임아웃을 더 길게 설정 (5분)
                timeout = REQUEST_TIMEOUT * 6 if key == "approval" else REQUEST_TIMEOUT
                results[key] = future.result(timeout=timeout)
            except concurrent.futures.TimeoutError as e:
                logger.warning(f"{key} API 호출 타임아웃 (엑셀 파일 로드 중일 수 있음): {str(e)}")
                results[key] = {
                    "success": False,
                    "error": f"요청 시간 초과 (엑셀 파일 로드 중일 수 있습니다)",
                    "items": [],
                    "totalCount": 0
                }
            except Exception as e:
                error_msg = str(e) if str(e) else "알 수 없는 오류"
                logger.error(f"{key} API 호출 실패: {error_msg}")
                results[key] = {
                    "success": False,
                    "error": error_msg,
                    "items": [],
                    "totalCount": 0
                }
    
    return results

