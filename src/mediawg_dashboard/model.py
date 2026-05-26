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


STAGE_DESCRIPTIONS: dict[str, str] = {
    "ED": "Editor's Draft — living document in GitHub; not yet published to /TR/.",
    "FPWD": "First Public Working Draft — first /TR/ publication; triggers IPR commitments and horizontal review eligibility.",
    "WD": "Working Draft — periodic /TR/ publications as the spec evolves.",
    "CR": "Candidate Recommendation — feature-complete; calls for implementations.",
    "CR-snapshot": "Candidate Recommendation Snapshot — formal publication that triggers wide review.",
    "CR-draft": "Candidate Recommendation Draft — continuous publication between CR Snapshots.",
    "PR": "Proposed Recommendation — implementations exist; AC reviewing for final approval.",
    "REC": "Recommendation — final W3C standard.",
    "NOTE": "Group Note — non-normative deliverable.",
    "Discontinued": "Discontinued — work abandoned or superseded.",
    "unknown": "Stage could not be determined from W3C API.",
}


class SpecMeta(BaseModel):
    shortname: str
    title: str
    repo: str
    w3c_shortname: str
    tr_url: str | None = None
    wpt_path: str | None = None


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
