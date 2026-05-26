from datetime import date
from typing import Literal

from pydantic import BaseModel

Stage = Literal[
    "ED",
    "FPWD",
    "WD",
    "CR-snapshot",
    "CR-draft",
    "CR",
    "PR",
    "REC",
    "NOTE",
    "Discontinued",
    "unknown",
]


class SpecMeta(BaseModel):
    shortname: str
    title: str
    repo: str
    w3c_shortname: str
    tr_url: str | None = None


class SpecStatus(BaseModel):
    stage: Stage
    last_tr_publication: date | None = None
    ed_url: str | None = None


class RepoStats(BaseModel):
    open_issues_count: int
    open_prs_count: int
    oldest_open_issue_age_days: int | None = None


class Spec(BaseModel):
    meta: SpecMeta
    status: SpecStatus
    stats: RepoStats
