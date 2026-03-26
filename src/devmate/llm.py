from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_deepseek import ChatDeepSeek

from devmate.config import AppConfig


def make_chat_model(config: AppConfig) -> BaseChatModel:
    provider = config.model.chat.provider.lower().strip()
    if provider == "openai":
        # ChatOpenAI supports `base_url` for OpenAI-compatible endpoints.
        return ChatOpenAI(
            model=config.model.chat.model_name,
            api_key=config.model.chat.api_key,
            base_url=config.model.chat.base_url,
            temperature=0,
        )

    if provider == "deepseek":
        # ChatDeepSeek accepts `api_base` (alias `base_url`).
        return ChatDeepSeek(
            model=config.model.chat.model_name,
            api_key=config.model.chat.api_key,
            api_base=config.model.chat.base_url,
            temperature=0,
        )

    raise ValueError(
        "Unsupported model provider: " + config.model.chat.provider
    )


def make_embeddings(config: AppConfig) -> OpenAIEmbeddings:
    # DeepSeek's embeddings API is OpenAI-compatible, so we can reuse
    # OpenAIEmbeddings by pointing `base_url` to the configured endpoint.
    return OpenAIEmbeddings(
        model=config.model.embedding.model_name,
        api_key=config.model.embedding.api_key,
        base_url=config.model.embedding.base_url,
    )

