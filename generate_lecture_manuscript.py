#!/usr/bin/env python3
"""6시간 학생용 강의원고 — 16:9 슬라이드형 PDF 60페이지 (웹앱 파스텔 디자인)."""

from __future__ import annotations

import random
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

BASE = Path(__file__).parent
ASSETS = BASE / "assets" / "manuscript"
FONT_TITLE_PATH = ASSETS / "fonts" / "GowunDodum-Regular.ttf"
FONT_BODY_PATH = ASSETS / "fonts" / "GowunDodum-Regular.ttf"
OUTPUT = BASE / "학생용_개념학습_강의원고_AI이미지기술_2026.pdf"
LEGACY_OUTPUT = BASE / "학생용_강의원고_6시간_AISW_퀵드로우_2026.pdf"
EXTRACTED = ASSETS / "images" / "extracted"
WEB = ASSETS / "images" / "web"

# PowerPoint 16:9 와이드 (13.333" × 7.5")
SLIDE_W = 960
SLIDE_H = 540
FONT_TITLE = "GowunTitle"
FONT_BODY = "GowunBody"

# 레이아웃 — 왼쪽·위 여유 간격 + 본문 대형 타이포
MX = 36           # 좌측·우측 여백
MY_TOP = 30       # 상단 여백
FOOTER_Y = 10
CARD_BOTTOM = 34

# 타이포 (본문 기존 대비 약 2배, 텍스트 전용은 카드에 맞게 더 키움)
SZ_CHIP = 14
SZ_TITLE = 34
SZ_TITLE_HERO = 40
SZ_BODY = 34           # 이미지 있는 슬라이드 본문
SZ_BODY_FULL = 42      # 텍스트 전용 슬라이드 본문
SZ_BODY_MAX = 40       # 이미지 슬라이드 최대 본문
SZ_BODY_FULL_MAX = 50  # 텍스트 전용 최대 본문
SZ_BODY_HERO = 40
SZ_BOX_TITLE = 20
SZ_BOX_BODY = 18
SZ_TIP = 18
LEAD_BODY = 48
LEAD_FULL = 58
LEAD_HERO = 54
PAD_IN = 20            # 카드 내부 패딩
MIN_BODY = 22

# 웹앱 테마 컬러
C_SKY = colors.HexColor("#e0f2fe")
C_SKY2 = colors.HexColor("#f0f9ff")
C_PINK = colors.HexColor("#fce7f3")
C_PINK2 = colors.HexColor("#fdf2f8")
C_ACCENT = colors.HexColor("#7c3aed")
C_BLUE = colors.HexColor("#2563eb")
C_PINK_ACCENT = colors.HexColor("#ec4899")
C_TEXT = colors.HexColor("#334155")
C_TEXT_LIGHT = colors.HexColor("#64748b")
C_CARD = colors.HexColor("#ffffff")
C_HERO_START = colors.HexColor("#7dd3fc")
C_HERO_END = colors.HexColor("#f9a8d4")
C_CHIP_BG = colors.HexColor("#ede9fe")
C_TIP_BG = colors.HexColor("#ecfdf5")
C_TIP_BORDER = colors.HexColor("#6ee7b7")
C_BOX_BG = colors.HexColor("#fff7ed")
C_BOX_BORDER = colors.HexColor("#fdba74")


def register_fonts() -> None:
    FONT_TITLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not FONT_TITLE_PATH.exists():
        import urllib.request

        url = "https://github.com/google/fonts/raw/main/ofl/gowundodum/GowunDodum-Regular.ttf"
        urllib.request.urlretrieve(url, FONT_TITLE_PATH)
    if FONT_TITLE not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_TITLE, str(FONT_TITLE_PATH)))
    if FONT_BODY not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_BODY, str(FONT_BODY_PATH if FONT_BODY_PATH.exists() else FONT_TITLE_PATH)))


class ImagePool:
    def __init__(self) -> None:
        self.extracted = sorted(
            p for p in EXTRACTED.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
        )
        self.web = sorted(WEB.glob("*"))
        random.seed(42)
        random.shuffle(self.extracted)
        self._i = 0
        self._used: set[str] = set()

    def pick(self, keyword: str = "") -> Path | None:
        if keyword:
            for p in self.web:
                if keyword.lower() in p.name.lower() and str(p) not in self._used:
                    self._used.add(str(p))
                    return p
            hits = [p for p in self.extracted if keyword.lower() in p.name.lower()]
            for p in hits:
                if str(p) not in self._used and p.stat().st_size > 4000:
                    self._used.add(str(p))
                    return p
        while self._i < len(self.extracted):
            p = self.extracted[self._i]
            self._i += 1
            if str(p) not in self._used and p.stat().st_size > 4000:
                self._used.add(str(p))
                return p
        return self.web[0] if self.web else None


def wrap_text(text: str, max_chars: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if len(test) <= max_chars:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def chars_per_line(text_w: float, font_size: float) -> int:
    """한글 기준 대략적인 한 줄 글자 수."""
    return max(8, int(text_w / (font_size * 0.55)))


def _wrap_body_lines(
    body: list[str],
    text_w: float,
    size: float,
    *,
    is_bullet: bool,
) -> tuple[list[str], float, float]:
    leading = size * 1.42
    cpl = chars_per_line(text_w, size)
    wrapped: list[str] = []
    for line in body:
        raw = line.lstrip("•□ ").strip()
        prefix = "• " if is_bullet or line.strip().startswith(("•", "□")) else ""
        if line.strip().startswith("□"):
            prefix = "□ "
        for sub in wrap_text(raw, cpl):
            wrapped.append(f"{prefix}{sub}" if prefix else sub)
    return wrapped, size, leading


def fit_body_lines(
    body: list[str],
    text_w: float,
    avail_h: float,
    *,
    full_width: bool,
    is_bullet: bool,
) -> tuple[list[str], float, float]:
    """본문을 카드 너비·높이에 맞게 줄바꿈·크기 조절 (부족하면 키움)."""
    max_size = SZ_BODY_FULL_MAX if full_width else SZ_BODY_MAX
    size = SZ_BODY_FULL if full_width else SZ_BODY
    wrapped, size, leading = _wrap_body_lines(body, text_w, size, is_bullet=is_bullet)

    while size >= MIN_BODY and len(wrapped) * leading > avail_h:
        size -= 1.5
        wrapped, size, leading = _wrap_body_lines(body, text_w, size, is_bullet=is_bullet)

    # 줄 수가 적을 때 카드 높이를 채우도록 글씨 키우기
    while size + 2 <= max_size:
        test_wrapped, test_size, test_leading = _wrap_body_lines(
            body, text_w, size + 2, is_bullet=is_bullet
        )
        if len(test_wrapped) * test_leading <= avail_h * 0.92:
            wrapped, size, leading = test_wrapped, test_size, test_leading
        else:
            break

    max_lines = max(1, int(avail_h / leading))
    return wrapped[:max_lines], size, leading


class SlideRenderer:
    def __init__(self, c: canvas.Canvas, pool: ImagePool) -> None:
        self.c = c
        self.pool = pool

    def _bg(self, hero: bool = False) -> None:
        c = self.c
        c.saveState()
        if hero:
            steps = 24
            for i in range(steps):
                t = i / steps
                r = C_HERO_START.red + t * (C_HERO_END.red - C_HERO_START.red)
                g = C_HERO_START.green + t * (C_HERO_END.green - C_HERO_START.green)
                b = C_HERO_START.blue + t * (C_HERO_END.blue - C_HERO_START.blue)
                c.setFillColor(colors.Color(r, g, b))
                c.rect(0, SLIDE_H - (i + 1) * (SLIDE_H / steps), SLIDE_W, SLIDE_H / steps + 1, fill=1, stroke=0)
        else:
            c.setFillColor(C_SKY2)
            c.rect(0, 0, SLIDE_W, SLIDE_H, fill=1, stroke=0)
            c.setFillColor(C_SKY)
            c.circle(80, SLIDE_H - 60, 100, fill=1, stroke=0)
            c.setFillColor(C_PINK)
            c.circle(SLIDE_W - 90, 70, 90, fill=1, stroke=0)
            c.setFillColor(C_PINK2)
            c.circle(SLIDE_W - 200, SLIDE_H - 50, 60, fill=1, stroke=0)
        c.restoreState()

    def _footer(self, num: int, total: int = 60) -> None:
        c = self.c
        c.saveState()
        c.setFillColor(C_TEXT_LIGHT)
        c.setFont(FONT_BODY, 7.5)
        c.drawString(MX, FOOTER_Y, "조선대학교부속고등학교 · 2026 AISW 교실 · 김다은")
        c.drawRightString(SLIDE_W - MX, FOOTER_Y, f"{num} / {total}")
        c.restoreState()

    def _chip(self, text: str, y: float) -> None:
        c = self.c
        c.saveState()
        c.setFont(FONT_BODY, SZ_CHIP)
        tw = c.stringWidth(text, FONT_BODY, SZ_CHIP)
        x, h, pad = MX, 22, 8
        c.setFillColor(C_CHIP_BG)
        c.setStrokeColor(colors.HexColor("#c4b5fd"))
        c.roundRect(x, y, tw + pad * 2, h, 12, fill=1, stroke=1)
        c.setFillColor(C_ACCENT)
        c.drawString(x + pad, y + 7, text)
        c.restoreState()

    def _card(self, x: float, y: float, w: float, h: float) -> None:
        c = self.c
        c.saveState()
        c.setFillColor(colors.Color(1, 1, 1, alpha=0.94))
        c.setStrokeColor(colors.HexColor("#c4b5fd"))
        c.setLineWidth(1.2)
        c.roundRect(x, y, w, h, 12, fill=1, stroke=1)
        c.restoreState()

    def _image_usable(self, path: Path | None, max_w: float, max_h: float) -> bool:
        """너무 작거나 가느다란 이미지는 텍스트 전용 레이아웃으로 전환."""
        if not path or not path.exists():
            return False
        from reportlab.lib.utils import ImageReader

        iw, ih = ImageReader(str(path)).getSize()
        if iw < 80 or ih < 80:
            return False
        scale = min(max_w / iw, max_h / ih)
        return ih * scale >= max_h * 0.28 and iw * scale >= max_w * 0.28

    def _draw_image(self, path: Path | None, x: float, y: float, max_w: float, max_h: float) -> None:
        if not path or not path.exists():
            return
        from reportlab.lib.utils import ImageReader

        ir = ImageReader(str(path))
        iw, ih = ir.getSize()
        scale = min(max_w / iw, max_h / ih)  # 영역을 꽉 채우도록 확대 허용
        dw, dh = iw * scale, ih * scale
        # 영역 내 중앙 정렬
        ox = x + (max_w - dw) / 2
        oy = y + (max_h - dh) / 2
        self.c.saveState()
        self.c.setStrokeColor(colors.HexColor("#a5b4fc"))
        self.c.setLineWidth(1.5)
        self.c.roundRect(ox - 3, oy - 3, dw + 6, dh + 6, 10, fill=0, stroke=1)
        self.c.drawImage(ir, ox, oy, width=dw, height=dh, mask="auto")
        self.c.restoreState()

    def _text_block(
        self,
        lines: list[str],
        x: float,
        y: float,
        size: float = 13.5,
        color=C_TEXT,
        leading: float = 21,
        bullet: bool = False,
        font: str | None = None,
    ) -> float:
        c = self.c
        fn = font or FONT_BODY
        c.setFont(fn, size)
        c.setFillColor(color)
        cy = y
        for line in lines:
            prefix = "• " if bullet and not line.startswith("•") else ""
            c.drawString(x, cy, prefix + line)
            cy -= leading
        return cy

    def render(
        self,
        num: int,
        chip: str,
        title: str,
        body: list[str],
        *,
        hero: bool = False,
        img_key: str = "",
        tip: str = "",
        box: tuple[str, str] | None = None,
        two_col_bullets: list[str] | None = None,
    ) -> None:
        if num > 1:
            self.c.showPage()
        self._bg(hero=hero)
        chip_y = SLIDE_H - MY_TOP - 24
        self._chip(chip, chip_y)
        self._footer(num)

        c = self.c
        title_y = chip_y - 52
        title_color = colors.white if hero else colors.HexColor("#0f172a")
        title_size = SZ_TITLE_HERO if hero else SZ_TITLE
        c.setFont(FONT_TITLE, title_size)
        c.setFillColor(title_color)
        c.drawString(MX, title_y, title[:24])

        # 제목 아래 충분한 간격 후 카드 시작 (대형 본문과 겹침 방지)
        card_top = title_y - title_size - 24
        card_y = CARD_BOTTOM
        card_h = card_top - card_y
        gap = 12

        # img_key가 있을 때만 이미지 배치 (없거나 너무 작으면 텍스트 전용 풀폭)
        img = self.pool.pick(img_key) if img_key else None
        probe_w = (SLIDE_W - MX * 2 - gap) * 0.46
        has_img = self._image_usable(img, probe_w, card_h) if img else False
        if img and not has_img:
            img = None

        if hero:
            body_x = MX + PAD_IN
            hero_lines, hero_sz, hero_lead = fit_body_lines(
                body[:5], SLIDE_W * 0.52, card_h, full_width=False, is_bullet=False
            )
            block_h = len(hero_lines) * hero_lead
            body_y = card_y + (card_h + block_h) / 2 - hero_lead
            c.setFont(FONT_BODY, hero_sz)
            c.setFillColor(colors.white)
            for i, line in enumerate(hero_lines):
                c.drawString(body_x, body_y - i * hero_lead, line)
            if img:
                img_w = SLIDE_W * 0.40
                self._draw_image(img, SLIDE_W - MX - img_w, card_y, img_w, card_h)
            return

        if has_img:
            img_w = (SLIDE_W - MX * 2 - gap) * 0.46
            text_w = SLIDE_W - MX * 2 - gap - img_w
        else:
            text_w = SLIDE_W - MX * 2
            img_w = 0

        card_w = text_w if has_img else SLIDE_W - MX * 2
        self._card(MX, card_y, card_w, card_h)

        reserve_bottom = 0
        if box:
            reserve_bottom += 82
        if tip:
            tip_lines_tmp = wrap_text(f"💡 TIP  {tip}", chars_per_line(text_w - PAD_IN * 2, SZ_TIP))
            reserve_bottom += 24 + len(tip_lines_tmp) * 20 + 8

        avail_h = card_h - PAD_IN * 2 - reserve_bottom
        is_bullet = any(b.startswith("•") or b.startswith("□") for b in body)

        if two_col_bullets:
            body_size = SZ_BODY if has_img else SZ_BODY_FULL
            body_leading = LEAD_BODY if has_img else LEAD_FULL
            mid = (len(two_col_bullets) + 1) // 2
            col_w = (text_w - PAD_IN * 2) / 2
            ty = card_y + card_h - PAD_IN
            self._text_block(
                two_col_bullets[:mid], MX + PAD_IN, ty, body_size, bullet=True, leading=body_leading
            )
            self._text_block(
                two_col_bullets[mid:], MX + PAD_IN + col_w, ty, body_size, bullet=True, leading=body_leading
            )
            display_body = []
            body_size = body_size
            body_leading = body_leading
        else:
            display_body, body_size, body_leading = fit_body_lines(
                body, text_w - PAD_IN * 2, avail_h, full_width=not has_img, is_bullet=is_bullet
            )
            block_h = len(display_body) * body_leading
            ty = card_y + card_h - PAD_IN
            self._text_block(
                display_body,
                MX + PAD_IN,
                ty,
                body_size,
                bullet=False,
                leading=body_leading,
            )

        if box:
            bx, by = MX + PAD_IN, card_y + PAD_IN
            box_h = 76
            self.c.saveState()
            self.c.setFillColor(C_BOX_BG)
            self.c.setStrokeColor(C_BOX_BORDER)
            self.c.roundRect(bx, by, text_w - PAD_IN * 2, box_h, 8, fill=1, stroke=1)
            c.setFont(FONT_TITLE, SZ_BOX_TITLE)
            c.setFillColor(colors.HexColor("#7c2d12"))
            c.drawString(bx + 12, by + box_h - 22, f"🎯 {box[0]}")
            c.setFont(FONT_BODY, SZ_BOX_BODY)
            for i, ln in enumerate(wrap_text(box[1], chars_per_line(text_w - PAD_IN * 2, SZ_BOX_BODY))[:2]):
                c.drawString(bx + 12, by + box_h - 44 - i * 20, ln)
            self.c.restoreState()

        if tip:
            self.c.saveState()
            self.c.setFillColor(C_TIP_BG)
            self.c.setStrokeColor(C_TIP_BORDER)
            tip_lines = wrap_text(f"💡 TIP  {tip}", chars_per_line(text_w - PAD_IN * 2, SZ_TIP))
            th = 24 + len(tip_lines) * 20
            ty0 = card_y + PAD_IN + (82 if box else 0)
            self.c.roundRect(MX + PAD_IN, ty0, text_w - PAD_IN * 2, th, 8, fill=1, stroke=1)
            self._text_block(tip_lines, MX + PAD_IN + 8, ty0 + th - 14, SZ_TIP, C_TEXT, leading=19)
            self.c.restoreState()

        if has_img:
            self._draw_image(img, SLIDE_W - MX - img_w, card_y, img_w, card_h)


def build_slides() -> list[dict]:
    """개념 학습용 60장 — 실습 활동 제외, AI·코딩·편향 이론 중심."""
    S = []

    def add(chip, title, body, **kw):
        S.append({"chip": chip, "title": title, "body": body, **kw})

    # ── 표지·안내 (4) ──
    add("COVER", "AI 이미지 기술 개념 학습", [
        "학생용 개념 슬라이드 · 60장",
        "이미지 인식 · 분류 · 생성 & 데이터 편향",
        "조선대학교부속고등학교 · 2026 AISW 교실",
        f"담당 김다은 · {date.today().year}",
    ], hero=True, img_key="neural")

    add("안내", "이 슬라이드는 무엇을 위한 자료인가요?", [
        "• 실습 절차(수집기·Colab·미드저니)는 제외",
        "• AI·프로그래밍·데이터 편향 '개념'만 정리",
        "• 수업 전 예습·수업 중 필기·시험 대비용",
        "• 16:9 슬라이드 — 교실 프로젝터에 최적화",
    ], tip="실습은 Streamlit 웹앱 메뉴를 따라 진행하세요")

    add("목차", "60 슬라이드 개념 로드맵", [
        "제1부  AI와 이미지 인텔리전스 개요 (5~12)",
        "제2부  AI 학습의 4단계와 일반화 (13~22)",
        "제3부  이미지 인식·분류 기술 (23~34)",
        "제4부  이미지 생성 AI 기술 (35~42)",
        "제5부  데이터 편향과 AI 윤리 (43~52)",
        "제6부  프로그래밍 기초 개념 (53~60)",
    ], img_key="07_")

    add("학습목표", "이 자료를 마치면 설명할 수 있어요", [
        "생성형 AI와 분류 AI의 차이",
        "데이터→학습→모델→추론 4단계",
        "CNN·합성곱이 이미지를 인식하는 원리",
        "데이터 편향이 성능에 미치는 영향",
        "변수·함수·반복문 등 코딩 기초",
    ], box=("핵심 질문", "AI는 왜 데이터에 따라 달라질까?"))

    # ── 제1부: AI 개요 (8장) 5~12 ──
    add("제1부", "인공지능(AI)이란?", [
        "사람처럼 학습·추론하는 컴퓨터 시스템",
        "규칙을 직접 짜기도, 데이터로 스스로 배우기도 함",
        "오늘 초점: 이미지를 다루는 AI",
    ], hero=True, img_key="ai_brain")

    add("제1부", "이미지 AI의 두 갈래", [
        "🔍 인식·분류: 그림→이름 (퀵드로우, 얼굴인식)",
        "🖌️ 생성: 글→새 그림 (미드저니, DALL·E)",
        "입력과 출력이 정반대!",
    ], img_key="07_")

    add("제1부", "규칙 기반 AI", [
        "사람이 IF-THEN 규칙을 직접 작성",
        "예: IF 동그라미 THEN 고양이",
        "규칙 밖 상황은 처리 불가",
    ], img_key="6장")

    add("제1부", "학습형 AI (Machine Learning)", [
        "데이터를 많이 보여주면 패턴을 스스로 학습",
        "규칙을 일일이 적지 않아도 새 상황 대응",
        "이미지 분류·인식의 핵심 방식",
    ], img_key="07_")

    add("제1부", "생성형 AI (Generative AI)", [
        "텍스트·이미지 등에서 '새로운' 결과 생성",
        "학습 데이터의 패턴을 바탕으로 창작",
        "프롬프트(명령문)로 결과를 조절",
    ], img_key="pptx")

    add("제1부", "세 가지 AI 비교", [
        "규칙: 명시적 규칙 · 유연성 낮음",
        "학습: 데이터 기반 · 일반화 가능",
        "생성: 새 콘텐츠 · 창의적 출력",
    ], two_col_bullets=[
        "전문가 시스템", "CNN 분류",
        "의료 영상 판독 보조", "텍스트→이미지",
    ])

    add("제1부", "개념 퀴즈 ①", [
        "Q. 그린 고양이 그림을 '고양이'라고 맞추는 AI?",
        "→ 분류(인식) AI",
        "Q. 'cute cat' 글을 넣어 새 그림 만드는 AI?",
        "→ 생성 AI",
    ], box=("정답", "입력이 그림이면 분류, 글이면 생성"))

    add("제1부", "제1부 정리", [
        "AI는 방식에 따라 규칙/학습/생성으로 나뉨",
        "이미지 수업의 핵심: 학습형 분류 + 생성형",
        "다음: AI가 배우는 4단계",
    ])

    # ── 제2부: 학습 4단계 (10장) 13~22 ──
    add("제2부", "AI 학습 4단계", [
        "1 데이터  2 학습  3 모델  4 추론",
        "모든 학습형 AI의 공통 파이프라인",
    ], hero=True)

    add("제2부", "1단계 — 데이터 (Data)", [
        "AI가 배우는 '교과서' = 학습 데이터",
        "이미지+라벨 쌍 (예: 고양이 그림+'cat')",
        "양과 질이 성능을 좌우",
    ], img_key="04_")

    add("제2부", "2단계 — 학습 (Training)", [
        "데이터에서 패턴·특징을 찾는 과정",
        "코드로 수천~수만 번 반복 계산",
        "학습 ≠ 암기 (아래에서 설명)",
    ])

    add("제2부", "3단계 — 모델 (Model)", [
        "학습이 끝난 AI의 '두뇌'",
        "가중치·구조가 저장된 결과물",
        "파일로 저장·불러오기 가능",
    ])

    add("제2부", "4단계 — 추론 (Inference)", [
        "처음 보는 입력에 대해 결과 예측",
        "학습 때 본 적 없는 그림도 테스트",
        "실제 서비스에서 쓰는 단계",
    ])

    add("제2부", "학습 vs 암기 — 일반화", [
        "암기: 본 문제만 맞힘",
        "일반화: 새 문제도 맞힘",
        "train 데이터로 공부, test로 실력 검증",
    ], tip="시험 문제를 미리 외우면 test 점수는 의미 없음")

    add("제2부", "train / test 분리", [
        "train: AI가 공부하는 데이터",
        "test: 처음 보는 시험 데이터",
        "test 성능이 '진짜 실력'",
    ], img_key="04_")

    add("제2부", "에포크·배치·검증", [
        "Epoch: 전체 데이터 반복 학습 횟수",
        "Batch: 한 번에 처리하는 샘플 수",
        "Validation: 학습 중 실력 중간 점검",
    ])

    add("제2부", "과적합·과소적합", [
        "과소적합: 너무 못 배움 (underfitting)",
        "과적합: train만 외움 (overfitting)",
        "적절한 학습이 일반화의 열쇠",
    ])

    add("제2부", "제2부 정리", [
        "데이터→학습→모델→추론 순서 기억",
        "test 성능으로 일반화 판단",
        "다음: 이미지 인식 기술",
    ])

    # ── 제3부: 이미지 인식 (12장) 23~34 ──
    add("제3부", "이미지 인식이란?", [
        "컴퓨터가 그림 속 대상을 식별",
        "얼굴 인식, 자율주행, 의료 영상 등",
        "딥러닝(CNN)이 핵심 기술",
    ], hero=True, img_key="07_")

    add("제3부", "픽셀 — 컴퓨터의 눈", [
        "그림 = 작은 사각형(픽셀)의 배열",
        "흑백: 0(검정)~255(흰색) 밝기 값",
        "컬러: R·G·B 채널",
    ], img_key="07_")

    add("제3부", "정규화 (Normalization)", [
        "0~255 → 0~1로 스케일 조정",
        "학습 안정성·수렴 속도 향상",
        "예: image / 255.0",
    ], box=("개념", "DIVISOR=255의 의미"))

    add("제3부", "이미지 shape 이해", [
        "(장수, 높이, 너비, 채널)",
        "흑백 28×28 50장 → (50,28,28,1)",
        "채널 1=흑백, 3=RGB",
    ], img_key="07_")

    add("제3부", "합성곱 (Convolution)", [
        "3×3 필터를 이미지 위에서 이동",
        "선·곡선·에지 등 특징 추출",
        "사람 눈의 특징 찾기를 수학으로",
    ], img_key="07_")

    add("제3부", "CNN 구조 한눈에", [
        "Conv2D: 특징 추출 (돋보기)",
        "MaxPooling: 정보 압축 (요약)",
        "Flatten+Dense: 최종 분류 (판단)",
    ], img_key="neural")

    add("제3부", "활성화 함수", [
        "ReLU: 음수 제거, 특징 강조",
        "Softmax: 여러 클래스 확률 출력",
        "출력층에서 '고양이 87%' 형태",
    ])

    add("제3부", "정확도 (Accuracy)", [
        "맞힌 수 / 전체 수",
        "직관적이지만 만능은 아님",
        "클래스 불균형 시 오해 가능",
    ])

    add("제3부", "손실 함수 (Loss)", [
        "틀린 정도를 숫자로 표현",
        "학습 목표: loss를 줄이는 방향",
        "accuracy와 함께 모니터링",
    ])

    add("제3부", "Confusion Matrix", [
        "정답(세로) vs 예측(가로) 표",
        "대각선 = 맞힌 횟수",
        "어떤 클래스끼리 헷갈리는지 분석",
    ], img_key="07_")

    add("제3부", "개념 퀴즈 ②", [
        "Q. 28×28 흑백 100장 shape?",
        "→ (100, 28, 28, 1)",
        "Q. Conv2D의 역할?",
        "→ 이미지에서 특징(패턴) 추출",
    ])

    add("제3부", "제3부 정리", [
        "픽셀→정규화→CNN→분류",
        "accuracy + Confusion Matrix로 평가",
        "다음: 이미지 생성 AI",
    ])

    # ── 제4부: 이미지 생성 (8장) 35~42 ──
    add("제4부", "이미지 생성 AI란?", [
        "텍스트·다른 이미지에서 새 그림 생성",
        "미드저니, Stable Diffusion, DALL·E",
        "분류 AI와 입력·출력이 반대",
    ], hero=True, img_key="pptx")

    add("제4부", "생성 AI 작동 원리 (개요)", [
        "대량 이미지-텍스트 쌍으로 학습",
        "텍스트 의미와 시각 패턴 연결",
        "새 프롬프트에 맞는 이미지 합성",
    ])

    add("제4부", "프롬프트 (Prompt)", [
        "AI에게 내리는 자연어 명령",
        "주제+스타일+색감이 결과 좌우",
        "같은 단어 변경 → 다른 결과",
    ])

    add("제4부", "확산 모델 (Diffusion) 개념", [
        "노이즈를 점점 제거하며 이미지 생성",
        "Stable Diffusion·Midjourney 계열",
        "고품질 이미지 생성에 널리 사용",
    ], img_key="pptx")

    add("제4부", "GAN 개념 (맛보기)", [
        "생성기 vs 판별기가 경쟁하며 학습",
        "가짜 이미지를 점점 진짜처럼",
        "역사적으로 중요한 생성 모델",
    ])

    add("제4부", "생성 vs 분류 비교", [
        "분류: 이미지→라벨 (인식)",
        "생성: 텍스트→이미지 (창작)",
        "같은 딥러닝이지만 목적이 다름",
    ], two_col_bullets=[
        "입력: 그림", "입력: 글",
        "출력: 이름", "출력: 새 그림",
    ])

    add("제4부", "생성 AI 한계", [
        "사실과 다른 이미지 생성 가능",
        "저작권·초상권 이슈",
        "프롬프트에 민감 — 편향 반영",
    ], tip="생성 AI도 학습 데이터에 영향을 받음")

    add("제4부", "제4부 정리", [
        "생성 AI = 새 콘텐츠 합성",
        "프롬프트가 생성 결과를 조절",
        "다음: 데이터 편향",
    ])

    # ── 제5부: 데이터 편향 (10장) 43~52 ──
    add("제5부", "데이터 편향이란?", [
        "학습 데이터가 특정 유형에 치우침",
        "AI도 그 편향을 그대로 학습",
        "공정성·정확도 문제의 핵심 원인",
    ], hero=True, img_key="04_")

    add("제5부", "편향이 생기는 이유", [
        "수집 환경·도구·참여자의 한계",
        "특정 각도·인종·성별만 많은 경우",
        "라벨링 오류·주관적 기준",
    ])

    add("제5부", "이미지 편향 사례", [
        "옆면 사진만 → 다른 각도 실패",
        "밝은 피부만 → 어두운 피부 오인식",
        "큰 글씨만 → 작은 글씨 실패",
    ], img_key="07_")

    add("제5부", "편향과 Confusion Matrix", [
        "특정 클래스 쌍에 오류 집중",
        "정확도는 높아도 특정 그룹 불리",
        "표를 보면 편향 패턴 발견",
    ])

    add("제5부", "데이터 다양성", [
        "크기·각도·위치·조명·스타일",
        "다양할수록 일반화 성능 향상",
        "'같은 라벨, 다른 모양'이 핵심",
    ])

    add("제5부", "대표성 (Representation)", [
        "데이터가 실제 세계를 대표해야 함",
        "일부 집단만 있으면 불공정 결과",
        "수집 단계에서 의식적 설계 필요",
    ])

    add("제5부", "편향 완화 전략", [
        "다양한 출처·조건에서 수집",
        "클래스별 균형(balance) 맞추기",
        "지속적 모니터링·재학습",
    ])

    add("제5부", "AI 윤리 기본", [
        "개인정보·초상권 존중",
        "딥페이크·허위 정보 주의",
        "AI 결과를 맹신하지 않기",
    ])

    add("제5부", "개념 퀴즈 ③", [
        "Q. 정면 고양이만 학습하면?",
        "→ 옆모습 고양이 인식 약화",
        "Q. 근본 해결책?",
        "→ 데이터 다양화·대표성 확보",
    ])

    add("제5부", "제5부 정리", [
        "AI는 데이터의 거울",
        "편향은 기술 문제이자 사회 문제",
        "다음: 프로그래밍 기초 개념",
    ])

    # ── 제6부: 프로그래밍 개념 (8장) 53~60 ──
    add("제6부", "코딩이란?", [
        "컴퓨터에 명령을 내리는 언어",
        "AI 구현·학습에 파이썬이 널리 쓰임",
        "개념만 이해해도 AI 원리가 보임",
    ], hero=True, img_key="03_")

    add("제6부", "변수 (Variable)", [
        "값을 저장하는 이름표",
        "예: DIVISOR = 255",
        "반복 계산·결과 재사용에 필수",
    ])

    add("제6부", "함수 (Function)", [
        "반복 코드를 묶어 재사용",
        "입력→처리→출력",
        "예: def normalize(img): return img/255",
    ])

    add("제6부", "조건문·반복문", [
        "if: 조건에 따라 분기",
        "for: 같은 작업 반복",
        "예: for img in images: 정규화",
    ])

    add("제6부", "리스트·배열", [
        "여러 값을 한 번에 관리",
        "labels = ['cat','dog','car']",
        "numpy 배열: 이미지 데이터 처리",
    ], img_key="03_")

    add("제6부", "라이브러리 & API", [
        "라이브러리: 미리 만든 코드 묶음",
        "import numpy, tensorflow 등",
        "API: 프로그램 간 데이터 주고받기",
    ])

    add("부록", "핵심 용어 사전", [
        "CNN·에포크·배치·정규화",
        "생성형AI·분류AI·편향·일반화",
        "Conv2D·Softmax·Confusion Matrix",
    ], two_col_bullets=[
        "추론 Inference", "과적합 Overfitting",
        "프롬프트 Prompt", "확산 Diffusion",
    ])

    add("마무리", "개념 학습 완료!", [
        "이제 실습에서 개념이 살아납니다",
        "AI = 데이터 + 알고리즘 + 목적",
        "궁금한 개념은 슬라이드로 복습하세요 📚",
    ], hero=True)

    assert len(S) == 60, f"슬라이드 수 {len(S)} != 60"
    return S


def build_manuscript() -> Path:
    register_fonts()
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    pool = ImagePool()
    slides = build_slides()

    c = canvas.Canvas(str(OUTPUT), pagesize=(SLIDE_W, SLIDE_H))
    c.setTitle("학생용 개념학습 강의원고 — AI 이미지 기술")
    c.setAuthor("김다은")

    renderer = SlideRenderer(c, pool)
    for i, s in enumerate(slides, 1):
        renderer.render(
            i,
            s["chip"],
            s["title"],
            s["body"],
            hero=s.get("hero", False),
            img_key=s.get("img_key", ""),
            tip=s.get("tip", ""),
            box=s.get("box"),
            two_col_bullets=s.get("two_col_bullets"),
        )

    c.save()
    # 이전 파일명 호환용 복사
    import shutil
    if OUTPUT != LEGACY_OUTPUT:
        shutil.copy2(OUTPUT, LEGACY_OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    # 이미지 추출 (없을 때만)
    if not list(EXTRACTED.glob("*")):
        import fitz

        for pdf in BASE.glob("*.pdf"):
            if "강의원고" in pdf.name:
                continue
            doc = fitz.open(pdf)
            for pi, page in enumerate(doc):
                for ji, img in enumerate(page.get_images(full=True)):
                    pix = fitz.Pixmap(doc, img[0])
                    if pix.n - pix.alpha > 3:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    if pix.width < 120:
                        continue
                    pix.save(str(EXTRACTED / f"{pdf.stem[:16]}_p{pi}_{ji}.png"))
            doc.close()

    out = build_manuscript()
    import fitz

    n = fitz.open(str(out)).page_count
    print(f"Generated: {out} | pages={n} | size={out.stat().st_size // 1024}KB")
