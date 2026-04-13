from __future__ import annotations

import logging
from collections.abc import Mapping
import re

from src.backend.domain.mentor import MentorFocus
from src.backend.domain.user import User
from src.backend.dto.learning import (
    GeneratedCardDraftDTO,
    SpeechDialogueDTO,
    SpeechDialogueTurnDTO,
    SpeechLineDTO,
    SpeechPracticeDTO,
    TrackWorkResultDTO,
    TrackWorkTaskResultDTO,
)
from src.backend.dto.mentor_dto import MentorReplyDTO
from src.backend.dto.profile_dto import (
    AIAdviceDTO,
    LearningPlanPageDTO,
    ProgressReportDTO,
)
from src.backend.infrastructure.observability import get_logger, log_event

logger = get_logger(__name__)


class LLMNormalizationMixin:
    @staticmethod
    def _normalize_cards(parsed: object, payload: dict) -> list[GeneratedCardDraftDTO]:
        parsed_items = HuggingFaceLLMClient._coerce_list(parsed)
        normalized: list[GeneratedCardDraftDTO] = []
        seen_topics: set[str] = set()
        seen_example_signatures: set[tuple[str, ...]] = set()
        for raw_item in parsed_items[: payload["batch_size"]]:
            if not isinstance(raw_item, Mapping):
                continue
            item = dict(raw_item)
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
            if not HuggingFaceLLMClient._card_matches_track(
                track=str(payload["track"]),
                topic=topic,
                explanation=str(item.get("explanation") or "").strip(),
                examples=normalized_examples,
                key_terms=key_terms,
            ):
                log_event(
                    logger,
                    logging.WARNING,
                    "llm.card_track_filtered",
                    "Filtered generated card outside track scope",
                    track=str(payload["track"]),
                    topic=topic,
                )
                continue
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
    def _normalize_mentor_reply(
        parsed: object,
        report: ProgressReportDTO,
        plan: LearningPlanPageDTO,
        active_focus: MentorFocus | None,
    ) -> MentorReplyDTO:
        parsed_object = HuggingFaceLLMClient._coerce_object(parsed)
        reply = str(
            parsed_object.get("reply")
            or parsed_object.get("answer")
            or parsed_object.get("message")
            or parsed_object.get("summary")
            or ""
        ).strip()
        action_steps = HuggingFaceLLMClient._coerce_text_list(
            parsed_object.get("action_steps")
            or parsed_object.get("steps")
            or parsed_object.get("next_steps")
            or [],
            limit=3,
        )
        suggested_prompts = HuggingFaceLLMClient._coerce_text_list(
            parsed_object.get("suggested_prompts")
            or parsed_object.get("follow_up_prompts")
            or parsed_object.get("prompts")
            or [],
            limit=3,
        )

        # Если reply пустой, но есть список строк — попробуем интерпретировать как reply + steps
        if not reply and isinstance(parsed, list) and len(parsed) >= 2:
            strings = [str(item).strip() for item in parsed if str(item).strip()]
            if strings:
                reply = strings[0]
                action_steps = [s for s in strings[1:] if s][:3]

        if not reply or len(action_steps) < 2:
            log_event(
                logger,
                logging.WARNING,
                "llm.mentor_reply_normalization_failed",
                "Mentor reply normalization failed, using fallback",
                reply_found=bool(reply),
                reply_length=len(reply),
                action_steps_count=len(action_steps),
                action_steps=action_steps,
                parsed_keys=(
                    list(parsed_object.keys())
                    if isinstance(parsed_object, dict)
                    else []
                ),
                parsed_type=type(parsed).__name__,
                raw_parsed=str(parsed)[:500] if parsed else None,
            )
            return HuggingFaceLLMClient._fallback_mentor_reply(
                report, plan, reply or "", active_focus
            )
        return MentorReplyDTO(
            reply=reply,
            action_steps=action_steps,
            suggested_prompts=(
                suggested_prompts
                or HuggingFaceLLMClient._mentor_prompt_suggestions(active_focus)
            ),
        )

    @staticmethod
    def _normalize_speech_practice(parsed: object, payload: dict) -> SpeechPracticeDTO:
        parsed_object = HuggingFaceLLMClient._coerce_object(parsed)
        sentences = [
            HuggingFaceLLMClient._to_speech_line(item)
            for item in (parsed_object.get("sentences") or [])
        ]
        dialogues = [
            HuggingFaceLLMClient._to_speech_dialogue(item)
            for item in (parsed_object.get("dialogues") or [])
            if isinstance(item, dict)
        ]
        if len(sentences) < 10 or len(dialogues) < 5:
            return HuggingFaceLLMClient._fallback_speech_practice(payload)
        return SpeechPracticeDTO(
            words=list(payload["words"]),
            sentences=sentences[:10],
            dialogues=dialogues[:5],
            coaching_tip=str(parsed_object.get("coaching_tip") or "").strip()
            or HuggingFaceLLMClient._speech_coaching_tip(payload),
            difficulty_label=str(parsed_object.get("difficulty_label") or "").strip()
            or HuggingFaceLLMClient._speech_difficulty_label(payload),
        )

    @staticmethod
    def _normalize_work_review(
        parsed: object,
        payload: dict,
        fallback_result: TrackWorkResultDTO,
    ) -> TrackWorkResultDTO:
        parsed_object = HuggingFaceLLMClient._coerce_object(parsed)
        raw_results = parsed_object.get("task_results") or parsed_object.get("results")
        raw_results_by_id: dict[str, Mapping[str, object]] = {}
        if isinstance(raw_results, list):
            for item in raw_results:
                if not isinstance(item, Mapping):
                    continue
                task_id = str(item.get("task_id") or item.get("id") or "").strip()
                if task_id:
                    raw_results_by_id[task_id] = item

        fallback_by_id = {
            item.task_id: item for item in fallback_result.task_results
        }
        normalized_task_results: list[TrackWorkTaskResultDTO] = []
        correct = 0

        for task in payload.get("tasks") or []:
            task_id = str(task.get("id") or "").strip()
            fallback_item = fallback_by_id.get(task_id)
            if not task_id or fallback_item is None:
                continue
            raw_item = raw_results_by_id.get(task_id)
            if raw_item is None:
                normalized_item = fallback_item
            else:
                is_correct = HuggingFaceLLMClient._coerce_bool(
                    raw_item.get("is_correct")
                    if "is_correct" in raw_item
                    else raw_item.get("correct")
                )
                if is_correct is None:
                    is_correct = fallback_item.is_correct
                feedback = str(
                    raw_item.get("feedback")
                    or raw_item.get("note")
                    or raw_item.get("comment")
                    or ""
                ).strip() or fallback_item.feedback
                normalized_item = TrackWorkTaskResultDTO(
                    task_id=task_id,
                    is_correct=is_correct,
                    feedback=feedback,
                    revealed_answer=(
                        None if is_correct else fallback_item.revealed_answer
                    ),
                )
            if normalized_item.is_correct:
                correct += 1
            normalized_task_results.append(normalized_item)

        if not normalized_task_results:
            return fallback_result

        score = round((correct / len(normalized_task_results)) * 100)
        pass_score = fallback_result.pass_score
        passed = score >= pass_score
        summary = str(parsed_object.get("summary") or "").strip()
        verdict = str(parsed_object.get("verdict") or "").strip()
        certificate_statement = str(
            parsed_object.get("certificate_statement") or ""
        ).strip() or None

        return TrackWorkResultDTO(
            score=score,
            pass_score=pass_score,
            passed=passed,
            summary=summary or HuggingFaceLLMClient._default_work_summary(passed),
            verdict=verdict or HuggingFaceLLMClient._default_work_verdict(passed),
            certificate_statement=(
                certificate_statement
                or HuggingFaceLLMClient._default_work_certificate(
                    passed=passed,
                    track=str(payload.get("track") or ""),
                    score=score,
                )
            ),
            task_results=normalized_task_results,
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
    def _card_matches_track(
        *,
        track: str,
        topic: str,
        explanation: str,
        examples: list[str],
        key_terms: list[str],
    ) -> bool:
        combined = " ".join([topic, explanation, *examples, *key_terms]).casefold()
        if track == "language":
            return HuggingFaceLLMClient._matches_language_scope(combined, examples)
        if track == "culture":
            return HuggingFaceLLMClient._matches_culture_scope(combined)
        if track == "history":
            return HuggingFaceLLMClient._matches_history_scope(combined)
        return True

    @staticmethod
    def _matches_language_scope(text: str, examples: list[str]) -> bool:
        if any(HuggingFaceLLMClient._contains_japanese_chars(example) for example in examples):
            return True
        language_keywords = (
            "фраз",
            "слово",
            "лексик",
            "граммат",
            "частиц",
            "ромадзи",
            "кандзи",
            "диалог",
            "реплик",
            "чтени",
            "перевод",
            "произнош",
            "вежлив",
            "язык",
        )
        return HuggingFaceLLMClient._contains_any(text, language_keywords)

    @staticmethod
    def _matches_culture_scope(text: str) -> bool:
        culture_keywords = (
            "культур",
            "обыча",
            "ритуал",
            "этик",
            "норм",
            "повседнев",
            "быт",
            "сервис",
            "уважен",
            "обществен",
            "жест",
            "район",
            "сосед",
            "фестиваль",
            "мусор",
            "дом",
            "пространств",
            "очеред",
            "поведен",
            "традиц",
        )
        history_keywords = (
            "эпох",
            "войн",
            "реформ",
            "реставрац",
            "послево",
            "император",
            "сёгун",
            "мэйдзи",
            "эдо",
            "сэнгоку",
            "хронолог",
            "истор",
            "конституц",
        )
        language_keywords = (
            "ромадзи",
            "граммат",
            "частиц",
            "кандзи",
            "перевод",
            "фраз",
            "реплик",
            "диалог",
        )
        if HuggingFaceLLMClient._contains_any(text, culture_keywords):
            return True
        if HuggingFaceLLMClient._contains_any(text, history_keywords):
            return False
        if HuggingFaceLLMClient._contains_any(text, language_keywords):
            return False
        return False

    @staticmethod
    def _matches_history_scope(text: str) -> bool:
        history_keywords = (
            "истор",
            "эпох",
            "период",
            "войн",
            "реформ",
            "реставрац",
            "послево",
            "император",
            "сёгун",
            "мэйдзи",
            "эдо",
            "сэнгоку",
            "тайсё",
            "сёва",
            "хэйсэй",
            "токугава",
            "оккупац",
            "конституц",
            "памят",
            "модернизац",
            "индустри",
            "государств",
            "политическ",
            "социальн",
            "экономическ",
            "катастроф",
            "перелом",
            "бакумацу",
            "колони",
            "революц",
            "битв",
        )
        offscope_keywords = (
            "виза",
            "документ",
            "аренд",
            "квартир",
            "жиль",
            "переезд",
            "туризм",
            "ресторан",
            "магазин",
            "поезд",
            "станци",
            "клиник",
            "кафе",
            "офис",
            "университет",
            "ромадзи",
            "граммат",
            "частиц",
            "диалог",
            "фраз",
            "этикет",
        )
        if re.search(r"\b(1[6-9]\d{2}|20\d{2})\b", text):
            return True
        if HuggingFaceLLMClient._contains_any(text, history_keywords):
            return True
        if HuggingFaceLLMClient._contains_any(text, offscope_keywords):
            return False
        return False

    @staticmethod
    def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _contains_japanese_chars(value: str) -> bool:
        return bool(re.search(r"[ぁ-んァ-ヶ一-龯々ー]", value))

    @staticmethod
    def _coerce_bool(value: object) -> bool | None:
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().casefold()
            if normalized in {"true", "1", "yes", "y", "correct", "ok"}:
                return True
            if normalized in {"false", "0", "no", "n", "incorrect", "wrong"}:
                return False
        return None

    @staticmethod
    def _default_work_summary(passed: bool) -> str:
        if passed:
            return "Материал по этой партии держится уверенно."
        return "По партии еще есть пробелы. Лучше еще раз пройти карточки и повторить работу."

    @staticmethod
    def _default_work_verdict(passed: bool) -> str:
        if passed:
            return "Система видит, что этот набор уже можно использовать в коротких ответах и сценах."
        return "Система пока не уверена, что этот набор закрепился в практике."

    @staticmethod
    def _default_work_certificate(
        *,
        passed: bool,
        track: str,
        score: int,
    ) -> str | None:
        if passed and track == "language" and score >= 100:
            return (
                "По этой партии система считает, что бытовые конструкции используются "
                "без заметной опоры на подсказки."
            )
        return None

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
    def _normalize_advice_payload(
        parsed: object,
        user: User,
        report: ProgressReportDTO,
    ) -> AIAdviceDTO:
        parsed_object = HuggingFaceLLMClient._coerce_object(parsed)
        focus_points = HuggingFaceLLMClient._coerce_text_list(
            parsed_object.get("focus_points")
            or parsed_object.get("action_steps")
            or parsed_object.get("steps")
            or [],
            limit=3,
        )
        headline = str(
            parsed_object.get("headline")
            or parsed_object.get("title")
            or "Следующий шаг"
        ).strip()
        summary = str(
            parsed_object.get("summary")
            or parsed_object.get("reply")
            or parsed_object.get("message")
            or ""
        ).strip()
        if not summary or len(focus_points) < 2:
            return HuggingFaceLLMClient._fallback_advice(user, report)
        return AIAdviceDTO(
            headline=headline,
            summary=summary,
            focus_points=focus_points,
        )
