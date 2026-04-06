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
    _CARDS_CACHE_VERSION = "cards-v2"
    _SPEECH_CACHE_VERSION = "speech-v2"
    _ADVICE_CACHE_VERSION = "advice-v2"

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
        for item in parsed[: payload["batch_size"]]:
            topic = str(item.get("topic") or "Тема без названия").strip()
            normalized_topic = topic.casefold()
            if not topic or normalized_topic in seen_topics:
                continue
            if HuggingFaceLLMClient._is_placeholder_topic(topic):
                continue
            normalized_examples = []
            for example in item.get("examples") or []:
                if isinstance(example, dict):
                    japanese = str(example.get("japanese") or "").strip()
                    romaji = str(example.get("romaji") or "").strip()
                    translation = str(
                        example.get("translation") or example.get("russian") or ""
                    ).strip()
                    pieces = [piece for piece in (japanese, romaji, translation) if piece]
                    normalized_examples.append(" | ".join(pieces))
                    continue
                normalized_examples.append(str(example).strip())
            seen_topics.add(normalized_topic)
            normalized.append(
                GeneratedCardDraftDTO(
                    topic=topic,
                    explanation=str(item.get("explanation") or "").strip(),
                    examples=normalized_examples[:3],
                    key_terms=[
                        str(term).strip() for term in item.get("key_terms") or []
                    ][:5],
                )
            )
        if len(normalized) < payload["batch_size"]:
            fallback = HuggingFaceLLMClient._fallback_cards(payload, seen_topics)
            for draft in fallback:
                if len(normalized) == payload["batch_size"]:
                    break
                topic_key = draft.topic.casefold()
                if topic_key in seen_topics:
                    continue
                seen_topics.add(topic_key)
                normalized.append(draft)
        return normalized

    @staticmethod
    def _build_cards_prompt(payload: dict) -> str:
        interests = ", ".join(payload["interests"]) or "не указаны"
        previous = ", ".join(payload["previous_topics"]) or "нет"
        return (
            "Сгенерируй карточки-конспекты по Японии.\n"
            f"Трек: {payload['track']}\n"
            f"Цель: {payload['goal']}\n"
            f"Уровень: {payload['language_level']}\n"
            f"Интересы: {interests}\n"
            f"Номер партии: {payload['batch_number']}\n"
            f"Размер партии: {payload['batch_size']}\n"
            f"Избегай повторов тем: {previous}\n"
            f"{HuggingFaceLLMClient._build_skill_context(payload)}\n"
            "Верни JSON-массив, где у каждой карточки есть topic, explanation, examples, key_terms.\n"
            "Explanation делай плотным конспектом длиной около 160-220 слов.\n"
            "Examples возвращай массивом строк в формате: Japanese | Romaji | Русский перевод.\n"
            "Если трек не языковой, все равно давай примеры в удобном формате для быстрого чтения."
        )

    @staticmethod
    def _build_advice_prompt(user: User, report: ProgressReportDTO) -> str:
        return (
            f"Пользователь: {user.display_name}.\n"
            f"Цель: {user.learning_goal.value if user.learning_goal else 'не указана'}.\n"
            f"Уровень: {user.language_level.value if user.language_level else 'не указан'}.\n"
            f"Интересы: {', '.join(user.interests) or 'не указаны'}.\n"
            f"{HuggingFaceLLMClient._build_skill_context_from_user(user)}\n"
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
            f"Цель: {payload['goal']}\n"
            f"Самооценка уровня: {payload['language_level']}\n"
            f"Интересы: {interests}\n"
            f"Слова: {words}\n"
            f"{HuggingFaceLLMClient._build_skill_context(payload)}\n"
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
                f"Диагностический уровень: {payload['diagnostic_level']}"
                if payload.get("diagnostic_level")
                else None
            ),
            (
                f"Диагностическая сводка: {payload['diagnostic_summary']}"
                if payload.get("diagnostic_summary")
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
        selected: list[GeneratedCardDraftDTO] = []
        for topic, explanation, examples, key_terms in library.get(
            payload["track"], []
        ):
            normalized_topic = topic.casefold()
            if normalized_topic in previous_topics:
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
                        skill_summary=str(payload.get("diagnostic_summary") or ""),
                    ),
                    examples=examples,
                    key_terms=key_terms,
                )
            )
            previous_topics.add(normalized_topic)
            if len(selected) == payload["batch_size"]:
                break
        if len(selected) < payload["batch_size"]:
            dynamic_cards = HuggingFaceLLMClient._build_dynamic_fallback_cards(
                payload=payload,
                interests=interests,
                excluded_topics=set(previous_topics),
            )
            for draft in dynamic_cards:
                if len(selected) == payload["batch_size"]:
                    break
                normalized_topic = draft.topic.casefold()
                if normalized_topic in previous_topics:
                    continue
                previous_topics.add(normalized_topic)
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
    ) -> list[GeneratedCardDraftDTO]:
        track = str(payload["track"])
        goal = str(payload.get("goal") or "погружение")
        language_level = str(payload.get("language_level") or "без уровня")
        candidates: list[GeneratedCardDraftDTO] = []

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
                explanation = HuggingFaceLLMClient._expand_fallback_note(
                    track=track,
                    topic=topic,
                    base_text=f"{context_text} {angle_text}",
                    interests=interests,
                    goal=goal,
                    language_level=language_level,
                    skill_summary=str(payload.get("diagnostic_summary") or ""),
                )
                key_terms = list(dict.fromkeys([*base_terms, angle_title, track]))[:5]
                candidates.append(
                    GeneratedCardDraftDTO(
                        topic=topic,
                        explanation=explanation,
                        examples=examples,
                        key_terms=key_terms,
                    )
                )
        return candidates

    @staticmethod
    def _expand_fallback_note(
        track: str,
        topic: str,
        base_text: str,
        interests: str,
        goal: str,
        language_level: str,
        skill_summary: str,
    ) -> str:
        contextual_blocks = {
            "language": (
                "Смотри на тему не как на отдельную формулу, а как на часть живого разговора. "
                "В японском важно не только само слово, но и дистанция между людьми, мягкость реплики, "
                "уровень вежливости и место, где эта фраза звучит естественно. "
                "Если ты учишь язык под цель "
                f"'{goal}', то полезно сразу представлять конкретную сцену: касса, улица, учебная аудитория, рабочий чат. "
                f"Для уровня '{language_level}' лучше не пытаться запомнить все сразу, а вытащить каркас: когда использовать, "
                "какой у фразы тон и какие части можно переставлять. После чтения проговори пример вслух и попробуй заменить одно слово своим."
            ),
            "culture": (
                "Эту тему лучше читать как описание правила среды, а не как абстрактный факт из статьи. "
                "Японская культура часто проявляется в мелких жестах, в ритме пространства, в том, как люди распределяют внимание и дистанцию. "
                "Поэтому важно не просто понять определение, а увидеть, как этот код работает в магазине, поезде, офисе, доме или на фестивале. "
                f"Твои интересы сейчас: {interests}. Попробуй связать эту тему с тем, что уже видел в аниме, фильмах, блогах или новостях, "
                "и выпиши один момент, который меняет твое восприятие повседневной Японии."
            ),
            "history": (
                "Историческую тему полезно держать как цепочку причин и последствий. "
                "Важно не только что произошло, но и почему этот поворот до сих пор чувствуется в языке, городе, институтах, массовой культуре и социальных привычках. "
                "Когда читаешь конспект, попробуй задавать себе три вопроса: что было до этого, что изменилось после, и какой след тема оставила в современной Японии. "
                f"С учетом интересов '{interests}' ищи мост между прошлым и настоящим: бизнес, поп-культура, городская жизнь, образование или повседневный этикет."
            ),
        }
        diagnostic_note = (
            f" Диагностика пользователя: {skill_summary}"
            if skill_summary
            else ""
        )
        return (
            f"{base_text} Эта карточка про тему '{topic}'. "
            f"{contextual_blocks.get(track, contextual_blocks['culture'])}"
            f"{diagnostic_note}"
        )

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
        weak_points = set(payload.get("weak_points") or [])
        if "Хирагана" in weak_points:
            return "Сначала прочитай строки по ромадзи, потом повтори без подсказки."
        if "Частицы" in weak_points:
            return "Проговаривай предложения с акцентом на частицы и меняй одно существительное."
        if "Базовый порядок предложения" in weak_points:
            return "Читай диалоги по ролям и отдельно отмечай тему, действие и объект."
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
        return AIAdviceDTO(
            headline="Следующий шаг",
            summary=(
                f"Сейчас лучше закончить текущую партию в разделе '{weakest_track.title}'. "
                f"Отдельно стоит следить за темами: {weak_points}."
            ),
            focus_points=[
                f"Закрой текущую партию в разделе '{weakest_track.title}'.",
                "После этого открой речевую практику и проговори слова из языкового блока.",
                "Перед новой партией отметь 2-3 места, которые остались непонятными.",
            ],
        )
