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
MANUSCRIPT_FILE = "학생용_개념학습_강의원고_AI이미지기술_2026.pdf"
MANUSCRIPT_LEGACY = "학생용_강의원고_6시간_AISW_퀵드로우_2026.pdf"

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
CURSOR_MAKER_URL = "https://www.cursor.cc/?action=import_request"
FOLDER_ICON_URL = "https://www.icoconverter.com/"
COLLECTOR_FILE = "나만의_퀵드로우_수집기.html"
COLLECTOR_API_URL = "https://script.google.com/macros/s/AKfycbzPP6GHuqSHltZxutD8qyt8-TW_F5HNU1-2jLtkxEMPa-H8ufKdMzbl6GnCC1Lnq3pA/exec"
COLLECTOR_CLASS_ID = "collector-submissions-2026"
WORKSHEET_CLASS_ID = "worksheet-submissions-2026"
GALLERY_CLASS_ID = "gallery-submissions-2026"
SURVEY_CLASS_ID = "satisfaction-survey-2026"
MJ_ACCOUNTS_FILE = BASE / "assets" / "midjourney" / "student_accounts.json"
GALLERY_FILE = BASE / "assets" / "gallery" / "works.json"
GALLERY_IMG_DIR = BASE / "assets" / "gallery" / "images"


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


def load_mj_accounts() -> list[dict]:
    if not MJ_ACCOUNTS_FILE.exists():
        return []
    try:
        return json.loads(MJ_ACCOUNTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def find_mj_account(cohort: str, number: int) -> dict | None:
    for row in load_mj_accounts():
        if str(row.get("cohort")) == str(cohort) and int(row.get("number", -1)) == int(number):
            return row
    return None


def load_gallery_works() -> list[dict]:
    GALLERY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not GALLERY_FILE.exists():
        return []
    try:
        data = json.loads(GALLERY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_gallery_work(item: dict) -> None:
    GALLERY_FILE.parent.mkdir(parents=True, exist_ok=True)
    GALLERY_IMG_DIR.mkdir(parents=True, exist_ok=True)
    works = load_gallery_works()
    works.insert(0, item)
    GALLERY_FILE.write_text(json.dumps(works, ensure_ascii=False, indent=2), encoding="utf-8")


def _init_principle_progress() -> None:
    if "principle_done" not in st.session_state:
        st.session_state.principle_done = {f"m{i}": False for i in range(1, 7)}
    if "_quiz_seed" not in st.session_state:
        st.session_state._quiz_seed = random.randint(1, 10_000_000)


def _mark_principle_done(module_key: str) -> None:
    st.session_state.principle_done[module_key] = True


def _principle_progress_ratio() -> float:
    done = st.session_state.get("principle_done", {})
    if not done:
        return 0.0
    return sum(1 for v in done.values() if v) / len(done)


def _lesson_card(title: str, body: str) -> None:
    st.markdown(
        f'<div class="lesson-card"><h4>{title}</h4><p>{body}</p></div>',
        unsafe_allow_html=True,
    )


def _shuffled_options(quiz_key: str, options: list[str], correct_idx: int) -> tuple[list[str], str]:
    """세션마다 선택지 순서를 섞어 정답이 항상 1번에 오지 않게 함."""
    state_key = f"{quiz_key}_shuffled"
    if state_key not in st.session_state:
        ordered = list(options)
        rng = random.Random(f"{quiz_key}:{st.session_state.get('_quiz_seed', 0)}")
        rng.shuffle(ordered)
        st.session_state[state_key] = ordered
    shuffled = st.session_state[state_key]
    correct_text = options[correct_idx]
    return shuffled, correct_text


def _quiz_block(
    module_key: str,
    quiz_key: str,
    question: str,
    options: list[str],
    correct_idx: int,
    explanation: str,
    *,
    allow_retry: bool = True,
) -> None:
    st.markdown(f"**📝 퀴즈:** {question}")
    shuffled, correct_text = _shuffled_options(quiz_key, options, correct_idx)
    choice = st.radio(
        "정답을 고르세요",
        shuffled,
        key=f"{quiz_key}_choice",
        label_visibility="collapsed",
    )
    if st.button("✅ 정답 확인", key=f"{quiz_key}_check"):
        if choice == correct_text:
            st.success("정답! 🎉")
            st.info(explanation)
            _mark_principle_done(module_key)
        elif allow_retry:
            st.error("아쉽지만 오답이에요. 설명을 다시 읽고 한 번 더 도전해보세요!")
            st.caption(explanation)


def _safe_run_python(code: str) -> tuple[bool, str]:
    """수업용 짧은 파이썬 코드를 안전하게 실행하고 stdout을 반환."""
    import ast
    import io
    from contextlib import redirect_stdout

    banned = ("import ", "open(", "exec(", "eval(", "os.", "sys.", "subprocess", "Path(")
    if "__" in code:
        return False, "보안상 '__' 가 들어간 코드는 실행할 수 없어요."
    lowered = code.lower()
    for token in banned:
        if token.lower() in lowered:
            return False, f"보안상 '{token.strip()}' 는 이 실습에서 사용할 수 없어요."

    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        return False, f"문법 오류: {e.msg}"

    safe_builtins = {
        "print": print,
        "len": len,
        "range": range,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "sorted": sorted,
        "list": list,
        "dict": dict,
        "tuple": tuple,
        "set": set,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "True": True,
        "False": False,
        "None": None,
    }
    stdout = io.StringIO()
    try:
        with redirect_stdout(stdout):
            exec(compile(tree, "<student>", "exec"), {"__builtins__": safe_builtins}, {})
    except Exception as e:  # pragma: no cover - classroom feedback path
        return False, f"실행 오류: {type(e).__name__}: {e}"
    out = stdout.getvalue().rstrip()
    return True, out if out else "(출력 없음)"


CODING_LAB_SNIPPETS: list[dict] = [
    {
        "id": "var_print",
        "title": "① 변수와 print",
        "hint": "변수에 담은 값을 화면에 출력해요.",
        "code": "name = \"퀵드로우\"\nscore = 95\nprint(name)\nprint(score)",
        "predict_options": ["퀵드로우 / 95", "name / score", "에러 발생"],
        "predict_answer": "퀵드로우 / 95",
    },
    {
        "id": "normalize",
        "title": "② 정규화 (÷ 255)",
        "hint": "픽셀 값을 0~1로 바꾸는 계산이에요.",
        "code": "DIVISOR = 255\npixel = 204\nnormalized = pixel / DIVISOR\nprint(round(normalized, 2))",
        "predict_options": ["0.8", "204", "255"],
        "predict_answer": "0.8",
    },
    {
        "id": "list_len",
        "title": "③ 리스트와 len",
        "hint": "여러 값을 묶고 개수를 세어 봐요.",
        "code": "labels = [\"cat\", \"dog\", \"car\"]\nprint(labels[0])\nprint(len(labels))",
        "predict_options": ["cat / 3", "dog / 3", "car / 2"],
        "predict_answer": "cat / 3",
    },
    {
        "id": "for_loop",
        "title": "④ for 반복문",
        "hint": "같은 일을 여러 번 자동으로 반복해요.",
        "code": "nums = [1, 2, 3]\ntotal = 0\nfor n in nums:\n    total = total + n\nprint(total)",
        "predict_options": ["6", "123", "3"],
        "predict_answer": "6",
    },
    {
        "id": "if_else",
        "title": "⑤ if 조건문",
        "hint": "조건에 따라 다른 결과를 출력해요.",
        "code": "acc = 0.92\nif acc >= 0.9:\n    print(\"합격\")\nelse:\n    print(\"재학습\")",
        "predict_options": ["합격", "재학습", "0.92"],
        "predict_answer": "합격",
    },
    {
        "id": "function",
        "title": "⑥ 함수 만들기",
        "hint": "자주 쓰는 계산을 함수로 묶어 재사용해요.",
        "code": "def double(x):\n    return x * 2\n\nprint(double(7))\nprint(double(10))",
        "predict_options": ["14 / 20", "7 / 10", "2 / 2"],
        "predict_answer": "14 / 20",
    },
    {
        "id": "shape_tuple",
        "title": "⑦ 이미지 shape 튜플",
        "hint": "(장수, 높이, 너비, 채널) 순서를 기억해요.",
        "code": "shape = (50, 28, 28, 1)\nprint(shape[0])\nprint(shape[-1])",
        "predict_options": ["50 / 1", "28 / 28", "1 / 50"],
        "predict_answer": "50 / 1",
    },
    {
        "id": "list_comp_lite",
        "title": "⑧ for로 리스트 만들기",
        "hint": "0~255 값을 0~1로 바꾸는 미니 정규화예요.",
        "code": "pixels = [0, 127, 255]\nnorm = []\nfor p in pixels:\n    norm.append(round(p / 255, 2))\nprint(norm)",
        "predict_options": ["[0.0, 0.5, 1.0]", "[0, 127, 255]", "[255, 127, 0]"],
        "predict_answer": "[0.0, 0.5, 1.0]",
    },
]


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
      .lesson-card {
        background: linear-gradient(135deg, #ffffff 0%, #f0f9ff 100%);
        border: 1px solid #93c5fd;
        border-radius: 16px;
        padding: 14px 16px;
        margin-bottom: 10px;
      }
      .lesson-card h4 { color: #7c3aed; margin: 0 0 6px 0; font-size: 15px; }
      .lesson-card p { margin: 0; color: #475569; font-size: 14px; line-height: 1.55; }
      .mission-badge {
        display: inline-block;
        background: #fef3c7;
        color: #b45309;
        border: 1px solid #fcd34d;
        border-radius: 999px;
        padding: 3px 11px;
        font-size: 12px;
        font-weight: 700;
        margin-right: 6px;
      }
      .link-chip {
        display: inline-block;
        background: #ede9fe;
        color: #6d28d9;
        border-radius: 8px;
        padding: 2px 8px;
        font-size: 12px;
        margin-top: 4px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ 사이드바
with st.sidebar:
    st.title("🎨 퀵 드로우 실습")
    st.caption("조대부고 AISW · 하루 수업 흐름")
    page = st.radio(
        "메뉴",
        [
            "🌈 1. OT·쁘띠빠크",
            "🧠 2. AI 원리·퀵드로우",
            "🧩 3. 데이터 편향 실습",
            "🎀 4. 미드저니 아트",
            "💻 5. Colab 퀵드로우",
            "🖼️ 6. 작품 공유·발표",
            "📝 학습지",
            "🖥️ 수업 슬라이드",
            "📎 참고자료",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown("**오늘의 시간표**")
    st.markdown(
        "9:00 OT·쁘띠빠크\n\n"
        "10:00 원리 설명·퀵드로우\n\n"
        "11:00 편향 실습·MJ 계정\n\n"
        "13:00 미드저니 작품 실습\n\n"
        "14:20 Colab 퀵드로우\n\n"
        "15:30 공유·발표·만족도"
    )


# ------------------------------------------------------------------ 도입
if page == "🌈 1. OT·쁘띠빠크":
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
        "왼쪽 메뉴를 시간표 순서대로 진행해보세요: **OT → 원리 → 편향 → 미드저니 → Colab → 공유·발표**"
    )

# ------------------------------------------------------------------ AI·코딩 핵심 원리 (30분 이론+퀴즈)
elif page == "🧠 2. AI 원리·퀵드로우":
    _init_principle_progress()
    st.markdown('<div class="section-chip">AI & CODING CORE · 30 MIN</div>', unsafe_allow_html=True)
    st.title("🧠 AI·코딩 핵심 원리")
    st.caption("약 30분 · 6개 미션 · 교재 핵심 개념 + 퀴즈·실습으로 재미있게 익혀요")
    st.markdown(
        """
        <div class="hero">
          <h3>🎮 AI 탐험대 — 오늘의 미션</h3>
          <p>규칙 AI vs 학습 AI, 이미지 인식(CNN), 데이터 편향, Colab 코딩까지!<br>
          업로드해 주신 교재(파이썬·캐글·합성곱신경망·규칙기반 AI) 핵심을 수업용으로 재구성했어요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(_principle_progress_ratio(), text=f"탐험 진행률 {int(_principle_progress_ratio() * 100)}%")

    m1, m2, m3, m4, m5, m6 = st.tabs(
        [
            "1️⃣ AI 3종류 (5분)",
            "2️⃣ 학습 4단계 (5분)",
            "3️⃣ 이미지 인식 (8분)",
            "4️⃣ 데이터 편향 (5분)",
            "5️⃣ 결과 분석 (3분)",
            "6️⃣ 코딩 기초 (4분)",
        ]
    )

    with m1:
        st.markdown("### 🤖 AI는 '방식'마다 다르게 일해요")
        _lesson_card(
            "📏 규칙기반 AI (Rule-based)",
            "사람이 <b>IF ~ THEN ~</b> 규칙을 직접 적어 둡니다.<br>"
            "예: <i>IF 동그라미 모양 THEN 고양이</i> → 규칙에 없는 그림은 못 맞춤.<br>"
            "늑대·염소·양배추 문제처럼 <b>정해진 규칙</b>으로 푸는 방식이에요.",
        )
        _lesson_card(
            "📚 학습형 AI (Machine Learning)",
            "사람이 규칙을 다 적지 않고, <b>데이터를 많이 보여주면</b> AI가 스스로 패턴을 찾아요.<br>"
            "오늘 만드는 <b>퀵드로우</b>, Teachable Machine(개/고양이 분류)이 여기에 해당!",
        )
        _lesson_card(
            "🎨 생성형 AI (Generative)",
            "글(프롬프트)을 넣으면 <b>새로운 그림·글</b>을 만들어 줍니다.<br>"
            "오늘 쓰는 <b>미드저니</b>가 대표예요. (Stable Diffusion도 같은 계열)",
        )
        st.markdown(
            """
            | AI 종류 | 입력 | 출력 | 오늘 수업 예시 |
            |---|---|---|---|
            | 규칙기반 | 상황·조건 | IF-THEN 답 | (개념 이해용) |
            | 학습형(분류) | 그림/사진 | 이름(라벨) | 퀵드로우, 수집기 |
            | 생성형 | 글(프롬프트) | 새 이미지 | 미드저니 |
            """
        )
        st.markdown('<span class="mission-badge">미션 1</span> 아래 퀴즈를 풀어보세요!', unsafe_allow_html=True)
        _quiz_block(
            "m1",
            "quiz_m1",
            "Teachable Machine에 개·고양이 사진 10장씩 넣고 'Train'을 누르면?",
            [
                "데이터를 보고 개/고양이를 구분하는 AI가 만들어진다",
                "미드저니처럼 새 고양이 그림이 생성된다",
                "IF-THEN 규칙 100개가 자동으로 작성된다",
            ],
            0,
            "Teachable Machine은 **학습형(분류) AI**입니다. 데이터로 패턴을 익혀 '이건 개! 이건 고양이!'라고 맞춥니다.",
        )

    with m2:
        st.markdown("### 🔄 AI가 똑똑해지는 4단계 + 시험 보는 법")
        s1, s2, s3, s4 = st.columns(4)
        s1.success("**1. 데이터**\n\n교과서=학습용 그림")
        s2.success("**2. 학습**\n\n패턴 익히기")
        s3.success("**3. 모델**\n\n시험 전 두뇌")
        s4.success("**4. 추론**\n\n새 그림 맞히기")
        _lesson_card(
            "⚠️ 학습 ≠ 암기!",
            "캐글 타이타닉 대회처럼, AI는 <b>train(학습용)</b> 데이터로 공부하고 "
            "<b>test(시험용)</b> 데이터로 <b>일반화</b>를 확인해요.<br>"
            "학습 데이터만 외우면 → 새 그림·새 상황에서 바로 틀립니다.",
        )
        st.markdown(
            """
            | 단계 | 쉬운 비유 | 오늘 수업 |
            |---|---|---|
            | 데이터 | 문제집 모으기 | 수집기에서 낙서 그리기 |
            | 학습 | 문제 풀며 패턴 찾기 | Colab `model.fit()` |
            | 모델 | 시험 전 정리된 두뇌 | 학습 완료된 CNN |
            | 추론 | 실전 시험 | 펜마우스로 그려서 테스트 |
            """
        )
        st.markdown("**🧪 미니 실습 ①:** 4단계 순서 맞추기")
        order_pick = st.multiselect(
            "순서대로 선택 (1→2→3→4)",
            ["추론", "데이터", "학습", "모델"],
            default=[],
            key="order_practice",
        )
        if st.button("순서 확인", key="order_check"):
            if order_pick == ["데이터", "학습", "모델", "추론"]:
                st.success("완벽! AI는 항상 데이터 → 학습 → 모델 → 추론 순서예요.")
            else:
                st.warning(f"현재: {' → '.join(order_pick) if order_pick else '(없음)'} · 정답: 데이터 → 학습 → 모델 → 추론")

        st.markdown("**🧪 미니 실습 ②:** train / test 역할 고르기")
        split_options = [
            "80장=train(학습), 20장=test(시험) — 맞는 방법!",
            "20장=train, 80장=test — 반대로 해야 한다",
            "100장 전부 train — 시험은 필요 없다",
        ]
        split_shuffled, split_correct = _shuffled_options("quiz_m2_split", split_options, 0)
        split_choice = st.radio(
            "수집기에서 80장 그리고, 처음 보는 20장으로 테스트한다면?",
            split_shuffled,
            key="split_choice",
        )
        if st.button("train/test 확인", key="split_check"):
            if split_choice == split_correct:
                st.success("정답! 새 데이터로 테스트해야 '진짜 실력'을 알 수 있어요.")
                _mark_principle_done("m2")
            else:
                st.error("힌트: 대부분은 학습용, 일부는 처음 보는 그림으로 시험봐요.")

    with m3:
        st.markdown("### 👁️ 컴퓨터는 그림을 '숫자'로 봐요")
        _lesson_card(
            "🔢 픽셀 & 정규화",
            "그림 = 작은 사각형(픽셀)의 모음. 각 픽셀 밝기는 <b>0~255</b>.<br>"
            "학습 전 <b>÷ 255</b>로 0~1로 바꾸면 AI가 더 안정적으로 공부해요. (Colab의 <code>DIVISOR = 255</code>)",
        )
        _lesson_card(
            "🔍 합성곱(Convolution) — 3×3 돋보기",
            "3×3 작은 필터를 그림 위에서 슬라이드하며 <b>선·곡선·에지</b>를 찾아요.<br>"
            "딥러닝 CNN의 Conv2D 층이 바로 이 역할! (교재 7장 합성곱 신경망)",
        )
        st.code(
            "# MNIST·퀵드로우 공통: 28×28 흑백\n"
            "x = image.reshape(-1, 28, 28, 1)  # (장수, 높이, 너비, 채널)\n"
            "x = x / 255.0                     # 0~1 정규화\n"
            "# Conv2D → MaxPooling → Flatten → Dense → '고양이!'",
            language="python",
        )
        st.markdown(
            """
            **CNN 레이어 — 게임 캐릭터 스킬 트리 🎮**
            | 레이어 | 하는 일 | 게임 비유 |
            |---|---|---|
            | Conv2D | 선·모양 특징 찾기 | 🔍 탐색 스킬 |
            | MaxPooling | 중요 정보만 남기기 | 🗜️ 압축 스킬 |
            | Flatten + Dense | 최종 답 고르기 | 🎯 필살기 |
            """
        )
        st.caption("참고: [Teachable Machine](https://teachablemachine.withgoogle.com) · 에포크·배치 크기 조절도 가능!")
        _quiz_block(
            "m3",
            "quiz_m3",
            "28×28 흑백 그림 50장을 CNN에 넣을 때 올바른 shape는?",
            ["(50, 28, 28, 1)", "(50, 28, 28)", "(28, 28, 50)", "(1, 50, 28, 28)"],
            0,
            "N=50장, 28×28 크기, 채널=1(흑백) → **(50, 28, 28, 1)**. Colab TODO에서 shape를 채울 때 기억하세요!",
        )

    with m4:
        st.markdown("### ⚖️ 데이터 편향 — AI가 특정 그림만 잘 맞히는 이유")
        _lesson_card(
            "🚗 수집기 실험과 연결",
            "자동차 <b>옆면만</b> 100장 → 앞면·윗면은 못 맞힘.<br>"
            "Teachable Machine에서 <b>정면 고양이만</b> 200장 → 옆모습 고양이는 '개'로 오인식.<br>"
            "→ <b>데이터가 한쪽으로 치우치면</b> AI도 한쪽만 잘 봐요!",
        )
        st.markdown(
            """
            | 편향 상황 | AI가 겪는 문제 | 해결 방법 |
            |---|---|---|
            | 한 각도만 많음 | 다른 각도 오인식 | 크기·방향·위치 다양하게 |
            | 한 사람 그림만 | 다른 사람 그림 실패 | 여러 명이 함께 그리기 |
            | 배경이 항상 같음 | 배경 바뀌면 실패 | 다양한 위치에 그리기 |
            """
        )
        st.markdown("**🧪 팀 토론 실습:** 시나리오를 읽고 가장 좋은 해결책을 고르세요.")
        _quiz_block(
            "m4",
            "quiz_m4",
            "팀원 4명 모두 '옆모습 자동차'만 그렸다. AI가 앞모습을 못 맞힌다면?",
            [
                "다양한 각도·크기로 추가 데이터를 더 수집한다",
                "에포크를 1000으로 늘린다",
                "미드저니로 배경만 바꾼다",
            ],
            0,
            "정답은 **데이터 다양성**! 에포크를 늘려도 편향된 데이터면 근본 해결이 어려워요.",
        )
        st.markdown("**✍️ 우리 팀 다짐 한 줄**")
        bias_note = st.text_input("수집기에서 지킬 규칙 1가지", key="bias_note", placeholder="예: 3가지 크기 + 2가지 방향으로 그리기")
        if st.button("다짐 기록", key="bias_note_save"):
            if bias_note.strip():
                st.success(f"📝 기록됨: {bias_note.strip()}")
                _mark_principle_done("m4")
            else:
                st.warning("한 줄이라도 적어주세요!")

    with m5:
        st.markdown("### 📊 정확도만 보면 속을 수 있어요 — Confusion Matrix")
        _lesson_card(
            "🎯 Confusion Matrix란?",
            "AI가 <b>정답(타깃)</b> vs <b>예측(출력)</b>을 표로 정리한 것.<br>"
            "대각선 = 맞힌 횟수. 대각선 밖 = 틀린 횟수.<br>"
            "교재 7장: 정확도 90%여도 <b>특정 클래스끼리만</b> 헷갈릴 수 있어요!",
        )
        st.markdown(
            """
            **예시:** 3-class 분류, 둘 다 정확도 90%
            - **모델 A**: 에러가 골고루 → 전반적으로 보통
            - **모델 B**: A↔B 사이에만 에러 집중 → **A와 B 데이터를 더 다양하게** 모으면 크게 개선!

            👉 오늘 수집기에서 "어떤 모양끼리 헷갈리는지" 기록하면 Confusion Matrix 분석과 같아요!
            """
        )
        st.markdown("**🧪 퀴즈:** Confusion Matrix 해석")
        _quiz_block(
            "m5",
            "quiz_m5",
            "정확도 85%인데 '고양이→개' 오인식만 집중된다면 가장 효과적인 조치는?",
            [
                "고양이·개 그림을 더 다양한 각도로 추가 수집",
                "학습 에포크를 0으로 줄인다",
                "프롬프트에 'cute'를 더 넣는다",
            ],
            0,
            "Confusion Matrix에서 **특정 쌍**에 오류가 몰리면, 그 클래스의 **데이터를 더 다양하게** 모으는 게 핵심!",
        )

    with m6:
        st.markdown("### 💻 코딩 기초 랩 — 예측하고, 바로 실행해 보세요!")
        _lesson_card(
            "📚 라이브러리 = 도서관 책 이름표",
            "numpy(배열), pandas(표), keras(CNN)처럼 <b>미리 만들어 둔 코드 묶음</b>이에요.<br>"
            "<code>import numpy as np</code> → 도서관에서 'numpy' 책 꺼내 쓰기!",
        )
        st.markdown(
            """
            | 개념 | 역할 | Colab에서 쓰는 곳 |
            |---|---|---|
            | **변수** | 값 저장 | `DIVISOR = 255` |
            | **리스트** | 여러 값 묶기 | `labels = ['cat','dog']` |
            | **함수** | 반복 코드 재사용 | `add_conv_block()` |
            | **for / if** | 반복·조건 분기 | 데이터 처리, 정규화 |
            """
        )
        st.info("아래 8개 예제를 순서대로: **① 결과 예측 → ② 실행 버튼 → ③ 실제 출력 확인** 해 보세요!")

        if "coding_lab_solved" not in st.session_state:
            st.session_state.coding_lab_solved = set()

        for snippet in CODING_LAB_SNIPPETS:
            sid = snippet["id"]
            with st.expander(snippet["title"], expanded=(sid == "var_print")):
                st.caption(snippet["hint"])
                code_key = f"lab_code_{sid}"
                reset_flag = f"lab_reset_flag_{sid}"
                # 위젯 생성 전에 복원 플래그 적용 (생성 후 같은 key 수정 시 Streamlit 오류)
                if st.session_state.pop(reset_flag, False):
                    st.session_state[code_key] = snippet["code"]
                if code_key not in st.session_state:
                    st.session_state[code_key] = snippet["code"]
                edited = st.text_area(
                    "코드",
                    height=140,
                    key=code_key,
                    label_visibility="collapsed",
                )

                pred_opts, pred_correct = _shuffled_options(
                    f"lab_pred_{sid}",
                    snippet["predict_options"],
                    snippet["predict_options"].index(snippet["predict_answer"]),
                )
                predict = st.radio(
                    "이 코드를 실행하면 어떤 결과가 나올까요?",
                    pred_opts,
                    key=f"lab_predict_{sid}",
                )
                c_pred, c_run, c_reset = st.columns(3)
                with c_pred:
                    if st.button("🔮 예측 확인", key=f"lab_pred_btn_{sid}"):
                        if predict == pred_correct:
                            st.success("예측 성공! 이제 실행해서 확인해 보세요.")
                            st.session_state.coding_lab_solved.add(f"{sid}_pred")
                        else:
                            st.error("다시 코드를 천천히 읽어 보세요.")
                with c_run:
                    if st.button("▶️ 실행", key=f"lab_run_btn_{sid}", type="primary"):
                        ok, result = _safe_run_python(edited)
                        if ok:
                            st.code(result, language="text")
                            st.session_state.coding_lab_solved.add(f"{sid}_run")
                            joined = " / ".join(line for line in result.splitlines() if line.strip())
                            if joined == snippet["predict_answer"] or result == snippet["predict_answer"]:
                                st.caption("실행 결과가 예측 정답과 잘 맞아요!")
                        else:
                            st.error(result)
                with c_reset:
                    if st.button("↺ 원본 복원", key=f"lab_reset_btn_{sid}"):
                        st.session_state[reset_flag] = True
                        st.rerun()

        solved_runs = sum(1 for s in CODING_LAB_SNIPPETS if f"{s['id']}_run" in st.session_state.coding_lab_solved)
        solved_preds = sum(1 for s in CODING_LAB_SNIPPETS if f"{s['id']}_pred" in st.session_state.coding_lab_solved)
        st.progress(
            (solved_runs + solved_preds) / (len(CODING_LAB_SNIPPETS) * 2),
            text=f"코딩 랩 진행: 예측 {solved_preds}/{len(CODING_LAB_SNIPPETS)} · 실행 {solved_runs}/{len(CODING_LAB_SNIPPETS)}",
        )
        if solved_runs >= 4 and solved_preds >= 4:
            _mark_principle_done("m6")
            st.success("미션 6 클리어! 변수·리스트·함수·반복·조건을 직접 돌려 봤어요.")
        else:
            st.caption("힌트: 예측 4개 + 실행 4개 이상 성공하면 미션 완료로 체크돼요.")

        st.info("Colab 노트북 TODO 칸을 채울 때: 변수 → 함수 → for/if 순서로 떠올려 보세요!")

    st.divider()
    done_count = sum(1 for v in st.session_state.principle_done.values() if v)
    st.markdown(f"**완료한 미션:** {done_count} / 6")
    if _principle_progress_ratio() >= 1.0:
        st.balloons()
        st.success("🎓 6개 미션 클리어! 이제 **수집기 체험**으로 데이터 편향을 직접 실험해 보세요.")
    else:
        remaining = [k.replace("m", "미션 ") for k, v in st.session_state.principle_done.items() if not v]
        st.caption(f"남은 미션: {', '.join(remaining)} · 각 탭의 퀴즈/실습을 완료하면 진행률이 올라갑니다.")

# ------------------------------------------------------------------ 수집기 체험
elif page == "🧩 3. 데이터 편향 실습":
    st.markdown('<div class="section-chip">DATA BIAS LAB</div>', unsafe_allow_html=True)
    st.title("🧩 데이터 편향 실습 (수집기)")
    st.caption("수집기로 편향 체험 → 이어서 미드저니 계정·사용법 안내")
    st.info("이 활동 뒤에는 **4. 미드저니 아트** 탭의 「내 계정 찾기」「사용법 안내」로 이동하세요.")
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
elif page == "📝 학습지":
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
elif page == "🎀 4. 미드저니 아트":
    st.markdown('<div class="section-chip">MIDJOURNEY CREATOR</div>', unsafe_allow_html=True)
    st.title("🖌️ 미드저니로 나만의 디지털 아트 만들기")
    st.markdown(
        "미드저니는 **글(프롬프트)을 쓰면 그림을 만들어 주는 AI**예요. "
        "오늘은 **내 노트북을 나만의 스타일로 꾸미는** 작품을 만들어 봅시다!"
    )

    tab_account, tab_guide, tab_make = st.tabs(
        ["🔑 내 계정 찾기", "📖 사용법 안내", "✨ 프롬프트·작품 만들기"]
    )

    with tab_account:
        st.subheader("조대부고 7기·8기 학생용 계정")
        st.info("본인 **기수**와 **번호**를 입력하면 이메일·비밀번호가 나타납니다. 다른 사람 계정은 사용하지 마세요!")
        c1, c2 = st.columns(2)
        with c1:
            cohort = st.selectbox("기수", ["7", "8"], format_func=lambda x: f"{x}기", key="mj_cohort")
        with c2:
            number = st.number_input("내 번호", min_value=1, max_value=20, value=1, step=1, key="mj_number")
        if st.button("내 계정 보기", type="primary", key="mj_lookup"):
            acc = find_mj_account(str(cohort), int(number))
            if not acc:
                st.error("해당 번호의 계정을 찾지 못했어요. 기수·번호를 다시 확인해주세요.")
            else:
                st.success(f"{acc['label']} 계정입니다.")
                st.markdown("**이메일**")
                st.code(acc["email"], language="text")
                st.markdown("**비밀번호**")
                st.code(acc["password"], language="text")
                st.caption("로그인 후 Discord/Midjourney 안내에 따라 사용하세요. 비밀번호를 바꾸지 말아 주세요.")
        st.link_button("🎨 미드저니 열기", MIDJOURNEY_URL, type="secondary")

    with tab_guide:
        st.subheader("미드저니 사용법 + 노트북 커스터마이징")
        st.markdown(
            """
            ### 1) 접속·로그인
            1. **내 계정 찾기** 탭에서 이메일·비밀번호 확인
            2. [미드저니](https://www.midjourney.com/imagine) 접속 후 로그인
            3. 처음이면 Discord 연동/약관 안내에 따라 진행

            ### 2) 그림 만들기 (`/imagine`)
            1. 입력창에 **프롬프트(영어 설명)** 붙여넣기
            2. 생성되면 이미지 4장이 한 세트로 나옵니다
            3. 마음에 드는 장을 고르고 **확대(U)** / **변형(V)** 사용
            4. 완성 이미지를 **다운로드**

            ### 3) 오늘 미션 — 내 노트북 꾸미기 🎒
            | 작품 | 어디에 쓰나요? | 비율 |
            |---|---|---|
            | 노트북 바탕화면 | Windows/Mac 배경화면 | 16:9 |
            | 프로필 사진 | 구글·인스타 프로필 | 1:1 |
            | 마우스 커서 아이콘 | 커서 파일로 변환 후 적용 | 1:1 |
            | 폴더 아이콘 | ICO로 변환 후 폴더에 적용 | 1:1 |

            ### 4) 적용 방법 (간단)
            - **바탕화면**: 다운로드 → 우클릭 → 배경으로 설정
            - **프로필**: 구글/인스타 설정에서 사진 변경
            - **마우스 커서**: 투명 배경 PNG 생성 → [cursor.cc](https://www.cursor.cc/?action=import_request)에서 커서 파일로 변환
            - **폴더 아이콘**: PNG 생성 → [icoconverter.com](https://www.icoconverter.com/)에서 `.ico` 변환 후 폴더 아이콘으로 지정

            ### 5) 수업 팁
            - Fast 시간이 제한될 수 있어요 → **꼭 필요한 4~6장만** 생성
            - 커서/폴더 아이콘은 **단순·선명·투명 배경**이 중요해요
            - 완성 작품은 **6. 작품 공유·발표** 탭에 올려 친구들과 나눠요
            """
        )
        l1, l2 = st.columns(2)
        with l1:
            st.link_button("🖱️ 마우스 커서 제작", CURSOR_MAKER_URL, type="primary")
        with l2:
            st.link_button("📁 폴더 아이콘 제작", FOLDER_ICON_URL, type="primary")

    with tab_make:
        st.subheader("✨ 프롬프트 자동 만들기")
        st.caption("만들고 싶은 용도를 고르면, 그에 맞는 영어 프롬프트가 자동으로 만들어져요!")
        st.link_button("🎨 미드저니 열기", MIDJOURNEY_URL, type="primary")

        purpose_presets = {
            "노트북 바탕화면": {
                "hint": "desktop wallpaper, wide landscape composition, no text, high resolution",
                "ratio": "16:9 (가로)",
                "extras_default": ["simple", "high detail"],
                "subject_default": "cozy desk with plants and soft light",
                "tip": "16:9로 만들고 노트북 배경화면으로 설정해 보세요.",
                "tool": None,
            },
            "구글·인스타 프로필": {
                "hint": "profile picture avatar, centered face or character, circular crop friendly, clean background",
                "ratio": "1:1 (정사각)",
                "extras_default": ["simple", "white background", "kawaii"],
                "subject_default": "cute cat face",
                "tip": "1:1 정사각으로 만들고 구글/인스타 프로필에 올려 보세요.",
                "tool": None,
            },
            "마우스 커서 아이콘": {
                "hint": "mouse cursor icon, single small icon, transparent background, crisp edges, minimal, no shadow clutter",
                "ratio": "1:1 (정사각)",
                "extras_default": ["simple", "minimal", "white background"],
                "subject_default": "pixel arrow cursor with star tip",
                "tip": "단순하고 선명한 아이콘으로 만든 뒤, 아래 링크로 커서 파일을 만드세요.",
                "tool": ("🖱️ 마우스 커서 제작 바로가기", CURSOR_MAKER_URL),
            },
            "폴더 아이콘": {
                "hint": "folder icon, app icon style, centered, transparent background, crisp vector edges",
                "ratio": "1:1 (정사각)",
                "extras_default": ["simple", "minimal", "logo"],
                "subject_default": "pastel folder with cat sticker",
                "tip": "아이콘을 만든 뒤 ICO로 변환해 폴더에 적용해 보세요.",
                "tool": ("📁 폴더 아이콘 제작 바로가기", FOLDER_ICON_URL),
            },
            "게임 마스코트": {
                "hint": "mascot character, full body, cute",
                "ratio": "1:1 (정사각)",
                "extras_default": ["simple", "white background", "mascot"],
                "subject_default": "cat",
                "tip": "퀵드로우 게임 정답 캐릭터로도 쓸 수 있어요.",
                "tool": None,
            },
            "직접 입력": {
                "hint": "",
                "ratio": "1:1 (정사각)",
                "extras_default": ["simple"],
                "subject_default": "cat",
                "tip": "원하는 용도에 맞게 키워드를 자유롭게 조합해 보세요.",
                "tool": None,
            },
        }

        purpose = st.selectbox(
            "무엇을 만들까요?",
            list(purpose_presets.keys()),
            key="mj_purpose",
        )
        preset = purpose_presets[purpose]
        st.info(f"💡 {preset['tip']}")
        if preset["tool"]:
            st.link_button(preset["tool"][0], preset["tool"][1], type="secondary")

        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input(
                "주제 / 모티프 (영어로 쓰면 더 잘 돼요)",
                value=preset["subject_default"],
                help="예: cute fox, neon city, my initials 'DK' ...",
                key=f"mj_subject_{purpose}",
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
                key=f"mj_style_{purpose}",
            )

        col3, col4 = st.columns(2)
        with col3:
            color = st.selectbox(
                "색감/분위기",
                ["pastel colors", "vivid colors", "bright and cheerful", "black and white", "neon"],
                key=f"mj_color_{purpose}",
            )
        with col4:
            ratio_options = ["1:1 (정사각)", "16:9 (가로)", "9:16 (세로)"]
            default_ratio_idx = ratio_options.index(preset["ratio"]) if preset["ratio"] in ratio_options else 0
            ratio = st.selectbox(
                "그림 비율 (--ar)",
                ratio_options,
                index=default_ratio_idx,
                key=f"mj_ratio_{purpose}",
            )

        extras = st.multiselect(
            "추가 옵션 (선택)",
            [
                "simple",
                "minimal",
                "white background",
                "transparent background",
                "kawaii",
                "logo",
                "mascot",
                "high detail",
                "no text",
                "centered",
            ],
            default=preset["extras_default"],
            key=f"mj_extras_{purpose}",
        )

        personal = st.text_input(
            "나만의 키워드 (선택)",
            placeholder="예: my name initial D, favorite color mint, soft glow",
            key=f"mj_personal_{purpose}",
        )

        ratio_code = {"1:1 (정사각)": "1:1", "16:9 (가로)": "16:9", "9:16 (세로)": "9:16"}[ratio]
        parts = [subject.strip(), preset["hint"], style, color, personal.strip()] + extras
        # 커서/폴더 아이콘은 투명·선명 강조
        if purpose in {"마우스 커서 아이콘", "폴더 아이콘"}:
            parts += ["icon only", "no watermark"]
        prompt_text = ", ".join([p for p in parts if p]).strip(", ")
        prompt_text = f"{prompt_text} --ar {ratio_code}"

        st.markdown("**👇 이 프롬프트를 복사해서 미드저니에 붙여넣으세요**")
        st.code(prompt_text, language="text")

        st.markdown(
            f"""
            ### 💡 실습 순서
            1. **내 계정 찾기**로 로그인
            2. 위 프롬프트를 복사해 `/imagine`에 붙여넣기
            3. 마음에 드는 그림 다운로드
            4. {"커서/폴더 변환 링크로 파일 만들기" if purpose in {"마우스 커서 아이콘", "폴더 아이콘"} else "내 노트북·프로필에 바로 적용"}
            5. **6. 작품 공유·발표** 탭에 업로드
            """
        )

        with st.expander("📌 용도별 추천 프롬프트 예시 보기"):
            st.markdown(
                """
                - **바탕화면**: `aurora night sky over quiet mountains, desktop wallpaper, wide landscape, no text, pastel colors --ar 16:9`
                - **프로필**: `cute fox avatar, centered face, circular crop friendly, clean pastel background --ar 1:1`
                - **마우스 커서**: `pixel star cursor icon, transparent background, crisp edges, minimal, icon only --ar 1:1`
                - **폴더 아이콘**: `pastel folder icon with cat sticker, app icon style, transparent background, vector --ar 1:1`
                """
            )

# ------------------------------------------------------------------ 실습
elif page == "💻 5. Colab 퀵드로우":
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

# ------------------------------------------------------------------ 작품 공유·발표·만족도
elif page == "🖼️ 6. 작품 공유·발표":
    st.markdown('<div class="section-chip">SHOWCASE · SURVEY</div>', unsafe_allow_html=True)
    st.title("🖼️ 작품 공유 · 발표 · 만족도")
    st.caption("친구 작품을 보고, 발표하고, 오늘 수업을 남겨 주세요")

    share_tab, gallery_tab, talk_tab, survey_tab = st.tabs(
        ["📤 내 작품 올리기", "👀 친구 작품 보기", "🎤 발표 질문", "😊 만족도 조사"]
    )

    with share_tab:
        st.subheader("내 작품 공유하기")
        st.markdown("미드저니 이미지 또는 Colab 결과 화면을 올려 친구들과 나눠 보세요.")
        with st.form("gallery_submit_form", clear_on_submit=True):
            g_cohort = st.selectbox("기수", ["7기", "8기"], key="gal_cohort")
            g_number = st.number_input("번호", min_value=1, max_value=20, value=1, key="gal_num")
            g_name = st.text_input("닉네임/이름 (선택)", placeholder="예: 다은")
            g_kind = st.selectbox(
                "작품 종류",
                ["노트북 바탕화면", "프로필 사진", "마우스 커서", "폴더 아이콘", "게임 마스코트", "Colab 퀵드로우", "기타"],
            )
            g_title = st.text_input("작품 제목", placeholder="예: 민트빛 고양이 프로필")
            g_desc = st.text_area("한 줄 설명", placeholder="어떤 프롬프트/아이디어였나요?")
            g_url = st.text_input("이미지 링크 (선택)", placeholder="https://...")
            g_file = st.file_uploader("이미지 파일 업로드 (png/jpg)", type=["png", "jpg", "jpeg", "webp"])
            submitted = st.form_submit_button("공유하기", type="primary")

        if submitted:
            if not g_title.strip():
                st.warning("작품 제목을 적어 주세요.")
            else:
                image_path = ""
                if g_file is not None:
                    GALLERY_IMG_DIR.mkdir(parents=True, exist_ok=True)
                    safe_name = f"{g_cohort}_{int(g_number)}_{datetime.now(timezone.utc).strftime('%H%M%S')}_{g_file.name}"
                    out = GALLERY_IMG_DIR / safe_name
                    out.write_bytes(g_file.getvalue())
                    image_path = str(out.relative_to(BASE))
                item = {
                    "id": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"),
                    "cohort": g_cohort,
                    "number": int(g_number),
                    "name": g_name.strip() or f"{g_cohort} {int(g_number)}번",
                    "kind": g_kind,
                    "title": g_title.strip(),
                    "desc": g_desc.strip(),
                    "url": g_url.strip(),
                    "image_path": image_path,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                save_gallery_work(item)
                post_json(
                    COLLECTOR_API_URL,
                    {
                        "classId": GALLERY_CLASS_ID,
                        "type": "gallery",
                        **{k: v for k, v in item.items() if k != "image_path"},
                        "hasImage": bool(image_path),
                    },
                )
                st.success("작품이 갤러리에 올라갔어요! '친구 작품 보기'에서 확인하세요.")
                st.balloons()

    with gallery_tab:
        st.subheader("친구들의 작품 갤러리")
        works = load_gallery_works()
        if not works:
            st.info("아직 올라온 작품이 없어요. 먼저 '내 작품 올리기'에서 공유해 보세요!")
        else:
            filter_kind = st.multiselect(
                "종류 필터",
                ["노트북 바탕화면", "프로필 사진", "마우스 커서", "폴더 아이콘", "게임 마스코트", "Colab 퀵드로우", "기타"],
                default=[],
            )
            shown = [w for w in works if not filter_kind or w.get("kind") in filter_kind]
            st.caption(f"총 {len(shown)}개")
            cols = st.columns(2)
            for i, w in enumerate(shown):
                with cols[i % 2]:
                    st.markdown(f"**{w.get('title', '(제목 없음)')}**")
                    st.caption(f"{w.get('name', '')} · {w.get('kind', '')}")
                    if w.get("desc"):
                        st.write(w["desc"])
                    img_rel = w.get("image_path") or ""
                    img_abs = BASE / img_rel if img_rel else None
                    if img_abs and img_abs.exists():
                        st.image(str(img_abs), use_container_width=True)
                    elif w.get("url"):
                        st.markdown(f"[이미지 링크 열기]({w['url']})")
                        if str(w["url"]).lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                            st.image(w["url"], use_container_width=True)
                    st.divider()

    with talk_tab:
        st.subheader("발표하며 이야기해 보기")
        slides_html = read_text(SLIDES_FILE)
        if slides_html:
            last_slide_html = slides_html.replace(
                "<body>",
                "<body><script>window.SLIDE_START = 20;</script>",
                1,
            )
            st.caption("발표용 질문 슬라이드")
            components.html(last_slide_html, height=480, scrolling=False)
        st.markdown(
            """
            - 오늘 만든 작품 중 가장 마음에 드는 것은?
            - AI가 잘 못 맞힌 그림은 무엇이었나요?
            - 학습 데이터가 한쪽으로 치우치면 어떤 일이 생길까요?
            - 미드저니 프롬프트에서 **한 단어**를 바꿨더니 어떻게 달라졌나요?
            """
        )

    with survey_tab:
        st.subheader("오늘 수업 만족도 조사")
        with st.form("satisfaction_form"):
            s_cohort = st.selectbox("기수", ["7기", "8기"], key="sv_cohort")
            s_number = st.number_input("번호", min_value=1, max_value=20, value=1, key="sv_num")
            s_score = st.slider("전반적 만족도", 1, 5, 4)
            s_fun = st.slider("재미있었나요?", 1, 5, 4)
            s_learn = st.slider("AI·코딩 개념이 이해됐나요?", 1, 5, 4)
            s_best = st.selectbox(
                "가장 좋았던 활동",
                ["쁘띠빠크", "AI 원리 퀴즈", "수집기(편향)", "미드저니", "Colab", "작품 공유"],
            )
            s_comment = st.text_area("남기고 싶은 말 (선택)")
            s_ok = st.form_submit_button("제출하기", type="primary")
        if s_ok:
            payload = {
                "classId": SURVEY_CLASS_ID,
                "type": "satisfaction",
                "cohort": s_cohort,
                "number": int(s_number),
                "score": int(s_score),
                "fun": int(s_fun),
                "learn": int(s_learn),
                "best": s_best,
                "comment": s_comment.strip(),
                "submittedAt": datetime.now(timezone.utc).isoformat(),
            }
            ok, msg = post_json(COLLECTOR_API_URL, payload)
            # local backup
            survey_file = BASE / "assets" / "gallery" / "surveys.json"
            try:
                surveys = json.loads(survey_file.read_text(encoding="utf-8")) if survey_file.exists() else []
            except Exception:
                surveys = []
            surveys.append(payload)
            survey_file.write_text(json.dumps(surveys, ensure_ascii=False, indent=2), encoding="utf-8")
            if ok:
                st.success("제출 완료! 오늘 수고했어요 🎓")
            else:
                st.success("로컬에 저장했어요. (원격 전송은 잠시 후 다시 시도될 수 있어요)")
                st.caption(msg[:160])

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
    st.markdown("### 📘 학생용 개념 학습 슬라이드 (60장)")
    st.caption("실습 절차 제외 · AI·코딩·데이터 편향 개념 정리 · 16:9 슬라이드형 PDF")
    ms_path = BASE / MANUSCRIPT_FILE
    if not ms_path.exists():
        ms_path = BASE / MANUSCRIPT_LEGACY
    if ms_path.exists():
        from datetime import datetime

        mtime = datetime.fromtimestamp(ms_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        size_mb = ms_path.stat().st_size / (1024 * 1024)
        st.caption(f"파일: {ms_path.name} · {size_mb:.1f}MB · 최종 갱신 {mtime}")
        st.download_button(
            "⬇️ 개념 학습 슬라이드 PDF",
            data=ms_path.read_bytes(),
            file_name=ms_path.name,
            mime="application/pdf",
            type="primary",
        )
    else:
        st.info("강의원고 PDF 파일이 저장소에 없습니다.")

    st.divider()
    st.markdown("### 📦 저장 위치 확인(수집기/학습지 제출)")
    st.markdown(
        """
        현재 제출은 **Google Drive 폴더 파일**이 아니라, 연결된 **Apps Script의 저장소(대부분 Google 스프레드시트)**로 들어갑니다.

        현재 앱의 저장 구분 키:
        - 수집기: `classId=collector-submissions-2026`
        - 학습지: `classId=worksheet-submissions-2026`
        - 작품 공유: `classId=gallery-submissions-2026`
        - 만족도: `classId=satisfaction-survey-2026`

        확인 방법:
        1. Apps Script 편집기에서 해당 웹앱 프로젝트 열기  
        2. 코드에서 `SpreadsheetApp` 사용 여부 확인  
        3. `openById(...)` 또는 `getActiveSpreadsheet()` 대상 스프레드시트를 Drive에서 열기
        """
    )

st.sidebar.divider()
st.sidebar.caption("© 커스텀 퀵 드로우 수업 · Streamlit")
