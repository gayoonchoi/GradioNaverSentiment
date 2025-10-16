import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def parse_component_text(element):
    text = element.get_text(strip=True)
    if not text:
        return []
    # 구분선이나 해시태그만 있는 경우 제외
    if all(c in '.-_~*# ' for c in text):
        return []
    if text.startswith("#"):
        return []
    sentences = re.split(r'(?<=[.?!~…])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def scrape_blog_content(driver, url: str) -> str:
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "mainFrame"))
        )
        try:
            # 최신 스마트에디터 ONE 기준
            content_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.se-main-container")
                )
            )
        except TimeoutException:
            # 구형 에디터 기준
            content_element = driver.find_element(By.CSS_SELECTOR, "div#postViewArea")

        html_content = content_element.get_attribute("innerHTML")
        soup = BeautifulSoup(html_content, "html.parser")

        # 스마트에디터 ONE 컴포넌트 기반 파싱
        parsed_sentences = []
        components = soup.find_all("div", class_="se-component", recursive=False)
        if not components: # 구형 에디터 또는 다른 구조일 경우 대비
            components = soup.select("div.se-component") # 더 넓은 범위로 탐색

        for component in components:
            if "se-text" in component.get("class", []):
                parsed_sentences.extend(parse_component_text(component))
            elif "se-image" in component.get("class", []):
                caption = component.select_one(".se-caption")
                if caption:
                    parsed_sentences.extend(parse_component_text(caption))
            elif "se-list" in component.get("class", []):
                list_items = component.select("li")
                for li in list_items:
                    parsed_sentences.extend(parse_component_text(li))
            elif "se-quote" in component.get("class", []):
                parsed_sentences.extend(parse_component_text(component))
            # 추가적인 se-component 타입들 (지도, 링크, 테이블 등) 파싱
            elif "se-map" in component.get("class", []):
                map_title = component.select_one(".se-map-title")
                if map_title:
                    parsed_sentences.extend(parse_component_text(map_title))
            elif "se-oglink" in component.get("class", []):
                link_title = component.select_one(".se-oglink-title")
                if link_title:
                    parsed_sentences.extend(parse_component_text(link_title))
            elif "se-table" in component.get("class", []):
                cells = component.select("td, th")
                for cell in cells:
                    parsed_sentences.extend(parse_component_text(cell))

        # 인사말, 마무리말 등 필터링
        final_sentences = []
        greeting_pattern = re.compile(r"^(안녕하세요|여러분|구독자님)")
        closing_pattern = re.compile(r"(감사합니다|구동과|좋아요|알림 설정)") # '구독과' 오타 수정
        for i, sentence in enumerate(parsed_sentences):
            sentence = re.sub(r'\s+', ' ', sentence).strip()
            sentence = sentence.replace("\u200b", "") # 제로폭 공백 제거
            if i < 2 and greeting_pattern.search(sentence):
                continue
            if i > len(parsed_sentences) - 3 and closing_pattern.search(sentence):
                continue
            if sentence:
                final_sentences.append(sentence)

        # 파싱된 문장이 없으면, 원본 텍스트라도 반환
        if not final_sentences:
            return content_element.text

        return "\n".join(final_sentences)

    except TimeoutException:
        return "오류: mainFrame을 찾거나 컨텐츠를 로드하는 데 시간이 너무 오래 걸립니다."
    except Exception as e:
        return f"크롤링 중 오류: {e}"
    finally:
        # 컨텍스트를 mainFrame에서 원래대로 되돌림
        driver.switch_to.default_content()
