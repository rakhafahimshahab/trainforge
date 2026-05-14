from __future__ import annotations

import logging
from typing import Iterable

from django.conf import settings
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from .schemas import AIPlanDraft

logger = logging.getLogger(__name__)

def _client_brief(client) -> str:
    parts = [
        f"Name: {client.full_name}",
        f"Goal: {client.fitness_goal or 'general fitness'}",
        f"Preferred training times: {client.preferred_times or 'unspecified'}",
        f"Notes / limitations: {client.notes or 'none recorded'}",
    ]
    return " | ".join(parts)

def _library_brief(exercises: Iterable) -> str:
    rows = [f"- {ex.name} ({ex.get_category_display()}, default {ex.default_display})" for ex in exercises]
    if not rows:
        return "No exercises in the trainer's library yet."
    return "\n".join(rows)

def generate_plan_draft(
    client,
    *,
    library,
    program_length_weeks: int,
    session_duration_min: int,
    extra_instructions: str,
) -> dict:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return {
            "error": (
                "OpenAI API key is not configured. Add OPENAI_API_KEY to your .env "
                "file to enable AI drafts."
            )
        }

    parser = JsonOutputParser(pydantic_object=AIPlanDraft)

    prompt = PromptTemplate(
        template=(
            "You are an experienced personal trainer drafting a multi-day program for one client.\n\n"
            "CLIENT:\n{client_brief}\n\n"
            "TRAINER'S EXERCISE LIBRARY (prefer these names where possible):\n{library_brief}\n\n"
            "CONSTRAINTS:\n"
            "- Program length: {weeks} week(s)\n"
            "- Session duration: about {minutes} minutes\n"
            "- Days per week: choose based on the client's preferred times (default 3 if unclear)\n"
            "- Respect noted limitations (e.g. avoid heavy loading on injured joints)\n"
            "- Extra instructions: {extra}\n\n"
            "Return ONE valid JSON object matching the schema. Do not wrap it in markdown.\n"
            "{format_instructions}\n"
        ),
        input_variables=["client_brief", "library_brief", "weeks", "minutes", "extra"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    llm = ChatOpenAI(
        api_key=api_key,
        model=settings.OPENAI_MODEL,
        temperature=0.6,
    )
    chain = prompt | llm | parser

    try:
        result = chain.invoke({
            "client_brief": _client_brief(client),
            "library_brief": _library_brief(library),
            "weeks": program_length_weeks,
            "minutes": session_duration_min,
            "extra": (extra_instructions or "none").strip(),
        })
    except Exception as exc:                                                                       
        logger.exception("AI draft generation failed")
        return {"error": f"Could not generate a draft: {exc}"}

    if hasattr(result, "model_dump"):
        return result.model_dump()
    return dict(result)
