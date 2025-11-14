"""
계절별 축제 분석 로직

festival_trends_summary.csv를 기반으로 계절별 인기 축제를 분석하고
워드클라우드, 타임라인 그래프, 테이블 데이터를 생성합니다.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
import datetime
import io

# 프로젝트 루트
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUMMARY_CSV_PATH = os.path.join(PROJECT_ROOT, "database", "festival_trends_summary.csv")
FONT_PATH = r"C:\Windows\Fonts\malgun.ttf"

# 계절별 색상
SEASON_COLORS = {
    "봄": ["#FF3F33", "#FFB5A7", "#FFE6E1", "#075B5E", "#9FC87E"],
    "여름": ["#799EFF", "#A7E9FF", "#FEFFC4", "#FFDE63", "#FFBC4C"],
    "가을": ["#0C0C0C", "#63372C", "#481E14", "#9B3922", "#F2613F"],
    "겨울": ["#000000", "#0B60B0", "#2081C3", "#40A2D8", "#F0EDCF"]
}


def load_seasonal_data(season: str = None):
    """
    트렌드 요약 데이터 로드

    Args:
        season: 계절 필터 (None이면 전체)

    Returns:
        pd.DataFrame: 트렌드 데이터
    """
    if not os.path.exists(SUMMARY_CSV_PATH):
        raise FileNotFoundError(
            f"트렌드 데이터 파일을 찾을 수 없습니다: {SUMMARY_CSV_PATH}\n"
            f"scripts/collect_all_trends.py를 먼저 실행해주세요."
        )

    df = pd.read_csv(SUMMARY_CSV_PATH)

    if season:
        df = df[df['season'] == season]

    return df


def get_top_festivals(season: str, top_n: int = 10):
    """
    계절별 상위 N개 축제 반환

    Args:
        season: 계절
        top_n: 상위 N개

    Returns:
        pd.DataFrame: 상위 축제 데이터
    """
    df = load_seasonal_data(season)
    df = df.sort_values('max_ratio', ascending=False).head(top_n)
    return df


def get_festival_frequency_dict(season: str, top_n: int = 120):
    """
    워드클라우드용 {축제명: 검색량} 딕셔너리 생성

    Args:
        season: 계절
        top_n: 상위 N개

    Returns:
        dict: {축제명: 검색량}
    """
    df = load_seasonal_data(season)
    df = df.sort_values('max_ratio', ascending=False).head(top_n)
    return dict(zip(df['festival_name'], df['max_ratio']))


def create_timeline_graph(season: str, top_n: int = 10) -> str:
    """
    계절별 상위 축제 타임라인 그래프 생성

    Args:
        season: 계절
        top_n: 상위 N개

    Returns:
        str: 임시 이미지 파일 경로
    """
    import uuid

    df = get_top_festivals(season, top_n)

    if df.empty:
        raise ValueError(f"{season} 시즌 데이터가 없습니다.")

    # 날짜 변환
    df['event_start_date'] = pd.to_datetime(df['event_start_date'])
    df['event_end_date'] = pd.to_datetime(df['event_end_date'])

    # 색상
    palette = SEASON_COLORS.get(season, SEASON_COLORS["봄"])

    # 그래프 생성
    fig, ax = plt.subplots(figsize=(13, 6))

    for i, row in df.iterrows():
        duration = (row['event_end_date'] - row['event_start_date']).days
        ax.barh(
            y=row['festival_name'],
            width=duration,
            left=row['event_start_date'],
            color=palette[0],
            alpha=0.7
        )
        ax.scatter(row['event_start_date'], row['festival_name'], color=palette[-1], s=35, zorder=3)
        ax.scatter(row['event_end_date'], row['festival_name'], color=palette[-1], s=35, zorder=3)

        # 검색량 표시
        ax.text(
            row['event_end_date'] + pd.Timedelta(days=2),
            row['festival_name'],
            f"{row['max_ratio']:.0f}",
            va='center',
            fontsize=10,
            color="#333"
        )

    ax.set_xlabel("축제 기간", fontsize=12, labelpad=10,
                  fontproperties=font_manager.FontProperties(fname=FONT_PATH))
    ax.set_ylabel("")
    ax.set_title(f"{season} 시즌 상위 {top_n}개 축제 기간 및 검색량", fontsize=18, pad=15, weight="bold",
                 fontproperties=font_manager.FontProperties(fname=FONT_PATH))
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.grid(axis='x', linestyle='--', alpha=0.4)

    # 한글 폰트 설정
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=FONT_PATH).get_name()
    plt.rcParams['axes.unicode_minus'] = False

    plt.tight_layout()

    # 임시 파일로 저장
    temp_dir = os.path.join(os.getcwd(), "temp_images")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"timeline_{season}_{uuid.uuid4()}.png")

    fig.savefig(temp_path, dpi=350, bbox_inches="tight")
    plt.close(fig)

    return temp_path


def get_table_data(season: str, top_n: int = 10):
    """
    Gradio DataTable용 데이터 반환

    Args:
        season: 계절
        top_n: 상위 N개

    Returns:
        pd.DataFrame: 테이블 데이터 (순위, 축제명, 검색량, 평균검색량, 행사기간)
    """
    df = get_top_festivals(season, top_n)

    if df.empty:
        return pd.DataFrame(columns=["순위", "축제명", "최대 검색량", "평균 검색량", "행사 시작일", "행사 종료일"])

    df = df.reset_index(drop=True)
    df['순위'] = df.index + 1

    table_df = df[[
        '순위', 'festival_name', 'max_ratio', 'mean_ratio',
        'event_start_date', 'event_end_date'
    ]].copy()

    table_df.columns = ["순위", "축제명", "최대 검색량", "평균 검색량", "행사 시작일", "행사 종료일"]

    return table_df


def get_festival_names_for_season(season: str, top_n: int = 10):
    """
    계절별 상위 N개 축제명 리스트 반환 (드롭다운용)

    Args:
        season: 계절
        top_n: 상위 N개

    Returns:
        list: 축제명 리스트
    """
    df = get_top_festivals(season, top_n)
    return df['festival_name'].tolist()


def create_individual_festival_trend_graph(festival_name: str, season: str = None) -> str:
    """
    개별 축제의 트렌드 그래프 생성

    Args:
        festival_name: 축제명
        season: 계절 (선택, 색상 선택용)

    Returns:
        str: 임시 이미지 파일 경로
    """
    import uuid
    from src.infrastructure.web.naver_trend_api import get_trend_data
    import datetime

    # 축제 정보 가져오기
    df = load_seasonal_data()
    festival_row = df[df['festival_name'] == festival_name]

    if festival_row.empty:
        raise ValueError(f"축제를 찾을 수 없습니다: {festival_name}")

    festival_row = festival_row.iloc[0]
    start_date = pd.to_datetime(festival_row['event_start_date']).date()
    end_date = pd.to_datetime(festival_row['event_end_date']).date()

    # 시즌 결정
    if season is None:
        season = festival_row['season']

    # API로 트렌드 데이터 가져오기 (행사 전후 30일)
    api_start = start_date - datetime.timedelta(days=30)
    api_end = min(end_date + datetime.timedelta(days=30), datetime.date.today())

    df_trend = get_trend_data(festival_name, api_start, api_end)

    if df_trend.empty:
        raise ValueError(f"트렌드 데이터를 가져올 수 없습니다: {festival_name}")

    # 그래프 생성
    palette = SEASON_COLORS.get(season, SEASON_COLORS["봄"])

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(df_trend['period'], df_trend['ratio'],
            color=palette[0], linewidth=2.5, marker='o', markersize=4)

    # 축제 기간 강조
    ax.axvspan(pd.to_datetime(start_date), pd.to_datetime(end_date),
               alpha=0.2, color=palette[2], label='축제 기간')

    ax.set_xlabel("날짜", fontsize=12,
                  fontproperties=font_manager.FontProperties(fname=FONT_PATH))
    ax.set_ylabel("검색량", fontsize=12,
                  fontproperties=font_manager.FontProperties(fname=FONT_PATH))
    ax.set_title(f"{festival_name} 검색 트렌드", fontsize=16, weight="bold", pad=15,
                 fontproperties=font_manager.FontProperties(fname=FONT_PATH))
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend(prop=font_manager.FontProperties(fname=FONT_PATH))

    # 한글 폰트 설정
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=FONT_PATH).get_name()
    plt.rcParams['axes.unicode_minus'] = False

    plt.tight_layout()

    # 임시 파일로 저장
    temp_dir = os.path.join(os.getcwd(), "temp_images")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"festival_trend_{uuid.uuid4()}.png")

    fig.savefig(temp_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return temp_path
