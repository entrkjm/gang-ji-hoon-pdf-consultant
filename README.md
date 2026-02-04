# 🎓 AI 생기부 컨설턴트 (Student Record AI Consultant)

고등학생의 생활기록부(PDF)를 업로드하면, **Google Gemini 2.0 Flash (Vertex AI)**를 활용하여 입학사정관 관점에서 학년별 활동을 요약하고, 희망 진로에 맞춘 심화 활동을 제안해주는 웹 애플리케이션입니다.

## 📁 프로젝트 구조

```bash
.
├── .gitignore                  # 보안을 위한 Git 무시 설정 (keys 폴더, .env 등 제외)
├── README.md                   # 프로젝트 설명서
└── pdf-to-suggestion/          # 메인 프로젝트 폴더
    ├── app.py                  # [핵심] Streamlit 웹앱 및 AI 로직 구현
    ├── requirements.txt        # 파이썬 의존성 패키지 목록
    ├── TODO.md                 # 향후 개선 계획 (API Key 전환 등)
    ├── SECRETS_COPY_ME.toml    # Streamlit Cloud 배포 시 Secrets 설정용 템플릿
    ├── examples/               # 테스트용 생기부 PDF 예시
    └── keys/                   # (Git 제외) 로컬 개발용 GCP 서비스 계정 키 폴더
```

## 🛠 기술 스택

- **Frontend/Backend**: [Streamlit](https://streamlit.io/) (Python 기반 웹 프레임워크)
- **AI Model**: Google Cloud Vertex AI - **Gemini 2.0 Flash** (멀티모달 PDF 처리)
- **Deployment**: Streamlit Cloud
- **Language**: Python 3.13

## 🚀 로컬 개발 환경 설정 (Local Setup)

1. **프로젝트 클론 및 이동**
   ```bash
   git clone https://github.com/entrkjm/gang-ji-hoon-pdf-consultant.git
   cd gang-ji-hoon-pdf-consultant/pdf-to-suggestion
   ```

2. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **GCP 인증 키 설정**
   - Google Cloud Console에서 서비스 계정 키(JSON)를 다운로드합니다.
   - `pdf-to-suggestion/keys/` 폴더를 만들고 JSON 파일을 넣습니다. (파일명 무관, `.gitignore` 처리됨)

4. **앱 실행**
   ```bash
   streamlit run app.py
   ```

## ☁️ 배포 가이드 (Streamlit Cloud)

1. **GitHub 연결**: Streamlit Cloud에서 이 리포지토리를 연결합니다.
2. **실행 경로 설정**: `Main file path`를 `pdf-to-suggestion/app.py`로 설정합니다.
3. **Secrets 설정 (가장 중요)**:
   - 로컬의 JSON 키 파일 내용은 보안상 GitHub에 올라가지 않습니다.
   - `pdf-to-suggestion/SECRETS_COPY_ME.toml` 파일의 내용을 참고하여, Streamlit 대시보드의 **Settings > Secrets**에 복사해 넣으세요.
   - `private_key`의 줄바꿈(`\n`) 처리가 자동으로 되도록 코드가 작성되어 있으므로, TOML 형식만 맞추면 됩니다.

## 💡 핵심 기능 및 로직

### 1. PDF 멀티모달 처리
별도의 OCR이나 텍스트 추출 라이브러리 없이, PDF 바이너리를 그대로 **Gemini 2.0 Flash**에게 전달하여 구조(표, 단락)를 인식하고 해석합니다.

### 2. 이중 인증 구조 (`app.py`)
- **로컬**: `keys/*.json` 파일을 자동으로 찾아 `GOOGLE_APPLICATION_CREDENTIALS` 환경변수로 설정.
- **배포**: Streamlit Secrets(`st.secrets["gcp_service_account"]`)를 감지하면 자동으로 딕셔너리를 구성하여 인증 객체 생성.

### 3. 프롬프트 엔지니어링
- **페르소나**: 대한민국 입학사정관.
- **분석 기준**: 학년별 '세특(세부능력 및 특기사항)'과 '창체(창의적 체험활동)' 위주 분석.
- **출력 제어**: 이모지 사용 금지, 가독성을 위한 마크다운 볼드 처리, 구체적인 활동(논문 주제 등) 3가지 필수 제안.

## 📝 TODO
- [ ] 현재 GCP 프로젝트 인증 방식에서 Gemini API Key 방식(AI Studio)으로 전환하여 설정 간소화 예정.
