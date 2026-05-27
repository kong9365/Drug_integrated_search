"""
의약품 통합 조회 시스템 실행 파일
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from drug_integrated_search.app import app

if __name__ == '__main__':
    print("=" * 60)
    print("[의약품] 통합 조회 시스템")
    print("=" * 60)
    print("서버가 시작됩니다...")
    print("브라우저에서 http://localhost:5005 을 열어주세요.")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5005, use_reloader=False)

