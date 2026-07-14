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
    charter_target: str | None = None  # neutral config fact, e.g. "CR Q4 2025"
    bcd_path: str | None = None  # MDN browser-compat-data key, e.g. api.MediaSource
    hr_shortname: str | None = None  # horizontal-issue-tracker shortname (defaults to shortname)


class SpecStatus(BaseModel):
    stage: Stage
    last_tr_publication: date | None = None
    ed_url: str | None = None


class RepoStats(BaseModel):
    open_issues_count: int
    open_prs_count: int
    oldest_open_issue_age_days: int | None = None


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
    """Shipping reality, presented evenly across engines (alphabetical).

    Support (chrome/firefox/safari + versions + mdn_url) comes from MDN
    browser-compat-data; WPT numbers come from wpt.fyi experimental (nightly)
    runs, both all-engines and per-engine (passes, total).
    """

    chrome: SupportState = "unknown"
    firefox: SupportState = "unknown"
    safari: SupportState = "unknown"
    chrome_version: str | None = None
    firefox_version: str | None = None
    safari_version: str | None = None
    mdn_url: str | None = None
    all_engines_wpt: float | None = None  # 0..100
    wpt_test_count: int | None = None
    wpt_chrome: tuple[int, int] | None = None  # (passes, total), nightly
    wpt_firefox: tuple[int, int] | None = None
    wpt_safari: tuple[int, int] | None = None
    interop_focus_year: int | None = None


class EngineRow(BaseModel):
    """One engine's interop line for the detail panel."""

    name: str  # Chrome / Firefox / Safari
    state: SupportState
    glyph: str
    version: str | None = None
    wpt: str | None = None  # "14/40" or None
    href: str | None = None  # MDN compat anchor


class SpecHealth(BaseModel):
    """Activity/health inputs for the Pulse signal (populated by fetchers)."""

    days_since_activity: int | None = None
    oldest_blocking_issue_days: int | None = None
    charter_target: str | None = None  # e.g. "CR Q1 2026"
    charter_overdue: bool = False
    backlog_trend: str | None = None  # rising / falling / flat (from snapshots)


class Blocker(BaseModel):
    label: str
    state: BlockerState
    kind: str = ""  # wide_review / horizontal / cr_blocking / impl_report / ac_review


class Pulse(BaseModel):
    tier: PulseTier
    reason: str = ""


class Spec(BaseModel):
    meta: SpecMeta
    status: SpecStatus
    stats: RepoStats
    milestones: SpecMilestones = Field(default_factory=SpecMilestones)
    interop: InteropStatus = Field(default_factory=InteropStatus)
    health: SpecHealth = Field(default_factory=SpecHealth)


class SpecView(BaseModel):
    """Everything the template renders for one spec row + its expand panel.

    A typed payload (not a bare dict) so template access is schema-checked and
    can grow safely across P3–P5.
    """

    spec: Spec
    next_gate: str | None
    readiness: str | None  # ready / blocked / unknown (None if terminal)
    readiness_glyph: str | None  # colour+shape mark for the readiness
    blocker_rows: list[tuple[str, str, str | None, str, str]]  # (glyph, label, href, state, kind)
    horizontal_rows: list[tuple[str, str, str]]  # (name, state, href) — nested under the horizontal blocker
    engine_rows: list[EngineRow]
    wpt_href: str | None
    needs_resolution_href: str  # open *-needs-resolution issues for the repo
    stage_age_days: int | None
    stage_age_label: str
    pulse: Pulse | None
