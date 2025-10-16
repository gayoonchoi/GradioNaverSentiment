import pandas as pd
import json
import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import sys

# --- Configuration ---
CSV_PATH = "C:\\Users\\SBA\\github\\GradioNaverSentiment\\축제공연행사csv.CSV"
FESTIVAL_COLUMN_NAME = 'title'
OVERVIEW_COLUMN_NAME = 'overview'
PROGRAM_COLUMN_NAME = 'program' # 행사내용 컬럼
JSON_OUTPUT_PATH = "C:\\Users\\SBA\\github\\GradioNaverSentiment\\festivals\\festivals_type.json"
CATEGORIES = [
    "전통/역사",
    "문화/예술/공연",
    "음식/특산물",
    "자연/생태/계절",
    "체험/레저",
    "도시/지역 이벤트",
    "기타"
]

# --- Load API Key ---
def setup_environment():
    dotenv_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(dotenv_path):
        print(f".env file found at {dotenv_path}. Loading environment variables.")
        load_dotenv(dotenv_path=dotenv_path, encoding="utf-8")
    else:
        print(f".env file not found at {dotenv_path}. Make sure GOOGLE_API_KEY is set as an environment variable.")

def get_google_api_key():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables or .env file.")
    return api_key

# --- Main Logic ---
def classify_festival(llm, festival_name, festival_overview, festival_program):
    overview_text = ""
    if isinstance(festival_overview, str) and festival_overview.strip():
        overview_text = f'\n\n행사 소개: "{festival_overview[:300]}..."'

    program_text = ""
    if isinstance(festival_program, str) and festival_program.strip():
        program_text = f'\n\n행사 내용: "{festival_program[:300]}..."'

    prompt = f"""
    주어진 축제 이름, 소개, 내용을 바탕으로, 아래 7개의 카테고리 중 어디에 가장 적합한지 번호만 반환해주세요.

    축제 이름: "{festival_name}"{overview_text}{program_text}

    카테고리:
    1. 전통/역사 (예: 문화재 야행, 단오제, 왕실 문화 축제)
    2. 문화/예술/공연 (예: 영화제, 음악 페스티벌, 연극제, 미술 전시)
    3. 음식/특산물 (예: 인삼 축제, 김치 축제, 커피 페스티벌)
    4. 자연/생태/계절 (예: 벚꽃 축제, 눈꽃 축제, 반딧불 축제, 억새 축제)
    5. 체험/레저 (예: 머드 축제, 물총 축제, 캠핑 페스티벌, 걷기 축제)
    6. 도시/지역 이벤트 (예: 빛 축제, 불꽃 축제, 지역민의 날, 야시장)
    7. 기타 (위 6개에 명확히 속하지 않는 경우)

    가장 적합한 카테고리 번호:
    """
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        for char in content:
            if char.isdigit():
                category_index = int(char) - 1
                if 0 <= category_index < len(CATEGORIES):
                    return category_index
        print(f"Warning: Could not parse category from '{content}' for '{festival_name}'. Defaulting to '기타'.")
        return 6 # Default to '기타'
    except Exception as e:
        print(f"Error classifying '{festival_name}': {e}")
        return 6 # Default to '기타'

def main():
    setup_environment()
    try:
        api_key = get_google_api_key()
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=api_key, temperature=0.0)
    except ValueError as e:
        print(f"API Key error: {e}")
        sys.exit(1)

    try:
        df = pd.read_csv(CSV_PATH, encoding='cp949')
    except FileNotFoundError:
        print(f"Error: CSV file not found at {CSV_PATH}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

    required_cols = [FESTIVAL_COLUMN_NAME, OVERVIEW_COLUMN_NAME, PROGRAM_COLUMN_NAME]
    if not all(col in df.columns for col in required_cols):
        print(f"Error: Columns '{required_cols}' not found in the CSV file.")
        print(f"Available columns: {df.columns.tolist()}")
        sys.exit(1)

    classified_festivals = {category: [] for category in CATEGORIES}
    
    unique_festivals = df.drop_duplicates(subset=[FESTIVAL_COLUMN_NAME])
    total_festivals = len(unique_festivals)

    for i, row in unique_festivals.iterrows():
        festival_name = row[FESTIVAL_COLUMN_NAME]
        festival_overview = row[OVERVIEW_COLUMN_NAME]
        festival_program = row[PROGRAM_COLUMN_NAME]
        
        if not isinstance(festival_name, str) or not festival_name.strip():
            continue

        print(f"Processing ({i+1}/{total_festivals}): {festival_name}")
        category_index = classify_festival(llm, festival_name, festival_overview, festival_program)
        category_name = CATEGORIES[category_index]
        classified_festivals[category_name].append(festival_name)
        time.sleep(0.5) # API rate limiting

    output_dir = os.path.dirname(JSON_OUTPUT_PATH)
    if not os.path.exists(output_dir):
        print(f"Creating directory: {output_dir}")
        os.makedirs(output_dir)

    print(f"Saving results to {JSON_OUTPUT_PATH}...")
    with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(classified_festivals, f, ensure_ascii=False, indent=4)

    print("Classification complete.")

if __name__ == "__main__":
    main()