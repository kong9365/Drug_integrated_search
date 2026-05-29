"""
의약품/식품 통합 조회 시스템 설정 파일 — RegHub 360

API 엔드포인트는 공공데이터포털(data.go.kr) 승인 명세서(2026-05-26 발급)를 기준으로 작성.
관련 문서: API_APPLICATION_LIST.md, IMPLEMENTATION_PLAN.md, OpenAPI 신청 목록.txt
"""
import logging
import os
from pathlib import Path

# KD-IRIS — .env 파일 자동 로드 (있을 경우에만, 없어도 무해)
try:
    from dotenv import load_dotenv
    # BASE_DIR 정의 전이므로 직접 경로 계산
    _ENV_PATH = Path(__file__).parent / ".env"
    if _ENV_PATH.exists():
        load_dotenv(_ENV_PATH, override=False)
except ImportError:
    # python-dotenv 미설치 시 환경변수만 사용
    pass

# 프로젝트 루트 디렉토리
BASE_DIR = Path(__file__).parent

# ============================================================================
# 인증키 (Service Key / Key ID)
# ============================================================================
# 공공데이터포털(data.go.kr) 공통 SERVICE_KEY — 환경변수에서만 로드
# 의약품/의약외품/식품(data.go.kr 계열) 18개 API 공통 적용
# 보안: 평문 fallback 제거됨. .env 또는 시스템 환경변수에 키 설정 필수.
#   - 로컬: cp .env.example .env  →  .env에 키 입력  →  셸에서 export 또는 python-dotenv 사용
#   - 운영: 시크릿 매니저(AWS Secrets Manager 등) → 환경변수 주입
SERVICE_KEY = os.getenv("PUBLIC_DATA_SERVICE_KEY", "")
if not SERVICE_KEY:
    logging.getLogger(__name__).warning(
        "PUBLIC_DATA_SERVICE_KEY 환경변수가 비어 있습니다. "
        "data.go.kr 계열 18개 API 호출이 실패할 수 있습니다. "
        ".env 또는 시스템 환경변수에 키를 설정하세요."
    )

# 식품안전나라(foodsafetykorea.go.kr) KeyID — 별도 발급 필요
# NO 339(식품 회수·판매중지), 푸드QR 등 일부 식품 API는 식품안전나라 인증 체계 사용
# URL 패턴: http://openapi.foodsafetykorea.go.kr/api/{KEY_ID}/{SERVICE_ID}/{TYPE}/{START}/{END}
FOODSAFETY_KEY_ID = os.getenv("FOODSAFETY_KEY_ID", "")  # 미발급 시 빈 문자열

# ============================================================================
# API 엔드포인트 (data.go.kr 계열) — 18개 승인 API
# Base: https://apis.data.go.kr/1471000
# ============================================================================

# 의약품 API Base URL들
_DATA_GO_KR_BASE = "https://apis.data.go.kr/1471000"

API_ENDPOINTS = {
    # ===== 의약품 (9개) =====================================================
    # NO 140 의약품 제품 허가정보 — 정식 함수명 (이전 List07은 잘못된 함수명이었음)
    "approval":         f"{_DATA_GO_KR_BASE}/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07",      # 목록 조회 ★정식
    "approval_detail":  f"{_DATA_GO_KR_BASE}/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnDtlInq06",   # 상세정보
    "approval_ingr":    f"{_DATA_GO_KR_BASE}/DrugPrdtPrmsnInfoService07/getDrugPrdtMcpnDtlInq07",    # 주성분 상세

    # NO 564 의약품 행정처분 정보 — 기존 연동 유지
    "disciplinary":     f"{_DATA_GO_KR_BASE}/MdcinExaathrService04/getMdcinExaathrList04",

    # NO 539 의약품 회수·판매중지 정보 — 4개 오퍼레이션
    "recall":           f"{_DATA_GO_KR_BASE}/MdcinRtrvlSleStpgeInfoService04/getMdcinRtrvlSleStpgelList03",  # 목록 (※스펠링: Stpgel)
    "recall_detail":    f"{_DATA_GO_KR_BASE}/MdcinRtrvlSleStpgeInfoService04/getMdcinRtrvlSleStpgeItem03",   # 상세 (기존 연동)
    "recall_etc":       f"{_DATA_GO_KR_BASE}/MdcinRtrvlSleStpgeInfoService04/getMdcinRtrvlSleStpgelEtcList02",  # 의약품외 목록
    "recall_etc_detail":f"{_DATA_GO_KR_BASE}/MdcinRtrvlSleStpgeInfoService04/getMdcinRtrvlSleStpgeEtcItem03",   # 의약품외 상세

    # NO 563 의약품 낱알식별 정보 — 기존 연동 유지
    "identification":   f"{_DATA_GO_KR_BASE}/MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03",

    # NO 547 의약품안전성서한 정보
    "safety_letter":    f"{_DATA_GO_KR_BASE}/DrugSafeLetterService02/getDrugSafeLetterList02",

    # NO 534 의약품 생산수입공급중단 정보
    "supply_stop":      f"{_DATA_GO_KR_BASE}/MdcinPrdctnIncmeSuplyService2/getMdcinPrdctnIncmeSuplyList",

    # NO 537 의약품공급부족 정보
    "supply_lack":      f"{_DATA_GO_KR_BASE}/MdcinSuplyLackService03/getMdcinSuplyLackList01",

    # NO 531 DUR 품목정보 — 9개 오퍼레이션
    "dur_item_combine":     f"{_DATA_GO_KR_BASE}/DURPrdlstInfoService03/getUsjntTabooInfoList03",          # 병용금기
    "dur_item_elderly":     f"{_DATA_GO_KR_BASE}/DURPrdlstInfoService03/getOdsnAtentInfoList03",          # 노인주의
    "dur_item_list":        f"{_DATA_GO_KR_BASE}/DURPrdlstInfoService03/getDurPrdlstInfoList03",          # DUR 품목
    "dur_item_age":         f"{_DATA_GO_KR_BASE}/DURPrdlstInfoService03/getSpcifyAgrdeTabooInfoList03",   # 특정연령대금기
    "dur_item_capacity":    f"{_DATA_GO_KR_BASE}/DURPrdlstInfoService03/getCpctyAtentInfoList03",         # 용량주의
    "dur_item_period":      f"{_DATA_GO_KR_BASE}/DURPrdlstInfoService03/getMdctnPdAtentInfoList03",       # 투여기간주의
    "dur_item_efficacy":    f"{_DATA_GO_KR_BASE}/DURPrdlstInfoService03/getEfcyDplctInfoList03",          # 효능군중복
    "dur_item_seobang":     f"{_DATA_GO_KR_BASE}/DURPrdlstInfoService03/getSeobangjeongPartitnAtentInfoList03",  # 서방정분할
    "dur_item_pregnancy":   f"{_DATA_GO_KR_BASE}/DURPrdlstInfoService03/getPwnmTabooInfoList03",          # 임부금기

    # NO 533 DUR 성분정보 — 7개 오퍼레이션
    "dur_ingr_combine":     f"{_DATA_GO_KR_BASE}/DURIrdntInfoService03/getUsjntTabooInfoList02",
    "dur_ingr_age":         f"{_DATA_GO_KR_BASE}/DURIrdntInfoService03/getSpcifyAgrdeTabooInfoList02",
    "dur_ingr_pregnancy":   f"{_DATA_GO_KR_BASE}/DURIrdntInfoService03/getPwnmTabooInfoList02",
    "dur_ingr_capacity":    f"{_DATA_GO_KR_BASE}/DURIrdntInfoService03/getCpctyAtentInfoList02",
    "dur_ingr_period":      f"{_DATA_GO_KR_BASE}/DURIrdntInfoService03/getMdctnPdAtentInfoList02",
    "dur_ingr_elderly":     f"{_DATA_GO_KR_BASE}/DURIrdntInfoService03/getOdsnAtentInfoList02",
    "dur_ingr_efficacy":    f"{_DATA_GO_KR_BASE}/DURIrdntInfoService03/getEfcyDplctInfoList02",

    # ===== 의약외품 (1개) =====================================================
    # NO 145 의약외품 제품 허가 정보
    "quasi_approval":   f"{_DATA_GO_KR_BASE}/QdrgPrdtPrmsnInfoService03/getQdrgPrdtPrmsnInfoInq03",

    # ===== 식품 — data.go.kr 계열 (5개) ======================================
    # NO 1 식품영양성분DB
    "food_nutrition":   f"{_DATA_GO_KR_BASE}/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02",

    # NO 3 행정처분(수입식품업)
    "food_disc_import": f"{_DATA_GO_KR_BASE}/AdmmRsltIprtFoodService/getAdmmRsltIprtFoodService",

    # NO 5 행정처분(식품판매업)
    "food_disc_sale":   f"{_DATA_GO_KR_BASE}/AdmmRsltFoodSaleService/getAdmmRsltFoodSaleBssh",

    # NO 6 행정처분(식품제조가공업)
    "food_disc_mnft":   f"{_DATA_GO_KR_BASE}/AdmmRsltFoodMnftPrcsService/getAdmmRsltFoodMnftPrcsBssh",

    # NO 153 수입식품 회수판매중지 제품 정보
    "food_recall_import": f"{_DATA_GO_KR_BASE}/IprtFoodReclSaleStopPrdtStusService/getIprtFoodReclSaleStopPrdtStusInq",

    # ===== 2026-05-27 추가 승인 17개 End Point (동일 SERVICE_KEY) ============
    # 의약품 핵심 정보
    "drug_easy":          f"{_DATA_GO_KR_BASE}/DrbEasyDrugInfoService/getDrbEasyDrugList",                # NO 248 e약은요
    "drug_bundle":        f"{_DATA_GO_KR_BASE}/DrbBundleInfoService02/getDrbBundleList02",               # NO 269 묶음의약품 (HIRA/ATC 매핑)
    "drug_gmp_jgmt":      f"{_DATA_GO_KR_BASE}/DrugGmpStbltJgmtIssuStusService/getDrugGmpStbltJgmtIssuStusInq",   # NO 132 (Inq, not List)
    "drug_natn_shipmnt":  f"{_DATA_GO_KR_BASE}/DrugNatnShipmntAprvInfoService/getDrugNatnShipmntAprvInfoInq",     # NO 142 (Inq)
    "drug_entity_list":   f"{_DATA_GO_KR_BASE}/DrugEtcBsshBspmStusService/getDrugBsshListInq",                    # NO 144 업체 목록
    "drug_entity_detail": f"{_DATA_GO_KR_BASE}/DrugEtcBsshBspmStusService/getDrugBsshItemInq",                    # NO 144 업체 상세
    "drug_dmf":           f"{_DATA_GO_KR_BASE}/MdcDmfInfoService01/getMdcDmfList01",                    # NO 483 원료의약품 DMF

    # 의약품 R&D / BD (8개)
    "drug_patent":        f"{_DATA_GO_KR_BASE}/MdcinPatentInfoService2/getMdcinPatentInfoList2",        # NO 561 (List2, 끝에 2)
    "drug_lawsuit":       f"{_DATA_GO_KR_BASE}/DmstcLwstMdcinInfoService02/getMdcinRefreeSttusList02",  # NO 557 (함수명 별도)
    "drug_fda_p4":        f"{_DATA_GO_KR_BASE}/ParagraphIVTrgetMdcinService02/getParagraphIVSearchsList02",  # NO 552 (SearchsList)
    "drug_fda_orangebook":f"{_DATA_GO_KR_BASE}/FdaOrngbkPatentInfoService01/getFdaOrngbkPatentInfoList01",   # NO 562 FDA 오렌지북
    "drug_clinical":      f"{_DATA_GO_KR_BASE}/MdcinClincTestInfoService02/getMdcinClincTestInfoList02",     # NO 566 (Info 포함)
    "drug_clinical_org":  f"{_DATA_GO_KR_BASE}/ClinicTestOprtnInsttInfoService01/getClinicTestOprtnInsttInfo01",  # NO 568 임상기관
    "drug_reference":     f"{_DATA_GO_KR_BASE}/MdcCompDrugInfoService04/getMdcCompDrugList04",          # NO 484 대조약
    "drug_bioeq":         f"{_DATA_GO_KR_BASE}/MdcBioEqInfoService01/getMdcBioEqList01",                # NO 485 생동성

    # 의약품 안전성·특수 (4개)
    "drug_review":        f"{_DATA_GO_KR_BASE}/MdcinRejdgeService01/getMdcinRdjdgeList01",              # NO 554 재심사
    "drug_reeval":        f"{_DATA_GO_KR_BASE}/MdcinRevalService02/getMdcinRevalList02",                # NO 556 재평가
    "drug_orphan":        f"{_DATA_GO_KR_BASE}/RareMdcinInfoService02/getRareMdcinList02",              # NO 565 희귀의약품
    # NO 81 희귀필수의약품 — 5개 오퍼레이션
    "drug_rare_self":     f"{_DATA_GO_KR_BASE}/RareEsentMdcin/getRareNartDrugSelftreat",                # 자가치료용
    "drug_rare_treat":    f"{_DATA_GO_KR_BASE}/RareEsentMdcin/getRareSelfmdcin",                        # 치료용
    "drug_rare_unreg":    f"{_DATA_GO_KR_BASE}/RareEsentMdcin/getRareEmerIntdInsurceUnregistMdcin",     # 긴급도입 미등재
    "drug_rare_reg":      f"{_DATA_GO_KR_BASE}/RareEsentMdcin/getRareEmerIntdInsurceRegistMdcin",       # 긴급도입 등재
    "drug_rare_narc":     f"{_DATA_GO_KR_BASE}/RareEsentMdcin/getRareEmerIntdNarticDrug",               # 긴급도입 마약류

    # 식품 추가
    "food_inspect_list":  f"{_DATA_GO_KR_BASE}/PrsecImproptFoodInfoService03/getPrsecImproptFoodList01",  # NO 535 검사부적합 목록
    "food_inspect_item":  f"{_DATA_GO_KR_BASE}/PrsecImproptFoodInfoService03/getPrsecImproptFoodItem02",  # NO 535 검사부적합 상세

    # 건강기능식품
    "hf_gmp":             f"{_DATA_GO_KR_BASE}/FoodGmpStbltCompInfo/getFoodGmpStbltCompInfo",            # NO 51 건기식 GMP

    # 한국식품안전관리인증원 (B553748 카테고리 — 동일 SERVICE_KEY 작동 여부 smoke test 검증 필요)
    "haccp_smart":        f"https://apis.data.go.kr/B553748/SmartCertFoodListService/getFoodList",      # NO 12 스마트HACCP

    # ===== 한약(생약) — 미신청 hook (승인 시 endpoint 채우면 즉시 작동) ==========
    # NO 35 한약(생약)제제 허가 기원 — enrichment 한약 라인 폴백 (1차: 미신청)
    # "herbal_approval":  f"{_DATA_GO_KR_BASE}/<TBD-NO35-Service>/<TBD-op>",
    # NO 90 한약(생약)제제 회수·판매중지 — 모니터링 5번째 API (1차: 미신청)
    # "herbal_recall":    f"{_DATA_GO_KR_BASE}/<TBD-NO90-Service>/<TBD-op>",
    #   → data.go.kr 마이페이지 활용신청 → 자동승인 → End Point 복사 후 주석 해제.
    #   → fetch_herbal_approval / fetch_herbal_recall (api_extras stub)가 자동 활성.

    # ===== End Point 명세 확인 대기 (식품안전나라 serviceId 확정 완료, KeyID 발급 대기) =====
    #   NO 339→I0490 · 225→I2810 · 477→I2630 · 444→I1250 · 470→C002
    #   FOODSAFETY_SERVICES 에 등록됨. FOODSAFETY_KEY_ID 발급 후 fetch_foodsafety() 작동.
    #
    # ※ 마스크 관련 API (NO 162, 172) — 프로젝트 범위에서 제외

    # ===== Legacy 호환 (기존 코드 참조용) =====================================
    "approval_list":    f"{_DATA_GO_KR_BASE}/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07",
    "approval_inq":     f"{_DATA_GO_KR_BASE}/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07",
    "approval_alt":     f"{_DATA_GO_KR_BASE}/DrugPrdtPrmsnInfoService06/getDrugPrdtPrmsnInq06",
}

# ============================================================================
# 식품안전나라 (foodsafetykorea.go.kr) — 별도 keyId 발급 필요
# URL 패턴: http://openapi.foodsafetykorea.go.kr/api/{KEY_ID}/{SERVICE_ID}/{TYPE}/{START}/{END}[/{변수명}={값}]
# 인증: SERVICE_KEY 와 무관 — 식품안전나라 회원가입 후 API 신청 별도
# ============================================================================
FOODSAFETY_BASE = "http://openapi.foodsafetykorea.go.kr/api"

FOODSAFETY_SERVICES = {
    # NO 339 식품의 회수 및 판매중지 정보 (serviceId: I0490)
    # 응답 필드: PRDTNM, RTRVLPRVNS(회수사유), BSSHNM(제조업체), ADDR, TELNO, BRCDNO,
    #          FRMLCUNIT, MNFDT, RTRVLPLANDOC_RTRVLMTHD(회수방법), DISTBTMLMT(유통/소비기한),
    #          PRDLST_TYPE, IMG_FILE_PATH, PRDLST_CD, CRET_DTM, RTRVLDSUSE_SEQ,
    #          PRDLST_REPORT_NO(품목제조보고번호), RTRVL_GRDCD_NM(회수등급), PRDLST_CD_NM, LCNS_NO
    # 추가 파라미터: CRET_DTM(등록일자), PRDLST_REPORT_NO(품목제조보고번호)
    "food_recall_domestic": "I0490",

    # NO 225 해외 위해식품 회수정보 (serviceId: I2810)
    # 응답: TITL(제품명), DETECT_TITL(유해물질), CRET_DTM(생성일자), BDT(본문내용),
    #      DOWNLOAD_URL(이미지 다운로드 URL), NTCTXT_NO(게시글번호)
    # 추가 파라미터: ST_CRET_DTM(생성 시작범위), END_CRET_DTM(생성 종료범위)
    "food_recall_overseas": "I2810",

    # NO 477 행정처분결과(식품접객업) (serviceId: I2630)
    # 응답: PRCSCITYPOINT_BSSHNM(업소명), INDUTY_CD_NM(업종), LCNS_NO(인허가번호),
    #      DSPS_DCSNDT(처분확정일), DSPS_BGNDT/DSPS_ENDDT(처분기간), DSPS_TYPECD_NM(처분유형),
    #      VILTCN(위반내용), ADDR, TEL_NO, PRSDNT_NM(대표자), DSPSCN(처분내용),
    #      LAWORD_CD_NM(위반법령), PUBLIC_DT(공개기한), LAST_UPDT_DTM, DSPS_INSTTCD_NM(처분기관), DSPSDTLS_SEQ
    # 추가 파라미터: CHNG_DT(변경일자), DSPS_DCSNDT(확정일자), LCNS_NO(인허가번호)
    "food_disc_service": "I2630",

    # NO 444 식품(첨가물) 품목제조보고 (serviceId: I1250)
    # 응답: LCNS_NO, BSSH_NM, PRDLST_REPORT_NO, PRMS_DT(허가일자), PRDLST_NM(제품명),
    #      PRDLST_DCNM(품목유형명), PRODUCTION(생산종료여부), HIENG_LNTRT_DVS_NM(고열량저영양),
    #      CHILD_CRTFC_YN(어린이기호식품 인증), POG_DAYCNT(소비기한), INDUTY_CD_NM(업종),
    #      QLITY_MNTNC_TMLMT_DAYCNT, USAGE(용법), PRPOS(용도), DISPOS(제품형태),
    #      FRMLC_MTRQLT(포장재질), ETQTY_XPORT_PRDLST_YN(내수/겸용), LAST_UPDT_DTM
    # 추가 파라미터: CHNG_DT, PRDLST_REPORT_NO, BSSH_NM, PRDLST_NM, LCNS_NO, PRMS_DT, PRDLST_DCNM
    "food_report": "I1250",

    # NO 470 식품(첨가물) 품목제조보고(원재료) (serviceId: C002)
    # 응답: LCNS_NO, BSSH_NM, PRDLST_REPORT_NO, PRMS_DT(보고일자), PRDLST_NM(품목명),
    #      PRDLST_DCNM(품목유형명), RAWMTRL_NM(원재료명), RAWMTRL_ORDNO(원재료표시순서),
    #      CHNG_DT(변경일자), ETQTY_XPORT_PRDLST_YN(내수/겸용)
    # 추가 파라미터: CHNG_DT, PRDLST_REPORT_NO, PRDLST_NM, BSSH_NM, LCNS_NO, RAWMTRL_NM, PRMS_DT, PRDLST_DCNM
    "food_report_raw": "C002",

    # 향후 추가 예정 (식품안전나라 신청 후):
    # "food_qr": "<푸드QR 서비스ID>",
    # "food_haccp": "<HACCP 서비스ID>",
}

# ============================================================================
# Flask 설정
# ============================================================================
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

# 정적 파일 경로
STATIC_FOLDER = BASE_DIR / "static"
IMAGES_FOLDER = STATIC_FOLDER / "images"
IMAGES_FOLDER.mkdir(parents=True, exist_ok=True)

# 로그 설정
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ============================================================================
# KD-IRIS 1차 빌드 — SQLite DB + 자사 품목 마스터 (기능재설계 v2 §11)
# ============================================================================
# 데이터 디렉터리 (워치리스트 JSON + SQLite DB 공용)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# SQLite DB 경로 (자사 마스터·스냅샷·이벤트 — .gitignore 처리됨)
DB_PATH = DATA_DIR / "kdiris.sqlite"

# DB 스키마 파일
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"

# 자사 품목 마스터 엑셀 경로 — 자사 기밀, repo 밖 C:\Temp 보관 (환경변수로 재정의 가능)
MASTER_XLSX_PATH = os.getenv(
    "MASTER_XLSX_PATH",
    r"C:\Temp\품목 마스터 관리_2026-05-28.xlsx",
)

# 자사 허가권자명 (enrichment 클라이언트 매칭에 사용 — NO 140 ENTP_NAME 부분일치)
COMPANY_NAME = os.getenv("COMPANY_NAME", "광동")

# ============================================================================
# API 요청 설정
# ============================================================================
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1  # 초

# SSL 검증 — Windows 환경에서 SSL 인증서 문제 발생 시 False
VERIFY_SSL = os.getenv("VERIFY_SSL", "False").lower() == "true"

# ============================================================================
# 데이터 동기화 설정 (Phase 2 이후)
# ============================================================================
DAILY_BATCH_HOUR = int(os.getenv("DAILY_BATCH_HOUR", "3"))  # 새벽 3시 야간 배치
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # Redis 캐시 1시간
