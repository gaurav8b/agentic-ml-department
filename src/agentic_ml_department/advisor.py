"""Business-question adviser: deterministic by default, optional local LangChain/Ollama."""
from __future__ import annotations

from .config import settings
from .modeling import OBJECTIVES


def build_business_questions(objective: str, profiles: list[dict], instructions: str = "") -> dict:
    spec = OBJECTIVES[objective]
    questions = [
        {"id": "primary", "question": spec["business_question"], "business_reason": spec["business_value"], "recommended": True},
        {"id": "drivers", "question": "Which observable factors are most associated with this outcome?", "business_reason": "Helps teams understand which operational levers may be worth investigating.", "recommended": True},
        {"id": "segments", "question": "Which customer or lead segments have materially different outcome rates?", "business_reason": "Supports more targeted sales and customer-success actions.", "recommended": True},
    ]
    total_rows = sum(p.get("rows", 0) for p in profiles)
    note = f"The connected synthetic business currently exposes {total_rows:,} rows across {len(profiles)} business datasets."
    llm_note = None
    if settings.agent_llm_provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
            from langchain_core.messages import HumanMessage, SystemMessage
            llm = ChatOllama(model=settings.ollama_model, base_url=settings.ollama_base_url, temperature=0.1)
            prompt = (
                f"Business objective: {spec['business_question']}\n"
                f"Dataset profiles: {profiles[:5]}\n"
                f"Supervisor instructions: {instructions or 'None'}\n"
                "Suggest at most three extra, testable business questions. Do not invent fields or claim causation. "
                "Return concise numbered questions and explain why each matters."
            )
            response = llm.invoke([SystemMessage(content="You are a cautious business analytics adviser. Be specific and avoid unsupported causal claims."), HumanMessage(content=prompt)])
            llm_note = str(response.content)
        except Exception as exc:
            llm_note = f"Optional local model was unavailable; deterministic suggestions were used ({type(exc).__name__})."
    return {"objective": objective, "objective_label": spec["label"], "questions": questions,
            "data_note": note, "llm_advice": llm_note,
            "supervisor_instructions": instructions,
            "approval_note": "Select or amend the business question before the model-training stage. The demo only trains one approved objective per run."}
