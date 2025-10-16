import pandas as pd
import re
from datetime import datetime

def save_summary_to_csv(summary_data: list, keyword: str) -> str:
    """분석 요약 데이터를 CSV 파일로 저장합니다."""
    summary_df = pd.DataFrame(summary_data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 파일명에 부적합한 문자 제거
    sanitized_keyword = re.sub(r'[\\/*?"<>|]', '', keyword)
    csv_filepath = f"{sanitized_keyword}_summary_{timestamp}.csv"
    
    summary_df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
    return csv_filepath
