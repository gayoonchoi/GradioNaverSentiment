# coding: utf-8
import pandas as pd
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# CSV 파일 경로
festival_csv = r"C:\Users\Eric\github\GradioNaverSentiment\database\축제공연행사csv.CSV"
culture_csv = r"C:\Users\Eric\github\GradioNaverSentiment\database\문화시설csv.CSV"
course_csv = r"C:\Users\Eric\github\GradioNaverSentiment\database\여행코스csv.CSV"

def analyze_csv(file_path, name):
    print(f"\n{'='*60}")
    print(f"{name} 분석")
    print('='*60)

    # 여러 인코딩 시도
    encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']

    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc, low_memory=False)
            print(f"\n✓ 인코딩 성공: {enc}")
            print(f"총 행 수: {len(df)}")
            print(f"총 컬럼 수: {len(df.columns)}")
            print(f"\n주요 컬럼:")
            for col in df.columns[:20]:  # 처음 20개 컬럼만
                print(f"  - {col}")

            # 축제 CSV인 경우 샘플 데이터 출력
            if '축제' in name:
                print(f"\n샘플 데이터 (처음 3행):")
                if 'title' in df.columns:
                    print("\n제목 샘플:")
                    print(df['title'].head(3).tolist())
                if 'eventstartdate' in df.columns:
                    print("\n시작일 샘플:")
                    print(df['eventstartdate'].head(3).tolist())
                if 'eventenddate' in df.columns:
                    print("\n종료일 샘플:")
                    print(df['eventenddate'].head(3).tolist())

                # "강릉커피축제" 검색
                if 'title' in df.columns:
                    matches = df[df['title'].str.contains('커피', na=False)]
                    print(f"\n'커피' 포함 축제: {len(matches)}개")
                    if len(matches) > 0:
                        print(matches[['title', 'eventstartdate', 'eventenddate']].head(5))

            return df, enc

        except Exception as e:
            print(f"✗ {enc} 실패: {str(e)[:100]}")
            continue

    return None, None

# 세 파일 분석
festival_df, festival_enc = analyze_csv(festival_csv, "축제공연행사")
culture_df, culture_enc = analyze_csv(culture_csv, "문화시설")
course_df, course_enc = analyze_csv(course_csv, "여행코스")

print(f"\n{'='*60}")
print("분석 완료")
print('='*60)
