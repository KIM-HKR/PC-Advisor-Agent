import streamlit as st
import json
import os
from openai import OpenAI
from tavily import TavilyClient

# ==========================================
# 1. Streamlit 페이지 및 환경 설정
# ==========================================
st.set_page_config(page_title="AI PC 조립 어드바이저", page_icon="💻", layout="wide")

st.title("💻 AI PC 조립 어드바이저 (Local LLM + RAG)")
st.caption("LM Studio와 Tavily Search를 활용한 지능형 PC 견적 에이전트입니다.")

# 사이드바 설정 영역
with st.sidebar:
    st.header("⚙️ 환경 설정")
    lm_studio_url = st.text_input("LM Studio Base URL", value="http://localhost:1234/v1")
    tavily_api_key = st.text_input("Tavily API Key (RAG 검색용)", type="password", placeholder="tvly-...")
    
    # 들여쓰기가 수정된 API 키 확인 UI
    if tavily_api_key:
        st.success("✅ API 키가 입력되었습니다! (실시간 검색 활성화)")
    else:
        st.info("ℹ️ API 키를 넣지 않으면 가상 데이터로 테스트합니다.")
        
    st.markdown("---")
    st.markdown("""
    **💡 대화 예시:**
    - "150만원대 게이밍 PC 견적 짜줘"
    - "RTX 5070과 9700X를 이용해서 250만원 내의 PC를 만들어줘"
    """)

# OpenAI 클라이언트 초기화 (LM Studio 로컬 서버 연결)
client = OpenAI(base_url=lm_studio_url, api_key="lm-studio")

# ==========================================
# 2. 에이전트 도구(Tools) 정의
# ==========================================
def search_latest_pc_parts(query):
    """주어진 예산과 목적에 맞는 최신 PC 부품 정보와 가격을 검색합니다."""
    if tavily_api_key:
        try:
            tavily_client = TavilyClient(api_key=tavily_api_key)
            # 심층 검색을 통해 최신 기사, 다나와, 컴퓨존 등의 정보를 가져옴
            response = tavily_client.search(query=query, search_depth="advanced", max_results=3)
            results = [res['content'] for res in response['results']]
            return "\n".join(results)
        except Exception as e:
            return f"검색 오류: {e}"
    else:
        # API 키가 없을 때의 시뮬레이션 데이터 (5070 업데이트 완료)
        return """
        [검색 결과 시뮬레이션 - API 키 미입력 상태]
        - CPU: AMD Ryzen 7 9700X (AM5 소켓, TDP 65W) - 약 450,000원
        - GPU: NVIDIA RTX 5070 (TGP 250W) - 약 950,000원 
        - 메인보드: B650M (AM5 소켓) - 약 180,000원
        - 파워서플라이: 750W 80Plus Gold - 약 120,000원
        """

def check_compatibility(cpu_socket, mb_socket, total_tdp, psu_wattage):
    """CPU와 메인보드의 소켓 일치 여부 및 파워 용량을 검증합니다."""
    is_socket_match = (cpu_socket.lower().strip() == mb_socket.lower().strip())
    required_power = total_tdp * 1.3  # 30% 마진 적용
    is_power_enough = (psu_wattage >= required_power)
    
    result = {
        "socket_match": is_socket_match,
        "power_enough": is_power_enough,
        "required_power_with_margin": required_power,
        "status": "Pass" if (is_socket_match and is_power_enough) else "Fail",
        "details": ""
    }
    
    if not is_socket_match:
        result["details"] += f"소켓 불일치 (CPU: {cpu_socket} vs MB: {mb_socket}). "
    if not is_power_enough:
        result["details"] += f"파워 부족 (필요: {int(required_power)}W 이상, 선택: {psu_wattage}W). "
        
    return json.dumps(result, ensure_ascii=False)

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_latest_pc_parts",
            "description": "최신 컴퓨터 부품 가격 및 추천 리스트를 인터넷에서 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색어 (예: 'RTX 5070 최신 가격 및 성능')"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_compatibility",
            "description": "선택한 부품들 간의 조립 호환성(소켓, 전력)을 확인합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cpu_socket": {"type": "string", "description": "CPU 소켓 이름 (예: AM5, LGA1700)"},
                    "mb_socket": {"type": "string", "description": "메인보드 소켓 이름 (예: AM5, LGA1700)"},
                    "total_tdp": {"type": "number", "description": "시스템 전체 예상 소비 전력(W)"},
                    "psu_wattage": {"type": "number", "description": "선택한 파워서플라이 용량(W)"}
                },
                "required": ["cpu_socket", "mb_socket", "total_tdp", "psu_wattage"],
            },
        },
    }
]

# ==========================================
# 3. Streamlit 세션 상태(대화 기록) 및 시스템 프롬프트 관리
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": """
        당신은 15년 경력의 전문 PC 조립 어드바이저입니다.
        
        [🚨시간 및 지식 동기화 (매우 중요)🚨]
        현재 연도는 2026년이며, 엔비디아 지포스 RTX 50 시리즈(5070, 5080, 5090 등)는 이미 2025년에 공식 출시되어 시장에서 널리 판매 중인 정식 부품입니다. 당신의 과거 학습 데이터에 미출시로 되어 있더라도 그 기억은 완전히 무시하세요.

        [동작 지침]
        1. 사용자가 RTX 5070 등을 요청하면, 절대 "출시 전이다" 혹은 "구형 4070 등으로 대체하겠다"라고 말하지 마세요.
        2. 반드시 search_latest_pc_parts 도구를 사용해 현재 시장에 판매 중인 최신 부품의 실제 가격과 공식 스펙을 검색하여 수집하세요.
        3. 수집된 실제 검색 결과와 스펙을 바탕으로 check_compatibility 도구를 실행해 호환성을 검증한 뒤, 최종 견적을 제공하세요.
        4. Markdown을 활용해 표와 리스트로 깔끔하게 답변하세요.
        """}
    ]

# 이전 대화 내용 출력 (시스템 프롬프트 제외)
for msg in st.session_state.messages:
    if msg["role"] not in ["system", "tool"]:
        # 도구 호출용 빈 메시지 방지
        if msg["role"] == "assistant" and not msg.get("content"):
            continue
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ==========================================
# 4. 사용자 입력 및 에이전트 구동 로직
# ==========================================
if user_prompt := st.chat_input("예산과 목적을 입력해주세요. (예: RTX 5070 포함 200만원대 PC)"):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.status("로컬 LLM이 생각 중입니다...", expanded=True) as status:
            current_messages = st.session_state.messages.copy()
            
            # 에이전트 도구 호출 루프 (최대 5번)
            for turn in range(5):
                try:
                    response = client.chat.completions.create(
                        model="local-model",
                        messages=current_messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=0.3
                    )
                    
                    response_message = response.choices[0].message
                    current_messages.append(response_message)
                    
                    if response_message.tool_calls:
                        for tool_call in response_message.tool_calls:
                            func_name = tool_call.function.name
                            
                            # 빈 arguments가 넘어올 경우를 대비한 안전 장치
                            try:
                                func_args = json.loads(tool_call.function.arguments)
                            except json.JSONDecodeError:
                                func_args = {}
                            
                            if func_name == "search_latest_pc_parts":
                                query = func_args.get("query", "최신 PC 부품 검색")
                                st.write(f"🔍 **Tavily 인터넷 검색 중...** (`{query}`)")
                                result = search_latest_pc_parts(query)
                                
                            elif func_name == "check_compatibility":
                                st.write(f"⚙️ **호환성 검증 중...** (CPU: {func_args.get('cpu_socket', '확인불가')} / 파워: {func_args.get('psu_wattage', 0)}W)")
                                result = check_compatibility(
                                    cpu_socket=func_args.get("cpu_socket", ""),
                                    mb_socket=func_args.get("mb_socket", ""),
                                    total_tdp=func_args.get("total_tdp", 0),
                                    psu_wattage=func_args.get("psu_wattage", 0)
                                )
                                res_dict = json.loads(result)
                                if res_dict["status"] == "Pass":
                                    st.write("✅ **호환성 검증 통과!**")
                                else:
                                    st.write(f"❌ **호환성 문제 발생:** {res_dict['details']}")

                            else:
                                result = "알 수 없는 도구입니다."
                                
                            current_messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": func_name,
                                "content": result
                            })
                    else:
                        status.update(label="에이전트가 견적을 완성했습니다!", state="complete", expanded=False)
                        break
                except Exception as e:
                    status.update(label="오류가 발생했습니다.", state="error")
                    st.error(f"실행 중 오류: {e}")
                    break
        
        # 최종 답변 화면 출력 및 세션 저장
        if response_message.content:
            final_answer = response_message.content
            st.markdown(final_answer)
            st.session_state.messages.append({"role": "assistant", "content": final_answer})