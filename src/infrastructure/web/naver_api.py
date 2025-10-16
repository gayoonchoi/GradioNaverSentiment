import requests
import urllib.parse
from src.config import get_naver_api_keys

def search_naver_blog_page(query, start_index=1):
    client_id, client_secret = get_naver_api_keys()
    encText = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/blog.json?query={encText}&display=100&start={start_index}"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        data = response.json()
        return data.get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"API 호출 오류: {e}")
        return []
