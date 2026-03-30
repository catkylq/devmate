from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from devmate.agent import run_agent_once
from devmate.config import AppConfig, load_config
from devmate.logging_setup import configure_logging
from devmate.skills_paths import project_root

logger = logging.getLogger(__name__)


class RunRequest(BaseModel):
    prompt: str = Field(..., description="User request for DevMate.")


class FileContent(BaseModel):
    path: str = Field(..., description="File path relative to workspace.")
    content: str = Field(..., description="File content.")


class FileCreateRequest(BaseModel):
    path: str = Field(..., description="File path relative to workspace.")
    content: str = Field(default="", description="File content.")


class FileUpdateRequest(BaseModel):
    path: str = Field(..., description="File path relative to workspace.")
    content: str = Field(..., description="New file content.")


class FileListResponse(BaseModel):
    files: list[str] = Field(default_factory=list)
    workspace: str


class FileResponse(BaseModel):
    path: str
    content: str
    workspace: str


def _get_workspace_root(config: AppConfig) -> Path:
    """Get the absolute workspace root directory."""
    pr = project_root()
    return (pr / config.app.workspace_dir).resolve()


def create_app(config: AppConfig) -> FastAPI:
    app = FastAPI(title="DevMate")
    workspace_root = _get_workspace_root(config)

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"ok": True}

    @app.get("/workspace")
    async def list_workspace() -> FileListResponse:
        """List all files in workspace directory."""
        if not workspace_root.exists():
            return FileListResponse(files=[], workspace=str(workspace_root))
        
        files = []
        for path in workspace_root.rglob("*"):
            if path.is_file():
                rel = path.relative_to(workspace_root).as_posix()
                files.append(rel)
        
        return FileListResponse(
            files=sorted(files),
            workspace=str(workspace_root)
        )

    @app.get("/workspace/{file_path:path}")
    async def read_file(file_path: str) -> FileResponse:
        """Read content of a specific file."""
        file_path = file_path.lstrip("/")
        full_path = workspace_root / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        if not full_path.is_file():
            raise HTTPException(status_code=400, detail=f"Not a file: {file_path}")
        
        try:
            content = full_path.read_text(encoding="utf-8")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
        
        return FileResponse(
            path=file_path,
            content=content,
            workspace=str(workspace_root)
        )

    @app.post("/workspace")
    async def create_file(req: FileCreateRequest) -> dict:
        """Create a new file in workspace."""
        full_path = workspace_root / req.path
        
        if full_path.exists():
            raise HTTPException(status_code=409, detail=f"File already exists: {req.path}")
        
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(req.content, encoding="utf-8")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create file: {str(e)}")
        
        return {"success": True, "path": req.path}

    @app.put("/workspace/{file_path:path}")
    async def update_file(file_path: str, req: FileUpdateRequest) -> dict:
        """Update an existing file in workspace."""
        file_path = file_path.lstrip("/")
        full_path = workspace_root / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        try:
            full_path.write_text(req.content, encoding="utf-8")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update file: {str(e)}")
        
        return {"success": True, "path": file_path}

    @app.delete("/workspace/{file_path:path}")
    async def delete_file(file_path: str) -> dict:
        """Delete a file from workspace."""
        file_path = file_path.lstrip("/")
        full_path = workspace_root / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        try:
            full_path.unlink()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
        
        return {"success": True, "path": file_path}

    @app.post("/run")
    async def run(req: RunRequest) -> dict:
        """Run the agent with the given prompt (non-streaming)."""
        result = await run_agent_once(config, req.prompt)
        return result

    @app.post("/run/stream")
    async def run_stream(req: RunRequest) -> StreamingResponse:
        """Run the agent with streaming output for real-time updates."""
        
        async def event_generator() -> AsyncIterator[str]:
            try:
                yield _sse_event("status", {"status": "starting", "message": "Initializing agent..."})
                
                # Use asyncio.to_thread to run sync agent in thread pool
                loop = asyncio.get_event_loop()
                
                # First, get workspace files before
                def get_before_files():
                    if not workspace_root.exists():
                        return set()
                    return {
                        path.relative_to(workspace_root).as_posix()
                        for path in workspace_root.rglob("*")
                        if path.is_file()
                    }
                
                before_files = await loop.run_in_executor(None, get_before_files)
                yield _sse_event("files_before", {"files": sorted(before_files)})
                yield _sse_event("status", {"status": "thinking", "message": "Agent is thinking..."})
                
                # Run agent and capture messages
                result = await run_agent_once(config, req.prompt)
                
                # Extract messages from result
                messages = []
                if "result" in result and hasattr(result["result"], "get"):
                    messages = result["result"].get("messages", [])
                
                for i, msg in enumerate(messages):
                    if isinstance(msg, dict):
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        if isinstance(content, list):
                            text_parts = [c.get("text", "") for c in content if isinstance(c, dict)]
                            content = "\n".join(text_parts)
                        
                        yield _sse_event("message", {
                            "index": i,
                            "role": role,
                            "content": content,
                            "type": "agent" if role != "user" else "user"
                        })
                    elif hasattr(msg, "content"):
                        content = msg.content
                        if isinstance(content, list):
                            text_parts = [c.text for c in content if hasattr(c, "text")]
                            content = "\n".join(text_parts)
                        yield _sse_event("message", {
                            "index": i,
                            "role": getattr(msg, "type", "unknown"),
                            "content": content,
                            "type": "agent"
                        })
                
                # Get workspace files after
                def get_after_files():
                    if not workspace_root.exists():
                        return set()
                    return {
                        path.relative_to(workspace_root).as_posix()
                        for path in workspace_root.rglob("*")
                        if path.is_file()
                    }
                
                after_files = await loop.run_in_executor(None, get_after_files)
                created_files = sorted(after_files - before_files)
                
                yield _sse_event("files_after", {
                    "files": sorted(after_files),
                    "created": created_files
                })
                
                yield _sse_event("status", {
                    "status": "completed",
                    "message": "Agent execution completed",
                    "created_files": created_files
                })
                
                if result.get("run_url"):
                    yield _sse_event("trace", {"url": result["run_url"]})
                
                if result.get("share_url"):
                    yield _sse_event("trace_share", {"url": result["share_url"]})
                
            except Exception as e:
                logger.exception("Error in stream")
                yield _sse_event("error", {"error": str(e), "message": "Agent execution failed"})
        
        return StreamingResponse(
            content=event_generator(),
            media_type="text/event-stream"
        )

    return app


def _sse_event(event_type: str, data: dict) -> str:
    """Create a Server-Sent Event string."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def main() -> None:
    configure_logging()
    config = load_config()
    app = create_app(config)
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
