# KD-IRIS — API 통합 레퍼런스

> **최종 갱신**: 2026-05-28 (검증 36/44 완전 작동, 실패 0)
> **출처**: `API_APPLICATION_LIST.md`(신청 목록) + `_verify_all_apis.py`(전수 검증) + data.go.kr 명세 페이지
> **검증 코드**: `python -m drug_integrated_search._verify_all_apis`

---

## 🔑 인증키 정보

### 공통 SERVICE_KEY (data.go.kr 계열 38개 API)
| 항목 | 값 |
|---|---|
| 환경변수 | `PUBLIC_DATA_SERVICE_KEY` |
| 발급처 | https://www.data.go.kr (공공데이터포털) |
| 보관 위치 | `.env` (gitignored, 로컬 전용) — 절대 git push 금지 |
| 호출 한도 | 개발계정 10,000회/일 |
| 유효기간 | 2026-05-26 ~ 2028-05-26 |
| 적용 API | NO 140·145·539·563·564·547·534·537·531·533 등 18개 작동 + 17개 신규 승인 |
| 로드 방식 | `config.py`에서 `python-dotenv` 자동 로드 |

### 식품안전나라 KeyID (별도 발급 필요)
| 항목 | 값 |
|---|---|
| 환경변수 | `FOODSAFETY_KEY_ID` |
| 현재 상태 | 미발급 (빈 문자열) |
| 발급처 | https://openapi.foodsafetykorea.go.kr |
| URL 패턴 | `http://openapi.foodsafetykorea.go.kr/api/{KEY_ID}/{SERVICE_ID}/{TYPE}/{START}/{END}` |
| 대기 API | NO 339(식품 회수·판매중지, serviceId `I0490`) 등 |

### B553748 카테고리 (한국식품안전관리인증원 — 동일 SERVICE_KEY 적용 확인)
| 항목 | 값 |
|---|---|
| Base | `https://apis.data.go.kr/B553748` |
| 인증 | `PUBLIC_DATA_SERVICE_KEY` 그대로 사용 |
| 적용 API | NO 12 스마트HACCP |

---

## 📐 파라미터 케이스 규칙 (검증 완료)

data.go.kr API는 케이스가 **API마다 다름**. 4종 패턴 혼재:

| 패턴 | 예시 | 적용 API |
|---|---|---|
| `snake_case` (소문자) | `item_name`, `entp_name`, `ingr_kor_name` | NO 140·145·563·142·144(상세)·483·485·554·562·568 |
| `camelCase` | `itemName`, `entpName`, `pageNo` | NO 248·269·531 |
| `UPPER_CASE` | `ITEM_NAME`, `BSSH_NM`, `PRCSCITYPOINT_BSSHNM` | NO 533·547·534·537·1·3·5·6·153·132·51 |
| `Pascal Case` | `Entrps`, `Induty`, `Prmisn_no` | NO 144 (목록) |
| 페이지/형식 (공통) | `pageNo`, `numOfRows`, `type` | 모든 API |

> ⚠ **NO 140 `item_seq` 파라미터는 무시됨** → 대안: `edi_code` 또는 `item_name` 사용
> ⚠ **R&D/BD 12개 API는 서버측 검색 무시** → `_client_filter()`로 클라이언트 필터링 필수

---

## 🔵 의약품 API (14개)

### NO 140 — 의약품 제품 허가정보 ⭐ 마스터
- **Base**: `apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07`
- **상태**: ✅ 완전 작동 (목록·상세·주성분 3 ops)

| op | 함수 | 파라미터 (snake) | 핵심 응답 필드 |
|---|---|---|---|
| 목록 | `getDrugPrdtPrmsnInq07` | `item_name`, `entp_name`, `edi_code`, `bar_code` | `ITEM_SEQ`, `ITEM_NAME`, `ENTP_NAME`, `ITEM_PERMIT_DATE`, `INDUTY`, `PRDUCT_TYPE`, `PRDUCT_PRMISN_NO` |
| 상세 | `getDrugPrdtPrmsnDtlInq06` | + `item_seq`, `bar_code`, `bizrno`, `atc_code`, `rare_drug_yn` | `MATERIAL_NAME`, `VALID_TERM`, `REEXAM_DATE`, `ATC_CODE`, `CHART`, `PACK_UNIT`, `STORAGE_METHOD`, `EE_DOC_DATA`(효능), `UD_DOC_DATA`(용법), `NB_DOC_DATA`(주의), `RARE_DRUG_YN`, `NARCOTIC_KIND_CODE` |
| 주성분 | `getDrugPrdtMcpnDtlInq07` | `item_name`, `entp_name` | `ENTRPS`, `PRDUCT`, `MTRAL_NM`(주성분명), `MTRAL_CODE`, `QNT`, `INGD_UNIT_CD` |

코드: `api_client.fetch_approval()` / `fetch_approval_detail()` ([api_client.py](api_client.py))

---

### NO 539 — 의약품 회수·판매중지 정보
- **Base**: `apis.data.go.kr/1471000/MdcinRtrvlSleStpgeInfoService04`
- **상태**: ✅ 완전 작동 (4 ops)

| op | 함수 | 파라미터 (snake) | 핵심 응답 필드 |
|---|---|---|---|
| 의약품 목록 | `getMdcinRtrvlSleStpgelList03` | `item_name`, `entp_name` | `PRDUCT`, `ENTRPS`, `RTRVL_RESN`(사유), `ENFRC_YN`, `RECALL_COMMAND_DATE`, `ITEM_SEQ`, `BIZRNO`, `STD_CD`(다중 표준코드, 쉼표 구분) |
| 의약품 상세 | `getMdcinRtrvlSleStpgeItem03` | `std_cd`, `item_seq` | + `ENTRPS_ADRES`, `ENTRPS_TELNO`, `MNFCTUR_NO`, `USGPD`(유효기간), `PACKNG_UNIT`, `OPEN_END_DATE` |
| 의약품외 목록 | `getMdcinRtrvlSleStpgelEtcList02` | `item_name`, `entp_name` | `PRDUCT`, `ENTRPS`, `ENFRC_YN`, `RTRVL_CMMND_DT`(필드명 주의), `BIZRNO` |
| 의약품외 상세 | `getMdcinRtrvlSleStpgeEtcItem03` | `item_seq` | + `ENTRPS_ADRES`, `ENTRPS_TELNO`, `PACKNG_UNIT`, `RM`, `ITEM_SEQ` |

코드: `api_client.fetch_recall()` + `fetch_recall_detail()` + `fetch_recall_etc()` + `fetch_recall_etc_detail()`

---

### NO 564 — 의약품 행정처분 정보
- **Base**: `apis.data.go.kr/1471000/MdcinExaathrService04/getMdcinExaathrList04`
- **상태**: ✅ 작동, 광동제약은 처분 0건 (정상)

| 파라미터 (snake) | 핵심 응답 필드 (12개 검증) |
|---|---|
| `entp_name`, `item_name`, `order` (=Y) | `ADM_DISPS_SEQ`(처분일련번호), `ENTP_NAME`, `ADDR`, `ENTP_NO`, `ITEM_NAME`, `BEF_APPLY_LAW`(위반법명), `EXPOSE_CONT`(공표내용), `ADM_DISPS_NAME`(처분명), `LAST_SETTLE_DATE`(처분일), `ITEM_SEQ`, `RLS_END_DATE`, `BIZRNO` |

> ⚠ **이전 가정 오류**: `VIOLATION_DETAIL`/`DISPS_NAME`/`DISPS_DATE` (실제로는 위 필드명)

코드: `api_client.fetch_disciplinary()`

---

### NO 547 — 의약품 안전성서한
- **Base**: `apis.data.go.kr/1471000/DrugSafeLetterService02/getDrugSafeLetterList02`
- **상태**: ✅ 완전 작동

| 파라미터 (UPPER) | 핵심 응답 필드 (12개 검증) |
|---|---|
| `TITLE` | `SAFT_LETT_NO`(서한번호), `TITLE`, `PBANC_DIVS_CD`/`PBANC_DIVS_NM`(공고구분), `PBANC_YMD`(공고일), `RLS_BGNG_YMD`(공개시작일), `SUMRY_CONT`(요약), `PBANC_CONT`(상세), `INQ_CNT`(조회수), `RGSTN_ID`/`CHRG_DEP`(담당), `ATTACH_FILE_URL`(첨부 PDF) |

코드: `api_extras.fetch_drug_safety_letter()`

---

### NO 531 — DUR 품목정보 (9 ops)
- **Base**: `apis.data.go.kr/1471000/DURPrdlstInfoService03`
- **상태**: ✅ 9 ops 모두 등록
- **파라미터**: `itemName` (camelCase) — *서버는 UPPER도 수용*

| op | 함수 | 의미 |
|---|---|---|
| 병용금기 | `getUsjntTabooInfoList03` | 함께 복용 금지 조합 |
| 노인주의 | `getOdsnAtentInfoList03` | 노인 환자 주의 |
| DUR 품목 | `getDurPrdlstInfoList03` | DUR 적용 품목 마스터 |
| 특정연령대금기 | `getSpcifyAgrdeTabooInfoList03` | 영유아·청소년 금기 |
| 용량주의 | `getCpctyAtentInfoList03` | 1일 최대 용량 주의 |
| 투여기간주의 | `getMdctnPdAtentInfoList03` | 최대 투여 기간 |
| 효능군중복 | `getEfcyDplctInfoList03` | 동일 효능 중복 처방 |
| 서방정분할 | `getSeobangjeongPartitnAtentInfoList03` | 서방정 분할/분쇄 금지 |
| 임부금기 | `getPwnmTabooInfoList03` | 임산부 금기 |

응답 핵심: `DUR_SEQ`, `TYPE_CODE`/`TYPE_NAME`, `ITEM_NAME`, `ITEM_SEQ`, `MIX`, `INGR_CODE`, `INGR_ENG_NAME`, `PROHBT_CONTENT`

코드: `api_extras.fetch_dur_item(category=…)`

---

### NO 533 — DUR 성분정보 (7 ops)
- **Base**: `apis.data.go.kr/1471000/DURIrdntInfoService03`
- **상태**: ✅ 7 ops 모두 등록
- **파라미터**: `INGR_NAME` (UPPER)

| op | 함수 |
|---|---|
| 병용금기 | `getUsjntTabooInfoList02` |
| 특정연령대 | `getSpcifyAgrdeTabooInfoList02` |
| 임부금기 | `getPwnmTabooInfoList02` |
| 용량주의 | `getCpctyAtentInfoList02` |
| 투여기간 | `getMdctnPdAtentInfoList02` |
| 노인주의 | `getOdsnAtentInfoList02` |
| 효능군중복 | `getEfcyDplctInfoList02` |

응답 핵심: `TYPE_NAME`, `MIX_TYPE`, `INGR_CODE`, `INGR_KOR_NAME`, `INGR_ENG_NAME`, `PROHBT_CONTENT`

코드: `api_extras.fetch_dur_ingredient(category=…)`

---

### NO 534 — 의약품 생산·수입·공급중단 정보
- **Base**: `apis.data.go.kr/1471000/MdcinPrdctnIncmeSuplyService2/getMdcinPrdctnIncmeSuplyList`
- **상태**: ✅ 작동 (서버 검색 미지원 → 클라 필터)

| 파라미터 (UPPER, 서버 무시) | 핵심 응답 필드 (26개) |
|---|---|
| `ENTP_NAME`, `ITEM_NAME` | `REPORT_PGS_CODE`(처리상태), `SUSPEND_REPORT_SEQ`, `SUSPEND_REPORT_FLAG`(생산/수입), `SUPPLY_YN`, `ENTP_SEQ`/`ENTP_NAME`/`ENTP_NO`, `ITEM_SEQ`/`ITEM_NAME`/`EDI_CODE`, `LAST_SUPPLY_DATE`, `SUSPEND_DATE`(중단일), `INV_DATE`/`INV_QTY`(자사재고), `SUSPEND_REASON`(중단사유), `SUPPLY_PLAN`(공급재개계획), `OPEN_AGREE_YN_NM`, `BIZRNO` |

> ⚠ **이전 가정 오류**: `SUPPLY_STOP_DATE`/`STOCK_QUANTITY`/`STANDARD_CODE`/`EXPECTED_DATE`/`REASON` (실제는 위 필드명)

코드: `api_extras.fetch_drug_supply_stop()`

---

### NO 537 — 의약품 공급부족 정보
- **Base**: `apis.data.go.kr/1471000/MdcinSuplyLackService03/getMdcinSuplyLackList01`
- **상태**: ✅ 작동

| 파라미터 (UPPER, 서버 무시) | 핵심 응답 필드 (23개) |
|---|---|
| `ENTP_NAME`, `ITEM_NAME` | `REPORT_PGS_CODE`, `SHORT_SUPPLY_REPORT_SEQ`, `ENTP_NAME`, `ITEM_NAME`, `EDI_CODE`, `SHORT_SUPPLY_EXPT_DATE`(예상일), `SHORT_SUPPLY_REASON`(부족사유), `LAST_SUPPLY_DATE`, `INV_QTY`(재고), `TREATMENT_INFU`(대체약), `SUPPLY_PLAN`(재개계획), `SUPPLY_PLAN_DATE`, `BIZRNO` |

코드: `api_extras.fetch_drug_supply_lack()`

---

### NO 563 — 의약품 낱알식별 정보
- **Base**: `apis.data.go.kr/1471000/MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03`
- **상태**: ✅ 완전 작동

| 파라미터 (snake) | 핵심 응답 필드 |
|---|---|
| `item_name`, `entp_name`, `item_seq` | `ITEM_SEQ`, `ITEM_NAME`, `ENTP_SEQ`, `ENTP_NAME`, `DRUG_SHAPE`(모양), `COLOR_CLASS1`(색), `PRINT_FRONT`/`PRINT_BACK`(식별표시), `ITEM_IMAGE`(URL), `BIG_PRDT_IMG_URL` |

코드: `api_client.fetch_identification()`

---

### NO 132 — 의약품 GMP 적합판정서 (2026-05-27 승인)
- **Base**: `apis.data.go.kr/1471000/DrugGmpStbltJgmtIssuStusService/getDrugGmpStbltJgmtIssuStusInq`
- **상태**: ✅ 작동 (광동제약 평택공장 검증값: `VLD_PRD_YMD=2027-03-28`)

| 파라미터 (UPPER) | 핵심 응답 필드 |
|---|---|
| `BSSH_NM` | `BSSH_NM`, `FCTR_ADDR`(공장주소), `KGMP_BGMP_NAME`(완제/원료구분), `GMP_INGR_MM_GROUP_NAME`(제형군), `VLD_PRD_YMD`(유효기간 만료) |

코드: `api_extras.fetch_drug_gmp(entp_name="광동제약")`

---

### NO 142 — 의약품 국가출하승인 정보
- **Base**: `apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService/getDrugNatnShipmntAprvInfoInq`
- **상태**: ✅ 작동

| 파라미터 (snake) | 핵심 응답 필드 |
|---|---|
| `goods_name`, `manuf_entp_name` | `RECEIPT_NO`, `SAMPLE_TYPE`, `GOODS_NAME`, `MANUF_ENTP_NAME`, `MAKE_NO`(제조번호), `RESULT_TIME`, `PROVT_UNIT`(검정규격), `VALID_TERM` |

> ⚠ **이전 가정 오류**: `goodsName`/`manufEntpName` (camelCase) → 명세는 snake_case

코드: `api_extras.fetch_drug_release()`

---

### NO 144 — 의약품 등 업체허가현황 (목록 + 상세)
- **Base**: `apis.data.go.kr/1471000/DrugEtcBsshBspmStusService`

| op | 파라미터 | 핵심 응답 필드 |
|---|---|---|
| 목록 `getDrugBsshListInq` | `Entrps`, `Induty` (Pascal) | `INDUTY`(업종), `ENTRPS`(업체명), `RPRSNTV`(대표자), `PRMISN_DT`(허가일), `ADRES`, `PRMISN_NO`, `BIZRNO` |
| 상세 `getDrugBsshItemInq` | `Prmisn_no` | 상세 품목 리스트 |

코드: `api_extras.fetch_drug_entity_list()` / `fetch_drug_entity_detail()`

---

### NO 248 — e약은요 (개요정보)
- **Base**: `apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList`
- **상태**: ✅ 완전 작동

| 파라미터 (camelCase) | 핵심 응답 필드 |
|---|---|
| `itemName`, `entpName`, `itemSeq` | `entpName`, `itemName`, `itemSeq`, `efcyQesitm`(효능), `useMethodQesitm`(용법), `atpnWarnQesitm`/`atpnQesitm`(주의), `intrcQesitm`(상호작용), `seQesitm`(부작용), `depositMethodQesitm`(보관), `itemImage` |

코드: `api_extras.fetch_drug_easy()`

---

### NO 269 — 묶음의약품정보 (HIRA/ATC 매핑)
- **Base**: `apis.data.go.kr/1471000/DrbBundleInfoService02/getDrbBundleList02`
- **상태**: 🟡 데이터 0건 (HIRA 처방의약품 위주, 일반의약품 미등록 — 정상)

| 파라미터 (camelCase) | 응답 필드 |
|---|---|
| `trustItemName`, `trustMainingr`, `atcCode` | `trustItemName`, `trustMainingr`, `trustItemSeq`, `consignItemName`, `atcCode` |

코드: `api_extras.fetch_drug_bundle()`

---

### NO 483 — 원료의약품등록(DMF) 현황
- **Base**: `apis.data.go.kr/1471000/MdcDmfInfoService01/getMdcDmfList01`

| 파라미터 (snake) | 핵심 응답 필드 |
|---|---|
| `ingr_kor_name`, `entp_name` | `DMF_PERMIT_NO`, `INGR_KOR_NAME`, `ENTP_NAME`, `MNFCTR_NAME`(제조소), `MNFCTR_PLACE`, `MANUF_COUNTRY_CODE_NM`, `DMF_PERMIT_DATE` |

> ⚠ 이전 가정: `INGR_KOR_NAME`/`MNFCTR_NAME` (UPPER) + `manufacturer` 인자가 잘못된 키에 묶임

코드: `api_extras.fetch_drug_dmf()`

---

## 🟠 R&D / BD / 안전성 API (11개) — 서버 검색 무시, 클라 필터링 필수

### NO 561 — 의약품 특허정보 (대용량 120,525건)
- **Base**: `apis.data.go.kr/1471000/MdcinPatentInfoService2/getMdcinPatentInfoList2`
- **상태**: ✅ 작동, `num_of_rows=50` 캡 권장
- **파라미터**: `ITEM_NAME`, `applicant` (서버 무시)
- **응답**: `INGR_ENG_NAME`, `INGR_NAME`, `ITEM_ENG_NAME`, `ITEM_NAME`, `ENTP_NAME`, `SHAPE`, `CONT_QY`, `CLASS_NO`

### NO 557 — 국내소송 의약품(특허)
- **Base**: `apis.data.go.kr/1471000/DmstcLwstMdcinInfoService02/getMdcinRefreeSttusList02`
- **파라미터**: `PRT_NAME`, `INGR_NAME` (UPPER, 노출)
- **응답**: `INGR_NAME`, `PRT_NAME`, `JUDGMENT_KIND`(심결구분), `KOR_PAT_NO`(특허번호), `SIGN_OF_CASE`(사건부호), `JUDGMENT_REQUEST_DATE`, `JUDGMENT_DECISION_DATE`, `REASON_OF_REQUEST`

### NO 552 — FDA Paragraph IV 대상 의약품 특허
- **Base**: `apis.data.go.kr/1471000/ParagraphIVTrgetMdcinService02/getParagraphIVSearchsList02`
- **파라미터**: `DRUG_NAME`
- **응답**: `DRUG_NAME`, `DOSAGE_FORM`, `STRENGTH`, `RLD`

### NO 562 — FDA 오렌지북 특허정보
- **Base**: `apis.data.go.kr/1471000/FdaOrngbkPatentInfoService01/getFdaOrngbkPatentInfoList01`
- **파라미터** (snake): `ingr_name`, `prt_name`
- **응답**: `INGR_NAME`, `PRT_NAME`, `KOR_APPLY_NO`, `KOR_PAT_NO`, `KOR_NAME_OF_INVENTION`, `KOR_APPLICANT`, `KOR_EXP_DATE`(만료일), `KOR_STATUS`

### NO 566 — 의약품 임상시험 정보
- **Base**: `apis.data.go.kr/1471000/MdcinClincTestInfoService02/getMdcinClincTestInfoList02`
- **파라미터**: `GOODS_NAME`, `APPLY_ENTP_NAME` (서버 무시)
- **응답**: `APPLY_ENTP_NAME`(신청업체), `APPROVAL_TIME`, `LAB_NAME`, `GOODS_NAME`, `CLINIC_EXAM_TITLE`(임상명), `CLINIC_STEP_NAME`(단계), `CLNC_TEST_SN`

### NO 568 — 의약품 임상시험 실시기관
- **Base**: `apis.data.go.kr/1471000/ClinicTestOprtnInsttInfoService01/getClinicTestOprtnInsttInfo01`
- **파라미터** (snake): `lab_name`
- **응답**: `LAB_SEQ`, `LAB_NAME`, `BOSS_NAME`, `APPOINT_DATE`, `EXAM_COMMT_GB_NAME`, `ADDR1`

### NO 484 — 대조약 조회
- **Base**: `apis.data.go.kr/1471000/MdcCompDrugInfoService04/getMdcCompDrugList04`
- **파라미터**: `INGR_NAME`, `ITEM_NAME` (서버 무시)
- **응답**: `INGR_NAME`, `ITEM_NAME`, `ENTP_NAME`, `SHAPE_CODE_NAME`, `BIOEQ_NOTICE_DATE`, `BIZRNO`, `ITEM_SEQ`

### NO 485 — 생동성 인정품목 조회
- **Base**: `apis.data.go.kr/1471000/MdcBioEqInfoService01/getMdcBioEqList01`
- **파라미터** (snake, 단일): `item_name`
- **응답**: `ITEM_SEQ`, `ITEM_NAME`, `ENTP_NAME`, `INGR_KOR_NAME`, `INGR_QTY`, `SHAPE_CODE_NAME`, `BIOEQ_PRODT_NOTICE_DATE`

### NO 554 — 의약품 재심사 정보 (대용량 112,554건)
- **Base**: `apis.data.go.kr/1471000/MdcinRejdgeService01/getMdcinRdjdgeList01`
- **파라미터** (snake): `entp_name`, `item_name`, `item_no` — `num_of_rows=50` 권장
- **응답**: `ENTP_NAME`, `FACTORY_ADDR`, `BOSS_NAME`, `ITEM_NAME`, `REPORT_FLAG_NM`, `CLASS_NO_NM`, `ITEM_NO`, `REEXAM_START_DATE`, `REEXAM_CODE_NM`, `YEAR_REPORT_DEADLINE_DATE`, `RESULT_DATE`, `BIZRNO`

### NO 556 — 의약품 재평가 정보 (대용량 64,827건)
- **Base**: `apis.data.go.kr/1471000/MdcinRevalService02/getMdcinRevalList02`
- **파라미터**: `ENTP_NAME`, `ITEM_NAME` (UPPER, 서버 무시) — `num_of_rows=50` 권장
- **응답**: `ENTP_NAME`, `ENTP_NO`, `BOSS_NAME`, `ITEM_NAME`, `CLASS_NO_NM`, `ITEM_NO`, `ITEM_PERMIT_DATE`, `SUBMIT_DOC_CODE_NM`

### NO 565 — 희귀의약품 정보
- **Base**: `apis.data.go.kr/1471000/RareMdcinInfoService02/getRareMdcinList02`
- **파라미터** (camelCase, 서버 무시): `productName`, `targetDisease`
- **응답** (대문자!): `PRODT_NAME`(제품명, 요청 키와 다름!), `RARITY_DRUG_APPOINT_NO`, `TARGET_DISEASE`, `APPOINT_DATE`, `DEVSTEP_YN`

---

## 🟣 희귀필수의약품 (NO 81 — 5 ops)

- **Base**: `apis.data.go.kr/1471000/RareEsentMdcin`
- **상태**: 🟡 카테고리별 데이터 변동 (자가치료용 0건 = 정상)

| op | 함수 | 의미 |
|---|---|---|
| 자가치료용 | `getRareNartDrugSelftreat` | 자가치료용 마약류 |
| 치료용 | `getRareSelfmdcin` | 일반 치료용 |
| 보험미등재 | `getRareEmerIntdInsurceUnregistMdcin` | 긴급도입 보험 미등재 |
| 보험등재 | `getRareEmerIntdInsurceRegistMdcin` | 긴급도입 보험 등재 |
| 마약류 긴급 | `getRareEmerIntdNarticDrug` | 긴급도입 마약류 |

응답 핵심: `INGR`(성분), `MEDCIN_NAME`(약품명)

코드: `api_extras.fetch_rare_essential(category="treat"|"self"|"unreg"|"reg"|"narc")`

---

## 🟡 의약외품 (1개)

### NO 145 — 의약외품 제품 허가 정보
- **Base**: `apis.data.go.kr/1471000/QdrgPrdtPrmsnInfoService03/getQdrgPrdtPrmsnInfoInq03`
- **상태**: ✅ 작동 (총 22,986건)

| 파라미터 (snake) | 핵심 응답 필드 |
|---|---|
| `item_name`, `entp_name` | `ITEM_SEQ`, `ITEM_NAME`, `ENTP_NAME`, `ITEM_PERMIT_DATE`, `ITEM_NO`, `CANCEL_CODE_NAME`(폐업/취소 상태), `CANCEL_DATE`, `ADIT_INGR`(첨가제) |

코드: `api_extras.fetch_quasi_approval()`

---

## 🟢 식품 API (5개 작동 + 5개 End Point 대기)

### NO 1 — 식품영양성분 DB
- **Base**: `apis.data.go.kr/1471000/FoodNtrCpntDbInfo02/getFoodNtrCpntDbInq02`

| 파라미터 (UPPER) | 핵심 응답 필드 |
|---|---|
| `FOOD_NM_KR`, `BSSH_NM` | `NUM`, `FOOD_CD`, `FOOD_NM_KR`(식품명), `DB_GRP_CM`/`DB_GRP_NM`(분류군), `DB_CLASS_CM`/`DB_CLASS_NM`, `MAKER_NAME`, `AMT_NUM1`, `NUTR_CONT1` |

### NO 3 — 행정처분 (수입식품업)
- **Base**: `apis.data.go.kr/1471000/AdmmRsltIprtFoodService/getAdmmRsltIprtFoodService`
- **파라미터**: `PRCSCITYPOINT_BSSHNM`
- **응답**: `PRCSCITYPOINT_BSSHNM`(업체명), `INDUTY_CD_NM`(업종), `LCNS_NO`(허가번호), `DSPS_DCSNDT`(처분일), `DSPS_BGNDT`/`DSPS_ENDDT`, `DSPS_TYPECD_NM`(처분유형), `VILTCN`(위반내용)

### NO 5 — 행정처분 (식품판매업)
- **Base**: `apis.data.go.kr/1471000/AdmmRsltFoodSaleService/getAdmmRsltFoodSaleBssh`
- **파라미터/응답**: NO 3과 동일 스키마

### NO 6 — 행정처분 (식품제조가공업)
- **Base**: `apis.data.go.kr/1471000/AdmmRsltFoodMnftPrcsService/getAdmmRsltFoodMnftPrcsBssh`
- **파라미터/응답**: NO 3과 동일 스키마

### NO 153 — 수입식품 회수판매중지 제품정보
- **Base**: `apis.data.go.kr/1471000/IprtFoodReclSaleStopPrdtStusService/getIprtFoodReclSaleStopPrdtStusInq`

| 파라미터 (UPPER) | 핵심 응답 필드 |
|---|---|
| `PRDT_NM`, `CLNT_BSSH_NM`(업체명), `BRCD_NO`(바코드) | `PRDT_NM`(제품명), `CLNT_BSSH_NM`, `MNFT_YMD_RLAT_CONT`(제조일자), `CIRC_PRD`(유통기한), `RECL_RESN_CONT`(회수사유), `RECL_MTH_CONT`(회수방법), `PRMT_NO`, `PRCS_POTM_DTL_ADDR`(주소), `BRCD_NO`, `PCKN_UNIT_INFO`(포장단위), `RECL_COMND_DT`(등록일), `RECL_GRAD_CD_NM`(회수등급), `PRDLST_NM`(식품분류) |

### NO 535 — 검사 부적합 식품정보 (목록 + 상세)
- **Base**: `apis.data.go.kr/1471000/PrsecImproptFoodInfoService03`

| op | 파라미터 | 핵심 응답 필드 |
|---|---|---|
| 목록 `getPrsecImproptFoodList01` | `PRDUCT` | `PRDUCT`(제품), `ENTRPS`(업체), `IMPROPT_ITM`(부적합 사유), `REGIST_DT`(등록일) |
| 상세 `getPrsecImproptFoodItem02` | `PRSEC_NO` | + `FOOD_TY`(식품유형), `ADRES1`, `DISTB_PD`(유통기한), `INSPCT_INSTT`(검사기관), `TEL_NO` |

### NO 12 — 식품 스마트HACCP 인증업체 (B553748 카테고리)
- **Base**: `apis.data.go.kr/B553748/SmartCertFoodListService/getFoodList`
- **인증**: PUBLIC_DATA_SERVICE_KEY 동일 적용
- **파라미터**: `businessnm` (소문자 단어)
- **응답**: `rnum`, `appointno`(인증번호), `businessnm`(품목), `appointyn`(인증여부), `licenseno`(허가번호), `company`(회사명), `ceoname`(대표자), `sido`(시도)

### NO 51 — 건강기능식품 GMP 지정현황
- **Base**: `apis.data.go.kr/1471000/FoodGmpStbltCompInfo/getFoodGmpStbltCompInfo`
- **파라미터**: `BSSH_NM`
- **응답**: `LCNS_NO`(인허가번호), `BSSH_NM`(업소명), `INDUTY_CD_NM`(업종), `PRSDNT_NM`(대표자), `SITE_ADDR`(소재지), `INSTT_CD_NM`(인허가기관), `CLSBIZ_DVS_CD_NM`(영업상태)

---

## ⏳ End Point 확인 대기 (5개)

마이페이지 → 개발계정 → "상세보기"에서 End Point 확인 후 `config.py:163-168` 의 주석 해제 + smoke test 필요.

| NO | 서비스 | URL |
|---|---|---|
| 339 | 식품의 회수 및 판매중지 정보 (식품안전나라 `I0490`) | https://www.data.go.kr/data/15074318/openapi.do |
| 225 | 해외 위해식품 회수정보 | https://www.data.go.kr/data/15077772/openapi.do |
| 477 | 행정처분결과(식품접객업) | https://www.data.go.kr/data/15058429/openapi.do |
| 444 | 식품(첨가물) 품목제조보고 | https://www.data.go.kr/data/15064909/openapi.do |
| 470 | 식품(첨가물) 품목제조보고(원재료) | https://www.data.go.kr/data/15062098/openapi.do |

---

## 📊 응답 공통 메시지 형식 (모든 data.go.kr API)

```xml
<response>
  <header>
    <resultCode>00</resultCode>            <!-- 00=정상, 99=실패 -->
    <resultMsg>NORMAL SERVICE.</resultMsg>
  </header>
  <body>
    <items>
      <item>...</item>
    </items>
    <totalCount>...</totalCount>
    <numOfRows>...</numOfRows>
    <pageNo>...</pageNo>
  </body>
</response>
```

`api_client._parse_xml_response()` 가 `{items, totalCount}` dict로 정규화.

---

## 📌 데이터 0건 = 정상 케이스 (graceful 처리 필수)

다음은 API 정상 호출 + 결과 0건이 *예상되는* 케이스. 에러로 표시하지 말 것:

| NO | 상황 |
|---|---|
| 269 묶음의약품 | HIRA 처방의약품 중심, 일반의약품(타이레놀·베니톨) 미등록 |
| 531 DUR 병용금기 | 일반의약품은 대부분 등록 안 됨 |
| 81 자가치료용 마약 | 전체 카테고리 0건 |
| 564 행정처분 (광동제약 조회) | 광동제약 처분 이력 없음 |
| 539 회수 (베니톨정 조회) | 베니톨정은 회수 이력 없음 |

---

## 🔧 운영 팁

- **대용량 API** (NO 561·554·556) 호출 시 `num_of_rows=50` 캡 — 메모리/응답시간 보호
- **서버 검색 무시** API는 `_client_filter()`로 클라이언트 사이드 필터링 (about 12 APIs)
- **타임아웃**: `REQUEST_TIMEOUT=30s` (`config.py:216`)
- **SSL 검증**: Windows 환경에서 `VERIFY_SSL=False` 권장 (config.py:221)
- **캐시**: `watchlist_match._cached()` 5분 TTL 인메모리 캐시
- **로그**: `logs/` 디렉토리에 daily rotate

---

## 🧪 전수 검증 실행

```bash
cd C:/Users/user/Desktop/Coding/cusor
python -m drug_integrated_search._verify_all_apis
```

최근 결과 (2026-05-28): **완전 작동 36 / 부분/0건 8 / 실패 0 / 전체 44**
