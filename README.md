## DevMate

DevMate is an AI coding assistant that can:
- Use MCP search via **Streamable HTTP**
- Use local-document RAG (Qdrant vector DB)
- Use Agent Skills (skills directory)
- Generate multi-file code outputs

### Local quickstart

1. Configure `config.toml` (place your API keys).
2. Create and install dependencies with `uv`.
3. Start Qdrant and the MCP server with Docker Compose:

```bash
docker compose up -d
docker compose up devmate-mcp-search
```

4. In another terminal, ingest local docs into Qdrant:

```bash
uv run devmate-rag-ingest
```

5. Run the agent:

```bash
uv run devmate --prompt "我想构建一个展示附近徒步路线的网站项目。"
```
