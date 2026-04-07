from __future__ import annotations

from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

import anyio
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.backend.domain.content import TrackType
from src.backend.dto.learning_dto import CardExampleDTO, KeyTermDTO, TrackCardDTO


class PdfBuilder:
    _BODY_FONT = "HeiseiMin-W3"
    _HEADING_FONT = "HeiseiKakuGo-W5"
    _PAPER = colors.HexColor("#F7F1E6")
    _PANEL = colors.HexColor("#FFFDF8")
    _INK = colors.HexColor("#1F252C")
    _MUTED = colors.HexColor("#67707A")
    _LINE = colors.HexColor("#D7C9B2")
    _SAND = colors.HexColor("#EFE5D5")

    def __init__(self):
        registered = set(pdfmetrics.getRegisteredFontNames())
        if self._BODY_FONT not in registered:
            pdfmetrics.registerFont(UnicodeCIDFont(self._BODY_FONT))
        if self._HEADING_FONT not in registered:
            pdfmetrics.registerFont(UnicodeCIDFont(self._HEADING_FONT))

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

    @classmethod
    def _build_pdf_sync(
        cls,
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
            topMargin=24 * mm,
            bottomMargin=18 * mm,
            title=f"ImmersJP - {track.title}",
            author="ImmersJP",
            pageCompression=1,
        )
        styles = cls._build_styles(track)
        story = cls._build_cover_story(
            user_display_name=user_display_name,
            track=track,
            card_count=len(cards),
            content_width=document.width,
            styles=styles,
        )
        story.append(PageBreak())
        story.extend(
            cls._build_intro_story(
                track=track,
                card_count=len(cards),
                content_width=document.width,
                styles=styles,
            )
        )

        for index, card in enumerate(cards, start=1):
            story.append(
                cls._build_card_block(
                    card=card,
                    index=index,
                    content_width=document.width,
                    styles=styles,
                    track=track,
                )
            )
            story.append(Spacer(1, 7 * mm))

        def draw_cover(canvas, doc):
            cls._draw_cover_page(canvas, doc, track)

        def draw_page(canvas, doc):
            cls._draw_content_page(canvas, doc, track, user_display_name)

        document.build(story, onFirstPage=draw_cover, onLaterPages=draw_page)
        return buffer.getvalue()

    @classmethod
    def _build_styles(cls, track: TrackType) -> dict[str, ParagraphStyle]:
        styles = getSampleStyleSheet()
        accent = cls._accent(track)
        accent_soft = cls._accent_soft(track)

        return {
            "cover_brand": ParagraphStyle(
                "PdfCoverBrand",
                parent=styles["Title"],
                fontName=cls._HEADING_FONT,
                fontSize=30,
                leading=34,
                textColor=colors.white,
                alignment=TA_CENTER,
                spaceAfter=4,
            ),
            "cover_track": ParagraphStyle(
                "PdfCoverTrack",
                parent=styles["Heading2"],
                fontName=cls._BODY_FONT,
                fontSize=12,
                leading=16,
                textColor=colors.HexColor("#F8EFE0"),
                alignment=TA_CENTER,
                spaceAfter=10,
            ),
            "cover_title": ParagraphStyle(
                "PdfCoverTitle",
                parent=styles["Heading1"],
                fontName=cls._HEADING_FONT,
                fontSize=20,
                leading=26,
                textColor=cls._INK,
                alignment=TA_CENTER,
                spaceAfter=8,
            ),
            "cover_body": ParagraphStyle(
                "PdfCoverBody",
                parent=styles["BodyText"],
                fontName=cls._BODY_FONT,
                fontSize=11.2,
                leading=17,
                textColor=cls._INK,
                alignment=TA_CENTER,
            ),
            "section_kicker": ParagraphStyle(
                "PdfSectionKicker",
                parent=styles["BodyText"],
                fontName=cls._HEADING_FONT,
                fontSize=8.8,
                leading=10,
                textColor=accent,
                spaceAfter=4,
            ),
            "section_title": ParagraphStyle(
                "PdfSectionTitle",
                parent=styles["Heading2"],
                fontName=cls._HEADING_FONT,
                fontSize=16,
                leading=20,
                textColor=cls._INK,
                spaceAfter=6,
            ),
            "body": ParagraphStyle(
                "PdfBody",
                parent=styles["BodyText"],
                fontName=cls._BODY_FONT,
                fontSize=10.4,
                leading=16,
                textColor=cls._INK,
                alignment=TA_JUSTIFY,
                wordWrap="CJK",
            ),
            "body_small": ParagraphStyle(
                "PdfBodySmall",
                parent=styles["BodyText"],
                fontName=cls._BODY_FONT,
                fontSize=9.3,
                leading=14,
                textColor=cls._MUTED,
                wordWrap="CJK",
            ),
            "metric_label": ParagraphStyle(
                "PdfMetricLabel",
                parent=styles["BodyText"],
                fontName=cls._HEADING_FONT,
                fontSize=8.5,
                leading=10,
                textColor=accent,
                spaceAfter=2,
            ),
            "metric_value": ParagraphStyle(
                "PdfMetricValue",
                parent=styles["BodyText"],
                fontName=cls._BODY_FONT,
                fontSize=10.4,
                leading=14,
                textColor=cls._INK,
                wordWrap="CJK",
            ),
            "card_meta": ParagraphStyle(
                "PdfCardMeta",
                parent=styles["BodyText"],
                fontName=cls._HEADING_FONT,
                fontSize=8.5,
                leading=10,
                textColor=accent,
            ),
            "card_title": ParagraphStyle(
                "PdfCardTitle",
                parent=styles["Heading3"],
                fontName=cls._HEADING_FONT,
                fontSize=15.4,
                leading=20,
                textColor=cls._INK,
                wordWrap="CJK",
            ),
            "subhead": ParagraphStyle(
                "PdfSubhead",
                parent=styles["BodyText"],
                fontName=cls._HEADING_FONT,
                fontSize=9,
                leading=12,
                textColor=accent,
            ),
            "table_head": ParagraphStyle(
                "PdfTableHead",
                parent=styles["BodyText"],
                fontName=cls._HEADING_FONT,
                fontSize=8.4,
                leading=10,
                textColor=cls._INK,
            ),
            "example_japanese": ParagraphStyle(
                "PdfExampleJapanese",
                parent=styles["BodyText"],
                fontName=cls._BODY_FONT,
                fontSize=10,
                leading=13,
                textColor=cls._INK,
                wordWrap="CJK",
            ),
            "example_meta": ParagraphStyle(
                "PdfExampleMeta",
                parent=styles["BodyText"],
                fontName=cls._BODY_FONT,
                fontSize=9.1,
                leading=12.5,
                textColor=cls._MUTED,
                wordWrap="CJK",
            ),
            "term": ParagraphStyle(
                "PdfTerm",
                parent=styles["BodyText"],
                fontName=cls._BODY_FONT,
                fontSize=9.2,
                leading=12,
                textColor=cls._INK,
                alignment=TA_CENTER,
                wordWrap="CJK",
            ),
            "divider_label": ParagraphStyle(
                "PdfDividerLabel",
                parent=styles["BodyText"],
                fontName=cls._BODY_FONT,
                fontSize=8.5,
                leading=10,
                textColor=accent_soft,
                alignment=TA_CENTER,
            ),
        }

    @classmethod
    def _build_cover_story(
        cls,
        *,
        user_display_name: str,
        track: TrackType,
        card_count: int,
        content_width: float,
        styles: dict[str, ParagraphStyle],
    ) -> list:
        issued_at = datetime.now().strftime("%d.%m.%Y")
        metrics = Table(
            [
                [
                    cls._metric_panel("Пользователь", user_display_name, styles),
                    cls._metric_panel("Трек", track.title, styles),
                ],
                [
                    cls._metric_panel("Карточек внутри", str(card_count), styles),
                    cls._metric_panel("Собрано", issued_at, styles),
                ],
            ],
            colWidths=[content_width / 2, content_width / 2],
        )
        metrics.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        return [
            Spacer(1, 58 * mm),
            Paragraph("ImmersJP", styles["cover_brand"]),
            Paragraph(f"{cls._track_mark(track)} / {track.subtitle}", styles["cover_track"]),
            Spacer(1, 10 * mm),
            Paragraph(f"Личный PDF-конспект по треку «{escape(track.title)}»", styles["cover_title"]),
            Paragraph(
                "Собранный материал рассчитан на спокойное повторение офлайн: тема, разбор, примеры и ключевые слова идут в одном документе без визуального мусора.",
                styles["cover_body"],
            ),
            Spacer(1, 12 * mm),
            metrics,
            Spacer(1, 9 * mm),
            Paragraph(
                "Используй этот файл как рабочий конспект: сначала перечитай тему, потом проговори примеры и только после этого переходи к следующей карточке.",
                styles["cover_body"],
            ),
        ]

    @classmethod
    def _build_intro_story(
        cls,
        *,
        track: TrackType,
        card_count: int,
        content_width: float,
        styles: dict[str, ParagraphStyle],
    ) -> list:
        intro_table = Table(
            [
                [
                    cls._info_panel(
                        "Структура",
                        "Каждая карточка отделена как самостоятельный блок: тема, разбор, примеры и ключевые слова.",
                        styles,
                    ),
                    cls._info_panel(
                        "Как повторять",
                        "Сначала читай тему целиком, затем проговаривай примеры вслух и возвращайся к терминам только после этого.",
                        styles,
                    ),
                    cls._info_panel(
                        "Объем",
                        f"Внутри файла {card_count} завершенных карточек по треку «{track.title}».",
                        styles,
                    ),
                ]
            ],
            colWidths=[content_width / 3, content_width / 3, content_width / 3],
        )
        intro_table.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        return [
            Paragraph("Конспект", styles["section_kicker"]),
            Paragraph("Материал собран в удобном порядке", styles["section_title"]),
            Paragraph(
                "PDF не пытается заменить живое прохождение карточек. Его задача проще: быстро вернуть в голову структуру темы и примеры, которые уже были пройдены.",
                styles["body"],
            ),
            Spacer(1, 6 * mm),
            intro_table,
            Spacer(1, 7 * mm),
            HRFlowable(
                width="100%",
                thickness=0.6,
                color=cls._LINE,
                spaceBefore=0,
                spaceAfter=0,
            ),
            Spacer(1, 7 * mm),
        ]

    @classmethod
    def _build_card_block(
        cls,
        *,
        card: TrackCardDTO,
        index: int,
        content_width: float,
        styles: dict[str, ParagraphStyle],
        track: TrackType,
    ) -> Table:
        inner_width = content_width - 14 * mm
        rows: list[list[object]] = [
            [Paragraph(
                f"Карточка {index:02d} · партия {card.batch_number} · позиция {card.position:02d}",
                styles["card_meta"],
            )],
            [Paragraph(escape(card.topic), styles["card_title"])],
            [Paragraph(cls._paragraph_markup(card.explanation), styles["body"])],
            [Paragraph("Примеры употребления", styles["subhead"])],
            [cls._build_examples_table(card.examples, inner_width, styles, track)],
        ]

        if card.key_term_items:
            rows.extend(
                [
                    [Paragraph("Ключевые слова", styles["subhead"])],
                    [cls._build_terms_table(card.key_term_items, inner_width, styles, track)],
                ]
            )

        card_table = Table(rows, colWidths=[content_width], splitByRow=1)
        card_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), cls._PANEL),
                    ("BACKGROUND", (0, 0), (-1, 0), cls._accent_soft(track)),
                    ("BOX", (0, 0), (-1, -1), 0.75, cls._LINE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7 * mm),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.6 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.6 * mm),
                    ("TOPPADDING", (0, 0), (-1, 0), 3.2 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 3.2 * mm),
                    ("LINEBELOW", (0, 1), (-1, 1), 0.4, cls._LINE),
                ]
            )
        )
        return card_table

    @classmethod
    def _build_examples_table(
        cls,
        examples: list[CardExampleDTO],
        content_width: float,
        styles: dict[str, ParagraphStyle],
        track: TrackType,
    ) -> Table:
        rows: list[list[Paragraph]] = [
            [
                Paragraph("Японский", styles["table_head"]),
                Paragraph("Ромадзи", styles["table_head"]),
                Paragraph("Перевод", styles["table_head"]),
            ]
        ]
        for item in examples:
            rows.append(
                [
                    Paragraph(cls._paragraph_markup(item.japanese), styles["example_japanese"]),
                    Paragraph(cls._paragraph_markup(item.romaji or "—"), styles["example_meta"]),
                    Paragraph(cls._paragraph_markup(item.translation or "—"), styles["example_meta"]),
                ]
            )

        table = Table(
            rows,
            colWidths=[
                content_width * 0.28,
                content_width * 0.28,
                content_width * 0.44,
            ],
            repeatRows=1,
            splitByRow=1,
        )
        commands = [
            ("BACKGROUND", (0, 0), (-1, 0), cls._accent_soft(track)),
            ("TEXTCOLOR", (0, 0), (-1, 0), cls._INK),
            ("GRID", (0, 0), (-1, -1), 0.45, cls._LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3.2 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3.2 * mm),
            ("TOPPADDING", (0, 0), (-1, -1), 2.4 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4 * mm),
        ]
        for row_index in range(1, len(rows)):
            row_color = cls._PANEL if row_index % 2 else cls._SAND
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), row_color))
        table.setStyle(TableStyle(commands))
        return table

    @classmethod
    def _build_terms_table(
        cls,
        terms: list[KeyTermDTO],
        content_width: float,
        styles: dict[str, ParagraphStyle],
        track: TrackType,
    ) -> Table:
        columns = 3
        prepared_terms = list(terms)
        while len(prepared_terms) % columns:
            prepared_terms.append("")

        rows: list[list[Paragraph]] = []
        for start in range(0, len(prepared_terms), columns):
            chunk = prepared_terms[start : start + columns]
            rows.append(
                [
                    Paragraph(
                        cls._term_markup(item) if item else cls._paragraph_markup(" "),
                        styles["term"],
                    )
                    for item in chunk
                ]
            )

        table = Table(
            rows,
            colWidths=[content_width / columns] * columns,
            splitByRow=1,
        )
        commands = [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2.4 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2.4 * mm),
            ("TOPPADDING", (0, 0), (-1, -1), 2.2 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2 * mm),
        ]

        for row_index, row in enumerate(rows):
            for col_index, term in enumerate(row):
                source_value = prepared_terms[row_index * columns + col_index]
                if not source_value:
                    commands.extend(
                        [
                            ("BACKGROUND", (col_index, row_index), (col_index, row_index), cls._PANEL),
                            ("LINEBELOW", (col_index, row_index), (col_index, row_index), 0, cls._PANEL),
                        ]
                    )
                    continue
                commands.extend(
                    [
                        ("BACKGROUND", (col_index, row_index), (col_index, row_index), cls._accent_soft(track)),
                        ("BOX", (col_index, row_index), (col_index, row_index), 0.45, cls._LINE),
                    ]
                )

        table.setStyle(TableStyle(commands))
        return table

    @classmethod
    def _term_markup(cls, item: KeyTermDTO) -> str:
        label = cls._paragraph_markup(item.label)
        if item.translation:
            translation = cls._paragraph_markup(item.translation)
            return f"<b>{label}</b><br/><font size='8.2'>{translation}</font>"
        return f"<b>{label}</b>"

    @classmethod
    def _metric_panel(
        cls,
        label: str,
        value: str,
        styles: dict[str, ParagraphStyle],
    ) -> Table:
        panel = Table(
            [
                [Paragraph(escape(label), styles["metric_label"])],
                [Paragraph(cls._paragraph_markup(value), styles["metric_value"])],
            ],
            colWidths=["*"],
        )
        panel.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), cls._PANEL),
                    ("BOX", (0, 0), (-1, -1), 0.55, cls._LINE),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4.4 * mm),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4.4 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.4 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.4 * mm),
                ]
            )
        )
        return panel

    @classmethod
    def _info_panel(
        cls,
        title: str,
        text: str,
        styles: dict[str, ParagraphStyle],
    ) -> Table:
        panel = Table(
            [
                [Paragraph(escape(title), styles["subhead"])],
                [Paragraph(cls._paragraph_markup(text), styles["body_small"])],
            ],
            colWidths=["*"],
        )
        panel.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), cls._PANEL),
                    ("BOX", (0, 0), (-1, -1), 0.55, cls._LINE),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.4 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.4 * mm),
                ]
            )
        )
        return panel

    @classmethod
    def _draw_cover_page(cls, canvas, doc, track: TrackType) -> None:
        page_width, page_height = A4
        accent = cls._accent(track)
        accent_deep = cls._accent_deep(track)

        canvas.saveState()
        canvas.setFillColor(cls._PAPER)
        canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)

        canvas.setFillColor(accent_deep)
        canvas.rect(0, page_height - 84 * mm, page_width, 84 * mm, fill=1, stroke=0)

        canvas.setFillColor(accent)
        canvas.rect(14 * mm, 0, 5 * mm, page_height, fill=1, stroke=0)

        canvas.setStrokeColor(colors.HexColor("#F1E7D6"))
        canvas.setLineWidth(0.7)
        canvas.line(28 * mm, page_height - 28 * mm, page_width - 18 * mm, page_height - 28 * mm)

        canvas.setFillColor(colors.HexColor("#EADFC9"))
        canvas.setFont(cls._HEADING_FONT, 26)
        canvas.drawRightString(page_width - 20 * mm, page_height - 20 * mm, cls._track_mark(track))

        canvas.restoreState()

    @classmethod
    def _draw_content_page(
        cls,
        canvas,
        doc,
        track: TrackType,
        user_display_name: str,
    ) -> None:
        page_width, page_height = A4
        accent = cls._accent(track)

        canvas.saveState()
        canvas.setFillColor(cls._PAPER)
        canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)

        canvas.setFillColor(accent)
        canvas.rect(doc.leftMargin, page_height - 12 * mm, doc.width, 2.3 * mm, fill=1, stroke=0)

        canvas.setStrokeColor(cls._LINE)
        canvas.setLineWidth(0.6)
        canvas.line(doc.leftMargin, 12 * mm, doc.leftMargin + doc.width, 12 * mm)

        canvas.setFont(cls._HEADING_FONT, 9)
        canvas.setFillColor(accent)
        canvas.drawString(doc.leftMargin, page_height - 17 * mm, f"ImmersJP / {track.title}")

        canvas.setFont(cls._BODY_FONT, 8.5)
        canvas.setFillColor(cls._MUTED)
        canvas.drawRightString(doc.leftMargin + doc.width, page_height - 17 * mm, user_display_name)
        canvas.drawString(doc.leftMargin, 8 * mm, f"Повторение по треку «{track.title}»")
        canvas.drawRightString(doc.leftMargin + doc.width, 8 * mm, f"Стр. {doc.page}")

        canvas.restoreState()

    @classmethod
    def _paragraph_markup(cls, value: str) -> str:
        return escape(str(value).strip()).replace("\n", "<br/>")

    @classmethod
    def _track_mark(cls, track: TrackType) -> str:
        labels = {
            TrackType.LANGUAGE: "言語",
            TrackType.CULTURE: "文化",
            TrackType.HISTORY: "歴史",
        }
        return labels[track]

    @classmethod
    def _accent(cls, track: TrackType):
        palette = {
            TrackType.LANGUAGE: colors.HexColor("#B14A32"),
            TrackType.CULTURE: colors.HexColor("#4A627B"),
            TrackType.HISTORY: colors.HexColor("#58664C"),
        }
        return palette[track]

    @classmethod
    def _accent_soft(cls, track: TrackType):
        palette = {
            TrackType.LANGUAGE: colors.HexColor("#F0DDD7"),
            TrackType.CULTURE: colors.HexColor("#DEE6EE"),
            TrackType.HISTORY: colors.HexColor("#E3E8DA"),
        }
        return palette[track]

    @classmethod
    def _accent_deep(cls, track: TrackType):
        palette = {
            TrackType.LANGUAGE: colors.HexColor("#7D2F1E"),
            TrackType.CULTURE: colors.HexColor("#2F445B"),
            TrackType.HISTORY: colors.HexColor("#3F4B35"),
        }
        return palette[track]
