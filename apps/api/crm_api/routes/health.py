"""Health check endpoints."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["health"])

_MANAGED_MARKER = "anyjames-managed-remote-ci"


@lru_cache
def _repo_root() -> Path:
    """Resolve monorepo root locally or fall back to the API app root in Docker."""
    start = Path(__file__).resolve()
    for parent in start.parents:
        if (parent / ".james" / "platform.json").is_file():
            return parent
    return start.parents[2]


def _required_james_paths() -> tuple[Path, ...]:
    james_root = _repo_root() / ".james"
    return (
        james_root / "README.md",
        james_root / "platform.json",
        james_root / "state" / ".gitkeep",
        james_root / "audit" / ".gitkeep",
        james_root / "tooling" / "ruff.toml",
        james_root / "tooling" / "lint.json",
    )


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe — confirms the CRM API process is running."""
    return {"status": "ok", "service": "crm-api"}


def _validate_james_bootstrap() -> dict[str, object]:
    repo_root = _repo_root()
    platform_json = repo_root / ".james" / "platform.json"
    remote_ci_workflow = repo_root / ".github" / "workflows" / "anyjames-remote-ci.yml"
    required_paths = _required_james_paths()

    missing = [
        str(path.relative_to(repo_root))
        for path in required_paths
        if not path.is_file()
    ]
    if missing:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "degraded",
                "reason": "missing_james_paths",
                "missing": missing,
            },
        )

    try:
        manifest = json.loads(platform_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "degraded",
                "reason": "invalid_platform_json",
                "error": str(exc),
            },
        ) from exc

    platform = manifest.get("platform")
    remote_ci = manifest.get("remote_ci") or {}
    if platform != "anyjames":
        raise HTTPException(
            status_code=503,
            detail={
                "status": "degraded",
                "reason": "unexpected_platform",
                "platform": platform,
            },
        )
    if remote_ci.get("provider") != "github":
        raise HTTPException(
            status_code=503,
            detail={
                "status": "degraded",
                "reason": "unexpected_provider",
                "provider": remote_ci.get("provider"),
            },
        )
    workflow_path = remote_ci.get("workflow_path")
    if workflow_path != ".github/workflows/anyjames-remote-ci.yml":
        raise HTTPException(
            status_code=503,
            detail={
                "status": "degraded",
                "reason": "unexpected_workflow_path",
                "workflow_path": workflow_path,
            },
        )

    if not remote_ci_workflow.is_file():
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "reason": "missing_workflow_file"},
        )
    workflow_content = remote_ci_workflow.read_text(encoding="utf-8")
    if _MANAGED_MARKER not in workflow_content:
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "reason": "missing_managed_marker"},
        )

    return {
        "status": "ok",
        "platform": platform,
        "remote_ci_provider": remote_ci.get("provider"),
        "workflow_path": workflow_path,
        "managed_marker": _MANAGED_MARKER,
    }


@router.get("/health/james-bootstrap")
async def james_bootstrap_health() -> dict[str, object]:
    """Readiness probe — validates AnyJames `.james` control-plane bootstrap."""
    return _validate_james_bootstrap()
