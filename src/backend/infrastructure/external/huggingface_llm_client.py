from __future__ import annotations

import json
from hashlib import sha256
from json import JSONDecoder

import httpx

from src.backend.dependencies.settings import Settings
from src.backend.domain.content import TrackType
from src.backend.domain.user import User
from src.backend.dto.learning_dto import GeneratedCardDraftDTO
from src.backend.dto.profile_dto import AIAdviceDTO, ProgressReportDTO
from src.backend.infrastructure.cache import KeyValueStore


class HuggingFaceLLMClient:
    def __init__(self, store: KeyValueStore):
        self._store = store
        self._http_client = httpx.AsyncClient(timeout=45.0)

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
            "user_id": user.id,
            "goal": user.learning_goal.value if user.learning_goal else None,
            "language_level": (
                user.language_level.value if user.language_level else None
            ),
            "interests": user.interests,
            "report": report.model_dump(),
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
                            "content": "Ты наставник ImmersJP. Верни JSON-объект с полями headline, summary, focus_points.",
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
        for item in parsed[: payload["batch_size"]]:
            normalized.append(
                GeneratedCardDraftDTO(
                    topic=str(item.get("topic") or "Тема без названия").strip(),
                    explanation=str(item.get("explanation") or "").strip(),
                    examples=[
                        str(example).strip() for example in item.get("examples") or []
                    ][:3],
                    key_terms=[
                        str(term).strip() for term in item.get("key_terms") or []
                    ][:5],
                )
            )
        if len(normalized) < payload["batch_size"]:
            fallback = HuggingFaceLLMClient._fallback_cards(payload)
            normalized.extend(fallback[len(normalized) : payload["batch_size"]])
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
            "Верни JSON-массив, где у каждой карточки есть topic, explanation, examples, key_terms."
        )

    @staticmethod
    def _build_advice_prompt(user: User, report: ProgressReportDTO) -> str:
        return (
            f"Пользователь: {user.display_name}.\n"
            f"Цель: {user.learning_goal.value if user.learning_goal else 'не указана'}.\n"
            f"Уровень: {user.language_level.value if user.language_level else 'не указан'}.\n"
            f"Интересы: {', '.join(user.interests) or 'не указаны'}.\n"
            f"Отчет: {report.model_dump_json()}\n"
            "Верни JSON-объект с полями headline, summary, focus_points."
        )

    @staticmethod
    def _fallback_cards(payload: dict) -> list[GeneratedCardDraftDTO]:
        interests = ", ".join(payload.get("interests") or []) or "живой контекст"
        library = {
            "language": [
                (
                    "Приветствия без учебниковой скуки",
                    "Когда и почему меняется тон японского приветствия.",
                    ["おはようございます", "こんにちは", "こんばんは"],
                    ["挨拶", "丁寧", "会話"],
                ),
                (
                    "Самопрезентация в реальном диалоге",
                    "Минимальный набор фраз, чтобы представиться естественно.",
                    ["はじめまして。", "セルゲイです。", "よろしくお願いします。"],
                    ["自己紹介", "名前", "よろしく"],
                ),
                (
                    "Просьба и вежливость",
                    "Как просить мягко и не звучать резко.",
                    [
                        "水をください。",
                        "もう一度お願いします。",
                        "手伝ってもらえますか。",
                    ],
                    ["ください", "お願い", "丁寧"],
                ),
                (
                    "Город и транспорт",
                    "Язык станции, маршрута и коротких вопросов на улице.",
                    [
                        "駅はどこですか。",
                        "この電車は新宿に行きますか。",
                        "ここから遠いですか。",
                    ],
                    ["駅", "電車", "道"],
                ),
                (
                    "Покупка в магазине",
                    "Что чаще всего звучит у кассы и в торговом зале.",
                    ["これをください。", "袋はいりません。", "カードで払えますか。"],
                    ["買う", "袋", "カード"],
                ),
                (
                    "Еда и предпочтения",
                    "Как объяснить вкусы и ограничения без сложной грамматики.",
                    ["魚が好きです。", "辛いものは苦手です。", "肉は食べません。"],
                    ["好き", "苦手", "食べる"],
                ),
                (
                    "Реакции в разговоре",
                    "Короткие фразы, которые делают речь живой.",
                    ["なるほど。", "本当ですか。", "すごいですね。"],
                    ["反応", "自然", "会話"],
                ),
                (
                    "Язык учебы",
                    "Фразы, с которыми проще учиться и уточнять непонятное.",
                    [
                        "この漢字はどう読みますか。",
                        "もう少しゆっくりお願いします。",
                        "メモしてもいいですか。",
                    ],
                    ["漢字", "読む", "勉強"],
                ),
                (
                    "Рабочая вежливость",
                    "Фразы для переписки и коротких рабочих диалогов.",
                    [
                        "確認します。",
                        "少々お待ちください。",
                        "共有ありがとうございます。",
                    ],
                    ["確認", "共有", "仕事"],
                ),
                (
                    "Частицы без боли",
                    "Как частицы держат каркас японского предложения.",
                    ["私は学生です。", "東京に行きます。", "日本語が好きです。"],
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
        previous_topics = {
            item.lower() for item in payload.get("previous_topics") or []
        }
        selected: list[GeneratedCardDraftDTO] = []
        for topic, explanation, examples, key_terms in library.get(
            payload["track"], []
        ):
            if topic.lower() in previous_topics:
                continue
            selected.append(
                GeneratedCardDraftDTO(
                    topic=topic,
                    explanation=f"{explanation} Текущая связка с интересами пользователя: {interests}.",
                    examples=examples,
                    key_terms=key_terms,
                )
            )
            if len(selected) == payload["batch_size"]:
                break
        while len(selected) < payload["batch_size"]:
            index = len(selected) + 1
            selected.append(
                GeneratedCardDraftDTO(
                    topic=f"Резервная тема {payload['batch_number']}.{index}",
                    explanation=(
                        "Эта карточка собрана локальным генератором, чтобы обучение не останавливалось. "
                        f"Трек: {payload['track']}. Интересы: {interests}."
                    ),
                    examples=[
                        "Сравни тему с тем, что уже видел в медиа или путешествиях.",
                        "Сформулируй один свой пример после чтения.",
                        "Вернись к карточке через день и проверь, что осталось в памяти.",
                    ],
                    key_terms=[
                        payload["track"],
                        "Japan",
                        "context",
                        f"batch-{payload['batch_number']}",
                    ][:5],
                )
            )
        return selected

    @staticmethod
    def _fallback_advice(user: User, report: ProgressReportDTO) -> AIAdviceDTO:
        weakest_track = min(
            report.tracks,
            key=lambda item: item.completion_rate if item.generated_cards else 101,
        )
        goal = user.learning_goal.value if user.learning_goal else "погружение"
        level = user.language_level.value if user.language_level else "без уровня"
        return AIAdviceDTO(
            headline="Не разрывай фокус",
            summary=(
                f"Для цели '{goal}' и уровня '{level}' сейчас полезнее добить текущую партию в блоке '{weakest_track.title}'. "
                "Так обучение будет выглядеть как маршрут, а не как набор случайных тем."
            ),
            focus_points=[
                f"Закрой текущий батч в разделе '{weakest_track.title}'.",
                "После каждой карточки выпиши одно новое слово или одну культурную деталь.",
                "Не переходи к следующей партии, пока текущая не стала понятной в собственных формулировках.",
            ],
        )
