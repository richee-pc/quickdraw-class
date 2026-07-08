# 파이썬 기반 커스텀 퀵 드로우 — 고등학생 6시간 수업 자료

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/richee-pc/quickdraw-class/blob/main/%EC%BB%A4%EC%8A%A4%ED%85%80_%ED%80%B5%EB%93%9C%EB%A1%9C%EC%9A%B0.ipynb)

그림을 알아맞히는 AI를 학생들이 직접 만들고, **펜마우스로 그려서** 자기 AI와 게임하는 6시간 수업 패키지입니다. **미드저니(생성형 AI)** 로 게임 아트를 만들고, **퀵 드로우(분류 AI)** 로 게임의 두뇌를 만드는 흐름입니다.

> 선생님이 처음이어도 진행할 수 있도록 구성했습니다. **먼저 `교사용_가이드.md` 부터 읽으세요.**

## 📁 파일 구성

| 파일 | 용도 | 여는 법 |
|------|------|--------|
| `교사용_가이드.md` | 선생님 사전 학습 + 진행 대본 + 문제 해결 | 텍스트 편집기/뷰어 |
| `커스텀_퀵드로우.ipynb` | 학생 실습용 Colab 노트북 (핵심 결과물) | Google Colab에 업로드 |
| `학습지.html` | 학생 배포용 인쇄 학습지 | 브라우저로 열고 `인쇄(Ctrl/Cmd+P)` |
| `슬라이드.html` | 수업용 발표 슬라이드 | 브라우저로 열고 `←` `→` 키로 이동 |
| `app.py` | **Streamlit 강의 실습 홈페이지** (슬라이드·학습지·실습·자료를 한 곳에) | `streamlit run app.py` 또는 클라우드 배포 |
| `requirements.txt` | 배포에 필요한 패키지 | — |
| `.streamlit/config.toml` | 홈페이지 테마 설정 | — |

## 🌐 학생용 실습 홈페이지 배포하기 (Streamlit)

`app.py` 는 학생들이 한 페이지에서 **발표 슬라이드 / 학습지 / 실습(Colab) / 참고자료**에
접근하는 강의 허브입니다.

### 로컬에서 먼저 보기

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 이 열립니다.

### 인터넷에 무료 배포 (Streamlit Community Cloud) — 추천

1. https://share.streamlit.io 접속 → GitHub 계정으로 로그인
2. `New app` → 저장소 `richee-pc/quickdraw-class`, 브랜치 `main`, 메인 파일 `app.py` 선택
3. `Deploy` 클릭 → 잠시 뒤 `https://...streamlit.app` 주소가 생성됩니다.
4. 그 주소를 학생들에게 공유하면 끝!

> 💡 **Colab 링크 연결**: 노트북을 Colab에 올린 뒤 공유 링크를 복사해서,
> `app.py` 상단의 `COLAB_NOTEBOOK_URL = ""` 안에 붙여넣으면
> 홈페이지의 "실습" 메뉴에 **바로 열기 버튼**이 생깁니다. (안 넣어도 파일 다운로드는 가능)

## 🚀 빠른 시작 (선생님용 3단계)

1. `교사용_가이드.md` 를 끝까지 읽는다.
2. `커스텀_퀵드로우.ipynb` 를 [Google Colab](https://colab.research.google.com)에 업로드해 **직접 한 번 끝까지 실행**해 본다. (리허설)
3. `학습지.html` 인쇄, `슬라이드.html` 화면 준비 → 수업 진행.

## 🧰 준비물

- 학생 1인 1대 컴퓨터 + **펜마우스**
- 학생/교사 **구글 계정** (Colab용)
- 학생 1인 1개 **미드저니 베이직 계정**
- 인터넷 연결 (학교망에서 Colab·미드저니 접속 가능한지 사전 확인)

## ⏱️ 한눈에 보는 흐름 (약 5시간 수업)

1. 도입 — AI의 두 얼굴
2. 미드저니로 게임 아트 만들기
3. 나만의 퀵드로우 수집기 체험 (데이터 학습·편향)
4. 퀵 드로우 원리 + 체험
5. Colab에서 AI 두뇌 만들기 (데이터→학습)
6. Gradio로 게임 완성 + 펜마우스 테스트
7. 발표 · 마무리 · 토론

## 🔗 참고 링크

- Google Quick, Draw! — https://quickdraw.withgoogle.com
- 그림 카테고리 목록/데이터 — https://quickdraw.withgoogle.com/data
- Google Colab — https://colab.research.google.com
- Teachable Machine (보조 체험) — https://teachablemachine.withgoogle.com
