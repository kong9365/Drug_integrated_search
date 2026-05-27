# 의약품 제품 허가정보 API 명세서

## 기본 정보

- **데이터명**: 식품의약품안전처_의약품 제품 허가정보
- **서비스 유형**: REST
- **데이터 포맷**: JSON+XML
- **Base URL**: `https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07`
- **활용기간**: 2025-10-31 ~ 2027-10-31
- **일일 트래픽**: 10,000건

## 상세기능

### 1. 의약품 제품 허가 목록
- **설명**: 의약품 제품 허가 목록 조회
- **일일 트래픽**: 10,000건

## 요청 파라미터

### 필수 파라미터
- `serviceKey` (string): 공공데이터포털에서 발급 받은 인증키 (URL Encode)
- `pageNo` (int): 페이지 번호 (기본값: 1)
- `numOfRows` (int): 한 페이지 결과수 (기본값: 3)
- `type` (string): 응답데이터 형식 (xml/json, 기본값: xml)

### 선택 파라미터
- `item_name` (string): 품목명
- `entp_name` (string): 업체명
- `induty` (string): 업종
- `spclty_pblc` (string): 전문/일반구분
- `prdlst_Stdr_code` (string): 품목일련번호
- `prduct_prmisn_no` (string): 품목허가번호
- `entp_seq` (string): 업일련번호
- `entp_no` (string): 업허가번호
- `edi_code` (string): 보험코드
- `item_ingr_name` (string): 주성분
- `bizrno` (string): 사업자등록번호
- `item_permit_date` (string): 허가일자 (YYYYMMDD 형식)
- `bar_code` (string): 표준코드
- `item_seq` (string): 품목기준코드
- `start_change_date` (string): 변경일자 시작 (YYYYMMDD)
- `end_change_date` (string): 변경일자 종료 (YYYYMMDD)
- `atc_code` (string): ATC코드
- `rare_drug_yn` (string): 희귀의약품여부
- `main_item_ingr` (string): 유효성분

## 예시 요청

```
GET https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnList07?
serviceKey={인증키}&
pageNo=1&
numOfRows=10&
type=xml&
item_name=타이레놀정
```

## 인증키

- **Encoding 버전**: `REDACTED_KEY`
- **Decoding 버전**: `REDACTED_KEY`

**참고**: API 환경 또는 API 호출 조건에 따라 인증키가 적용되는 방식이 다를 수 있습니다. 포털에서 제공되는 Encoding/Decoding 된 인증키를 적용하면서 구동되는 키를 사용하시기 바랍니다.

## 응답 형식

### XML 응답 예시
```xml
<response>
  <header>
    <resultCode>00</resultCode>
    <resultMsg>NORMAL SERVICE.</resultMsg>
  </header>
  <body>
    <numOfRows>10</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>25354</totalCount>
    <items>
      <item>
        <ITEM_SEQ>200808876</ITEM_SEQ>
        <ITEM_NAME>가스디알정50밀리그램</ITEM_NAME>
        <ENTP_NAME>일동제약(주)</ENTP_NAME>
        <!-- 기타 필드 -->
      </item>
    </items>
  </body>
</response>
```

## 주요 응답 필드

- `ITEM_SEQ`: 품목기준코드
- `ITEM_NAME`: 품목명
- `ENTP_NAME`: 업체명
- `ITEM_PERMIT_DATE`: 허가일자
- `BIZRNO`: 사업자등록번호
- 기타 허가 관련 정보

## 현재 상태

⚠️ **주의**: 현재 모든 엔드포인트가 404 오류를 반환하고 있습니다.
- `getDrugPrdtPrmsnList07` - 404 오류
- `getDrugPrdtPrmsnDtlInq07` - 404 오류
- `getDrugPrdtPrmsnList06` - 404 오류

공공데이터포털에서 최신 함수명을 확인하거나 관리부서에 문의가 필요합니다.

## 참고

- 공공데이터포털: https://www.data.go.kr
- 관리부서: 식품의약품안전처 데이터혁신기획팀
- 전화: 043-719-1626

