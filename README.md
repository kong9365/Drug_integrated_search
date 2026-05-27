# 💊 의약품 통합 조회 시스템

식품의약품안전처 공공데이터포털 API를 활용한 의약품 종합 정보 조회 시스템

## 📋 주요 기능

- **의약품 허가정보 조회**: 제품명, 업체명, 허가일자, 유효기간 등 기본 정보
- **행정처분정보 조회**: 제조업무정지, 품목취소 등 행정처분 내역
- **회수·판매중지정보 조회**: 품질이슈로 인한 회수명령 및 판매중지 현황
- **낱알식별정보 조회**: 의약품 외형정보(모양, 색상, 각인) 및 이미지

## 🚀 설치 및 실행

### 1. 필수 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (선택사항)

```bash
# Windows PowerShell
$env:PUBLIC_DATA_SERVICE_KEY="your-service-key-here"
$env:FLASK_DEBUG="True"
$env:VERIFY_SSL="False"  # 테스트 환경에서만 사용

# Linux/Mac
export PUBLIC_DATA_SERVICE_KEY="your-service-key-here"
export FLASK_DEBUG="True"
export VERIFY_SSL="False"
```

### 3. 애플리케이션 실행

```bash
python run.py
```

또는

```bash
python -m drug_integrated_search.run
```

브라우저에서 `http://localhost:5005` 접속

## 📁 프로젝트 구조

```
drug_integrated_search/
├── __init__.py          # 패키지 초기화
├── config.py            # 설정 파일
├── api_client.py        # API 클라이언트 모듈
├── app.py              # Flask 애플리케이션
├── run.py              # 실행 파일
├── requirements.txt    # 필수 패키지 목록
├── README.md           # 프로젝트 문서
├── templates/          # HTML 템플릿
│   └── index.html      # 메인 페이지
├── static/             # 정적 파일
│   └── images/         # 다운로드된 이미지 저장
└── logs/              # 로그 파일
    └── app.log         # 애플리케이션 로그
```

## 🔌 API 엔드포인트

### 통합 검색
```
GET /api/search?item_name={제품명}&entp_name={업체명}
```

### 개별 API
- `GET /api/approval` - 허가정보 조회
- `GET /api/disciplinary` - 행정처분정보 조회
- `GET /api/recall` - 회수·판매중지정보 조회
- `GET /api/identification` - 낱알식별정보 조회

## 📊 사용 예시

### 웹 인터페이스
1. 브라우저에서 `http://localhost:5005` 접속
2. 제품명 또는 업체명 입력
3. "검색하기" 버튼 클릭
4. 결과를 탭별로 확인

### API 직접 호출
```python
import requests

# 통합 검색
response = requests.get(
    'http://localhost:5005/api/search',
    params={
        'item_name': '타이레놀정',
        'entp_name': '한국얀센'
    }
)
data = response.json()
print(data)
```

## ⚙️ 설정 옵션

`config.py` 파일에서 다음 설정을 변경할 수 있습니다:

- `SERVICE_KEY`: 공공데이터포털 API 인증키
- `REQUEST_TIMEOUT`: API 요청 타임아웃 (기본: 30초)
- `MAX_RETRIES`: 재시도 횟수 (기본: 3회)
- `VERIFY_SSL`: SSL 인증서 검증 여부

## 🔒 보안 주의사항

- 프로덕션 환경에서는 `SECRET_KEY`를 반드시 변경하세요
- API 인증키는 환경 변수로 관리하는 것을 권장합니다
- SSL 검증은 가능한 한 활성화하세요 (`VERIFY_SSL=True`)

## 📝 로깅

로그 파일은 `logs/app.log`에 저장됩니다. 로그 레벨은 `INFO`로 설정되어 있습니다.

## 🐛 문제 해결

### API 401 오류
- 인증키가 올바른지 확인하세요
- 인증키가 URL 인코딩되어 있는지 확인하세요

### API 500 오류
- 네트워크 연결을 확인하세요
- 공공데이터포털 서버 상태를 확인하세요
- 재시도 로직이 자동으로 작동합니다

### 이미지 다운로드 실패
- 이미지 URL이 유효한지 확인하세요
- 네트워크 연결을 확인하세요
- 실패해도 다른 정보는 정상적으로 표시됩니다

## 📄 라이선스

이 프로젝트는 공공데이터포털의 OpenAPI를 활용합니다.

## 🔗 참고 링크

- [공공데이터포털](https://www.data.go.kr)
- [식품의약품안전처 의약품 낱알식별 정보](https://www.data.go.kr/data/15057639/openapi.do)

