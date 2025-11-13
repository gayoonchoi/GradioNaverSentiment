# src/infrastructure/database/festival_repository.py
"""데이터베이스에서 축제 정보를 조회하는 Repository"""
from .db_manager import get_connection
from functools import lru_cache

@lru_cache(maxsize=256)
def search_festival_by_title(festival_name: str) -> dict | None:
    """
    축제 이름으로 축제 정보를 검색합니다.

    Args:
        festival_name: 검색할 축제 이름

    Returns:
        축제 정보 딕셔너리 또는 None
        - start_date: 시작일 (YYYYMMDD 형식)
        - end_date: 종료일 (YYYYMMDD 형식)
        - addr1: 주소1
        - addr2: 주소2
        - mapx: X 좌표
        - mapy: Y 좌표
        - contentid: 컨텐츠 ID
        - cat1, cat2, cat3: 카테고리
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. 정확히 일치하는 제목 검색
    cursor.execute('''
        SELECT contentid, title, eventstartdate, eventenddate, addr1, addr2,
               mapx, mapy, cat1, cat2, cat3, areacode
        FROM festivals
        WHERE title = ?
    ''', (festival_name,))

    result = cursor.fetchone()

    if result:
        conn.close()
        print(f"[DB] Exact match found for '{festival_name}'")
        return {
            "contentid": result["contentid"],
            "title": result["title"],
            "start_date": _format_date(result["eventstartdate"]),
            "end_date": _format_date(result["eventenddate"]),
            "addr1": result["addr1"],
            "addr2": result["addr2"],
            "mapx": result["mapx"],
            "mapy": result["mapy"],
            "cat1": result["cat1"],
            "cat2": result["cat2"],
            "cat3": result["cat3"],
            "areacode": result["areacode"]
        }

    # 2. 부분 일치 검색 (정확한 일치를 찾지 못한 경우)
    cursor.execute('''
        SELECT contentid, title, eventstartdate, eventenddate, addr1, addr2,
               mapx, mapy, cat1, cat2, cat3, areacode
        FROM festivals
        WHERE title LIKE ?
        ORDER BY
            CASE
                WHEN title = ? THEN 1
                WHEN title LIKE ? THEN 2
                ELSE 3
            END
        LIMIT 5
    ''', (f'%{festival_name}%', festival_name, f'{festival_name}%'))

    results = cursor.fetchall()
    conn.close()

    if results:
        print(f"[DB] Found {len(results)} partial matches for '{festival_name}':")
        for i, row in enumerate(results, 1):
            print(f"  {i}. {row['title']}")

        # 첫 번째 결과 반환
        best_match = results[0]
        print(f"[DB] Using best match: '{best_match['title']}'")

        return {
            "contentid": best_match["contentid"],
            "title": best_match["title"],
            "start_date": _format_date(best_match["eventstartdate"]),
            "end_date": _format_date(best_match["eventenddate"]),
            "addr1": best_match["addr1"],
            "addr2": best_match["addr2"],
            "mapx": best_match["mapx"],
            "mapy": best_match["mapy"],
            "cat1": best_match["cat1"],
            "cat2": best_match["cat2"],
            "cat3": best_match["cat3"],
            "areacode": best_match["areacode"]
        }

    print(f"[DB] No match found for '{festival_name}'")
    return None

def _format_date(date_value) -> str | None:
    """날짜 값을 YYYYMMDD 형식 문자열로 변환합니다."""
    if date_value is None:
        return None

    # float 형식 (20251030.0) -> 문자열 변환
    if isinstance(date_value, float):
        return str(int(date_value))

    # 이미 문자열인 경우
    if isinstance(date_value, str):
        # 소수점 제거
        return date_value.split('.')[0]

    # int 형식
    if isinstance(date_value, int):
        return str(date_value)

    return None

def get_festival_period(festival_name: str) -> tuple[str | None, str | None]:
    """
    축제 이름으로 축제 기간을 조회합니다.

    Args:
        festival_name: 축제 이름

    Returns:
        (시작일, 종료일) 튜플 (YYYYMMDD 형식 문자열)
    """
    details = search_festival_by_title(festival_name)
    if details:
        return details.get("start_date"), details.get("end_date")
    return None, None

if __name__ == "__main__":
    # 테스트
    print("="*60)
    print("축제 검색 테스트")
    print("="*60)

    test_keywords = ["강릉커피축제", "커피", "부산"]

    for keyword in test_keywords:
        print(f"\n'{keyword}' 검색:")
        details = search_festival_by_title(keyword)
        if details:
            print(f"  제목: {details['title']}")
            print(f"  기간: {details['start_date']} ~ {details['end_date']}")
            print(f"  주소: {details['addr1']} {details['addr2']}")
        else:
            print(f"  검색 결과 없음")
