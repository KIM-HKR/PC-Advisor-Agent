# 💻 PC 조립 어드바이저 AI 에이전트 (PC Assembly Advisor)
> **LM Studio 로컬 LLM** 과 **RAG(검색 증강 생성)** 를 결합하여 사용자 맞춤형 PC 견적을 제안하고 호환성을 자동 검증하는 지능형 어드바이저 에이전트입니다.

## 📅 프로젝트 개요
- **개발자:** 김학경 
- **주요 기술:** Python, Streamlit, LM Studio (Local LLM), Tavily Search API (RAG)

## ✨ 핵심 기능
1. **실시간 부품 시세 반영 (RAG):** Tavily API를 통해 다나와, 컴퓨존 등 주요 쇼핑몰의 최신 가격 데이터를 실시간으로 수집합니다. (2025~2026년 최신 부품인 RTX 50 시리즈 포함)
2. **지능형 호환성 검증 (Python Executor):** LLM이 직접 파이썬 코드를 실행하여 CPU 소켓 일치 여부와 파워 서플라이 권장 용량을 수학적으로 검증합니다.
3. **컨텍스트 엔지니어링:** 사용자의 예산, 용도, 선호 브랜드를 기억하고 대화 문맥에 맞는 최적의 대안을 제시합니다.
4. **로컬 환경 구동:** LM Studio를 통해 로컬 환경에서 LLM을 구동함으로써 개인정보를 보호하고 모델 제어권을 확보했습니다.
 <img width="400"  alt="Image" src="https://github.com/user-attachments/assets/c34f269b-3cb6-4fa9-b7e4-4d9dc49dd9ad" /> <img width="400" alt="Image" src="https://github.com/user-attachments/assets/a3810f3e-0bb3-41f5-b5eb-138fc6d0a06c" /> <img width="400"  alt="Image" src="https://github.com/user-attachments/assets/c6c66e84-bc1b-478f-853a-b68b3f92911e" />

## 🛠 기술 스택
- **언어:** Python 3.10+
- **프레임워크:** Streamlit
- **LLM 서버:** LM Studio (OpenAI API Compatible)
- **외부 API:** Tavily Search API (Search Tool)

## 🚀 실행 방법
1. **LM Studio 설정:**
   - 함수 호출(Tool Calling)이 가능한 모델을 로드하고 로컬 서버를 시작합니다. (Port: 1234)
2. **환경 변수 설정:**
   - `Tavily API Key`를 준비합니다.
3. **라이브러리 설치:**
   ```bash
   pip install streamlit openai tavily-python
4. **프로그램 실행:**
   ```bash
   streamlit run app.py
## 🛠 데모 영상
```bash
https://youtu.be/8f0aa7P5eYg 
