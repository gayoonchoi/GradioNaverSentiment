# coding: utf-8
# TourAPI 테스트 스크립트 v2
import requests
from src.config import get_tour_api_key
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_tour_api_detailed(keyword):
    api_key = get_tour_api_key()
    print(f"API Key length: {len(api_key) if api_key else 0}")
    print(f"API Key first 10 chars: {api_key[:10] if api_key else 'None'}")

    if not api_key:
        print("TOUR_API_KEY를 읽을 수 없습니다.")
        return

    # KorService1/searchKeyword1 엔드포인트 테스트
    url = "https://apis.data.go.kr/B551011/KorService1/searchKeyword1"

    params = {
        "serviceKey": api_key,
        "numOfRows": "5",
        "pageNo": "1",
        "MobileOS": "ETC",
        "MobileApp": "FestInsight",
        "listYN": "Y",
        "arrange": "A",
        "keyword": keyword,
        "_type": "json"
    }

    print(f"\nSearching for: {keyword}")
    print(f"URL: {url}")

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

        # 응답 내용 출력
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\nJSON Response:")
                import json
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except:
                print(f"Response text: {response.text[:1000]}")
        else:
            print(f"Error response: {response.text[:1000]}")

    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    test_tour_api_detailed("강릉커피축제")
