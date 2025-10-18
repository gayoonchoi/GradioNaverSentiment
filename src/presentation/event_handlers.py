# src/presentation/event_handlers.py
import gradio as gr
import pandas as pd
# 분리된 모듈 임포트
from ..data import festival_loader
from ..infrastructure.reporting.charts import create_donut_chart, create_sentence_score_bar_chart
from ..application.utils import change_page # utils에서 임포트
from ..application.result_packager import package_festival_details # result_packager에서 임포트

def update_individual_charts(evt: gr.SelectData, df_full: pd.DataFrame, judgments_list: list, page_num: int):
    """모든 블로그 표 클릭을 처리하는 통합 핸들러"""
    if not evt.value or not isinstance(judgments_list, list) or not judgments_list : # judgments_list 타입 및 빈 리스트 체크 추가
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False, open=False)

    PAGE_SIZE = 10
    try:
        actual_index = (int(page_num) - 1) * PAGE_SIZE + evt.index[0]

        # 인덱스 범위 체크
        if not (0 <= actual_index < len(df_full) and 0 <= actual_index < len(judgments_list)):
             print(f"오류: 잘못된 인덱스 접근 시도 - actual_index={actual_index}, df_len={len(df_full)}, judge_len={len(judgments_list)}")
             return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False, open=False)

        selected_row = df_full.iloc[actual_index]
        # 데이터 유효성 체크 추가
        blog_title = selected_row.get("블로그 제목", "제목 없음")
        pos_count = int(selected_row.get("긍정 문장 수", 0))
        neg_count = int(selected_row.get("부정 문장 수", 0))
        summary_text = str(selected_row.get("긍/부정 문장 요약", "")).replace('*', '').replace('---', '')
        judgments = judgments_list[actual_index]

        # judgments 유효성 체크
        if not isinstance(judgments, list):
             print(f"오류: judgments가 리스트가 아님 - index={actual_index}, type={type(judgments)}")
             judgments = [] # 오류 시 빈 리스트로 처리

        score_chart = create_sentence_score_bar_chart(judgments, f'{blog_title[:20]}... 문장별 점수')
        donut_chart = create_donut_chart(pos_count, neg_count, f'{blog_title[:20]}... 긍/부정 비율')
        
        return gr.update(value=donut_chart, visible=True), gr.update(value=score_chart, visible=True), gr.update(value=summary_text, visible=True), gr.update(open=True, visible=True)
        
    except IndexError:
         print(f"오류: 인덱스 범위 초과 - page_num={page_num}, evt.index={evt.index}, df_len={len(df_full)}, judge_len={len(judgments_list)}")
         return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False, open=False)
    except Exception as e:
         print(f"update_individual_charts 오류: {e}")
         import traceback
         traceback.print_exc()
         return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False, open=False)


def update_festival_detail_charts(evt: gr.SelectData, df_full: pd.DataFrame, festival_full_results: list, page_num: int):
    """축제 표 클릭 핸들러"""
    if not evt.value or not isinstance(festival_full_results, list) or not festival_full_results:
        return [gr.update(visible=False)] * 8

    PAGE_SIZE = 10
    try:
        actual_index = (int(page_num) - 1) * PAGE_SIZE + evt.index[0]
        
        if not (0 <= actual_index < len(df_full) and 0 <= actual_index < len(festival_full_results)):
             print(f"오류: 잘못된 인덱스 접근 시도 (축제) - actual_index={actual_index}, df_len={len(df_full)}, results_len={len(festival_full_results)}")
             return [gr.update(visible=False)] * 8

        selected_row = df_full.iloc[actual_index]
        festival_name = selected_row.get("축제명", "이름 없음")
        selected_festival_result = festival_full_results[actual_index]

        # package_festival_details 함수가 딕셔너리를 받는지 확인
        if not isinstance(selected_festival_result, dict):
             print(f"오류: festival_full_results의 요소가 dict가 아님 - index={actual_index}, type={type(selected_festival_result)}")
             return [f"오류: 축제 '{festival_name}'의 상세 데이터 형식 오류"] + [gr.update(visible=False)] * 7

        return package_festival_details(selected_festival_result, festival_name)
        
    except IndexError:
         print(f"오류: 인덱스 범위 초과 (축제) - page_num={page_num}, evt.index={evt.index}, df_len={len(df_full)}, results_len={len(festival_full_results)}")
         return [gr.update(visible=False)] * 8
    except Exception as e:
         print(f"update_festival_detail_charts 오류: {e}")
         import traceback
         traceback.print_exc()
         return [gr.update(visible=False)] * 8


# --- 드롭다운 업데이트 함수들 ---
def update_cat2_choices(cat1): 
    choices = festival_loader.get_cat2_choices(cat1)
    return gr.update(choices=choices, value=None, interactive=bool(choices))

def update_cat3_choices(cat1, cat2): 
    choices = festival_loader.get_cat3_choices(cat1, cat2)
    return gr.update(choices=choices, value=None, interactive=bool(choices))

def update_festival_choices(cat1, cat2, cat3):
    festivals = festival_loader.get_festivals(cat1, cat2, cat3)
    return gr.update(choices=festivals, value=None, interactive=bool(festivals))

# change_page 함수는 utils.py에서 임포트하여 사용
# package_festival_details 함수는 result_packager.py에서 임포트하여 사용