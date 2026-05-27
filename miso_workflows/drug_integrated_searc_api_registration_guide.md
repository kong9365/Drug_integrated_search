# 공공데이터 API를 MISO 에 등록하는 방법

식품의약품안전처 공공데이터포털 4종 API 를 MISO 에 연결하는 방법은 **2가지** 다. 본 프로젝트는 **방법 1 (환경변수 + HTTP 요청 노드)** 을 기본으로 채택하였으며, 방법 2 도 보조적으로 사용 가능하다.

---

## 방법 1 (권장) — 환경변수 + HTTP 요청 노드

본 저장소의 4개 YAML 이 모두 이 방식을 사용한다.

### 1-1. 원리

- 각 앱의 `environment_variables` 섹션에 `DATA_GO_KR_BASE`(string) 와 `SERVICE_KEY`(secret) 를 선언
- 워크플로우 HTTP 요청 노드에서 `url: {{#env.DATA_GO_KR_BASE#}}/<서비스명>/<함수명>` 으로 참조
- `params:` 블록에 `serviceKey: {{#env.SERVICE_KEY#}}` 포함 → MISO 가 URL 인코딩 수행

### 1-2. 장점

- DSL 가져오기 한 번으로 등록 완료 (UI 작업 불필요)
- 인증키 회전 시 환경변수 1곳만 수정
- 앱별 격리 — 키가 다른 워크스페이스로 복제돼도 환경변수가 따라감
- 엔드포인트·파라미터·헤더·타임아웃을 워크플로우 내에서 통째로 검토 가능

### 1-3. 사용 예 (YAML 발췌)

```yaml
environment_variables:
  - name: DATA_GO_KR_BASE
    value_type: string
    value: "https://apis.data.go.kr/1471000"
  - name: SERVICE_KEY
    value_type: secret
    value: "REDACTED_KEY"

# HTTP 요청 노드
- id: node_fetch_recall
  data:
    type: http-request
    method: get
    url: "{{#env.DATA_GO_KR_BASE#}}/MdcinRtrvlSleStpgeInfoService04/getMdcinRtrvlSleStpgeItem03"
    headers: |
      Accept: application/json
    params: |
      serviceKey: {{#env.SERVICE_KEY#}}
      pageNo: 1
      numOfRows: 100
      type: json
    timeout:
      max_connect_timeout: 10
      max_read_timeout: 30
      max_write_timeout: 10
```

---

## 방법 2 (보조) — 외부 데이터 API 연결

MISO 콘솔의 **지식 관리 → 외부 데이터 API 연결** 메뉴를 사용하는 방식.

### 2-1. 원리

- 워크스페이스 레벨에서 Base URL + API Key 를 1회 등록
- 에이전트 **외부 데이터** 기능 또는 **지식 검색** 과 연계하여 RAG 스타일로 활용

### 2-2. 한계

공공데이터포털 API 는 Dify 스타일의 **RAG 검색 API 계약(`/retrieval` POST with `knowledge_id` etc.)** 을 준수하지 않는다. 즉 MISO 의 "외부 데이터 API 연결" 은 원칙적으로 RAG 검색용 인터페이스를 기대하므로, 공공데이터 API 를 여기에 바로 등록해도 **지식 검색 결과로 변환되지 않는다**.

따라서 **워크플로우의 일반 HTTP 호출 용도로는 방법 1 이 적합**하다.

### 2-3. 등록 절차 (참고용)

1. MISO 콘솔 좌측 메뉴 → **지식 관리** → **외부 데이터 API 연결**
2. "외부 데이터 API 관리" 에서 `+ 새 API` 클릭
3. 다음 입력:
   - 입력 필드 이름: `drug_recall_api` (예)
   - API Endpoint: `https://apis.data.go.kr/1471000/MdcinRtrvlSleStpgeInfoService04`
   - API Key: `REDACTED_KEY` (Decoding 버전)
4. 연결 후, 에이전트 외부 데이터 연결에서 선택 가능 (단 위 한계 유의)

4개 API 를 각각 별도 등록해야 하며, 각 Base URL 이 서로 다름에 유의.

---

## 방법 3 (선택) — 커스텀 도구 (OpenAPI) 등록

MISO 콘솔 → **도구 모듈** → **커스텀 도구** 에서 OpenAPI 3.0 스펙을 업로드하여 등록하는 방식.

### 3-1. 적합한 경우

- 에이전트가 **자율적으로** API 를 호출하도록 하려는 경우 (워크플로우 고정 흐름이 아닌 동적 의사결정)
- 4개 API 를 하나의 OpenAPI 문서로 묶어 에이전트 도구로 노출

### 3-2. OpenAPI 스켈레톤 (참고)

```yaml
openapi: 3.0.0
info:
  title: MFDS Public Data API
  version: "1.0"
servers:
  - url: https://apis.data.go.kr/1471000
paths:
  /MdcinRtrvlSleStpgeInfoService04/getMdcinRtrvlSleStpgeItem03:
    get:
      operationId: getDrugRecallList
      summary: 의약품 회수·판매중지 목록 조회
      parameters:
        - name: serviceKey
          in: query
          required: true
          schema: { type: string }
        - name: pageNo
          in: query
          schema: { type: integer, default: 1 }
        - name: numOfRows
          in: query
          schema: { type: integer, default: 10 }
        - name: type
          in: query
          schema: { type: string, default: json }
        - name: item_name
          in: query
          schema: { type: string }
        - name: entp_name
          in: query
          schema: { type: string }
      responses:
        "200":
          description: OK
  /MdcinExaathrService04/getMdcinExaathrList04:
    get:
      operationId: getDrugDisciplinaryList
      # 이하 동일 패턴
  /DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnList07:
    get:
      operationId: getDrugApprovalList
  /MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03:
    get:
      operationId: getDrugIdentificationList
security:
  - ApiKeyQuery: []
components:
  securitySchemes:
    ApiKeyQuery:
      type: apiKey
      in: query
      name: serviceKey
```

MISO 콘솔에서 위 문서를 업로드 후 API Key 값에 Decoding 인증키 입력.

---

## 3가지 방식 선택 매트릭스

| 기준 | 방법 1 (환경변수) | 방법 2 (외부 데이터 API) | 방법 3 (커스텀 도구) |
|------|------------------|-------------------------|---------------------|
| 용도 | 워크플로우 HTTP 호출 | RAG 검색 연동 | 에이전트 자율 도구 사용 |
| 등록 방식 | DSL YAML 가져오기 | UI 수동 등록 | OpenAPI 문서 업로드 |
| 본 프로젝트 채택 | **예 (기본)** | 아니오 (계약 불일치) | 선택 (필요 시) |
| 자동 실행 호환 | 완벽 | 부분 | 부분 |
| 인증키 보호 | secret 타입 환경변수 | UI 저장 | OpenAPI security |

---

## 인증키 관리 유의사항

- 본 저장소 YAML 에 들어간 인증키는 `drug_integrated_search/config.py` 의 Decoding 버전. 공공 노출 방지를 위해 **운영 환경 배포 시 환경변수 값을 실제 키로 교체 후 Git 에 커밋하지 말 것.**
- MISO 환경변수는 `value_type: secret` 으로 지정되면 UI 에서 마스킹되며 API 응답에도 노출되지 않음.
- 공공데이터포털 활용기간: 2025-10-31 ~ 2027-10-31, 일일 트래픽 10,000 건 (허가정보 API 기준).
