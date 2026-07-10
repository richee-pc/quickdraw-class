#!/usr/bin/env python3
"""6시간 수업용 학생 배포 강의원고 PDF (~70페이지) 생성기."""

from __future__ import annotations

import random
import textwrap
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE = Path(__file__).parent
ASSETS = BASE / "assets" / "manuscript"
FONT_PATH = Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")
OUTPUT = BASE / "학생용_강의원고_6시간_AISW_퀵드로우_2026.pdf"
EXTRACTED = ASSETS / "images" / "extracted"
WEB = ASSETS / "images" / "web"

PAGE_W, PAGE_H = A4
MARGIN = 2.0 * cm


def register_fonts() -> str:
    name = "WQY"
    if name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(name, str(FONT_PATH), subfontIndex=0))
    return name


class ImagePool:
    """교재 추출·웹 이미지를 섹션별로 골고루 배치."""

    def __init__(self) -> None:
        self.extracted = sorted(
            p for p in EXTRACTED.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
        )
        self.web = sorted(WEB.glob("*"))
        random.seed(42)
        random.shuffle(self.extracted)
        self._i = 0
        self._used: set[str] = set()

    def _pick(self, candidates: list[Path], fallback: bool = True) -> Path | None:
        for p in candidates:
            key = str(p)
            if key in self._used:
                continue
            if p.stat().st_size < 4000:
                continue
            self._used.add(key)
            return p
        if fallback and self.extracted:
            while self._i < len(self.extracted):
                p = self.extracted[self._i]
                self._i += 1
                if str(p) not in self._used and p.stat().st_size > 4000:
                    self._used.add(str(p))
                    return p
        return self.web[0] if self.web else None

    def for_section(self, keyword: str) -> Path | None:
        key = keyword.lower()
        hits = [p for p in self.extracted if key in p.name.lower()]
        return self._pick(hits)

    def any_image(self) -> Path | None:
        return self._pick(self.extracted)


def build_styles(font: str):
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "MTitle",
            fontName=font,
            fontSize=22,
            leading=28,
            textColor=colors.HexColor("#1e3a8a"),
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "subtitle": ParagraphStyle(
            "MSubtitle",
            fontName=font,
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#475569"),
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "section": ParagraphStyle(
            "MSection",
            fontName=font,
            fontSize=11,
            leading=14,
            textColor=colors.white,
            backColor=colors.HexColor("#7c3aed"),
            leftIndent=6,
            spaceBefore=4,
            spaceAfter=6,
        ),
        "h1": ParagraphStyle(
            "MH1",
            fontName=font,
            fontSize=16,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=6,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "MH2",
            fontName=font,
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#1d4ed8"),
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "MBody",
            fontName=font,
            fontSize=10.5,
            leading=16,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "MBullet",
            fontName=font,
            fontSize=10.5,
            leading=15,
            leftIndent=14,
            bulletIndent=4,
            textColor=colors.HexColor("#334155"),
            spaceAfter=3,
        ),
        "box": ParagraphStyle(
            "MBox",
            fontName=font,
            fontSize=10,
            leading=15,
            textColor=colors.HexColor("#7c2d12"),
            backColor=colors.HexColor("#fff7ed"),
            borderColor=colors.HexColor("#fdba74"),
            borderWidth=1,
            borderPadding=8,
            spaceAfter=8,
        ),
        "tip": ParagraphStyle(
            "MTip",
            fontName=font,
            fontSize=10,
            leading=15,
            textColor=colors.HexColor("#065f46"),
            backColor=colors.HexColor("#ecfdf5"),
            borderPadding=8,
            spaceAfter=8,
        ),
        "footer": ParagraphStyle(
            "MFooter",
            fontName=font,
            fontSize=8,
            textColor=colors.HexColor("#94a3b8"),
            alignment=TA_CENTER,
        ),
        "toc": ParagraphStyle(
            "MToc",
            fontName=font,
            fontSize=11,
            leading=18,
            textColor=colors.HexColor("#1e293b"),
        ),
    }
    return styles


def img_flow(path: Path | None, max_w: float = 14 * cm, max_h: float = 7.5 * cm):
    if not path or not path.exists():
        return Spacer(1, 4)
    im = Image(str(path))
    iw, ih = im.imageWidth, im.imageHeight
    scale = min(max_w / iw, max_h / ih, 1.0)
    im.drawWidth = iw * scale
    im.drawHeight = ih * scale
    im.hAlign = "CENTER"
    return im


def bullets(font_style, items: list[str]):
    return [Paragraph(f"• {item}", font_style) for item in items]


def activity_box(styles, title: str, body: str):
    return Paragraph(f"<b>🎯 {title}</b><br/>{body}", styles["box"])


def tip_box(styles, text: str):
    return Paragraph(f"<b>💡 TIP</b> {text}", styles["tip"])


def page_header(styles, section: str, title: str):
    return [
        Paragraph(section, styles["section"]),
        Paragraph(title, styles["h1"]),
        Spacer(1, 4),
    ]


def add_page(story, styles, pool: ImagePool, section: str, title: str, blocks, img_key: str = ""):
    story.extend(page_header(styles, section, title))
    for kind, content in blocks:
        if kind == "p":
            story.append(Paragraph(content, styles["body"]))
        elif kind == "h2":
            story.append(Paragraph(content, styles["h2"]))
        elif kind == "ul":
            story.extend(bullets(styles["bullet"], content))
            story.append(Spacer(1, 4))
        elif kind == "box":
            story.append(activity_box(styles, content[0], content[1]))
        elif kind == "tip":
            story.append(tip_box(styles, content))
        elif kind == "sp":
            story.append(Spacer(1, content))
    img = pool.for_section(img_key) if img_key else pool.any_image()
    story.append(Spacer(1, 6))
    story.append(img_flow(img))
    story.append(PageBreak())


def build_manuscript() -> Path:
    font = register_fonts()
    styles = build_styles(font)
    pool = ImagePool()
    story: list = []

    # ----- 표지 -----
    story.append(Spacer(1, 3.5 * cm))
    story.append(Paragraph("나만의 커스텀 퀵드로우 만들기", styles["title"]))
    story.append(Paragraph("학생용 강의원고 (6시간 완성본)", styles["subtitle"]))
    story.append(Spacer(1, 0.8 * cm))
    meta = [
        ["주최", "조선대학교부속고등학교"],
        ["프로그램", "2026 여름방학 고등학생 AISW 교실"],
        ["담당", "김다은"],
        ["분량", "약 70페이지 · 6시간"],
        ["버전", f"{date.today().isoformat()}"],
    ]
    t = Table(meta, colWidths=[3.2 * cm, 10 * cm])
    t.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), font, 11),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#64748b")),
                ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#0f172a")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 1.2 * cm))
    story.append(img_flow(pool.for_section("07_") or pool.any_image(), max_h=6 * cm))
    story.append(PageBreak())

    # ----- 사용 안내 -----
    add_page(
        story,
        styles,
        pool,
        "안내",
        "이 원고를 어떻게 쓰나요?",
        [
            (
                "p",
                "본 강의원고는 Streamlit 학습 웹앱(도입·핵심 원리·수집기·미드저니·Colab·발표)의 "
                "모든 내용을 6시간 수업 흐름에 맞춰 정리한 학생 배포용 자료입니다. "
                "수업 중 필기 공간을 넉넉히 두었으며, 활동·퀴즈·체크리스트를 함께 실천하세요.",
            ),
            (
                "ul",
                [
                    "1~2시간차: 도입 + AI·코딩 핵심 원리 (이론·퀴즈)",
                    "3시간차: 나만의 퀵드로우 수집기 (데이터 편향 체험)",
                    "4시간차: 미드저니 게임 아트 제작",
                    "5~6시간차: Colab 코딩 실습 + Gradio 게임 + 발표",
                ],
            ),
            ("box", ("준비물", "노트북, 펜마우스, 구글 계정, 미드저니 계정, 인터넷")),
            ("tip", "웹앱 메뉴 순서대로 따라가면 수업이 자연스럽게 연결됩니다."),
        ],
        "03_",
    )

    # ----- 목차 -----
    story.append(Paragraph("목 차", styles["h1"]))
    toc = [
        "제1부  도입 · 아이스브레이킹 · AI 두 얼굴 ............... 5",
        "제2부  AI·코딩 핵심 원리 (30분 이론+퀴즈) .............. 15",
        "제3부  데이터 학습·편향 — 나만의 퀵드로우 수집기 ....... 27",
        "제4부  미드저니로 게임 아트 만들기 .................... 37",
        "제5부  Colab으로 나만의 퀵드로우 만들기 ............... 45",
        "제6부  발표·마무리 · 학습지 · 참고자료 ................ 61",
        "부록   용어 사전 · 링크 모음 · 퀴즈 정답 ................ 67",
    ]
    for line in toc:
        story.append(Paragraph(line, styles["toc"]))
    story.append(PageBreak())

    # ----- 6시간 타임테이블 -----
    add_page(
        story,
        styles,
        pool,
        "개관",
        "6시간 수업 타임테이블",
        [
            (
                "p",
                "아래 표는 권장 진행 시간입니다. 학교 환경에 따라 ±10분 조절 가능합니다.",
            ),
        ],
        "04_",
    )
    schedule = [
        ["시간", "차시", "주제", "핵심 활동"],
        ["0:00~0:50", "1", "도입", "쁘띠바크·팀 구성·AI 두 얼굴"],
        ["0:50~1:20", "2", "핵심 원리", "6개 미션 퀴즈·실습"],
        ["1:20~2:20", "3", "수집기", "데이터 직접 생성·편향 관찰"],
        ["2:20~3:10", "4", "미드저니", "프롬프트·게임 아트 3종"],
        ["3:10~5:10", "5~6", "Colab", "코드 작성·학습·Gradio 게임"],
        ["5:10~6:00", "마무리", "발표·학습지·회고"],
    ]
    st = Table(schedule, colWidths=[2.4 * cm, 1.2 * cm, 3 * cm, 8 * cm])
    st.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), font, 9.5),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.append(st)
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "<b>오늘의 목표:</b> 수업이 끝나면 내가 직접 만든 AI에게 펜마우스로 그림을 그려주면 "
            "AI가 이름을 맞힙니다. 🖊️ → 🤖 → \"고양이!\"",
            styles["body"],
        )
    )
    story.append(PageBreak())

    # ==================== 제1부: 도입 (10 pages) ====================
    part1_pages = [
        (
            "제1부 · 도입",
            "환영합니다 — AI를 만드는 하루",
            [
                (
                    "p",
                    "안녕하세요! 오늘은 '그림을 알아맞히는 AI'를 직접 만들고, "
                    "펜마우스로 그려서 게임하는 특별한 하루입니다. "
                    "생성형 AI(미드저니)로 예쁜 그림을 만들고, "
                    "분류 AI(퀵드로우)로 게임의 두뇌를 코딩해 봅니다.",
                ),
                (
                    "ul",
                    [
                        "데이터가 왜 중요한지 직접 체험합니다.",
                        "파이썬 코드의 기초를 Colab에서 작성합니다.",
                        "팀 협업으로 게임을 완성하고 발표합니다.",
                    ],
                ),
            ],
            "03_",
        ),
        (
            "제1부 · 도입",
            "아이스브레이킹: 쁘띠바크 게임",
            [
                (
                    "p",
                    "OT 10~15분 동안 팀을 구성하고 쁘띠바크(Petit Bac) 게임으로 분위기를 올립니다. "
                    "4~5명이 한 팀, 라운드당 3분 제한을 권장합니다.",
                ),
                ("h2", "진행 순서"),
                (
                    "ul",
                    [
                        "4~5명 팀 구성 (웹앱 랜덤 팀 배정 도구 활용 가능)",
                        "영상 규칙 확인 후 1~2라운드 진행",
                        "팀별 기록자 1명 지정",
                        "활동 후 팀 구호·역할 정하기",
                    ],
                ),
                ("box", ("교사 팁", "라운드 종료 후 '우리 팀이 잘한 협업 규칙' 1가지를 발표하게 하세요.")),
            ],
            "pptx",
        ),
        (
            "제1부 · 도입",
            "팀 빌딩이 수업에 중요한 이유",
            [
                (
                    "p",
                    "오늘 활동은 데이터 수집·코딩·아트 제작·발표가 모두 포함됩니다. "
                    "팀원마다 역할(기록자, 프롬프트 담당, 테스터, 발표자)을 나누면 "
                    "6시간을 훨씬 효율적으로 보낼 수 있습니다.",
                ),
                (
                    "ul",
                    [
                        "데이터 수집: 다양한 각도·크기로 그림 그리기",
                        "미드저니: 통일된 스타일의 게임 아트 제작",
                        "Colab: TODO 코드를 함께 해결",
                        "발표: AI가 틀린 이유를 데이터 관점에서 설명",
                    ],
                ),
            ],
            "04_",
        ),
        (
            "제1부 · 도입",
            "AI의 두 얼굴 — 생성 vs 분류",
            [
                (
                    "p",
                    "AI라고 해서 모두 같은 일을 하는 것은 아닙니다. "
                    "오늘은 두 가지 대표 유형을 다룹니다.",
                ),
                ("h2", "🖌️ 생성형 AI (Generative)"),
                (
                    "p",
                    "글(프롬프트)을 입력하면 새로운 이미지·글을 만들어 줍니다. 예: 미드저니, DALL·E, Stable Diffusion.",
                ),
                ("h2", "🔍 분류 AI (Classification)"),
                (
                    "p",
                    "이미 있는 그림·사진을 보고 '이게 뭐지?'라고 이름(라벨)을 맞춥니다. 예: 퀵드로우, 얼굴 인식, Teachable Machine.",
                ),
            ],
            "07_",
        ),
        (
            "제1부 · 도입",
            "생성형 AI 체험 — 미드저니 맛보기",
            [
                (
                    "p",
                    "미드저니는 텍스트 한 줄로 게임에 쓸 로고·캐릭터·배경을 만들 수 있습니다. "
                    "4시간차에 본격적으로 다루지만, 지금은 개념만 잡아 둡니다.",
                ),
                (
                    "ul",
                    [
                        "입력: 영어 프롬프트 (예: cute cat mascot, flat vector, pastel)",
                        "출력: 새로운 이미지 파일",
                        "팁: Fast 생성 시간이 제한되므로 꼭 필요한 4~6장만 제작",
                    ],
                ),
                ("tip", "프롬프트 공식 = 주제 + 스타일 + 색감/분위기 + --ar 비율"),
            ],
            "pptx",
        ),
        (
            "제1부 · 도입",
            "분류 AI 체험 — Quick, Draw! & Teachable Machine",
            [
                (
                    "p",
                    "Google Quick, Draw!는 전 세계 사용자의 낙서로 학습된 분류 AI입니다. "
                    "Teachable Machine은 코딩 없이 사진을 올려 직접 분류 모델을 만들 수 있습니다.",
                ),
                (
                    "ul",
                    [
                        "Quick, Draw!: https://quickdraw.withgoogle.com",
                        "Teachable Machine: https://teachablemachine.withgoogle.com",
                        "개·고양이 사진 10장씩 → Train → 새 사진으로 테스트",
                    ],
                ),
                ("box", ("생각해 보기", "같은 '고양이'인데 왜 어떤 사진은 맞히고 어떤 사진은 틀릴까요?")),
            ],
            "07_",
        ),
        (
            "제1부 · 도입",
            "컴퓨터는 어떻게 그림을 맞출까? — 4단계",
            [
                ("p", "분류 AI가 똑똑해지는 과정은 네 단계로 요약됩니다."),
                (
                    "ul",
                    [
                        "1. 데이터: 학습용 그림 수천~수만 장",
                        "2. 학습: 패턴·특징 찾기 (코드: model.fit)",
                        "3. 모델: 학습이 끝난 AI 두뇌",
                        "4. 추론: 처음 보는 그림 맞히기 (펜마우스 테스트)",
                    ],
                ),
                (
                    "p",
                    "오늘 여러분은 1번(수집기)과 2~4번(Colab)을 직접 수행합니다.",
                ),
            ],
            "04_",
        ),
        (
            "제1부 · 도입",
            "규칙 기반 AI vs 학습형 AI (맛보기)",
            [
                (
                    "p",
                    "규칙 기반 AI는 사람이 IF-THEN 규칙을 직접 적습니다. "
                    "예: '동그라미면 고양이'. 규칙에 없는 그림은 절대 맞히지 못합니다.",
                ),
                (
                    "p",
                    "학습형 AI는 데이터를 많이 보여 주면 스스로 패턴을 찾습니다. "
                    "오늘 만드는 퀵드로우가 바로 학습형 AI입니다.",
                ),
                ("box", ("퀴즈", "미드저니는 생성형, 퀵드로우는 분류형 AI입니다. O/X? → O")),
            ],
            "6장",
        ),
        (
            "제1부 · 도입",
            "1시간차 정리 & 웹앱 이동",
            [
                (
                    "ul",
                    [
                        "✅ 팀 구성·역할 분담 완료",
                        "✅ 생성형 vs 분류 AI 차이 이해",
                        "✅ 데이터→학습→모델→추론 4단계 이름 말하기",
                        "➡️ 다음: 웹앱 'AI·코딩 핵심 원리' 탭으로 이동",
                    ],
                ),
                (
                    "p",
                    "필기: 'AI는 데이터의 거울이다' — 어떤 데이터를 주느냐에 따라 "
                    "AI의 성격과 실력이 달라집니다.",
                ),
            ],
            "03_",
        ),
    ]

    for sec, title, blocks, key in part1_pages:
        add_page(story, styles, pool, sec, title, blocks, key)

    # ==================== 제2부: 핵심 원리 (12 pages) ====================
    part2 = [
        ("제2부 · 핵심 원리", "AI 탐험대 — 6개 미션 개요", [("p", "약 30분 동안 6개 미션을 클리어하며 이론+퀴즈를 진행합니다. 웹앱 진행률 바를 100%로 채워 보세요.")], "07_"),
        ("제2부 · 미션 1", "AI 3종류 — 규칙 · 학습 · 생성", [
            ("p", "규칙 기반: IF-THEN. 학습형: 데이터로 패턴 학습. 생성형: 새 콘텐츠 생성."),
            ("ul", ["규칙: 늑대·염소·양배추 문제", "학습: Teachable Machine, 퀵드로우", "생성: 미드저니"]),
            ("box", ("퀴즈", "Teachable Machine Train 버튼은? → 분류 AI 생성")),
        ], "6장"),
        ("제2부 · 미션 2", "학습 4단계 + train/test", [
            ("p", "학습은 암기가 아닙니다. train 데이터로 공부하고, test 데이터로 일반화를 확인합니다."),
            ("ul", ["캐글 타이타닉: train.csv / test.csv", "수집기: 80장 학습 + 20장 시험", "시험 문제를 미리 보면 안 되는 이유와 같음"]),
            ("tip", "처음 보는 그림에 강한 AI가 좋은 AI입니다."),
        ], "04_"),
        ("제2부 · 미션 2", "에포크·배치·검증 데이터", [
            ("p", "에포크(Epoch): 전체 데이터를 몇 번 반복 학습할지. 배치(Batch): 한 번에 몇 장씩 볼지."),
            ("ul", ["에포크 너무 적음 → underfitting (under 학습)", "에포크 너무 많음 → overfitting (외워 버림)", "validation_split: 일부를 검증용으로 빼 둠"]),
        ], "07_"),
        ("제2부 · 미션 3", "픽셀과 정규화", [
            ("p", "그림은 픽셀(작은 사각형)의 모음. 흑백 픽셀 밝기 0~255."),
            ("p", "학습 전 255로 나누어 0~1로 정규화 → Colab의 DIVISOR = 255"),
            ("box", ("빈칸", "DIVISOR = ? → 255")),
        ], "07_"),
        ("제2부 · 미션 3", "합성곱(Convolution) — 3×3 돋보기", [
            ("p", "3×3 필터를 이미지 위에서 슬라이드하며 선·곡선·에지를 찾습니다."),
            ("ul", ["OpenCV·CNN Conv2D 층이 같은 원리", "에지 추출 필터 예: [[-1,0,1],[-2,0,2],[-1,0,1]]"]),
        ], "07_"),
        ("제2부 · 미션 3", "CNN 레이어 구조", [
            ("ul", [
                "Conv2D: 특징(선·모양) 추출",
                "MaxPooling: 중요 정보만 압축",
                "Flatten + Dense: 최종 라벨 선택",
            ]),
            ("p", "28×28 흑백 50장 → shape (50, 28, 28, 1)"),
            ("box", ("퀴즈", "채널=1인 이유? → 흑백이므로")),
        ], "07_"),
        ("제2부 · 미션 4", "데이터 편향이란?", [
            ("p", "학습 데이터가 특정 유형에만 치우치면, AI도 그쪽만 잘 봅니다."),
            ("ul", [
                "자동차 옆면만 100장 → 앞면·윗면 실패",
                "정면 고양이만 → 옆모습 오인식",
                "한 사람 글씨만 → 다른 사람 글씨 실패",
            ]),
        ], "04_"),
        ("제2부 · 미션 4", "편향 줄이기 전략", [
            ("ul", [
                "크기·방향·위치를 다양하게",
                "여러 팀원이 각자 다른 스타일로 그리기",
                "같은 라벨이라도 최소 3가지 변형 수집",
            ]),
            ("box", ("실습", "우리 팀 수집기 규칙 1가지 적기")),
        ], "04_"),
        ("제2부 · 미션 5", "Confusion Matrix", [
            ("p", "정답(타깃) vs 예측(출력)을 표로 정리. 대각선=맞힌 횟수."),
            ("p", "정확도 90%여도 특정 클래스 쌍에서만 오류가 몰릴 수 있음."),
            ("tip", "수집기에서 '어떤 그림끼리 헷갈리는지' 기록 = Confusion Matrix 분석"),
        ], "07_"),
        ("제2부 · 미션 6", "Colab 코딩 4종", [
            ("ul", [
                "변수: DIVISOR = 255",
                "리스트: labels = ['cat','dog']",
                "함수: add_conv_block()",
                "for/if: 모든 이미지 정규화",
            ]),
            ("p", "라이브러리 = 도서관. import numpy as np"),
        ], "03_"),
        ("제2부 · 정리", "2시간차 마무리", [
            ("ul", [
                "✅ 6개 미션 퀴즈 완료",
                "✅ train/test, CNN, 편향, Confusion Matrix 키워드",
                "➡️ 다음: 나만의 퀵드로우 수집기",
            ]),
        ], "03_"),
    ]
    for sec, title, blocks, key in part2:
        add_page(story, styles, pool, sec, title, blocks, key)

    # ==================== 제3부: 수집기 (10 pages) ====================
    part3 = [
        ("제3부 · 수집기", "나만의 퀵드로우 수집기란?", [
            ("p", "본격 Colab 실습 전, 직접 그림 데이터를 만들며 '학습 데이터의 중요성'과 '편향'을 체험하는 사전 활동입니다."),
            ("ul", ["웹앱에 내장된 HTML 수집기 실행", "한 물체(예: 자동차)를 자유롭게 그리기", "로컬 테스트로 오인식 확인"]),
        ], "07_"),
        ("제3부 · 수집기", "수집기 사용법", [
            ("ul", [
                "이름 입력",
                "학습할 물체 이름 입력 (예: car)",
                "캔버스에 그림 → 제출",
                "'전체 제출 이미지 모아보기'로 팀 데이터 확인",
            ]),
            ("tip", "제출 데이터는 Apps Script를 통해 스프레드시트에 저장됩니다."),
        ], "03_"),
        ("제3부 · 수집기", "미션: 다양한 자동차 그리기", [
            ("p", "같은 '자동차'라도 옆면·정면·윗면·크기·위치를 바꿔 최소 15장 이상 수집해 보세요."),
            ("box", ("실험", "옆면만 20장 vs 다양한 각도 20장 → 테스트 결과 비교")),
        ], "07_"),
        ("제3부 · 수집기", "관찰 포인트 ①", [
            ("ul", [
                "데이터가 많을수록 인식이 안정적인가?",
                "비슷한 형태만 많으면 어떤 그림을 못 맞히는가?",
                "다양한 데이터 추가 후 점수가 변했는가?",
            ]),
        ], "04_"),
        ("제3부 · 수집기", "관찰 포인트 ② — 편향 일지", [
            ("p", "아래 표를 채우며 팀별 편향 일지를 작성하세요."),
            ("ul", ["처음 수집 데이터 특징", "문제/오인식 사례", "개선 방법", "개선 후 변화"]),
        ], "04_"),
        ("제3부 · 수집기", "팀 토론: 왜 AI가 틀렸을까?", [
            ("p", "AI가 틀린 이유를 '모델이 나빠서'가 아니라 '데이터가 어떻게 모였는지' 관점에서 설명해 보세요."),
            ("box", ("발표 1분", "우리 팀의 편향 사례 1가지 공유")),
        ], "04_"),
        ("제3부 · 수집기", "수집기 → Colab 연결", [
            ("p", "수집기에서보낸 JSON을 Colab 노트북 2.5단계에서 학습 데이터에 합칠 수 있습니다(선택)."),
            ("ul", ["quickdraw_collector_dataset.json 다운로드", "Colab 업로드 셀 실행", "클래스 라벨 확인"]),
        ], "03_"),
        ("제3부 · 수집기", "체크리스트", [
            ("ul", [
                "□ 한 물체 정하고 데이터 수집",
                "□ 각자 자유롭게 충분히 그리기",
                "□ 로컬 테스트로 오인식 기록",
                "□ 모양/크기/위치 다양화 후 재테스트",
                "□ '왜 성능이 달라졌는지' 한 줄 정리",
            ]),
        ], "07_"),
        ("제3부 · 수집기", "3시간차 정리", [
            ("p", "데이터 편향은 책 속 개념이 아니라, 방금 여러분이 직접 만든 현상입니다."),
            ("tip", "다음 미드저니 시간에는 '정답 오브젝트를 여러 각도로' 아트도 만들어 보세요."),
        ], "04_"),
        ("제3부 · 수집기", "퀴즈 정리", [
            ("box", ("Q", "옆면 자동차만 많으면? → 다른 각도 인식 약함")),
            ("box", ("Q", "편향 해결법? → 데이터 다양화")),
        ], "04_"),
    ]
    for sec, title, blocks, key in part3:
        add_page(story, styles, pool, sec, title, blocks, key)

    # ==================== 제4부: 미드저니 (8 pages) ====================
    part4 = [
        ("제4부 · 미드저니", "게임 아트 3종 만들기", [
            ("p", "미드저니로 ① 게임 제목 로고 ② 정답 캐릭터(마스코트) ③ 배경을 제작합니다."),
            ("ul", ["접속: https://www.midjourney.com/imagine", "로그인 후 /imagine 입력"]),
        ], "pptx"),
        ("제4부 · 미드저니", "프롬프트 공식", [
            ("p", "주제 + 스타일 + 색감/분위기 + --ar 비율"),
            ("p", "예: cute cat mascot, flat vector illustration, pastel colors, simple, white background --ar 1:1"),
        ], "pptx"),
        ("제4부 · 미드저니", "웹앱 프롬프트 자동 생성기", [
            ("ul", [
                "용도: 캐릭터/로고/배경 선택",
                "주제·스타일·색감·비율 선택",
                "생성된 영어 프롬프트 복사 → 미드저니 붙여넣기",
            ]),
        ], "pptx"),
        ("제4부 · 미드저니", "베이직 플랜 운영 팁", [
            ("ul", [
                "Fast 생성 시간 제한 → 4~6장만 핵심 제작",
                "프롬프트 미리 팀에서 합의",
                "마음에 드는 결과만 Upscale·다운로드",
            ]),
        ], "pptx"),
        ("제4부 · 미드저니", "게임 완성도 업그레이드 아이디어", [
            ("ul", [
                "클래스별 통일 디자인 (색감·선 두께 고정)",
                "정답 보상 이미지 / 힌트 이미지 따로 제작",
                "정면·측면·원근 각 1장씩 → 데이터 다양성 연결",
                "프롬프트 1단어만 바꿔 3회 비교 실험",
            ]),
        ], "pptx"),
        ("제4부 · 미드저니", "Colab과 연동 (선택)", [
            ("p", "노트북 Gradio 셀에서 USE_MIDJOURNEY_ART=True 설정 시, 업로드한 아트를 클래스 라벨과 매칭해 표시할 수 있습니다."),
        ], "03_"),
        ("제4부 · 미드저니", "4시간차 실습 순서", [
            ("ul", ["1. 미드저니 접속", "2. 프롬프트 생성·복사", "3. 3종 아트 다운로드", "4. 팀 폴더에 공유"]),
        ], "pptx"),
        ("제4부 · 미드저니", "4시간차 정리", [
            ("box", ("성찰", "생성형 AI와 분류 AI 중 오늘 내 역할에 더 가까운 것은?")),
        ], "pptx"),
    ]
    for sec, title, blocks, key in part4:
        add_page(story, styles, pool, sec, title, blocks, key)

    # ==================== 제5부: Colab (16 pages) ====================
    part5 = [
        ("제5부 · Colab", "Colab 시작하기", [
            ("p", "Google Colab은 브라우저만으로 파이썬·AI를 실행할 수 있는 환경입니다. 설치 없이 GPU 사용 가능(세션당 제한)."),
            ("ul", ["웹앱 'Colab으로 퀵드로우 만들기' 버튼", "또는 .ipynb 다운로드 후 업로드"]),
        ], "03_"),
        ("제5부 · Colab", "노트북 7단계 로드맵", [
            ("ul", [
                "1. 준비물 설치",
                "2. 그림 데이터 가져오기",
                "2.5 (선택) 수집기 JSON 합치기",
                "3. 데이터 살펴보기",
                "4. 학습 준비 (TODO)",
                "5. AI 두뇌 만들기 (TODO)",
                "6. 성적 확인",
                "7. 펜마우스로 그려서 맞히기",
            ]),
        ], "03_"),
        ("제5부 · Colab", "1단계 — 준비물 설치", [
            ("p", "Gradio, TensorFlow 등 필요한 라이브러리를 설치합니다. 셀 왼쪽 [실행] 또는 Runtime → Run all."),
            ("tip", "막히면 위 셀부터 순서대로 다시 실행하세요."),
        ], "03_"),
        ("제5부 · Colab", "2단계 — 클래스 선택", [
            ("p", "인식할 그림 종류 3~5개를 고릅니다. Quick Draw 데이터 또는 수집기 JSON 사용."),
            ("ul", ["cat, apple, car 등 영어 라벨", "팀마다 테마 통일 추천"]),
        ], "07_"),
        ("제5부 · Colab", "3단계 — 데이터 시각화", [
            ("p", "학습할 그림을 눈으로 확인합니다. 잘못된 라벨·깨진 데이터가 없는지 점검."),
        ], "07_"),
        ("제5부 · Colab", "4단계 TODO — DIVISOR & CHANNELS", [
            ("p", "학생이 직접 채워야 하는 값입니다."),
            ("ul", ["DIVISOR = 255  (정규화)", "CHANNELS = 1   (흑백)"]),
            ("box", ("코드", "normalized = image / DIVISOR")),
        ], "03_"),
        ("제5부 · Colab", "5단계 TODO — ACTIVATION & FILTERS", [
            ("ul", ["ACTIVATION = 'relu' (또는 'softmax' 출력층)", "FILTERS = 32, 64 등 Conv 필터 수"]),
            ("p", "add_conv_block() 함수 내부 TODO 완성 — Conv2D + MaxPooling"),
        ], "07_"),
        ("제5부 · Colab", "model.fit — 학습 실행", [
            ("p", "model.fit(x_train, y_train, epochs=..., batch_size=..., validation_split=...)"),
            ("ul", ["에포크: 5~15 권장", "배치: 32 또는 64", "검증 분할: 0.2~0.3"]),
        ], "07_"),
        ("제5부 · Colab", "6단계 — 정확도 확인", [
            ("p", "테스트 데이터로 accuracy를 확인합니다. 70% 이상이면 훌륭, 85% 이상이면 매우 우수."),
            ("p", "Confusion Matrix로 어떤 클래스끼리 헷갈리는지 분석해 보세요."),
        ], "07_"),
        ("제5부 · Colab", "7단계 — Gradio 게임", [
            ("p", "펜마우스·마우스로 캔버스에 그리면 AI가 실시간으로 예측합니다."),
            ("ul", ["미드저니 아트 연동(선택)", "팀 게임 이름·아트로 꾸미기"]),
        ], "03_"),
        ("제5부 · Colab", "코딩 디버깅 가이드", [
            ("ul", [
                "NameError → 위 셀 미실행",
                "Shape 오류 → (N,28,28,1) 확인",
                "정확도 10%대 → 라벨·데이터 확인",
                "런타임 끊김 → 다시 연결 후 처음부터",
            ]),
        ], "03_"),
        ("제5부 · Colab", "하이퍼파라미터 실험", [
            ("p", "FILTERS, EPOCHS, N_PER_CLASS 값을 바꿔 성능 변화를 기록해 보세요."),
            ("box", ("실험 노트", "변경한 값 / 정확도 / 느낀 점 3줄")),
        ], "07_"),
        ("제5부 · Colab", "펜마우스 테스트 프로토콜", [
            ("ul", [
                "클래스당 3장씩 직접 그리기",
                "맞힌 그림·틀린 그림 스크린샷",
                "틀린 이유를 데이터 관점에서 설명",
            ]),
        ], "07_"),
        ("제5부 · Colab", "팀별 게임 완성 체크", [
            ("ul", ["□ Colab 전 셀 실행 완료", "□ TODO 직접 작성", "□ Gradio 링크 공유", "□ 미드저니 아트 적용"]),
        ], "03_"),
        ("제5부 · Colab", "5~6시간차 정리", [
            ("p", "오늘 여러분은 데이터 수집부터 모델 학습, 게임 배포까지 전 과정을 경험했습니다."),
        ], "03_"),
        ("제5부 · Colab", "코드 작성 체크리스트", [
            ("ul", [
                "□ DIVISOR, CHANNELS 작성",
                "□ ACTIVATION, FILTERS 작성",
                "□ add_conv_block() 완성",
                "□ model.fit 실행",
                "□ accuracy 기록",
            ]),
        ], "03_"),
    ]
    for sec, title, blocks, key in part5:
        add_page(story, styles, pool, sec, title, blocks, key)

    # ==================== 제6부: 발표·마무리 (6 pages) ====================
    part6 = [
        ("제6부 · 발표", "발표 템플릿", [
            ("ul", [
                "1. 우리 게임 소개 (이름·클래스·아트)",
                "2. 데이터 수집 전략 & 편향 경험",
                "3. Colab에서 작성한 핵심 코드 설명",
                "4. 최종 정확도 & 실패 사례",
                "5. AI가 틀린 이유 — 데이터 관점",
            ]),
        ], "04_"),
        ("제6부 · 발표", "토론 질문", [
            ("ul", [
                "AI가 잘 못 맞힌 그림은?",
                "학습 데이터가 한쪽으로 치우치면?",
                "더 다양하게 그리면 결과는?",
            ]),
        ], "04_"),
        ("제6부 · 학습지", "웹 학습지 제출 항목", [
            ("ul", [
                "생성형/분류 AI 예시",
                "편향 체험 기록 (전·문제·개선)",
                "Colab 최종 정확도",
                "성능 향상 팁 & 성찰",
            ]),
            ("p", "웹앱 '학습지 작성·제출' 탭에서 제출"),
        ], "04_"),
        ("제6부 · 참고", "참고 링크 모음", [
            ("ul", [
                "Quick Draw: quickdraw.withgoogle.com",
                "Colab: colab.research.google.com",
                "Teachable Machine: teachablemachine.withgoogle.com",
                "미드저니: midjourney.com/imagine",
            ]),
        ], "03_"),
        ("제6부 · 참고", "데이터 저장 안내", [
            ("p", "수집기: classId=collector-submissions-2026"),
            ("p", "학습지: classId=worksheet-submissions-2026"),
            ("tip", "Apps Script 연동 스프레드시트에서 확인"),
        ], "04_"),
        ("제6부 · 마무리", "오늘의 한 줄", [
            ("p", "AI는 마법이 아니라 데이터와 코드, 그리고 여러분의 상상력이 만든 결과물입니다."),
            ("p", "수고하셨습니다! 🎨🤖"),
        ], "07_"),
    ]
    for sec, title, blocks, key in part6:
        add_page(story, styles, pool, sec, title, blocks, key)

    # ==================== 부록 (4 pages) ====================
    appendix = [
        ("부록 A", "핵심 용어 사전", [
            ("ul", [
                "생성형 AI: 새 콘텐츠 생성",
                "분류 AI: 입력을 카테고리로 분류",
                "CNN: 합성곱 신경망",
                "편향: 데이터 치우침",
                "정규화: 0~255 → 0~1",
                "에포크: 전체 데이터 반복 학습 횟수",
                "Confusion Matrix: 오인식 표",
            ]),
        ], "03_"),
        ("부록 B", "퀴즈 정답 요약", [
            ("ul", [
                "미드저니 → 새 그림 생성",
                "Teachable Machine Train → 분류 AI",
                "DIVISOR → 255",
                "shape → (N,28,28,1)",
                "편향 해결 → 데이터 다양화",
                "for img in images → 반복 정규화",
            ]),
        ], "03_"),
        ("부록 C", "교재·이미지 출처", [
            ("p", "본 원고는 다음 자료의 핵심 개념을 수업용으로 재구성했습니다."),
            ("ul", [
                "딥러닝입문 WITH KAGGLE — 파이썬·코딩 기초",
                "구글 코랩과 데이터 분석의 기초",
                "이미지를 인식하는 네트워크, 합성곱신경망",
                "규칙기반 인공지능 / 데이터 수집 및 분석 with 캐글",
                "조선대학교부속고등학교 AISW 교실 수업 자료",
            ]),
            ("p", "일부 이미지: 교재 PDF/PPTX 추출, Wikimedia Commons, Unsplash (교육용)"),
        ], "04_"),
        ("부록 D", "필기·성찰 공간 안내", [
            ("p", "아래 여백에 오늘 가장 기억에 남는 순간, 팀원에게 고마웠던 점, 다음에 만들고 싶은 AI를 자유롭게 적어 보세요."),
            ("sp", 200),
            ("p", "────────────────────────────────────"),
            ("sp", 200),
            ("p", "────────────────────────────────────"),
        ], "03_"),
    ]
    for sec, title, blocks, key in appendix:
        add_page(story, styles, pool, sec, title, blocks, key)

  # Build PDF with page numbers
    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont(font, 8)
        canvas.setFillColor(colors.HexColor("#94a3b8"))
        canvas.drawString(MARGIN, 1.2 * cm, "조선대학교부속고등학교 · 2026 AISW 교실 · 김다은")
        canvas.drawRightString(PAGE_W - MARGIN, 1.2 * cm, f"- {canvas.getPageNumber()} -")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=1.8 * cm,
        title="학생용 강의원고 — 나만의 커스텀 퀵드로우",
        author="김다은",
    )
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return OUTPUT


if __name__ == "__main__":
    out = build_manuscript()
    print(f"Generated: {out} ({out.stat().st_size // 1024} KB)")
