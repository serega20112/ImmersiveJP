from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CourseTopic:
    """Тема учебной программы — минимальная единица изучения.

    Атрибуты:
        id: Идентификатор темы.
        title: Название темы.
        position: Порядок темы внутри модуля.
    """

    id: int
    title: str
    position: int = 1


@dataclass(slots=True)
class CourseModule:
    """Модуль учебной программы, объединяющий темы одной грани этапа.

    Атрибуты:
        id: Идентификатор модуля.
        code: Устойчивый программный идентификатор вида basic-grammar.particles.
        title: Название модуля.
        position: Порядок модуля внутри этапа.
        topics: Темы модуля.
    """

    id: int
    code: str
    title: str
    position: int = 1
    topics: list[CourseTopic] = field(default_factory=list)


@dataclass(slots=True)
class CourseStage:
    """Этап учебной программы.

    Этап — это не срок в календаре, а уровень, на котором набор тем перестаёт
    требовать предыдущего. Название и описание служат человеку, а code — коду:
    по нему сверяются ссылки из диагностики и генерации, не завися от переименования.

    Атрибуты:
        id: Идентификатор этапа.
        code: Устойчивый программный идентификатор вида basic-grammar.
        title: Название этапа.
        timeframe: Ориентир по срокам.
        summary: Описание этапа.
        position: Порядок этапа в программе.
        modules: Модули этапа.
    """

    id: int
    code: str
    title: str
    timeframe: str
    summary: str
    position: int = 0
    modules: list[CourseModule] = field(default_factory=list)
