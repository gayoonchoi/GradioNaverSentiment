import matplotlib
matplotlib.use('Agg') # UI 백엔드가 없는 환경을 위한 설정
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib import font_manager, rc

def setup_matplotlib_font():
    """한글 폰트를 설정합니다."""
    try:
        rc('font', family='Malgun Gothic')
    except:
        print("Malgun Gothic 폰트를 찾을 수 없습니다. 다른 한글 폰트로 설정해주세요.")
    plt.rcParams['axes.unicode_minus'] = False # 마이너스 부호 깨짐 방지

# 모듈 로드 시 폰트 설정
setup_matplotlib_font()

def create_donut_chart(total_pos: int, total_neg: int, title: str) -> Figure | None:
    total = total_pos + total_neg
    if total == 0:
        return None

    pos_perc = (total_pos / total) * 100
    neg_perc = (total_neg / total) * 100

    fig, ax = plt.subplots(figsize=(6, 4), subplot_kw=dict(aspect="equal"))

    labels = ['긍정', '부정']
    sizes = [pos_perc, neg_perc]
    colors = ['#3498db', '#e74c3c']
    explode = (0.05, 0)

    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=None, autopct='%1.1f%%',
                                      startangle=90, colors=colors, pctdistance=0.85,
                                      wedgeprops=dict(width=0.3, edgecolor='w'))

    ax.set_title(title, fontsize=16, pad=20)
    ax.legend(wedges, [f'{l} ({s:.1f}%)' for l, s in zip(labels, sizes)],
              title="감성",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1))

    plt.setp(autotexts, size=10, weight="bold", color="white")
    plt.tight_layout()
    return fig

def create_stacked_bar_chart(total_pos: int, total_neg: int, title: str, figsize=(6, 1.5)) -> Figure | None:
    total = total_pos + total_neg
    if total == 0:
        return None

    pos_perc = (total_pos / total) * 100
    neg_perc = (total_neg / total) * 100

    fig, ax = plt.subplots(figsize=figsize)

    labels = [title]
    pos_data = [pos_perc]
    neg_data = [neg_perc]

    ax.barh(labels, pos_data, color='#3498db', edgecolor='white', height=0.3, label=f'긍정 ({pos_perc:.1f}%)')
    ax.barh(labels, neg_data, left=pos_data, color='#e74c3c', edgecolor='white', height=0.3, label=f'부정 ({neg_perc:.1f}%)')

    ax.set_xlabel('비율 (%)', fontsize=9)
    ax.set_title(f'{title} 긍정/부정 비율', fontsize=12)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(axis='x', labelsize=8)
    ax.tick_params(axis='y', labelsize=10)

    handles, legend_labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], legend_labels[::-1], loc='upper center', bbox_to_anchor=(0.5, -0.3), ncol=2, frameon=False, fontsize=8)

    plt.tight_layout(pad=2.5)
    return fig
