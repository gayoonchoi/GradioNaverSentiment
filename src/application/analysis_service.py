# src/application/analysis_service.py
import gradio as gr
import traceback
# 분리된 모듈 임포트
from .analysis_logic import analyze_single_keyword_fully, perform_category_analysis
from .result_packager import package_keyword_results, package_category_results, package_festival_details
from .utils import create_driver, summarize_negative_feedback
from ..infrastructure.web.naver_trend_api import create_trend_graph

# --- Public Service Functions for Gradio ---

def analyze_keyword_and_generate_report(keyword: str, num_reviews: int, log_details: bool, progress=gr.Progress(track_tqdm=True)):
    driver = None
    num_outputs = 20 # create_keyword_analysis_outputs 반환 개수
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


def run_comparison_analysis(keyword_a: str, keyword_b: str, num_reviews: int, log_details: bool, progress=gr.Progress(track_tqdm=True)):
    driver = None
    num_outputs_per_keyword = 20
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


def analyze_festivals_by_category(cat1, cat2, cat3, num_reviews, log_details, progress=gr.Progress(track_tqdm=True)):
    driver = None
    num_outputs = 34 # create_category_analysis_outputs 반환 개수
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


def compare_categories(cat1_a, cat2_a, cat3_a, cat1_b, cat2_b, cat3_b, num_reviews, log_details, progress=gr.Progress(track_tqdm=True)):
    driver = None
    num_outputs_per_category = 34
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
        error_msg = f"카테고리 비교 분석 중 오류 발생: {e}"
        error_tuple = (error_msg,) + (gr.update(visible=False),)*(num_outputs_per_category - 1)
        return error_tuple * 2
    finally:
        if driver: 
            try: driver.quit()
            except Exception as e_quit: print(f"WebDriver 종료 오류: {e_quit}")


def run_selected_festivals_comparison(
    festival_1, festival_2, festival_3, festival_4, 
    num_reviews, log_details, progress=gr.Progress(track_tqdm=True)
):
    driver = None
    num_outputs_per_festival = 21 
    
    selected_festivals = [f for f in [festival_1, festival_2, festival_3, festival_4] if f] 
    
    if not selected_festivals:
        error_msg = "오류: 비교할 축제를 하나 이상 선택하세요."
        error_tuple = (error_msg,) + (gr.update(visible=False),) * (num_outputs_per_festival - 1)
        # 모든 슬롯에 오류 메시지 + 숨김 반환
        return error_tuple * 4

    all_results_packaged = []
    
    try:
        driver = create_driver()
        total_selected = len(selected_festivals)
        
        for i, festival_name in enumerate(selected_festivals):
            def selected_progress_callback(p, desc=""):
                base_progress = i / total_selected
                step_progress = p / total_selected
                current_progress = base_progress + step_progress
                progress(min(current_progress, 1.0), desc=f"분석 중: {festival_name} ({i+1}/{total_selected}) - {desc}")
            
            print(f"--- 선택 축제 분석 시작: {festival_name} ---")
            result = analyze_single_keyword_fully(festival_name, int(num_reviews), driver, log_details, selected_progress_callback, f"선택({i+1})")
            
            # 오류 발생 시 해당 슬롯은 오류 처리
            if "error" in result:
                 print(f"--- 선택 축제 분석 오류: {festival_name} - {result['error']} ---")
                 error_package = (f"오류: {result['error']}",) + (gr.update(visible=False),) * (num_outputs_per_festival - 1)
                 all_results_packaged.append(error_package)
                 continue # 다음 축제로

            # 개별 분석 결과 패키징 (미리 요약 포함)
            if "negative_sentences" in result:
                 result['precomputed_negative_summary'] = summarize_negative_feedback(result["negative_sentences"])
            else:
                 result['precomputed_negative_summary'] = "부정 문장 없음" # 요약할 내용 없을 경우 대비
                 
            packaged_result = package_keyword_results(result, festival_name)
            all_results_packaged.append(packaged_result)
            print(f"--- 선택 축제 분석 완료: {festival_name} ---")

        # 남은 슬롯 채우기
        num_remaining_slots = 4 - len(all_results_packaged) # 오류 포함해서 계산
        if num_remaining_slots > 0:
            empty_package = ("",) + (gr.update(visible=False),) * (num_outputs_per_festival - 1)
            for _ in range(num_remaining_slots):
                all_results_packaged.append(empty_package)

        final_output_tuple = ()
        for package in all_results_packaged:
            final_output_tuple += package
            
        return final_output_tuple

    except Exception as e:
        print(f"선택 축제 비교 분석 중 예외 발생: {e}")
        traceback.print_exc()
        error_msg = f"선택 축제 비교 분석 중 오류 발생: {e}"
        error_output = (error_msg,) + (gr.update(visible=False),) * (num_outputs_per_festival - 1)
        return tuple(error_output * 4) 
    finally:
        if driver: 
             try:
                 driver.quit()
             except Exception as e_quit: 
                 print(f"WebDriver 종료 중 오류: {e_quit}")

# change_page 함수는 UI 레이어(event_handlers.py)에서도 직접 사용하므로,
# utils.py로 옮긴 후에도 여기서 다시 임포트하거나,
# UI 레이어에서 직접 utils.py를 임포트하도록 변경해야 합니다.
# 여기서는 후자를 가정하고 analysis_service.py에서는 제거합니다.
# from .utils import change_page 
# -> gradio_ui.py 또는 event_handlers.py에서 from src.application.utils import change_page 로 임포트 필요

# package_festival_details 함수도 UI 레이어(event_handlers.py)에서 직접 사용합니다.
# result_packager.py로 옮긴 후에도 여기서 다시 임포트하거나,
# UI 레이어에서 직접 result_packager.py를 임포트하도록 변경해야 합니다.
# 여기서는 후자를 가정하고 analysis_service.py에서는 제거합니다.
# from .result_packager import package_festival_details
# -> gradio_ui.py 또는 event_handlers.py에서 from src.application.result_packager import package_festival_details 로 임포트 필요

def get_trend_graph_for_festival(festival_name: str):
    """축제 이름으로 트렌드 그래프를 생성합니다."""
    if not festival_name:
        return gr.update(visible=False)
    
    try:
        # 여기서는 축제 기간 정보 없이 호출합니다.
        # 필요하다면, festival_loader 등을 통해 축제 기간을 조회하는 로직을 추가할 수 있습니다.
        graph = create_trend_graph(festival_name)
        return gr.update(value=graph, visible=graph is not None)
    except Exception as e:
        print(f"트렌드 그래프 생성 중 오류 ({festival_name}): {e}")
        traceback.print_exc()
        return gr.update(visible=False)