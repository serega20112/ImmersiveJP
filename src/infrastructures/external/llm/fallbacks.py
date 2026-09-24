from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructures.external.llm.client import HuggingFaceLLMClient

from src.application.dto.learning import (
    GeneratedCardDraftDTO,
    SpeechDialogueDTO,
    SpeechDialogueTurnDTO,
    SpeechLineDTO,
    SpeechPracticeDTO,
)
from src.application.dto.mentor import MentorReplyDTO
from src.application.dto.profile import (
    AIAdviceDTO,
    LearningPlanPageDTO,
    ProgressReportDTO,
)
from src.domain.aggregates.user import User
from src.domain.entities.mentor import MentorFocus
from src.infrastructures.external.llm.fallback_content import (
    card_library,
    default_language_scene,
    language_scenes,
)


class LLMFallbackMixin:
    @staticmethod
    def _fallback_cards(
        payload: dict,
        excluded_topics: set[str] | None = None,
        excluded_example_signatures: set[tuple[str, ...]] | None = None,
    ) -> list[GeneratedCardDraftDTO]:
        interests = ", ".join(payload.get("interests") or []) or "живой контекст"
        library = card_library()
        previous_topics = {item.casefold() for item in payload.get("previous_topics") or []}
        if excluded_topics:
            previous_topics.update(topic.casefold() for topic in excluded_topics)
        seen_example_signatures = set(excluded_example_signatures or set())
        selected: list[GeneratedCardDraftDTO] = []
        for card in library.get(payload["track"], []):
            topic = card.topic
            explanation = card.explanation
            examples = list(card.examples)
            key_terms = list(card.key_terms)
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
                example_signature = HuggingFaceLLMClient._example_signature(draft.examples)
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
                (
                    "мягкие просьбы",
                    "Важно выбрать форму, которая звучит вежливо, но не излишне тяжело для реальной сцены.",
                ),
                (
                    "короткие уточнения",
                    "Такие реплики помогают быстро сузить ситуацию и не потеряться в деталях.",
                ),
                (
                    "переспрос без неловкости",
                    "Переспрос в японском часто подается мягко, чтобы не ломать ритм разговора.",
                ),
                (
                    "естественные реакции",
                    "Живой диалог держится не только на вопросах, но и на коротких реакциях, которые поддерживают контакт.",
                ),
                (
                    "вежливые отказы",
                    "Отказ обычно смягчают так, чтобы сохранить дистанцию и не звучать резко.",
                ),
                (
                    "самопрезентация по делу",
                    "Короткое представление должно сразу объяснять, кто ты и зачем находишься в этой ситуации.",
                ),
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
                (
                    "как считывается уважение",
                    "Главное здесь не декларация ценностей, а мелкие действия, которые уменьшают трение для других.",
                ),
                (
                    "почему норму редко объясняют вслух",
                    "Многие культурные правила работают именно потому, что считываются из контекста, а не проговариваются отдельно.",
                ),
                (
                    "что считается удобством для других",
                    "Удобство в японской среде часто понимают как умение не создавать лишнюю нагрузку для общего пространства.",
                ),
                (
                    "как маленькие жесты создают доверие",
                    "Репутация спокойного и надежного человека собирается из повторяющихся мелких действий.",
                ),
                (
                    "что происходит, когда ритм нарушают",
                    "Нарушение нормы чаще всего не вызывает открытую конфронтацию, но резко меняет атмосферу взаимодействия.",
                ),
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
                (
                    "через повседневность",
                    "Такой ракурс помогает увидеть, как большие процессы опускаются в рутину обычного человека.",
                ),
                (
                    "через город",
                    "Городская ткань показывает след истории нагляднее, чем абстрактный список дат.",
                ),
                (
                    "через институты",
                    "Институты сохраняют последствия исторических решений дольше, чем политические лозунги.",
                ),
                (
                    "через культуру памяти",
                    "Важно смотреть, как тема переживается, вспоминается и спорится в разных поколениях.",
                ),
                (
                    "через работу и образование",
                    "Школа и рынок труда часто лучше всего показывают, как история превращается в норму.",
                ),
            ]

        for context_title, context_text, _examples, base_terms in contexts:
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
                example_signature = HuggingFaceLLMClient._example_signature(generated_examples)
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
            HuggingFaceLLMClient._parse_seed_word(word) for word in payload.get("words") or []
        ]
        if not seed_words:
            seed_words = [HuggingFaceLLMClient._parse_seed_word("日本語 | nihongo | японский язык")]

        sentence_templates = [
            (
                "{surface}を使います。",
                "{reading} o tsukaimasu.",
                "Я использую {translation}.",
            ),
            (
                "毎日{surface}を練習します。",
                "mainichi {reading} o renshuu shimasu.",
                "Я каждый день тренирую {translation}.",
            ),
            (
                "{surface}が好きです。",
                "{reading} ga suki desu.",
                "Мне нравится {translation}.",
            ),
            (
                "今日は{surface}を確認します。",
                "kyou wa {reading} o kakunin shimasu.",
                "Сегодня я повторяю {translation}.",
            ),
            (
                "あとで{surface}を読みます。",
                "ato de {reading} o yomimasu.",
                "Позже я прочитаю {translation}.",
            ),
            (
                "先生と{surface}を話します。",
                "sensei to {reading} o hanashimasu.",
                "Я обсуждаю {translation} с преподавателем.",
            ),
            (
                "友だちに{surface}を見せます。",
                "tomodachi ni {reading} o misemasu.",
                "Я показываю {translation} другу.",
            ),
            (
                "まず{surface}を覚えます。",
                "mazu {reading} o oboemasu.",
                "Сначала я запоминаю {translation}.",
            ),
            (
                "明日{surface}をもう一度使います。",
                "ashita {reading} o mou ichido tsukaimasu.",
                "Завтра я еще раз использую {translation}.",
            ),
            (
                "この場面では{surface}が大事です。",
                "kono bamen de wa {reading} ga daiji desu.",
                "В этой сцене важно {translation}.",
            ),
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
                    (
                        "A",
                        "{surface}はありますか。",
                        "{reading} wa arimasu ka.",
                        "У вас есть {translation}?",
                    ),
                    (
                        "B",
                        "はい、{surface}があります。",
                        "hai, {reading} ga arimasu.",
                        "Да, {translation} есть.",
                    ),
                    (
                        "A",
                        "じゃあ、{surface}をお願いします。",
                        "jaa, {reading} o onegaishimasu.",
                        "Тогда {translation}, пожалуйста.",
                    ),
                ],
            ),
            (
                "Уточнить понимание",
                "Проверка, что слово услышано и понято правильно.",
                [
                    (
                        "A",
                        "{surface}はどういう意味ですか。",
                        "{reading} wa dou iu imi desu ka.",
                        "Что значит {translation}?",
                    ),
                    (
                        "B",
                        "{surface}は大切な言葉です。",
                        "{reading} wa taisetsu na kotoba desu.",
                        "{translation} это важное слово.",
                    ),
                    (
                        "A",
                        "わかりました。{surface}を使ってみます。",
                        "wakarimashita. {reading} o tsukatte mimasu.",
                        "Понял. Попробую использовать {translation}.",
                    ),
                ],
            ),
            (
                "Короткая самопрезентация",
                "Вставить слово в очень простой разговор о себе.",
                [
                    (
                        "A",
                        "今、{surface}を勉強しています。",
                        "ima, {reading} o benkyou shiteimasu.",
                        "Сейчас я изучаю {translation}.",
                    ),
                    (
                        "B",
                        "いいですね。どこで{surface}を使いますか。",
                        "ii desu ne. doko de {reading} o tsukaimasu ka.",
                        "Здорово. Где ты используешь {translation}?",
                    ),
                    (
                        "A",
                        "授業と会話で使います。",
                        "jugyou to kaiwa de tsukaimasu.",
                        "Использую на занятиях и в разговоре.",
                    ),
                ],
            ),
            (
                "Переспрос без паники",
                "Формула, чтобы спокойно попросить повторить слово.",
                [
                    (
                        "A",
                        "すみません、{surface}をもう一度言ってください。",
                        "sumimasen, {reading} o mou ichido itte kudasai.",
                        "Извините, повторите {translation} еще раз.",
                    ),
                    (
                        "B",
                        "はい、{surface}です。",
                        "hai, {reading} desu.",
                        "Да, это {translation}.",
                    ),
                    (
                        "A",
                        "ありがとうございます。今なら言えます。",
                        "arigatou gozaimasu. ima nara iemasu.",
                        "Спасибо. Теперь я могу это произнести.",
                    ),
                ],
            ),
            (
                "Мини-диалог для закрепления",
                "Три реплики, которые удобно проговаривать циклом.",
                [
                    (
                        "A",
                        "{surface}を知っていますか。",
                        "{reading} o shitteimasu ka.",
                        "Ты знаешь {translation}?",
                    ),
                    (
                        "B",
                        "はい、少し知っています。",
                        "hai, sukoshi shitteimasu.",
                        "Да, немного знаю.",
                    ),
                    (
                        "A",
                        "じゃあ、次は{surface}で文を作りましょう。",
                        "jaa, tsugi wa {reading} de bun o tsukurimashou.",
                        "Тогда давай составим предложение с {translation}.",
                    ),
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
            dialogues.append(SpeechDialogueDTO(title=title, scenario=scenario, turns=turns))

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
        """Выбрать языковую сцену по маркеру в заголовке контекста.

        Args:
            context_title: Заголовок контекста, по которому ищется сцена.

        Returns:
            Копию набора частей сцены: вызывающий код достраивает фразы, и
            общий кэш трогать нельзя.
        """
        normalized = context_title.casefold()
        for marker, scene in language_scenes():
            if marker in normalized:
                return dict(scene)
        return dict(default_language_scene())

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

    @staticmethod
    def _fallback_mentor_reply(
        report: ProgressReportDTO,
        plan: LearningPlanPageDTO,
        message: str,
        active_focus: MentorFocus | None,
    ) -> MentorReplyDTO:
        focus_title = active_focus.title if active_focus is not None else "текущую базу"
        weakest_track = min(
            report.tracks,
            key=lambda item: item.completion_rate if item.generated_cards else 101,
        )
        normalized = message.casefold()
        if "кандз" in normalized or "kanji" in normalized:
            reply = (
                "Кандзи лучше не врезать отдельным хаотичным блоком. Сначала добей текущую языковую партию и работу по ней, "
                "потому что именно через них система понимает, насколько можно усиливать чтение. Фокус уже смещен на кандзи: "
                "следующие языковые партии будут сильнее тянуть чтение знаков и узнавание их в словах."
            )
        elif "частиц" in normalized or "граммат" in normalized:
            reply = (
                "Сейчас невыгодно прыгать дальше по плану, пока не держатся частицы и каркас предложения. "
                "Сначала закрой текущий language batch, затем работа покажет, где именно ломается грамматика, и уже после этого новая партия пойдет с большим упором на этот блок."
            )
        else:
            reply = (
                f"Сейчас план держится на этапе '{plan.current_stage_title}'. Я бы не рвал траекторию, а использовал наставника как механизм перенастройки фокуса: "
                f"закрываешь текущую партию, проходишь работу, затем следующая генерация усиливает блок '{focus_title}'."
            )
        return MentorReplyDTO(
            reply=reply,
            action_steps=[
                f"Закрой текущую партию в разделе '{weakest_track.title}'.",
                "После этого пройди речевую практику или работу по уже закрытому батчу.",
                f"Открой следующую языковую партию: она пойдет с фокусом на '{focus_title}'.",
            ],
            suggested_prompts=HuggingFaceLLMClient._mentor_prompt_suggestions(active_focus),
        )

    @staticmethod
    def _mentor_prompt_suggestions(
        active_focus: MentorFocus | None,
    ) -> list[str]:
        prompts = [
            "Что мне сейчас мешает идти дальше по плану?",
            "Как лучше добить слабые места без новой каши из тем?",
            "Когда можно будет убрать часть опор и идти сложнее?",
        ]
        if active_focus is not None:
            prompts.insert(0, f"Как лучше закрепить фокус: {active_focus.title}?")
        return prompts[:3]

    @staticmethod
    def _fallback_knowledge_check(payload: dict) -> list[dict]:
        return [
            {
                "id": "q1",
                "kind": "recall",
                "question": "Как переводится 食べる на русский?",
                "context": "",
                "expected_answer": "есть, кушать",
                "hints": ["Базовый глагол"],
            },
            {
                "id": "q2",
                "kind": "translation_ru_ja",
                "question": "Переведи на японский: «я иду в школу»",
                "context": "Используй глагол 行く",
                "expected_answer": "私は学校に行きます",
                "hints": ["Подлежащее + は + место + に + глагол"],
            },
            {
                "id": "q3",
                "kind": "grammar",
                "question": "Какой частицей отмечается объект действия?",
                "context": "",
                "expected_answer": "を",
                "hints": ["Ставится после существительного"],
            },
        ]

    @staticmethod
    def _fallback_knowledge_eval(
        questions: list[dict],
        answers: dict[str, str],
    ) -> dict:
        results = []
        correct_count = 0
        for q in questions:
            qid = q["id"]
            user_ans = answers.get(qid, "").strip().lower()
            expected = q.get("expected_answer", "").strip().lower()
            is_correct = bool(user_ans and expected and user_ans == expected)
            if is_correct:
                correct_count += 1
            results.append(
                {
                    "question_id": qid,
                    "is_correct": is_correct,
                    "user_answer": answers.get(qid, ""),
                    "expected_answer": q.get("expected_answer", ""),
                    "feedback": "Верно!" if is_correct else "Ответ не совпал с ожидаемым.",
                }
            )
        total = len(questions) or 1
        score = round((correct_count / total) * 100)
        return {
            "score": score,
            "summary": f"Правильно: {correct_count} из {len(questions)}.",
            "results": results,
        }
