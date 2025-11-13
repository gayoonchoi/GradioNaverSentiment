# src/application/analysis_service.py
import gradio as gr
import traceback
from .analysis_logic import analyze_single_keyword_fully, perform_category_analysis, perform_festival_group_analysis
from .result_packager import package_keyword_results, package_category_results
from .utils import create_driver
from ..data import festival_loader
from ..infrastructure.web.naver_trend_api import create_trend_graph, create_focused_trend_graph
from ..infrastructure.web.tour_api_client import get_festival_period

# --- 단일 키워드 분석 --- #
def analyze_keyword_and_generate_report(keyword: str, num_reviews: int, log_details: bool, progress=gr.Progress(track_tqdm=True)):
    driver = None
    num_outputs = 29
    if not keyword: return ["오류: 검색어를 입력하세요."] + [gr.update(visible=False)]*(num_outputs - 1)
    try:
        driver = create_driver()
        results = analyze_single_keyword_fully(keyword, int(num_reviews), driver, log_details, progress, "단일 분석")
        return package_keyword_results(results, keyword)
    except Exception as e:
        print(f"단일 키워드 분석 중 예외 발생: {e}")
        traceback.print_exc()
        return [f"분석 중 오류 발생: {e}"] + [gr.update(visible=False)]*(num_outputs - 1)
    finally:
        if driver: 
            try: driver.quit()
            except Exception as e_quit: print(f"WebDriver 종료 오류: {e_quit}")

# --- 키워드 비교 분석 --- #
def run_comparison_analysis(keyword_a: str, keyword_b: str, num_reviews: int, log_details: bool, progress=gr.Progress(track_tqdm=True)):
    driver = None
    num_outputs_per_keyword = 29
    if not keyword_a or not keyword_b:
        error_msg = "오류: 비교할 키워드 A와 B를 모두 입력하세요."
        error_tuple = (error_msg,) + (gr.update(visible=False),)*(num_outputs_per_keyword -1)
        return error_tuple * 2

    try:
        driver = create_driver()
        results_a = analyze_single_keyword_fully(keyword_a, int(num_reviews), driver, log_details, progress, "비교(A)")
        results_b = analyze_single_keyword_fully(keyword_b, int(num_reviews), driver, log_details, progress, "비교(B)")
        output_a = package_keyword_results(results_a, keyword_a)
        output_b = package_keyword_results(results_b, keyword_b)
        return tuple(output_a) + tuple(output_b)
    except Exception as e:
        print(f"키워드 비교 분석 중 예외 발생: {e}")
        traceback.print_exc()
        error_msg = f"비교 분석 중 오류 발생: {e}"
        error_tuple = (error_msg,) + (gr.update(visible=False),)*(num_outputs_per_keyword -1)
        return error_tuple * 2
    finally:
        if driver: 
            try: driver.quit()
            except Exception as e_quit: print(f"WebDriver 종료 오류: {e_quit}")

# --- 카테고리 분석 --- #
def analyze_festivals_by_category(cat1, cat2, cat3, num_reviews, log_details, progress=gr.Progress(track_tqdm=True)):
    driver = None
    num_outputs = 48
    category_name = cat3 or cat2 or cat1
    if not category_name:
        return ["오류: 분석할 카테고리를 선택하세요."] + [gr.update(visible=False)]*(num_outputs - 1)
        
    try:
        driver = create_driver()
        results = perform_category_analysis(cat1, cat2, cat3, int(num_reviews), driver, log_details, progress, 0, 1)
        return package_category_results(results, category_name)
    except Exception as e:
        print(f"카테고리 분석 중 예외 발생: {e}")
        traceback.print_exc()
        return [f"카테고리 분석 중 오류 발생: {e}"] + [gr.update(visible=False)]*(num_outputs - 1)
    finally:
        if driver: 
            try: driver.quit()
            except Exception as e_quit: print(f"WebDriver 종료 오류: {e_quit}")

# --- 카테고리 비교 분석 --- #
def compare_categories(cat1_a, cat2_a, cat3_a, cat1_b, cat2_b, cat3_b, num_reviews, log_details, progress=gr.Progress(track_tqdm=True)):
    driver = None
    num_outputs_per_category = 48
    category_name_a = cat3_a or cat2_a or cat1_a
    category_name_b = cat3_b or cat2_b or cat1_b
    if not category_name_a or not category_name_b:
        error_msg = "오류: 비교할 카테고리 A와 B를 모두 선택하세요."
        error_tuple = (error_msg,) + (gr.update(visible=False),)*(num_outputs_per_category - 1)
        return error_tuple * 2

    try:
        driver = create_driver()
        results_a = perform_category_analysis(cat1_a, cat2_a, cat3_a, int(num_reviews), driver, log_details, progress, 0, 2)
        results_b = perform_category_analysis(cat1_b, cat2_b, cat3_b, int(num_reviews), driver, log_details, progress, 1, 2)
        output_a = package_category_results(results_a, category_name_a)
        output_b = package_category_results(results_b, category_name_b)
        return tuple(output_a) + tuple(output_b)
    except Exception as e:
        print(f"카테고리 비교 분석 중 예외 발생: {e}")
        traceback.print_exc()
        error_msg = f"비교 분석 중 오류 발생: {e}"
        error_tuple = (error_msg,) + (gr.update(visible=False),)*(num_outputs_per_category - 1)
        return error_tuple * 2
    finally:
        if driver: 
            try: driver.quit()
            except Exception as e_quit: print(f"WebDriver 종료 오류: {e_quit}")

# --- 자유 그룹 분석 (Helper & Main) --- #
# Helper: 인자를 명시적으로 받도록 수정
def _analyze_single_festival_group(cat1, cat2, cat3, selected_festivals, num_reviews, driver, log_details, progress, initial_progress, total_steps):
    num_outputs = 48
    festivals_to_analyze = []
    group_name = ""

    if selected_festivals:
        festivals_to_analyze = selected_festivals
        group_name = f"사용자 선택 그룹 ({len(festivals_to_analyze)}개)"
    elif cat1:
        festivals_to_analyze = festival_loader.get_festivals(cat1, cat2, cat3)
        group_name = cat3 or cat2 or cat1
    else:
        return ["분석할 그룹이 선택되지 않았습니다."] + [gr.update(visible=False)] * (num_outputs - 1)

    if not festivals_to_analyze:
        return [f"'{group_name}' 그룹에서 분석할 축제를 찾을 수 없습니다."] + [gr.update(visible=False)] * (num_outputs - 1)

    results = perform_festival_group_analysis(festivals_to_analyze, group_name, int(num_reviews), driver, log_details, progress, initial_progress, total_steps)
    return package_category_results(results, group_name)

# Main: UI와 직접 연결되는 함수. *args 대신 모든 인자를 명시적으로 받도록 수정
def run_multi_group_comparison(c1a, c2a, c3a, sfa, c1b, c2b, c3b, sfb, c1c, c2c, c3c, sfc, c1d, c2d, c3d, sfd, num_reviews, log_details, progress=gr.Progress()):
    num_outputs_per_group = 44
    num_groups = 4

    # 각 그룹의 입력을 리스트로 묶음
    all_group_inputs = [
        [c1a, c2a, c3a, sfa],
        [c1b, c2b, c3b, sfb],
        [c1c, c2c, c3c, sfc],
        [c1d, c2d, c3d, sfd],
    ]

    active_groups_count = sum(1 for group in all_group_inputs if group[0] or group[3])

    if active_groups_count == 0:
        error_tuple = ["오류: 분석할 그룹을 하나 이상 선택하세요."] + [gr.update(visible=False)] * (num_outputs_per_group - 1)
        return tuple(error_tuple * num_groups)

    driver = None
    try:
        driver = create_driver()
        all_results = []
        active_group_idx = 0
        for i in range(num_groups):
            cat1, cat2, cat3, selected_festivals = all_group_inputs[i]
            is_active = bool(cat1 or selected_festivals)

            if is_active:
                group_result = _analyze_single_festival_group(
                    cat1, cat2, cat3, selected_festivals, num_reviews,
                    driver, log_details, progress, active_group_idx, active_groups_count
                )
                all_results.extend(group_result)
                active_group_idx += 1
            else:
                all_results.extend([None] + [gr.update(visible=False)] * (num_outputs_per_group - 1))
        
        return tuple(all_results)

    except Exception as e:
        print(f"다중 그룹 비교 분석 중 예외 발생: {e}")
        traceback.print_exc()
        error_msg = f"그룹 비교 분석 중 오류 발생: {e}"
        error_tuple = (error_msg,) + (gr.update(visible=False),) * (num_outputs_per_group - 1)
        return tuple(error_tuple * num_groups)
    finally:
        if driver:
            try: driver.quit()
            except Exception as e_quit: print(f"WebDriver 종료 오류: {e_quit}")

def get_trend_graph_for_festival(festival_name: str):
    if not festival_name:
        return None

    try:
        # create_trend_graph는 (그래프 경로, 데이터프레임) 튜플을 반환하므로, 경로만 사용합니다.
        graph_path, _ = create_trend_graph(festival_name)
        return graph_path
    except Exception as e:
        print(f"트렌드 그래프 생성 중 오류 ({festival_name}): {e}")
        traceback.print_exc()
        return None

def get_focused_trend_graph_for_festival(festival_name: str):
    if not festival_name:
        return None

    try:
        # TourAPI에서 축제 기간 가져오기 (없어도 최근 60일 트렌드 생성)
        start_date_str, end_date_str = get_festival_period(festival_name)

        if not start_date_str or not end_date_str:
            print(f"⚠️ '{festival_name}' 축제 기간 정보 없음 - 최근 60일 트렌드 생성")

        # create_focused_trend_graph는 (그래프 경로, 데이터프레임) 튜플을 반환하므로, 경로만 사용합니다.
        # 축제 기간이 없어도 함수가 알아서 최근 60일 트렌드를 생성합니다.
        graph_path, _ = create_focused_trend_graph(festival_name, start_date_str, end_date_str)
        return graph_path
    except Exception as e:
        print(f"❌ 집중 트렌드 그래프 생성 중 오류 ({festival_name}): {e}")
        traceback.print_exc()
        return None
