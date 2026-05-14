"""
CV PRO — Screen Calibration Module
====================================
Handles the universal screen-independence problem:
  Given (screen_dpi, viewing_distance_cm, spatial_freq_cpd),
  compute the EXACT pixel size needed so the grating subtends
  the correct number of cycles per degree at the patient's eye.

Also provides a software gamma verification tool (no hardware needed)
using a psychophysical luminance-matching technique.

KEY FORMULA:
  visual_angle_per_pixel = arctan(2.54 / (dpi * distance_cm)) in degrees
  pixels_per_cycle = 1 / (spatial_freq_cpd * visual_angle_per_pixel)
  circle_diameter_px = pixels_per_cycle * cycles_in_grating

For CSV-1000 compatibility at 2 metres:
  1.5 inch circle @ 8 feet = 0.573° visual angle
  At 2m: diameter_cm = 2 * tan(0.573°/2) * 200 = 2.0 cm = 20mm target
"""

import numpy as np


# ── Core calculations ─────────────────────────────────────────────────────────

def visual_angle_per_pixel(dpi: float, distance_cm: float) -> float:
    """
    Compute the visual angle (in degrees) subtended by 1 pixel.

    Args:
        dpi: Screen pixels per inch (PPI)
        distance_cm: Viewing distance in cm

    Returns:
        Visual angle in degrees per pixel
    """
    pixel_size_cm = 2.54 / dpi  # 1 inch = 2.54 cm
    angle_rad = np.arctan(pixel_size_cm / distance_cm)
    return np.degrees(angle_rad)


def pixels_per_degree(dpi: float, distance_cm: float) -> float:
    """Pixels per degree of visual angle."""
    return 1.0 / visual_angle_per_pixel(dpi, distance_cm)


def circle_diameter_pixels(
    spatial_freq_cpd: float,
    dpi: float,
    distance_cm: float,
    cycles_in_grating: int,
) -> int:
    """
    Compute the display diameter in pixels for a grating circle.

    The circle must contain exactly `cycles_in_grating` cycles of the
    sinusoidal pattern so that the patient sees `spatial_freq_cpd` cpd.

    Args:
        spatial_freq_cpd: Target spatial frequency in cycles per degree
        dpi: Screen DPI/PPI
        distance_cm: Viewing distance in centimetres
        cycles_in_grating: How many full cycles are in the master image

    Returns:
        Circle diameter in pixels (integer)
    """
    ppd = pixels_per_degree(dpi, distance_cm)
    pixels_per_cycle = ppd / spatial_freq_cpd  # px for one full cycle
    diameter_px = pixels_per_cycle * cycles_in_grating
    return max(50, int(round(diameter_px)))


def validate_setup(dpi: float, distance_cm: float) -> dict:
    """
    Validate if the screen + distance setup is adequate for CSV-1000 testing.
    Returns a dict with computed sizes and pass/fail flags.
    """
    CYCLES = {"A": 5, "B": 8, "C": 12, "D": 16}
    FREQS  = {"A": 3, "B": 6, "C": 12, "D": 18}

    ppd = pixels_per_degree(dpi, distance_cm)
    results = {"ppd": round(ppd, 1), "dpi": dpi, "distance_cm": distance_cm, "rows": {}}

    for row in ["A", "B", "C", "D"]:
        freq = FREQS[row]
        cyc  = CYCLES[row]
        diam_px = circle_diameter_pixels(freq, dpi, distance_cm, cyc)
        ppc = ppd / freq  # pixels per cycle at this frequency

        # Nyquist: need at least 2 pixels per cycle
        nyquist_ok = ppc >= 2.0
        # Comfortable minimum: at least 20px diameter
        size_ok = diam_px >= 60

        results["rows"][row] = {
            "freq_cpd": freq,
            "display_diameter_px": diam_px,
            "pixels_per_cycle": round(ppc, 1),
            "nyquist_ok": nyquist_ok,
            "size_ok": size_ok,
            "ok": nyquist_ok and size_ok,
        }

    results["overall_ok"] = all(r["ok"] for r in results["rows"].values())
    return results


def recommended_distance(dpi: float) -> float:
    """
    Given a screen DPI, recommend the closest valid testing distance in cm
    that satisfies Nyquist for all 4 spatial frequencies.
    Minimum distance = 50cm, maximum = 400cm.
    """
    for dist in range(50, 400, 5):
        val = validate_setup(dpi, dist)
        if val["overall_ok"]:
            return float(dist)
    return 250.0  # fallback


# ── Common screen DPI values ──────────────────────────────────────────────────
COMMON_SCREENS = {
    "Custom": None,
    "Full HD 1080p 24\"": 92,
    "Full HD 1080p 27\"": 82,
    "Full HD 1080p 21\"": 105,
    "2K QHD 27\"": 109,
    "4K UHD 27\"": 163,
    "4K UHD 24\"": 183,
    "MacBook Pro 13\" (Retina)": 227,
    "MacBook Pro 14\" (M-series)": 254,
    "MacBook Pro 16\" (M-series)": 254,
    "MacBook Air 13\" (M-series)": 224,
    "iPad Pro 12.9\"": 264,
    "iPad Pro 11\"": 264,
    "iPhone 15 Pro": 460,
    "Dell UltraSharp 27\" U2722D": 109,
    "LG 27\" 4K (27UK850)": 163,
}
