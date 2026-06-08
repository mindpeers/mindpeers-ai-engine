"""Build L2 feature row from staging daily series."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from features.compute import (
    cortisol_flag_v1_proxy,
    engagement_rate,
    maturity_stage,
    ols_slope,
    sleep_mood_coupled_decline,
    window_mean,
    window_std,
    withdrawal_flag,
)


@dataclass
class DailySeries:
    """One value per local_date, oldest first, ending at as_of_date."""

    dates: list[str]
    mood: list[Optional[float]] = field(default_factory=list)
    sleep_hours: list[Optional[float]] = field(default_factory=list)
    engagement_active: list[int] = field(default_factory=list)
    resting_hr: list[Optional[float]] = field(default_factory=list)


@dataclass
class FeatureRow:
    user_id: str
    as_of_date: str
    feature_version: str = "feat_v1.0.0"
    days_active: int = 0
    system_type: int = 1
    features: dict[str, Any] = field(default_factory=dict)
    missing_flags: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "as_of_date": self.as_of_date,
            "feature_version": self.feature_version,
            "days_active": self.days_active,
            "system_type": self.system_type,
            "data_maturity_stage": maturity_stage(self.days_active),
            **self.features,
            **{k: v for k, v in self.missing_flags.items()},
        }


def _set(row: FeatureRow, name: str, value: Any, min_required: bool = True) -> None:
    row.features[name] = value
    if value is None and min_required:
        row.missing_flags[f"{name}_missing"] = 1
    else:
        row.missing_flags[f"{name}_missing"] = 0


def compute_features(
    user_id: str,
    as_of_date: str,
    series: DailySeries,
    days_active: int = 45,
    system_type: int = 1,
) -> FeatureRow:
    """Compute v1 subset from daily series ending at as_of_date."""
    row = FeatureRow(user_id=user_id, as_of_date=as_of_date, days_active=days_active, system_type=system_type)

    mood_14 = series.mood[-14:] if len(series.mood) >= 14 else series.mood
    mood_7 = series.mood[-7:] if len(series.mood) >= 7 else series.mood
    sleep_7 = series.sleep_hours[-7:] if len(series.sleep_hours) >= 7 else series.sleep_hours
    sleep_14 = series.sleep_hours[-14:] if len(series.sleep_hours) >= 14 else series.sleep_hours
    eng_7 = series.engagement_active[-7:] if len(series.engagement_active) >= 7 else series.engagement_active

    _set(row, "mood_avg_14d", window_mean(mood_14, min_points=3))
    _set(row, "mood_slope_7d", ols_slope(mood_7))
    _set(row, "mood_volatility_14d", window_std(mood_14, min_points=5))
    _set(row, "sleep_avg_7d", window_mean(sleep_7, min_points=3))

    eng_rate = engagement_rate(eng_7) if eng_7 else 0.0
    _set(row, "engagement_rate_7d", eng_rate)
    _set(row, "engagement_slope_7d", ols_slope([float(x) for x in eng_7]) if eng_7 else None)
    _set(row, "withdrawal_flag", withdrawal_flag(eng_rate))

    low_sleep = sum(1 for h in sleep_14 if h is not None and h < 6)
    _set(row, "sleep_persistence_low_days", low_sleep)

    sleep_delta = None
    if days_active >= 30 and len(series.sleep_hours) >= 37:
        now_block = series.sleep_hours[-7:]
        base_block = series.sleep_hours[-37:-30]
        m_now = window_mean(now_block, 1)
        m_base = window_mean(base_block, 1)
        if m_now is not None and m_base is not None:
            sleep_delta = m_now - m_base
    _set(row, "sleep_delta_30d", sleep_delta)

    mood_slope = row.features.get("mood_slope_7d")
    _set(row, "sleep_mood_coupled_decline", sleep_mood_coupled_decline(sleep_delta, mood_slope))

    if system_type == 1 and days_active >= 30 and len(series.resting_hr) >= 37:
        hr_7 = series.resting_hr[-7:]
        hr_base = series.resting_hr[-37:-30]
        from features.compute import resting_hr_relative

        _set(row, "resting_hr_relative", resting_hr_relative(hr_7, hr_base))
    else:
        _set(row, "resting_hr_relative", None)

    vol = row.features.get("mood_volatility_14d")
    hr_rel = row.features.get("resting_hr_relative")
    _set(row, "cortisol_flag", cortisol_flag_v1_proxy(hr_rel, vol))

    populated = sum(1 for k, v in row.features.items() if v is not None and not k.endswith("_missing"))
    required = 12 if days_active <= 7 else (20 if days_active <= 30 else 24)
    from features.compute import data_completeness_score

    _set(row, "data_completeness_score", data_completeness_score(populated, required), min_required=False)

    return row
