"""
네트워크 연결 테스트 스크립트
"""
import requests
import urllib3
from config import API_ENDPOINTS, SERVICE_KEY, VERIFY_SSL

# SSL 경고 비활성화
if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_connection():
    """API 연결 테스트"""
    print("=" * 60)
    print("네트워크 연결 테스트")
    print("=" * 60)
    
    test_url = API_ENDPOINTS["approval"]
    params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": "1",
        "numOfRows": "1",
        "type": "xml"
    }
    
    print(f"\n테스트 URL: {test_url}")
    print(f"SSL 검증: {VERIFY_SSL}")
    print("\n연결 테스트 중...\n")
    
    try:
        response = requests.get(
            test_url,
            params=params,
            timeout=10,
            verify=VERIFY_SSL
        )
        print(f"✅ 연결 성공!")
        print(f"상태 코드: {response.status_code}")
        print(f"응답 크기: {len(response.text)} bytes")
        
        # 응답 내용 일부 확인
        if "resultCode" in response.text:
            print("\n응답 확인: API가 정상적으로 응답했습니다.")
        else:
            print("\n⚠️ 응답 형식이 예상과 다를 수 있습니다.")
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL 인증서 오류:")
        print(f"   {str(e)}")
        print("\n해결 방법:")
        print("1. config.py에서 VERIFY_SSL = False로 설정")
        print("2. 또는 환경 변수: VERIFY_SSL=False")
        
        # SSL 검증 없이 재시도
        print("\nSSL 검증 없이 재시도 중...")
        try:
            response = requests.get(
                test_url,
                params=params,
                timeout=10,
                verify=False
            )
            print(f"✅ SSL 검증 없이 연결 성공!")
            print(f"상태 코드: {response.status_code}")
        except Exception as retry_error:
            print(f"❌ 재시도도 실패: {str(retry_error)}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 네트워크 연결 오류:")
        print(f"   {str(e)}")
        print("\n확인 사항:")
        print("1. 인터넷 연결 상태 확인")
        print("2. 방화벽 설정 확인")
        print("3. 프록시 설정 확인")
        
    except requests.exceptions.Timeout as e:
        print(f"❌ 요청 시간 초과:")
        print(f"   {str(e)}")
        print("\n확인 사항:")
        print("1. 네트워크 속도 확인")
        print("2. 서버 응답 시간 확인")
        
    except Exception as e:
        print(f"❌ 오류 발생:")
        print(f"   {type(e).__name__}: {str(e)}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_connection()

