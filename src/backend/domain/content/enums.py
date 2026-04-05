from __future__ import annotations

from enum import StrEnum


class TrackType(StrEnum):
    LANGUAGE = "language"
    CULTURE = "culture"
    HISTORY = "history"

    @property
    def title(self) -> str:
        titles = {
            TrackType.LANGUAGE: "Язык",
            TrackType.CULTURE: "Культура",
            TrackType.HISTORY: "История",
        }
        return titles[self]

    @property
    def subtitle(self) -> str:
        subtitles = {
            TrackType.LANGUAGE: "Фразы, грамматика и живые контексты",
            TrackType.CULTURE: "Повседневность, ритуалы и социальные коды",
            TrackType.HISTORY: "Эпохи, переломы и люди, которые меняли страну",
        }
        return subtitles[self]
