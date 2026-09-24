from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from src.domain.value_objects import (
    BatchGenerationState,
    Timestamp,
    TrackType,
    UserID,
)


@dataclass
class LearningSession:
    """Доменная модель учебной сессии.

    Хранит не только номер последней партии, но и ход её генерации: партия
    бронируется до обращения к модели и дописывается карточка за карточкой,
    поэтому страница должна отличать «готово» от «ещё генерируется» и «сорвалось».

    Атрибуты:
        user_id: Владелец сессии.
        track: Тип трека.
        last_generated_batch: Номер последней забронированной или сгенерированной партии.
        updated_at: Момент последнего изменения записи.
        generation_state: Текущее состояние генерации партии.
        generation_started_at: Момент брони партии либо None для готовых партий.
    """

    user_id: UserID
    track: TrackType
    last_generated_batch: int
    updated_at: Timestamp
    generation_state: BatchGenerationState = BatchGenerationState.READY
    generation_started_at: Timestamp | None = None

    @classmethod
    def create(cls, user_id: UserID, track: TrackType) -> LearningSession:
        """Создаёт новую учебную сессию.

        Args:
            user_id: Идентификатор пользователя.
            track: Тип трека.

        Returns:
            Новая учебная сессия.
        """
        timestamp = Timestamp.now()
        return cls(
            user_id=user_id,
            track=track,
            last_generated_batch=0,
            updated_at=timestamp,
        )

    @property
    def is_generating(self) -> bool:
        """Бронируется ли сейчас партия и дописывается ли она фоном."""
        return self.generation_state is BatchGenerationState.GENERATING

    def reserve_next_batch(self, *, started_at: Timestamp | None = None) -> int:
        """Забронировать следующую партию и перевести сессию в генерацию.

        Возвращает номер, под которым карточки будут появляться в базе, чтобы
        страница сразу знала, за какой партией следить.

        Args:
            started_at: Момент брони; по умолчанию текущее время.

        Returns:
            Номер забронированной партии.
        """
        self.last_generated_batch += 1
        self.generation_state = BatchGenerationState.GENERATING
        self.generation_started_at = started_at or Timestamp.now()
        self.updated_at = self.updated_at.refresh()
        return self.last_generated_batch

    def finish_generation(self) -> None:
        """Отметить партию сгенерированной."""
        self.generation_state = BatchGenerationState.READY
        self.generation_started_at = None
        self.updated_at = self.updated_at.refresh()

    def retry_generation(self) -> int:
        """Повторить генерацию той же партии.

        Номер не увеличивается: оборвавшуюся партию надо дописать, а не бросить
        наполовину заполненной и не уйти в новую. Иначе незакрытая партия
        навсегда осталась бы в базе, а проверка «сначала закрой текущую»
        заблокировала бы пользователю любой дальнейший шаг.

        Returns:
            Номер партии, которую надо дописать.
        """
        self.generation_state = BatchGenerationState.GENERATING
        self.generation_started_at = Timestamp.now()
        self.updated_at = self.updated_at.refresh()
        return self.last_generated_batch

    def fail_generation(self) -> None:
        """Отметить генерацию оборванной: партия неполная, нужен повтор."""
        self.generation_state = BatchGenerationState.FAILED
        self.updated_at = self.updated_at.refresh()

    @property
    def needs_retry(self) -> bool:
        """Требуется ли дозаполнение оборвавшейся партии."""
        return self.generation_state is BatchGenerationState.FAILED

    def advance_batch(self) -> None:
        """Увеличивает номер последнего сгенерированного батча."""
        self.last_generated_batch += 1
        self.updated_at = self.updated_at.refresh()

    def is_generation_stale(self, timeout_seconds: int) -> bool:
        """Зависла ли генерация дольше допустимого.

        Нужно потому, что фоновая задача может погибнуть вместе с процессом:
        без этого сессия навсегда остаётся в состоянии генерации и блокирует
        пользователю и страницу, и следующую партию.

        Args:
            timeout_seconds: Сколько секунд генерация считается живая.

        Returns:
            True, если партия генерируется и время брони превысило порог.
        """
        if not self.is_generating or self.generation_started_at is None:
            return False
        elapsed = Timestamp.now().value - self.generation_started_at.value
        return elapsed > timedelta(seconds=timeout_seconds)
