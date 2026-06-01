# KD-IRIS — API 정보 표기 누락 점검 보고서

> 작성일 2026-06-01 · 기준 품목 **베니톨정(199401695)** / **니페딕스지속정(200502319)** 실측
> 목적: 각 공공데이터 API가 반환하는 필드가 화면에 **누락 없이** 표기되는지 검증.

## 0. 핵심 결론

| 표시 화면 | 대상 API | 표기 보장 | 비고 |
|---|---|:---:|---|
| 품목마스터 9탭 · **허가상세** | NO140 상세 | ✅ **100%** | 명시 행 + **원본 전체 필드 덤프** 추가 |
| Product360 · **허가상세** | NO140 상세 | ✅ **100%** | 동일 덤프 추가 |
| Product360 · 낱알식별 탭 | 낱알식별 | ✅ 핵심 전부 | 내부 좌표/조각 필드만 제외 |
| 규제 모니터링 · **이벤트 상세** | 회수·처분·서한·GMP | ✅ **100%** | `원시 API 데이터` 접기(raw_payload) |
| 광동 허가 현황 | NO140(회사명) | ◐ 핵심 | 백본 목록용 — 의도적 요약 |

**판정**: 필드를 한 건씩 읽는 모든 상세 화면은 이제 **"명시 표 + 원본 전체 필드 덤프"** 2중 구조로 **무손실**을 보장합니다. 집계/카운트성 화면(워크스페이스 등)은 본래 상세표시 대상이 아닙니다.

---

## 1. 필드 상세 표시 API (제품·품목 상세)

### 1-1. 의약품 허가상세 — `getDrugPrdtPrmsnDtlInq06` (NO 140 상세)
- **반환 42필드**(실측): ATC_CODE, BAR_CODE, BIZRNO, CANCEL_DATE, CANCEL_NAME, CHANGE_DATE, CHART, CNSGN_MANUF, EDI_CODE, EE_DOC_DATA, EE_DOC_ID, ENTP_ENG_NAME, ENTP_NAME, ENTP_NO, ETC_OTC_CODE, GBN_NAME, INDUTY_TYPE, INGR_NAME, INSERT_FILE, ITEM_ENG_NAME, ITEM_NAME, ITEM_PERMIT_DATE, ITEM_SEQ, MAIN_INGR_ENG, MAIN_ITEM_INGR, MAKE_MATERIAL_FLAG, MATERIAL_NAME, NARCOTIC_KIND_CODE, NB_DOC_DATA, NB_DOC_ID, NEWDRUG_CLASS_NAME, PACK_UNIT, PERMIT_KIND_NAME, PN_DOC_DATA, RARE_DRUG_YN, REEXAM_DATE, REEXAM_TARGET, STORAGE_METHOD, TOTAL_CONTENT, UD_DOC_DATA, UD_DOC_ID, VALID_TERM
- **표기 위치**: `품목마스터 → 허가상세 탭`, `Product360 → 허가상세 탭`
- **이번 보강(2026-06-01)**: 누락 행 추가 — 유효성분(MAIN_ITEM_INGR)·첨가제명(INGR_NAME)·총량·변경이력(GBN_NAME)·취소상태(CANCEL_NAME)·완제/원료(MAKE_MATERIAL_FLAG)·업종(INDUTY_TYPE)·첨부문서(II). **+ `🔎 API 원본 전체 필드(N개)` 덤프**로 42필드 전수 노출.
- **판정**: ✅ **누락 0** (덤프로 신규 필드까지 자동 노출)

### 1-2. 의약품 허가목록 — `getDrugPrdtPrmsnInq07` (NO 140 목록)
- **반환 21필드**: BIG_PRDT_IMG_URL, BIZRNO, CANCEL_DATE/NAME, EDI_CODE, ENTP_ENG_NAME, ENTP_NAME, ENTP_NO, ENTP_SEQ, INDUTY, ITEM_ENG_NAME, ITEM_INGR_CNT, ITEM_INGR_NAME, ITEM_NAME, ITEM_PERMIT_DATE, ITEM_SEQ, PERMIT_KIND_CODE, PRDLST_STDR_CODE, PRDUCT_PRMISN_NO, PRDUCT_TYPE, SPCLTY_PBLC
- **⚠ 주의(실측)**: 목록 함수는 **`item_seq` 파라미터를 무시**합니다(199401695 조회 시 엉뚱한 품목 반환). 정확 조회는 **상세(DtlInq06)** 로, 회사명 일괄은 **`entp_name`(서버 필터 정상)** 으로.
- **표기 위치**: 허가번호(497)·업소일련번호 등 목록 고유 필드는 헤더/광동 허가 현황에서 표기. 나머지는 상세에 흡수.
- **판정**: ✅ 상세와 합쳐 전 필드 커버

### 1-3. 낱알식별 — `getMdcinGrnIdntfcInfoList03`
- **반환 33필드**: BIZRNO, CHANGE_DATE, CHART, CLASS_NAME, CLASS_NO, COLOR_CLASS1/2, DRUG_SHAPE, EDI_CODE, ENTP_NAME, ENTP_SEQ, ETC_OTC_NAME, FORM_CODE_NAME, IMG_REGIST_TS, ITEM_ENG_NAME, ITEM_IMAGE, ITEM_NAME, ITEM_PERMIT_DATE, ITEM_SEQ, LENG_LONG/SHORT, THICK, PRINT_FRONT/BACK, LINE_FRONT/BACK, STD_CD, MARK_CODE_FRONT/BACK(+_ANAL/_IMG)
- **표기 위치**: Product360 낱알 탭(제형·색상·앞뒤각인·장단축·두께·이미지·분류번호/명·표준코드) + 품목마스터 헤더 낱알 이미지.
- **판정**: ✅ 사람이 읽는 핵심 전 필드 표기. 내부용 `MARK_CODE_*_ANAL/_IMG`(각인 이미지 조각·좌표)만 비표시(불필요).

### 1-4. e약은요 — `getDrbEasyDrugList` (`fetch_drug_easy`)
- **주요 필드**: efcyQesitm(효능), useMethodQesitm(용법), atpnQesitm(주의), depositMethodQesitm(보관), seQesitm(이상반응), intrcQesitm(상호작용)
- **표기 위치**: Product360 — NO140 상세 실패 시 **폴백**으로 효능/용법/주의/보관 표시.
- **판정**: ✅ 폴백 용도 핵심 필드 표기 (베니톨정은 e약은요 DB 미수록 → 빈 결과 정상)

---

## 2. 규제 모니터링 API (이벤트 상세 = 원본 payload 접기)

> 회수·처분·서한·GMP는 일별 스냅샷 → diff → `event` 적재 → **이벤트 상세 화면**에서 표시.
> 이벤트 상세에는 **`원시 API 데이터`(raw_payload JSON 전문) 접기**가 있어 **반환 전 필드 무손실** 확인 가능.

| API | 함수 | 반환 필드(실측) | 표기 |
|---|---|---|:---:|
| 회수·판매중지 | `getMdcinRtrvlSleStpgeItem03` | 9: PRDUCT, ENTRPS, BIZRNO, ITEM_SEQ, STD_CD, RTRVL_RESN, RTRVL_CMMND_DT, RECALL_COMMAND_DATE, ENFRC_YN | ✅ raw 전문 |
| 행정처분 | `getMdcinExaathrList04` | 12: ENTP_NAME, ITEM_NAME, ADM_DISPS_NAME, EXPOSE_CONT, BEF_APPLY_LAW, ADDR, BIZRNO, LAST_SETTLE_DATE, RLS_END_DATE … | ✅ raw 전문 |
| 안전성서한 | (안전성정보) | 14: TITLE, SUMRY_CONT, PBANC_CONT, ACTN_MTTR_CONT, ATTACH_FILE_URL, CHRG_DEP, PBANC_YMD, SAFT_LETT_NO … | ✅ raw 전문 |
| GMP 적합판정 | `getDrugGMPList` | 6: BSSH_NM, FCTR_ADDR, BIZRNO, GMP_INGR_MM_GROUP_NAME, KGMP_BGMP_NAME, VLD_PRD_YMD | ✅ raw 전문 |
| 재심사/재평가 | `fetch_drug_review/reeval` | 12: ITEM_NAME, REEXAM_CODE_NM, REEXAM_START_DATE, RESULT_DATE, YEAR_REPORT_DEADLINE_DATE, CLASS_NO_NM, FACTORY_ADDR … | ✅ Product360 변경이력 시계열 |

**판정**: ✅ 이벤트 상세 `원시 API 데이터` 접기로 **전 필드 무손실**. 카드/표는 핵심 요약, 전문은 접기에서.

---

## 3. 집계·워크스페이스·식품 API (상세표시 비대상)

DUR(병용·임부·노인), 의약외품(145), 한약(35/90), 특허/소송/FDA/임상, 식품(영양·HACCP·행정처분·회수·검사부적합·건기식) 등 ~30종은
**카운트·리스트·차트 집계** surface(워크스페이스/모니터)에서 활용됩니다. 필드 한 건씩 읽는 상세표시 대상이 아니므로
"필드 누락" 기준이 아니라 **집계 정확도** 기준으로 관리합니다. (PoC 동결 범위 포함)

---

## 4. 이번 작업 변경점 (요청 #1·#2)

1. **품목마스터 허가상세** — 누락 행 8종 추가 + `원본 전체 필드 덤프` → 무손실 (요청 #1)
2. **Product360 허가상세** — 동일 `원본 전체 필드 덤프` 추가 → 무손실 (요청 #1)
3. **포장단위 탭 삭제** — 허가상세의 PACK_UNIT(포장단위)와 중복이므로 9탭에서 제거 (요청 #2)
   - 포장규격은 헤더 + 허가상세에 유지, `포장자재` 탭(SAP 연동 대기)은 존속.

## 5. 권고

- 신규 필드가 API에 추가돼도 **원본 덤프**가 자동 노출하므로 별도 코드 수정 불필요.
- 회수·처분 등도 필요 시 카드에 핵심 컬럼을 추가할 수 있으나, 현재 `원시 데이터 접기`로 충분.
