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
FONT_PATH = Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")
OUTPUT = BASE / "학생용_강의원고_6시간_AISW_퀵드로우_2026.pdf"
EXTRACTED = ASSETS / "images" / "extracted"
WEB = ASSETS / "images" / "web"

# PowerPoint 16:9 와이드 (13.333" × 7.5")
SLIDE_W = 960
SLIDE_H = 540
FONT = "WQY"

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
    if FONT not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT, str(FONT_PATH), subfontIndex=0))


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
        c.setFont(FONT, 8)
        c.drawString(36, 18, "조선대학교부속고등학교 · 2026 AISW 교실 · 김다은")
        c.drawRightString(SLIDE_W - 36, 18, f"{num} / {total}")
        c.restoreState()

    def _chip(self, text: str, y: float) -> None:
        c = self.c
        c.saveState()
        c.setFont(FONT, 9)
        tw = c.stringWidth(text, FONT, 9)
        x, h, pad = 36, 22, 12
        c.setFillColor(C_CHIP_BG)
        c.setStrokeColor(colors.HexColor("#c4b5fd"))
        c.roundRect(x, y, tw + pad * 2, h, 11, fill=1, stroke=1)
        c.setFillColor(C_ACCENT)
        c.drawString(x + pad, y + 6, text)
        c.restoreState()

    def _card(self, x: float, y: float, w: float, h: float) -> None:
        c = self.c
        c.saveState()
        c.setFillColor(C_CARD)
        c.setStrokeColor(colors.HexColor("#c4b5fd"))
        c.roundRect(x, y, w, h, 14, fill=1, stroke=1)
        c.restoreState()

    def _draw_image(self, path: Path | None, x: float, y: float, max_w: float, max_h: float) -> None:
        if not path or not path.exists():
            return
        from reportlab.lib.utils import ImageReader

        ir = ImageReader(str(path))
        iw, ih = ir.getSize()
        scale = min(max_w / iw, max_h / ih, 1.0)
        dw, dh = iw * scale, ih * scale
        self.c.saveState()
        self.c.setStrokeColor(colors.HexColor("#a5b4fc"))
        self.c.setLineWidth(1.5)
        self.c.roundRect(x - 2, y - 2, dw + 4, dh + 4, 10, fill=0, stroke=1)
        self.c.drawImage(ir, x, y, width=dw, height=dh, mask="auto")
        self.c.restoreState()

    def _text_block(
        self,
        lines: list[str],
        x: float,
        y: float,
        size: float = 11,
        color=C_TEXT,
        leading: float = 16,
        bullet: bool = False,
    ) -> float:
        c = self.c
        c.setFont(FONT, size)
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
        self._chip(chip, SLIDE_H - 52)
        self._footer(num)

        c = self.c
        title_color = colors.white if hero else colors.HexColor("#0f172a")
        c.setFont(FONT, 22 if hero else 20)
        c.setFillColor(title_color)
        c.drawString(36, SLIDE_H - 88, title[:42])

        img = self.pool.pick(img_key)
        img_x, img_y = SLIDE_W - 36 - 260, 70
        has_img = img is not None
        card_x, card_y = 36, 52
        card_w = 520 if has_img else SLIDE_W - 72
        card_h = 340

        if hero:
            c.setFont(FONT, 13)
            c.setFillColor(colors.white)
            for i, line in enumerate(body[:4]):
                c.drawString(48, SLIDE_H - 130 - i * 20, line)
            if img:
                self._draw_image(img, SLIDE_W - 300, 120, 250, 200)
            return

        self._card(card_x, card_y, card_w, card_h)
        ty = card_y + card_h - 28
        if two_col_bullets:
            mid = (len(two_col_bullets) + 1) // 2
            self._text_block(two_col_bullets[:mid], card_x + 18, ty, 10.5, bullet=True)
            self._text_block(two_col_bullets[mid:], card_x + card_w // 2, ty, 10.5, bullet=True)
        else:
            ty = self._text_block(body, card_x + 18, ty, 10.5, bullet=any(b.startswith("•") for b in body))

        if tip:
            self.c.saveState()
            self.c.setFillColor(C_TIP_BG)
            self.c.setStrokeColor(C_TIP_BORDER)
            tip_lines = wrap_text(f"💡 TIP  {tip}", 52)
            th = 16 + len(tip_lines) * 14
            self.c.roundRect(card_x + 12, card_y + 12, card_w - 24, th, 8, fill=1, stroke=1)
            self._text_block(tip_lines, card_x + 20, card_y + th - 4, 9.5, C_TEXT)
            self.c.restoreState()

        if box:
            bx, by = card_x + 12, card_y + 12
            self.c.saveState()
            self.c.setFillColor(C_BOX_BG)
            self.c.setStrokeColor(C_BOX_BORDER)
            self.c.roundRect(bx, by, card_w - 24, 52, 8, fill=1, stroke=1)
            c.setFont(FONT, 10)
            c.setFillColor(colors.HexColor("#7c2d12"))
            c.drawString(bx + 10, by + 34, f"🎯 {box[0]}")
            c.setFont(FONT, 9.5)
            for i, ln in enumerate(wrap_text(box[1], 48)[:2]):
                c.drawString(bx + 10, by + 18 - i * 13, ln)
            self.c.restoreState()

        if has_img:
            self._draw_image(img, img_x, img_y, 260, 300)


def build_slides() -> list[dict]:
    """정확히 60장 슬라이드 정의."""
    S = []  # chip, title, body, kwargs

    def add(chip, title, body, **kw):
        S.append({"chip": chip, "title": title, "body": body, **kw})

    # 1-3 표지·안내
    add("COVER", "나만의 커스텀 퀵드로우 만들기", [
        "학생용 강의원고 · 6시간 · 60 슬라이드",
        "조선대학교부속고등학교",
        "2026 여름방학 고등학생 AISW 교실",
        f"담당 김다은 · {date.today().year}",
    ], hero=True, img_key="07_")

    add("안내", "이 원고 사용법", [
        "• Streamlit 웹앱 전 메뉴를 6시간 흐름으로 정리했습니다",
        "• 슬라이드마다 활동·퀴즈·체크리스트를 실천하세요",
        "• 16:9 화면 비율 — 프로젝터·태블릿에 최적화",
        "• 필기는 카드 여백 또는 별도 노트에!",
    ], tip="웹앱 메뉴 순서: 도입 → 핵심원리 → 수집기 → 미드저니 → Colab → 발표")

    add("목차", "60 슬라이드 로드맵", [
        "제1부  도입·아이스브레이킹·AI 두 얼굴 (1~10)",
        "제2부  AI·코딩 핵심 원리 6미션 (11~22)",
        "제3부  데이터 수집기·편향 체험 (23~32)",
        "제4부  미드저니 게임 아트 (33~40)",
        "제5부  Colab 코딩·Gradio 게임 (41~54)",
        "제6부  발표·학습지·부록 (55~60)",
    ], img_key="03_")

    # 4 타임테이블
    add("개관", "6시간 타임테이블", [
        "0:00~0:50  ① 도입 — 쁘띠바크·팀 구성·AI 두 얼굴",
        "0:50~1:20  ② 핵심 원리 — 6개 미션 퀴즈",
        "1:20~2:20  ③ 수집기 — 데이터·편향 직접 체험",
        "2:20~3:10  ④ 미드저니 — 게임 아트 3종",
        "3:10~5:10  ⑤⑥ Colab — 코드 작성·게임 완성",
        "5:10~6:00  마무리 — 발표·학습지 제출",
    ], box=("오늘의 목표", "펜마우스로 그리면 AI가 맞힌다! 🖊️→🤖→고양이!"))

    # 제1부 5-10 (6장) -> slides 5-10
    add("제1부", "환영합니다!", [
        "그림을 알아맞히는 AI를 직접 만들고 게임합니다",
        "생성형 AI(미드저니) + 분류 AI(퀵드로우)",
        "데이터 수집 → 코딩 → 발표까지 한 번에!",
    ], hero=True, img_key="ai_brain")

    add("제1부", "아이스브레이킹: 쁘띠바크", [
        "4~5명 팀 구성 · 라운드 3분",
        "영상 규칙 확인 후 1~2라운드",
        "팀 기록자 지정 · 구호·역할 정하기",
    ], box=("교사 팁", "라운드 후 협업 규칙 1가지 팀 발표"), img_key="pptx")

    add("제1부", "AI의 두 얼굴", [
        "🖌️ 생성형: 글→새 그림 (미드저니)",
        "🔍 분류형: 그림→이름 (퀵드로우)",
        "같은 'AI'지만 하는 일이 완전히 다름!",
    ], two_col_bullets=[
        "Quick Draw 체험", "Teachable Machine",
        "프롬프트 입력", "사진 업로드·Train",
    ], img_key="07_")

    add("제1부", "AI 4단계 한눈에", [
        "1 데이터 — 낙서·사진 모으기",
        "2 학습 — 패턴 찾기 (model.fit)",
        "3 모델 — 똑똑해진 두뇌",
        "4 추론 — 새 그림 맞히기 (게임!)",
    ], tip="오늘 1번=수집기, 2~4번=Colab")

    add("제1부", "규칙 AI vs 학습 AI", [
        "규칙: IF-THEN 직접 작성 (늑대·염소 문제)",
        "학습: 데이터로 스스로 패턴 (퀵드로우)",
        "퀴즈: 미드저니=생성, 퀵드로우=분류 → O",
    ], img_key="6장")

    add("제1부", "1시간차 체크", [
        "✅ 팀·역할 분담 완료",
        "✅ 생성 vs 분류 차이 설명 가능",
        "✅ 4단계 이름 말하기",
        "➡️ 웹앱 'AI·코딩 핵심 원리' 이동",
    ])

    # 제2부 11-22 (12장)
    add("제2부", "AI 탐험대 — 6미션", [
        "30분 · 웹앱 진행률 100% 도전!",
        "이론+퀴즈+미니 실습으로 개념 정리",
    ], hero=True)

    add("미션 1", "AI 3종류", [
        "규칙 기반 — IF-THEN",
        "학습형 — 데이터→패턴",
        "생성형 — 새 콘텐츠",
    ], box=("퀴즈", "Teachable Machine Train → 분류 AI 생성"), img_key="6장")

    add("미션 2", "train / test 분리", [
        "학습 ≠ 암기! 새 데이터로 시험",
        "train.csv / test.csv (캐글 타이타닉)",
        "수집기: 80장 학습 + 20장 시험",
    ], img_key="04_")

    add("미션 2", "에포크·배치", [
        "Epoch: 전체 데이터 반복 횟수",
        "Batch: 한 번에 보는 장수",
        "너무 적음→못 배움 / 너무 많음→외움",
    ])

    add("미션 3", "픽셀 & 정규화", [
        "그림 = 픽셀 모음 (0~255)",
        "÷255 → 0~1 정규화",
        "Colab: DIVISOR = 255",
    ], box=("빈칸", "DIVISOR = ? → 255"), img_key="07_")

    add("미션 3", "합성곱 CNN", [
        "3×3 필터로 선·에지·패턴 추출",
        "Conv2D → MaxPool → Dense",
        "shape: (N, 28, 28, 1)",
    ], img_key="07_")

    add("미션 4", "데이터 편향", [
        "옆면 자동차만 → 앞면 실패",
        "정면 고양이만 → 옆모습 오인식",
        "해결: 크기·방향·위치 다양화",
    ], img_key="04_")

    add("미션 4", "우리 팀 다짐", [
        "수집기에서 지킬 규칙 1가지 적기",
        "예: 3가지 크기 + 2가지 방향",
        "팀원마다 다른 스타일로 그리기",
    ], box=("실습", "필기란에 팀 규칙 작성"))

    add("미션 5", "Confusion Matrix", [
        "정답 vs 예측 표 · 대각선=정답",
        "90%여도 특정 쌍만 틀릴 수 있음",
        "→ 그 클래스 데이터 더 모으기",
    ], img_key="07_")

    add("미션 6", "코딩 4종", [
        "변수 DIVISOR=255 · 리스트 labels",
        "함수 add_conv_block()",
        "for/if로 모든 이미지 정규화",
    ], tip="import numpy as np — 라이브러리=도서관")

    add("미션 6", "코딩 빈칸 퀴즈", [
        "for img in images: img = img / 255",
        "→ 모든 이미지에 반복 적용",
        "Colab TODO 칸을 직접 채워보자!",
    ], img_key="03_")

    add("제2부", "2시간차 완료", [
        "✅ 6미션 퀴즈 클리어",
        "✅ CNN·편향·Confusion Matrix",
        "➡️ 나만의 퀵드로우 수집기",
    ])

    # 제3부 23-32 (10장)
    add("제3부", "수집기란?", [
        "Colab 전 사전 체험 — 데이터 직접 생성",
        "한 물체(자동차) 자유롭게 그리기",
        "로컬 테스트로 오인식 관찰",
    ], hero=True, img_key="07_")

    add("제3부", "수집기 사용법", [
        "이름·물체 이름 입력 → 그림 제출",
        "전체 제출 이미지 모아보기",
        "Apps Script → 스프레드시트 저장",
    ])

    add("제3부", "다양한 데이터 미션", [
        "옆·앞·위 · 크기·위치 바꿔 15장+",
        "실험: 옆면만 vs 다양하게",
        "결과 차이 팀 토론",
    ], box=("관찰", "어떤 그림을 못 맞히나?"), img_key="07_")

    add("제3부", "편향 일지", [
        "처음 데이터 특징",
        "오인식 사례",
        "개선 방법 → 변화 기록",
    ])

    add("제3부", "왜 AI가 틀릴까?", [
        "모델 탓 ❌ → 데이터 탓 ⭕",
        "한 줄: 우리 데이터가 어떻게 모였나?",
        "1분 팀 발표",
    ])

    add("제3부", "수집기→Colab", [
        "JSON 다운로드 (선택)",
        "노트북 2.5단계에서 합치기",
        "수집기 경험이 Colab 성능에 반영!",
    ], img_key="03_")

    add("제3부", "체크리스트", [
        "□ 물체 정하고 수집", "□ 충분히 그리기",
        "□ 오인식 기록", "□ 다양화 후 재테스트",
        "□ 한 줄 정리",
    ])

    add("제3부", "팀 토론 3분", [
        "Q1. 우리 데이터 어디에 치우쳤나?",
        "Q2. 추가하면 좋을 그림은?",
        "Q3. Colab에서 기대하는 변화는?",
    ], box=("발표", "팀 대표 1분 공유"))

    add("제3부", "3시간차 정리", [
        "편향은 책 속 개념이 아닌 '방금 겪은 일'",
        "다음: 미드저니로 아트도 다양하게!",
    ])

    # 제4부 33-40 (8장)
    add("제4부", "미드저니 게임 아트", [
        "① 로고 ② 마스코트 ③ 배경",
        "midjourney.com/imagine",
    ], hero=True, img_key="pptx")

    add("제4부", "프롬프트 공식", [
        "주제 + 스타일 + 색감 + --ar",
        "예: cute cat mascot, flat vector,",
        "pastel colors, white bg --ar 1:1",
    ])

    add("제4부", "웹앱 프롬프트 도구", [
        "용도·주제·스타일·비율 선택",
        "자동 생성 → 복사·붙여넣기",
    ])

    add("제4부", "베이직 플랜 팁", [
        "Fast 시간 제한 → 4~6장만",
        "프롬프트 팀 합의 후 제작",
        "Upscale·다운로드",
    ], tip="정답 캐릭터를 정면·측면·원근 각 1장")

    add("제4부", "게임 완성도 UP", [
        "통일 디자인 (색감·선 두께)",
        "정답 보상 / 힌트 이미지 분리",
        "프롬프트 1단어 실험 3회",
    ])

    add("제4부", "프롬프트 실험 노트", [
        "같은 주제에서 단어 1개만 바꿔 3회 생성",
        "결과 스크린샷 + 차이 한 줄 기록",
        "팀 최종 프롬프트 합의",
    ])

    add("제4부", "Colab 아트 연동", [
        "USE_MIDJOURNEY_ART=True (선택)",
        "업로드 아트 ↔ 클래스 라벨 매칭",
    ])

    add("제4부", "4시간차 완료", [
        "✅ 3종 아트 다운로드",
        "➡️ Colab 코딩 시작",
    ])

    # 제5부 41-54 (14장)
    add("제5부", "Colab 시작!", [
        "브라우저만으로 파이썬·AI",
        "웹앱 버튼 또는 ipynb 업로드",
    ], hero=True, img_key="colab")

    add("제5부", "노트북 7단계", [
        "1설치 2데이터 2.5JSON 3확인",
        "4학습준비 5모델 6성적 7게임",
    ])

    add("제5부", "2단계 클래스 선택", [
        "3~5개 라벨 (cat, apple, car…)",
        "팀 테마 통일 추천",
    ], img_key="07_")

    add("제5부", "4단계 TODO", [
        "DIVISOR = 255",
        "CHANNELS = 1 (흑백)",
        "직접 채워야 실행됨!",
    ], box=("✍️", "코드 작성 체크리스트 확인"))

    add("제5부", "5단계 TODO", [
        "ACTIVATION = 'relu'",
        "FILTERS = 32, 64…",
        "add_conv_block() 함수 완성",
    ], img_key="07_")

    add("제5부", "model.fit 학습", [
        "epochs=5~15 · batch=32/64",
        "validation_split=0.2~0.3",
        "순서대로 셀 실행!",
    ])

    add("제5부", "정확도 & Confusion Matrix", [
        "70%+ 훌륭 · 85%+ 매우 우수",
        "어떤 클래스끼리 헷갈리나?",
    ])

    add("제5부", "Gradio 게임", [
        "펜마우스로 그리면 실시간 예측",
        "미드저니 아트로 꾸미기",
    ], img_key="drawing")

    add("제5부", "코드 작성 체크리스트", [
        "□ DIVISOR · CHANNELS",
        "□ ACTIVATION · FILTERS",
        "□ add_conv_block() 완성",
        "□ model.fit · accuracy 기록",
    ], img_key="03_")

    add("제5부", "디버깅 가이드", [
        "NameError → 위 셀 재실행",
        "Shape 오류 → (N,28,28,1)",
        "런타임 끊김 → 재연결",
    ])

    add("제5부", "하이퍼파라미터 실험", [
        "FILTERS·EPOCHS 바꿔보기",
        "변경값 / 정확도 / 느낀 점 기록",
    ])

    add("제5부", "펜마우스 테스트", [
        "클래스당 3장 그리기",
        "맞힌/틀린 스크린샷",
        "데이터 관점 설명",
    ])

    add("제5부", "팀 완성 체크", [
        "□ TODO 작성 □ Gradio 공유",
        "□ 아트 적용 □ accuracy 기록",
    ])

    add("제5부", "5~6시간차 완료", [
        "데이터→코드→게임 전 과정 경험!",
        "자신만의 퀵드로우 탄생 🎉",
    ])

    # 제6부 55-60 (6장)
    add("제6부", "발표 템플릿", [
        "게임 소개 · 데이터 전략",
        "핵심 코드 · 정확도",
        "AI가 틀린 이유 (데이터 관점)",
    ])

    add("제6부", "토론 질문", [
        "못 맞힌 그림은?",
        "데이터 치우치면?",
        "다양하게 그리면?",
    ])

    add("제6부", "학습지 제출", [
        "생성/분류 AI · 편향 기록",
        "정확도 · 성찰",
        "웹앱 '학습지 작성·제출' 탭",
    ])

    add("제6부", "참고 & 데이터 저장", [
        "수집기: collector-submissions-2026",
        "학습지: worksheet-submissions-2026",
        "Apps Script 스프레드시트에서 확인",
    ], tip="웹앱 참고자료 탭에서 링크 모음")

    add("부록", "핵심 용어 & 링크", [
        "CNN·편향·정규화·에포크",
        "quickdraw.withgoogle.com",
        "colab.research.google.com",
        "teachablemachine.withgoogle.com",
    ], two_col_bullets=[
        "생성형 AI", "분류 AI",
        "Confusion Matrix", "미드저니",
    ])

    add("부록", "퀴즈 정답", [
        "DIVISOR=255 · shape=(N,28,28,1)",
        "편향→데이터 다양화",
        "for img in images → 반복",
    ])

    add("마무리", "수고하셨습니다!", [
        "AI = 데이터 + 코드 + 상상력",
        "오늘 만든 게임을 계속 업그레이드해 보세요!",
        "🎨 🤖 💖",
    ], hero=True)

    assert len(S) == 60, f"슬라이드 수 {len(S)} != 60"
    return S


def build_manuscript() -> Path:
    register_fonts()
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    pool = ImagePool()
    slides = build_slides()

    c = canvas.Canvas(str(OUTPUT), pagesize=(SLIDE_W, SLIDE_H))
    c.setTitle("학생용 강의원고 — 나만의 커스텀 퀵드로우")
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
