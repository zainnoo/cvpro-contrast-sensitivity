"""
CS Logic — official VectorVision CSV-1000 lookup table and calculations.
Source: https://www.vectorvision.com/csv1000-norms/
"""

import numpy as np

# ── Official log CS lookup tables (score 1-8, 0 = not seen) ──────────────────
LOG_CS = {
    "A": {1: 1.00, 2: 1.17, 3: 1.34, 4: 1.49, 5: 1.63, 6: 1.78, 7: 1.93, 8: 2.08},
    "B": {1: 1.21, 2: 1.38, 3: 1.55, 4: 1.70, 5: 1.84, 6: 1.99, 7: 2.14, 8: 2.29},
    "C": {1: 0.91, 2: 1.08, 3: 1.25, 4: 1.40, 5: 1.54, 6: 1.69, 7: 1.84, 8: 1.99},
    "D": {1: 0.47, 2: 0.64, 3: 0.81, 4: 0.96, 5: 1.10, 6: 1.25, 7: 1.40, 8: 1.55},
}

SPATIAL_FREQS = [3, 6, 12, 18]  # cpd
LOG_SPATIAL_FREQS = [np.log10(f) for f in SPATIAL_FREQS]  # for AULCSF integration

# ── Age-normed population data (photopic, VectorVision norms) ─────────────────
AGE_NORMS = {
    "20-55": {
        "mean": [1.84, 2.09, 1.76, 1.33],
        "sd":   [0.14, 0.16, 0.17, 0.19],
    },
    "56-75": {
        "mean": [1.56, 1.80, 1.50, 0.93],
        "sd":   [0.15, 0.165, 0.15, 0.25],
    },
}

ROW_LABELS = ["A", "B", "C", "D"]
ROW_NAMES  = {"A": "3 cpd", "B": "6 cpd", "C": "12 cpd", "D": "18 cpd"}


def score_to_log(row: str, score: int | None) -> float | None:
    """Convert a 1-8 CV PRO score to log CS. Returns None if score is 0 or None."""
    if not score:
        return None
    return LOG_CS[row].get(score)


def calc_aulcsf(log_vals: list[float | None]) -> float | None:
    """
    AULCSF via trapezoidal integration of log CS vs log spatial frequency.
    Applegate et al. method: integrate between log10(3) and log10(18).
    """
    if all(v is None for v in log_vals):
        return None
    v = [x if x is not None else 0.0 for x in log_vals]
    x = LOG_SPATIAL_FREQS
    area = sum(
        ((v[i] + v[i + 1]) / 2) * (x[i + 1] - x[i])
        for i in range(len(x) - 1)
    )
    return round(area, 3)


def interpret_aulcsf(val: float | None) -> tuple[str, str]:
    """Returns (label, color) for AULCSF interpretation."""
    if val is None:
        return "Insufficient data", "gray"
    if val >= 0.60:
        return "Normal", "green"
    if val >= 0.45:
        return "Mildly reduced", "orange"
    if val >= 0.30:
        return "Moderately reduced", "red"
    return "Severely reduced", "darkred"


def get_norm_band(age_group: str) -> dict:
    norms = AGE_NORMS[age_group]
    return {
        "upper": [m + s for m, s in zip(norms["mean"], norms["sd"])],
        "mean":  norms["mean"],
        "lower": [max(0, m - s) for m, s in zip(norms["mean"], norms["sd"])],
    }


def age_group(age: int) -> str:
    return "20-55" if age < 56 else "56-75"
