import json
import logging
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from flask import current_app

from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class EmailState(TypedDict):
    email: dict
    requirements: dict
    gmail_service: object

    context_str: str

    action: Optional[str]
    reasoning: Optional[str]
    error: Optional[str]

def prepare_context(state: EmailState) -> EmailState:
    email = state["email"]
    reqs = state.get("requirements", {})

    categories = reqs.get("categories", [])
    cat_text = "\n".join(
        f'  - {c["name"]}: {c.get("description", "")} (keywords: {", ".join(c.get("keywords", []))})'
        for c in categories
    ) or "  (No specific categories defined)"

    allowed = ", ".join(reqs.get("allowed_senders", [])) or "Any"
    blocked = ", ".join(reqs.get("blocked_senders", [])) or "None"
    global_kw = ", ".join(reqs.get("global_keywords", [])) or "None"
    summary = reqs.get("summary") or "Strict Allowlist Mode: You must ONLY keep or label emails that perfectly match the categories below. If an email does not match any category, you MUST delete it."
    
    category_names = [c.get("name") for c in categories if c.get("name")]
    available_labels = " | ".join([f'label:{n}' for n in category_names]) if category_names else "None (Do not use the label action)"

    context = f"""
=== USER REQUIREMENTS ===
Summary: {summary}

**AVAILABLE LABELS (YOU MUST ONLY CHOOSE FROM EXACTLY THESE):**
{available_labels}

Categories to Label Details:
{cat_text}

Allowed Senders/Domains: {allowed}
Blocked Senders/Domains: {blocked}
Global Keywords to Keep: {global_kw}

=== EMAIL TO ANALYZE ===
Subject: {email.get("subject", "(No Subject)")}
From: {email.get("sender", "unknown")}
Date: {email.get("date", "")}
Preview: {email.get("snippet", "")}

Body:
{email.get("body", "(No body)")[:2500]}
""".strip()

    state["context_str"] = context
    return state

def analyze_email(state: EmailState) -> EmailState:
    context = state.get("context_str", "(No context provided)")

    try:
        llm = ChatOpenAI(
            model=current_app.config["OPENAI_MODEL"],
            api_key=current_app.config["OPENAI_API_KEY"],
            temperature=0,
            response_format={"type": "json_object"},
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=context),
        ]

        response = llm.invoke(messages)
        result = json.loads(response.content)

        state["action"] = result.get("action", "keep")
        state["reasoning"] = result.get("reasoning", "")

    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        state["action"] = "keep"
        state["reasoning"] = f"AI analysis failed, defaulting to keep. Error: {str(e)}"
        state["error"] = str(e)

    return state

def execute_action(state: EmailState) -> EmailState:
    from app.gmail_service import trash_email, spam_email, get_or_create_label, apply_label

    action = state.get("action", "keep")
    email_id = state["email"]["id"]
    service = state["gmail_service"]

    try:
        if action == "delete":
            trash_email(service, email_id)
            logger.info(f"Trashed email {email_id}")

        elif action.startswith("label:"):
            raw_label = action.split(":", 1)[1]
            label_name = raw_label.strip(" \"'[](){}<>")
            
            if label_name:
                label_id = get_or_create_label(service, label_name)
                apply_label(service, email_id, label_id)
                logger.info(f"Labeled email {email_id} as '{label_name}'")
            else:
                logger.info(f"Keeping email {email_id} (empty label name parsed)")

        else:
            logger.info(f"Keeping email {email_id} as-is")

    except Exception as e:
        logger.error(f"Gmail action failed for email {email_id}: {e}")
        state["error"] = str(e)

    return state

def create_email_agent():
    graph = StateGraph(EmailState)

    graph.add_node("prepare_context", prepare_context)
    graph.add_node("analyze_email", analyze_email)
    graph.add_node("execute_action", execute_action)

    graph.set_entry_point("prepare_context")
    graph.add_edge("prepare_context", "analyze_email")
    graph.add_edge("analyze_email", "execute_action")
    graph.add_edge("execute_action", END)

    return graph.compile()

def analyze_and_act(email: dict, requirements: dict, gmail_service) -> dict:
    agent = create_email_agent()

    initial_state: EmailState = {
        "email": email,
        "requirements": requirements,
        "gmail_service": gmail_service,
        "context_str": "",
        "action": None,
        "reasoning": None,
        "error": None,
    }

    final_state = agent.invoke(initial_state)
    return {
        "action": final_state.get("action", "keep"),
        "reasoning": final_state.get("reasoning", ""),
        "error": final_state.get("error"),
    }
