from __future__ import annotations

from io import BytesIO

import anyio
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from src.backend.domain.content import TrackType
from src.backend.dto.learning_dto import TrackCardDTO


class PdfBuilder:
    def __init__(self):
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

    async def build_cards_pdf(
        self,
        user_display_name: str,
        track: TrackType,
        cards: list[TrackCardDTO],
    ) -> bytes:
        return await anyio.to_thread.run_sync(
            self._build_pdf_sync,
            user_display_name,
            track,
            cards,
        )

    @staticmethod
    def _build_pdf_sync(
        user_display_name: str,
        track: TrackType,
        cards: list[TrackCardDTO],
    ) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Title"],
            fontName="HeiseiMin-W3",
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#111827"),
        )
        body_style = ParagraphStyle(
            "BodyStyle",
            parent=styles["BodyText"],
            fontName="HeiseiMin-W3",
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#1f2937"),
        )
        muted_style = ParagraphStyle(
            "MutedStyle",
            parent=body_style,
            textColor=colors.HexColor("#6b7280"),
        )

        story = [
            Paragraph(f"ImmersJP - {track.title}", title_style),
            Spacer(1, 6 * mm),
            Paragraph(f"Конспект пользователя: {user_display_name}", muted_style),
            Spacer(1, 10 * mm),
        ]

        for index, card in enumerate(cards, start=1):
            story.append(Paragraph(f"{index}. {card.topic}", body_style))
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(card.explanation, body_style))
            story.append(Spacer(1, 2 * mm))
            examples = "<br/>".join(
                f"- {item.raw_text}" for item in card.examples
            )
            story.append(Paragraph(f"Примеры:<br/>{examples}", body_style))
            story.append(Spacer(1, 2 * mm))
            key_terms = ", ".join(card.key_terms)
            story.append(Paragraph(f"Ключевые слова: {key_terms}", muted_style))
            story.append(Spacer(1, 6 * mm))

        document.build(story)
        return buffer.getvalue()
