from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

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


# --- Expandable-view types (all vendor-neutral) ---

SupportState = Literal["shipped", "partial", "none", "unknown"]
ReviewState = Literal["resolved", "open", "requested", "na", "unknown"]
BlockerState = Literal["done", "open", "partial", "unknown"]
PulseTier = Literal["on-track", "watch", "at-risk"]


class HorizontalReviews(BaseModel):
    """State of the 5 W3C horizontal reviews for a spec."""

    a11y: ReviewState = "unknown"
    i18n: ReviewState = "unknown"
    privacy: ReviewState = "unknown"
    security: ReviewState = "unknown"
    tag: ReviewState = "unknown"


class SpecMilestones(BaseModel):
    """Process facts that gate the next Rec-track transition.

    Fields are optional/unknown by default; fetchers or config populate them.
    """

    wide_review_complete: bool | None = None
    horizontal: HorizontalReviews = Field(default_factory=HorizontalReviews)
    impl_report_ready: bool | None = None
    ac_review_done: bool | None = None
    cr_blocking_issues_open: int | None = None


class InteropStatus(BaseModel):
    """Shipping reality, presented evenly across engines (alphabetical)."""

    chrome: SupportState = "unknown"
    firefox: SupportState = "unknown"
    safari: SupportState = "unknown"
    all_engines_wpt: float | None = None  # 0..100
    wpt_test_count: int | None = None
    interop_focus_year: int | None = None


class Blocker(BaseModel):
    label: str
    state: BlockerState


class Pulse(BaseModel):
    tier: PulseTier
    reason: str = ""
