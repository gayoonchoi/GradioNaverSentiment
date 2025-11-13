# coding: utf-8
"""DB 통합 테스트"""
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.infrastructure.web.tour_api_client import get_festival_period, get_festival_details
from datetime import datetime

def test_festival_lookup(festival_name):
    print(f"\n{'='*60}")
    print(f"축제 이름: {festival_name}")
    print('='*60)

    # 1. get_festival_period 테스트
    start_date_str, end_date_str = get_festival_period(festival_name)

    if start_date_str and end_date_str:
        print(f"[OK] 축제 기간 조회 성공")
        print(f"  시작일: {start_date_str}")
        print(f"  종료일: {end_date_str}")

        # datetime 변환 테스트
        try:
            start_date = datetime.strptime(start_date_str, "%Y%m%d")
            end_date = datetime.strptime(end_date_str, "%Y%m%d")
            event_period = (end_date - start_date).days + 1
            print(f"  축제 기간: {event_period}일")
        except ValueError as e:
            print(f"  [ERROR] 날짜 변환 실패: {e}")

    else:
        print(f"[WARN] 축제 기간 정보 없음")

    # 2. get_festival_details 테스트
    details = get_festival_details(festival_name)
    if details:
        print(f"\n[OK] 상세 정보 조회 성공")
        print(f"  제목: {details.get('title')}")
        print(f"  주소1: {details.get('addr1')}")
        print(f"  주소2: {details.get('addr2')}")
        print(f"  카테고리: {details.get('cat1')} > {details.get('cat2')} > {details.get('cat3')}")
        print(f"  좌표: ({details.get('mapx')}, {details.get('mapy')})")
    else:
        print(f"\n[WARN] 상세 정보 없음")

if __name__ == "__main__":
    test_cases = [
        "강릉커피축제",
        "부산바다축제",
        "존재하지않는축제123",
        "커피"
    ]

    for festival_name in test_cases:
        test_festival_lookup(festival_name)

    print(f"\n{'='*60}")
    print("테스트 완료")
    print('='*60)
