# src/infrastructure/web/tour_api_client.py
"""
축제 정보 조회 클라이언트
기존에는 TourAPI를 사용했지만, 현재는 로컬 데이터베이스를 사용합니다.
"""
from functools import lru_cache
from ..database.festival_repository import search_festival_by_title as _search_db

@lru_cache(maxsize=256)
def get_festival_details(festival_name: str) -> dict | None:
    """
    데이터베이스에서 축제 이름으로 검색하여 해당 축제의 상세 정보를 반환합니다.
    - 시작일, 종료일, 주소, 좌표 등

    Args:
        festival_name: 검색할 축제 이름

    Returns:
        축제 정보 딕셔너리 또는 None
    """
    return _search_db(festival_name)

def get_festival_period(festival_name: str) -> tuple[str | None, str | None]:
    """
    축제 이름으로 축제 기간을 조회합니다.

    Args:
        festival_name: 축제 이름

    Returns:
        (시작일, 종료일) 튜플 (YYYYMMDD 형식 문자열)
    """
    details = get_festival_details(festival_name)
    if details:
        return details.get("start_date"), details.get("end_date")
    return None, None
