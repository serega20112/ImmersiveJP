from __future__ import annotations

import json
from hashlib import sha256
from json import JSONDecoder

import httpx

from src.backend.dependencies.settings import Settings
from src.backend.domain.content import TrackType
from src.backend.domain.user import User
from src.backend.dto.learning_dto import (
    GeneratedCardDraftDTO,
    SpeechDialogueDTO,
    SpeechDialogueTurnDTO,
    SpeechLineDTO,
    SpeechPracticeDTO,
)
from src.backend.dto.profile_dto import AIAdviceDTO, ProgressReportDTO
from src.backend.infrastructure.cache import KeyValueStore


class HuggingFaceLLMClient:
    _CARDS_CACHE_VERSION = "cards-v3"
    _SPEECH_CACHE_VERSION = "speech-v3"
    _ADVICE_CACHE_VERSION = "advice-v3"

    def __init__(self, store: KeyValueStore):
        self._store = store
        self._http_client = httpx.AsyncClient(timeout=8.0)

    async def generate_cards(
        self,
        user: User,
        track: TrackType,
        batch_number: int,
        batch_size: int,
        previous_topics: list[str],
    ) -> list[GeneratedCardDraftDTO]:
        payload = {
            "kind": "cards",
            "version": self._CARDS_CACHE_VERSION,
            "user_id": user.id,
            "track": track.value,
            "batch_number": batch_number,
            "batch_size": batch_size,
            "goal": user.learning_goal.value if user.learning_goal else None,
            "language_level": (
                user.language_level.value if user.language_level else None
            ),
            "study_timeline": (
                user.study_timeline.value if user.study_timeline else None
            ),
            "interests": user.interests,
            "previous_topics": previous_topics,
            "diagnostic_level": (
                user.skill_assessment.estimated_level.value
                if user.skill_assessment and user.skill_assessment.estimated_level
                else None
            ),
            "diagnostic_summary": (
                user.skill_assessment.summary if user.skill_assessment else None
            ),
            "strengths": (
                list(user.skill_assessment.strengths) if user.skill_assessment else []
            ),
            "weak_points": (
                list(user.skill_assessment.weak_points)
                if user.skill_assessment
                else []
            ),
        }
        cache_key = self._cache_key(payload)
        cached = await self._store.get_json(cache_key)
        if cached is not None:
            return [GeneratedCardDraftDTO.model_validate(item) for item in cached]

        generated = await self._request_cards(payload)
        await self._store.set_json(
            cache_key,
            [item.model_dump() for item in generated],
            expire_seconds=24 * 60 * 60,
        )
        return generated

    async def generate_advice(
        self, user: User, report: ProgressReportDTO
    ) -> AIAdviceDTO:
        payload = {
            "kind": "advice",
            "version": self._ADVICE_CACHE_VERSION,
            "user_id": user.id,
            "goal": user.learning_goal.value if user.learning_goal else None,
            "language_level": (
                user.language_level.value if user.language_level else None
            ),
            "study_timeline": (
                user.study_timeline.value if user.study_timeline else None
            ),
            "interests": user.interests,
            "report": report.model_dump(),
            "diagnostic_level": (
                user.skill_assessment.estimated_level.value
                if user.skill_assessment and user.skill_assessment.estimated_level
                else None
            ),
            "diagnostic_summary": (
                user.skill_assessment.summary if user.skill_assessment else None
            ),
            "strengths": (
                list(user.skill_assessment.strengths) if user.skill_assessment else []
            ),
            "weak_points": (
                list(user.skill_assessment.weak_points)
                if user.skill_assessment
                else []
            ),
        }
        cache_key = self._cache_key(payload)
        cached = await self._store.get_json(cache_key)
        if cached is not None:
            return AIAdviceDTO.model_validate(cached)

        advice = await self._request_advice(user, report)
        await self._store.set_json(
            cache_key, advice.model_dump(), expire_seconds=6 * 60 * 60
        )
        return advice

    async def generate_speech_practice(
        self,
        user: User,
        words: list[str],
    ) -> SpeechPracticeDTO:
        payload = {
            "kind": "speech",
            "version": self._SPEECH_CACHE_VERSION,
            "user_id": user.id,
            "goal": user.learning_goal.value if user.learning_goal else None,
            "language_level": (
                user.language_level.value if user.language_level else None
            ),
            "study_timeline": (
                user.study_timeline.value if user.study_timeline else None
            ),
            "interests": user.interests,
            "words": words,
            "diagnostic_level": (
                user.skill_assessment.estimated_level.value
                if user.skill_assessment and user.skill_assessment.estimated_level
                else None
            ),
            "diagnostic_summary": (
                user.skill_assessment.summary if user.skill_assessment else None
            ),
            "strengths": (
                list(user.skill_assessment.strengths) if user.skill_assessment else []
            ),
            "weak_points": (
                list(user.skill_assessment.weak_points)
                if user.skill_assessment
                else []
            ),
        }
        cache_key = self._cache_key(payload)
        cached = await self._store.get_json(cache_key)
        if cached is not None:
            return SpeechPracticeDTO.model_validate(cached)

        practice = await self._request_speech_practice(payload)
        await self._store.set_json(
            cache_key, practice.model_dump(), expire_seconds=12 * 60 * 60
        )
        return practice

    async def close(self) -> None:
        await self._http_client.aclose()

    async def _request_cards(self, payload: dict) -> list[GeneratedCardDraftDTO]:
        if not Settings.hf_api_token:
            return self._fallback_cards(payload)
        prompt = self._build_cards_prompt(payload)
        try:
            response = await self._http_client.post(
                Settings.hf_api_url,
                headers={
                    "Authorization": f"Bearer {Settings.hf_api_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": Settings.hf_model,
                    "provider": Settings.hf_provider,
                    "temperature": 0.8,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ты методист по Японии. Отвечай только JSON-массивом без текста вне JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return self._normalize_cards(self._extract_json(content), payload)
        except Exception:
            return self._fallback_cards(payload)

    async def _request_advice(
        self, user: User, report: ProgressReportDTO
    ) -> AIAdviceDTO:
        if not Settings.hf_api_token:
            return self._fallback_advice(user, report)
        try:
            response = await self._http_client.post(
                Settings.hf_api_url,
                headers={
                    "Authorization": f"Bearer {Settings.hf_api_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": Settings.hf_model,
                    "provider": Settings.hf_provider,
                    "temperature": 0.6,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Ты редактор учебных рекомендаций ImmersJP. "
                                "Верни только JSON-объект с полями headline, summary, focus_points. "
                                "Тон спокойный, короткий, практический."
                            ),
                        },
                        {
                            "role": "user",
                            "content": self._build_advice_prompt(user, report),
                        },
                    ],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return AIAdviceDTO.model_validate(self._extract_json(content))
        except Exception:
            return self._fallback_advice(user, report)

    async def _request_speech_practice(self, payload: dict) -> SpeechPracticeDTO:
        if not Settings.hf_api_token:
            return self._fallback_speech_practice(payload)
        try:
            response = await self._http_client.post(
                Settings.hf_api_url,
                headers={
                    "Authorization": f"Bearer {Settings.hf_api_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": Settings.hf_model,
                    "provider": Settings.hf_provider,
                    "temperature": 0.7,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Верни только JSON-объект с полями sentences, dialogues, coaching_tip, difficulty_label. "
                                "Тон короткий и практический."
                            ),
                        },
                        {
                            "role": "user",
                            "content": self._build_speech_prompt(payload),
                        },
                    ],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return self._normalize_speech_practice(self._extract_json(content), payload)
        except Exception:
            return self._fallback_speech_practice(payload)

    @staticmethod
    def _cache_key(payload: dict) -> str:
        dumped = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return f"llm:{sha256(dumped.encode('utf-8')).hexdigest()}"

    @staticmethod
    def _extract_json(raw_content: str):
        decoder = JSONDecoder()
        for marker in ("[", "{"):
            start = raw_content.find(marker)
            if start == -1:
                continue
            try:
                parsed, _ = decoder.raw_decode(raw_content[start:])
                return parsed
            except json.JSONDecodeError:
                continue
        raise ValueError("JSON payload was not found in model response")

    @staticmethod
    def _normalize_cards(
        parsed: list[dict], payload: dict
    ) -> list[GeneratedCardDraftDTO]:
        normalized: list[GeneratedCardDraftDTO] = []
        seen_topics: set[str] = set()
        seen_example_signatures: set[tuple[str, ...]] = set()
        for item in parsed[: payload["batch_size"]]:
            topic = str(item.get("topic") or "Тема без названия").strip()
            normalized_topic = topic.casefold()
            if not topic or normalized_topic in seen_topics:
                continue
            if HuggingFaceLLMClient._is_placeholder_topic(topic):
                continue
            key_terms = HuggingFaceLLMClient._normalize_key_terms(
                item.get("key_terms") or [],
                track=str(payload["track"]),
            )[:5]
            normalized_examples = HuggingFaceLLMClient._normalize_card_examples(
                item.get("examples") or []
            )
            if len(normalized_examples) < 3:
                normalized_examples = HuggingFaceLLMClient._build_dynamic_examples(
                    track=str(payload["track"]),
                    context_title=topic,
                    angle_title=topic,
                    base_terms=key_terms,
                )
            example_signature = HuggingFaceLLMClient._example_signature(
                normalized_examples
            )
            if example_signature and example_signature in seen_example_signatures:
                continue
            seen_topics.add(normalized_topic)
            if example_signature:
                seen_example_signatures.add(example_signature)
            normalized.append(
                GeneratedCardDraftDTO(
                    topic=topic,
                    explanation=str(item.get("explanation") or "").strip(),
                    examples=normalized_examples[:3],
                    key_terms=key_terms,
                )
            )
        if len(normalized) < payload["batch_size"]:
            fallback = HuggingFaceLLMClient._fallback_cards(
                payload,
                seen_topics,
                seen_example_signatures,
            )
            for draft in fallback:
                if len(normalized) == payload["batch_size"]:
                    break
                topic_key = draft.topic.casefold()
                if topic_key in seen_topics:
                    continue
                example_signature = HuggingFaceLLMClient._example_signature(
                    draft.examples
                )
                if example_signature and example_signature in seen_example_signatures:
                    continue
                seen_topics.add(topic_key)
                if example_signature:
                    seen_example_signatures.add(example_signature)
                normalized.append(draft)
        return normalized

    @staticmethod
    def _build_cards_prompt(payload: dict) -> str:
        interests = ", ".join(payload["interests"]) or "не указаны"
        previous = ", ".join(payload["previous_topics"]) or "нет"
        return (
            "Сгенерируй карточки-конспекты по Японии.\n"
            f"Трек: {payload['track']}\n"
            f"Цель: {HuggingFaceLLMClient._goal_label(payload.get('goal'))}\n"
            f"Уровень: {HuggingFaceLLMClient._level_label(payload.get('language_level'))}\n"
            f"Горизонт обучения: {HuggingFaceLLMClient._timeline_label(payload.get('study_timeline'))}\n"
            f"Интересы: {interests}\n"
            f"Номер партии: {payload['batch_number']}\n"
            f"Размер партии: {payload['batch_size']}\n"
            f"Избегай повторов тем: {previous}\n"
            f"{HuggingFaceLLMClient._build_generation_context(payload)}\n"
            "Верни JSON-массив, где у каждой карточки есть topic, explanation, examples, key_terms.\n"
            f"{HuggingFaceLLMClient._explanation_length_instruction(payload)}\n"
            "Examples возвращай массивом строк в формате: Japanese | Romaji | Русский перевод.\n"
            "key_terms возвращай массивом из 4-6 строк. Если термин японский, формат каждой строки: Термин | Русский перевод.\n"
            "Если термин уже русский, можно вернуть его как есть или дать короткое пояснение через |.\n"
            "Пиши естественным русским языком без канцелярита и рекламного тона.\n"
            "Не используй английские слова, если есть нормальный русский эквивалент.\n"
            "Не упоминай диагностику пользователя, trust score, тесты, сильные или слабые стороны.\n"
            "Не начинай explanation с формул вроде 'эта карточка про тему', 'смотри на тему', 'для уровня'.\n"
            "Темы внутри партии должны отличаться не только названием, но и сценой применения.\n"
            "Examples должны быть уникальными для карточки и прямо отражать ее тему. Не повторяй один и тот же набор примеров в соседних карточках.\n"
            "Если трек не языковой, все равно давай примеры в удобном формате для быстрого чтения."
        )

    @staticmethod
    def _build_advice_prompt(user: User, report: ProgressReportDTO) -> str:
        return (
            f"Пользователь: {user.display_name}.\n"
            f"Цель: {user.learning_goal.value if user.learning_goal else 'не указана'}.\n"
            f"Уровень: {user.language_level.value if user.language_level else 'не указан'}.\n"
            f"Горизонт обучения: {HuggingFaceLLMClient._timeline_label(user.study_timeline.value if user.study_timeline else None)}.\n"
            f"Интересы: {', '.join(user.interests) or 'не указаны'}.\n"
            f"{HuggingFaceLLMClient._build_skill_context_from_user(user)}\n"
            f"{HuggingFaceLLMClient._timeline_advice_context(user.study_timeline.value if user.study_timeline else None)}\n"
            f"Отчет: {report.model_dump_json()}\n"
            "Верни JSON-объект с полями headline, summary, focus_points.\n"
            "headline: до 5 слов.\n"
            "summary: 1-2 коротких предложения.\n"
            "focus_points: 3 коротких действия.\n"
            "Без рекламного тона, без мотивационных лозунгов, без образных метафор."
        )

    @staticmethod
    def _normalize_speech_practice(parsed: dict, payload: dict) -> SpeechPracticeDTO:
        sentences = [
            HuggingFaceLLMClient._to_speech_line(item)
            for item in parsed.get("sentences") or []
        ]
        dialogues = [
            HuggingFaceLLMClient._to_speech_dialogue(item)
            for item in parsed.get("dialogues") or []
            if isinstance(item, dict)
        ]
        if len(sentences) < 10 or len(dialogues) < 5:
            return HuggingFaceLLMClient._fallback_speech_practice(payload)
        return SpeechPracticeDTO(
            words=list(payload["words"]),
            sentences=sentences[:10],
            dialogues=dialogues[:5],
            coaching_tip=str(parsed.get("coaching_tip") or "").strip()
            or HuggingFaceLLMClient._speech_coaching_tip(payload),
            difficulty_label=str(parsed.get("difficulty_label") or "").strip()
            or HuggingFaceLLMClient._speech_difficulty_label(payload),
        )

    @staticmethod
    def _to_speech_line(item: dict | str) -> SpeechLineDTO:
        if isinstance(item, dict):
            return SpeechLineDTO(
                japanese=str(item.get("japanese") or "").strip(),
                romaji=str(item.get("romaji") or "").strip() or None,
                translation=str(item.get("translation") or "").strip() or None,
            )
        parts = [part.strip() for part in str(item).split("|")]
        if len(parts) >= 3:
            return SpeechLineDTO(
                japanese=parts[0],
                romaji=parts[1],
                translation=parts[2],
            )
        if len(parts) == 2:
            return SpeechLineDTO(japanese=parts[0], translation=parts[1])
        return SpeechLineDTO(japanese=str(item).strip())

    @staticmethod
    def _to_speech_dialogue(item: dict) -> SpeechDialogueDTO:
        turns = []
        for turn in item.get("turns") or []:
            if isinstance(turn, dict):
                turns.append(
                    SpeechDialogueTurnDTO(
                        speaker=str(turn.get("speaker") or "A").strip() or "A",
                        japanese=str(turn.get("japanese") or "").strip(),
                        romaji=str(turn.get("romaji") or "").strip() or None,
                        translation=str(turn.get("translation") or "").strip() or None,
                    )
                )
                continue
            line = HuggingFaceLLMClient._to_speech_line(turn)
            turns.append(
                SpeechDialogueTurnDTO(
                    speaker="A",
                    japanese=line.japanese,
                    romaji=line.romaji,
                    translation=line.translation,
                )
            )
        return SpeechDialogueDTO(
            title=str(item.get("title") or "Диалог").strip(),
            scenario=str(item.get("scenario") or "").strip(),
            turns=turns,
        )

    @staticmethod
    def _build_speech_prompt(payload: dict) -> str:
        words = ", ".join(payload["words"]) or "слов нет"
        interests = ", ".join(payload["interests"]) or "не указаны"
        return (
            "Собери разговорную тренировку для ImmersJP.\n"
            f"Цель: {HuggingFaceLLMClient._goal_label(payload.get('goal'))}\n"
            f"Самооценка уровня: {HuggingFaceLLMClient._level_label(payload.get('language_level'))}\n"
            f"Горизонт обучения: {HuggingFaceLLMClient._timeline_label(payload.get('study_timeline'))}\n"
            f"Интересы: {interests}\n"
            f"Слова: {words}\n"
            f"{HuggingFaceLLMClient._build_generation_context(payload)}\n"
            "Верни JSON-объект.\n"
            "sentences: массив из 10 объектов с полями japanese, romaji, translation.\n"
            "dialogues: массив из 5 объектов с полями title, scenario, turns.\n"
            "turns: массив объектов с полями speaker, japanese, romaji, translation.\n"
            "coaching_tip: 1 короткое практическое предложение.\n"
            "difficulty_label: 2-3 слова без рекламного тона.\n"
            "Используй максимум слов из списка и делай материал пригодным для проговаривания."
        )

    @staticmethod
    def _build_skill_context(payload: dict) -> str:
        details = [
            (
                f"Диагностический уровень: {HuggingFaceLLMClient._level_label(payload.get('diagnostic_level'))}"
                if payload.get("diagnostic_level")
                else None
            ),
            (
                f"Сильные стороны: {', '.join(payload.get('strengths') or [])}"
                if payload.get("strengths")
                else None
            ),
            (
                f"Слабые стороны: {', '.join(payload.get('weak_points') or [])}"
                if payload.get("weak_points")
                else None
            ),
        ]
        lines = [line for line in details if line]
        return "\n".join(lines) if lines else "Диагностика пока не заполнена."

    @staticmethod
    def _build_skill_context_from_user(user: User) -> str:
        if user.skill_assessment is None:
            return "Диагностика пока не заполнена."
        payload = {
            "diagnostic_level": (
                user.skill_assessment.estimated_level.value
                if user.skill_assessment.estimated_level
                else None
            ),
            "diagnostic_summary": user.skill_assessment.summary,
            "strengths": user.skill_assessment.strengths,
            "weak_points": user.skill_assessment.weak_points,
        }
        return HuggingFaceLLMClient._build_skill_context(payload)

    @staticmethod
    def _fallback_cards(
        payload: dict,
        excluded_topics: set[str] | None = None,
        excluded_example_signatures: set[tuple[str, ...]] | None = None,
    ) -> list[GeneratedCardDraftDTO]:
        interests = ", ".join(payload.get("interests") or []) or "живой контекст"
        library = {
            "language": [
                (
                    "Приветствия без учебниковой скуки",
                    "Когда и почему меняется тон японского приветствия.",
                    [
                        "おはようございます。 | ohayou gozaimasu. | Доброе утро.",
                        "こんにちは。 | konnichiwa. | Добрый день.",
                        "こんばんは。 | konbanwa. | Добрый вечер.",
                    ],
                    ["挨拶", "丁寧", "会話"],
                ),
                (
                    "Самопрезентация в реальном диалоге",
                    "Минимальный набор фраз, чтобы представиться естественно.",
                    [
                        "はじめまして。 | hajimemashite. | Приятно познакомиться.",
                        "セルゲイです。 | seregei desu. | Я Сергей.",
                        "よろしくお願いします。 | yoroshiku onegaishimasu. | Рассчитываю на хорошее общение.",
                    ],
                    ["自己紹介", "名前", "よろしく"],
                ),
                (
                    "Просьба и вежливость",
                    "Как просить мягко и не звучать резко.",
                    [
                        "水をください。 | mizu o kudasai. | Дайте, пожалуйста, воды.",
                        "もう一度お願いします。 | mou ichido onegaishimasu. | Повторите, пожалуйста, еще раз.",
                        "手伝ってもらえますか。 | tetsudatte moraemasu ka. | Можете помочь?",
                    ],
                    ["ください", "お願い", "丁寧"],
                ),
                (
                    "Город и транспорт",
                    "Язык станции, маршрута и коротких вопросов на улице.",
                    [
                        "駅はどこですか。 | eki wa doko desu ka. | Где станция?",
                        "この電車は新宿に行きますか。 | kono densha wa shinjuku ni ikimasu ka. | Этот поезд идет в Синдзюку?",
                        "ここから遠いですか。 | koko kara tooi desu ka. | Это далеко отсюда?",
                    ],
                    ["駅", "電車", "道"],
                ),
                (
                    "Покупка в магазине",
                    "Что чаще всего звучит у кассы и в торговом зале.",
                    [
                        "これをください。 | kore o kudasai. | Мне вот это, пожалуйста.",
                        "袋はいりません。 | fukuro wa irimasen. | Пакет не нужен.",
                        "カードで払えますか。 | kaado de haraemasu ka. | Можно оплатить картой?",
                    ],
                    ["買う", "袋", "カード"],
                ),
                (
                    "Еда и предпочтения",
                    "Как объяснить вкусы и ограничения без сложной грамматики.",
                    [
                        "魚が好きです。 | sakana ga suki desu. | Я люблю рыбу.",
                        "辛いものは苦手です。 | karai mono wa nigate desu. | Острое мне дается тяжело.",
                        "肉は食べません。 | niku wa tabemasen. | Я не ем мясо.",
                    ],
                    ["好き", "苦手", "食べる"],
                ),
                (
                    "Реакции в разговоре",
                    "Короткие фразы, которые делают речь живой.",
                    [
                        "なるほど。 | naruhodo. | Понятно.",
                        "本当ですか。 | hontou desu ka. | Правда?",
                        "すごいですね。 | sugoi desu ne. | Ничего себе.",
                    ],
                    ["反応", "自然", "会話"],
                ),
                (
                    "Язык учебы",
                    "Фразы, с которыми проще учиться и уточнять непонятное.",
                    [
                        "この漢字はどう読みますか。 | kono kanji wa dou yomimasu ka. | Как читается этот кандзи?",
                        "もう少しゆっくりお願いします。 | mou sukoshi yukkuri onegaishimasu. | Можно немного медленнее?",
                        "メモしてもいいですか。 | memo shite mo ii desu ka. | Можно я запишу?",
                    ],
                    ["漢字", "読む", "勉強"],
                ),
                (
                    "Рабочая вежливость",
                    "Фразы для переписки и коротких рабочих диалогов.",
                    [
                        "確認します。 | kakunin shimasu. | Я проверю.",
                        "少々お待ちください。 | shoushou omachi kudasai. | Пожалуйста, немного подождите.",
                        "共有ありがとうございます。 | kyouyuu arigatou gozaimasu. | Спасибо за информацию.",
                    ],
                    ["確認", "共有", "仕事"],
                ),
                (
                    "Частицы без боли",
                    "Как частицы держат каркас японского предложения.",
                    [
                        "私は学生です。 | watashi wa gakusei desu. | Я студент.",
                        "東京に行きます。 | toukyou ni ikimasu. | Я еду в Токио.",
                        "日本語が好きです。 | nihongo ga suki desu. | Мне нравится японский язык.",
                    ],
                    ["は", "に", "が"],
                ),
            ],
            "culture": [
                (
                    "Тишина как уважение",
                    "Почему в общественных местах Японии тишина воспринимается как социальная норма.",
                    [
                        "В поезде стараются не говорить громко.",
                        "Телефонный звонок быстро глушат или сбрасывают.",
                        "Тишина защищает общее пространство.",
                    ],
                    ["respect", "public space", "train"],
                ),
                (
                    "Дом и улица",
                    "Граница между внешним и домашним пространством в японском быту.",
                    [
                        "Обувь снимают у входа.",
                        "Есть отдельные тапочки для дома.",
                        "Порог genkan задает ритуал входа.",
                    ],
                    ["genkan", "home", "ritual"],
                ),
                (
                    "Сезонность в повседневности",
                    "Смена сезона чувствуется в меню, декоре и социальных ритуалах.",
                    [
                        "Весенние сладости отличаются от осенних.",
                        "Праздники привязаны к времени года.",
                        "Сезонность работает как способ замечать мир.",
                    ],
                    ["season", "food", "ritual"],
                ),
                (
                    "Очередь и порядок",
                    "Как японская городская дисциплина проявляется в мелочах.",
                    [
                        "Люди выстраиваются по разметке.",
                        "Очередь работает даже без контроля.",
                        "Нарушение порядка быстро считывается.",
                    ],
                    ["queue", "city", "discipline"],
                ),
                (
                    "Подарок и упаковка",
                    "Упаковка в Японии часто равна самому жесту внимания.",
                    [
                        "Подарок тщательно заворачивают.",
                        "Внешний вид вещи считается частью опыта.",
                        "Упаковка показывает уважение.",
                    ],
                    ["gift", "service", "presentation"],
                ),
                (
                    "Matsuri как жизнь района",
                    "Локальные фестивали держатся не на туристах, а на соседстве и памяти места.",
                    [
                        "Храм становится центром района.",
                        "Подготовка идет заранее.",
                        "Праздник собирает сообщество вокруг общего ритма.",
                    ],
                    ["matsuri", "community", "shrine"],
                ),
                (
                    "Омакасе и доверие",
                    "В omakase важна не только еда, но и готовность довериться мастеру.",
                    [
                        "Гость не контролирует каждую деталь.",
                        "Повар ведет тебя по сценарию вкуса.",
                        "Это часть ремесленной культуры.",
                    ],
                    ["omakase", "craft", "trust"],
                ),
                (
                    "Визитки и деловой код",
                    "Meishi задает тон деловому контакту еще до разговора.",
                    [
                        "Визитку подают двумя руками.",
                        "Сразу прятать ее в карман невежливо.",
                        "Жест показывает серьезность общения.",
                    ],
                    ["meishi", "business", "respect"],
                ),
                (
                    "Неформальное после работы",
                    "Nomikai долго оставалось продолжением офисной культуры.",
                    [
                        "После работы иерархия немного смягчается.",
                        "Не все любят этот формат одинаково.",
                        "Культура меняется, но след остается.",
                    ],
                    ["nomikai", "office", "hierarchy"],
                ),
                (
                    "Контекст аниме",
                    "Многие аниме-сцены читаются глубже, если знать бытовой фон и социальные ритуалы.",
                    [
                        "Школьный фестиваль не выдуман из воздуха.",
                        "Язык старших и младших реально важен.",
                        "Даже еда в кадре часто несет сезонный смысл.",
                    ],
                    ["anime", "context", "school"],
                ),
            ],
            "history": [
                (
                    "Эдо как основа современного Токио",
                    "Городская культура эпохи Эдо до сих пор чувствуется в ритме столицы.",
                    [
                        "Росли кварталы ремесла и развлечений.",
                        "Плотность города стала нормой.",
                        "Коммерция меняла быт снизу.",
                    ],
                    ["Edo", "Tokyo", "city"],
                ),
                (
                    "Мэйдзи без пафоса",
                    "Реставрация Мэйдзи была резкой и болезненной модернизацией.",
                    [
                        "Менялись армия и школа.",
                        "Западные модели перенимали выборочно.",
                        "Общество платило цену за ускорение.",
                    ],
                    ["Meiji", "modernization", "state"],
                ),
                (
                    "Самурайский код после самураев",
                    "После исчезновения сословия самурайский язык чести не исчез из культуры.",
                    [
                        "Он перешел в школу и армию.",
                        "Дисциплина стала новой оболочкой старого кода.",
                        "Отголоски видны даже в корпоративной этике.",
                    ],
                    ["samurai", "ethics", "discipline"],
                ),
                (
                    "Сэнгоку и жажда порядка",
                    "Опыт эпохи войн сделал стабильность политической ценностью.",
                    [
                        "Союзы были хрупкими.",
                        "Военная мобильность стала повседневностью.",
                        "Потом страна надолго потянулась к централизации.",
                    ],
                    ["Sengoku", "war", "order"],
                ),
                (
                    "Токио после 1923 года",
                    "Землетрясение Кантo перестроило не только улицы, но и представление о городе.",
                    [
                        "Изменились планы застройки.",
                        "Катастрофа повлияла на память города.",
                        "Токио стал более инженерным.",
                    ],
                    ["Kanto", "Tokyo", "urbanism"],
                ),
                (
                    "Экономическое чудо после войны",
                    "Послевоенный рост опирался на дисциплину, экспорт и государственную стратегию.",
                    [
                        "Промышленность стала национальным проектом.",
                        "Экспорт задавал темп развития.",
                        "У роста была и социальная цена.",
                    ],
                    ["postwar", "growth", "industry"],
                ),
                (
                    "Император после 1945 года",
                    "Роль императора изменилась вместе с политической архитектурой страны.",
                    [
                        "Символическая функция стала важнее власти.",
                        "Изменился публичный язык вокруг трона.",
                        "Это влияет на современный церемониал.",
                    ],
                    ["emperor", "symbol", "constitution"],
                ),
                (
                    "Память о войне",
                    "Современная Япония спорит о войне не только в политике, но и в культуре памяти.",
                    [
                        "Учебники и кино говорят об этом по-разному.",
                        "Память у поколений неодинакова.",
                        "Тема остается живой.",
                    ],
                    ["memory", "war", "media"],
                ),
                (
                    "Хоккайдо и периферия",
                    "История страны читается иначе, если смотреть не только на Токио и Киото.",
                    [
                        "Север показывает другой угол на государство.",
                        "История айнов ломает простой нарратив.",
                        "Периферия помогает увидеть центр.",
                    ],
                    ["Hokkaido", "Ainu", "frontier"],
                ),
                (
                    "История в городском маршруте",
                    "В Японии прошлое часто живет не в памятнике, а в повседневном маршруте.",
                    [
                        "Станция, храм и мост хранят слой истории.",
                        "Город сам работает как учебник.",
                        "Это важно для живого погружения.",
                    ],
                    ["city", "memory", "place"],
                ),
            ],
        }
        previous_topics = {item.casefold() for item in payload.get("previous_topics") or []}
        if excluded_topics:
            previous_topics.update(topic.casefold() for topic in excluded_topics)
        seen_example_signatures = set(excluded_example_signatures or set())
        selected: list[GeneratedCardDraftDTO] = []
        for topic, explanation, examples, key_terms in library.get(
            payload["track"], []
        ):
            normalized_topic = topic.casefold()
            if normalized_topic in previous_topics:
                continue
            example_signature = HuggingFaceLLMClient._example_signature(examples)
            if example_signature and example_signature in seen_example_signatures:
                continue
            selected.append(
                GeneratedCardDraftDTO(
                    topic=topic,
                    explanation=HuggingFaceLLMClient._expand_fallback_note(
                        track=payload["track"],
                        topic=topic,
                        base_text=explanation,
                        interests=interests,
                        goal=str(payload.get("goal") or "погружение"),
                        language_level=str(payload.get("language_level") or "без уровня"),
                        study_timeline=str(payload.get("study_timeline") or "flexible"),
                        skill_summary=str(payload.get("diagnostic_summary") or ""),
                    ),
                    examples=examples,
                    key_terms=HuggingFaceLLMClient._normalize_key_terms(
                        key_terms,
                        track=str(payload["track"]),
                    ),
                )
            )
            previous_topics.add(normalized_topic)
            if example_signature:
                seen_example_signatures.add(example_signature)
            if len(selected) == payload["batch_size"]:
                break
        if len(selected) < payload["batch_size"]:
            dynamic_cards = HuggingFaceLLMClient._build_dynamic_fallback_cards(
                payload=payload,
                interests=interests,
                excluded_topics=set(previous_topics),
                excluded_example_signatures=set(seen_example_signatures),
            )
            for draft in dynamic_cards:
                if len(selected) == payload["batch_size"]:
                    break
                normalized_topic = draft.topic.casefold()
                if normalized_topic in previous_topics:
                    continue
                example_signature = HuggingFaceLLMClient._example_signature(
                    draft.examples
                )
                if example_signature and example_signature in seen_example_signatures:
                    continue
                previous_topics.add(normalized_topic)
                if example_signature:
                    seen_example_signatures.add(example_signature)
                selected.append(draft)
        return selected

    @staticmethod
    def _is_placeholder_topic(topic: str) -> bool:
        return topic.strip().casefold().startswith("резервная тема")

    @staticmethod
    def _build_dynamic_fallback_cards(
        *,
        payload: dict,
        interests: str,
        excluded_topics: set[str],
        excluded_example_signatures: set[tuple[str, ...]],
    ) -> list[GeneratedCardDraftDTO]:
        track = str(payload["track"])
        goal = str(payload.get("goal") or "погружение")
        language_level = str(payload.get("language_level") or "без уровня")
        candidates: list[GeneratedCardDraftDTO] = []
        seen_example_signatures = set(excluded_example_signatures)

        if track == "language":
            contexts = [
                (
                    "В кафе",
                    "Бытовой диалог в кафе строится на мягких просьбах, коротких уточнениях и понятной последовательности реплик.",
                    [
                        "メニューをお願いします。 | menyuu o onegaishimasu. | Меню, пожалуйста.",
                        "おすすめは何ですか。 | osusume wa nan desu ka. | Что вы посоветуете?",
                        "会計をお願いします。 | okaikei o onegaishimasu. | Счет, пожалуйста.",
                    ],
                    ["кафе", "注文", "会話"],
                ),
                (
                    "На станции",
                    "Язык станции держится на направлении, времени и переспросе, когда нужно быстро понять маршрут.",
                    [
                        "この電車は上野に行きますか。 | kono densha wa ueno ni ikimasu ka. | Этот поезд идет в Уэно?",
                        "何番線ですか。 | nanbansen desu ka. | Это какая платформа?",
                        "乗り換えはどこですか。 | norikae wa doko desu ka. | Где пересадка?",
                    ],
                    ["駅", "移動", "質問"],
                ),
                (
                    "В магазине",
                    "Покупка в магазине требует коротких формулировок без лишней сложности: показать, уточнить, оплатить.",
                    [
                        "これをください。 | kore o kudasai. | Мне вот это, пожалуйста.",
                        "試着できますか。 | shichaku dekimasu ka. | Можно примерить?",
                        "現金だけですか。 | genkin dake desu ka. | Только наличные?",
                    ],
                    ["買い物", "店", "質問"],
                ),
                (
                    "В университете",
                    "Учебная среда требует вежливого переспроса и умения быстро фиксировать, что именно непонятно.",
                    [
                        "この課題はいつまでですか。 | kono kadai wa itsu made desu ka. | До какого срока это задание?",
                        "もう一度説明してもらえますか。 | mou ichido setsumei shite moraemasu ka. | Можете объяснить еще раз?",
                        "ここをメモしてもいいですか。 | koko o memo shite mo ii desu ka. | Можно я это запишу?",
                    ],
                    ["大学", "勉強", "確認"],
                ),
                (
                    "В офисе",
                    "Рабочая коммуникация строится на подтверждении, аккуратной передаче статуса и уважении к времени собеседника.",
                    [
                        "確認して共有します。 | kakunin shite kyouyuu shimasu. | Проверю и сообщу.",
                        "少し遅れます。 | sukoshi okuremasu. | Я немного задержусь.",
                        "先に送っておきます。 | saki ni okutte okimasu. | Я заранее отправлю.",
                    ],
                    ["仕事", "確認", "共有"],
                ),
                (
                    "При аренде жилья",
                    "Язык жилья полезен для вопросов о договоре, счетах и бытовых правилах, которые редко объясняют простыми словами.",
                    [
                        "家賃には何が含まれますか。 | yachin ni wa nani ga fukumaremasu ka. | Что входит в аренду?",
                        "ゴミはいつ出しますか。 | gomi wa itsu dashimasu ka. | Когда выносят мусор?",
                        "更新料はありますか。 | koushinryou wa arimasu ka. | Есть ли плата за продление?",
                    ],
                    ["住まい", "契約", "生活"],
                ),
                (
                    "В клинике",
                    "Даже базовый визит к врачу требует точного словаря ощущений и спокойного переспроса.",
                    [
                        "昨日から熱があります。 | kinou kara netsu ga arimasu. | Со вчерашнего дня у меня температура.",
                        "どこで待てばいいですか。 | doko de mateba ii desu ka. | Где мне подождать?",
                        "薬はいつ飲みますか。 | kusuri wa itsu nomimasu ka. | Когда принимать лекарство?",
                    ],
                    ["病院", "説明", "体調"],
                ),
                (
                    "На улице",
                    "Уличный диалог обычно короткий: направление, ориентир и проверка, что ты понял правильно.",
                    [
                        "この道で合っていますか。 | kono michi de atteimasu ka. | Я правильно иду по этой дороге?",
                        "歩いて何分ですか。 | aruite nanpun desu ka. | Сколько минут пешком?",
                        "近くにコンビニはありますか。 | chikaku ni konbini wa arimasu ka. | Рядом есть конбини?",
                    ],
                    ["道", "案内", "街"],
                ),
            ]
            angles = [
                ("мягкие просьбы", "Важно выбрать форму, которая звучит вежливо, но не излишне тяжело для реальной сцены."),
                ("короткие уточнения", "Такие реплики помогают быстро сузить ситуацию и не потеряться в деталях."),
                ("переспрос без неловкости", "Переспрос в японском часто подается мягко, чтобы не ломать ритм разговора."),
                ("естественные реакции", "Живой диалог держится не только на вопросах, но и на коротких реакциях, которые поддерживают контакт."),
                ("вежливые отказы", "Отказ обычно смягчают так, чтобы сохранить дистанцию и не звучать резко."),
                ("самопрезентация по делу", "Короткое представление должно сразу объяснять, кто ты и зачем находишься в этой ситуации."),
            ]
        elif track == "culture":
            contexts = [
                (
                    "В транспорте",
                    "Общественный транспорт в Японии работает лучше, когда каждый человек поддерживает общий ритм пространства.",
                    [
                        "Громкий разговор сразу выбивается из нормы.",
                        "Телефон стараются убрать с общего звукового поля.",
                        "Тишина ощущается как форма уважения.",
                    ],
                    ["транспорт", "норма", "пространство"],
                ),
                (
                    "В магазине",
                    "Магазин в Японии часто показывает культуру точного сервиса: ясность действий важнее эффектности.",
                    [
                        "Покупателю заранее подсказывают сценарий действия.",
                        "Упаковка считается частью отношения к вещи.",
                        "Даже короткая покупка строится как аккуратный ритуал.",
                    ],
                    ["магазин", "сервис", "ритуал"],
                ),
                (
                    "Дома и у входа",
                    "Домашнее пространство разделено на зоны, и эта граница чувствуется еще до начала разговора.",
                    [
                        "Смена обуви задает тон входа.",
                        "Genkan работает как граница улицы и дома.",
                        "Даже мелкий жест на входе показывает уважение к месту.",
                    ],
                    ["дом", "genkan", "граница"],
                ),
                (
                    "В офисе",
                    "Офисная культура держится на предсказуемости, роли и способности не создавать лишнего трения для других.",
                    [
                        "Иерархия читается по форме обращения.",
                        "Согласование часто важнее резкой инициативы.",
                        "Тон письма и встречи обычно выравнивают заранее.",
                    ],
                    ["офис", "иерархия", "коммуникация"],
                ),
                (
                    "В университете",
                    "Учебная среда показывает, как сочетаются формальность, групповая работа и личная ответственность.",
                    [
                        "Семинар может быть неформальным по тону, но строгим по ожиданиям.",
                        "Групповая динамика влияет на поведение не меньше расписания.",
                        "Даже клубная жизнь продолжает социальное обучение.",
                    ],
                    ["университет", "группа", "норма"],
                ),
                (
                    "На фестивале",
                    "Фестиваль держится не только на зрелище, но и на локальной памяти, соседстве и распределении ролей.",
                    [
                        "Праздник связывает район в общий ритм.",
                        "Подготовка нередко важнее самой витрины события.",
                        "Локальная идентичность проявляется через маршрут и участие.",
                    ],
                    ["matsuri", "район", "память"],
                ),
                (
                    "В районе и у соседей",
                    "Соседство в Японии часто построено на тихой предсказуемости, а не на активной демонстрации дружелюбия.",
                    [
                        "Люди уважают личную дистанцию, не делая из этого холодность.",
                        "Правила мусора и шума быстро показывают, как устроено сообщество.",
                        "Доверие строится через повторяющуюся аккуратность.",
                    ],
                    ["район", "соседи", "повседневность"],
                ),
                (
                    "В ресторане",
                    "Ресторанная среда показывает японское отношение к роли мастера, ритму подачи и вниманию к деталям.",
                    [
                        "У гостя и персонала есть понятный сценарий взаимодействия.",
                        "Даже паузы между блюдами считываются как часть опыта.",
                        "В omakase доверие становится частью сервиса.",
                    ],
                    ["еда", "сервис", "ритм"],
                ),
            ]
            angles = [
                ("как считывается уважение", "Главное здесь не декларация ценностей, а мелкие действия, которые уменьшают трение для других."),
                ("почему норму редко объясняют вслух", "Многие культурные правила работают именно потому, что считываются из контекста, а не проговариваются отдельно."),
                ("что считается удобством для других", "Удобство в японской среде часто понимают как умение не создавать лишнюю нагрузку для общего пространства."),
                ("как маленькие жесты создают доверие", "Репутация спокойного и надежного человека собирается из повторяющихся мелких действий."),
                ("что происходит, когда ритм нарушают", "Нарушение нормы чаще всего не вызывает открытую конфронтацию, но резко меняет атмосферу взаимодействия."),
            ]
        else:
            contexts = [
                (
                    "Эдо",
                    "Эдо важно читать как модель плотного города, где ремесло, торговля и повседневность быстро формировали современный ритм жизни.",
                    [
                        "Плотность городской жизни стала нормой задолго до современного Токио.",
                        "Коммерция влияла на быт снизу, а не только через указ сверху.",
                        "Городская культура формировала вкус, язык и поведение.",
                    ],
                    ["Эдо", "город", "повседневность"],
                ),
                (
                    "Реформы Мэйдзи",
                    "Мэйдзи стоит смотреть как на ускоренную перестройку институтов, а не только как на красивый символ модернизации.",
                    [
                        "Армия, школа и бюрократия менялись одновременно.",
                        "Заимствование западных моделей было выборочным, а не слепым.",
                        "Цена ускорения распределялась по всему обществу.",
                    ],
                    ["Мэйдзи", "модернизация", "государство"],
                ),
                (
                    "Сэнгоку",
                    "Опыт эпохи войн сделал порядок и централизацию особенно ценными в следующих периодах истории.",
                    [
                        "Политические союзы были короткими и нестабильными.",
                        "Военная логика проникала в повседневность.",
                        "Потребность в устойчивом центре выросла из опыта хаоса.",
                    ],
                    ["Сэнгоку", "война", "порядок"],
                ),
                (
                    "Послевоенный рост",
                    "После 1945 года Япония перестраивала себя через промышленность, экспорт и институциональную дисциплину.",
                    [
                        "Экономический рост стал национальным проектом.",
                        "Промышленная стратегия влияла на городской и семейный быт.",
                        "Успех не отменял социальных издержек.",
                    ],
                    ["послевоенный период", "экономика", "индустрия"],
                ),
                (
                    "Токио после катастроф",
                    "Землетрясения и пожары меняли не только архитектуру города, но и представление о безопасности и управлении пространством.",
                    [
                        "После катастроф город пересобирали инженерно и административно.",
                        "Память о бедствии влияла на планирование улиц.",
                        "Урбанистика и страх катастроф долго шли рядом.",
                    ],
                    ["Токио", "катастрофы", "урбанизм"],
                ),
                (
                    "Хоккайдо и айны",
                    "Север Японии показывает, что национальная история страны гораздо сложнее столичного нарратива.",
                    [
                        "История айнов ломает слишком ровный рассказ о единой нации.",
                        "Периферия помогает увидеть государственное расширение иначе.",
                        "Региональная история меняет угол взгляда на центр.",
                    ],
                    ["Хоккайдо", "айны", "периферия"],
                ),
                (
                    "Пузырь 1980-х",
                    "Экономический пузырь конца XX века важен не только цифрами, но и тем, как он изменил ожидания общества.",
                    [
                        "Оптимизм роста проникал в городской стиль жизни.",
                        "Крах пузыря повлиял на карьерные и семейные стратегии.",
                        "Память об этом периоде до сих пор чувствуется в осторожности решений.",
                    ],
                    ["пузырь", "экономика", "общество"],
                ),
                (
                    "Память о войне",
                    "Тема войны в Японии живет одновременно в политике, школе, городе и массовой культуре.",
                    [
                        "Учебники, кино и мемориалы могут говорить об одном периоде по-разному.",
                        "Память меняется от поколения к поколению.",
                        "История продолжает влиять на внешний и внутренний язык страны.",
                    ],
                    ["память", "война", "культура"],
                ),
            ]
            angles = [
                ("через повседневность", "Такой ракурс помогает увидеть, как большие процессы опускаются в рутину обычного человека."),
                ("через город", "Городская ткань показывает след истории нагляднее, чем абстрактный список дат."),
                ("через институты", "Институты сохраняют последствия исторических решений дольше, чем политические лозунги."),
                ("через культуру памяти", "Важно смотреть, как тема переживается, вспоминается и спорится в разных поколениях."),
                ("через работу и образование", "Школа и рынок труда часто лучше всего показывают, как история превращается в норму."),
            ]

        for context_title, context_text, examples, base_terms in contexts:
            for angle_title, angle_text in angles:
                topic = f"{context_title}: {angle_title}"
                normalized_topic = topic.casefold()
                if normalized_topic in excluded_topics:
                    continue
                generated_examples = HuggingFaceLLMClient._build_dynamic_examples(
                    track=track,
                    context_title=context_title,
                    angle_title=angle_title,
                    base_terms=base_terms,
                )
                example_signature = HuggingFaceLLMClient._example_signature(
                    generated_examples
                )
                if example_signature and example_signature in seen_example_signatures:
                    continue
                explanation = HuggingFaceLLMClient._expand_fallback_note(
                    track=track,
                    topic=topic,
                    base_text=f"{context_text} {angle_text}",
                    interests=interests,
                    goal=goal,
                    language_level=language_level,
                    study_timeline=str(payload.get("study_timeline") or "flexible"),
                    skill_summary=str(payload.get("diagnostic_summary") or ""),
                )
                key_terms = HuggingFaceLLMClient._normalize_key_terms(
                    list(dict.fromkeys([*base_terms, angle_title, track]))[:5],
                    track=track,
                )
                candidates.append(
                    GeneratedCardDraftDTO(
                        topic=topic,
                        explanation=explanation,
                        examples=generated_examples,
                        key_terms=key_terms,
                    )
                )
                if example_signature:
                    seen_example_signatures.add(example_signature)
        return candidates

    @staticmethod
    def _expand_fallback_note(
        track: str,
        topic: str,
        base_text: str,
        interests: str,
        goal: str,
        language_level: str,
        study_timeline: str,
        skill_summary: str,
    ) -> str:
        contextual_blocks = {
            "language": (
                "Здесь важнее всего сцена: кто говорит, зачем говорит и насколько мягко должна звучать реплика. "
                "После чтения полезно проговорить пример вслух и заменить один элемент на свой."
            ),
            "culture": (
                "Эту тему лучше держать как правило повседневной среды. Полезно сразу привязать конспект к одной конкретной сцене: магазин, транспорт, дом, офис или улица."
            ),
            "history": (
                "Историческую тему полезно читать как цепочку причин и последствий. Важно понять, что было до события, что изменилось после него и почему это заметно в современной Японии."
            ),
        }
        timeline_blocks = {
            "three_months": "Держи фокус на одной практической задаче и быстро привязывай тему к реальной ситуации.",
            "six_months": "Сразу связывай правило с действием: как сказать, как понять, где применить.",
            "one_year": "После базового смысла полезно заметить, где тема чаще всего ломается у новичка и как этого избежать.",
            "two_years": "Полезно не только выучить форму, но и увидеть, как тема связана с соседними конструкциями и контекстом.",
            "flexible": "Если тема пока держится слабо, полезно прочитать пример вслух и проверить, что именно в ней было непонятно.",
        }
        return (
            f"{base_text} "
            f"{contextual_blocks.get(track, contextual_blocks['culture'])} "
            f"{timeline_blocks.get(study_timeline, timeline_blocks['flexible'])}"
        ).strip()

    @staticmethod
    def _fallback_speech_practice(payload: dict) -> SpeechPracticeDTO:
        seed_words = [
            HuggingFaceLLMClient._parse_seed_word(word)
            for word in payload.get("words") or []
        ]
        if not seed_words:
            seed_words = [HuggingFaceLLMClient._parse_seed_word("日本語 | nihongo | японский язык")]

        sentence_templates = [
            ("{surface}を使います。", "{reading} o tsukaimasu.", "Я использую {translation}."),
            ("毎日{surface}を練習します。", "mainichi {reading} o renshuu shimasu.", "Я каждый день тренирую {translation}."),
            ("{surface}が好きです。", "{reading} ga suki desu.", "Мне нравится {translation}."),
            ("今日は{surface}を確認します。", "kyou wa {reading} o kakunin shimasu.", "Сегодня я повторяю {translation}."),
            ("あとで{surface}を読みます。", "ato de {reading} o yomimasu.", "Позже я прочитаю {translation}."),
            ("先生と{surface}を話します。", "sensei to {reading} o hanashimasu.", "Я обсуждаю {translation} с преподавателем."),
            ("友だちに{surface}を見せます。", "tomodachi ni {reading} o misemasu.", "Я показываю {translation} другу."),
            ("まず{surface}を覚えます。", "mazu {reading} o oboemasu.", "Сначала я запоминаю {translation}."),
            ("明日{surface}をもう一度使います。", "ashita {reading} o mou ichido tsukaimasu.", "Завтра я еще раз использую {translation}."),
            ("この場面では{surface}が大事です。", "kono bamen de wa {reading} ga daiji desu.", "В этой сцене важно {translation}."),
        ]
        sentences: list[SpeechLineDTO] = []
        for index, template in enumerate(sentence_templates):
            word = seed_words[index % len(seed_words)]
            sentences.append(
                SpeechLineDTO(
                    japanese=template[0].format(surface=word["surface"]),
                    romaji=template[1].format(reading=word["reading"]),
                    translation=template[2].format(translation=word["translation"]),
                )
            )

        dialogue_templates = [
            (
                "Попросить и подтвердить",
                "Короткий бытовой запрос без сложной грамматики.",
                [
                    ("A", "{surface}はありますか。", "{reading} wa arimasu ka.", "У вас есть {translation}?"),
                    ("B", "はい、{surface}があります。", "hai, {reading} ga arimasu.", "Да, {translation} есть."),
                    ("A", "じゃあ、{surface}をお願いします。", "jaa, {reading} o onegaishimasu.", "Тогда {translation}, пожалуйста."),
                ],
            ),
            (
                "Уточнить понимание",
                "Проверка, что слово услышано и понято правильно.",
                [
                    ("A", "{surface}はどういう意味ですか。", "{reading} wa dou iu imi desu ka.", "Что значит {translation}?"),
                    ("B", "{surface}は大切な言葉です。", "{reading} wa taisetsu na kotoba desu.", "{translation} это важное слово."),
                    ("A", "わかりました。{surface}を使ってみます。", "wakarimashita. {reading} o tsukatte mimasu.", "Понял. Попробую использовать {translation}."),
                ],
            ),
            (
                "Короткая самопрезентация",
                "Вставить слово в очень простой разговор о себе.",
                [
                    ("A", "今、{surface}を勉強しています。", "ima, {reading} o benkyou shiteimasu.", "Сейчас я изучаю {translation}."),
                    ("B", "いいですね。どこで{surface}を使いますか。", "ii desu ne. doko de {reading} o tsukaimasu ka.", "Здорово. Где ты используешь {translation}?"),
                    ("A", "授業と会話で使います。", "jugyou to kaiwa de tsukaimasu.", "Использую на занятиях и в разговоре."),
                ],
            ),
            (
                "Переспрос без паники",
                "Формула, чтобы спокойно попросить повторить слово.",
                [
                    ("A", "すみません、{surface}をもう一度言ってください。", "sumimasen, {reading} o mou ichido itte kudasai.", "Извините, повторите {translation} еще раз."),
                    ("B", "はい、{surface}です。", "hai, {reading} desu.", "Да, это {translation}."),
                    ("A", "ありがとうございます。今なら言えます。", "arigatou gozaimasu. ima nara iemasu.", "Спасибо. Теперь я могу это произнести."),
                ],
            ),
            (
                "Мини-диалог для закрепления",
                "Три реплики, которые удобно проговаривать циклом.",
                [
                    ("A", "{surface}を知っていますか。", "{reading} o shitteimasu ka.", "Ты знаешь {translation}?"),
                    ("B", "はい、少し知っています。", "hai, sukoshi shitteimasu.", "Да, немного знаю."),
                    ("A", "じゃあ、次は{surface}で文を作りましょう。", "jaa, tsugi wa {reading} de bun o tsukurimashou.", "Тогда давай составим предложение с {translation}."),
                ],
            ),
        ]
        dialogues: list[SpeechDialogueDTO] = []
        for index, (title, scenario, turns_template) in enumerate(dialogue_templates):
            word = seed_words[index % len(seed_words)]
            turns = [
                SpeechDialogueTurnDTO(
                    speaker=speaker,
                    japanese=japanese.format(surface=word["surface"]),
                    romaji=romaji.format(reading=word["reading"]),
                    translation=translation.format(translation=word["translation"]),
                )
                for speaker, japanese, romaji, translation in turns_template
            ]
            dialogues.append(
                SpeechDialogueDTO(title=title, scenario=scenario, turns=turns)
            )

        return SpeechPracticeDTO(
            words=[word["surface"] for word in seed_words],
            sentences=sentences,
            dialogues=dialogues,
            coaching_tip=HuggingFaceLLMClient._speech_coaching_tip(payload),
            difficulty_label=HuggingFaceLLMClient._speech_difficulty_label(payload),
        )

    @staticmethod
    def _parse_seed_word(raw_word: str) -> dict[str, str]:
        normalized = raw_word.strip()
        if "|" in normalized:
            parts = [part.strip() for part in normalized.split("|")]
        elif " - " in normalized:
            parts = [part.strip() for part in normalized.split(" - ")]
        else:
            parts = [normalized]
        surface = parts[0] if parts else normalized
        reading = parts[1] if len(parts) >= 2 else surface
        translation = parts[2] if len(parts) >= 3 else surface
        return {
            "surface": surface,
            "reading": reading,
            "translation": translation,
        }

    @staticmethod
    def _normalize_card_examples(raw_examples: list[dict | str]) -> list[str]:
        normalized_examples: list[str] = []
        seen_signatures: set[str] = set()
        for example in raw_examples:
            if isinstance(example, dict):
                japanese = str(example.get("japanese") or "").strip()
                romaji = str(example.get("romaji") or "").strip()
                translation = str(
                    example.get("translation") or example.get("russian") or ""
                ).strip()
                pieces = [piece for piece in (japanese, romaji, translation) if piece]
                normalized = " | ".join(pieces)
            else:
                normalized = str(example).strip()
            if not normalized:
                continue
            signature = HuggingFaceLLMClient._normalize_example_signature(normalized)
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            normalized_examples.append(normalized)
        return normalized_examples[:3]

    @staticmethod
    def _normalize_key_terms(raw_terms: list[dict | str], track: str) -> list[str]:
        translation_map = {
            "挨拶": "приветствие",
            "丁寧": "вежливая форма",
            "会話": "разговор",
            "自己紹介": "самопрезентация",
            "名前": "имя",
            "よろしく": "вежливая завершающая формула",
            "注文": "заказ",
            "お願い": "просьба",
            "おすすめ": "рекомендация",
            "会計": "счет",
            "メニュー": "меню",
            "水": "вода",
            "電車": "поезд",
            "駅": "станция",
            "移動": "перемещение",
            "質問": "вопрос",
            "買い物": "покупки",
            "店": "магазин",
            "大学": "университет",
            "勉強": "учеба",
            "確認": "уточнение",
            "仕事": "работа",
            "共有": "обмен информацией",
            "住まい": "жилье",
            "契約": "договор",
            "生活": "быт",
            "歴史": "история",
            "文化": "культура",
            "時代": "эпоха",
            "変化": "изменение",
            "伝統": "традиция",
            "習慣": "привычка",
            "礼儀": "этикет",
            "空気": "атмосфера общения",
            "city": "город",
            "memory": "память",
            "place": "место",
            "language": "язык",
            "history": "история",
            "culture": "культура",
            "work": "работа",
        }
        normalized_terms: list[str] = []
        seen: set[str] = set()
        for raw_term in raw_terms:
            cleaned = " ".join(str(raw_term or "").split()).strip(" ,.;")
            if not cleaned:
                continue
            label = cleaned
            translation = None

            for separator in ("|", " - ", " — ", " – ", ":", " -> "):
                if separator not in cleaned:
                    continue
                parts = [
                    part.strip(" ,.;")
                    for part in cleaned.split(separator)
                    if part.strip(" ,.;")
                ]
                if len(parts) >= 2:
                    label = parts[0]
                    translation = parts[-1]
                    break

            if translation is None:
                translation = translation_map.get(label) or translation_map.get(
                    label.casefold()
                )

            if translation and translation != label:
                prepared = f"{label} | {translation}"
            else:
                prepared = label

            signature = HuggingFaceLLMClient._normalize_example_signature(prepared)
            if signature in seen:
                continue
            seen.add(signature)
            normalized_terms.append(prepared)
        if track != "language":
            return normalized_terms[:5]
        return normalized_terms[:5]

    @staticmethod
    def _key_term_focus_text(term: str) -> str:
        cleaned = " ".join(str(term or "").split()).strip(" ,.;")
        if "|" in cleaned:
            parts = [part.strip() for part in cleaned.split("|") if part.strip()]
            if len(parts) >= 2:
                return parts[-1]
        if " - " in cleaned:
            parts = [part.strip() for part in cleaned.split(" - ") if part.strip()]
            if len(parts) >= 2:
                return parts[-1]
        return cleaned

    @staticmethod
    def _normalize_example_signature(example: str) -> str:
        compact = " ".join(str(example).split()).casefold()
        return compact.replace("ё", "е")

    @staticmethod
    def _example_signature(examples: list[str]) -> tuple[str, ...]:
        signatures = [
            HuggingFaceLLMClient._normalize_example_signature(example)
            for example in examples
            if str(example).strip()
        ]
        return tuple(dict.fromkeys(signatures))

    @staticmethod
    def _build_dynamic_examples(
        *,
        track: str,
        context_title: str,
        angle_title: str,
        base_terms: list[str],
    ) -> list[str]:
        if track == "language":
            return HuggingFaceLLMClient._build_language_dynamic_examples(
                context_title=context_title,
                angle_title=angle_title,
            )

        focus_term = (
            HuggingFaceLLMClient._key_term_focus_text(base_terms[0])
            if base_terms
            else context_title
        )
        return [
            f"{context_title}: здесь {angle_title} читается через конкретное поведение, а не через абстрактное правило.",
            f"{focus_term} помогает быстро заметить, как тема проявляется в живой ситуации и почему это важно для контекста.",
            f"Если перенести тему в реальную сцену, становится видно, как {angle_title} меняет восприятие всей ситуации.",
        ]

    @staticmethod
    def _build_language_dynamic_examples(
        *,
        context_title: str,
        angle_title: str,
    ) -> list[str]:
        scene = HuggingFaceLLMClient._language_scene_parts(context_title)
        angle = angle_title.casefold()

        if "мягкие просьбы" in angle:
            return [
                f"{scene['request_jp']}をお願いします。 | {scene['request_ro']} o onegaishimasu. | {scene['request_ru']}, пожалуйста.",
                f"{scene['option_jp']}を見せてもらえますか。 | {scene['option_ro']} o misete moraemasu ka. | Можно посмотреть {scene['option_ru']}?",
                "少しゆっくりお願いします。 | sukoshi yukkuri onegaishimasu. | Пожалуйста, чуть медленнее.",
            ]
        if "короткие уточнения" in angle:
            return [
                f"{scene['option_jp']}はどれですか。 | {scene['option_ro']} wa dore desu ka. | Какой вариант здесь нужен?",
                "ここで合っていますか。 | koko de atteimasu ka. | Я правильно понял место или вариант?",
                f"いつ{scene['action_jp']}しますか。 | itsu {scene['action_ro']} shimasu ka. | Когда происходит {scene['action_ru']}?",
            ]
        if "переспрос" in angle:
            return [
                f"すみません、{scene['option_jp']}をもう一度言ってください。 | sumimasen, {scene['option_ro']} o mou ichido itte kudasai. | Извините, повторите это еще раз.",
                "今の言い方で合っていますか。 | ima no iikata de atteimasu ka. | Я правильно понял, как это было сказано?",
                f"{scene['place_jp']}はどこでしたか。 | {scene['place_ro']} wa doko deshita ka. | Напомните, где здесь {scene['place_ru']}?",
            ]
        if "естественные реакции" in angle:
            return [
                f"わかりました。{scene['request_jp']}にします。 | wakarimashita. {scene['request_ro']} ni shimasu. | Понял, тогда беру {scene['request_ru']}.",
                "ありがとうございます。それで大丈夫です。 | arigatou gozaimasu. sore de daijoubu desu. | Спасибо, так подойдет.",
                "いいですね。では、そうします。 | ii desu ne. dewa, sou shimasu. | Хорошо, тогда так и сделаю.",
            ]
        if "вежливые отказы" in angle:
            return [
                f"今日は{scene['request_jp']}はやめておきます。 | kyou wa {scene['request_ro']} wa yamete okimasu. | Сегодня я пока откажусь от {scene['request_ru']}.",
                "今回は大丈夫です。ありがとうございます。 | konkai wa daijoubu desu. arigatou gozaimasu. | В этот раз не нужно, спасибо.",
                "また後でお願いします。 | mata ato de onegaishimasu. | Давайте чуть позже.",
            ]
        return [
            f"初めてなので、{scene['place_jp']}で少し緊張しています。 | hajimete na node, {scene['place_ro']} de sukoshi kinchou shiteimasu. | Я здесь впервые, поэтому немного волнуюсь.",
            f"{scene['place_jp']}では簡単な日本語で話します。 | {scene['place_ro']} de wa kantan na nihongo de hanashimasu. | В этой ситуации я говорю простым японским.",
            f"今日は{scene['action_jp']}のために来ました。 | kyou wa {scene['action_ro']} no tame ni kimashita. | Сегодня я пришел по поводу этого вопроса.",
        ]

    @staticmethod
    def _language_scene_parts(context_title: str) -> dict[str, str]:
        normalized = context_title.casefold()
        scenes = [
            (
                "кафе",
                {
                    "request_jp": "メニュー",
                    "request_ro": "menyuu",
                    "request_ru": "меню",
                    "option_jp": "おすすめ",
                    "option_ro": "osusume",
                    "option_ru": "рекомендация",
                    "action_jp": "注文",
                    "action_ro": "chuumon",
                    "action_ru": "заказ",
                    "place_jp": "カフェ",
                    "place_ro": "kafe",
                    "place_ru": "кафе",
                },
            ),
            (
                "стан",
                {
                    "request_jp": "路線図",
                    "request_ro": "rosenzu",
                    "request_ru": "схема линий",
                    "option_jp": "乗り場",
                    "option_ro": "noriba",
                    "option_ru": "нужная платформа",
                    "action_jp": "乗り換え",
                    "action_ro": "norikae",
                    "action_ru": "пересадка",
                    "place_jp": "駅",
                    "place_ro": "eki",
                    "place_ru": "станция",
                },
            ),
            (
                "магаз",
                {
                    "request_jp": "これ",
                    "request_ro": "kore",
                    "request_ru": "этот товар",
                    "option_jp": "別のサイズ",
                    "option_ro": "betsu no saizu",
                    "option_ru": "другой размер",
                    "action_jp": "支払い",
                    "action_ro": "shiharai",
                    "action_ru": "оплата",
                    "place_jp": "店内",
                    "place_ro": "tennai",
                    "place_ru": "магазин",
                },
            ),
            (
                "универс",
                {
                    "request_jp": "資料",
                    "request_ro": "shiryou",
                    "request_ru": "материалы",
                    "option_jp": "この課題",
                    "option_ro": "kono kadai",
                    "option_ru": "это задание",
                    "action_jp": "確認",
                    "action_ro": "kakunin",
                    "action_ru": "уточнение",
                    "place_jp": "教室",
                    "place_ro": "kyoushitsu",
                    "place_ru": "аудитория",
                },
            ),
            (
                "офис",
                {
                    "request_jp": "資料",
                    "request_ro": "shiryou",
                    "request_ru": "документ",
                    "option_jp": "進捗",
                    "option_ro": "shinchoku",
                    "option_ru": "статус задачи",
                    "action_jp": "共有",
                    "action_ro": "kyouyuu",
                    "action_ru": "обновление для команды",
                    "place_jp": "会議",
                    "place_ro": "kaigi",
                    "place_ru": "рабочая встреча",
                },
            ),
            (
                "жиль",
                {
                    "request_jp": "契約書",
                    "request_ro": "keiyakusho",
                    "request_ru": "договор",
                    "option_jp": "更新料",
                    "option_ro": "koushinryou",
                    "option_ru": "плата за продление",
                    "action_jp": "確認",
                    "action_ro": "kakunin",
                    "action_ru": "уточнение условий",
                    "place_jp": "不動産屋",
                    "place_ro": "fudousanya",
                    "place_ru": "агентство жилья",
                },
            ),
            (
                "клиник",
                {
                    "request_jp": "薬",
                    "request_ro": "kusuri",
                    "request_ru": "лекарство",
                    "option_jp": "症状",
                    "option_ro": "shoujou",
                    "option_ru": "симптом",
                    "action_jp": "説明",
                    "action_ro": "setsumei",
                    "action_ru": "объяснение состояния",
                    "place_jp": "受付",
                    "place_ro": "uketsuke",
                    "place_ru": "регистратура",
                },
            ),
            (
                "улиц",
                {
                    "request_jp": "地図",
                    "request_ro": "chizu",
                    "request_ru": "карта",
                    "option_jp": "近い道",
                    "option_ro": "chikai michi",
                    "option_ru": "ближайший путь",
                    "action_jp": "案内",
                    "action_ro": "annai",
                    "action_ru": "подсказка по маршруту",
                    "place_jp": "この道",
                    "place_ro": "kono michi",
                    "place_ru": "эта дорога",
                },
            ),
        ]
        for marker, scene in scenes:
            if marker in normalized:
                return scene
        return {
            "request_jp": "言い方",
            "request_ro": "iikata",
            "request_ru": "эту формулировку",
            "option_jp": "表現",
            "option_ro": "hyougen",
            "option_ru": "выражение",
            "action_jp": "会話",
            "action_ro": "kaiwa",
            "action_ru": "разговор",
            "place_jp": "場面",
            "place_ro": "bamen",
            "place_ru": "сцену",
        }

    @staticmethod
    def _goal_label(goal: str | None) -> str:
        labels = {
            "tourism": "туризм",
            "relocation": "переезд",
            "work": "работа",
            "university": "университет",
        }
        return labels.get(str(goal), "не указана")

    @staticmethod
    def _level_label(level: str | None) -> str:
        labels = {
            "zero": "стартовый",
            "basic": "базовый",
            "intermediate": "уверенный",
        }
        return labels.get(str(level), "не указан")

    @staticmethod
    def _timeline_label(timeline: str | None) -> str:
        labels = {
            "three_months": "3 месяца",
            "six_months": "6 месяцев",
            "one_year": "1 год",
            "two_years": "2 года и дольше",
            "flexible": "без жесткого дедлайна",
        }
        return labels.get(str(timeline), "гибкий темп")

    @staticmethod
    def _timeline_generation_instruction(timeline: str | None) -> str:
        instructions = {
            "three_months": (
                "Темп сжатый: давай только самые частые и прикладные объяснения, меньше обходной теории, "
                "быстрее переходи к сцене применения."
            ),
            "six_months": (
                "Темп интенсивный: объясняй по делу, держи материал плотным и сразу закрепляй его через практику."
            ),
            "one_year": (
                "Темп сбалансированный: объясняй подробно, но без затяжных отступлений, чтобы теория сразу работала в практике."
            ),
            "two_years": (
                "Темп глубокий: можно объяснять шире, показывать связи между темами и не спешить с убиранием опор без необходимости."
            ),
            "flexible": (
                "Темп гибкий: подробность объяснения подстраивай под сложность темы и слабые места пользователя."
            ),
        }
        return instructions.get(str(timeline), instructions["flexible"])

    @staticmethod
    def _timeline_advice_context(timeline: str | None) -> str:
        contexts = {
            "three_months": "Советы должны быть жестко приоритизированы: сначала то, что дает быстрый практический эффект.",
            "six_months": "Советы должны держать интенсивный, но реалистичный темп без лишних ответвлений.",
            "one_year": "Советы должны удерживать баланс между подробным разбором и нормальным темпом.",
            "two_years": "Советы могут включать больше контекста, чтения и постепенного усложнения.",
            "flexible": "Советы должны подстраиваться под реальные просадки, а не под искусственный дедлайн.",
        }
        return contexts.get(str(timeline), contexts["flexible"])

    @staticmethod
    def _explanation_length_instruction(payload: dict) -> str:
        timeline = str(payload.get("study_timeline") or "flexible")
        instructions = {
            "three_months": "Explanation делай плотным конспектом длиной около 130-170 слов.",
            "six_months": "Explanation делай плотным конспектом длиной около 150-190 слов.",
            "one_year": "Explanation делай плотным конспектом длиной около 170-220 слов.",
            "two_years": "Explanation делай подробным конспектом длиной около 190-240 слов.",
            "flexible": "Explanation делай подробным, но прикладным конспектом длиной около 180-230 слов.",
        }
        return instructions.get(timeline, instructions["flexible"])

    @staticmethod
    def _build_generation_context(payload: dict) -> str:
        level = HuggingFaceLLMClient._level_label(
            payload.get("diagnostic_level") or payload.get("language_level")
        )
        lines = [
            f"Адаптируй сложность под уровень: {level}.",
            HuggingFaceLLMClient._timeline_generation_instruction(
                payload.get("study_timeline")
            ),
        ]

        weak_points = ", ".join(payload.get("weak_points") or [])
        if weak_points:
            lines.append(f"Упрощай материал там, где обычно проседают: {weak_points}.")

        strengths = ", ".join(payload.get("strengths") or [])
        if strengths:
            lines.append(f"Можно быстрее опираться на: {strengths}.")

        return " ".join(lines)

    @staticmethod
    def _speech_difficulty_label(payload: dict) -> str:
        level = payload.get("diagnostic_level") or payload.get("language_level")
        labels = {
            "zero": "Простой режим",
            "basic": "Базовый режим",
            "intermediate": "Расширенный режим",
        }
        return labels.get(str(level), "Речевая практика")

    @staticmethod
    def _speech_coaching_tip(payload: dict) -> str:
        timeline = str(payload.get("study_timeline") or "flexible")
        weak_points = set(payload.get("weak_points") or [])
        if "Хирагана" in weak_points:
            return "Сначала прочитай строки по ромадзи, потом повтори без подсказки."
        if "Частицы" in weak_points:
            return "Проговаривай предложения с акцентом на частицы и меняй одно существительное."
        if "Базовый порядок предложения" in weak_points:
            return "Читай диалоги по ролям и отдельно отмечай тему, действие и объект."
        if timeline == "three_months":
            return "Говори короткими циклами: предложение, пауза, повтор без чтения."
        if timeline == "two_years":
            return "Проговаривай сначала медленно, потом еще раз без опоры на перевод и отмечай, где смысл собирается из контекста."
        return "Сначала прочитай предложения, потом проговори диалоги."

    @staticmethod
    def _fallback_advice(user: User, report: ProgressReportDTO) -> AIAdviceDTO:
        weakest_track = min(
            report.tracks,
            key=lambda item: item.completion_rate if item.generated_cards else 101,
        )
        weak_points = (
            ", ".join(user.skill_assessment.weak_points)
            if user.skill_assessment and user.skill_assessment.weak_points
            else "заметных слабых мест пока нет"
        )
        timeline_note = HuggingFaceLLMClient._timeline_advice_context(
            user.study_timeline.value if user.study_timeline else None
        )
        return AIAdviceDTO(
            headline="Следующий шаг",
            summary=(
                f"Сейчас лучше закончить текущую партию в разделе '{weakest_track.title}'. "
                f"Отдельно стоит следить за темами: {weak_points}. {timeline_note}"
            ),
            focus_points=[
                f"Закрой текущую партию в разделе '{weakest_track.title}'.",
                "После этого открой речевую практику и проговори слова из языкового блока.",
                "Перед новой партией отметь 2-3 места, которые остались непонятными.",
            ],
        )
