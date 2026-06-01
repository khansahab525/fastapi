import uuid
from typing import Any

from langgraph.checkpoint.memory import MemorySaver

from app.agent.graph import build_cargo_agent, extract_agent_reply
from app.config import PROJECT_ROOT, load_env_file, settings

_checkpointer = MemorySaver()
_agent = None


class ChatConfigurationError(Exception):
    """Raised when required chat service configuration is missing."""


def _validate_config() -> None:
    env_file = load_env_file()
    env_hint = (
        f"Loaded from {env_file}" if env_file else f"No .env file found at {PROJECT_ROOT / '.env'}"
    )

    if not settings.openai_api_key:
        raise ChatConfigurationError(
            f"OPENAI_API_KEY is not set. Add it to {PROJECT_ROOT / '.env'} "
            f"(copy from .env.example). {env_hint}"
        )
    if not settings.odoo_api_key:
        raise ChatConfigurationError(
            f"ODOO_API_KEY is not set. Add it to {PROJECT_ROOT / '.env'} "
            f"(same value as ai_chatbot_api.api_key in Odoo). {env_hint}"
        )


def _get_agent():
    global _agent
    _validate_config()
    if _agent is None:
        _agent = build_cargo_agent(checkpointer=_checkpointer)
    return _agent


class ChatService:
    def __init__(self) -> None:
        from app.services.odoo_client import OdooClient

        self.odoo = OdooClient()

    async def chat(self, message: str, session_id: str | None = None) -> dict[str, Any]:
        agent = _get_agent()
        thread_id = session_id or str(uuid.uuid4())

        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": message}]},
            config={"configurable": {"thread_id": thread_id}},
        )

        reply = extract_agent_reply(result["messages"])
        if not reply:
            reply = "I could not generate a response. Please try again with a cargo line reference or search details."

        return {
            "reply": reply,
            "session_id": thread_id,
            "source": "langgraph",
        }
