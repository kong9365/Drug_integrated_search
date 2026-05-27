# RegHub 360 — 공공데이터 API 신청 목록

> **목적**: 의약품·의약외품·식품 통합 규제정보 허브 구축에 필요한 공공데이터 API 인증키 신청 가이드
> **신청 사이트**: https://www.data.go.kr (공공데이터포털)
> **활용목적 기재 예시**: "사내 의약품/식품 규제정보 통합 조회 시스템 개발 및 PoC"
> **2026-05-26 업데이트**: 23개 신청 완료 (18 작동 + 5 End Point 대기), 마스크 관련 2개 프로젝트 제외

---

## ⭐ MVP 1차 — 24개 API (즉시 신청 권장)

### 🔵 의약품 (9개)

| NO | 서비스명 | 신청 URL | 비고 |
|----|---------|---------|------|
| 140 | 의약품 제품 허가정보 | https://www.data.go.kr/data/15095677/openapi.do | 제품 마스터 |
| 539 | 의약품 회수·판매중지 정보 | https://www.data.go.kr/data/15059114/openapi.do | ✓ 기존 연동 |
| 564 | 의약품 행정처분 정보 | https://www.data.go.kr/data/15058457/openapi.do | ✓ 기존 연동 |
| 547 | 의약품안전성서한 정보 | https://www.data.go.kr/data/15059182/openapi.do | RA/QA 핵심 |
| 531 | 의약품안전사용서비스(DUR) 품목정보 | https://www.data.go.kr/data/15059486/openapi.do | 병용·임부·연령금기 |
| 533 | 의약품안전사용서비스(DUR) 성분정보 | https://www.data.go.kr/data/15056780/openapi.do | DUR 성분 |
| 534 | 의약품 생산수입공급중단 정보 | https://www.data.go.kr/data/15057899/openapi.do | SCM 핵심 |
| 537 | 의약품공급부족 정보 | https://www.data.go.kr/data/15056886/openapi.do | SCM 핵심 |
| 563 | 의약품 낱알식별 정보 | https://www.data.go.kr/data/15057639/openapi.do | ✓ 기존 연동 |

### 🟡 의약외품 (1개) — 마스크 관련 제외 (2026-05-26)

| NO | 서비스명 | 신청 URL | 상태 |
|----|---------|---------|------|
| 145 | 의약외품 제품 허가 정보 | https://www.data.go.kr/data/15095679/openapi.do | ✅ 작동 확인 |

> ~~NO 518 의약외품 허가정보(구버전)~~ — NO 145로 대체, 신청 불요
> ~~NO 162 마스크 관련 업체 행정처분~~ — 프로젝트 범위에서 제외
> ~~NO 172 마스크 회수 제품 정보~~ — 프로젝트 범위에서 제외

### 🟢 식품 (10개)

| NO | 서비스명 | 신청 URL | 상태 |
|----|---------|---------|------|
| 339 | 식품의 회수 및 판매중지 정보 | https://www.data.go.kr/data/15074318/openapi.do | 🟡 승인됨, End Point 확인 대기 |
| 153 | 수입식품 회수판매중지 제품 정보 | https://www.data.go.kr/data/15095378/openapi.do | ✅ 작동 확인 |
| 225 | 해외 위해식품 회수정보 | https://www.data.go.kr/data/15077772/openapi.do | 🟡 승인됨, End Point 확인 대기 |
| 6 | 행정처분결과(식품제조가공업) | https://www.data.go.kr/data/15124560/openapi.do | ✅ 작동 확인 |
| 5 | 행정처분결과(식품판매업) | https://www.data.go.kr/data/15124559/openapi.do | ✅ 작동 확인 |
| 3 | 행정처분결과(수입식품업) | https://www.data.go.kr/data/15125111/openapi.do | ✅ 작동 확인 |
| 477 | 행정처분결과(식품접객업) | https://www.data.go.kr/data/15058429/openapi.do | 🟡 승인됨, End Point 확인 대기 |
| 444 | 식품(첨가물) 품목제조보고 | https://www.data.go.kr/data/15064909/openapi.do | 🟡 승인됨, End Point 확인 대기 |
| 470 | 식품(첨가물) 품목제조보고(원재료) | https://www.data.go.kr/data/15062098/openapi.do | 🟡 승인됨, End Point 확인 대기 |
| 1 | 식품영양성분DB정보 | https://www.data.go.kr/data/15127578/openapi.do | ✅ 작동 확인 |

> ~~NO 555 식품 영양성분 정보~~ — NO 1로 대체 가능, 신청 불요

---

## 🟠 MVP 2차 — 30개 API (Phase 2 진입 시 신청)

### 의약품 핵심 확장 (7개)

| NO | 서비스명 | 신청 URL |
|----|---------|---------|
| 248 | 의약품개요정보(e약은요) | https://www.data.go.kr/data/15075057/openapi.do |
| 269 | 묶음의약품정보서비스 (HIRA/ATC 매핑) | https://www.data.go.kr/data/15063908/openapi.do |
| 132 | 의약품GMP적합판정서발급현황 | https://www.data.go.kr/data/15097207/openapi.do |
| 142 | 의약품 국가출하승인정보 | https://www.data.go.kr/data/15095681/openapi.do |
| 144 | 의약품 등 업체허가현황 | https://www.data.go.kr/data/15095682/openapi.do |
| 483 | 원료의약품등록(DMF)현황 | https://www.data.go.kr/data/15057075/openapi.do |
| 134 | 안전상비의약품 정보 | https://www.data.go.kr/data/15097208/openapi.do |

### 의약품 R&D/BD (12개)

| NO | 서비스명 | 신청 URL |
|----|---------|---------|
| 561 | 의약품 특허정보 | https://www.data.go.kr/data/15057623/openapi.do |
| 557 | 국내소송 의약품(특허) 정보 | https://www.data.go.kr/data/15056710/openapi.do |
| 552 | FDA Paragraph IV 대상 의약품 특허 | https://www.data.go.kr/data/15058137/openapi.do |
| 562 | FDA 오렌지북 특허정보 | https://www.data.go.kr/data/15057931/openapi.do |
| 566 | 의약품 임상시험 정보 | https://www.data.go.kr/data/15056835/openapi.do |
| 568 | 의약품임상시험 실시기관 정보 | https://www.data.go.kr/data/15058129/openapi.do |
| 484 | 대조약조회 | https://www.data.go.kr/data/15058806/openapi.do |
| 485 | 생동성인정품목조회 | https://www.data.go.kr/data/15058447/openapi.do |
| 554 | 의약품 재심사 정보 | https://www.data.go.kr/data/15058034/openapi.do |
| 556 | 의약품 재평가 정보 | https://www.data.go.kr/data/15057382/openapi.do |
| 565 | 희귀의약품 정보 | https://www.data.go.kr/data/15057935/openapi.do |
| 81 | 희귀필수의약품 | https://www.data.go.kr/data/15107573/openapi.do |

### 식품 확장 (7개)

| NO | 서비스명 | 신청 URL |
|----|---------|---------|
| 469 | 검사부적합(국내) | https://www.data.go.kr/data/15063677/openapi.do |
| 535 | 검사 부적합 식품정보 | https://www.data.go.kr/data/15056516/openapi.do |
| 491 | 식품 유해물질 기준규격 정보 | https://www.data.go.kr/data/15058838/openapi.do |
| 538 | 식품 허위·과대광고정보 | https://www.data.go.kr/data/15058599/openapi.do |
| 12 | 식품 스마트HACCP 인증업체 정보 | https://www.data.go.kr/data/15118080/openapi.do |
| 13 | 축산물 스마트HACCP 인증업체 정보 | https://www.data.go.kr/data/15118113/openapi.do |
| 128 | HACCP 적용업소 지정 현황 | https://www.data.go.kr/data/15098712/openapi.do |

### 건강기능식품 (4개)

| NO | 서비스명 | 신청 URL |
|----|---------|---------|
| 478 | 건강기능식품 품목제조 신고사항 현황 | https://www.data.go.kr/data/15058865/openapi.do |
| 51 | 건강기능식품 GMP 지정현황 조회 | https://www.data.go.kr/data/15111987/openapi.do |
| 203 | 건강기능식품 영양DB | https://www.data.go.kr/data/15085712/openapi.do |
| 334 | 건강기능식품 개별인정형 정보 | https://www.data.go.kr/data/15074311/openapi.do |

---

## 🟣 Phase 3 — 마약류 통계 시리즈 (14개)

R&D/BD/마약류 사업 시 신청.

| NO | 서비스명 | 신청 URL |
|----|---------|---------|
| 278 | 마약류취급완료보고 사용내역 정보 | https://www.data.go.kr/data/15074221/openapi.do |
| 281 | 분류별 마약류취급자 정보 | https://www.data.go.kr/data/15074227/openapi.do |
| 286 | 마약류 취급완료보고 정보 | https://www.data.go.kr/data/15074217/openapi.do |
| 291 | 마약류취급승인 취급품목정보 | https://www.data.go.kr/data/15074184/openapi.do |
| 295 | 마약류 생산(수출입)실적 정보 | https://www.data.go.kr/data/15074205/openapi.do |
| 298 | 연도별 마약류취급승인정보 | https://www.data.go.kr/data/15074234/openapi.do |
| 301 | 분류별 마약류품목정보 | https://www.data.go.kr/data/15074235/openapi.do |
| 303 | 연도별 마약류취급자 정보 | https://www.data.go.kr/data/15074225/openapi.do |
| 307 | 희귀의약품성분 정보 | https://www.data.go.kr/data/15073980/openapi.do |
| 309 | 마약류원료물질 취급승인 취급품목정보 | https://www.data.go.kr/data/15074224/openapi.do |
| 314 | 마약류원료물질제조정보 | https://www.data.go.kr/data/15074223/openapi.do |
| 319 | 마약류취급자 허가정보 | https://www.data.go.kr/data/15074173/openapi.do |
| 543 | 마약류 약물 및 오남용 정보 | https://www.data.go.kr/data/15058963/openapi.do |
| 558 | 마약류 및 원료물질 정보 | https://www.data.go.kr/data/15058041/openapi.do |

---

## 📋 신청 절차

### Step 1. 공공데이터포털 로그인
- https://www.data.go.kr 접속 → 회원가입/로그인 (간편 인증 또는 ID/PW)

### Step 2. 각 API 페이지 활용신청
1. 위 표의 신청 URL 클릭
2. 우상단 **"활용신청"** 버튼 클릭
3. 신청 양식 작성:
   - **활용목적**: "사내 의약품/식품 규제정보 통합 조회 시스템 개발 및 PoC"
   - **시스템유형**: 일반
   - **사용기간**: 1년 (기본)
   - **상세 활용 내용**: "의약품·의약외품·식품 통합 규제정보 플랫폼 RegHub 360 구축 — RA/QA/QC/SCM/R&D 부서별 워크스페이스, 통합 이벤트 타임라인, 리스크 모니터링"
4. **이용허락범위 동의** → 신청

### Step 3. 승인 확인
- **개발계정**은 보통 **즉시 자동승인** (1일 10,000회 호출 한도)
- 마이페이지 → 개발계정: https://www.data.go.kr/iim/api/selectAcountList.do
- 승인 메일 수신 → 인증키 확인 가능

### Step 4. 인증키 수집
각 API 페이지에서 두 가지 형태 키 확인:
- **일반 인증키(Encoding)**: URL에 그대로 붙여 사용
- **일반 인증키(Decoding)**: 코드에서 가공 시 사용

> 💡 **팁**: 식약처 계열 API들은 보통 **하나의 통합 SERVICE_KEY** 로 다수 API 호출 가능. 기존 [config.py](drug_integrated_search/config.py) 의 키도 3개 API에 공통 적용됨.

### Step 5. 키 전달 (Claude에게)
다음 형식으로 메시지에 붙여 전달:

```
=== 인증키 등록 요청 ===

[공통 키]
SERVICE_KEY: <Decoding 키 전체 붙여넣기>

[API별 키가 다른 경우만]
NO 140 (의약품 허가): <키>
NO 547 (안전성서한): <키>
NO 339 (식품 회수): <키>
... (받은 것만 적기)

[추가 정보]
- 운영계정 신청 여부:
- 응답 형식 선호: JSON / XML
```

---

## ✅ 한 눈에 보기 — MVP 1차 진행 현황 (2026-05-26)

총 23개 신청 (마스크 제외) — **18개 작동 확인 완료**, **5개 End Point 확인 대기**.

**의약품 (9개 — 전부 ✅)**
- [x] NO 140 의약품 제품 허가정보 ⭐404 해결
- [x] NO 539 의약품 회수·판매중지 정보
- [x] NO 564 의약품 행정처분 정보
- [x] NO 547 의약품안전성서한 정보
- [x] NO 531 의약품 DUR 품목정보
- [x] NO 533 의약품 DUR 성분정보
- [x] NO 534 의약품 생산수입공급중단
- [x] NO 537 의약품공급부족 정보
- [x] NO 563 의약품 낱알식별 정보

**의약외품 (1개 — ✅)**
- [x] NO 145 의약외품 제품 허가 정보

**식품 (8개 작동 ✅ + 5개 End Point 대기 🟡)**
- [x] NO 153 수입식품 회수판매중지
- [x] NO 6 행정처분결과(식품제조가공업)
- [x] NO 5 행정처분결과(식품판매업)
- [x] NO 3 행정처분결과(수입식품업)
- [x] NO 1 식품영양성분DB정보
- [ ] 🟡 NO 339 식품 회수 및 판매중지 — **End Point 확인 필요**
- [ ] 🟡 NO 225 해외 위해식품 회수 — **End Point 확인 필요**
- [ ] 🟡 NO 477 행정처분결과(식품접객업) — **End Point 확인 필요**
- [ ] 🟡 NO 444 식품(첨가물) 품목제조보고 — **End Point 확인 필요**
- [ ] 🟡 NO 470 식품 품목제조보고 원재료 — **End Point 확인 필요**

### 🟡 End Point 확인 절차 (5개)

1. https://www.data.go.kr/iim/api/selectAcountList.do 마이페이지 > 개발계정
2. 각 API "상세보기" 클릭 → "기본정보 > End Point" URL 복사
3. "활용신청 상세기능정보" 표의 함수명 복사
4. Claude에게 5개 모두 전달 → 자동 등록 + smoke test 재실행

### ⚪ 프로젝트 제외 (2개)
- ~~NO 162 마스크 관련 업체 행정처분~~
- ~~NO 172 마스크 회수 제품 정보~~

---

## 📌 참고사항

- **기존 보유 키**: [config.py:14](config.py) 에 식약처 발급 키가 있으며, 현재 NO 539/564/563(회수/행정처분/낱알식별)에 적용 중. 동일 키로 의약품 계열 신규 API들도 호출 가능성 높음 → 신청 시 시도해볼 것.
- **호출 한도**: 개발계정 10,000회/일. RegHub 360은 야간 배치 + Redis 캐시 구조이므로 충분.
- **운영계정**: 활용사례 등록 후 신청 가능, 호출 한도 무제한. MVP 안정화 후 단계적 전환.
- **장애 폴백**: 의약품 허가정보(NO 140)는 [config.py:22](config.py) 의 엔드포인트에서 404 발생 이력 있음 → 식약처 엑셀 다운로드 폴백([excel_data_loader.py](excel_data_loader.py)) 유지.
