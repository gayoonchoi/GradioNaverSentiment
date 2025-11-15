"""
계절별 축제 워드클라우드 생성 모듈

Tour_Trend_WordCloud의 로직을 기반으로 계절별 인기 축제를
워드클라우드로 시각화합니다.
"""

import os
import matplotlib
matplotlib.use('Agg')  # GUI 없는 백엔드 사용 (FastAPI 비동기 환경 호환)
import matplotlib.pyplot as plt
from matplotlib import font_manager
from wordcloud import WordCloud
import numpy as np
from PIL import Image
import random
import io

# 한글 폰트 설정
FONT_PATH = r"C:\Windows\Fonts\malgun.ttf"

# 계절별 색상 팔레트
SEASON_COLORS = {
    "봄": ["#FF3F33", "#FFB5A7", "#FFE6E1", "#075B5E", "#9FC87E"],
    "여름": ["#799EFF", "#A7E9FF", "#FEFFC4", "#FFDE63", "#FFBC4C"],
    "가을": ["#0C0C0C", "#63372C", "#481E14", "#9B3922", "#F2613F"],
    "겨울": ["#000000", "#0B60B0", "#2081C3", "#40A2D8", "#F0EDCF"]
}

# 마스크 이미지 경로 (선택적)
MASK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets")


def blended_color_func(palette):
    """색상 블렌딩 함수 생성기"""
    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        base_idx = int(min(font_size / 100 * len(palette), len(palette) - 1))
        color = palette[base_idx]
        if random.random() > 0.5:
            color = random.choice(palette)
        return color
    return color_func


def create_seasonal_wordcloud(festival_freq: dict, season: str, mask_image_path: str = None) -> bytes:
    """
    계절별 축제 워드클라우드 생성

    Args:
        festival_freq: {축제명: 검색량} 딕셔너리
        season: 계절 ("봄", "여름", "가을", "겨울")
        mask_image_path: 마스크 이미지 경로 (선택)

    Returns:
        bytes: PNG 이미지 바이트 데이터
    """
    if not festival_freq:
        raise ValueError("축제 데이터가 비어있습니다.")

    # 색상 팔레트
    palette = SEASON_COLORS.get(season, SEASON_COLORS["봄"])

    # 마스크 이미지 로드 (있으면)
    mask = None
    if mask_image_path and os.path.exists(mask_image_path):
        try:
            mask_img = np.array(Image.open(mask_image_path).convert("L"))
            mask = np.where(mask_img > 128, 255, 0).astype(np.uint8)
        except Exception as e:
            print(f"마스크 이미지 로드 실패: {e}")

    # 워드클라우드 생성
    wc = WordCloud(
        font_path=FONT_PATH,
        width=1400,
        height=800,
        background_color="white",
        mask=mask,
        contour_color="#ddd" if mask is not None else None,
        contour_width=1 if mask is not None else 0,
        max_words=120,
        prefer_horizontal=0.9,
        relative_scaling=0.45,
        color_func=blended_color_func(palette),
        collocations=False,
        scale=3
    ).generate_from_frequencies(festival_freq)

    # 시각화
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(f"{season} 시즌 검색 인기 축제", fontsize=24, weight="bold", pad=22,
                 fontproperties=font_manager.FontProperties(fname=FONT_PATH))
    plt.tight_layout()

    # 바이트로 변환
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=350, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)

    return buf.getvalue()


def save_seasonal_wordcloud(festival_freq: dict, season: str, output_path: str, mask_image_path: str = None):
    """
    계절별 워드클라우드를 파일로 저장

    Args:
        festival_freq: {축제명: 검색량} 딕셔너리
        season: 계절
        output_path: 출력 파일 경로
        mask_image_path: 마스크 이미지 경로 (선택)
    """
    image_bytes = create_seasonal_wordcloud(festival_freq, season, mask_image_path)

    with open(output_path, 'wb') as f:
        f.write(image_bytes)

    print(f"워드클라우드 저장 완료: {output_path}")


def create_wordcloud_for_gradio(festival_freq: dict, season: str) -> str:
    """
    Gradio용 워드클라우드 생성 (임시 파일 경로 반환)

    Args:
        festival_freq: {축제명: 검색량} 딕셔너리
        season: 계절

    Returns:
        str: 임시 이미지 파일 경로
    """
    import tempfile
    import uuid

    # 임시 디렉토리에 저장
    temp_dir = os.path.join(os.getcwd(), "temp_images")
    os.makedirs(temp_dir, exist_ok=True)

    temp_path = os.path.join(temp_dir, f"wordcloud_{season}_{uuid.uuid4()}.png")

    # 마스크 이미지 확인 (있으면 사용)
    mask_files = {
        "봄": "mask_spring.png",
        "여름": "mask_summer.png",
        "가을": "mask_fall.png",
        "겨울": "mask_winter.png"
    }

    mask_path = None
    if os.path.exists(MASK_DIR):
        potential_mask = os.path.join(MASK_DIR, mask_files.get(season, ""))
        if os.path.exists(potential_mask):
            mask_path = potential_mask

    save_seasonal_wordcloud(festival_freq, season, temp_path, mask_path)

    return temp_path
