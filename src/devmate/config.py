from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomllib


@dataclass(frozen=True)
class ChatModelConfig:
    provider: str
    base_url: str
    api_key: str
    model_name: str


@dataclass(frozen=True)
class EmbeddingModelConfig:
    base_url: str
    api_key: str
    model_name: str


@dataclass(frozen=True)
class ModelConfig:
    chat: ChatModelConfig
    embedding: EmbeddingModelConfig


@dataclass(frozen=True)
class SearchConfig:
    tavily_api_key: str


@dataclass(frozen=True)
class LangSmithConfig:
    langchain_tracing_v2: bool
    langchain_api_key: str


@dataclass(frozen=True)
class SkillsConfig:
    skills_dir: str


@dataclass(frozen=True)
class MCPConfig:
    host: str
    port: int
    path: str
    url: str
    server_name: str


@dataclass(frozen=True)
class QdrantConfig:
    url: str
    collection_name: str
    vector_size: int
    prefer_grpc: bool = False


@dataclass(frozen=True)
class RuntimeConfig:
    workspace_dir: str


@dataclass(frozen=True)
class AppConfig:
    model: ModelConfig
    search: SearchConfig
    langsmith: LangSmithConfig
    skills: SkillsConfig
    mcp: MCPConfig
    qdrant: QdrantConfig
    app: RuntimeConfig


class ConfigError(RuntimeError):
    pass


def _require(data: dict[str, Any], key: str) -> Any:
    if key not in data or data[key] in (None, ""):
        raise ConfigError(f"Missing required config key: {key}")
    return data[key]


def load_config(path: str | Path = "config.toml") -> AppConfig:
    config_path = Path(path)
    raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError("Invalid config.toml format")

    model_raw = raw.get("model") or {}
    search_raw = raw.get("search") or {}
    langsmith_raw = raw.get("langsmith") or {}
    skills_raw = raw.get("skills") or {}
    mcp_raw = raw.get("mcp") or {}
    qdrant_raw = raw.get("qdrant") or {}
    app_raw = raw.get("app") or {}

    # Support both formats:
    # 1) New format:
    #    [model.chat] + [model.embedding]
    # 2) Legacy format:
    #    [model] ai_base_url/api_key/model_name/embedding_model_name
    if (
        isinstance(model_raw, dict)
        and "chat" in model_raw
        and "embedding" in model_raw
    ):
        chat_raw = model_raw.get("chat") or {}
        embedding_raw = model_raw.get("embedding") or {}
        model = ModelConfig(
            chat=ChatModelConfig(
                provider=_require(chat_raw, "provider"),
                base_url=_require(chat_raw, "base_url"),
                api_key=_require(chat_raw, "api_key"),
                model_name=_require(chat_raw, "model_name"),
            ),
            embedding=EmbeddingModelConfig(
                base_url=_require(embedding_raw, "base_url"),
                api_key=_require(embedding_raw, "api_key"),
                model_name=_require(embedding_raw, "model_name"),
            ),
        )
    else:
        model = ModelConfig(
            chat=ChatModelConfig(
                provider=model_raw.get("provider", "openai"),
                base_url=_require(model_raw, "ai_base_url"),
                api_key=_require(model_raw, "api_key"),
                model_name=_require(model_raw, "model_name"),
            ),
            embedding=EmbeddingModelConfig(
                base_url=_require(model_raw, "ai_base_url"),
                api_key=_require(model_raw, "api_key"),
                model_name=_require(model_raw, "embedding_model_name"),
            ),
        )
    search = SearchConfig(
        tavily_api_key=_require(search_raw, "tavily_api_key"),
    )
    langsmith = LangSmithConfig(
        langchain_tracing_v2=bool(
            langsmith_raw.get("langchain_tracing_v2", False)
        ),
        langchain_api_key=_require(langsmith_raw, "langchain_api_key"),
    )
    skills = SkillsConfig(skills_dir=_require(skills_raw, "skills_dir"))
    mcp = MCPConfig(
        host=_require(mcp_raw, "host"),
        port=int(_require(mcp_raw, "port")),
        path=_require(mcp_raw, "path"),
        url=_require(mcp_raw, "url"),
        server_name=_require(mcp_raw, "server_name"),
    )
    qdrant = QdrantConfig(
        url=_require(qdrant_raw, "url"),
        collection_name=_require(qdrant_raw, "collection_name"),
        vector_size=int(_require(qdrant_raw, "vector_size")),
        prefer_grpc=bool(qdrant_raw.get("prefer_grpc", False)),
    )
    app = RuntimeConfig(workspace_dir=_require(app_raw, "workspace_dir"))

    return AppConfig(
        model=model,
        search=search,
        langsmith=langsmith,
        skills=skills,
        mcp=mcp,
        qdrant=qdrant,
        app=app,
    )

