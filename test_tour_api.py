# TourAPI 테스트 스크립트
import requests
from src.config import get_tour_api_key

def test_tour_api(keyword):
    api_key = get_tour_api_key()
    print(f"API Key 읽기: {'성공' if api_key else '실패'}")

    if not api_key:
        print("❌ TOUR_API_KEY를 읽을 수 없습니다.")
        return

    url = "https://apis.data.go.kr/B551011/KorService1/searchKeyword1"
    params = {
        "serviceKey": api_key,
        "numOfRows": 10,
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "FestInsight",
        "listYN": "Y",
        "arrange": "A",
        "keyword": keyword,
        "_type": "json"
    }

    print(f"\n'{keyword}' 검색 중...")
    response = requests.get(url, params=params, timeout=10)
    print(f"HTTP Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

        if not items:
            print(f"'{keyword}' 검색 결과 없음")
        else:
            if not isinstance(items, list):
                items = [items]

            print(f"\n총 {len(items)}개 결과 발견:")
            for i, item in enumerate(items, 1):
                print(f"\n[{i}] 제목: {item.get('title')}")
                print(f"    시작일: {item.get('eventstartdate')}")
                print(f"    종료일: {item.get('eventenddate')}")
                print(f"    주소: {item.get('addr1')}")
    else:
        print(f"API 호출 실패: {response.status_code}")
        print(response.text[:500])

if __name__ == "__main__":
    test_tour_api("강릉커피축제")
    print("\n" + "="*50 + "\n")
    test_tour_api("커피")
    print("\n" + "="*50 + "\n")
    test_tour_api("강릉")
