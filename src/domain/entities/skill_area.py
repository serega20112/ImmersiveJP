from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SkillArea:
    """Область навыка из диагностики.

    Отвечает на вопрос «что именно у человека просело» и связывает ответ с
    учебной программой. Заголовок служит человеку и нейросети в промптах,
    код — коду: по нему сверяют этап плана и подбирают подсказку для речи, не
    завися от переименования.

    Атрибуты:
        code: Устойчивый программный идентификатор вида basic-sentence-order.
        title: Название области навыков.
        stage_position: Позиция этапа программы, к которому относится область,
            либо None, если этап не определён.
        coaching_tip: Подсказка по произношению для речевой практики, либо None.
    """

    code: str
    title: str
    stage_position: int | None = None
    coaching_tip: str | None = None
