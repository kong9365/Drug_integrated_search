"""
의약품/식품 통합 조회 시스템 설정 파일 — RegHub 360

API 엔드포인트는 공공데이터포털(data.go.kr) 승인 명세서(2026-05-26 발급)를 기준으로 작성.
관련 문서: API_APPLICATION_LIST.md, IMPLEMENTATION_PLAN.md, OpenAPI 신청 목록.txt
"""
import os
from pathlib import Path

# 프로젝트 루트 디렉토리
BASE_DIR = Path(__file__).parent

# ============================================================================
# 인증키 (Service Key / Key ID)
# ============================================================================
# 공공데이터포털(data.go.kr) 공통 SERVICE_KEY — 2026-05-26 발급
# 의약품/의약외품/식품(data.go.kr 계열) 18개 API 공통 적용
# 보안: 운영 환경에서는 반드시 환경변수 PUBLIC_DATA_SERVICE_KEY 사용
SERVICE_KEY = os.getenv(
    "PUBLIC_DATA_SERVICE_KEY",
    ""
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

    # ===== End Point 명세 확인 대기 5개 (마이페이지 재확인 필요) ==================
    # "food_recall_domestic":  "<TBD — NO 339 식품의 회수 및 판매중지 정보>",
    # "food_recall_overseas":  "<TBD — NO 225 해외 위해식품 회수정보>",
    # "food_report":           "<TBD — NO 444 식품(첨가물)품목제조보고>",
    # "food_raw":              "<TBD — NO 470 식품(첨가물)품목제조보고(원재료)>",
    # "food_disc_service":     "<TBD — NO 477 행정처분결과(식품접객업)>",
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
    "food_recall_domestic": "I0490",

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
