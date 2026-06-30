"""커스텀 퀵 드로우 강의용 실습 홈페이지 (Streamlit)

학생들이 한 곳에서 발표 슬라이드 / 학습지 / 실습 노트북 / 참고자료에
접근할 수 있는 강의 허브입니다.

로컬 실행:  streamlit run app.py
"""
from pathlib import Path
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components

BASE = Path(__file__).parent

# ------------------------------------------------------------------ 설정
st.set_page_config(
    page_title="나만의 커스텀 퀵 드로우",
    page_icon="🎨",
    layout="wide",
)

NOTEBOOK_FILE = "커스텀_퀵드로우.ipynb"
SLIDES_FILE = "슬라이드.html"
WORKSHEET_FILE = "학습지.html"

# GitHub 저장소 정보 — 이 노트북을 Colab에서 바로 열도록 자동 연결합니다.
GITHUB_OWNER_REPO = "richee-pc/quickdraw-class"
GITHUB_BRANCH = "main"

# GitHub에 올라간 노트북을 Colab에서 바로 여는 링크 (자동 생성)
COLAB_NOTEBOOK_URL = (
    "https://colab.research.google.com/github/"
    f"{GITHUB_OWNER_REPO}/blob/{GITHUB_BRANCH}/"
    + urllib.parse.quote(NOTEBOOK_FILE)
)

# 미드저니 접속 주소
MIDJOURNEY_URL = "https://www.midjourney.com/imagine"


def read_text(filename: str) -> str:
    path = BASE / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def read_bytes(filename: str) -> bytes:
    path = BASE / filename
    if not path.exists():
        return b""
    return path.read_bytes()


# ------------------------------------------------------------------ 사이드바
with st.sidebar:
    st.title("🎨 퀵 드로우 실습")
    st.caption("AI를 직접 만들고 펜마우스로 그려서 게임하기")
    page = st.radio(
        "메뉴",
        ["🏠 홈", "🖥️ 발표 슬라이드", "📄 학습지", "🖌️ 미드저니", "🧪 실습 (Colab)", "🔗 참고자료"],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown("**오늘의 흐름**")
    st.markdown(
        "1. AI의 두 얼굴\n"
        "2. 미드저니로 아트 만들기\n"
        "3. 퀵 드로우 원리\n"
        "4. AI 두뇌 만들기\n"
        "5. 펜마우스로 게임!\n"
        "6. 발표 · 마무리"
    )


# ------------------------------------------------------------------ 홈
if page == "🏠 홈":
    st.title("나만의 커스텀 퀵 드로우 만들기")
    st.subheader("그림을 알아맞히는 AI를 직접 만들고, 펜마우스로 게임해봐요!")

    st.markdown(
        """
        > **오늘의 목표**: 수업이 끝나면, **내가 직접 만든 AI**에게
        > 펜마우스로 그림을 그려주면 AI가 알아맞힙니다. 🖊️ → 🤖 → "고양이!"
        """
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🖌️ 만든다 — 생성형 AI")
        st.markdown("글을 쓰면 그림을 그려줌\n\n**예: 미드저니**")
    with c2:
        st.markdown("### 🔍 알아맞힌다 — 분류 AI")
        st.markdown("그림을 보면 이름을 말해줌\n\n**예: 퀵 드로우**")

    st.divider()
    st.markdown("### 컴퓨터는 어떻게 알아맞힐까? (4단계)")
    s1, s2, s3, s4 = st.columns(4)
    s1.info("**1. 데이터**\n\n낙서 수천 장")
    s2.info("**2. 학습**\n\n패턴 익히기")
    s3.info("**3. 모델**\n\n똑똑해진 두뇌")
    s4.info("**4. 추론**\n\n\"이게 뭐게?\"")

    st.divider()
    st.markdown(
        "왼쪽 메뉴에서 **발표 슬라이드 → 학습지 → 실습(Colab)** 순서로 진행하세요."
    )

# ------------------------------------------------------------------ 슬라이드
elif page == "🖥️ 발표 슬라이드":
    st.title("🖥️ 발표 슬라이드")
    st.caption("슬라이드를 한 번 클릭한 뒤, 키보드 ← → 방향키 또는 화면의 ◀ ▶ 버튼으로 넘기세요.")
    html = read_text(SLIDES_FILE)
    if html:
        components.html(html, height=620, scrolling=False)
        st.download_button(
            "⬇️ 슬라이드 파일 내려받기 (HTML)",
            data=read_bytes(SLIDES_FILE),
            file_name=SLIDES_FILE,
            mime="text/html",
        )
    else:
        st.error(f"{SLIDES_FILE} 파일을 찾을 수 없습니다.")

# ------------------------------------------------------------------ 학습지
elif page == "📄 학습지":
    st.title("📄 학습지")
    st.caption("아래에서 미리 보고, 내려받아 인쇄해서 사용하세요. (인쇄: 브라우저에서 Ctrl/Cmd + P)")
    html = read_text(WORKSHEET_FILE)
    if html:
        st.download_button(
            "⬇️ 학습지 내려받기 (HTML)",
            data=read_bytes(WORKSHEET_FILE),
            file_name=WORKSHEET_FILE,
            mime="text/html",
        )
        components.html(html, height=900, scrolling=True)
    else:
        st.error(f"{WORKSHEET_FILE} 파일을 찾을 수 없습니다.")

# ------------------------------------------------------------------ 미드저니
elif page == "🖌️ 미드저니":
    st.title("🖌️ 미드저니로 게임 아트 만들기")
    st.markdown(
        "미드저니는 **글(프롬프트)을 쓰면 그림을 만들어 주는 AI**예요. "
        "내 게임에 쓸 ① 제목 로고 ② 정답 캐릭터(마스코트) ③ 배경을 만들어 봅시다."
    )
    st.link_button("🎨 미드저니 열기", MIDJOURNEY_URL, type="primary")

    st.divider()
    st.subheader("✨ 프롬프트 자동 만들기")
    st.caption("아래에서 고르면 미드저니에 넣을 영어 프롬프트가 자동으로 만들어져요. 복사해서 붙여넣으세요!")

    purpose = st.selectbox(
        "무엇을 만들까요?",
        ["정답 캐릭터(마스코트)", "게임 제목 로고", "배경", "직접 입력"],
    )

    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input(
            "주제 (영어로 쓰면 더 잘 돼요)",
            value="cat",
            help="예: cat, apple, robot, space ...",
        )
    with col2:
        style = st.selectbox(
            "그림 스타일",
            [
                "flat vector illustration",
                "cute cartoon",
                "watercolor painting",
                "pixel art",
                "3d render",
                "simple line art",
                "sticker design",
            ],
        )

    col3, col4 = st.columns(2)
    with col3:
        color = st.selectbox(
            "색감/분위기",
            ["pastel colors", "vivid colors", "bright and cheerful", "black and white", "neon"],
        )
    with col4:
        ratio = st.selectbox("그림 비율 (--ar)", ["1:1 (정사각)", "16:9 (가로)", "9:16 (세로)"])

    extras = st.multiselect(
        "추가 옵션 (선택)",
        ["simple", "minimal", "white background", "kawaii", "logo", "mascot", "high detail"],
        default=["simple", "white background"],
    )

    # 용도별 기본 키워드 살짝 더하기
    purpose_hint = {
        "정답 캐릭터(마스코트)": "mascot character",
        "게임 제목 로고": "game logo, text",
        "배경": "background scene",
        "직접 입력": "",
    }[purpose]

    ratio_code = {"1:1 (정사각)": "1:1", "16:9 (가로)": "16:9", "9:16 (세로)": "9:16"}[ratio]

    parts = [subject.strip(), purpose_hint, style, color] + extras
    prompt_text = ", ".join([p for p in parts if p]).strip(", ")
    prompt_text = f"{prompt_text} --ar {ratio_code}"

    st.markdown("**👇 이 프롬프트를 복사해서 미드저니에 붙여넣으세요**")
    st.code(prompt_text, language="text")

    st.divider()
    st.markdown(
        """
        ### 💡 사용 순서
        1. 위 **미드저니 열기** 버튼으로 접속 (로그인)
        2. 만들어진 프롬프트를 복사해서 입력칸(`/imagine`)에 붙여넣기
        3. 마음에 드는 그림을 골라 **다운로드**
        4. 실습에서 만든 게임을 이 그림으로 꾸미기

        > ⚠️ **베이직 플랜 팁**: 빠른 생성(Fast) 시간이 정해져 있어요.
        > 프롬프트를 미리 잘 정한 뒤 **꼭 필요한 4~6장만** 만드세요.
        """
    )

# ------------------------------------------------------------------ 실습
elif page == "🧪 실습 (Colab)":
    st.title("🧪 실습 — 나만의 AI 만들기")
    st.markdown(
        "구글 Colab에서 코드를 순서대로 실행하면 됩니다. "
        "설치가 필요 없고, 구글 로그인만 하면 바로 시작할 수 있어요."
    )

    st.link_button("🚀 Colab에서 실습 노트북 열기", COLAB_NOTEBOOK_URL, type="primary")
    st.caption(
        "버튼이 안 열리면(저장소가 비공개일 때) 아래에서 노트북을 내려받아 "
        "Colab(좌측 상단 파일 → 노트북 업로드)에 올려서 사용하세요."
    )

    st.download_button(
        "⬇️ 노트북 파일 내려받기 (.ipynb)",
        data=read_bytes(NOTEBOOK_FILE),
        file_name=NOTEBOOK_FILE,
        mime="application/x-ipynb+json",
    )

    st.divider()
    st.markdown(
        """
        ### 실습 순서 (노트북 7단계)
        1. **준비물 설치** — 그림판 도구 설치
        2. **그림 데이터 가져오기** — 내가 쓸 그림 3~5개 고르기 ✏️
        3. **데이터 살펴보기** — 학습할 그림 눈으로 확인
        4. **학습 준비** — 데이터 다듬고 나누기
        5. **AI 두뇌 만들고 학습** — 정확도 올라가는 것 확인
        6. **성적 확인** — 시험 그림으로 정확도 측정
        7. **펜마우스로 그려서 맞히기!** 🖊️

        > 💡 막히면? 위 셀부터 **순서대로** 다시 실행하거나, `런타임 → 모두 실행`.
        """
    )

# ------------------------------------------------------------------ 참고자료
elif page == "🔗 참고자료":
    st.title("🔗 참고자료")
    st.markdown(
        """
        - **Google Quick, Draw! (체험)** — https://quickdraw.withgoogle.com
        - **그림 카테고리 목록/데이터** — https://quickdraw.withgoogle.com/data
        - **Google Colab** — https://colab.research.google.com
        - **Teachable Machine (보조 체험)** — https://teachablemachine.withgoogle.com

        ---
        ### 미드저니 프롬프트 공식
        `주제 + 스타일 + 색감/분위기`

        예) `cute cat mascot, flat vector illustration, pastel colors, simple`

        만들 것: ① 게임 제목 로고 ② 정답 캐릭터(마스코트) ③ 배경
        """
    )

st.sidebar.divider()
st.sidebar.caption("© 커스텀 퀵 드로우 수업 · Streamlit")
