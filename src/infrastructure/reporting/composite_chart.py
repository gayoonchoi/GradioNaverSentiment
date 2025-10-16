
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import math
import numpy as np

def create_composite_image(figures: list[Figure], title: str) -> Figure | None:
    """
    여러 Matplotlib Figure를 하나의 큰 Figure로 합칩니다.
    각 Figure를 이미지로 렌더링한 후, 큰 Figure의 subplot에 배치합니다.
    """
    if not figures:
        return None

    num_figures = len(figures)
    cols = 2  # 2열로 고정
    rows = math.ceil(num_figures / cols)

    # 개별 차트가 보통 (6, 1.5) 또는 (6, 4) 크기이므로, 비율을 고려하여 전체 크기 설정
    composite_fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 2.5))
    if num_figures > 1: # 차트가 하나일 때는 suptitle이 너무 커보일 수 있음
        composite_fig.suptitle(title, fontsize=20, y=0.98)
    
    # axes가 단일 객체일 경우(subplot이 1개) 배열로 만듦
    if num_figures == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    for i, fig in enumerate(figures):
        # Figure를 이미지 버퍼로 렌더링
        fig.canvas.draw()
        # RGBA 버퍼를 numpy 배열로 변환
        img_data = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
        img_w, img_h = fig.canvas.get_width_height()
        img_as_array = img_data.reshape((img_h, img_w, 4))

        # 해당 subplot에 이미지 표시
        axes[i].imshow(img_as_array)
        axes[i].set_axis_off()
        plt.close(fig)  # 메모리 해제를 위해 원본 Figure 닫기

    # 남는 subplot들을 비활성화
    for j in range(num_figures, len(axes)):
        axes[j].set_axis_off()

    composite_fig.tight_layout()
    return composite_fig
