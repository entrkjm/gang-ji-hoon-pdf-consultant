import streamlit as st
import os
import tempfile
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from dotenv import load_dotenv
import glob
import json
from google.oauth2 import service_account

# 로컬 개발 환경용 (.env 로드)
load_dotenv()

# Streamlit 페이지 설정
st.set_page_config(page_title="AI 생기부 컨설턴트 (Vertex AI)")

# --- GCP 설정 ---
credentials = None
PROJECT_ID = "vaiv-observatory"
LOCATION = "us-central1"

# 1. 인증 시도 (우선순위: Streamlit Secrets -> 로컬 JSON 파일)
if "gcp_service_account" in st.secrets:
    try:
        # Streamlit Cloud 배포용 (Secrets에서 로드)
        service_account_info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
        PROJECT_ID = service_account_info.get("project_id", PROJECT_ID)
    except Exception as e:
        st.error(f"Secrets 인증 오류: {e}")

else:
    # 로컬 개발용 (파일에서 로드)
    key_path = "pdf-to-suggestion/keys/project-ai-proc.gcpkey.json"
    alt_key_path = "keys/project-ai-proc.gcpkey.json"
    
    target_key_path = None
    if os.path.exists(key_path):
        target_key_path = key_path
    elif os.path.exists(alt_key_path):
        target_key_path = alt_key_path
        
    if target_key_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = target_key_path
        # vertexai.init이 환경변수를 자동으로 잡지만, 명시적으로 로드 가능
        # credentials = service_account.Credentials.from_service_account_file(target_key_path) 
    elif not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        st.warning("GCP 서비스 계정 키를 찾을 수 없습니다. (로컬: keys 폴더 / 배포: Secrets 설정 필요)")

# Vertex AI 초기화
try:
    if credentials:
        vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
    else:
        # 환경변수(GOOGLE_APPLICATION_CREDENTIALS) 기반 초기화
        vertexai.init(project=PROJECT_ID, location=LOCATION)
except Exception as e:
    st.error(f"Vertex AI 초기화 실패: {e}. GCP 프로젝트 ID 및 키 설정을 확인하세요.")

# 모델 설정 (Gemini 2.0 Flash)
MODEL_NAME = "gemini-2.0-flash-001"

def analyze_record(file_path, target_major):
    """Vertex AI Gemini에게 생기부 분석 요청"""
    
    # 1. 모델 로드
    model = GenerativeModel(MODEL_NAME)
    
    # 2. 파일 데이터 읽기 (로컬 파일을 Bytes로 변환하여 Part 객체 생성)
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    # PDF는 'application/pdf' MIME 타입 사용
    pdf_part = Part.from_data(data=file_content, mime_type="application/pdf")

    # 3. 프롬프트 구성
    prompt = f"""
    당신은 대한민국 최고의 대입 입학사정관이자 진로 컨설턴트입니다.
    제공된 고등학교 생활기록부(PDF)를 정밀 분석하여 학생의 입시 전략을 수립해야 합니다.
    
    학생의 희망 진로: {target_major}
    
    다음 지침을 엄수하여 분석 결과를 작성하세요:
    1. **이모지 사용 금지**: 모든 텍스트에 이모지를 사용하지 마십시오.
    2. **가독성 강화**: 핵심 키워드나 중요한 수치, 등급 등은 굵게(** **) 표시하여 가독성을 높이십시오.
    3. **마크다운 준수**: 마크다운 문법이 깨지지 않도록 주의하십시오.

    ---
    
    ## 1. 학년별 핵심 활동 요약
    각 학년별로 학생의 역량이 돋보이는 활동(교과 세특, 동아리, 진로활동 등)을 핵심만 3~4줄로 요약하십시오.
    
    * **1학년**: 
    * **2학년**: 
    * **3학년**: (내용이 없으면 '자료 없음' 표시)

    ## 2. 전공 적합성 및 역량 평가
    * **종합 평가**: (S/A/B/C 등급으로 매기고 이유를 서술)
    * **강점**: 희망 진로와 관련하여 돋보이는 역량
    * **약점 및 보완점**: 현재 생기부에서 부족해 보이거나 아쉬운 점

    ## 3. 합격을 부르는 심화 활동 제안
    희망 진로인 '{target_major}' 합격 확률을 높이기 위해, 다음 학기나 남은 기간 동안 반드시 해야 할 **구체적인 활동 3가지**를 제안하십시오.
    단순한 추천이 아니라, 구체적인 **탐구 주제(논문 제목 예시)**, **심화 서적**, **수행평가 연계 아이디어**를 포함해야 합니다.
    
    1. **[주제 1]**: ...
    2. **[주제 2]**: ...
    3. **[주제 3]**: ...
    """

    # 4. 콘텐츠 생성 요청
    # Vertex AI는 system_instruction을 init할 때 넣거나, 프롬프트 앞에 붙여도 됨.
    # 여기선 멀티모달(Part + Text)로 리스트에 담아 보냄.
    responses = model.generate_content(
        [pdf_part, prompt],
        generation_config={
            "max_output_tokens": 4096,
            "temperature": 0.4,
            "top_p": 0.9,
        },
        stream=True,
    )
    
    final_text = ""
    # 스트리밍 응답 처리 (UI 경험 향상)
    result_container = st.empty()
    for response in responses:
        text = response.text
        final_text += text
        result_container.markdown(final_text)
        
    return final_text

# --- UI 구성 ---
st.title("AI 생기부 컨설턴트 (Vertex AI)")
st.caption(f"Powered by Google Cloud Vertex AI ({MODEL_NAME})")

with st.sidebar:
    st.header("설정 및 입력")
    # 프로젝트 ID가 환경변수에 없으면 입력받기
    if not PROJECT_ID:
        st.warning("환경변수 GCP_PROJECT_ID가 없습니다.")
        user_project_id = st.text_input("GCP Project ID 입력")
        if user_project_id:
            PROJECT_ID = user_project_id
            try:
                vertexai.init(project=PROJECT_ID, location=LOCATION)
                st.success("재설정 완료")
            except:
                pass
    
    target_major = st.text_input("희망 학과/진로", placeholder="예: 컴퓨터공학과, 의예과")
    uploaded_file = st.file_uploader("생기부 PDF 업로드", type=["pdf"])
    st.info("개인정보 보호를 위해 파일은 분석 후 즉시 삭제됩니다.")

if uploaded_file and target_major:
    st.divider()
    if st.button("분석 시작하기", type="primary"):
        # 검증
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and not st.secrets.get("GOOGLE_APPLICATION_CREDENTIALS"):
             st.error("GCP 인증 키가 없습니다. 'keys/' 폴더에 JSON 키를 넣어주세요.")
             st.stop()

        with st.spinner("AI가 생기부를 분석 중입니다... (Vertex AI)"):
            try:
                # 임시 파일 저장
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # 분석 실행 (스트리밍으로 출력됨)
                analyze_record(tmp_file_path, target_major)
                
                # 정리
                os.remove(tmp_file_path)
                
            except Exception as e:
                st.error(f"오류 발생: {e}")
