# KD-IRIS 실행 가이드

> **광동 KD-IRIS** — 의약품·의약외품·식품 통합 규제정보 허브
> v1.0-mvp (2026-05-27 D1~D5 완료)

## 빠른 시작

### 1. 프로젝트 루트에서 실행 (권장)
```bash
cd C:\Users\user\Desktop\Coding\cusor
python -m drug_integrated_search.app
```

### 2. drug_integrated_search 폴더에서 실행
```bash
cd drug_integrated_search
python run.py
```

## 페이지 가이드

서버 기동 후 브라우저에서 다음 URL 접속:

| URL | 화면 |
|-----|------|
| http://localhost:5005/ | **랜딩 페이지** (광동 KD-IRIS) |
| http://localhost:5005/app | 앱 진입 (9개 화면 미리보기) |
| http://localhost:5005/app/search | 통합 검색 |
| http://localhost:5005/app/product/200305423 | Product 360 — 의약품 (베니톨정 데모) |
| http://localhost:5005/app/product-food/19850713-01 | Product 360 — 식품 (비타500 데모) |
| http://localhost:5005/app/workspace/qa | QA/QC 워크스페이스 |
| http://localhost:5005/app/workspace/exec | 경영진 대시보드 |
| http://localhost:5005/app/timeline | 통합 이벤트 타임라인 |
| http://localhost:5005/app/watchlist | 워치리스트 |
| http://localhost:5005/app/reports | 리포트 |
| http://localhost:5005/app/copilot | AI 코파일럿 |
| http://localhost:5005/docs/handoff | 개발자 핸드오프 문서 |
| http://localhost:5005/healthz | 헬스 체크 (JSON) |

## API 작동 검증

35개 공공 API 작동 확인:
```bash
cd drug_integrated_search
python smoke_test_apis.py
```

## 테마 (라이트/다크/오토)

랜딩 또는 앱 화면 우상단 ☀️/🌙 아이콘 클릭 → **light → dark → auto** 3단계 순환.
- `light`: 강제 라이트
- `dark`: 강제 다크
- `auto`: OS 시스템 설정 따름 (Windows 10/11 야간 모드 등)
- 설정은 `localStorage('reghub.theme')` 에 영속화

## 문제 해결

- **ModuleNotFoundError**: 프로젝트 루트(`cusor/`)에서 `python -m drug_integrated_search.app` 실행
- **UnicodeEncodeError**: PowerShell/CMD에서 한글 출력 깨짐 — UTF-8 강제 처리됨 (app.py에 적용)
- **404 페이지**: URL 경로 재확인. 알 수 없는 경로는 `/` 또는 `/app` 으로 이동 안내
- **검색 결과 없음**: smoke_test_apis.py 로 SERVICE_KEY 작동 확인

## 관련 문서

- [README.md](README.md) — 프로젝트 개요
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — 전체 구현 계획
- [API_STATUS.md](API_STATUS.md) — API 작동 현황 (45/46 작동 중)
- [API_APPLICATION_LIST.md](API_APPLICATION_LIST.md) — 공공 API 신청 가이드
- [docs/HANDOFF.md](docs/HANDOFF.md) — 디자인 핸드오프 (광동제약 KD-IRIS 디자인 팀)
