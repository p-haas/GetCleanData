# app/chat.py
from typing import List, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
)
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory

from .config import settings
from .db import get_mongo_client

# LLM global
LLM: ChatAnthropic | None = None


def init_llm():
    global LLM
    if LLM is not None:
        return

    LLM = ChatAnthropic(
        model=settings.claude_model,
        temperature=0.2,
        api_key=settings.anthropic_api_key,
    )


def get_chat_history(session_id: str) -> MongoDBChatMessageHistory:
    client = get_mongo_client()
        
    return MongoDBChatMessageHistory(
        connection_string=settings.mongodb_uri,           # 👈 IMPORTANT
        session_id=session_id,
        database_name=settings.mongodb_db_name,
        collection_name=settings.mongodb_collection_name,
    )


def chat_with_user(
    session_id: str,
    user_message: str,
    excel_context: Optional[str] = None,
) -> str:
    """
    Conversation avec l'utilisateur, avec éventuel contexte issu d'un Excel.

    - Récupère l'historique dans MongoDB
    - Ajoute un message système
    - Ajoute le contexte Excel comme message système supplémentaire
    - Appelle Claude
    - Enregistre la nouvelle interaction dans MongoDB
    """

    if LLM is None:
        raise RuntimeError("LLM not initialized; call init_llm() first.")

    history = get_chat_history(session_id)

    messages: List[BaseMessage] = []

    # Build a single system message, optionally including Excel/dataset context
    system_content = (
        "You are a helpful assistant specialized in data quality checks and error detection "
        "for tabular datasets (for example, data extracted from Excel or CSV files). "
        "When the user provides you with tabular data or an error report, use it as your primary "
        "source of truth to answer precisely. "
        "If some information is not present in the data or in the error report, clearly explain "
        "that it is missing instead of inventing values. "
        "Always help the user understand what is wrong in the dataset, how to interpret the errors, "
        "and suggest concrete steps to fix data issues."
    )

    if excel_context:
        system_content += (
            "\n\nHere is tabular context and an error report provided by the user "
            "from a dataset (e.g., Excel/CSV):\n"
            f"{excel_context}"
        )

    # ✅ Un seul SystemMessage, en première position
    messages.append(SystemMessage(content=system_content))

    # ✅ Puis l'historique
    messages.extend(history.messages)

    # ✅ Puis le nouveau message utilisateur
    messages.append(HumanMessage(content=user_message))

    # Appel du LLM
    ai_msg: AIMessage = LLM.invoke(messages)

    # Sauvegarder dans l'historique
    history.add_user_message(user_message)
    history.add_ai_message(ai_msg.content)

    return ai_msg.content
