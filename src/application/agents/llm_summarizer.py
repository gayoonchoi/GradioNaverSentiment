from src.domain.state import LLMGraphState
from src.domain.knowledge_base import knowledge_base
from src.infrastructure.llm_client import get_llm_client

def agent_llm_summarizer(state: LLMGraphState):
    if state["log_details"]:
        print("\n--- [Agent 1: Real LLM Summarizer] 핵심 경험 요약 시작 ---")

    text = state["original_text"]
    keyword = state["keyword"]
    feedback_message = state.get("feedback_message")
    re_summarize_count = state.get("re_summarize_count", 0)

    llm = get_llm_client()

    system_prompt = "당신은 블로그 리뷰의 핵심 요약 전문가입니다."
    user_prompt = f"""아래는 '{keyword}'에 대한 블로그 리뷰 본문입니다.\n\n본문 전체를 읽고, 글쓴이가 '{keyword}'와 관련하여 경험한 내용 전체에 대한 '긍정적인 점'과 '부정적인 점'을 각각 글머리 기호(bullet points) 형식으로 요약해주세요.\n\n[매우 중요] 요약 시, 감성 표현(명사, 형용사, 부사, 관용어)과 그 감성을 수식하는 표현(강조어, 완화어, 부정어)을 모두 ****로 감싸주세요. 만약 수식 관계가 명확하다면, 수식어 뒤에 (수식어구: [수식받는 감성 표현]) 형식으로 괄호를 추가해주세요.\n예시: \"이 축제는 ****정말****(수식어구: 환상적) ****환상적****이었어요.\" 또는 \"음식이 ****너무****(수식어구: 별로) ****별로****였어요.\" 그리고 \"불꽃놀이는 ****황홀****했어요.\"\n- ****는 감성 강도에 명확하게 영향을 미치는 표현에만 사용해야 합니다.\n- 감성 강도에 영향을 미치지 않는 일반적인 단어에는 ****를 사용하지 마세요.\n\n[참고] 감성 표현 사전 예시:\n- 관용어: {list(knowledge_base.idioms.keys())[:5]}...\n- 강조어: {list(knowledge_base.amplifiers.keys())[:5]}...\n- 완화어: {list(knowledge_base.downtoners.keys())[:5]}...\n- 부정어: {knowledge_base.negators[:5]}...\n- 감성 형용사: {list(knowledge_base.adjectives.keys())[:5]}...\n- 감성 부사: {list(knowledge_base.adverbs.keys())[:5]}...\n- 감성 명사: {list(knowledge_base.sentiment_nouns.keys())[:5]}...\n\n(예: 원문이 '정말 맛있다'이면, 요약도 '정말 맛있다'여야 합니다. '맛있다'로 줄이면 안 됩니다.)\n\n다른 부가적인 설명 없이, 아래의 정확한 형식에 맞춰 요약만 제공해주세요.\n\n- 긍정적인 점:\n  - (여기에 긍정적인 경험 요약)\n- 부정적인 점:\n  - (여기에 부정적인 경험 요약)\n\n--- 블로그 본문 시작 ---\n{text}\n--- 블로그 본문 끝 ---""
    if feedback_message and re_summarize_count < 3:  # 최대 3회 재요약 시도
        user_prompt = f"{user_prompt}\n\n[이전 요약에 대한 피드백]\n{feedback_message}\n\n위 피드백을 바탕으로 요약을 다시 생성해주세요. 특히 감성 표현의 마킹과 수식어구 연결에 주의하여 감성 점수와 일관되도록 해주세요."
        if state["log_details"]:
            print(
                f"   [LLM 재요청] 피드백 반영하여 요약 재시도 (시도 횟수: {re_summarize_count + 1})"
            )
    elif re_summarize_count >= 3:
        if state["log_details"]:
            print("   [LLM 재요청 실패] 최대 재요약 횟수 초과. 원본 요약 반환.")
        return {"llm_summary": state["llm_summary"], "feedback_message": None}

    try:
        response = llm.invoke(user_prompt)
        summary = response.content.strip()

    except Exception as e:
        print(f"LLM 요약 중 오류 발생: {e}")
        summary = ""

    if state["log_details"]:
        print("--- LLM 핵심 경험 요약 결과 ---")
        print(summary if summary else "[요약할 내용이 없습니다]")
        print("---------------------------")

    return {"llm_summary": summary, "feedback_message": None}
