"""커스텀 퀵 드로우 학생 실습 홈페이지 (Streamlit)

학생들이 한 곳에서 발표 슬라이드 / 학습지 / 실습 노트북 / 참고자료에
접근할 수 있는 강의 허브입니다.

로컬 실행:  streamlit run app.py
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import random
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
COLLECTOR_CLASS_ID = "collector-submissions-2026"
WORKSHEET_CLASS_ID = "worksheet-submissions-2026"


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


def _init_principle_progress() -> None:
    if "principle_done" not in st.session_state:
        st.session_state.principle_done = {f"m{i}": False for i in range(1, 6)}


def _mark_principle_done(module_key: str) -> None:
    st.session_state.principle_done[module_key] = True


def _principle_progress_ratio() -> float:
    done = st.session_state.get("principle_done", {})
    if not done:
        return 0.0
    return sum(1 for v in done.values() if v) / len(done)


def _quiz_block(
    module_key: str,
    quiz_key: str,
    question: str,
    options: list[str],
    correct_idx: int,
    explanation: str,
) -> None:
    st.markdown(f"**📝 퀴즈:** {question}")
    choice = st.radio(
        "정답을 고르세요",
        options,
        key=f"{quiz_key}_choice",
        label_visibility="collapsed",
    )
    if st.button("✅ 정답 확인", key=f"{quiz_key}_check"):
        picked = options.index(choice)
        if picked == correct_idx:
            st.success("정답! 🎉")
            st.info(explanation)
            _mark_principle_done(module_key)
        else:
            st.error("아쉽지만 오답이에요. 설명을 다시 읽고 한 번 더 도전해보세요!")
            st.caption(explanation)


st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Noto+Sans+KR:wght@400;500;700&display=swap');
      .stApp {
        background:
          radial-gradient(1200px 540px at 10% -10%, #dbeafe 0%, rgba(219,234,254,0) 60%),
          radial-gradient(1000px 420px at 90% -20%, #fce7f3 0%, rgba(252,231,243,0) 58%),
          linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 55%, #fdf2f8 100%);
        font-family: 'Noto Sans KR', 'Malgun Gothic', system-ui, sans-serif;
      }
      [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 42%, #fce7f3 100%);
        border-right: 1px solid #bfdbfe;
      }
      [data-testid="stSidebar"] * { color: #334155 !important; }
      h1, h2, h3 {
        font-family: 'Gowun Dodum', 'Noto Sans KR', sans-serif !important;
        letter-spacing: 0.1px;
      }
      .card {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid #c4b5fd;
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 12px 28px rgba(219, 39, 119, 0.08);
      }
      .hero {
        background: linear-gradient(135deg, #7dd3fc 0%, #93c5fd 42%, #f9a8d4 100%);
        color: #ffffff;
        border-radius: 22px;
        padding: 22px 20px;
        box-shadow: 0 14px 34px rgba(236, 72, 153, 0.24);
      }
      .hero h3, .hero p { color: #ffffff !important; margin: 0; }
      .hero p { opacity: 0.95; margin-top: 8px; }
      .section-chip {
        display: inline-block;
        background: linear-gradient(135deg, #e0f2fe 0%, #fce7f3 100%);
        color: #7e22ce;
        border: 1px solid #c4b5fd;
        border-radius: 999px;
        padding: 4px 13px;
        font-size: 13px;
        margin-bottom: 8px;
      }
      .worksheet-wrap {
        background: rgba(255,255,255,0.9);
        border: 1px solid #c4b5fd;
        border-radius: 18px;
        padding: 16px 16px 4px;
        box-shadow: 0 12px 30px rgba(236, 72, 153, 0.12);
      }
      .stButton>button, .stDownloadButton>button, .stFormSubmitButton>button {
        border-radius: 12px !important;
        border: 1px solid #a5b4fc !important;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 55%, #f472b6 100%) !important;
        color: white !important;
        font-weight: 700 !important;
      }
      .stTextInput input, .stTextArea textarea {
        border-radius: 12px !important;
        border-color: #a5b4fc !important;
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
            "🌈 도입",
            "🧠 AI·코딩 핵심 원리",
            "🧩 데이터 학습·편향 (수집기)",
            "🖥️ 수업 슬라이드",
            "📝 학습지 작성·제출",
            "🎀 미드저니 아트 만들기",
            "💻 Colab으로 퀵드로우 만들기",
            "🎤 발표·마무리",
            "📎 참고자료",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown("**오늘의 흐름**")
    st.markdown(
        "1. 도입 — 아이스브레이킹 + AI 두 얼굴\n"
        "2. AI·코딩 핵심 원리 — 30분 이론+퀴즈\n"
        "3. 데이터 학습·편향 — 수집기 체험\n"
        "4. 미드저니 아트 만들기\n"
        "5-6. Colab으로 나만의 퀵드로우 만들기(코드 작성)\n"
        "7. 발표·마무리"
    )


# ------------------------------------------------------------------ 도입
if page == "🌈 도입":
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

    st.divider()
    st.markdown("### 🧊 아이스 브레이킹: 팀 구성 + 쁘띠바크 게임")
    st.caption("OT 시작 10~15분 활동으로 팀 분위기를 빠르게 만들어요.")
    st.video("https://www.youtube.com/watch?v=ctsnCNBf7Dw")

    g1, g2 = st.columns(2)
    with g1:
        st.markdown(
            """
            <div class="card">
              <h3>진행 순서</h3>
              <p>1) 4~5명 팀 구성<br>
              2) 영상 규칙 확인<br>
              3) 팀별 1~2라운드 진행<br>
              4) 팀 구호/역할 정하기</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with g2:
        st.markdown(
            """
            <div class="card">
              <h3>교사 운영 팁</h3>
              <p>• 시간 제한: 라운드당 3분<br>
              • 팀별 기록자 1명 지정<br>
              • 활동 후 \"협업 규칙\" 1개씩 발표</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("### 🎲 랜덤 팀 배정")
    st.caption("학생 이름을 줄바꿈으로 입력하면 팀을 자동으로 나눠줍니다.")
    name_text = st.text_area(
        "학생 이름 목록 (한 줄에 한 명)",
        height=130,
        placeholder="김다은\n홍길동\n이하늘\n박소연",
        key="icebreak_names",
    )
    team_count = st.slider("팀 수", min_value=2, max_value=8, value=4, key="icebreak_team_count")

    if st.button("랜덤 팀 배정하기", key="assign_teams"):
        names = [n.strip() for n in name_text.splitlines() if n.strip()]
        if len(names) < team_count:
            st.warning("팀 수보다 학생 수가 많아야 팀을 나눌 수 있어요.")
        else:
            random.shuffle(names)
            teams = [[] for _ in range(team_count)]
            for idx, name in enumerate(names):
                teams[idx % team_count].append(name)
            st.session_state["icebreak_teams"] = teams

    teams = st.session_state.get("icebreak_teams", [])
    if teams:
        cols = st.columns(min(len(teams), 4))
        for i, team in enumerate(teams):
            with cols[i % len(cols)]:
                members = "<br>".join(team) if team else "(없음)"
                st.markdown(
                    f"""
                    <div class="card">
                      <h3>팀 {i + 1}</h3>
                      <p>{members}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.divider()
    st.markdown("### 🗂️ 쁘띠바크 게임 양식 틀")
    st.caption("영상 규칙에 맞춰 팀별 기록을 남길 수 있는 제출용 템플릿입니다.")

    with st.form("petitbac-template-form"):
        c1, c2 = st.columns(2)
        with c1:
            pb_team_name = st.text_input("팀 이름", placeholder="예: 스카이블루팀")
            pb_round = st.text_input("라운드", placeholder="예: 1라운드")
        with c2:
            pb_initial = st.text_input("제시 글자/초성", placeholder="예: ㄱ")
            pb_time = st.text_input("제한 시간", value="3분")

        st.markdown("#### 카테고리별 답안")
        pb_cat1 = st.text_input("1) 카테고리 A", placeholder="예: 동물")
        pb_ans1 = st.text_input("1) 우리 팀 답")
        pb_cat2 = st.text_input("2) 카테고리 B", placeholder="예: 음식")
        pb_ans2 = st.text_input("2) 우리 팀 답")
        pb_cat3 = st.text_input("3) 카테고리 C", placeholder="예: 사물")
        pb_ans3 = st.text_input("3) 우리 팀 답")
        pb_cat4 = st.text_input("4) 카테고리 D", placeholder="예: 장소")
        pb_ans4 = st.text_input("4) 우리 팀 답")
        pb_cat5 = st.text_input("5) 카테고리 E", placeholder="예: 직업")
        pb_ans5 = st.text_input("5) 우리 팀 답")

        st.markdown("#### 결과 기록")
        pb_score = st.text_input("라운드 점수", placeholder="예: 35")
        pb_feedback = st.text_area("팀 회고/피드백", height=90, placeholder="무엇이 잘 됐고, 다음 라운드에서 무엇을 바꿀지")

        pb_submit = st.form_submit_button("✅ 쁘띠바크 기록 제출")

    if pb_submit:
        if not pb_team_name.strip():
            st.warning("팀 이름을 입력해주세요.")
        else:
            pb_payload = {
                "action": "append",
                "classId": "petitbac-submissions-2026",
                "objectName": "petitbac-record",
                "records": [
                    {
                        "studentId": pb_team_name.strip(),
                        "vec": [],
                        "meta": {
                            "submittedAt": datetime.now(timezone.utc).isoformat(),
                            "round": pb_round.strip(),
                            "initial": pb_initial.strip(),
                            "timeLimit": pb_time.strip(),
                            "categoryA": pb_cat1.strip(),
                            "answerA": pb_ans1.strip(),
                            "categoryB": pb_cat2.strip(),
                            "answerB": pb_ans2.strip(),
                            "categoryC": pb_cat3.strip(),
                            "answerC": pb_ans3.strip(),
                            "categoryD": pb_cat4.strip(),
                            "answerD": pb_ans4.strip(),
                            "categoryE": pb_cat5.strip(),
                            "answerE": pb_ans5.strip(),
                            "score": pb_score.strip(),
                            "feedback": pb_feedback.strip(),
                        },
                        "createdAt": datetime.now(timezone.utc).isoformat(),
                    }
                ],
            }
            ok, msg = post_json(COLLECTOR_API_URL, pb_payload)
            if ok:
                st.success("쁘띠바크 기록이 제출되었어요!")
                st.caption(f"응답: {msg[:140]}")
            else:
                st.error("제출 중 오류가 발생했습니다.")
                st.caption(msg[:180])

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
        "왼쪽 메뉴를 순서대로 진행해보세요: **도입 → 핵심 원리 → 수집기 → 미드저니 → Colab → 발표·마무리**"
    )

# ------------------------------------------------------------------ AI·코딩 핵심 원리 (30분 이론+퀴즈)
elif page == "🧠 AI·코딩 핵심 원리":
    _init_principle_progress()
    st.markdown('<div class="section-chip">AI & CODING CORE · 30 MIN</div>', unsafe_allow_html=True)
    st.title("🧠 AI·코딩 핵심 원리")
    st.caption("약 30분 · 5개 모듈 · 중간중간 퀴즈와 미니 실습으로 개념을 익혀요")
    st.markdown(
        """
        <div class="hero">
          <h3>오늘 배울 핵심</h3>
          <p>이미지 생성·인식 AI가 어떻게 작동하는지, 데이터 편향이 왜 중요한지, 코랩 실습에 필요한 코딩 개념까지 한 번에 정리해요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(_principle_progress_ratio(), text=f"학습 진행률 {int(_principle_progress_ratio() * 100)}%")

    m1, m2, m3, m4, m5 = st.tabs(
        ["1️⃣ AI 두 얼굴 (5분)", "2️⃣ AI 4단계 (5분)", "3️⃣ 이미지 인식 (8분)", "4️⃣ 데이터 편향 (7분)", "5️⃣ 코딩 기초 (5분)"]
    )

    with m1:
        st.markdown("### 생성형 AI vs 분류 AI")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                """
                <div class="card">
                  <h3>🖌️ 생성형 AI (Generative)</h3>
                  <p><b>입력:</b> 글(프롬프트)<br>
                  <b>출력:</b> 새로운 이미지/글<br>
                  <b>예:</b> 미드저니, DALL·E</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                """
                <div class="card">
                  <h3>🔍 분류 AI (Classification)</h3>
                  <p><b>입력:</b> 그림/사진<br>
                  <b>출력:</b> 이름(라벨)<br>
                  <b>예:</b> 퀵드로우, 얼굴 인식</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.info("오늘 수업: 미드저니(생성) + 퀵드로우(분류)를 모두 다룹니다. 같은 'AI'지만 하는 일이 완전히 달라요!")
        _quiz_block(
            "m1",
            "quiz_m1",
            "미드저니에 'cute cat'이라고 입력하면 어떤 일이 일어날까요?",
            ["고양이 그림을 새로 만들어준다", "내가 그린 고양이를 맞춰준다", "고양이 사진을 삭제한다"],
            0,
            "생성형 AI는 텍스트를 받아 **새로운 이미지**를 만듭니다. 분류 AI는 이미 있는 그림을 보고 **이름을 맞춥니다**.",
        )

    with m2:
        st.markdown("### AI가 똑똑해지는 4단계")
        s1, s2, s3, s4 = st.columns(4)
        s1.success("**1. 데이터**\n\n예: 낙서 1000장")
        s2.success("**2. 학습**\n\n패턴 찾기")
        s3.success("**3. 모델**\n\n학습된 두뇌")
        s4.success("**4. 추론**\n\n새 그림 맞히기")
        st.markdown(
            """
            | 단계 | 비유 | 오늘 수업에서 |
            |---|---|---|
            | 데이터 | 교과서 문제집 | 수집기에서 직접 그림 |
            | 학습 | 문제 풀며 공부 | Colab에서 모델 학습 |
            | 모델 | 시험 전 머릿속 | 학습 완료된 AI |
            | 추론 | 실전 시험 | 펜마우스로 그려서 테스트 |
            """
        )
        st.markdown("**🧪 미니 실습:** 아래 단계를 올바른 순서로 배열해보세요.")
        order_pick = st.multiselect(
            "순서대로 클릭 (1→2→3→4)",
            ["추론", "데이터", "학습", "모델"],
            default=[],
            key="order_practice",
        )
        if st.button("순서 확인", key="order_check"):
            if order_pick == ["데이터", "학습", "모델", "추론"]:
                st.success("완벽해요! AI는 항상 데이터 → 학습 → 모델 → 추론 순서로 진행됩니다.")
                _mark_principle_done("m2")
            else:
                st.warning(f"현재 선택: {' → '.join(order_pick) if order_pick else '(없음)'} · 정답: 데이터 → 학습 → 모델 → 추론")

    with m3:
        st.markdown("### 컴퓨터는 그림을 어떻게 볼까?")
        st.markdown(
            """
            1. **픽셀**: 그림은 작은 사각형(픽셀)의 모음. 각 픽셀은 0~255 밝기 값.
            2. **정규화**: 0~255 → 0~1로 바꿔 학습을 안정적으로 (`÷ 255`).
            3. **CNN(합성곱 신경망)**: 그림에서 **선·모양·패턴**을 단계적으로 찾는 AI 구조.
            """
        )
        st.code(
            "# 28×28 흑백 그림 100장 → (100, 28, 28, 1)\n"
            "shape = (N, height, width, channels)\n"
            "normalized = image / 255.0",
            language="python",
        )
        st.markdown(
            """
            **CNN 레이어 역할 (쉬운 비유)**
            - `Conv2D`: 돋보기로 특징(선, 곡선) 찾기
            - `MaxPooling`: 중요한 정보만 남기기
            - `Flatten` + `Dense`: 찾은 특징으로 최종 답(라벨) 고르기
            """
        )
        _quiz_block(
            "m3",
            "quiz_m3",
            "28×28 흑백 그림 50장을 학습할 때, 올바른 shape는?",
            ["(50, 28, 28, 1)", "(50, 28, 28)", "(28, 28, 50, 1)", "(1, 50, 28, 28)"],
            0,
            "N=50장, 높이=28, 너비=28, 채널=1(흑백) → **(50, 28, 28, 1)** 이 맞습니다.",
        )

    with m4:
        st.markdown("### 데이터 편향 — AI가 틀리는 대표 이유")
        st.markdown(
            """
            **데이터 편향(Bias)**: 학습 데이터가 특정 유형에만 치우쳐 있을 때 발생.

            | 상황 | 결과 |
            |---|---|
            | 자동차 옆면만 100장 | 앞면·윗면은 못 맞힘 |
            | 큰 글씨만 학습 | 작은 글씨 오인식 |
            | 한 사람 손글씨만 | 다른 사람 글씨 실패 |
            """
        )
        st.warning("수집기 체험에서 '같은 물체를 다양한 각도·크기로' 그리는 이유가 바로 편향을 줄이기 위해서예요!")
        st.markdown("**🧪 시나리오 실습:** 팀 토론 후 답을 골라보세요.")
        _quiz_block(
            "m4",
            "quiz_m4",
            "고양이 정면 사진만 200장 학습했다면, 가장 가능성 높은 문제는?",
            ["고양이 옆모습을 '개'로 착각", "정면 고양이는 잘 맞힘", "그림 생성 속도가 느려짐"],
            0,
            "한 각도/유형만 많으면 **다른 각도**에서 성능이 떨어집니다. 이것이 데이터 편향의 대표 사례예요.",
        )
        st.markdown("**✍️ 한 줄 실습:** 내 팀이 수집기에서 그릴 때 주의할 점 1가지")
        bias_note = st.text_input("예: 크기와 방향을 다양하게 그리기", key="bias_note")
        if st.button("실습 기록 저장", key="bias_note_save"):
            if bias_note.strip():
                st.success(f"기록됨: {bias_note.strip()}")
                _mark_principle_done("m4")
            else:
                st.warning("한 줄이라도 적어주세요!")

    with m5:
        st.markdown("### Colab 실습에 꼭 필요한 코딩 4종")
        st.markdown(
            """
            | 개념 | 역할 | 오늘 쓰는 곳 |
            |---|---|---|
            | **변수** | 값 저장 | `DIVISOR = 255` |
            | **리스트** | 여러 값 묶기 | 클래스 이름 목록 |
            | **함수** | 반복 코드 재사용 | `add_conv_block()` |
            | **for / if** | 반복·조건 | 데이터 처리, 분기 |
            """
        )
        st.code(
            "DIVISOR = 255          # 변수\n"
            "labels = ['cat', 'dog']  # 리스트\n"
            "def normalize(x):      # 함수\n"
            "    return x / DIVISOR\n"
            "for img in images:     # 반복\n"
            "    if img.max() > 1:  # 조건\n"
            "        img = normalize(img)",
            language="python",
        )
        st.markdown("**🧪 빈칸 채우기:** 아래 코드에서 `???`에 들어갈 값은?")
        fill_answer = st.text_input("정답 입력 (숫자만)", key="fill_divisor", placeholder="255")
        if st.button("빈칸 확인", key="fill_check"):
            if fill_answer.strip() == "255":
                st.success("맞아요! 255로 나누면 0~1 범위로 정규화됩니다.")
                _mark_principle_done("m5")
            else:
                st.error("힌트: 픽셀 최대값은 255입니다.")
        st.info("Colab 노트북의 TODO 칸을 채울 때, 위 4가지 개념을 떠올리면 훨씬 수월해요!")

    st.divider()
    if _principle_progress_ratio() >= 1.0:
        st.balloons()
        st.success("🎓 5개 모듈을 모두 완료했어요! 이제 **수집기 체험**으로 데이터 편향을 직접 확인해보세요.")
    else:
        remaining = [k for k, v in st.session_state.principle_done.items() if not v]
        st.caption(f"아직 완료하지 않은 모듈: {', '.join(remaining)} · 각 탭의 퀴즈/실습을 마치면 진행률이 올라갑니다.")

# ------------------------------------------------------------------ 수집기 체험
elif page == "🧩 데이터 학습·편향 (수집기)":
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
elif page == "🖥️ 수업 슬라이드":
    st.markdown('<div class="section-chip">CLASS PRESENTATION</div>', unsafe_allow_html=True)
    st.title("🖥️ 수업 슬라이드")
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
elif page == "📝 학습지 작성·제출":
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
                "classId": WORKSHEET_CLASS_ID,
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
elif page == "🎀 미드저니 아트 만들기":
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
elif page == "💻 Colab으로 퀵드로우 만들기":
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
elif page == "🎤 발표·마무리":
    st.markdown('<div class="section-chip">SHOWCASE TIME</div>', unsafe_allow_html=True)
    st.title("6️⃣ 발표 · 마무리")
    st.subheader("AI가 틀리는 이유를 데이터 관점으로 이야기해봐요")

    slides_html = read_text(SLIDES_FILE)
    if slides_html:
        last_slide_html = slides_html.replace(
            "<body>",
            "<body><script>window.SLIDE_START = 20;</script>",
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
elif page == "📎 참고자료":
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

        현재 앱의 저장 구분 키:
        - 수집기: `classId=collector-submissions-2026`
        - 학습지: `classId=worksheet-submissions-2026`

        확인 방법:
        1. Apps Script 편집기에서 해당 웹앱 프로젝트 열기  
        2. 코드에서 `SpreadsheetApp` 사용 여부 확인  
        3. `openById(...)` 또는 `getActiveSpreadsheet()` 대상 스프레드시트를 Drive에서 열기
        """
    )

st.sidebar.divider()
st.sidebar.caption("© 커스텀 퀵 드로우 수업 · Streamlit")
