# src/infrastructure/reporting/wordclouds.py
import os
import uuid
from wordcloud import WordCloud
from konlpy.tag import Okt
from collections import Counter
import re
import numpy as np
from PIL import Image

okt = Okt()

STOPWORDS = set([
    '가', '이', '은', '는', '을', '를', '의', '에', '와', '과', '도', '으로', '로', '하다', '되다', '이다', '있다', '없다',
    '것', '수', '등', '그', '저', '이', '저희', '때', '그것', '곳', '더', '또', '및', '좀', '잘', '꼭', '축제', '후기',
    '입니다', '있습니다', '있어요', '없어요', '해요', '하고', '하는', '그리고', '그래서', '그런데', '하지만', '이제',
    '정말', '매우', '아주', '너무', '진짜', '완전', '많이', '전', '안', '못', '위해', '통해', '대한', '때문', '여기',
    '거기', '저기', '오늘', '내일', '어제', '먼저', '다음', '바로', '다시', '한번', '계속', '이후', '이전', '속',
    '위', '아래', '앞', '뒤', '근처', '주변', '사이', '중', '하나', '정도', '관련', '부분', '경우', '생각', '느낌',
    '방문', '사용', '체험', '추천', '가격', '시간', '사람', '분', '곳', '날', '수', '것', '저', '제', '내', '나', '너',
    '우리', '다른', '모든', '여러', '각종', '다양한', '함께', '직접', '역시', '일단', '사실', '주차', '이용', '가능'
])

FONT_PATHS = [
    'C:/gemini_translation/폰트/maplestory_regular.ttf',
    'C:/gemini_translation/폰트/dunggeunmo.ttf',
    'C:/Windows/Fonts/Malgun.ttf',
    '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
]

def find_font_path():
    for path in FONT_PATHS:
        if os.path.exists(path):
            print(f"[WordCloud] Font found: {path}")
            return path
    print("[WordCloud] Error: No valid font file found in the specified paths.")
    return None

def create_wordcloud(text: str, keyword: str, mask_path: str = None) -> str:
    print(f"[WordCloud] create_wordcloud started for keyword: {keyword}")
    if not text:
        print("[WordCloud] Text is empty, returning None.")
        return None

    try:
        font_path = find_font_path()
        if not font_path:
            return None

        mask_array = None
        if mask_path and os.path.exists(mask_path):
            try:
                print(f"[WordCloud] Attempting to load mask: {mask_path}")
                img = Image.open(mask_path).convert("L")
                mask_array = np.array(img, dtype=np.uint8)
                print(f"[WordCloud] Mask loaded successfully. Shape: {mask_array.shape}, Type: {mask_array.dtype}, Unique values: {np.unique(mask_array)}")
            except Exception as e:
                print(f"[WordCloud] Error loading mask image: {e}")
                mask_array = None
        else:
            print(f"[WordCloud] No valid mask path provided or file not found: {mask_path}")

        nouns = okt.nouns(text)
        words = [n for n in nouns if n not in STOPWORDS and len(n) > 1]
        words = [w for w in words if keyword not in w]

        if not words:
            print("[WordCloud] No meaningful words left after filtering.")
            return None

        counter = Counter(words)
        
        if mask_array is not None:
            print("[WordCloud] Passing non-None mask to WordCloud constructor.")
        else:
            print("[WordCloud] Passing None mask to WordCloud constructor.")

        wc = WordCloud(
            font_path=font_path,
            width=800,
            height=800,
            background_color='white',
            mask=mask_array,
            max_words=100,
            contour_width=1,
            contour_color='steelblue'
        ).generate_from_frequencies(counter)

        temp_dir = os.path.join(os.getcwd(), "temp_images")
        os.makedirs(temp_dir, exist_ok=True)
        
        sanitized_keyword = re.sub(r'[\\/:*?"<>|]', '_', keyword)
        file_path = os.path.join(temp_dir, f"wc_{sanitized_keyword}_{uuid.uuid4()}.png")
        
        wc.to_file(file_path)
        
        print(f"[WordCloud] Generation complete: {file_path}")
        return file_path

    except Exception as e:
        print(f"[WordCloud] Error during generation: {e}")
        traceback.print_exc()
        return None