"""Health check endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["health"])

_REPO_ROOT = Path(__file__).resolve().parents[4]
_JAMES_ROOT = _REPO_ROOT / ".james"
_PLATFORM_JSON = _JAMES_ROOT / "platform.json"
_REMOTE_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "anyjames-remote-ci.yml"
_MANAGED_MARKER = "anyjames-managed-remote-ci"

_REQUIRED_JAMES_PATHS = (
    _JAMES_ROOT / "README.md",
    _PLATFORM_JSON,
    _JAMES_ROOT / "state" / ".gitkeep",
    _JAMES_ROOT / "audit" / ".gitkeep",
    _JAMES_ROOT / "tooling" / "ruff.toml",
    _JAMES_ROOT / "tooling" / "lint.json",
)


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe — confirms the CRM API process is running."""
    return {"status": "ok", "service": "crm-api"}


def _validate_james_bootstrap() -> dict[str, object]:
    missing = [
        str(path.relative_to(_REPO_ROOT)) for path in _REQUIRED_JAMES_PATHS if not path.is_file()
    ]
    if missing:
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "reason": "missing_james_paths", "missing": missing},
        )

    try:
        manifest = json.loads(_PLATFORM_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "reason": "invalid_platform_json", "error": str(exc)},
        ) from exc

    platform = manifest.get("platform")
    remote_ci = manifest.get("remote_ci") or {}
    if platform != "anyjames":
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "reason": "unexpected_platform", "platform": platform},
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

    if not _REMOTE_CI_WORKFLOW.is_file():
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "reason": "missing_workflow_file"},
        )
    workflow_content = _REMOTE_CI_WORKFLOW.read_text(encoding="utf-8")
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
