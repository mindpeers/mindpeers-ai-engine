"""
Clinical outcome label generation — CRS spec §4.3.

Offline training pipeline only. Labels are never attached to production inference rows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional, Sequence


LABEL_VERSION = "label_v2.0.0"


class LabelConfidence(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


class CensorReason(str, Enum):
    NO_FOLLOWUP = "no_followup_in_window"
    DROPOUT_BEFORE_WINDOW = "dropout_before_window"


@dataclass(frozen=True)
class LabelConfig:
    """Thresholds — clinical sign-off required before production use."""

    core_om_mcid_total: float = 5.0
    core_om_mcid_subscale_norm: float = 0.10
    gad7_mcid: float = 4.0
    core_om_risk_relapse_threshold: float = 0.70
    core_om_risk_increase_threshold: float = 0.15
    assessment_horizon_days: int = 30
    assessment_window_min_days: int = 21
    assessment_window_max_days: int = 45
    dropout_horizon_days: int = 60
    dropout_inactive_days: int = 30
    engagement_loss_horizon_days: int = 14
    engagement_loss_relative_drop: float = 0.50
    label_version: str = LABEL_VERSION


@dataclass(frozen=True)
class CoreOmSnapshot:
    """CORE-OM at a point in time."""

    occurred_at: date
    total_score: float
    wellbeing_norm: float
    problems_norm: float
    functioning_norm: float
    risk_norm: float
    assessment_id: Optional[str] = None


@dataclass(frozen=True)
class Gad7Snapshot:
    occurred_at: date
    total_score: float
    assessment_id: Optional[str] = None


@dataclass
class LabelResult:
    user_id: str
    snapshot_date: date
    recovery_label: Optional[int]
    relapse_label: Optional[int]
    dropout_label: int
    engagement_loss_label: int
    label_version: str
    label_confidence: Optional[LabelConfidence] = None
    label_censored_reason: Optional[CensorReason] = None
    relapse_criteria_met: list[str] = field(default_factory=list)
    recovery_criteria_met: list[str] = field(default_factory=list)


def _days_from_snapshot(occurred: date, snapshot: date) -> int:
    return (occurred - snapshot).days


def select_nearest_in_window(
    records: Sequence,
    snapshot_date: date,
    window_min_days: int,
    window_max_days: int,
    horizon_days: int,
    date_attr: str = "occurred_at",
) -> Optional[object]:
    """Return record nearest to T+horizon within [T+min, T+max], or None."""
    target = snapshot_date + timedelta(days=horizon_days)
    candidates: list[tuple[int, object]] = []
    for record in records:
        occurred: date = getattr(record, date_attr)
        offset = _days_from_snapshot(occurred, snapshot_date)
        if window_min_days <= offset <= window_max_days:
            candidates.append((abs((occurred - target).days), record))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def relapse_criteria_met(
    baseline: CoreOmSnapshot,
    followup: CoreOmSnapshot,
    config: LabelConfig,
    gad7_baseline: Optional[Gad7Snapshot] = None,
    gad7_followup: Optional[Gad7Snapshot] = None,
    core_om_absent: bool = False,
) -> list[str]:
    """Return list of criterion IDs that fired (L1–L5)."""
    met: list[str] = []
    total_delta = followup.total_score - baseline.total_score
    if total_delta >= config.core_om_mcid_total:
        met.append("L1")

    problems_delta = followup.problems_norm - baseline.problems_norm
    if problems_delta >= config.core_om_mcid_subscale_norm:
        met.append("L2")

    if followup.risk_norm >= config.core_om_risk_relapse_threshold:
        met.append("L3")

    risk_delta = followup.risk_norm - baseline.risk_norm
    if risk_delta >= config.core_om_risk_increase_threshold:
        met.append("L4")

    if core_om_absent and gad7_baseline and gad7_followup:
        gad7_delta = gad7_followup.total_score - gad7_baseline.total_score
        if gad7_delta >= config.gad7_mcid:
            met.append("L5")

    return met


def recovery_criteria_met(
    baseline: CoreOmSnapshot,
    followup: CoreOmSnapshot,
    config: LabelConfig,
) -> list[str]:
    """Return list of criterion IDs that fired (R1–R4)."""
    met: list[str] = []
    total_delta = followup.total_score - baseline.total_score
    if total_delta <= -config.core_om_mcid_total:
        met.append("R1")

    if (followup.problems_norm - baseline.problems_norm) <= -config.core_om_mcid_subscale_norm:
        met.append("R2")

    if (followup.wellbeing_norm - baseline.wellbeing_norm) >= config.core_om_mcid_subscale_norm:
        met.append("R3")

    if (followup.functioning_norm - baseline.functioning_norm) >= config.core_om_mcid_subscale_norm:
        met.append("R4")

    return met


def recovery_via_gad7_confirmer(
    gad7_baseline: Gad7Snapshot,
    gad7_followup: Gad7Snapshot,
    mood_slope_7d_at_followup: Optional[float],
    config: LabelConfig,
) -> bool:
    """Secondary recovery path when CORE-OM follow-up is missing."""
    if mood_slope_7d_at_followup is None or mood_slope_7d_at_followup <= 0:
        return False
    gad7_delta = gad7_followup.total_score - gad7_baseline.total_score
    return gad7_delta <= -config.gad7_mcid


def compute_clinical_labels(
    user_id: str,
    snapshot_date: date,
    core_om_baseline: Optional[CoreOmSnapshot],
    core_om_history: Sequence[CoreOmSnapshot],
    config: LabelConfig | None = None,
    gad7_baseline: Optional[Gad7Snapshot] = None,
    gad7_history: Sequence[Gad7Snapshot] = (),
    mood_slope_7d_at_followup: Optional[float] = None,
    user_churned: bool = False,
) -> LabelResult:
    """
    Compute recovery_label and relapse_label with precedence (§4.3.9).

    Returns null clinical labels when censored (no valid follow-up).
    """
    cfg = config or LabelConfig()
    result = LabelResult(
        user_id=user_id,
        snapshot_date=snapshot_date,
        recovery_label=None,
        relapse_label=None,
        dropout_label=0,
        engagement_loss_label=0,
        label_version=cfg.label_version,
    )

    if user_churned:
        result.label_censored_reason = CensorReason.DROPOUT_BEFORE_WINDOW
        return result

    if core_om_baseline is None:
        gad7_base = gad7_baseline or _nearest_on_or_before(gad7_history, snapshot_date)
        gad7_follow = select_nearest_in_window(
            gad7_history,
            snapshot_date,
            cfg.assessment_window_min_days,
            cfg.assessment_window_max_days,
            cfg.assessment_horizon_days,
        )
        if gad7_base and gad7_follow and recovery_via_gad7_confirmer(
            gad7_base, gad7_follow, mood_slope_7d_at_followup, cfg
        ):
            result.recovery_label = 1
            result.relapse_label = 0
            result.label_confidence = LabelConfidence.SECONDARY
            return result
        result.label_censored_reason = CensorReason.NO_FOLLOWUP
        return result

    followup = select_nearest_in_window(
        [r for r in core_om_history if r.occurred_at > snapshot_date],
        snapshot_date,
        cfg.assessment_window_min_days,
        cfg.assessment_window_max_days,
        cfg.assessment_horizon_days,
    )

    if followup is None:
        gad7_base = gad7_baseline or _nearest_on_or_before(gad7_history, snapshot_date)
        gad7_follow = select_nearest_in_window(
            gad7_history,
            snapshot_date,
            cfg.assessment_window_min_days,
            cfg.assessment_window_max_days,
            cfg.assessment_horizon_days,
        )
        if gad7_base and gad7_follow and recovery_via_gad7_confirmer(
            gad7_base, gad7_follow, mood_slope_7d_at_followup, cfg
        ):
            result.recovery_label = 1
            result.relapse_label = 0
            result.label_confidence = LabelConfidence.SECONDARY
            return result
        result.label_censored_reason = CensorReason.NO_FOLLOWUP
        return result

    assert isinstance(followup, CoreOmSnapshot)
    relapse_met = relapse_criteria_met(core_om_baseline, followup, cfg)
    result.relapse_criteria_met = relapse_met

    if relapse_met:
        result.relapse_label = 1
        result.recovery_label = 0
        result.label_confidence = LabelConfidence.PRIMARY
        return result

    recovery_met = recovery_criteria_met(core_om_baseline, followup, cfg)
    result.recovery_criteria_met = recovery_met

    if recovery_met and followup.risk_norm < cfg.core_om_risk_relapse_threshold:
        result.recovery_label = 1
        result.relapse_label = 0
        result.label_confidence = LabelConfidence.PRIMARY
        return result

    result.recovery_label = 0
    result.relapse_label = 0
    result.label_confidence = LabelConfidence.PRIMARY
    return result


def compute_dropout_label(
    snapshot_date: date,
    config: LabelConfig | None = None,
    user_churned_at: Optional[date] = None,
    therapy_terminated: bool = False,
    max_consecutive_inactive_days: Optional[int] = None,
) -> int:
    """Program/business outcome — independent of clinical labels."""
    cfg = config or LabelConfig()
    if therapy_terminated:
        return 1
    if user_churned_at is not None:
        days = _days_from_snapshot(user_churned_at, snapshot_date)
        if 0 <= days <= cfg.dropout_horizon_days:
            return 1
    if max_consecutive_inactive_days is not None:
        if max_consecutive_inactive_days >= cfg.dropout_inactive_days:
            return 1
    return 0


def compute_engagement_loss_label(
    engagement_rate_at_t: float,
    engagement_rate_at_future: float,
    config: LabelConfig | None = None,
) -> int:
    cfg = config or LabelConfig()
    threshold = engagement_rate_at_t * (1.0 - cfg.engagement_loss_relative_drop)
    return 1 if engagement_rate_at_future <= threshold else 0


def compute_all_labels(
    user_id: str,
    snapshot_date: date,
    core_om_baseline: Optional[CoreOmSnapshot],
    core_om_history: Sequence[CoreOmSnapshot],
    config: LabelConfig | None = None,
    engagement_rate_at_t: Optional[float] = None,
    engagement_rate_at_future: Optional[float] = None,
    **clinical_kwargs: object,
) -> LabelResult:
    """Full label row for ml.training_labels."""
    result = compute_clinical_labels(
        user_id,
        snapshot_date,
        core_om_baseline,
        core_om_history,
        config,
        **clinical_kwargs,  # type: ignore[arg-type]
    )
    cfg = config or LabelConfig()
    result.dropout_label = compute_dropout_label(
        snapshot_date,
        cfg,
        user_churned_at=clinical_kwargs.get("user_churned_at"),  # type: ignore[arg-type]
        therapy_terminated=bool(clinical_kwargs.get("therapy_terminated", False)),
        max_consecutive_inactive_days=clinical_kwargs.get("max_consecutive_inactive_days"),  # type: ignore[arg-type]
    )
    if engagement_rate_at_t is not None and engagement_rate_at_future is not None:
        result.engagement_loss_label = compute_engagement_loss_label(
            engagement_rate_at_t,
            engagement_rate_at_future,
            cfg,
        )
    return result


def _nearest_on_or_before(
    records: Sequence,
    snapshot_date: date,
    date_attr: str = "occurred_at",
) -> Optional[object]:
    eligible = [r for r in records if getattr(r, date_attr) <= snapshot_date]
    if not eligible:
        return None
    return max(eligible, key=lambda r: getattr(r, date_attr))
