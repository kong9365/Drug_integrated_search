# KD-IRIS — API 작동 현황

> **마지막 업데이트**: 2026-05-29 (식품안전나라 KeyID 활성 + 한약 NO35/90 승인 반영)
> **공통 SERVICE_KEY 발급일**: 2026-05-26 (활용기간 2년)
> **상세 연결 현황**: → [`API_REFERENCE.md` § 🔌 현재 통합·활용 현황](API_REFERENCE.md) (API별 fetch 함수·연결 화면·상태)
> **테스트 스크립트**: [smoke_test_apis.py](smoke_test_apis.py)

---

## 📊 종합 현황 (2026-05-29 기준)

| 구분 | 건수 | 비고 |
|------|------|------|
| 🟢 data.go.kr 작동 (의약품·의약외품·식품) | **40+ 오퍼레이션** | 허가·회수·처분·DUR·특허·임상·재심사·GMP 등 전수 작동 |
| 🟢 식품안전나라 활성 (`FOODSAFETY_KEY_ID`) | **7 서비스** | I0490·I2630·I2810 + 건기식 I-0050·I0760·I0030 + 식품공전 I0930 |
| 🟢 한약(생약) NO 90 회수 | **작동 (290건)** | 이벤트 모니터 연결 |
| ⚠️ 한약(생약) NO 35 허가기원 | **403 전파지연** | 엔드포인트·키 정상, 승인(2026-05-29) 전파 대기 |
| ✅ 화면 연결 | **핵심 전수** | 검색·모니터·워치리스트·제품상세·5개 워크스페이스·홈·검사부적합 |
| ⚪ 함수 보유·미연결 | 소수 | 회수 상세(드릴다운)·DUR성분(533)·업체상세(144)·식품안전나라 이벤트 5종(data.go.kr 동등본 사용) |
| ⚪ 프로젝트 제외 | 2 | 마스크 관련 (사용자 결정) |

> 키·엔드포인트는 **전부 등록·인증되어 호출 가능**. 미연결 항목은 "상세 드릴다운" 또는 "data.go.kr↔식품안전나라 중복본"이라 의도적 보류.

---

## 🟢 작동 중 — 18개 API (21개 오퍼레이션)

모든 호출이 HTTP 200 + resultCode=00 + 정상 데이터 반환 확인.

### 의약품 (9개)

| NO | 서비스명 | 오퍼레이션 | totalCount | 응답 필드 샘플 |
|----|---------|-----------|-----------:|--------------|
| **140** | 의약품 제품 허가정보 (목록) ⭐404 해결 | `getDrugPrdtPrmsnInq07` | 7 | ITEM_SEQ, ITEM_NAME, ITEM_ENG_NAME, ENTP_NAME |
| 140 | 의약품 제품 허가정보 (상세) | `getDrugPrdtPrmsnDtlInq06` | 7 | ITEM_SEQ, ITEM_NAME, ENTP_NAME, ITEM_PERMIT_DATE |
| 140 | 의약품 제품 주성분 상세 | `getDrugPrdtMcpnDtlInq07` | 127,124 | ENTRPS_PRMISN_NO, ENTRPS, PRDUCT, MTRAL_SN |
| 564 | 의약품 행정처분 정보 | `getMdcinExaathrList04` | 614 | ADM_DISPS_SEQ, ENTP_NAME, ADDR, ENTP_NO |
| 539 | 의약품 회수·판매중지 목록 | `getMdcinRtrvlSleStpgelList03` | 948 | PRDUCT, ENTRPS, RTRVL_RESN, ENFRC_YN |
| 539 | 의약품 회수·판매중지 상세 | `getMdcinRtrvlSleStpgeItem03` | 948 | ENTRPS, ENTRPS_ADRES, ENTRPS_TELNO, PRDUCT |
| 539 | 의약품외 회수·판매중지 목록 | `getMdcinRtrvlSleStpgelEtcList02` | 191 | PRDUCT, ENTRPS, RTRVL_RESN, ENFRC_YN |
| 563 | 의약품 낱알식별 | `getMdcinGrnIdntfcInfoList03` | 4 | ITEM_SEQ, ITEM_NAME, ENTP_SEQ, ENTP_NAME |
| 547 | 의약품안전성서한 | `getDrugSafeLetterList02` | 320 | SAFT_LETT_NO, TITLE, PBANC_NO, PBANC_DIVS_CD |
| 534 | 의약품 생산수입공급중단 | `getMdcinPrdctnIncmeSuplyList` | 1,285 | REPORT_PGS_CODE, SUSPEND_REPORT_SEQ, SUPPLY_YN |
| 537 | 의약품 공급부족 | `getMdcinSuplyLackList01` | 733 | REPORT_PGS_CODE, SHORT_SUPPLY_REPORT_SEQ, ENTP_NAME |
| 531 | DUR 품목 — 9개 오퍼레이션 | `DURPrdlstInfoService03/*` | 811,620 / 23,535 외 | DUR_SEQ, TYPE_CODE, ITEM_NAME, MIX |
| 533 | DUR 성분 — 7개 오퍼레이션 | `DURIrdntInfoService03/*` | 1,816 / 1,433 외 | TYPE_NAME, MIX_TYPE, INGR_CODE, INGR_ENG_NAME |

### 의약외품 (1개)

| NO | 서비스명 | 오퍼레이션 | totalCount | 응답 필드 샘플 |
|----|---------|-----------|-----------:|--------------|
| 145 | 의약외품 제품 허가 정보 | `getQdrgPrdtPrmsnInfoInq03` | 22,986 | ITEM_SEQ, ITEM_NAME, ENTP_NAME, ITEM_PERMIT_DATE |

### 식품 (5개)

| NO | 서비스명 | 오퍼레이션 | totalCount | 응답 필드 샘플 |
|----|---------|-----------|-----------:|--------------|
| 1 | 식품 영양성분 DB | `getFoodNtrCpntDbInq02` | 282,296 | NUM, FOOD_CD, FOOD_NM_KR, DB_GRP_CM |
| 3 | 행정처분(수입식품업) | `getAdmmRsltIprtFoodService` | 56 | PRCSCITYPOINT_BSSHNM, INDUTY_CD_NM, LCNS_NO, DSPS_DCSNDT |
| 5 | 행정처분(식품판매업) | `getAdmmRsltFoodSaleBssh` | 686 | (동일 스키마) |
| 6 | 행정처분(식품제조가공업) | `getAdmmRsltFoodMnftPrcsBssh` | 296 | (동일 스키마) |
| 153 | 수입식품 회수판매중지 | `getIprtFoodReclSaleStopPrdtStusInq` | 1,095 | PRDT_NM, CLNT_BSSH_NM, MNFT_YMD_RLAT_CONT, CIRC_PRD |

---

## 🟡 승인됐으나 End Point 확인 필요 — 5개

> **동일 SERVICE_KEY 사용 확정** (사용자 확인). 다만 `OpenAPI 신청 목록.txt` 에 명시된 데이터명만 있고 End Point URL은 누락됨.
> Smoke test 가 22개 후보 명명 패턴을 시도했으나 모두 HTTP 500 → 정식 명세 확인 필요.

| NO | 서비스명 | 신청 URL | 마이페이지 |
|----|---------|---------|---------|
| 339 | 식품의 회수 및 판매중지 정보 | https://www.data.go.kr/data/15074318/openapi.do | 상세보기 → End Point 확인 |
| 225 | 해외 위해식품 회수정보 | https://www.data.go.kr/data/15077772/openapi.do | 상세보기 → End Point 확인 |
| 444 | 식품(첨가물) 품목제조보고 | https://www.data.go.kr/data/15064909/openapi.do | 상세보기 → End Point 확인 |
| 470 | 식품(첨가물) 품목제조보고(원재료) | https://www.data.go.kr/data/15062098/openapi.do | 상세보기 → End Point 확인 |
| 477 | 행정처분결과(식품접객업) | https://www.data.go.kr/data/15058429/openapi.do | 상세보기 → End Point 확인 |

### 🆘 사용자 액션 — End Point 확인 절차

1. https://www.data.go.kr/iim/api/selectAcountList.do (마이페이지 > 개발계정)
2. 위 5개 API 각각의 **"상세보기"** 클릭
3. **"기본정보"** 섹션에서 다음 두 값 복사:
   - **End Point**: `https://apis.data.go.kr/1471000/<ServiceName>`
   - **활용신청 상세기능정보** 표의 **상세기능 함수명** (예: `/get<XXX>List`)
4. Claude에게 전달:

```
NO 339:
  End Point: https://apis.data.go.kr/1471000/<XXX>
  오퍼레이션: /get<XXX>
NO 225:
  End Point: ...
  오퍼레이션: ...
NO 444:
  End Point: ...
  오퍼레이션: ...
NO 470:
  End Point: ...
  오퍼레이션: ...
NO 477:
  End Point: ...
  오퍼레이션: ...
```

5건 전달 후 Claude가 [config.py](config.py) 에 자동 등록 + smoke test 재실행 → 23/23 통과 완성.

---

## ⚪ 프로젝트 제외 — 2개 (마스크 관련)

사용자 결정으로 RegHub 360 범위에서 제외:
- ~~NO 162 마스크 관련 업체 행정처분 정보~~
- ~~NO 172 마스크 회수 제품 정보~~

향후 의약외품 카테고리 확장 시 재검토 가능.

---

## 🔧 기술 노트

### 인증키 동작 검증
- 현재 [config.py:15-18](config.py) 의 SERVICE_KEY는 2026-05-26 발급된 키와 동일
- **단일 SERVICE_KEY로 18개 API 21개 오퍼레이션 호출 성공** (개발계정 각 API 10,000회/일)
- 신규 5개도 동일 SERVICE_KEY 사용 확정 (사용자 확인)
- URL 인코딩(`%2B`, `%2F`, `%3D`) 자동 처리는 [api_client.py:39-46](api_client.py) 의 `_clean_service_key()` 가 담당

### NO 140 의약품 허가정보 404 해결 경위
- **이전 문제**: 기존 [config.py](config.py) 의 함수명 `getDrugPrdtPrmsnList07` 사용 → 404
- **원인**: 공식 함수명은 `getDrugPrdtPrmsnInq07` (List가 아닌 Inq)
- **해결**: 2026-05-26 [config.py](config.py) 의 `approval` 키를 `getDrugPrdtPrmsnInq07` 로 수정
- **검증**: smoke test에서 "타이레놀" 검색 시 7건 정상 반환
- **결론**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 의 의약품 허가정보 API 404 이슈는 **함수명 오타가 원인**이었음. 식약처 문의 불필요. 엑셀 폴백도 더 이상 필수 아님(상시 보조용으로만 유지).

### 신규 5개 자동 탐색 실패 원인 분석
- 22개 후보 URL 모두 HTTP 500 반환
- 500은 "엔드포인트 자체는 라우팅됐으나 함수명/파라미터 오류"를 의미
- → 실제 End Point는 추측 패턴과 다른 명명 사용 (예: 약어, 다른 접두사)
- → 마이페이지 정식 명세 확인이 유일한 정확한 방법

### 응답 형식
- 전 API JSON+XML 모두 지원 (`type=xml` 또는 `type=json` 파라미터)
- 현재 [api_client.py](api_client.py) 는 XML 파싱 사용
- 향후 JSON 통일 시 응답 코드 단순화 가능

### 활용기간
- 대부분 API 활용기간: 2026-05-26 ~ 2028-05-26 (2년)
- 일부 기존 API(낱알식별, 의약외품, 회수, 행정처분) 활용기간: 2025년~2027년
- 만료 전 재신청 필요 — Phase 3 운영 단계에서 알림 체계 구축

---

## 📜 변경 이력

| 일자 | 변경 |
|------|------|
| **2026-05-26 v2** | 신규 5개 승인 반영(NO 339·225·444·470·477) — End Point 확인 대기 / 마스크 2개 프로젝트 제외 / 식품안전나라 별도 인증 체계는 폴백용으로만 유지 |
| 2026-05-26 v1 | smoke test 21/22 통과 — NO 140 의약품 허가정보 404 해결, 식품안전나라 별도 인증 체계 명시 |
| 2025-11-13 | 의약품 허가정보 API 404 오류 확인 (함수명 오타가 원인이었음 — 2026-05-26 해결) |
