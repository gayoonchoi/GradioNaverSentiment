# src/infrastructure/database/csv_importer.py
"""CSV 파일을 SQLite 데이터베이스로 import하는 모듈"""
import pandas as pd
import os
from .db_manager import get_connection, initialize_database

# CSV 파일 경로
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
FESTIVAL_CSV = os.path.join(BASE_DIR, "database", "축제공연행사csv.CSV")
CULTURE_CSV = os.path.join(BASE_DIR, "database", "문화시설csv.CSV")
COURSE_CSV = os.path.join(BASE_DIR, "database", "여행코스csv.CSV")

def import_festivals():
    """축제 CSV 데이터를 데이터베이스에 import합니다."""
    print("축제 데이터 import 시작...")

    try:
        # CSV 읽기 (cp949 인코딩)
        df = pd.read_csv(FESTIVAL_CSV, encoding='cp949', low_memory=False)
        print(f"  - CSV 읽기 완료: {len(df)}개 행")

        # 필요한 컬럼만 선택
        columns_to_import = [
            'contentid', 'title', 'eventstartdate', 'eventenddate', 'addr1', 'addr2',
            'areacode', 'cat1', 'cat2', 'cat3', 'contenttypeid', 'mapx', 'mapy',
            'tel', 'firstimage', 'firstimage2'
        ]

        # CSV에 실제로 존재하는 컬럼만 선택
        available_columns = [col for col in columns_to_import if col in df.columns]
        df_filtered = df[available_columns].copy()

        # NaN을 None으로 변환
        df_filtered = df_filtered.where(pd.notna(df_filtered), None)

        # 데이터베이스에 저장
        conn = get_connection()
        cursor = conn.cursor()

        # 기존 데이터 삭제
        cursor.execute('DELETE FROM festivals')

        # 데이터 삽입
        inserted = 0
        for _, row in df_filtered.iterrows():
            try:
                placeholders = ', '.join(['?' for _ in available_columns])
                columns_str = ', '.join(available_columns)
                query = f'INSERT INTO festivals ({columns_str}) VALUES ({placeholders})'
                cursor.execute(query, tuple(row[col] for col in available_columns))
                inserted += 1
            except Exception as e:
                print(f"    경고: 행 삽입 실패 - {e}")
                continue

        conn.commit()
        conn.close()

        print(f"  [OK] 축제 데이터 import 완료: {inserted}개")
        return inserted

    except Exception as e:
        print(f"  [ERROR] 축제 데이터 import 실패: {e}")
        import traceback
        traceback.print_exc()
        return 0

def import_culture_facilities():
    """문화시설 CSV 데이터를 데이터베이스에 import합니다."""
    print("문화시설 데이터 import 시작...")

    try:
        df = pd.read_csv(CULTURE_CSV, encoding='cp949', low_memory=False)
        print(f"  - CSV 읽기 완료: {len(df)}개 행")

        columns_to_import = [
            'contentid', 'title', 'addr1', 'addr2', 'areacode', 'cat1', 'cat2', 'cat3',
            'contenttypeid', 'mapx', 'mapy', 'tel', 'firstimage', 'firstimage2'
        ]

        available_columns = [col for col in columns_to_import if col in df.columns]
        df_filtered = df[available_columns].copy()
        df_filtered = df_filtered.where(pd.notna(df_filtered), None)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM culture_facilities')

        inserted = 0
        for _, row in df_filtered.iterrows():
            try:
                placeholders = ', '.join(['?' for _ in available_columns])
                columns_str = ', '.join(available_columns)
                query = f'INSERT INTO culture_facilities ({columns_str}) VALUES ({placeholders})'
                cursor.execute(query, tuple(row[col] for col in available_columns))
                inserted += 1
            except Exception as e:
                continue

        conn.commit()
        conn.close()

        print(f"  [OK] 문화시설 데이터 import 완료: {inserted}개")
        return inserted

    except Exception as e:
        print(f"  [ERROR] 문화시설 데이터 import 실패: {e}")
        return 0

def import_travel_courses():
    """여행코스 CSV 데이터를 데이터베이스에 import합니다."""
    print("여행코스 데이터 import 시작...")

    try:
        df = pd.read_csv(COURSE_CSV, encoding='cp949', low_memory=False)
        print(f"  - CSV 읽기 완료: {len(df)}개 행")

        columns_to_import = [
            'contentid', 'title', 'addr1', 'addr2', 'areacode', 'cat1', 'cat2', 'cat3',
            'contenttypeid', 'mapx', 'mapy', 'firstimage', 'firstimage2'
        ]

        available_columns = [col for col in columns_to_import if col in df.columns]
        df_filtered = df[available_columns].copy()
        df_filtered = df_filtered.where(pd.notna(df_filtered), None)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM travel_courses')

        inserted = 0
        for _, row in df_filtered.iterrows():
            try:
                placeholders = ', '.join(['?' for _ in available_columns])
                columns_str = ', '.join(available_columns)
                query = f'INSERT INTO travel_courses ({columns_str}) VALUES ({placeholders})'
                cursor.execute(query, tuple(row[col] for col in available_columns))
                inserted += 1
            except Exception as e:
                continue

        conn.commit()
        conn.close()

        print(f"  [OK] 여행코스 데이터 import 완료: {inserted}개")
        return inserted

    except Exception as e:
        print(f"  [ERROR] 여행코스 데이터 import 실패: {e}")
        return 0

def import_all_data():
    """모든 CSV 데이터를 데이터베이스에 import합니다."""
    print("="*60)
    print("CSV 데이터 import 시작")
    print("="*60)

    # 데이터베이스 초기화
    initialize_database()

    # 각 CSV import
    festival_count = import_festivals()
    culture_count = import_culture_facilities()
    course_count = import_travel_courses()

    print("="*60)
    print("CSV 데이터 import 완료")
    print(f"  - 축제: {festival_count}개")
    print(f"  - 문화시설: {culture_count}개")
    print(f"  - 여행코스: {course_count}개")
    print(f"  - 총합: {festival_count + culture_count + course_count}개")
    print("="*60)

if __name__ == "__main__":
    import_all_data()
