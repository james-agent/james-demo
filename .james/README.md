# AnyJames platform control (`.james`)

This folder is managed by [AnyJames](https://anyjames.ai) for pipeline governance. It does not replace or modify your application source layout.

## Layout

- `platform.json` — remote CI and platform flags for James pipeline runs.
- `tooling/lint.json` — lint command manifest for Python (Ruff) and Node projects.
- `tooling/ruff.toml` — portable Ruff config; **keep in sync** with root `pyproject.toml` `[tool.ruff]` when rules change.
- `state/` and `audit/` — local engine state (gitignored runtime data when applicable).

Do not delete this folder while using AnyJames automated delivery.
