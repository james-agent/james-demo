"""Persistence helpers for q2_provision_runs."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ext.q2.models.provision_run import Q2ProvisionRun


class ProvisionRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, run: Q2ProvisionRun) -> Q2ProvisionRun:
        self.session.add(run)
        self.session.flush()
        return run

    def get(self, run_id: str) -> Q2ProvisionRun | None:
        return self.session.get(Q2ProvisionRun, run_id)

    def save(self, run: Q2ProvisionRun) -> Q2ProvisionRun:
        self.session.add(run)
        self.session.flush()
        return run
