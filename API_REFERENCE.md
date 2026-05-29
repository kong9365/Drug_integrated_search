# KD-IRIS — API 통합 레퍼런스

> **최종 갱신**: 2026-05-29 (식품안전나라 KeyID 활성화 + 한약 NO35/90 승인 반영 + 화면 연결 현황 추가)
> **출처**: `API_APPLICATION_LIST.md`(신청 목록) + `_verify_all_apis.py`(전수 검증) + data.go.kr 명세 페이지
> **검증 코드**: `python -m drug_integrated_search._verify_all_apis`
>
> **변경 요약 (2026-05-29)**:
> - `FOODSAFETY_KEY_ID` **발급·활성** → 식품안전나라 라인 가동(회수 I0490·접객업처분 I2630·해외위해 I2810 + 건기식 개별인정형 I-0050·영양DB I0760·품목제조 I0030·식품공전 I0930)
> - 한약(생약) **NO 35 허가기원·NO 90 회수** 승인 등록 (동일 `PUBLIC_DATA_SERVICE_KEY`)
> - 미연결 API 다수 화면 연결: 의약품외 회수(539)·희귀필수(81)·임상기관(568)
> - 하단 **"🔌 현재 통합·활용 현황"** 표에서 API별 연결 화면·상태 확인

---

## 🔑 인증키 정보

### 공통 SERVICE_KEY (data.go.kr 계열 40+ API)
| 항목 | 값 |
|---|---|
| 환경변수 | `PUBLIC_DATA_SERVICE_KEY` |
| 발급처 | https://www.data.go.kr (공공데이터포털) |
| 키 식별자 | `5cd…d1` (마이페이지 16자 prefix — 전체 키는 .env에서만 관리) |
| 보관 위치 | `.env` (gitignored, 로컬 전용) — 절대 git push 금지 |
| 호출 한도 | 개발계정 **10,000회/일/API** (활용신청 표 일괄 확인) |
| 신청 유형 | 개발계정 / 활용신청 / **자동 승인** |
| 서비스 유형 | REST |
| 데이터 포맷 | JSON+XML (NO 484·485·483 등 일부는 XML only) |
| 활용기간 | API별 상이 — 2025-05-13(NO 539)·2025-07-03(NO 564)·2025-10-31(NO 140)·2025-11-13(NO 145·563)·2026-05-26·2026-05-27 |
| 적용 API | 작동 18개 + 2026-05-26~27 신규 승인 22개 + 식품공전·건기식 4개 |
| 로드 방식 | `config.py`에서 `python-dotenv` 자동 로드 |
| 활용 목적 | 의약품/식품 규제정보 통합 조회 시스템 개발 및 PoC |

### 식품안전나라 KeyID (별도 발급)
| 항목 | 값 |
|---|---|
| 환경변수 | `FOODSAFETY_KEY_ID` |
| 현재 상태 | **발급·활성 (라이브 작동 확인 2026-05-29)** — 키는 `.env`에만 보관 |
| 활성 서비스 | `I0490`(회수 350)·`I2630`(접객업처분 2,904)·`I2810`(해외위해)·`I-0050`(개별인정형 430)·`I0760`(영양DB 585)·`I0030`(품목제조 44,832)·`I0930`(식품공전, 품목명 검색형) |
| 발급처 | https://openapi.foodsafetykorea.go.kr |
| 신청 페이지 | https://www.foodsafetykorea.go.kr/api/openApiInfo.do (회원가입 후 OpenAPI 이용신청) |
| URL 패턴 | `http://openapi.foodsafetykorea.go.kr/api/{KEY_ID}/{SERVICE_ID}/{TYPE}/{START}/{END}[/{변수}={값}&{변수}={값}]` |
| 지원 데이터 포맷 | xml, json |
| 가용 API | **97개 OPEN-API 전수 명세 수집 완료** (식약처 ORGN01 카테고리) — 본 문서 하단 "🍜 식품안전나라 OPEN-API" 섹션 |
| 핵심 API | `I0490`(회수·판매중지)·`I0470`/`I0480`/`I0481`/`I0482`/`I2630`(행정처분 5종)·`I0580`(HACCP)·`I2620`(검사부적합)·`I2810`(해외위해)·`I2791`(영양DB)·`I-0050`(건기식 개별인정형) 등 |

### B553748 카테고리 (한국식품안전관리인증원 — 동일 SERVICE_KEY 적용 확인)
| 항목 | 값 |
|---|---|
| Base | `https://apis.data.go.kr/B553748` |
| 인증 | `PUBLIC_DATA_SERVICE_KEY` 그대로 사용 |
| 적용 API | NO 12 스마트HACCP |

---

## 🔌 현재 통합·활용 현황 (2026-05-29)

> 키·엔드포인트는 **전부 등록·인증되어 호출 가능**. 아래는 실제 **화면 연결(활용)** 기준 현황.
> **범례** — ✅ 화면 연결됨 · ⚪ 함수 보유(미연결) · ⚠️ 응답 대기(승인 전파 등)

### 의약품 (data.go.kr · `PUBLIC_DATA_SERVICE_KEY`)
| NO | 서비스 | fetch 함수 | 연결 화면 | 상태 |
|----|--------|-----------|-----------|:---:|
| 140 | 허가 목록 | `fetch_approval` | 검색·제품상세 | ✅ |
| 140 | 허가 상세 | `fetch_approval_detail` | 제품상세(허가상세) | ✅ |
| 140 | 주성분 상세 | `fetch_approval_ingr` | (MATERIAL_NAME 파싱으로 대체) | ⚪ |
| 564 | 행정처분 | `fetch_disciplinary` | 모니터·검색·제품상세 신호등 | ✅ |
| 539 | 회수 목록 | `fetch_recall` | 모니터·검색·제품상세·워치리스트 | ✅ |
| 539 | 의약품외 회수 목록 | `fetch_recall_etc` | 모니터 | ✅ |
| 539 | 회수/의약품외 상세 | `fetch_recall_detail`·`fetch_recall_etc_detail` | (드릴다운용) | ⚪ |
| 563 | 낱알식별 | `fetch_identification` | 제품상세(낱알) | ✅ |
| 547 | 안전성서한 | `fetch_drug_safety_letter` | 모니터·검색·제품상세·워치리스트 | ✅ |
| 534 | 공급중단 | `fetch_drug_supply_stop` | 모니터·검색·제품상세 | ✅ |
| 537 | 공급부족 | `fetch_drug_supply_lack` | SCM 워크스페이스 | ✅ |
| 531 | DUR 품목(병용·임부·노인) | `fetch_dur_item` | 제품상세 안전성 탭 | ✅ |
| 533 | DUR 성분 | `fetch_dur_ingredient` | (531 품목으로 충족) | ⚪ |
| 248 | e약은요 | `fetch_drug_easy` | 검색·제품상세 | ✅ |
| 269 | 묶음의약품 | `fetch_drug_bundle` | 제품상세 | ✅ |
| 132 | GMP 적합판정 | `fetch_drug_gmp` | 홈·제품상세·RA 워크스페이스 | ✅ |
| 142 | 국가출하승인 | `fetch_drug_release` | 검색·제품상세 | ✅ |
| 144 | 업체허가 목록 | `fetch_drug_entity_list` | 검색 | ✅ |
| 144 | 업체허가 상세 | `fetch_drug_entity_detail` | — | ⚪ |
| 483 | 원료의약품 DMF | `fetch_drug_dmf` | 검색·제품상세·SCM | ✅ |
| 561 | 의약품 특허 | `fetch_drug_patent` | 검색·제품상세 | ✅ |
| **557** | **국내소송 의약품(특허)** | `fetch_drug_lawsuit` | **R&D 특허 트래커·제품상세** | ✅ |
| 552 | FDA Paragraph IV | `fetch_drug_fda_p4` | R&D 트래커·검색·제품상세 | ✅ |
| 562 | FDA 오렌지북 | `fetch_drug_fda_orangebook` | R&D 트래커·검색·제품상세 | ✅ |
| 566 | 임상시험 | `fetch_drug_clinical` | 모니터·검색·제품상세 | ✅ |
| 568 | 임상시험 실시기관 | `fetch_drug_clinical_org` | R&D 워크스페이스 | ✅ |
| 484 | 대조약 | `fetch_drug_reference` | 검색·제품상세 | ✅ |
| 485 | 생동성인정품목 | `fetch_drug_bioeq` | 검색·제품상세 | ✅ |
| 554 | 재심사 | `fetch_drug_review` | 모니터·검색·제품상세·홈·RA D-Day | ✅ |
| 556 | 재평가 | `fetch_drug_reeval` | 모니터·검색·제품상세 | ✅ |
| 565 | 희귀의약품 | `fetch_drug_orphan` | 검색·제품상세 | ✅ |
| 81 | 희귀필수의약품(5종) | `fetch_rare_essential` | R&D 워크스페이스 | ✅ |

### 의약외품 / 식품 (data.go.kr)
| NO | 서비스 | fetch 함수 | 연결 화면 | 상태 |
|----|--------|-----------|-----------|:---:|
| 145 | 의약외품 허가 | `fetch_quasi_approval` | 의약외품 제품상세·자사 enrichment | ✅ |
| 1 | 식품영양성분DB | `fetch_food_nutrition` | 검색 | ✅ |
| 3·5·6 | 식품 행정처분(수입·판매·제조) | `fetch_food_disc` | 식품QA 워크스페이스 | ✅ |
| 153 | 수입식품 회수 | `fetch_food_recall_import` | 검색·식품 제품상세 | ✅ |
| 535 | 검사부적합 목록 | `fetch_food_inspect` | 검사부적합 페이지·모니터 | ✅ |
| 535 | 검사부적합 상세 | `fetch_food_inspect_detail` | — | ⚪ |
| 51 | 건강기능식품 GMP | `fetch_hf_gmp` | 검색 | ✅ |
| 12 | 스마트HACCP | `fetch_haccp_smart` | 검색 | ✅ |

### 식품안전나라 (`FOODSAFETY_KEY_ID` · 활성)
| serviceId | 서비스 | fetch 함수 | 연결 화면 | 상태 |
|-----------|--------|-----------|-----------|:---:|
| I-0050 | 건기식 개별인정형 | `fetch_hf_individual` | 식품QA | ✅ |
| I0760 | 건기식 영양DB 분류 | `fetch_hf_nutrition` | 식품QA | ✅ |
| I0030 | 건기식 품목제조 신고 | `fetch_hf_report` | 식품QA | ✅ |
| I0930 | 식품공전 기준규격 | `fetch_food_code` | 식품QA(품목명 검색형) | ✅ |
| I0490 | 식품 회수·판매중지 | `fetch_food_recall_domestic` | (data.go.kr 동등본 사용) | ⚪ |
| I2810 | 해외 위해식품 회수 | `fetch_food_recall_overseas` | — | ⚪ |
| I2630 | 행정처분(식품접객업) | `fetch_food_disc_service` | — | ⚪ |
| I1250·C002 | 식품(첨가물) 품목제조보고 | `fetch_food_report`·`_raw` | — | ⚪ |

### 한약(생약) (2026-05-29 승인 · `PUBLIC_DATA_SERVICE_KEY`)
| NO | 서비스 | 엔드포인트 | fetch 함수 | 연결 화면 | 상태 |
|----|--------|-----------|-----------|-----------|:---:|
| 90 | 한약제제 회수·판매중지 | `1471000/HerbRtrvlSleStpgeInfo` | `fetch_herbal_recall` | 모니터(한약 회수, 290건) | ✅ |
| 35 | 한약제제 허가 기원 | `1471057/HbmdMdctPrmsnOrigInfoService` | `fetch_herbal_approval` | RA 워크스페이스(생약명 검색) | ⚠️ |

> ⚠️ **NO 35** — 엔드포인트·키 정상 등록. 단, 2026-05-29 승인 직후 접근 시 **403 Forbidden**(승인 전파 지연 추정). 화면은 graceful 안내 처리. 전파 후 자동 작동.
> 파라미터 — NO 35: `DRNM`(생약명)·`TXNGRP_NM`(동식물명) / NO 90: `ITEM_NAME`·`ENTP_NAME` (응답 `DISPS_CONT` 회수사유).

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

## ⏳ End Point 확인 대기 → 식품안전나라 serviceId 확정 (5개)

> 5개 모두 **식품안전나라(foodsafetykorea.go.kr)** 계열로 serviceId 확정됨. data.go.kr 키가 아닌 `FOODSAFETY_KEY_ID` 사용.
> 공통 URL 패턴: `http://openapi.foodsafetykorea.go.kr/api/{KEY_ID}/{serviceId}/{xml|json}/{startIdx}/{endIdx}[/{변수}={값}&{변수}={값}]`
> 공통 요청인자 5개: `keyId`·`serviceId`·`dataType`·`startIdx`·`endIdx` (이하 추가 파라미터만 명시)
> 코드: `config.py:FOODSAFETY_SERVICES` 등록 + `api_extras.fetch_foodsafety()` 호출

| NO | data.go.kr 원본 | serviceId | 코드 키 |
|---|---|---|---|
| 339 | https://www.data.go.kr/data/15074318/openapi.do | `I0490` | `food_recall_domestic` |
| 225 | https://www.data.go.kr/data/15077772/openapi.do | `I2810` | `food_recall_overseas` |
| 477 | https://www.data.go.kr/data/15058429/openapi.do | `I2630` | `food_disc_service` |
| 444 | https://www.data.go.kr/data/15064909/openapi.do | `I1250` | `food_report` |
| 470 | https://www.data.go.kr/data/15062098/openapi.do | `C002` | `food_report_raw` |

### `I0490` — 식품 회수·판매중지 정보 (NO 339)
- **추가 파라미터**: `CRET_DTM`(등록일자 YYYYMMDD) · `PRDLST_REPORT_NO`(품목제조보고번호)
- **응답 필드 (19)**: `PRDTNM`(제품명) / `RTRVLPRVNS`(회수사유) / `BSSHNM`(제조업체명) / `ADDR`(업체주소) / `TELNO`(전화번호) / `BRCDNO`(바코드) / `FRMLCUNIT`(포장단위) / `MNFDT`(제조일자) / `RTRVLPLANDOC_RTRVLMTHD`(회수방법) / `DISTBTMLMT`(유통/소비기한) / `PRDLST_TYPE`(식품분류) / `IMG_FILE_PATH`(제품사진 URL) / `PRDLST_CD`(품목코드) / `CRET_DTM`(등록일) / `RTRVLDSUSE_SEQ`(회수 일련번호) / `PRDLST_REPORT_NO`(품목제조보고번호) / `RTRVL_GRDCD_NM`(회수등급) / `PRDLST_CD_NM`(품목유형) / `LCNS_NO`(업체인허가번호)

### `I2810` — 해외 위해식품 회수정보 (NO 225)
- **추가 파라미터**: `ST_CRET_DTM`(생성일자 시작범위 YYYYMMDD) · `END_CRET_DTM`(생성일자 종료범위)
- **응답 필드 (6)**: `TITL`(제품명) / `DETECT_TITL`(유해물질) / `CRET_DTM`(생성일자) / `BDT`(본문내용) / `DOWNLOAD_URL`(이미지 다운로드 URL) / `NTCTXT_NO`(게시글번호)

### `I2630` — 행정처분결과(식품접객업) (NO 477)
- **추가 파라미터**: `CHNG_DT`(변경일자 — 기준 이후 자료) · `DSPS_DCSNDT`(확정일자) · `LCNS_NO`(인허가번호)
- **응답 필드 (17)**: `PRCSCITYPOINT_BSSHNM`(업소명) / `INDUTY_CD_NM`(업종) / `LCNS_NO`(인허가번호) / `DSPS_DCSNDT`(처분확정일) / `DSPS_BGNDT`(처분시작일) / `DSPS_ENDDT`(처분종료일) / `DSPS_TYPECD_NM`(처분유형) / `VILTCN`(위반일자·내용) / `ADDR`(주소) / `TEL_NO`(전화번호) / `PRSDNT_NM`(대표자명) / `DSPSCN`(처분내용) / `LAWORD_CD_NM`(위반법령) / `PUBLIC_DT`(공개기한) / `LAST_UPDT_DTM`(최종수정일) / `DSPS_INSTTCD_NM`(처분기관명) / `DSPSDTLS_SEQ`(전산키)

### `I1250` — 식품(첨가물) 품목제조보고 (NO 444)
- **추가 파라미터**: `CHNG_DT`(변경일자) · `PRDLST_REPORT_NO`(품목제조번호) · `BSSH_NM`(업소명) · `PRDLST_NM`(제품명) · `LCNS_NO`(인허가번호) · `PRMS_DT`(보고일자) · `PRDLST_DCNM`(품목유형명)
- **응답 필드 (18)**: `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `PRDLST_REPORT_NO`(품목제조번호) / `PRMS_DT`(허가일자) / `PRDLST_NM`(제품명) / `PRDLST_DCNM`(품목유형명) / `PRODUCTION`(생산종료여부) / `HIENG_LNTRT_DVS_NM`(고열량저영양여부) / `CHILD_CRTFC_YN`(어린이기호식품 품질인증) / `POG_DAYCNT`(소비기한) / `LAST_UPDT_DTM`(최종수정일) / `INDUTY_CD_NM`(업종) / `QLITY_MNTNC_TMLMT_DAYCNT`(품질유지기한) / `USAGE`(용법) / `PRPOS`(용도) / `DISPOS`(제품형태) / `FRMLC_MTRQLT`(포장재질) / `ETQTY_XPORT_PRDLST_YN`(내수/겸용)

### `C002` — 식품(첨가물) 품목제조보고(원재료) (NO 470)
- **추가 파라미터**: `CHNG_DT`(변경일자) · `PRDLST_REPORT_NO`(품목제조번호) · `PRDLST_NM`(품목명) · `BSSH_NM`(업소명) · `LCNS_NO`(인허가번호) · `RAWMTRL_NM`(원재료명) · `PRMS_DT`(보고일자) · `PRDLST_DCNM`(품목유형명)
- **응답 필드 (10)**: `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `PRDLST_REPORT_NO`(품목제조번호) / `PRMS_DT`(보고일자) / `PRDLST_NM`(품목명) / `PRDLST_DCNM`(품목유형명) / `RAWMTRL_NM`(원재료명) / `RAWMTRL_ORDNO`(원재료표시순서) / `CHNG_DT`(변경일자) / `ETQTY_XPORT_PRDLST_YN`(내수/겸용)

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

---

## 📑 API 운영 메타데이터 (활용기간·참고문서·일일 트래픽)

> 공통 사항: 서비스 유형 **REST**, 자동 승인, **일일 트래픽 10,000회/API**.
> 데이터 포맷은 `JSON+XML` 기본, 일부 API만 `XML only` 표기.

### 의약품 핵심 (Phase 1 — 기존 작동 18개)

| NO | 서비스 | End Point Base | 활용기간 | 참고 문서 | Format |
|---|---|---|---|---|---|
| 140 | 의약품 제품 허가정보 (3 ops) | `…/DrugPrdtPrmsnInfoService07` | 2025-10-31 ~ 2027-10-31 | — | JSON+XML |
| 539 | 의약품 회수·판매중지 (4 ops) | `…/MdcinRtrvlSleStpgeInfoService04` | 2025-05-13 ~ 2027-05-13 | — | JSON+XML |
| 564 | 의약품 행정처분 | `…/MdcinExaathrService04` | 2025-07-03 ~ 2027-07-03 | `IROS_50_의약품행정처분서비스_v1.6.docx` | JSON+XML |
| 563 | 의약품 낱알식별 | `…/MdcinGrnIdntfcInfoService03` | 2025-11-13 ~ 2027-11-13 | — | JSON+XML |
| 547 | 의약품 안전성서한 | `…/DrugSafeLetterService02` | 2026-05-26 ~ 2028-05-26 | — | JSON+XML |
| 531 | DUR 품목정보 (9 ops) | `…/DURPrdlstInfoService03` | 2026-05-26 ~ 2028-05-26 | — | JSON+XML |
| 533 | DUR 성분정보 (7 ops) | `…/DURIrdntInfoService03` | 2026-05-26 ~ 2028-05-26 | — | JSON+XML |
| 534 | 의약품 생산·수입·공급중단 | `…/MdcinPrdctnIncmeSuplyService2` | 2026-05-26 ~ 2028-05-26 | `IROS_73_의약품생산수입공급중단 정보_v1.2.docx` | JSON+XML |
| 537 | 의약품 공급부족 | `…/MdcinSuplyLackService03` | 2026-05-26 ~ 2028-05-26 | — | JSON+XML |
| 145 | 의약외품 제품 허가 | `…/QdrgPrdtPrmsnInfoService03` | 2025-11-13 ~ 2027-11-13 | — | JSON+XML |
| 1 | 식품영양성분 DB | `…/FoodNtrCpntDbInfo02` | 2026-05-26 ~ 2028-05-26 | `출력메세지_식품영양성분DB정보.xlsx` | JSON+XML |
| 3 | 행정처분(수입식품업) | `…/AdmmRsltIprtFoodService` | 2026-05-26 ~ 2028-05-26 | — | JSON+XML |
| 5 | 행정처분(식품판매업) | `…/AdmmRsltFoodSaleService` | 2026-05-26 ~ 2028-05-26 | — | JSON+XML |
| 6 | 행정처분(식품제조가공업) | `…/AdmmRsltFoodMnftPrcsService` | 2026-05-26 ~ 2028-05-26 | — | JSON+XML |
| 153 | 수입식품 회수판매중지 | `…/IprtFoodReclSaleStopPrdtStusService` | 2026-05-26 ~ 2028-05-26 | `IROS_373_수입식품회수판매중지제품 정보_v1.0-수정.docx` | JSON+XML |

### 의약품 Phase 2 — 2026-05-27 신규 승인 (R&D / BD / 안전성·품질)

> **활용기간 일괄: 2026-05-27 ~ 2028-05-27 · 모두 일일 10,000회**

| NO | 서비스 | End Point Base | 참고 문서 | Format |
|---|---|---|---|---|
| 248 | 의약품개요정보(e약은요) | `…/DrbEasyDrugInfoService` | `IROS_239_의약품개요정보(e약은요) 서비스_v1.0.docx` | JSON+XML |
| 269 | 묶음의약품정보서비스 | `…/DrbBundleInfoService02` | — | JSON+XML |
| 132 | 의약품GMP적합판정서발급현황 | `…/DrugGmpStbltJgmtIssuStusService` | `IROS_408_의약품GMP적합판정서발급현황_v1.0.docx` | JSON+XML |
| 142 | 의약품 국가출하승인정보 | `…/DrugNatnShipmntAprvInfoService` | `IROS_402_의약품_국가출하승인정보_v1.0.docx` | JSON+XML |
| 144 | 의약품 등 업체허가현황 (2 ops) | `…/DrugEtcBsshBspmStusService` | `IROS_403_의약품등_업체허가현황_v1.0.docx` | JSON+XML |
| 483 | 원료의약품등록(DMF)현황 | `…/MdcDmfInfoService01` | `IROS_76_원료의약품(DMF)현황_v1.1.docx` | **XML only** |
| 561 | 의약품 특허정보 | `…/MdcinPatentInfoService2` | — | JSON+XML |
| 557 | 국내소송 의약품(특허) | `…/DmstcLwstMdcinInfoService02` | — | JSON+XML |
| 552 | FDA Paragraph IV | `…/ParagraphIVTrgetMdcinService02` | — | JSON+XML |
| 562 | FDA 오렌지북 특허정보 | `…/FdaOrngbkPatentInfoService01` | `IROS_30_FDA 오렌지북 특허정보_v1.1.docx` | JSON+XML |
| 566 | 의약품 임상시험 정보 | `…/MdcinClincTestInfoService02` | — | JSON+XML |
| 568 | 의약품임상시험 실시기관 | `…/ClinicTestOprtnInsttInfoService01` | `IROS_15_의약품임상시험 실시기관 정보_v1.1.docx` | JSON+XML |
| 484 | 대조약조회 | `…/MdcCompDrugInfoService04` | — | **XML only** |
| 485 | 생동성인정품목조회 | `…/MdcBioEqInfoService01` | `IROS_77_생동성인정품목조회_v1.2.docx` | **XML only** |
| 554 | 의약품 재심사 정보 | `…/MdcinRejdgeService01` | `IROS_54_의약품 재심사 정보_v1.1.docx` | JSON+XML |
| 556 | 의약품 재평가 정보 | `…/MdcinRevalService02` | — | JSON+XML |
| 565 | 희귀의약품 정보 | `…/RareMdcinInfoService02` | — | JSON+XML |
| 81 | 희귀필수의약품 (5 ops) | `…/RareEsentMdcin` | — | JSON+XML |

### 식품·건기식·HACCP — 2026-05-26 ~ 2026-05-27 신규 승인

| NO | 서비스 | End Point Base | 활용기간 | Format |
|---|---|---|---|---|
| 535 | 검사 부적합 식품정보 (2 ops) | `…/PrsecImproptFoodInfoService03` | 2026-05-27 ~ 2028-05-27 | JSON+XML |
| 12 | 식품 스마트HACCP (B553748) | `…/B553748/SmartCertFoodListService` | 2026-05-27 ~ 2028-05-27 | JSON+XML |
| 51 | 건강기능식품 GMP | `…/FoodGmpStbltCompInfo` | 2026-05-27 ~ 2028-05-27 | JSON+XML |

---

## 🆕 추가 신청 완료 API (2026-05-26 ~ 2026-05-27)

> 이전엔 **"End Point 확인 대기"** 였던 5개 + 신규 4개. End Point 매핑 후 `config.py`에 추가 등록 + smoke test 필요.

### 건강기능식품 4개 (모두 2026-05-27 승인)

| NO | 서비스명 | data.go.kr URL | 활용기간 |
|---|---|---|---|
| 334 | 건강기능식품 개별인정형 정보 | https://www.data.go.kr/data/15074311/openapi.do | 2026-05-27 ~ 2028-05-27 |
| 203 | 건강기능식품 영양DB | https://www.data.go.kr/data/15085712/openapi.do | 2026-05-27 ~ 2028-05-27 |
| 478 | 건강기능식품 품목제조 신고사항 현황 | https://www.data.go.kr/data/15058865/openapi.do | 2026-05-27 ~ 2028-05-27 |
| 51 | 건강기능식품 GMP 지정현황 | https://www.data.go.kr/data/15111987/openapi.do | 2026-05-27 ~ 2028-05-27 |

### 식품 (2026-05-26 ~ 2026-05-27)

| NO | 서비스명 | data.go.kr URL | 활용기간 |
|---|---|---|---|
| - | 식품공전 | https://www.data.go.kr (검색 필요) | 2026-05-27 ~ 2028-05-27 |
| 469 | 검사부적합(국내) | https://www.data.go.kr/data/15063677/openapi.do | 2026-05-27 ~ 2028-05-27 |
| 477 | 행정처분결과(식품접객업) | https://www.data.go.kr/data/15058429/openapi.do | 2026-05-26 ~ 2028-05-26 |
| 444 | 식품(첨가물)품목제조보고 | https://www.data.go.kr/data/15064909/openapi.do | 2026-05-26 ~ 2028-05-26 |
| 470 | 식품(첨가물)품목제조보고(원재료) | https://www.data.go.kr/data/15062098/openapi.do | 2026-05-26 ~ 2028-05-26 |
| 225 | 해외 위해식품 회수정보 | https://www.data.go.kr/data/15077772/openapi.do | 2026-05-26 ~ 2028-05-26 |
| 339 | 식품의 회수·판매중지 정보 | https://www.data.go.kr/data/15074318/openapi.do | 2026-05-26 ~ 2028-05-26 |

> 위 9개 API는 신청은 완료됐으나 **End Point URL이 마이페이지 상세에 표기되지 않은 경우** 가 있음. 각 API 상세 페이지에서 End Point 확인 후 `config.py:API_ENDPOINTS`에 등록 + 활용 함수 작성 필요.

---

## 🔐 보안 처리 가이드

| 항목 | 처리 방식 |
|---|---|
| `PUBLIC_DATA_SERVICE_KEY` 전체 키 | **`.env` 로컬 전용 — git push 금지** (`.gitignore` 50줄) |
| 키 식별자 prefix | 마이페이지에서 확인 가능, 본 문서는 검열 처리 (`5cd…d1`) |
| Encoding/Decoding 인증키 구분 | data.go.kr API 호출은 **Decoding 키** 사용 (URL encode 없이 그대로) |
| 키 발급 영구 보관 | data.go.kr 마이페이지 → 개발계정 → 인증키 보기 (재발급 시 기존 키 즉시 무효화) |
| 키 노출 사고 대응 | 마이페이지에서 키 폐기 + 신규 발급 → `.env` 갱신 |
| GitHub history rewrite | `git filter-branch --tree-filter` 로 모든 커밋에서 키 흔적 제거 (이미 Phase 3에서 적용) |

---

## 📝 활용 목적·내용 (data.go.kr 활용신청 일관)

| 항목 | 내용 |
|---|---|
| 활용 목적 | 웹 사이트 개발 (일부 API는 "기타" / "프로그램개발" 분류) |
| 활용 내용 | "의약품/식품 규제정보 통합 조회 시스템 개발 및 PoC" |
| 활용 시스템 | **KD-IRIS** (KwangDong Integrated Regulatory Intelligence System) |
| 대상 부서 | RA·QA·QC·SCM·R&D·식품QA·영업 (Workspaces 7개) |
| 운영 모드 | Phase 1 개발계정 (10,000회/일) → Phase 2 운영계정 전환 검토 (활용사례 등록 후) |


---

## 🍜 식품안전나라 OPEN-API (foodsafetykorea.go.kr — 97개 전수)

> data.go.kr 인증키와 **별도 KeyID** 필요. 환경변수: `FOODSAFETY_KEY_ID` (`config.py:44`)
> 공통 URL 패턴: `http://openapi.foodsafetykorea.go.kr/api/{KEY_ID}/{서비스ID}/{xml|json}/{startIdx}/{endIdx}[/{변수명}={값}&{변수명}={값}]`
> 모든 API 공통 요청인자 5개: `keyId`·`serviceId`·`dataType`(xml/json)·`startIdx`·`endIdx` (이하 카드는 추가 파라미터만 명시)
> 출처: https://www.foodsafetykorea.go.kr/api/datasetList.do?menu_grp=MENU_GRP31&menu_no=849&provd_instt=ORGN01

### 📁 카테고리: HACCP지정현황 (2개)

### `I0580` — HACCP 적용업소 지정 현황
- **카테고리**: HACCP지정현황
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0580/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LCNS_NO`(인허가번호) · `HACCP_APPN_NO`(HACCP 지정번호) · `CHNG_DT`(변경일자)
- **응답 필드**: `LCNS_NO`(인허가번호) / `INDUTY_CD_NM`(업종) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `SITE_ADDR`(주소) / `HACCP_APPN_DT`(HACCP 지정일자) / `HACCP_APPN_NO`(HACCP 지정번호) / `PRDLST_NM`(품목명) / `CLSBIZ_DVS_CD_NM`(영업상태) / `CLSBIZ_DT`(폐업일자) / `ASGN_CANCL_DT`(지정취소일자) / `CRTFC_ENDDT`(인증종료일자) … 외 1개

### `I0600` — HACCP 교육훈련기관 지정 현황
- **카테고리**: HACCP지정현황
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0600/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `EDC_INSTT_APPN_NO`(지정번호) / `BSSH_NM`(교육훈련기관명) / `BSSH_ADDR`(주소) / `PRSDNT_NM`(대표자) / `PRMS_DT`(허가일자) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수)) / `startIdx`(STRING(필수))


### 📁 카테고리: 건강기능식품 (10개)

### `C003` — 건강기능식품 품목제조신고(원재료)
- **카테고리**: 건강기능식품
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/C003/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자(YYYYMMDD)) · `PRDLST_REPORT_NO`(품목제조번호) · `PRMS_DT`(보고일자(YYYYMMDD)) · `PRDLST_NM`(품목명) · `BSSH_NM`(업소명) · `LCNS_NO`(인허가번호)
- **응답 필드**: `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `PRDLST_REPORT_NO`(품목제조번호) / `PRDLST_NM`(품목명) / `PRMS_DT`(보고일자) / `POG_DAYCNT`(소비기한) / `DISPOS`(성상) / `NTK_MTHD`(섭취방법) / `PRIMARY_FNCLTY`(주된기능성) / `IFTKN_ATNT_MATR_CN`(섭취시주의사항) / `CSTDY_MTHD`(보관방법) / `SHAP`(형태) … 외 5개

### `I-0020` — 건강기능식품 전문.벤처제조업인허가 현황
- **카테고리**: 건강기능식품
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I-0020/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `LCNS_NO`(인허가번호)
- **응답 필드**: `LCNS_NO`(인허가 번호) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자) / `INDUTY_NM`(업종) / `PRMS_DT`(허가일자) / `TELNO`(전화번호) / `LOCP_ADDR`(주소) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수))

### `I-0040` — 건강기능식품 기능성 원료인정현황
- **카테고리**: 건강기능식품
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I-0040/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `PRMS_DT`(인정일자) · `APLC_RAWMTRL_NM`(신청원료명) · `HF_FNCLTY_MTRAL_RCOGN_NO`(인정번호)
- **응답 필드**: `HF_FNCLTY_MTRAL_RCOGN_NO`(인정번호) / `PRMS_DT`(인정일자) / `BSSH_NM`(업체명) / `INDUTY_NM`(업종) / `ADDR`(주소) / `APLC_RAWMTRL_NM`(신청원료명) / `FNCLTY_CN`(기능성 내용) / `DAY_INTK_CN`(1일 섭취량) / `IFTKN_ATNT_MATR_CN`(섭취시 주의사항)

### `I-0050` — 건강기능식품 개별인정형 정보
- **카테고리**: 건강기능식품
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I-0050/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `HF_FNCLTY_MTRAL_RCOGN_NO`(원료인정번호) / `DAY_INTK_HIGHLIMIT`(1일 섭취량 상한선) / `DAY_INTK_LOWLIMIT`(1일 섭취량 하한선) / `WT_UNIT`(중량 단위) / `RAWMTRL_NM`(원재료 명) / `IFTKN_ATNT_MATR_CN`(섭취시 주의 사항 내용) / `PRIMARY_FNCLTY`(주된 기능성) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수))

### `I0030` — 건강기능식품 품목제조 신고사항 현황
- **카테고리**: 건강기능식품
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0030/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자(YYYYMMDD)) · `BSSH_NM`(업소명) · `PRDLST_NM`(품목명) · `PRDLST_REPORT_NO`(품목제조번호)
- **응답 필드**: `LCNS_NO`(인허가번호) / `BSSH_NM`(업소_명) / `PRDLST_REPORT_NO`(품목제조번호) / `PRDLST_NM`(품목_명) / `PRMS_DT`(허가_일자) / `POG_DAYCNT`(소비기한_일수) / `DISPOS`(제품형태) / `NTK_MTHD`(섭취방법) / `PRIMARY_FNCLTY`(주된기능성) / `IFTKN_ATNT_MATR_CN`(섭취시주의사항) / `CSTDY_MTHD`(보관방법) / `PRDLST_CDNM`(유형) … 외 14개

### `I0310` — 건강기능식품 생산실적 보고 품목 현황
- **카테고리**: 건강기능식품
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0310/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `EVL_YR`(생산실적보고년도(YYYY)(필수)) · `LCNS_NO`(인허가번호) · `PRDLST_CD_NM`(품목유형명)
- **응답 필드**: `BSSH_NM`(업소명) / `PRDLST_NM`(품목명) / `GUBUN`(품목구분) / `H_ITEM_NM`(품목유형) / `LCNS_NO`(인허가번호) / `EVL_YR`(보고년도) / `PRDLST_REPORT_NO`(품목제조보고번호) / `FYER_PRDCTN_ABRT_QY`(연간생산능력(KG)) / `PRDCTN_QY`(생산량(KG))

### `I0630` — 건강기능식품GMP 지정 현황
- **카테고리**: 건강기능식품
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0630/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `GMP_APPN_NO`(GMP지정번호) / `APPN_DT`(지정일자) / `BSSH_NM`(업소명) / `LCNS_NO`(업고고유번호) / `APPN_CANCL_DT`(GMP취소일자) / `INDUTY_CD_NM`(업종명) / `PRSDNT_NM`(대표자명) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수))

### `I1290` — 건강기능식품판매업
- **카테고리**: 건강기능식품
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1290/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `LCNS_NO`(인허가번호)
- **응답 필드**: `LCNS_NO`(인허가 번호) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `INDUTY_NM`(업종) / `PRMS_DT`(허가일자) / `TELNO`(전화번호) / `LOCP_ADDR`(주소) / `INSTT_NM`(기관명) / `keyId`(STRING(필수))

### `I2710` — 건강기능식품 품목분류정보
- **카테고리**: 건강기능식품
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2710/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `PRDCT_NM`(품목명) / `IFTKN_ATNT_MATR_CN`(섭취시주의사항) / `PRIMARY_FNCLTY`(주된기능성) / `DAY_INTK_LOWLIMIT`(일일섭취량 하한) / `DAY_INTK_HIGHLIMIT`(일일섭취량 상한) / `INTK_UNIT`(단위) / `INTK_MEMO`(REMARK) / `SKLL_IX_IRDNT_RAWMTRL`(성분명) / `CRET_DTM`(최초등록일) / `LAST_UPDT_DTM`(최종수정일)

### `I2860` — 건강기능식품업소 인허가 변경 정보
- **카테고리**: 건강기능식품
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2860/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LCNS_NO`(인허가번호) · `BSSH_NM`(업소명)
- **응답 필드**: `BSSH_NM`(업소명) / `INDUTY_CD_NM`(업종명) / `LCNS_NO`(인허가번호) / `TELNO`(전화번호) / `SITE_ADDR`(주소) / `CHNG_DT`(변경일자) / `CHNG_BF_CN`(변경전내용) / `CHNG_AF_CN`(변경후내용) / `CHNG_PRVNS`(변경사유)


### 📁 카테고리: 수입식품 등 (6개)

### `C001` — 수입식품등영업신고대장
- **카테고리**: 수입식품 등
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/C001/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `LCNS_NO`(인허가번호)
- **응답 필드**: `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `INDUTY_NM`(업종) / `PRMS_DT`(허가일자) / `LOCP_ADDR`(주소) / `INSTT_NM`(기관명) / `TELNO`(전화번호) / `keyId`(STRING(필수))

### `I0130` — LMO 수입 승인 현황
- **카테고리**: 수입식품 등
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0130/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `LMO_CONFM_NO`(유전자 변형 생물체 승인번호) / `CONFM_DT`(승인일자) / `BSSH_NM`(업소명) / `ADDR`(주소) / `COMMON_NM`(보통명) / `SYSTM_NM`(계통명) / `BNE_NM`(학명) / `PRPOS`(용도) / `NATN_CD_NM`(수입국) / `keyId`(STRING(필수))

### `I0250` — 우수수입업소 등록 현황
- **카테고리**: 수입식품 등
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0250/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `EXCLNC_INCM_BSSH_REGNO`(우수수입업소등록번호) / `PRMS_DT`(허가일자) / `BSSH_NM`(업소명) / `ADDR`(소재지) / `EXCOURY_NATN_CD_NM`(수출국가) / `INCM_PRDT_XPORT_MC_NM`(수입제품제조회사명) / `PRDLST_CNT`(품목수) / `PRDLST_NM`(품목명) / `LCNS_NO`(인허가번호) / `keyId`(STRING(필수))

### `I1260` — 식품등수입판매업정보
- **카테고리**: 수입식품 등
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1260/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `LCNS_NO`(인허가번호) · `BSSH_NM`(업소명)
- **응답 필드**: `LCNS_NO`(인허가 번호) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `INDUTY_NM`(업종) / `PRMS_DT`(허가일자) / `TELNO`(전화번호) / `LOCP_ADDR`(주소) / `INSTT_NM`(기관명) / `keyId`(STRING(필수))

### `I2780` — 수입쇠고기 냉동전환 정보
- **카테고리**: 수입식품 등
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2780/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `MEATWATCH_NO`(이력번호) · `HIST_NO`(수입신고확인증번호) · `ACCEPT_NO`(축산물수입신고필증번호)
- **응답 필드**: `MEATWATCH_NO`(이력번호) / `HIST_NO`(수입신고확인증번호) / `ORGNP_NM`(원산지) / `BSSH_NM`(수입업체명) / `APLC_DTM`(신고일) / `PRDLST_NM`(품명(한글)) / `FREEZING_CNVRS_QTY`(전환수량(BOX)) / `FREEZING_CNVRS_WT`(전환중량(KG)) / `FRESH_DISTB_TMLMT_BGN_DT`(냉장유통/소비기한 시작일자) / `FRESH_DISTB_TMLMT_DT`(냉장유통/소비기한 만료일자) / `FREEZING_CNVRS_OPRTN_DT`(냉동전환 실시일) / `FREEZING_CNVRS_PREARNGE_DT`(냉동전환 완료일) … 외 2개

### `I2781` — 수입축산물 냉동전환 정보
- **카테고리**: 수입식품 등
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2781/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `MEATWATCH_NO`(이력번호) · `ACCEPT_NO`(축산물수입신고필증번호) · `HIST_NO`(수입신고확인증번호)
- **응답 필드**: `MEATWATCH_NO`(이력번호) / `ACCEPT_NO`(축산물수입신고필증번호) / `HIST_NO`(수입신고확인증번호) / `ORGNP_NM`(원산지) / `BSSH_NM`(수입업체명) / `APLC_DTM`(신고일) / `PRDLST_NM`(품명(한글)) / `FREEZING_CNVRS_QTY`(전환수량(BOX)) / `FREEZING_CNVRS_WT`(전환중량(KG)) / `FRESH_DISTB_TMLMT_BGN_DT`(냉장유통/소비기한 시작일자) / `FRESH_DISTB_TMLMT_DT`(냉장유통/소비기한 만료일자) / `FREEZING_CNVRS_OPRTN_DT`(냉동전환 실시일) … 외 2개


### 📁 카테고리: 식품위해관리 (14개)

### `I0470` — 행정처분결과
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0470/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자(YYYYMMDD)) · `DSPS_DCSNDT`(확정일자(YYYYMMDD)) · `LCNS_NO`(인허가번호)
- **응답 필드**: `PRCSCITYPOINT_BSSHNM`(업소명) / `INDUTY_CD_NM`(업종) / `LCNS_NO`(인허가번호) / `DSPS_DCSNDT`(처분확정일자) / `DSPS_BGNDT`(처분시작일(영업정지의경우)) / `DSPS_ENDDT`(처분종료일(영업정지의경우)) / `DSPS_TYPECD_NM`(처분유형) / `VILTCN`(위반일자및위반내용) / `ADDR`(주소) / `TELNO`(전화번호) / `PRSDNT_NM`(대표자명) / `DSPSCN`(처분내용) … 외 5개

### `I0480` — 행정처분결과(식품제조가공업)
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0480/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자(YYYYMMDD)) · `DSPS_DCSNDT`(확정일자(YYYYMMDD)) · `LCNS_NO`(인허가번호)
- **응답 필드**: `PRCSCITYPOINT_BSSHNM`(업소명) / `INDUTY_CD_NM`(업종) / `LCNS_NO`(인허가번호) / `DSPS_DCSNDT`(처분확정일자) / `DSPS_BGNDT`(처분시작일(영업정지의경우)) / `DSPS_ENDDT`(처분종료일(영업정지의경우)) / `DSPS_TYPECD_NM`(처분유형) / `VILTCN`(위반일자및위반내용) / `ADDR`(주소) / `TELNO`(전화번호) / `PRSDNT_NM`(대표자명) / `LAWORD_CD_NM`(위반법령) … 외 5개

### `I0481` — 행정처분결과(식품판매업)
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0481/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자(YYYYMMDD)) · `DSPS_DCSNDT`(확정일자(YYYYMMDD)) · `LCNS_NO`(인허가번호)
- **응답 필드**: `PRCSCITYPOINT_BSSHNM`(업소명) / `INDUTY_CD_NM`(업종) / `LCNS_NO`(인허가번호) / `DSPS_DCSNDT`(처분확정일자) / `DSPS_BGNDT`(처분시작일(영업정지의경우)) / `DSPS_ENDDT`(처분종료일(영업정지의경우)) / `DSPS_TYPECD_NM`(처분유형) / `VILTCN`(위반일자 및 위반내용) / `ADDR`(주소) / `TELNO`(전화번호) / `PRSDNT_NM`(대표자명) / `LAWORD_CD_NM`(위반법령) … 외 5개

### `I0482` — 행정처분결과(수입식품업)
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0482/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자(YYYYMMDD)) · `DSPS_DCSNDT`(확정일자(YYYYMMDD)) · `LCNS_NO`(인허가번호)
- **응답 필드**: `PRCSCITYPOINT_BSSHNM`(업소명) / `INDUTY_CD_NM`(업종) / `LCNS_NO`(인허가번호) / `DSPS_DCSNDT`(처분확정일자) / `DSPS_BGNDT`(처분시작일(영업정지의경우)) / `DSPS_ENDDT`(처분종료일(영업정지의경우)) / `DSPS_TYPECD_NM`(처분유형) / `VILTCN`(위반일자 및 위반내용) / `ADDR`(주소) / `TELNO`(전화번호) / `PRSDNT_NM`(대표자명) / `LAWORD_CD_NM`(위반법령) … 외 5개

### `I0490` — 회수.판매중지 정보
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0490/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CRET_DTM`(등록일자(YYYYMMDD)) · `PRDLST_REPORT_NO`(품목제조보고번호)
- **응답 필드**: `PRDTNM`(제품명) / `RTRVLPRVNS`(회수사유) / `BSSHNM`(제조업체명) / `ADDR`(업체주소) / `TELNO`(전화번호) / `BRCDNO`(바코드번호) / `FRMLCUNIT`(포장단위) / `MNFDT`(제조일자) / `RTRVLPLANDOC_RTRVLMTHD`(회수방법) / `DISTBTMLMT`(유통/소비기한) / `PRDLST_TYPE`(식품분류) / `IMG_FILE_PATH`(제품사진 URL) … 외 7개

### `I2620` — 검사부적합(국내)
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2620/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `PRDTNM`(제품명) · `PRDLST_REPORT_NO`(품목제조보고번호)
- **응답 필드**: `PRDTNM`(제품명) / `BSSHNM`(업소명) / `MNFDT`(제조일자) / `DISTBTMLMT`(유통/소비기한) / `ADDR`(영업자주소) / `INSTT_NM`(검사기관) / `REGSTR_TELNO`(전화번호) / `BRCDNO`(바코드번호) / `FRMLCUNIT`(포장단위) / `TEST_ITMNM`(부적합항목) / `STDR_STND`(기준규격) / `TESTANALS_RSLT`(검사결과) … 외 6개

### `I2630` — 행정처분결과(식품접객업)
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2630/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자(YYYYMMDD)) · `DSPS_DCSNDT`(확정일자(YYYYMMDD)) · `LCNS_NO`(인허가번호)
- **응답 필드**: `PRCSCITYPOINT_BSSHNM`(업소명) / `INDUTY_CD_NM`(업종) / `LCNS_NO`(인허가번호) / `DSPS_DCSNDT`(처분확정일자) / `DSPS_BGNDT`(처분시작일(영업정지의경우)) / `DSPS_ENDDT`(처분종료일(영업정지의경우)) / `DSPS_TYPECD_NM`(처분유형) / `VILTCN`(위반일자및위반내용) / `ADDR`(주소) / `TEL_NO`(전화번호) / `PRSDNT_NM`(대표자명) / `DSPSCN`(처분내용) … 외 5개

### `I2640` — 검사부적합 현황(농산물)
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2640/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `PRDTNM`(제품명)
- **응답 필드**: `PRDTNM`(제품명) / `BSSHNM`(업소명) / `MNFDT`(제조일자) / `DISTBTMLMT`(유통/소비기한) / `ADDR`(영업자주소) / `INSTT_NM`(검사기관) / `REGSTR_TELNO`(전화번호) / `BRCDNO`(바코드번호) / `FRMLCUNIT`(포장단위) / `TEST_ITMNM`(부적합항목) / `STDR_STND`(기준규격) / `TESTANALS_RSLT`(검사결과) … 외 4개

### `I2715` — 해외직구 위해식품 차단정보
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2715/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CRET_DTM`(등록일자(YYYYMMDD)) · `LAST_UPDT_DTM`(최종수정일자(YYYYMMDD)) · `PRDT_NM`(제품명) · `MUFC_NM`(제조사명) · `MUFC_CNTRY_NM`(제조국가명) · `INGR_NM_LST`(위해성분명)
- **응답 필드**: `PRDT_NM`(제품명) / `MUFC_NM`(제조사명) / `MUFC_CNTRY_NM`(제조국가명) / `INGR_NM_LST`(위해성분명) / `STT_YMD`(적용시작일) / `END_YMD`(적용종료일) / `CRET_DTM`(등록일) / `LAST_UPDT_DTM`(최종수정일) / `IMAGE_URL`(이미지URL) / `SELF_IMPORT_SEQ`(일련번호(고유키값)) / `BARCD_CTN`(바코드번호)

### `I2810` — 해외 위해식품 회수정보
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2810/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `ST_CRET_DTM`(생성일자시작범위(YYYYMMDD)) · `END_CRET_DTM`(생성일자종료범위(YYYYMMDD))
- **응답 필드**: `TITL`(제품명) / `DETECT_TITL`(유해물질) / `CRET_DTM`(생성일자) / `BDT`(본문내용) / `DOWNLOAD_URL`(이미지 다운로드 URL) / `NTCTXT_NO`(게시글번호) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수))

### `I2848` — 식중독 지역별 현황
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2848/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `OCCRNC_YEAR`(발생년(YYYY)) · `OCCRNC_MM`(발생월(MM)) · `OCCRNC_AREA`(발생지역)
- **응답 필드**: `OCCRNC_YEAR`(발생년) / `OCCRNC_MM`(발생월) / `OCCRNC_AREA`(발생지역) / `OCCRNC_CNT`(발생건수) / `PATNT_CNT`(환자수) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수))

### `I2849` — 식중독 원인시설별 현황
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2849/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `OCCRNC_YEAR`(발생년(YYYY)) · `OCCRNC_MM`(발생월(MM)) · `OCCRNC_PLC`(발생장소)
- **응답 필드**: `OCCRNC_YEAR`(발생년) / `OCCRNC_MM`(발생월) / `OCCRNC_PLC`(발생장소) / `OCCRNC_CNT`(발생건수) / `PATNT_CNT`(환자수) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수))

### `I2850` — 식중독 원인물질별 현황
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2850/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `OCCRNC_YEAR`(발생년(YYYY)) · `OCCRNC_MM`(발생월(MM)) · `OCCRNC_VIRS`(발생물질)
- **응답 필드**: `OCCRNC_YEAR`(발생년) / `OCCRNC_MM`(발생월) / `OCCRNC_VIRS`(발생물질) / `OCCRNC_CNT`(발생건수) / `PATNT_CNT`(환자수) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수))

### `I2854` — 식품별 유해오염물질 검출량
- **카테고리**: 식품위해관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2854/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `PRDLST_CD`(식품유형) · `PRDLST_NM`(식품명) · `ANALS_YEAR`(분석연도)
- **응답 필드**: `SNT_GBN`(구분) / `PRDLST_CD`(식품유형) / `PRDLST_NM`(식품명) / `ANALS_YEAR`(분석연도) / `COL_A_RESULT`(다이옥신) / `COL_B_RESULT`(PCBs) / `COL_C_RESULT`(벤조피렌) / `COL_D_RESULT`(3-MCPD) / `COL_E_RESULT`(총 아플라톡신) / `COL_F_RESULT`(아플라톡신B1) / `COL_G_RESULT`(오크라톡신) / `COL_H_RESULT`(푸모니신) … 외 12개


### 📁 카테고리: 기준규격정보 (25개)

### `I0930` — 식품공전
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0930/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LAST_UPDT_DTM`(최종수정일(YYYYMMDD)) · `PRDLST_NM`(품목명)
- **응답 필드**: `PRDLST_NM`(품목명) / `T_KOR_NM`(시험항목) / `FNPRT_ITM_NM`(세부항목) / `PIAM_KOR_NM`(품목항목속성) / `SPEC_VAL`(기준규격값) / `VALD_BEGN_DT`(유효개시일자) / `VALD_END_DT`(유효종료일자) / `SPEC_VAL_SUMUP`(규격값요약) / `JDGMNT_FNPRT_CD_NM`(판정형식) / `MXMM_VAL`(최대값) / `MXMM_VAL_FNPRT_CD_NM`(이하/미만) / `MIMM_VAL`(최소값) … 외 5개

### `I0940` — 식품용 기구 및 용기.포장 공전
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0940/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `PRDLST_CD`(품목코드) / `PC_KOR_NM`(품목한글명) / `TESTITM_CD`(시험항목코드) / `T_KOR_NM`(시험항목 한글명) / `FNPRT_ITM_NM`(세부항목명) / `SPEC_VAL`(기준규격값) / `SPEC_VAL_SUMUP`(기준규격값 요약) / `VALD_BEGN_DT`(유효개시일자) / `VALD_END_DT`(유효종료일자) / `SORC`(출처) / `MXMM_VAL`(최대값) / `MIMM_VAL`(최소값) … 외 2개

### `I0950` — 식품첨가물공전
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0950/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `PRDLST_CD`(품목유형코드) · `LAST_UPDT_DTM`(최종수정일(YYYYMMDD)) · `TESTITM_CD`(시험항목코드)
- **응답 필드**: `PRDLST_CD`(품목코드) / `PC_KOR_NM`(품목한글명) / `TESTITM_CD`(시험항목코드) / `T_KOR_NM`(시험항목 한글명) / `FNPRT_ITM_NM`(세부항목명) / `SPEC_VAL`(기준규격값) / `SPEC_VAL_SUMUP`(기준규격값 요약) / `VALD_BEGN_DT`(유효개시일자) / `VALD_END_DT`(유효종료일자) / `SORC`(출처) / `MXMM_VAL`(최대값) / `MIMM_VAL`(최소값) … 외 2개

### `I0960` — 건강기능식품공전
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0960/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LAST_UPDT_DTM`(최종수정일(YYYYMMDD)) · `PRDLST_CD`(품목유형코드)
- **응답 필드**: `PRDLST_CD`(품목코드) / `PC_KOR_NM`(품목한글명) / `TESTITM_CD`(시험항목코드) / `T_KOR_NM`(시험항목 한글명) / `FNPRT_ITM_NM`(세부항목명) / `SPEC_VAL`(기준규격값) / `SPEC_VAL_SUMUP`(기준규격값 요약) / `VALD_BEGN_DT`(유효개시일자) / `VALD_END_DT`(유효종료일자) / `SORC`(출처) / `MXMM_VAL`(최대값) / `MIMM_VAL`(최소값) … 외 2개

### `I0980` — 식품원료의 한시적 기준 및 규격 인정 현황
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0980/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `LIMIT_STDR_STND_RCOGN_NO`(한시적 기준 규격 인정 번호) / `BSSH_NM`(업소명) / `BSSH_ADDR`(주소) / `PRSDNT_NM`(대표자) / `RCOGN_DT`(인정일자) / `PRDT_NM`(제품명) / `RAWMTRL_NM`(원재료명) / `PRPOS`(용도) / `USED`(사용량) / `USING_UNIT`(사용량단위)

### `I0990` — 기구 및 용기.포장의 한시적 기준 및 규격 인정 현황
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0990/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `LIMIT_STDR_STND_RCOGN_NO`(인정번호) / `RCOGN_DT`(인정일자) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `TELNO`(전화번호) / `MC_NM`(제조회사) / `PRDT_NM`(제품명) / `MC_NATN_CD_NM`(제조회사 국가) / `keyId`(STRING(필수))

### `I1000` — 식품첨가물의 한시적 기준 및 규격 인정 현황
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1000/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `LIMIT_STDR_STND_RCOGN_NO`(인정번호) / `RCOGN_DT`(인정일자) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `TELNO`(전화번호) / `MC_NM`(제조회사) / `PRDT_NM`(제품명) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수))

### `I1010` — 기구등의 살균소독제 한시적 기준 및 규격 인정 현황
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1010/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `LIMIT_STDR_STND_RCOGN_NO`(인정번호) / `RCOGN_DT`(인정일자) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `TELNO`(전화번호) / `MC_NM`(제조회사) / `PRDT_NM`(제품명) / `MC_NATN_CD_NM`(제조회사 국가) / `keyId`(STRING(필수))

### `I1020` — 식품원재료(식물,동물,미생물,수산물) 정보
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1020/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `LCLAS_NM`(대분류) / `MLSFC_NM`(중분류) / `RPRSNT_RAWMTRL_NM`(원재료명) / `RAWMTRL_NCKNM`(이명) / `ENG_NM`(영문명) / `SCNM`(학명) / `REGN_CD_NM`(부위명) / `RAWMTRL_STATS_CD_NM`(상태명) / `USE_CND_NM`(사용조건) / `USE_CND_STDR_CN`(사용조건기준내용)

### `I1030` — 방사선조사식품 품목 인정 현황
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1030/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `SPEC_NM`(기준규격명) / `PC_KOR_NM`(품목한글명) / `T_KOR_NM`(시험항목 한글명) / `PIAM_KOR_NM`(품목항목속성 한글명) / `SPEC_VAL`(기준규격값) / `SPEC_VAL_SUMUP`(기준규격값 요약) / `VALD_BEGN_DT`(유효개시일자) / `VALD_END_DT`(유효종료일자) / `SORC`(출처) / `MXMM_VAL`(최대값) / `MIMM_VAL`(최소값) / `UNIT_NM`(단위명)

### `I1040` — 농약잔류허용기준
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1040/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `시행시점(YYYYMMDD)`(LAUNCH_POINT)
- **응답 필드**: `AGCHM_KOR_NM`(농약명) / `FOOD_KOR_NM`(식품명) / `OPERTN_CITYPOINT`(시행 시점) / `STEP`(단계) / `MRL_VAL`(MRL 값) / `DSUSE_YN`(폐기 여부) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수))

### `I1050` — 식품별 농약잔류허용기준
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1050/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `FOOD_KOR_NM`(식품한글명) / `FOOD_ENG_NM`(식품영문명) / `AGCHM_KOR_NM`(농약명) / `DEDE_NTK_QTY`(일일섭취량) / `TMPR_STDR_APPLC_YN`(잠정기준적용여부) / `LCLAS_NM`(대분류) / `MLSFC_NM`(중분류) / `SCLAS_NM`(소분류) / `OPERTN_CITYPOINT`(시행시점) / `STEP`(단계) / `MRL_VAL`(MRL 값) / `ETC_YN`(기타여부) … 외 1개

### `I1060` — 시약정보
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1060/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `VALD_TERM`(유효기간(YYYYMM))
- **응답 필드**: `CITYMEDI_NM_CD`(시약 명) / `CMPNY_NO`(회사 명) / `CTPRVNACCTO_INTD_NO`(시도별 지방청) / `STATS_NO`(상태) / `PUREDO`(순도) / `VALD_TERM`(유효기간) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수))

### `I1070` — 동물용의약품 현황
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1070/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `ANIMAL_ONLY_MDCIN_NM_KOR`(의약품 한글명) / `ANIMAL_ONLY_MDCIN_NM_ENG`(의약품 영문명) / `APPLC_OBJ_ANIMAL`(적용 대상 동물) / `MCFRL`(분자식) / `MCWGH`(분자량) / `SYSTM_NM`(계통명) / `IUPAC_NM`(IUPAC 명) / `CAS_NM`(CAS 명) / `SHAP_NM`(형태) / `POIOF`(녹는점) / `BOILPNT`(끓는점) / `STEPR`(증기압) … 외 5개

### `I1080` — 동물의약품별 잔류허용 기준
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1080/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `CDX_KOREA_DVS_CD`(구분) / `ANIMAL_ONLY_MDCIN_NM_KOR`(동물 전용 의약품 한글명) / `OPERTN_CITYPOINT`(시행 시점) / `STEP`(단계) / `MRL`(MRL) / `FOOD_KOR_NM`(식품 한글명) / `FOOD_ENG_NM`(식품 영문명) / `ETC_YN`(기타 여부) / `TMPR_STDR_APPLC_YN`(임시기준적용여부) / `DSUSE_YN`(폐기 여부)

### `I1090` — 잔류동물의약품 식품별 잔류허용 기준
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1090/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `FOOD_KOR_NM`(식품한글명) / `FOOD_ENG_NM`(식품영문명) / `DEDE_NTK_QTY`(일일섭취량) / `TMPR_STDR_APPLC_YN`(잠정기준적용여부) / `LCLAS_NM`(대분류) / `MLSFC_NM`(중분류) / `SCLAS_NM`(소분류) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수))

### `I1100` — 기구등의 살균소독제 기준규격
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1100/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LAST_UPDT_DTM`(최종수정일(YYYYMMDD)) · `PRDLST_CD`(품목유형코드)
- **응답 필드**: `PC_KOR_NM`(품목한글명) / `T_KOR_NM`(시험항목 한글명) / `FNPRT_ITM_NM`(세부항목명) / `PIAM_KOR_NM`(품목항목속성 한글명) / `SPEC_VAL`(기준규격값) / `SPEC_VAL_SUMUP`(기준규격값 요약) / `VALD_BEGN_DT`(유효개시일자) / `VALD_END_DT`(유효종료일자) / `SORC`(출처) / `MXMM_VAL`(최대값) / `MIMM_VAL`(최소값) / `INJRY_YN`(위해여부) … 외 3개

### `I1101` — 식품첨가물의 기준 및 규격 현황
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1101/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LAST_UPDT_DTM`(최종수정일(YYYYMMDD)) · `PRDLST_CD`(품목유형코드)
- **응답 필드**: `PC_KOR_NM`(품목한글명) / `PRDLST_CD`(품목분류코드) / `T_KOR_NM`(시험항목 한글명) / `FNPRT_ITM_NM`(세부항목명) / `PIAM_KOR_NM`(품목항목속성 한글명) / `SPEC_VAL`(기준규격값) / `SPEC_VAL_SUMUP`(기준규격값 요약) / `VALD_BEGN_DT`(유효개시일자) / `VALD_END_DT`(유효종료일자) / `SORC`(출처) / `MXMM_VAL`(최대값) / `MIMM_VAL`(최소값) … 외 4개

### `I1650` — 신고대상분류기준
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1650/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `CMMN_CD_NM`(분류) / `FNPRT_CD_NM`(신고분류) / `USER_DFN_CLMN_1`(분류1) / `USER_DFN_CLMN_2`(분류2) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수)) / `startIdx`(STRING(필수))

### `I1660` — 과징금부과기준
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1660/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `VALD_BGN_DT`(유효시작일자(YYYYMMDD))
- **응답 필드**: `DSPS_STDR_CD_NM`(처분기준명) / `LAWORD_CD_NM`(식품법령) / `BASIS_LAWORD`(근거법령) / `VILT_TYPE_NM`(위반유형) / `LV_NO`(레벨) / `VALD_BGN_DT`(유효시작일자) / `VALD_END_DT`(유효종료일자) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수))

### `I1670` — 과태료부과기준
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1670/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `VALD_BGN_DT`(유효시작일자)
- **응답 필드**: `DSPS_STDR_CD`(처분기준코드) / `DSPS_STDR_CD_NM`(처분기준명) / `LV_NO`(레벨) / `BASIS_LAWORD`(근거법령) / `VILT_TYPE_NM`(위반유형) / `VALD_BGN_DT`(유효시작일자) / `VALD_END_DT`(유효종료일자) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수))

### `I2580` — 개별기준규격
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2580/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LAST_UPDT_DTM`(최종수정일(YYYYMMDD)) · `PRDLST_CD`(품목유형코드)
- **응답 필드**: `INDV_SPEC_SEQ`(개별기준규격일련번호) / `PRDLST_CD`(품목분류코드) / `PRDLST_CD_NM`(품목명) / `TESTITM_CD`(시험항목코드) / `TESTITM_NM`(시험항목명) / `FNPRT_ITM_NM`(세부항목명) / `ATTRB_SEQ`(단서조항일련번호) / `PIAM_KOR_NM`(단서조항명) / `SPEC_VAL`(기준규격) / `SPEC_VAL_SUMUP`(기준규격요약) / `VALD_BEGN_DT`(유효개시일) / `VALD_END_DT`(유효종료일) … 외 28개

### `I2590` — 공통기준종류
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2590/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LAST_UPDT_DTM`(최종수정일(YYYYMMDD))
- **응답 필드**: `CMMN_SPEC_CD`(공통기준규격코드) / `SPEC_NM`(기준규격명) / `HRNK_CMMN_SPEC_CD`(상위공통기준규격코드) / `LV`(레벨) / `DFN`(정의) / `USE_YN`(사용여부) / `LAST_UPDT_DTM`(최종수정일시) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수))

### `I2600` — 공통기준규격
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2600/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LAST_UPDT_DTM`(최종수정일(YYYYMMDD)) · `PRDLST_CD`(품목유형코드)
- **응답 필드**: `CMMN_SPEC_SEQ`(공통기준종류코드일련번호) / `CMMN_SPEC_CD`(공통기준종류코드) / `SPEC_NM`(공통기준종류명) / `PRDLST_CD`(품목분류코드) / `PRDLST_CD_NM`(품목명) / `TESTITM_CD`(시험항목코드) / `TESTITM_NM`(시험항목명) / `FNPRT_ITM_NM`(세부항목명) / `ATTRB_SEQ`(단서조항일련번호) / `PIAM_KOR_NM`(단서조항명) / `SPEC_VAL`(기준규격) / `SPEC_VAL_SUMUP`(기준규격요약) … 외 30개

### `I2610` — 공통기준제외
- **카테고리**: 기준규격정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2610/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LAST_UPDT_DTM`(최종수정일(YYYYMMDD))
- **응답 필드**: `CMMN_SPEC_CD`(공통기준규격코드) / `SPEC_NM`(기준규격명) / `PRDLST_CD`(품목코드) / `KOR_NM`(한글명) / `TESTITM_CD`(시험항목코드) / `LAST_UPDT_DTM`(최종수정일시) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수))


### 📁 카테고리: 식품안전관리 (4개)

### `I0140` — 유전자변형식품등의 안전성 평가 심사 결과 현황
- **카테고리**: 식품안전관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0140/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `PRDLST_NM`(품목 명) / `GOODS_NM`(상품 명) / `INJECTION_GENE_CN`(삽입된 유전자 내용) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `PRMS_DT`(허가 일자) / `ENDOW_CHARTR_CN`(부여된 특성 내용) / `GMO_SAFTY_NO`(통보 번호) / `GMO_PRDT_KND_CL_NM`(제품종류) / `keyId`(STRING(필수))

### `I0150` — 후대교배종의 안전성 평가 신청 및 검토 정보
- **카테고리**: 식품안전관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0150/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `PRMS_DT`(허가일자) / `PRDLST_NM`(품목명) / `LMOCHILD_BTHTR_CRSS_YN`(이종간교배여부) / `LMOCHILD_DFFPNT_YN`(차이점여부) / `LMOCHILD_CHARTR_CHNGE_YN`(특성변화여부) / `GMO_PRDT_KND`(제품종류) / `GOODS_NM`(제품명) / `keyId`(STRING(필수))

### `I0460` — 수거검사 계획 및 실적 관련 현황
- **카테고리**: 식품안전관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0460/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `SEARCHSTDT`(수거시작일자(YYYYMMDD)) · `SEARCHENDDT`(수거종료일자(YYYYMMDD)) · `TKAWYSPCI_TYPECD`(검체구분(0수산물1가공식품2식품첨가물3건강기능식품4농산물5축산물6기구용기7위생용품8식품접객업9기타)) · `LAST_UPDT_DTM`(최종수정일자(YYYYMMDD)) · `BSSH_NM`(업소명)
- **응답 필드**: `PRCSCITYPOINT_INDUTYCD_NM`(업종) / `BSSH_NM`(업소명) / `SITE_ADDR`(소재지) / `PRDTNM`(제품명) / `TKAWYDTM`(수거일자) / `JDGMNT_CD_NM`(판정결과) / `EXC_INSTT_NM`(수행기관명) / `TKAWYSPCI_TYPECD_NM`(검체구분) / `PRDLST_REPORT_NO`(품목제조보고번호) / `LAST_UPDT_DTM`(최종수정일시) / `TKAWYPRNO`(수거증번호) / `PLAN_TITL`(수거계획명)

### `I2839` — 건강기능식품제조업, 건강기능식품판매업 지도단속계획 및 실적현황
- **카테고리**: 식품안전관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2839/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `SEARCHSTDT`(지도점검일자시작범위(YYYYMMDD)) · `SEARCHENDDT`(지도점검일자종료범위(YYYYMMDD))
- **응답 필드**: `PLAN_CLCD`(계획분류) / `CHCK_BGNDT`(계획시작일자) / `CHCK_ENDDT`(계획종료일자) / `EXC_INSTTCD`(점검기관) / `BSSH_NM`(업소명) / `GIDCHCK_DT`(지도점검일자) / `BLDINSCTR_NAME`(피점검자성명) / `GIDCHCK_RSLTCD`(점검결과) / `PLAN_TITL`(계획명)


### 📁 카테고리: 식품영양정보 (2개)

### `COOKRCP01` — 조리식품의 레시피 DB
- **카테고리**: 식품영양정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/COOKRCP01/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `RCP_NM`(메뉴명) · `RCP_PARTS_DTLS`(재료정보1) · `CHNG_DT`(변경일자(YYYYMMDD)) · `RCP_PAT2`(요리종류(ex) 반찬, 국, 후식 등))
- **응답 필드**: `RCP_SEQ`(일련번호) / `RCP_NM`(메뉴명) / `RCP_WAY2`(조리방법) / `RCP_PAT2`(요리종류) / `INFO_WGT`(중량(1인분)) / `INFO_ENG`(열량) / `INFO_CAR`(탄수화물) / `INFO_PRO`(단백질) / `INFO_FAT`(지방) / `INFO_NA`(나트륨) / `HASH_TAG`(해쉬태그) / `ATT_FILE_NO_MAIN`(이미지경로(소)) … 외 37개

### `I0760` — 건강기능식품 영양DB
- **카테고리**: 식품영양정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0760/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `HELT_ITM_GRP_NM`(명칭)
- **응답 필드**: `HELT_ITM_GRP_CD`(건강 항목 그룹 코드) / `HELT_ITM_GRP_NM`(건강 항목 그룹 명) / `LCLAS_CD`(대분류 코드) / `LCLAS_NM`(대분류 명) / `MLSFC_CD`(중분류 코드) / `MLSFC_NM`(중분류 명) / `SCLAS_CD`(소분류 코드) / `SCLAS_NM`(소분류 명) / `keyId`(STRING(필수))


### 📁 카테고리: 이력추적관리 (1개)

### `I0320` — 식품이력추적관리 등록 현황
- **카테고리**: 이력추적관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0320/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `MOD_DT`(최종수정일(YYYYMMDD)) · `BRNCH_NM`(업체명) · `BTYPE`(업종) · `PDT_NM`(제품명) · `PDT_TYPE`(식품유형) · `FOOD_TYPE`(식품구분)
- **응답 필드**: `REG_NUM`(등록번호) / `PDT_NM`(제품명) / `PDT_BARCD`(바코드) / `PDT_TYPE`(식품유형) / `MAKE_TYPE`(제조구분) / `ADDR`(주소) / `BRNCH_NM`(업체명) / `BTYPE`(업종) / `FOOD_TYPE`(식품구분) / `PRDLST_REPORT_NO`(품목보고번호) / `MNFT_DAY`(제조일자) / `FOOD_HISTRACE_NUM`(식품이력추적관리번호) … 외 2개


### 📁 카테고리: 검사기관정보 (4개)

### `I0890` — 식품위생검사기관 지정 현황
- **카테고리**: 검사기관정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0890/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `PRSEC_INSTT_RCOGN_NO`(지정번호) / `BSSH_NM`(기관명) / `PRSDNT_NM`(대표자) / `APPN_BGN_DT`(지정일자) / `APPN_END_DT`(지정종료일자) / `WORK_SCOPE`(업무범위) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수))

### `I0900` — 축산물위생검사기관 지정 현황
- **카테고리**: 검사기관정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0900/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `BSSH_NM`(검사기관명) / `PRSDNT_NM`(대표자) / `ADDR`(주소) / `APPN_BGN_DT`(지정시작일자) / `APPN_END_DT`(지정종료일자) / `WORK_SCOPE`(업무범위) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수))

### `I0910` — 국외검사기관 인정 현황
- **카테고리**: 검사기관정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0910/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `PRSEC_INSTT_RCOGN_NO`(인정번호) / `BSSH_NM`(기관명) / `PRSDNT_NM`(대표자) / `APPN_BGN_DT`(지정일자) / `PRSEC_ITM_CD_NM`(검사항목) / `TELNO`(전화번호) / `BSSH_ADDR`(주소) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수))

### `I0920` — 식품검사기관별 시험항목정보조회
- **카테고리**: 검사기관정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0920/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CMPTNC_INSTT_NM`(관할기관) · `INSTT_NM`(검사기관) · `TESTITM_NM`(시험항목명) · `CHNG_DT`(변경일자(YYYYMMDD))
- **응답 필드**: `REALM_NM`(분야) / `CMPTNC_INSTT_NM`(관할기관) / `INSTT_NM`(검사기관) / `ADDR`(소재지) / `MSK_TELNO`(전화번호) / `TESTITM_LCLAS_NM`(대분류) / `TESTITM_MLSFC_NM`(중분류) / `TESTITM_NM`(시험항목명) / `RM`(비고) / `CHNG_DT`(변경일자(YYYYMMDD))


### 📁 카테고리: 어린이식품안전관리 (4개)

### `I0080` — 어린이 기호식품 품질인증 현황 및 재심사 현황
- **카테고리**: 어린이식품안전관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0080/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `CHILD_FFQ_CRTFC_NO`(인증번호) / `BSSH_NM`(업소명) / `LCNS_NO`(인허가번호) / `PRDLST_CD_NM`(식품유형) / `PRDLST_NM`(제품명) / `CN_WT`(제품용량) / `APPN_BGN_DT`(인증일자) / `APPN_END_DT`(만료일자) / `CHILD_FAVOR_FOOD_TYPE_NM`(제품형태) / `PRDLST_REPORT_NO`(품목보고번호)

### `I0340` — 어린이 식품안전보호구역 관리 현황
- **카테고리**: 어린이식품안전관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0340/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `APPN_DT`(지정일자) · `SCHL_NM`(학교명)
- **응답 필드**: `HOLD_INSTT_NM`(관할기관) / `SCHL_NM`(학교명) / `FOOD_SAFE_PRTC_ZONE_NM`(식품안전보호구역지정명) / `ADDR`(위치) / `APPN_DT`(지정일자) / `BSSH_NO`(업소고유번호(미사용)) / `UPSO_NM`(업소명(미사용)) / `UPJONG`(업종(미사용)) / `keyId`(STRING(필수))

### `I2840` — 어린이 우수판매업소 지정현황
- **카테고리**: 어린이식품안전관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2840/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `APPN_DT`(지정일자(YYYYMMDD)) · `UPSO_NM`(업소명) · `GNT_NO`(인허가번호)
- **응답 필드**: `GNT_NO`(인허가번호) / `UPSO_NM`(업소명) / `UPJONG`(업종) / `ADDR`(주소) / `APLC_DT`(지정_일자) / `HOLD_INSTT_CD`(관할기관) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수))

### `I2846` — 어린이 급식센터 지원현황
- **카테고리**: 어린이식품안전관리
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2846/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `REPORT_YR`(년도(YYYY)) · `CNTER_NM`(센터명)
- **응답 필드**: `INSTT_NM`(관할기관) / `CNTER_NM`(센터명) / `REPORT_YR`(년도) / `REPORT_QU`(분기) / `KNDRGR_REG_CO`(유치원 수) / `KNDRGR_NMPR_CO`(유치원 인원수) / `DCCNTR_REG_CO`(어린이집 수) / `DCCNTR_NMPR_CO`(어린이집 인원수) / `ETC_REG_CO`(기타 수) / `ETC_NMPR_CO`(기타 인원수)


### 📁 카테고리: 위생용품 (2개)

### `I2714` — 위생용품수입업영업신고대장
- **카테고리**: 위생용품
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2714/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `LCNS_NO`(인허가번호) · `BSSH_NM`(업소명)
- **응답 필드**: `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `INDUTY_NM`(업종) / `PRMS_DT`(허가일자) / `LOCP_ADDR`(주소) / `INSTT_NM`(기관명) / `TELNO`(전화번호) / `keyId`(STRING(필수))

### `I2851` — 위생용품영업 생산실적보고
- **카테고리**: 위생용품
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2851/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `EVL_YR`(생산실적보고년도(YYYY)(필수)) · `LCNS_NO`(인허가번호) · `H_ITEM_NM`(품목유형)
- **응답 필드**: `BSSH_NM`(업소명) / `PRDLST_NM`(품목명) / `GUBUN`(품목구분) / `H_ITEM_NM`(품목유형) / `LCNS_NO`(인허가번호) / `EVL_YR`(보고년도) / `PRDLST_REPORT_NO`(품목제조보고번호) / `PRDCTN_QY`(생산량(KG/위생물수건:매)) / `keyId`(STRING(필수))


### 📁 카테고리: 축산물 (1개)

### `I1420` — 축산물 생산실적정보
- **카테고리**: 축산물
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1420/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `EVL_YR`(생산실적보고년도(YYYY)(필수)) · `LCNS_NO`(인허가번호) · `PRDLST_CD_NM`(품목유형) · `BSSH_NM`(업소명)
- **응답 필드**: `BSSH_NM`(업소명) / `PRDLST_NM`(품목명) / `GUBUN`(품목구분) / `H_ITEM_NM`(품목유형) / `LCNS_NO`(인허가번호) / `EVL_YR`(보고년도) / `PRDLST_REPORT_NO`(품목제조보고번호) / `FYER_PRDCTN_ABRT_QY`(연간생산능력(KG)) / `PRDCTN_QY`(생산량(KG))


### 📁 카테고리: 용어사전 (1개)

### `I2837` — 용어사전(기구용기포장∙식의약품용어집)
- **카테고리**: 용어사전
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2837/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `WORD`(단어) · `CHNG_DT`(변경일자)
- **응답 필드**: `WORD`(단어) / `FRNTNFISH`(외국어) / `DTL_DESC`(설명) / `KEYWORD`(연관어) / `SAUS`(출처) / `LAST_UPDT_DTM`(최종수정일) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수))


### 📁 카테고리: 코드정보 (8개)

### `C005` — 바코드연계제품정보
- **카테고리**: 코드정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/C005/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `PRDLST_REPORT_NO`(품목제조보고번호) · `BAR_CD`(바코드번호)
- **응답 필드**: `PRDLST_REPORT_NO`(품목보고(신고)번호) / `PRMS_DT`(보고(신고일)) / `END_DT`(생산중단일) / `PRDLST_NM`(제품명) / `POG_DAYCNT`(소비기한) / `PRDLST_DCNM`(식품 유형) / `BSSH_NM`(제조사명) / `INDUTY_NM`(업종) / `SITE_ADDR`(주소) / `CLSBIZ_DT`(폐업일자) / `BAR_CD`(유통바코드)

### `I2510` — 품목유형코드
- **카테고리**: 코드정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2510/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LAST_UPDT_DTM`(최종수정일(YYYYMMDD))
- **응답 필드**: `LV`(레벨) / `PRDLST_CD`(품목코드) / `KOR_NM`(한글명) / `ENG_NM`(영문명) / `DFN`(정의) / `VALD_BEGN_DT`(유효개시일자) / `VALD_END_DT`(유효종료일자) / `HRNK_PRDLST_CD`(상위품목코드) / `HTRK_PRDLST_CD`(최상위품목코드) / `MXTR_PRDLST_YN`(조합품목여부) / `ATTRB_SEQ`(속성일련번호) / `PIAM_KOR_NM`(속성한글명) … 외 7개

### `I2520` — 식품원재료코드
- **카테고리**: 코드정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2520/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `RPRSNT_RAWMTRL_NM`(원재료명)
- **응답 필드**: `RAWMTRL_CD`(원재료코드) / `RAWMTRL_LCLAS_NM`(대분류) / `RAWMTRL_MLSFC_NM`(중분류) / `RPRSNT_RAWMTRL_NM`(원재료명) / `RAWMTRL_NCKNM`(원재료이명) / `ENG_NM`(영문명) / `SCNM`(학명) / `REGN_CD`(부위코드) / `REGN_CD_NM`(부위코드명) / `PRCSS_PROCS_CD`(가공공정코드) / `PRCSS_PROCS_CD_NM`(가공공정코드명) / `RAWMTRL_STATS_CD`(원재료코드) … 외 5개

### `I2530` — 시험항목코드
- **카테고리**: 코드정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2530/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LAST_UPDT_DTM`(최종수정일(YYYYMMDD))
- **응답 필드**: `TESTITM_CD`(시험항목코드) / `KOR_NM`(한글명) / `ENG_NM`(영문명) / `ABRV`(약어) / `NCKNM`(이명) / `TESTITM_NM`(시험항목명) / `TESTITM_LCLAS_CD`(시험항목대분류시퀀스) / `L_ATTRB_CD`(시험항목대분류코드) / `L_KOR_NM`(대분류한글명) / `TESTITM_MLSFC_CD`(시험항목중분류시퀀스) / `M_ATTRB_CD`(시험항목중분류코드) / `M_KOR_NM`(중분류한글명) … 외 3개

### `I2540` — 법령코드
- **카테고리**: 코드정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2540/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `VALD_BGN_DT`(유효시작일자(YYYYMMDD)) · `VALD_END_DT`(유효종료일자(YYYYMMDD))
- **응답 필드**: `FOOD_LAWORD_CD`(법령코드) / `HRNK_LAWORD_CD`(상위법령코드) / `WORK_REALM_CD_NM`(업무분야) / `LAWORD_CD_NM`(법령명) / `ALL_LAWORD_CD_NM`(전체법령명) / `LV_NO`(레벨) / `USE_YN`(사용여부) / `VALD_BGN_DT`(유효시작일자) / `VALD_END_DT`(유효종료일자) / `LAST_UPDT_DTM`(최종수정일시)

### `I2550` — 처분기준코드
- **카테고리**: 코드정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2550/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `VALD_BGN_DT`(유효시작일자(YYYYMMDD)) · `VALD_END_DT`(유효종료일자(YYYYMMDD))
- **응답 필드**: `DSPS_STDR_CD`(처분기준코드) / `HRNK_DSPS_STDR_CD`(상위처분기준코드) / `LV_NO`(레벨) / `DSPS_STDR_CD_NM`(처분기준코드명) / `BASIS_LAWORD`(근거법령) / `VILT_TYPE_CD`(위반유형코드) / `VILT_TYPE_CD_NM`(위반유형명) / `USE_YN`(사용여부) / `VALD_BGN_DT`(유효시작일자) / `VALD_END_DT`(유효종료일자) / `LAST_UPDT_DTM`(최종수정일시)

### `I2560` — 영업소재지 GIS 코드
- **카테고리**: 코드정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2560/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(최종수정일) · `LCNS_NO`(인허가번호)
- **응답 필드**: `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `LOCPLC`(소재지) / `SAN`(산) / `LNBR`(번지) / `ISSNO`(호) / `TONG`(통) / `BAN`(반) / `SPCLADDR`(특수주소) / `SPCPPDONG`(특수지동) / `SPCPPISSNO`(특수지호) / `ROADNMSIGNGUCD`(도로명시군구코드) … 외 9개

### `I2570` — 유통바코드
- **카테고리**: 코드정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2570/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `PRDLST_REPORT_NO`(품목제조보고번호) · `PRDT_NM`(제품명) · `BRCD_NO`(바코드번호)
- **응답 필드**: `BRCD_NO`(바코드번호) / `PRDLST_REPORT_NO`(품목보고번호) / `CMPNY_NM`(회사명) / `PRDT_NM`(제품명) / `LAST_UPDT_DTM`(최종수정일시) / `PRDLST_NM`(품목분류_소분류) / `HRNK_PRDLST_NM`(품목분류_중분류) / `HTRK_PRDLST_NM`(품목분류_대분류) / `keyId`(STRING(필수))


### 📁 카테고리: 식품 등 (5개)

### `C004` — 식품접객업소 위생등급 지정현황
- **카테고리**: 식품 등
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/C004/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `LCNS_NO`(인허가번호) · `ASGN_FROM`(지정시작일(YYYYMMDD)) · `UPSO_NM`(업소명) · `ADDR`(주소) · `WRKR_REG_NO`(사업자등록번호)
- **응답 필드**: `HG_ASGN_NM`(지정기관) / `HG_ASGN_LV`(지정등급) / `HG_ASGN_NO`(지정번호) / `HG_ASGN_YMD`(지정일자) / `INDUTY_NM`(업종) / `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자) / `ADDR`(주소) / `ASGN_FROM`(지정시작일자) / `ASGN_TO`(지정종료일자) / `TELNO`(업소전화번호) … 외 6개

### `I0060` — 주류제조.면허자 식품제조.가공영업 등록 현황
- **카테고리**: 식품 등
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0060/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `LCNS_NO`(인허가번호)
- **응답 필드**: `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `ADDR`(주소) / `LCNS_NO`(인허가번호) / `INDUTY_NM`(업종명) / `PRMS_DT`(허가일자) / `INSTT_NM`(기관명) / `TELNO`(전화번호) / `keyId`(STRING(필수))

### `I0300` — 식품.식품첨가물 생산실적 보고 현황
- **카테고리**: 식품 등
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0300/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `EVL_YR`(생산실적보고년도(YYYY)(필수)) · `LCNS_NO`(인허가번호) · `BSSH_NM`(업소명) · `PRDLST_NM`(제품명) · `PRDLST_CD_NM`(품목유형)
- **응답 필드**: `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `SITE_ADDR`(주소) / `EVL_YR`(보고년도) / `PRDLST_REPORT_NO`(품목제조보고번호) / `H_ITEM_NM`(품목유형) / `PRDLST_NM`(품목명) / `FYER_PRDCTN_ABRT_QY`(연간생산능력(KG/옹기류:개)) / `PRDCTN_QY`(생산량(KG/옹기류:개))

### `I0680` — 위생관리등급별 업소 현황
- **카테고리**: 식품 등
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I0680/{xml|json}/{startIdx}/{endIdx}`
- **응답 필드**: `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `EVL_TYPE_DVS_NM`(평가유형) / `EVL_GRD_NM`(평가등급) / `EVL_DT`(평가일자) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수)) / `dataType`(STRING(필수)) / `startIdx`(STRING(필수))

### `I1560` — 식품위생교육내역
- **카테고리**: 식품 등
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I1560/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `LCNS_NO`(인허가번호((NULL값 존재)) · `COMPL_ST_DTM`(수료일자_범위_시작(YYYYMMDD)) · `COMPL_END_DTM`(수료일자_범위_종료(YYYYMMDD)) · `INSTT_CD_NM`(교육기관명) · `INDUTY_NM`(업종명)
- **응답 필드**: `EDC_TYPE_NM`(교육유형) / `EDC_DVS_NM`(교육구분) / `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `INDUTY_NM`(업종) / `EDC_OBJ_NM`(교육대상) / `CMPLTR_NAME`(성명) / `CTFHV_NO`(수료증번호) / `COMPL_DTM`(수료일자) / `EDC_MEDIA`(매체) / `EDC_COMPL_NMPR`(교육수료인원) / `INSTT_CD_NM`(교육기관명) … 외 3개


### 📁 카테고리: 업체인허가현황 (4개)

### `I-0010` — 식품조사처리업 인허가 현황
- **카테고리**: 업체인허가현황
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I-0010/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `LCNS_NO`(인허가번호)
- **응답 필드**: `LCNS_NO`(인허가 번호) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `INDUTY_NM`(업종) / `FOOD_HF_LS_CL_CD_NM`(식품건기축산분류) / `PRMS_DT`(허가일자) / `TELNO`(전화번호) / `LOCP_ADDR`(주소) / `keyId`(STRING(필수))

### `I2500` — 인허가 업소 정보
- **카테고리**: 업체인허가현황
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2500/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LCNS_NO`(영업고유구분번호(인허가번호)) · `INDUTY_CD_NM`(업종) · `BSSH_NM`(업소명) · `CHNG_DT`(최종수정일자(YYYYMMDD))
- **응답 필드**: `LCNS_NO`(영업고유구분번호(인허가번호)) / `INDUTY_CD_NM`(업종) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `TELNO`(전화번호) / `PRMS_DT`(허가일자) / `ADDR`(주소) / `keyId`(STRING(필수)) / `serviceId`(STRING(필수))

### `I2852` — 생산중단제품정보
- **카테고리**: 업체인허가현황
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2852/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `PRDLST_REPORT_NO`(품목제조보고번호) · `PRDLST_NM`(제품명) · `END_DT`(생산중단일자) · `FOOD_HF_LS_CL_CD`(구분(001:식품(식품첨가물),002:건강기능식품,003:축산물,011:위생용품)) · `PRMS_DT`(품목보고일자) · `LCNS_NO`(인허가번호)
- **응답 필드**: `PRDLST_REPORT_NO`(품목제조보고번호) / `PRMS_DT`(품목보고일자) / `PRDLST_NM`(제품명) / `END_DT`(생산중단일자) / `PRDLST_DCNM`(품목유형명) / `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `FOOD_HF_LS_CL_CD_NM`(구분) / `ARTCL_END_WHY`(생산중단사유)

### `I2856` — 푸드트럭지정현황조회
- **카테고리**: 업체인허가현황
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2856/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `LCNS_NO`(인허가번호) · `BSSH_NM`(업소명) · `CHNG_DT`(변경일자(YYYYMMDD))
- **응답 필드**: `LCNS_NO`(인허가번호) / `PRMS_DT`(인허가일자) / `INSTT_CDNM`(인허가기관명) / `INDUTY_CDNM`(업종명) / `BSSH_NM`(업소명) / `LOCP_ADDR`(업소주소) / `PRSDNT_NM`(업소대표자명) / `TELNO`(업소전화번호) / `CHNG_DT`(변경일자(YYYYMMDD))


### 📁 카테고리: 폐업정보 (4개)

### `I2817` — 식품보존업 폐업정보
- **카테고리**: 폐업정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2817/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `LCNS_NO`(인허가번호) · `CLSBIZ_DT`(폐업일자)
- **응답 필드**: `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `INDUTY_NM`(업종) / `PRMS_DT`(허가일자) / `CLSBIZ_DT`(폐업일자) / `CLSBIZ_DVS_CD_NM`(페업상태) / `LOCP_ADDR`(주소) / `INSTT_NM`(기관명)

### `I2821` — 수입식품업 폐업정보
- **카테고리**: 폐업정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2821/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `LCNS_NO`(인허가번호)
- **응답 필드**: `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `INDUTY_NM`(업종) / `PRMS_DT`(허가일자) / `CLSBIZ_DT`(폐업일자) / `CLSBIZ_DVS_CD_NM`(페업상태) / `LOCP_ADDR`(주소) / `INSTT_NM`(기관명)

### `I2822` — 건강기능식품 폐업정보
- **카테고리**: 폐업정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2822/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `LCNS_NO`(인허가번호) · `CLSBIZ_DT`(폐업일자)
- **응답 필드**: `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `INDUTY_NM`(업종) / `PRMS_DT`(허가일자) / `CLSBIZ_DT`(폐업일자) / `CLSBIZ_DVS_CD_NM`(페업상태) / `LOCP_ADDR`(주소) / `INSTT_NM`(기관명)

### `I2823` — 위생용품 폐업정보
- **카테고리**: 폐업정보
- **URL 패턴**: `http://openapi.foodsafetykorea.go.kr/api/{keyId}/I2823/{xml|json}/{startIdx}/{endIdx}`
- **추가 파라미터**: `CHNG_DT`(변경일자) · `LCNS_NO`(인허가번호) · `CLSBIZ_DT`(폐업일자)
- **응답 필드**: `LCNS_NO`(인허가번호) / `BSSH_NM`(업소명) / `PRSDNT_NM`(대표자명) / `INDUTY_NM`(업종) / `PRMS_DT`(허가일자) / `CLSBIZ_DT`(폐업일자) / `CLSBIZ_DVS_CD_NM`(페업상태) / `LOCP_ADDR`(주소) / `INSTT_NM`(기관명)



### 📊 카테고리별 통계

| 카테고리 | API 수 |
|---|---|
| HACCP지정현황 | 2 |
| 건강기능식품 | 10 |
| 수입식품 등 | 6 |
| 식품위해관리 | 14 |
| 기준규격정보 | 25 |
| 식품안전관리 | 4 |
| 식품영양정보 | 2 |
| 이력추적관리 | 1 |
| 검사기관정보 | 4 |
| 어린이식품안전관리 | 4 |
| 위생용품 | 2 |
| 축산물 | 1 |
| 용어사전 | 1 |
| 코드정보 | 8 |
| 식품 등 | 5 |
| 업체인허가현황 | 4 |
| 폐업정보 | 4 |
| **합계** | **97** |
