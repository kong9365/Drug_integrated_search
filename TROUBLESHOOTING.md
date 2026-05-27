# 문제 해결 가이드

## 허가정보 API 404 오류

### 현재 상황
허가정보 API의 모든 엔드포인트가 404 오류를 반환하고 있습니다.

### 시도한 엔드포인트
1. `getDrugPrdtPrmsnList07` - 404 오류
2. `getDrugPrdtPrmsnDtlInq07` - 404 오류  
3. `getDrugPrdtPrmsnList06` - 404 오류

### 해결 방법

#### 1. 공공데이터포털에서 최신 API 확인
- https://www.data.go.kr 접속
- "의약품 허가정보" 또는 "DrugPrdtPrmsnInfoService" 검색
- 최신 API 엔드포인트 및 함수명 확인

#### 2. 관리부서 문의
- **기관**: 식품의약품안전처 데이터혁신기획팀
- **전화**: 043-719-1626
- **이메일**: 공공데이터포털을 통해 문의

#### 3. 임시 조치
현재 시스템은 허가정보 API 오류가 있어도 다른 3개 API는 정상 작동합니다:
- ✅ 행정처분정보 API
- ✅ 회수·판매중지정보 API  
- ✅ 낱알식별정보 API

웹 인터페이스에서 허가정보 탭에 오류 메시지가 표시되지만, 다른 탭은 정상적으로 사용할 수 있습니다.

### 엔드포인트 업데이트 방법

최신 엔드포인트를 확인하신 후:

1. `drug_integrated_search/config.py` 파일 열기
2. `API_ENDPOINTS` 딕셔너리에서 `approval` 값 수정
3. 애플리케이션 재시작

예시:
```python
API_ENDPOINTS = {
    "approval": "https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/새로운함수명",
    # ...
}
```

### 확인 사항
- [ ] 공공데이터포털에서 API 활용신청이 완료되었는지 확인
- [ ] API 키가 올바르게 설정되었는지 확인
- [ ] API 서비스가 활성화되어 있는지 확인
- [ ] 최신 엔드포인트 URL 확인

