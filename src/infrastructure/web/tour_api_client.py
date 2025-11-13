# src/infrastructure/web/tour_api_client.py
import requests
import os
from functools import lru_cache
from ...config import get_tour_api_key

BASE_URL = "https://apis.data.go.kr/B551011/KorService1/searchKeyword1"

@lru_cache(maxsize=128)
def get_festival_period(festival_name: str):
    """
    TourAPI를 사용해 축제 이름으로 검색하여 해당 축제의 시작일과 종료일을 반환합니다.
    """
    api_key = get_tour_api_key()
    if not api_key:
        print("Warning: TourAPI key is not configured. Skipping festival period fetch.")
        return None, None

    params = {
        "serviceKey": api_key,
        "numOfRows": 1,
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "FestInsight",
        "listYN": "Y",
        "arrange": "A", # 제목순
        "keyword": festival_name,
        "_type": "json"
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        
        if not items:
            return None, None
        
        # 리스트가 아닌 경우 단일 항목이므로 리스트로 만듭니다.
        if not isinstance(items, list):
            items = [items]

        # 정확히 일치하는 축제를 찾습니다.
        for item in items:
            if item.get('title') == festival_name:
                start_date = item.get("eventstartdate")
                end_date = item.get("eventenddate")
                return start_date, end_date
        
        # 정확히 일치하는 것이 없으면 첫 번째 결과를 반환합니다.
        first_item = items[0]
        start_date = first_item.get("eventstartdate")
        end_date = first_item.get("eventenddate")
        return start_date, end_date

    except requests.exceptions.RequestException as e:
        print(f"Error fetching festival period for '{festival_name}': {e}")
        return None, None
    except (KeyError, TypeError, ValueError) as e:
        print(f"Error parsing TourAPI response for '{festival_name}': {e}")
        return None, None
