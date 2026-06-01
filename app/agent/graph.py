from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.agent.tools import get_cargo_tools
from app.config import settings

SYSTEM_PROMPT = """You are Albassami cargo assistant. You help customers and staff with
cargo sale order line status, residual (unpaid) amounts, delivery, payment, and trip information.

Rules:
- You MUST use the provided tools to fetch all cargo data from Odoo. Never answer from memory.
- For any lookup (reference, chassis, plate, mobile, customer, order), call the appropriate tool.
- If multiple lines match, list them briefly and ask the user to specify the reference.
- Present amounts with currency when available.
- Be concise and professional. Support English and Arabic when the user writes in Arabic.
- Never invent order references, amounts, or statuses.
"""


def build_cargo_agent(*, checkpointer: MemorySaver | None = None):
    """Build LangGraph ReAct agent with Odoo cargo tools."""
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )
    return create_react_agent(
        llm,
        get_cargo_tools(),
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer or MemorySaver(),
    )


def extract_agent_reply(messages: list) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            content = message.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = [
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                return "".join(parts).strip()
    return ""
