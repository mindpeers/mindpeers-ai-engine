"""L2 Feature Store — window computations."""

from __future__ import annotations

import math
from statistics import mean, stdev
from typing import Optional


def ols_slope(values: list[Optional[float]]) -> Optional[float]:
    """OLS slope over ordered daily values; null if fewer than 4 points."""
    pts = [(i, v) for i, v in enumerate(values) if v is not None]
    if len(pts) < 4:
        return None
    n = len(pts)
    sx = sum(i for i, _ in pts)
    sy = sum(v for _, v in pts)
    sxx = sum(i * i for i, _ in pts)
    sxy = sum(i * v for i, v in pts)
    denom = n * sxx - sx * sx
    if denom == 0:
        return None
    return (n * sxy - sx * sy) / denom


def window_mean(values: list[Optional[float]], min_points: int) -> Optional[float]:
    present = [v for v in values if v is not None]
    if len(present) < min_points:
        return None
    return mean(present)


def window_std(values: list[Optional[float]], min_points: int) -> Optional[float]:
    present = [v for v in values if v is not None]
    if len(present) < min_points:
        return None
    if len(present) == 1:
        return 0.0
    return stdev(present)


def engagement_rate(active_flags: list[int]) -> float:
    """active_flags: 1 if engaged that day else 0."""
    if not active_flags:
        return 0.0
    return sum(active_flags) / len(active_flags)


def withdrawal_flag(engagement_rate_7d: float) -> int:
    return 1 if engagement_rate_7d < 0.25 else 0


def sleep_mood_coupled_decline(
    sleep_delta_30d: Optional[float],
    mood_slope_7d: Optional[float],
) -> int:
    if sleep_delta_30d is None or mood_slope_7d is None:
        return 0
    return 1 if sleep_delta_30d < -1.5 and mood_slope_7d < -0.3 else 0


def cortisol_flag_v1_proxy(
    resting_hr_relative: Optional[float],
    mood_volatility_14d: Optional[float],
    stress_days_last_7: int = 0,
) -> int:
    """v1 proxy per L2 spec §9.3."""
    if stress_days_last_7 >= 2:
        return 1
    if resting_hr_relative is not None and mood_volatility_14d is not None:
        if resting_hr_relative > 0.10 and mood_volatility_14d > 0.6:
            return 1
    return 0


def normalize_mood_to_canonical(raw_score: float, scale_max: float) -> float:
    """Map app mood to canonical 0-5 (L0/L2 boundary)."""
    if scale_max == 10:
        return raw_score * 0.5
    if scale_max == 5:
        return raw_score
    return raw_score * (5.0 / scale_max)


def resting_hr_relative(hr_7d: list[Optional[float]], hr_baseline_7d: list[Optional[float]]) -> Optional[float]:
    """hr_baseline_7d: block at D-30 from 30d+ users."""
    present_7 = [h for h in hr_7d if h is not None]
    present_base = [h for h in hr_baseline_7d if h is not None]
    if len(present_7) < 3 or len(present_base) < 3:
        return None
    m7 = mean(present_7)
    m30 = mean(present_base)
    if m30 == 0:
        return None
    return (m7 - m30) / m30


def data_completeness_score(populated: int, required: int) -> float:
    if required == 0:
        return 0.0
    return round(populated / required, 2)


def maturity_stage(days_active: int) -> str:
    if days_active <= 7:
        return "cold_start"
    if days_active <= 30:
        return "early"
    return "full"
