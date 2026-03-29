from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from langchain_text_splitters import RecursiveCharacterTextSplitter

from devmate.config import AppConfig, load_config
from devmate.llm import make_embeddings

logger = logging.getLogger(__name__)


def _iter_doc_texts(docs_dir: str | Path) -> list[tuple[str, str]]:
    base = Path(docs_dir)
    md_files = sorted(base.glob("**/*.md"))
    out: list[tuple[str, str]] = []
    for file_path in md_files:
        text = file_path.read_text(encoding="utf-8")
        out.append((file_path.name, text))
    return out


def make_qdrant_client(config: AppConfig) -> QdrantClient:
    return QdrantClient(
        url=config.qdrant.url,
        prefer_grpc=config.qdrant.prefer_grpc,
    )


def _try_get_collection_dim(qdrant: QdrantClient, name: str) -> int | None:
    try:
        collection = qdrant.get_collection(name)
    except Exception:  # noqa: BLE001 - qdrant throws when not found
        return None

    params = getattr(getattr(collection, "config", None), "params", None)
    if params is None:
        return None

    vectors = getattr(params, "vectors", None)
    size = getattr(vectors, "size", None)
    if isinstance(size, int):
        return size
    return None


def ensure_collection(
    qdrant: QdrantClient,
    config: AppConfig,
    *,
    dim: int,
) -> None:
    try:
        existing_dim = _try_get_collection_dim(
            qdrant,
            config.qdrant.collection_name,
        )
        if existing_dim is not None and existing_dim == dim:
            return
    except Exception:  # noqa: BLE001 - qdrant throws when not found
        return

    qdrant.recreate_collection(
        collection_name=config.qdrant.collection_name,
        vectors_config=qmodels.VectorParams(
            size=dim,
            distance=qmodels.Distance.COSINE,
        ),
    )


def ingest_docs(config: AppConfig, docs_dir: str | Path = "docs") -> int:
    qdrant = make_qdrant_client(config)
    embeddings = make_embeddings(config)
    # Determine vector dimension from the embedding model output.
    # This avoids mismatches when using non-default embedding providers.
    dim = len(embeddings.embed_query("dimension-check"))
    ensure_collection(qdrant, config, dim=dim)

    doc_texts = _iter_doc_texts(docs_dir)
    if not doc_texts:
        logger.warning("No markdown docs found in docs dir: %s", docs_dir)
        return 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""],
    )

    points: list[qmodels.PointStruct] = []
    next_id = 0
    for source_name, raw_text in doc_texts:
        chunks = splitter.split_text(raw_text)
        for chunk_idx, chunk in enumerate(chunks):
            points.append(
                qmodels.PointStruct(
                    id=next_id,
                    vector=embeddings.embed_query(chunk),
                    payload={
                        "text": chunk,
                        "source": source_name,
                        "chunk_index": chunk_idx,
                    },
                )
            )
            next_id += 1

    qdrant.upsert(
        collection_name=config.qdrant.collection_name,
        points=points,
    )
    return len(points)


def count_points(config: AppConfig) -> int:
    qdrant = make_qdrant_client(config)
    try:
        return int(qdrant.count(config.qdrant.collection_name).count)
    except Exception:  # noqa: BLE001 - treat missing collection as empty
        return 0


def maybe_ingest(config: AppConfig, docs_dir: str | Path = "docs") -> None:
    if count_points(config) > 0:
        return
    added = ingest_docs(config, docs_dir=docs_dir)
    logger.info("Ingested %d chunks into Qdrant", added)


def search_knowledge_base(
    config: AppConfig,
    query: str,
    top_k: int = 4,
) -> list[dict[str, Any]]:
    """Search the Qdrant collection for documents similar to the query."""
    try:
        qdrant = make_qdrant_client(config)
        embeddings = make_embeddings(config)
        query_vec = embeddings.embed_query(query)

        # 兼容不同 Qdrant 客户端版本：
        # - 新版本常用 query_points
        # - 部分版本提供 search / search_points
        if hasattr(qdrant, "query_points"):
            points_result = qdrant.query_points(
                collection_name=config.qdrant.collection_name,
                query=query_vec,
                limit=top_k,
                with_payload=True,
            )
            hits = getattr(points_result, "points", points_result)
        elif hasattr(qdrant, "search"):
            hits = qdrant.search(
                collection_name=config.qdrant.collection_name,
                query_vector=query_vec,
                limit=top_k,
                with_payload=True,
            )
        elif hasattr(qdrant, "search_points"):
            hits = qdrant.search_points(
                collection_name=config.qdrant.collection_name,
                vector=query_vec,
                limit=top_k,
                with_payload=True,
            )
        else:
            logger.error("Qdrant client has no search method")
            return []
    except Exception as e:
        logger.exception(f"RAG search failed: {e}")
        return []

    results: list[dict[str, Any]] = []
    for hit in hits:
        payload = getattr(hit, "payload", None) or {}
        results.append(
            {
                "text": payload.get("text"),
                "source": payload.get("source"),
                "chunk_index": payload.get("chunk_index"),
                "score": getattr(hit, "score", None),
            }
        )
    return results


def ingest_main() -> None:
    config = load_config()
    added = ingest_docs(config, docs_dir="docs")
    logger.info("RAG ingest finished, chunks=%d", added)


if __name__ == "__main__":
    ingest_main()
