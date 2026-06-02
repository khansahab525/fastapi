import uuid
from typing import Any

from langgraph.checkpoint.memory import MemorySaver

from app.agent.graph import build_cargo_agent, extract_agent_reply
from app.auth.context import get_current_user, get_pending_vehicle
from app.config import settings

_checkpointer = MemorySaver()
_agent = None


class ChatConfigurationError(Exception):
    """Raised when required chat service configuration is missing."""


def _validate_config() -> None:
    from app.config import PROJECT_ROOT, load_env_file

    load_env_file()
    env_file = load_env_file()
    env_hint = (
        f"Loaded from {env_file}" if env_file else f"No .env file found at {PROJECT_ROOT / '.env'}"
    )

    if not settings.openai_api_key:
        raise ChatConfigurationError(
            f"OPENAI_API_KEY is not set. Add it to {PROJECT_ROOT / '.env'}. {env_hint}"
        )
    if not settings.odoo_api_key:
        raise ChatConfigurationError(
            f"ODOO_API_KEY is not set. Add it to {PROJECT_ROOT / '.env'}. {env_hint}"
        )


def _get_agent():
    global _agent
    _validate_config()
    if _agent is None:
        _agent = build_cargo_agent(checkpointer=_checkpointer)
    return _agent


def _user_context_prefix() -> str:
    parts = []
    user = get_current_user()
    if user:
        parts.append(
            f"[Logged-in Odoo user: user_id={user.get('user_id')}, "
            f"partner_id={user.get('partner_id')}, name={user.get('name')}, "
            f"mobile={user.get('mobile')}]"
        )
    pending = get_pending_vehicle()
    if pending:
        parts.append(
            f"[User just saved a new vehicle via the form: vehicle_id={pending.get('id')}, "
            f"name={pending.get('name')}. Use this vehicle_id for create_cargo_sale_order "
            f"unless the user picks a different saved vehicle.]"
        )
    if not parts:
        return ""
    return "\n".join(parts) + "\n"


def _meta_intent_prefix(message: str) -> str:
    text = (message or "").strip().lower()
    if not text:
        return ""
    meta_phrases = (
        "what can you do",
        "help",
        "capabilities",
        "menu",
        "services",
        "options",
        "ماذا يمكنك",
        "ايش تقدر",
        "وش تقدر",
        "مساعدة",
    )
    if any(phrase in text for phrase in meta_phrases):
        return (
            "[Meta-intent override: User is asking about capabilities/help. "
            "Do NOT continue any previous order workflow state. "
            "Do NOT ask for vehicle/location/agreement in this turn. "
            "Reply with concise capability options and ask what the user wants next.]\n"
        )
    return ""


class ChatService:
    def __init__(self) -> None:
        from app.services.odoo_client import OdooClient

        self.odoo = OdooClient()

    async def chat(self, message: str, session_id: str | None = None) -> dict[str, Any]:
        agent = _get_agent()
        thread_id = session_id or str(uuid.uuid4())
        full_message = _meta_intent_prefix(message) + _user_context_prefix() + message

        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": full_message}]},
            config={"configurable": {"thread_id": thread_id}},
        )

        reply = extract_agent_reply(result["messages"])
        if not reply:
            reply = "I could not generate a response. Please try again."

        return {
            "reply": reply,
            "session_id": thread_id,
            "source": "langgraph",
        }
