# 의약품 공공데이터 MISO 워크플로우

식품의약품안전처 공공데이터포털 4종 API(허가정보·회수판매중지·행정처분·낱알식별)를 MISO 플랫폼에 등록해 자동 리포트 및 통합 조회 에이전트로 활용하기 위한 MISO DSL YAML 모음.

---

## 1. 파일 구성

| 파일 | 타입 | 용도 | 자동실행 권장 |
|------|------|------|------|
| `drug_daily_recall_report.yml` | workflow | 최근 N일 회수·판매중지 요약 리포트 | 매일 08:00 |
| `drug_daily_disciplinary_report.yml` | workflow | 최근 N일 행정처분 요약 리포트 | 매일 08:05 |
| `drug_integrated_search_workflow.yml` | workflow | 4종 API 병렬 호출 통합 조회 (도구용) | - |
| `drug_integrated_search_agent.yml` | advanced-chat | 자연어 질의 기반 통합 조회 챗 에이전트 (자립형) | - |
| `drug_consult_agent.yml` | agent-chat | 위 워크플로우를 **도구로 호출**하는 재사용형 에이전트 | - |
| `api_registration_guide.md` | doc | API 등록 2가지 방식 비교 | - |
| `README.md` | doc | 본 문서 | - |

### 1-1. 두 에이전트의 차이

| 구분 | `drug_integrated_search_agent.yml` | `drug_consult_agent.yml` |
|------|------------------------------------|--------------------------|
| 모드 | `advanced-chat` (워크플로우 그래프 내장) | `agent-chat` (LLM + 도구) |
| API 호출 | **자체 노드**에서 4개 HTTP 직접 호출 | **외부 워크플로우 도구** 호출 |
| 사전 준비 | 없음 (단독 import 후 즉시 동작) | `drug_integrated_search_workflow` 를 먼저 발행·도구 등록 |
| 수정 영향 범위 | 에이전트 1개 | 워크플로우만 수정하면 모든 에이전트에 반영 |
| 추천 사용처 | 단일 부서용, 빠른 배포 | 여러 에이전트 공유, 중앙 관리 |

---

## 2. 등록·발행 순서

아래 순서로 한 번만 진행하면 된다.

### 2-1. 공통 사전 작업 — 인증키 확인

- 기존 인증키: `drug_integrated_search/config.py` L12-15 의 Decoding 버전
- 모든 YAML 의 `environment_variables.SERVICE_KEY.value` 에 선입력되어 있음 → **그대로 가져오기 가능**
- 키가 폐기/변경된 경우 4개 YAML 모두 수정 또는 가져오기 후 MISO 콘솔에서 환경변수 편집

### 2-2. 앱 가져오기 (순서)

1. **drug_daily_recall_report.yml** — MISO 콘솔 → 앱 만들기 → DSL 파일 가져오기
2. **drug_daily_disciplinary_report.yml** — 동일 방식
3. **drug_integrated_search_workflow.yml** — 동일 방식 → **발행** 필수 (도구화 대상)
4. **drug_integrated_search_agent.yml** — 동일 방식

가져오기 직후 4개 앱 모두:
- 환경변수 `DATA_GO_KR_BASE` = `https://apis.data.go.kr/1471000`
- 환경변수 `SERVICE_KEY` = (Decoding 버전 인증키, secret)

를 자동으로 갖는다. 추가 UI 작업 불필요.

### 2-3. (선택) 통합 조회 워크플로우를 에이전트 도구로 연결

`drug_integrated_search_agent.yml` 은 **자체적으로 4종 API 를 직접 호출**하므로 도구 연결 없이도 독립 동작한다.

대신 `drug_consult_agent.yml` 은 `drug_integrated_search_workflow` 를 **도구로 호출**하는 구조이므로, 아래 바인딩 단계가 필요하다.

#### A. 워크플로우 발행 (필수 선행)

1. `drug_integrated_search_workflow.yml` 을 가져오기 후 우측 상단 **발행(Publish)** 버튼 클릭
2. 발행 대화상자에서 버전명·설명 입력 → 발행 완료
3. 발행 후 "앱 상세" 에 표시되는 **App ID** 를 복사해둔다 (선택, 방법 B-2 에서 사용)

#### B. 도구 바인딩 (UI 에서만 진행)

> **주의**: `drug_consult_agent.yml` 의 `agent_mode.tools` 는 의도적으로 **빈 배열(`[]`)** 로 비워져 있다.
> DSL 에 존재하지 않는 `provider_id` 를 지정하면 MISO 서버가 "Internal Server Error" 를 반환하므로,
> 반드시 **UI 에서 바인딩** 해야 한다. (YAML 을 편집할 필요 없음)

1. `drug_consult_agent.yml` 가져오기 (import) → 오류 없이 생성되는지 확인
2. 에이전트 편집 화면 오른쪽 **도구** 섹션 → "편집" 버튼
3. 도구 설정 대화상자 → 도구 유형 탭 **"워크플로우"** 선택
4. 목록에서 방금 발행한 **"의약품 통합 조회 워크플로우"** 체크
5. 표시되는 파라미터 4개(item_name, entp_name, item_seq, num_of_rows) 그대로 저장
6. 에이전트 편집 화면 우측 상단 "저장" 후 "미리보기" 로 동작 확인

#### C. 바인딩 검증

에이전트 대화창에서 다음 질문을 순서대로 시험:

| # | 질문 | 기대 동작 |
|---|------|----------|
| 1 | `타이레놀정500밀리그람 조회해줘` | 도구 호출 로그에 `item_name="타이레놀정500밀리그람"` 표시, 허가정보 1건+회수·행정처분·낱알식별 합계 |
| 2 | `한국얀센 최근 행정처분 건 있어?` | `entp_name="한국얀센"` 로 호출, 행정처분 건수 표시 |
| 3 | `품목기준코드 201108117 정보` | `item_seq="201108117"` 로 호출, 해당 품목만 필터링 |
| 4 | `없는제품명xyz 정보` | 4개 API 모두 0건 → "조회되지 않음" 응답 |

위 네 케이스가 모두 정상 동작하면 바인딩 완료.

---

## 3. 자동실행 스케줄 설정

각 일일 리포트 앱(`drug_daily_recall_report`, `drug_daily_disciplinary_report`)에서:

1. 앱 편집 화면 → 설정 → **자동 실행** 탭
2. 일정: **매일**
3. 실행 시간: 08:00 (회수), 08:05 (처분)
4. 대화: 입력값 `period_days: 1`, `top_n: 10`, 키워드 필터 비워둠

리포트 결과(`report_markdown`)는 다음과 같은 방식으로 활용 가능:

- MISO 실행 로그에서 확인
- MISO SIMPLE EMAIL SERVICE 도구 등을 추가 노드로 연결해 이메일 푸시
- API 로 외부 시스템에서 폴링

---

## 4. 아키텍처

```
┌──────────────────────────────── MISO Cloud ────────────────────────────────┐
│                                                                              │
│   [drug_daily_recall_report]        [drug_daily_disciplinary_report]        │
│          │                                   │                               │
│          ▼                                   ▼                               │
│   HTTP 요청 노드                      HTTP 요청 노드                         │
│   (회수·판매중지 API)                 (행정처분 API)                         │
│                                                                              │
│   [drug_integrated_search_agent]    [drug_integrated_search_workflow]       │
│          │                                   │                               │
│          └─── 4개 HTTP 노드 병렬 ────────────┘                              │
│               (허가·회수·처분·낱알식별)                                       │
│                                                                              │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │  env.SERVICE_KEY (secret)
                                   ▼
                       ┌─────────────────────────┐
                       │  apis.data.go.kr/1471000 │
                       │  식품의약품안전처 4종 API │
                       └─────────────────────────┘
```

---

## 5. 워크플로우 입력·출력 요약

### drug_daily_recall_report
- **입력**: `period_days`(1), `top_n`(10), `item_keyword`("")
- **출력**: `report_markdown`, `new_count`

### drug_daily_disciplinary_report
- **입력**: `period_days`(1), `top_n`(10), `entp_keyword`("")
- **출력**: `report_markdown`, `new_count`

### drug_integrated_search_workflow
- **입력**: `item_name`(""), `entp_name`(""), `item_seq`(""), `num_of_rows`(10)
- **출력**: `approval_items`, `recall_items`, `disciplinary_items`, `identification_items`, `summary_text`, `has_risk`

### drug_integrated_search_agent (chatflow)
- **입력**: `sys.query` (사용자 채팅 메시지)
- **출력**: 자연어 마크다운 답변 (회수·처분 존재 시 상단에 경고 블록)

---

## 6. 확장 아이디어

| 확장 | 구현 방법 |
|------|----------|
| 이메일 발송 자동화 | 각 리포트 워크플로우 끝단에 `MISO SIMPLE EMAIL SERVICE` 도구 노드 추가 |
| 특정 성분(ATC코드) 감시 | 통합 조회 워크플로우에 `atc_code` 입력 추가 후 허가정보 API 파라미터 전달 |
| 이전 실행 결과와 diff | `conversation_variables` 로 이전 일자 리스트 저장 후 코드 노드 비교 |
| Slack/Teams 알림 | HTTP 요청 노드(Incoming Webhook) 를 End 전에 추가 |

---

## 7. 실측 기반 엔드포인트·응답 스키마 (2026-04 검증)

본 워크플로우의 HTTP 노드·파싱 코드는 아래 실측치를 기준으로 작성되었다.
변경 시 `_probe_fields.py` / `_test_parse.py` 를 재실행하여 재검증할 것.

### 7-1. 엔드포인트 상태

| API | 엔드포인트 | 상태 |
|-----|-----------|------|
| 허가정보 | `DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnInq07` | ✅ 200 |
| 허가정보 (List07) | `DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnList07` | ❌ 404 (폐기) |
| 회수·판매중지 | `MdcinRtrvlSleStpgeInfoService04/getMdcinRtrvlSleStpgeItem03` | ✅ 200 |
| 행정처분 | `MdcinExaathrService04/getMdcinExaathrList04` | ✅ 200 |
| 낱알식별 | `MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03` | ✅ 200 |

### 7-2. 응답 스키마 (JSON 기준)

**공통 트리**: `response.body.items[*]` 또는 `response.body.items` 내부

**회수 API 특이사항**: `items` 원소가 `{"item": {...실데이터...}}` 로 한 단계 더 감싸져 있음. 파싱 시 unwrap 필요.

### 7-3. 필드 매핑 (실측)

| 용도 | 허가정보 (Inq07) | 회수 | 행정처분 | 낱알식별 |
|------|-----------------|------|---------|---------|
| 업체명 | `ENTP_NAME` | `ENTRPS` | `ENTP_NAME` | `ENTP_NAME` |
| 품목명 | `ITEM_NAME` | `PRDUCT` | `ITEM_NAME` (null 가능) | `ITEM_NAME` |
| 날짜 | `ITEM_PERMIT_DATE` | `RECALL_COMMAND_DATE` | `LAST_SETTLE_DATE` | `ITEM_PERMIT_DATE` |
| 사유/내용 | - | `RTRVL_RESN` | `ADM_DISPS_NAME` + `EXPOSE_CONT` | - |
| 고유ID | `ITEM_SEQ` | `ITEM_SEQ` | `ADM_DISPS_SEQ` | `ITEM_SEQ` |
| 분류 | `PRDUCT_TYPE`, `SPCLTY_PBLC` | - | `BEF_APPLY_LAW` | `CLASS_NAME`, `ETC_OTC_NAME` |

날짜는 모두 **YYYYMMDD** 문자열 → Parse 노드에서 `YYYY-MM-DD` 로 정규화.

### 7-4. 회수 API 응답 예시

```json
{
  "response": {
    "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
    "body": {
      "pageNo": 1,
      "totalCount": 910,
      "numOfRows": 3,
      "items": [
        {"item": {"ENTRPS": "우리생활건강", "PRDUCT": "...", "RTRVL_RESN": "...", "RECALL_COMMAND_DATE": "20260420", "MNFCTUR_NO": "WL20281012"}},
        {"item": {...}}
      ]
    }
  }
}
```

---

## 8. 파싱 검증 스크립트

본 디렉터리의 `_probe_fields.py`, `_test_parse.py` 는 **MISO 런타임과 무관한 로컬 검증용** 스크립트다.

- `_probe_fields.py`: 4개 API 각각의 실제 응답 필드명을 출력 (스키마 변경 감지용)
- `_test_parse.py`: 각 YAML 내부의 Parse/Merge 코드 블록을 추출해 실제 API 응답으로 실행, 주요 필드가 비어있지 않은지 assert

```bash
python drug_integrated_search/miso_workflows/_probe_fields.py  # 스키마 확인
python drug_integrated_search/miso_workflows/_test_parse.py    # 파싱 E2E 테스트
python drug_integrated_search/miso_workflows/_validate.py      # YAML 구조 검증
```

공공 API 가 필드명을 변경할 경우 위 3개 스크립트로 즉시 탐지 후 해당 YAML 의 Parse/Merge 코드 블록만 수정하면 됨.

---

## 9. 참고 문서

- MISO 플랫폼 레퍼런스: `MISO/MISO_PLATFORM_REFERENCE.md`
- 공공데이터 API 명세: `drug_integrated_search/API_SPEC.md`
- API 상태: `drug_integrated_search/API_STATUS.md`
- 기존 MISO 워크플로우 패턴: `QMS_Integrated_Dashboard/miso_workflows/qms_oos_daily_report.yml`
