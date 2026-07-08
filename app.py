"""커스텀 퀵 드로우 학생 실습 홈페이지 (Streamlit)

학생들이 한 곳에서 발표 슬라이드 / 학습지 / 실습 노트북 / 참고자료에
접근할 수 있는 강의 허브입니다.

로컬 실행:  streamlit run app.py
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import urllib.parse
import urllib.request
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
COLLECTOR_FILE = "나만의_퀵드로우_수집기.html"
COLLECTOR_API_URL = "https://script.google.com/macros/s/AKfycbzPP6GHuqSHltZxutD8qyt8-TW_F5HNU1-2jLtkxEMPa-H8ufKdMzbl6GnCC1Lnq3pA/exec"


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


def post_json(url: str, payload: dict) -> tuple[bool, str]:
    """Server-side POST helper for Apps Script endpoints."""
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            body = res.read().decode("utf-8", errors="ignore")
        return True, body
    except Exception as e:  # pragma: no cover - UI fallback path
        return False, str(e)


st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&display=swap');
      .stApp {
        background:
          radial-gradient(1200px 540px at 10% -10%, #dbeafe 0%, rgba(219,234,254,0) 60%),
          radial-gradient(1000px 420px at 90% -20%, #e0f2fe 0%, rgba(224,242,254,0) 60%),
          linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 100%);
        font-family: 'Gowun Dodum', 'Malgun Gothic', system-ui, sans-serif;
      }
      [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e3a8a 60%, #0369a1 100%);
      }
      [data-testid="stSidebar"] * { color: #f8fafc !important; }
      h1, h2, h3 {
        font-family: 'Jua', 'Gowun Dodum', sans-serif !important;
        letter-spacing: 0.2px;
      }
      .card {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid #bfdbfe;
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 10px 26px rgba(14, 116, 144, 0.10);
      }
      .hero {
        background: linear-gradient(135deg, #38bdf8 0%, #60a5fa 45%, #6366f1 100%);
        color: #ffffff;
        border-radius: 22px;
        padding: 22px 20px;
        box-shadow: 0 14px 34px rgba(37, 99, 235, 0.28);
      }
      .hero h3, .hero p { color: #ffffff !important; margin: 0; }
      .hero p { opacity: 0.95; margin-top: 8px; }
      .section-chip {
        display: inline-block;
        background: #e0f2fe;
        color: #075985;
        border: 1px solid #bae6fd;
        border-radius: 999px;
        padding: 4px 12px;
        font-size: 13px;
        margin-bottom: 8px;
      }
      .worksheet-wrap {
        background: rgba(255,255,255,0.9);
        border: 1px solid #bae6fd;
        border-radius: 18px;
        padding: 16px 16px 4px;
        box-shadow: 0 10px 24px rgba(14, 116, 144, 0.1);
      }
      .stButton>button, .stDownloadButton>button, .stFormSubmitButton>button {
        border-radius: 12px !important;
        border: 1px solid #7dd3fc !important;
        background: linear-gradient(135deg, #38bdf8 0%, #60a5fa 100%) !important;
        color: white !important;
        font-weight: 700 !important;
      }
      .stTextInput input, .stTextArea textarea {
        border-radius: 12px !important;
        border-color: #7dd3fc !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ 사이드바
with st.sidebar:
    st.title("🎨 퀵 드로우 실습")
    st.caption("AI를 직접 만들고 펜마우스로 그려서 게임하기")
    page = st.radio(
        "메뉴",
        [
            "1️⃣ 도입",
            "2️⃣ 데이터 학습·편향 (수집기)",
            "🖥️ 발표 슬라이드",
            "📄 학습지 작성·제출",
            "3️⃣ 미드저니 아트 만들기",
            "4️⃣~5️⃣ Colab으로 퀵드로우 만들기",
            "6️⃣ 발표·마무리",
            "🔗 참고자료",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown("**오늘의 흐름**")
    st.markdown(
        "1. 도입 — AI 두 얼굴 시연\n"
        "2. 데이터 학습·편향 — 수집기 체험\n"
        "3. 미드저니 아트 만들기\n"
        "4-5. Colab으로 나만의 퀵드로우 만들기(코드 작성)\n"
        "6. 발표·마무리"
    )


# ------------------------------------------------------------------ 도입
if page == "1️⃣ 도입":
    st.title("나만의 커스텀 퀵 드로우 만들기")
    st.subheader("그림을 알아맞히는 AI를 직접 만들고, 펜마우스로 게임해봐요!")
    st.markdown(
        """
        <div class="hero">
          <h3>✨ 오늘의 미션</h3>
          <p>데이터를 모으고, AI를 학습시키고, 내가 만든 퀵드로우 게임을 직접 플레이해요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        > **오늘의 목표**: 수업이 끝나면, **내가 직접 만든 AI**에게
        > 펜마우스로 그림을 그려주면 AI가 알아맞힙니다. 🖊️ → 🤖 → "고양이!"
        """
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            '<div class="card"><h3>🖌️ 만든다 — 생성형 AI</h3><p>글을 쓰면 그림을 그려줌<br><b>예: 미드저니</b></p></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="card"><h3>🔍 알아맞힌다 — 분류 AI</h3><p>그림을 보면 이름을 말해줌<br><b>예: 퀵 드로우</b></p></div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("### 컴퓨터는 어떻게 알아맞힐까? (4단계)")
    s1, s2, s3, s4 = st.columns(4)
    s1.info("**1. 데이터**\n\n낙서 수천 장")
    s2.info("**2. 학습**\n\n패턴 익히기")
    s3.info("**3. 모델**\n\n똑똑해진 두뇌")
    s4.info("**4. 추론**\n\n\"이게 뭐게?\"")

    st.divider()
    st.markdown(
        "왼쪽 메뉴를 순서대로 진행해보세요: **도입 → 수집기 → 미드저니 → Colab → 발표·마무리**"
    )

# ------------------------------------------------------------------ 수집기 체험
elif page == "2️⃣ 데이터 학습·편향 (수집기)":
    st.markdown('<div class="section-chip">DATA BIAS LAB</div>', unsafe_allow_html=True)
    st.title("🧩 나만의 퀵드로우 수집기")
    st.subheader("직접 데이터를 만들며 학습과 편향의 의미를 먼저 체험해요")
    st.markdown(
        """
        이 활동은 본격적인 파이썬 실습 전에 진행하는 **사전 체험 단계**입니다.
        학생이 한 물체(예: 자동차)를 자유롭게 그려 데이터를 모으고,
        로컬 테스트를 통해 **데이터 다양성과 편향의 영향**을 확인합니다.
        """
    )
    collector_html = read_text(COLLECTOR_FILE)
    if collector_html:
        st.download_button(
            "⬇️ 수집기 파일 내려받기 (HTML)",
            data=read_bytes(COLLECTOR_FILE),
            file_name=COLLECTOR_FILE,
            mime="text/html",
        )
        components.html(collector_html, height=1020, scrolling=True)
    else:
        st.error(f"{COLLECTOR_FILE} 파일을 찾을 수 없습니다.")

    st.divider()
    st.markdown("### 👀 무엇을 관찰하면 좋을까요?")
    st.markdown(
        """
        - **데이터 학습의 중요성**: 학습 데이터가 많고 다양할수록 인식이 안정적입니다.
        - **데이터 편향의 영향**: 비슷한 형태만 많이 그리면 성능이 흔들릴 수 있습니다.
        - **비교 실험**: 같은 물체를 다양한 방식으로 그렸을 때 결과가 어떻게 달라지는지 확인해 보세요.
        """
    )

    st.markdown("### ✅ 활동 체크리스트")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            1. 한 물체를 정하고 그림 데이터 수집  
            2. 각자 자유롭게 충분히 그리기  
            3. 로컬 테스트로 오인식 사례 기록
            """
        )
    with c2:
        st.markdown(
            """
            4. 모양/크기/위치를 바꿔 추가 수집  
            5. 다시 테스트해서 변화 비교  
            6. "왜 성능이 달라졌는지" 한 줄 정리
            """
        )

    st.info(
        "팁: 같은 물체라도 모양/크기/그림 위치가 다양할수록, AI도 더 잘 맞힐 가능성이 커져요."
    )

# ------------------------------------------------------------------ 슬라이드
elif page == "🖥️ 발표 슬라이드":
    st.markdown('<div class="section-chip">CLASS PRESENTATION</div>', unsafe_allow_html=True)
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
elif page == "📄 학습지 작성·제출":
    st.markdown('<div class="section-chip">WORKSHEET SUBMISSION</div>', unsafe_allow_html=True)
    st.title("📄 학습지 작성 · 제출")
    st.caption("인쇄 대신 웹에서 바로 작성하고 제출할 수 있어요.")
    st.markdown(
        """
        <div class="hero">
          <h3>🧊 여름 캠프 미션 카드</h3>
          <p>핵심 개념 + 데이터 편향 체험 + 코랩 결과를 정리해서 제출해요!</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="worksheet-wrap">', unsafe_allow_html=True)

    with st.form("worksheet-submit-form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            student_name = st.text_input("이름", max_chars=30)
        with c2:
            student_class = st.text_input("학년/반", max_chars=30)
        with c3:
            student_number = st.text_input("번호(선택)", max_chars=10)

        st.markdown("### 1) 오늘의 핵심 개념")
        concept_gen_ai = st.text_input("생성형 AI 예시 1개", placeholder="예: 미드저니")
        concept_cls_ai = st.text_input("분류 AI 예시 1개", placeholder="예: 퀵드로우")

        st.markdown("### 2) 데이터 편향 체험 기록")
        bias_before = st.text_area("처음 수집 데이터 특징", placeholder="예: 비슷한 모양으로만 그림", height=90)
        bias_issue = st.text_area("문제/오인식 사례", placeholder="예: 특정 모양만 잘 맞힘", height=90)
        bias_fix = st.text_area("개선 방법", placeholder="예: 크기·위치·모양을 다양하게 추가", height=90)

        st.markdown("### 3) 코랩 실습 결과")
        accuracy = st.text_input("최종 정확도(%)", placeholder="예: 84.5")
        best_tip = st.text_area("내가 찾은 성능 향상 팁 1가지", height=90)

        st.markdown("### 4) 마무리")
        reflection = st.text_area("AI가 틀린 이유와 느낀 점", height=120)

        submit = st.form_submit_button("📨 선생님께 제출")
    st.markdown("</div>", unsafe_allow_html=True)

    if submit:
        if not student_name.strip():
            st.error("이름은 꼭 입력해주세요.")
        else:
            payload = {
                "action": "append",
                "classId": "worksheet-camp",
                "objectName": "worksheet-response",
                "records": [
                    {
                        "studentId": f"{student_class.strip()} {student_name.strip()} {student_number.strip()}".strip(),
                        "vec": [],
                        "meta": {
                            "submittedAt": datetime.now(timezone.utc).isoformat(),
                            "name": student_name.strip(),
                            "class": student_class.strip(),
                            "number": student_number.strip(),
                            "concept_gen_ai": concept_gen_ai.strip(),
                            "concept_cls_ai": concept_cls_ai.strip(),
                            "bias_before": bias_before.strip(),
                            "bias_issue": bias_issue.strip(),
                            "bias_fix": bias_fix.strip(),
                            "accuracy": accuracy.strip(),
                            "best_tip": best_tip.strip(),
                            "reflection": reflection.strip(),
                        },
                        "createdAt": datetime.now(timezone.utc).isoformat(),
                    }
                ],
            }
            ok, msg = post_json(COLLECTOR_API_URL, payload)
            if ok:
                st.success("제출 완료! 선생님에게 전송되었습니다.")
                st.caption(f"응답: {msg[:160]}")
            else:
                st.error("제출 중 오류가 발생했어요. 잠시 후 다시 시도해 주세요.")
                st.caption(msg[:200])

# ------------------------------------------------------------------ 미드저니
elif page == "3️⃣ 미드저니 아트 만들기":
    st.markdown('<div class="section-chip">MIDJOURNEY CREATOR</div>', unsafe_allow_html=True)
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

    st.divider()
    st.markdown("### 🎯 미드저니를 더 잘 쓰는 아이디어")
    st.markdown(
        """
        - **클래스별 통일 디자인**: 같은 스타일 키워드(색감/선 두께/배경 톤)를 고정해서 3~5개 클래스를 한 세트로 만드세요.
        - **오답 줄이기 아트 전략**: 정답 오브젝트를 **정면·측면·원근**으로 각각 1장씩 생성해서 학생 스케치 다양성을 유도해요.
        - **게임 완성도 업**: 맞혔을 때 보여줄 `정답 보상 이미지`, 틀렸을 때 보여줄 `힌트 이미지`를 따로 만들어 두세요.
        - **프롬프트 실험 노트**: 한 단어만 바꿨을 때 결과가 어떻게 달라지는지 3회 비교 기록해보세요.
        """
    )

# ------------------------------------------------------------------ 실습
elif page == "4️⃣~5️⃣ Colab으로 퀵드로우 만들기":
    st.markdown('<div class="section-chip">PYTHON BUILD ZONE</div>', unsafe_allow_html=True)
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
        2.5 **(선택) 수집기 JSON 합치기** — 초반 체험 데이터를 학습셋에 추가
        3. **데이터 살펴보기** — 학습할 그림 눈으로 확인
        4. **학습 준비** — DIVISOR / CHANNELS 를 코드에서 직접 채워야 실행됩니다 ✏️
        5. **AI 두뇌 만들고 학습** — ACTIVATION / FILTERS, 그리고 `add_conv_block()`의 TODO를 완성하세요 ✏️
        6. **성적 확인** — 시험 그림으로 정확도 측정
        7. **펜마우스로 그려서 맞히기!** 🖊️

        > 💡 막히면? 위 셀부터 **순서대로** 다시 실행하거나, `런타임 → 모두 실행`.
        """
    )

# ------------------------------------------------------------------ 발표·마무리
elif page == "6️⃣ 발표·마무리":
    st.markdown('<div class="section-chip">SHOWCASE TIME</div>', unsafe_allow_html=True)
    st.title("6️⃣ 발표 · 마무리")
    st.subheader("AI가 틀리는 이유를 데이터 관점으로 이야기해봐요")

    slides_html = read_text(SLIDES_FILE)
    if slides_html:
        last_slide_html = slides_html.replace(
            "<body>",
            "<body><script>window.SLIDE_START = 9;</script>",
            1,
        )
        st.caption("아래는 발표용 마지막 질문 슬라이드(자동 시작)입니다.")
        components.html(last_slide_html, height=520, scrolling=False)

    st.markdown(
        """
        아래 질문에 답해보세요.
        - AI가 잘 못 맞힌 그림은 무엇이었나요?
        - 학습 데이터가 한쪽으로 치우치면 어떤 일이 생길까요?
        - 수집기에서 더 다양하게 그리면 결과가 어떻게 달라질까요?
        """
    )

    st.divider()
    st.markdown("### 학습지(인쇄/확인)")
    st.download_button(
        "⬇️ 학습지 내려받기 (HTML)",
        data=read_bytes(WORKSHEET_FILE),
        file_name=WORKSHEET_FILE,
        mime="text/html",
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

    st.divider()
    st.markdown("### 📦 저장 위치 확인(수집기/학습지 제출)")
    st.markdown(
        """
        현재 제출은 **Google Drive 폴더 파일**이 아니라, 연결된 **Apps Script의 저장소(대부분 Google 스프레드시트)**로 들어갑니다.

        확인 방법:
        1. Apps Script 편집기에서 해당 웹앱 프로젝트 열기  
        2. 코드에서 `SpreadsheetApp` 사용 여부 확인  
        3. `openById(...)` 또는 `getActiveSpreadsheet()` 대상 스프레드시트를 Drive에서 열기
        """
    )

st.sidebar.divider()
st.sidebar.caption("© 커스텀 퀵 드로우 수업 · Streamlit")
