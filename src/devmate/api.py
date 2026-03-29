from __future__ import annotations

import logging

from fastapi import FastAPI
from pydantic import BaseModel, Field

from devmate.agent import run_agent_once
from devmate.config import AppConfig, load_config
from devmate.logging_setup import configure_logging

logger = logging.getLogger(__name__)


class RunRequest(BaseModel):
    prompt: str = Field(..., description="User request for DevMate.")


def create_app(config: AppConfig) -> FastAPI:
    app = FastAPI(title="DevMate")

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"ok": True}

    @app.post("/run")
    async def run(req: RunRequest) -> dict:
        result = await run_agent_once(config, req.prompt)
        return result

    return app


def main() -> None:
    configure_logging()
    config = load_config()
    app = create_app(config)
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
