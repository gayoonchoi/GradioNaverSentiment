import json
import os
from functools import lru_cache

# 현재 파일의 위치를 기준으로 프로젝트 루트 디렉토리를 계산합니다.
# (src/data/festival_loader.py -> src/data -> src -> GradioNaverSentiment)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FESTIVALS_DIR = os.path.join(PROJECT_ROOT, "festivals")

CATEGORY_FILES = [
    "festivals_type_계절과_자연.json",
    "festivals_type_도시와_커뮤니티.json",
    "festivals_type_레저와_스포츠.json",
    "festivals_type_문화와_예술.json",
    "festivals_type_미식과_특산물.json",
    "festivals_type_전통과_역사.json",
    "festivals_type_종교와_영성.json",
    "festivals_type_체험과_교육.json",
]


def strip_nested_keys(d):
    """딕셔너리의 모든 키에서 재귀적으로 공백을 제거합니다."""
    if isinstance(d, dict):
        return {key.strip(): strip_nested_keys(value) for key, value in d.items()}
    elif isinstance(d, list):
        # 리스트 내의 각 항목에 대해 재귀적으로 함수를 적용합니다 (필요한 경우).
        return [strip_nested_keys(item) for item in d]
    return d


@lru_cache(maxsize=1)
def load_festival_data():
    """각 파일이 대분류를 최상위 키로 갖는 구조에 맞춰 데이터를 로드하고 합칩니다."""
    combined_data = {}
    for filename in CATEGORY_FILES:
        file_path = os.path.join(FESTIVALS_DIR, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data_from_file = json.load(f)
                # JSON 키의 모든 공백을 재귀적으로 제거합니다.
                stripped_data = strip_nested_keys(data_from_file)
                combined_data.update(stripped_data)
        except FileNotFoundError:
            print(f"Warning: Festival JSON file not found at {file_path}")
            continue
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {file_path}")
            continue
    return combined_data


def get_cat1_choices():
    """대분류 목록을 반환합니다."""
    data = load_festival_data()
    return list(data.keys())


def get_cat2_choices(cat1: str):
    """선택된 대분류에 따른 중분류 목록을 반환합니다."""
    if not cat1:
        return []
    data = load_festival_data()
    # 입력값에서도 공백을 제거하여 일관성을 유지합니다.
    return list(data.get(cat1.strip(), {}).keys())


def get_cat3_choices(cat1: str, cat2: str):
    """선택된 대분류, 중분류에 따른 소분류 목록을 반환합니다."""
    if not cat1 or not cat2:
        return []
    data = load_festival_data()
    # 입력값에서도 공백을 제거하여 일관성을 유지합니다.
    return list(data.get(cat1.strip(), {}).get(cat2.strip(), {}).keys())


def get_festivals(cat1: str, cat2: str = None, cat3: str = None) -> list:
    """선택된 분류에 해당하는 모든 축제 목록을 반환합니다."""
    data = load_festival_data()
    if not cat1:
        return []

    festivals = []
    if cat1 and not cat2 and not cat3:
        # 대분류만 선택된 경우
        for cat2_data in data.get(cat1, {}).values():
            for cat3_data in cat2_data.values():
                festivals.extend(cat3_data)
    elif cat1 and cat2 and not cat3:
        # 중분류까지 선택된 경우
        cat2_data = data.get(cat1, {}).get(cat2, {})
        for cat3_data in cat2_data.values():
            festivals.extend(cat3_data)
    elif cat1 and cat2 and cat3:
        # 소분류까지 모두 선택된 경우
        festivals.extend(data.get(cat1, {}).get(cat2, {}).get(cat3, []))

    return sorted(list(set(festivals)))  # 중복 제거 후 정렬
