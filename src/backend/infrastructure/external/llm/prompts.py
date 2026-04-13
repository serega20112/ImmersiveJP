from __future__ import annotations

import json

from src.backend.domain.mentor import MentorMessage
from src.backend.domain.user import User
from src.backend.dto.learning import TrackWorkResultDTO
from src.backend.dto.profile_dto import LearningPlanPageDTO, ProgressReportDTO


class LLMPromptMixin:
    @staticmethod
    def _build_cards_prompt(payload: dict) -> str:
        interests = ", ".join((payload["interests"] or [])[:6]) or "не указаны"
        previous = ", ".join((payload["previous_topics"] or [])[:12]) or "нет"
        mentor_focus_note = (
            f"Особый запрос пользователя на ближайшие партии: {payload.get('mentor_focus')}\n"
            if payload.get("mentor_focus")
            else ""
        )
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
            f"{HuggingFaceLLMClient._track_scope_instruction(payload.get('track'))}\n"
            "Цель, интересы и горизонт обучения могут менять только угол подачи внутри выбранного трека, "
            "но не имеют права уводить карточки в другой трек.\n"
            f"{mentor_focus_note}"
            "Верни JSON-массив, где у каждой карточки есть topic, explanation, examples, key_terms.\n"
            "topic: короткий заголовок до 7 слов.\n"
            f"{HuggingFaceLLMClient._explanation_length_instruction(payload)}\n"
            "Examples можно вернуть пустым массивом или массивом до 2 очень коротких строк в формате: Japanese | Romaji | Русский перевод.\n"
            "key_terms возвращай массивом ровно из 3 коротких строк. Если термин японский, формат каждой строки: Термин | Русский перевод.\n"
            "Если термин уже русский, можно вернуть его как есть или дать короткое пояснение через |.\n"
            "Пиши естественным русским языком без канцелярита и рекламного тона.\n"
            "Не используй английские слова, если есть нормальный русский эквивалент.\n"
            "Не упоминай диагностику пользователя, trust score, тесты, сильные или слабые стороны.\n"
            "Не начинай explanation с формул вроде 'эта карточка про тему', 'смотри на тему', 'для уровня'.\n"
            "Темы внутри партии должны отличаться не только названием, но и сценой применения.\n"
            "Если даешь examples, они должны быть уникальными и прямо отражать тему карточки.\n"
            "Пиши плотно и коротко. Лучше компактно, чем многословно."
        )

    @staticmethod
    def _build_work_review_prompt(
        payload: dict,
        fallback_result: TrackWorkResultDTO,
    ) -> str:
        tasks_json = json.dumps(payload.get("tasks") or [], ensure_ascii=False)
        return (
            "Проверь учебную работу ImmersJP по уже завершенной партии карточек.\n"
            f"Трек: {payload['track']}\n"
            f"Номер партии: {payload['batch_number']}\n"
            f"Цель: {HuggingFaceLLMClient._goal_label(payload.get('goal'))}\n"
            f"Уровень: {HuggingFaceLLMClient._level_label(payload.get('language_level'))}\n"
            f"Горизонт обучения: {HuggingFaceLLMClient._timeline_label(payload.get('study_timeline'))}\n"
            f"{HuggingFaceLLMClient._track_scope_instruction(payload.get('track'))}\n"
            "Оценивай только то, насколько ответ опирается на материал партии и закрывает сам вопрос.\n"
            "Для recall-задач сверяйся с expected_answers, но засчитывай стандартные варианты ромадзи, "
            "мелкие опечатки, kana/kanji запись той же фразы и короткие естественные русские перефразировки, "
            "если смысл совпадает.\n"
            "Для production и immersion разрешай перефразировку, если смысл верный и опора на материал партии реально есть.\n"
            "Не засчитывай пустые ответы, общие фразы не по теме и ответы, которые не используют нужные элементы.\n"
            f"Проходной балл: {fallback_result.pass_score}\n"
            f"Задания и ответы JSON: {tasks_json}\n"
            "Верни JSON-объект с полями summary, verdict, task_results, certificate_statement.\n"
            "task_results: массив объектов с полями task_id, is_correct, feedback.\n"
            "feedback: одно короткое предложение о том, что получилось или чего не хватило.\n"
            "summary: 1 короткое предложение по партии целиком.\n"
            "verdict: 1 короткое предложение, можно ли считать материал закрепленным.\n"
            "certificate_statement: optional, только если ответ действительно сильный.\n"
            "Без markdown, без reasoning, без текста вне JSON."
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
    def _build_mentor_prompt(
        *,
        user: User,
        report: ProgressReportDTO,
        plan: LearningPlanPageDTO,
        message: str,
        history: list[MentorMessage],
    ) -> str:
        history_lines = []
        for item in history[-4:]:
            history_lines.append(f"{item.role}: {item.content}")
        history_text = "\n".join(history_lines) or "история пока пустая"
        track_lines = [
            f"{track.title}: {track.completed_cards}/{track.generated_cards}, батчей закрыто {track.completed_batches}"
            for track in report.tracks
        ]
        return (
            "Ты помогаешь выстроить следующий практический шаг, не ломая уже текущий план.\n"
            f"Пользователь: {user.display_name}\n"
            f"Цель: {HuggingFaceLLMClient._goal_label(user.learning_goal.value if user.learning_goal else None)}\n"
            f"Уровень: {HuggingFaceLLMClient._level_label(user.language_level.value if user.language_level else None)}\n"
            f"Горизонт обучения: {HuggingFaceLLMClient._timeline_label(user.study_timeline.value if user.study_timeline else None)}\n"
            f"Trust score: {report.trust_score.score} ({report.trust_score.band_title})\n"
            f"Следующий шаг: {report.next_step}\n"
            f"Текущий этап плана: {plan.current_stage_title}\n"
            f"Режим контента: {plan.content_mode.title}\n"
            f"Темп: {plan.pace_mode.title}\n"
            f"Слабые места: {', '.join(report.skill_assessment.weak_points) if report.skill_assessment and report.skill_assessment.weak_points else 'нет явных'}\n"
            f"Сильные места: {', '.join(report.skill_assessment.strengths) if report.skill_assessment and report.skill_assessment.strengths else 'пока не выделены'}\n"
            f"Прогресс по трекам:\n- " + "\n- ".join(track_lines) + "\n"
            f"Последние сообщения:\n{history_text}\n"
            f"Новый запрос пользователя: {message}\n"
            "Верни JSON-объект.\n"
            "reply: один короткий абзац до 320 символов.\n"
            "action_steps: ровно 3 коротких шага.\n"
            "suggested_prompts: ровно 2 коротких следующих вопроса.\n"
            "Если пользователь просит усилить кандзи, грамматику или речь, объясни через текущую партию, работу и следующую генерацию, а не через хаотичный прыжок."
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
            "sentences: ровно 10 объектов с полями japanese, romaji, translation.\n"
            "Каждое предложение короткое, бытовое, пригодное для проговаривания.\n"
            "dialogues: ровно 5 объектов с полями title, scenario, turns.\n"
            "Каждый dialogue очень короткий: title 2-4 слова, scenario 1 короткая фраза, turns ровно 2 объекта.\n"
            "turns: объекты с полями speaker, japanese, romaji, translation.\n"
            "Каждая реплика короткая, без длинных объяснений.\n"
            "coaching_tip: 1 короткое практическое предложение.\n"
            "difficulty_label: 2-3 слова без рекламного тона.\n"
            "Используй максимум слов из списка и не добавляй текст вне JSON."
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
            "three_months": "Explanation делай плотным конспектом длиной около 35-50 слов.",
            "six_months": "Explanation делай плотным конспектом длиной около 40-55 слов.",
            "one_year": "Explanation делай плотным конспектом длиной около 45-60 слов.",
            "two_years": "Explanation делай компактным, но содержательным конспектом длиной около 50-70 слов.",
            "flexible": "Explanation делай компактным конспектом длиной около 45-65 слов.",
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
    def _track_scope_instruction(track: str | None) -> str:
        instructions = {
            "language": (
                "Трек language означает только японский язык: слова, грамматика, частицы, регистр, "
                "фразы, речевые сцены и понимание реплик. Не превращай карточки в культурологию, "
                "историю, визовые инструкции, бытовой гайд по переезду или общие советы по жизни."
            ),
            "culture": (
                "Трек culture означает только культурные нормы, повседневный быт, ритуалы, сервис, "
                "этикет, общественное поведение, социальные роли и привычки среды. Не уходи в "
                "историческую хронологию, войны, реформы, политические события, а также не делай "
                "из карточек учебник языка, визовый гайд или инструкцию по документам."
            ),
            "history": (
                "Трек history означает только историю: эпохи, события, реформы, войны, фигуры, "
                "политические и социальные переломы, экономические сдвиги, память о прошлом и их "
                "последствия. Не уходи в визы, переезд, жилье, аренду, транспорт, бытовые советы, "
                "этикет повседневности и разговорные фразы."
            ),
        }
        return instructions.get(str(track), instructions["culture"])
