"""
CV PRO — Grating Test Display Module
=======================================
Renders the actual patient-facing grating test in Streamlit.

PROTOCOL:
  - 4 rows shown sequentially: A (3cpd) → B (6cpd) → C (12cpd) → D (18cpd)
  - Each position: one pair shown (grating + blank, randomly top/bottom)
  - Patient or examiner clicks Top / Bottom / Neither (Can't see)
  - Software records last correct response → that is the score
  - Randomisation of grating position (top/bottom) per pair, per row

RANDOMISATION:
  CSV-1000 uses a fixed random key (printed on the chart).
  CV PRO uses a fresh random seed each session, which is actually
  more rigorous. The answer key is recorded in session_state.
"""

import streamlit as st
import numpy as np
from PIL import Image
import os
import json
import random
from screen_calibration import (
    circle_diameter_pixels, validate_setup,
    COMMON_SCREENS, recommended_distance
)

GRATING_DIR = os.path.join(os.path.dirname(__file__), "gratings_output", "gratings")
BLANK_DIR   = os.path.join(os.path.dirname(__file__), "gratings_output", "blanks")
MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "gratings_output", "manifest.json")

ROWS = ["A", "B", "C", "D"]
ROW_NAMES = {"A": "3 cpd", "B": "6 cpd", "C": "12 cpd", "D": "18 cpd"}
SCORES = ["S", "1", "2", "3", "4", "5", "6", "7", "8"]
CYCLES = {"A": 5, "B": 8, "C": 12, "D": 16}

@st.cache_resource
def load_manifest():
    with open(MANIFEST_PATH) as f:
        return json.load(f)

@st.cache_data
def load_grating_image(row: str, score: str, diameter_px: int) -> Image.Image:
    """Load and resize a grating to the exact display diameter."""
    path = os.path.join(GRATING_DIR, f"grating_{row}{score}.png")
    img = Image.open(path)
    return img.resize((diameter_px, diameter_px), Image.LANCZOS)

@st.cache_data
def load_blank_image(row: str, diameter_px: int) -> Image.Image:
    path = os.path.join(BLANK_DIR, f"blank_{row}.png")
    img = Image.open(path)
    return img.resize((diameter_px, diameter_px), Image.LANCZOS)


def render_calibration_ui():
    """Screen calibration sidebar section."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🖥️ Screen Setup")

    screen_choice = st.sidebar.selectbox(
        "Screen type",
        list(COMMON_SCREENS.keys()),
        key="screen_choice"
    )

    if screen_choice == "Custom":
        dpi = st.sidebar.number_input("Custom DPI/PPI", min_value=60, max_value=600,
                                       value=96, step=1, key="custom_dpi")
    else:
        dpi = COMMON_SCREENS[screen_choice]
        st.sidebar.caption(f"DPI: **{dpi}**")

    distance_cm = st.sidebar.number_input(
        "Testing distance (cm)", min_value=50, max_value=400,
        value=200, step=10, key="distance_cm"
    )

    val = validate_setup(dpi, distance_cm)
    st.session_state["screen_dpi"] = dpi
    st.session_state["distance_cm"] = distance_cm
    st.session_state["screen_valid"] = val

    if val["overall_ok"]:
        st.sidebar.success(f"✅ Setup valid · {val['ppd']} px/deg")
    else:
        bad = [r for r, v in val["rows"].items() if not v["ok"]]
        rec = recommended_distance(dpi)
        st.sidebar.warning(
            f"⚠️ Rows {', '.join(bad)} may be inaccurate at {distance_cm}cm.\n"
            f"Recommended minimum distance: **{int(rec)}cm**"
        )

    # Show computed circle sizes
    with st.sidebar.expander("Circle sizes at this setup"):
        for row in ROWS:
            r = val["rows"][row]
            icon = "✅" if r["ok"] else "⚠️"
            st.caption(f"{icon} Row {row} ({r['freq_cpd']} cpd): **{r['display_diameter_px']}px**")

    return dpi, distance_cm, val


def render_test_ui(patient_name: str, patient_age: int):
    """Main grating test display UI."""
    dpi = st.session_state.get("screen_dpi", 96)
    distance_cm = st.session_state.get("distance_cm", 200)
    val = st.session_state.get("screen_valid", {})

    st.markdown(f"## 👁️ Test: {patient_name}")
    st.caption(f"Screen: {dpi} DPI · Distance: {distance_cm} cm · {val.get('ppd', '?')} px/°")

    # Init test state
    if "test_row_idx" not in st.session_state:
        st.session_state.test_row_idx = 0
        st.session_state.test_score_idx = 0  # 0=S, 1..8
        st.session_state.test_answers = {}
        st.session_state.test_scores = {}
        st.session_state.test_grating_pos = {}  # {(row,score): 'top'|'bottom'}
        st.session_state.test_done = False
        # Pre-randomise grating positions for all pairs
        for row in ROWS:
            for score in SCORES:
                st.session_state.test_grating_pos[(row, score)] = random.choice(["top", "bottom"])

    if st.session_state.test_done:
        render_test_results()
        return

    row_idx   = st.session_state.test_row_idx
    score_idx = st.session_state.test_score_idx

    if row_idx >= len(ROWS):
        st.session_state.test_done = True
        render_test_results()
        return

    row   = ROWS[row_idx]
    score = SCORES[score_idx]
    freq  = {"A": 3, "B": 6, "C": 12, "D": 18}[row]
    diam  = circle_diameter_pixels(freq, dpi, distance_cm, CYCLES[row])
    grat_pos = st.session_state.test_grating_pos[(row, score)]

    # Progress
    total_pairs = 4 * 9
    done_pairs  = row_idx * 9 + score_idx
    st.progress(done_pairs / total_pairs,
                text=f"Row {row} ({ROW_NAMES[row]}) — Position {score} of 8")

    st.markdown("---")

    # Instructions
    st.markdown(
        "**Which circle has the stripes?** — Top, Bottom, or Neither"
        if score != "S" else
        "**Sample grating.** The stripes are visible on the left circle. "
        "Click **Top** or **Bottom** based on their position."
    )

    # Load images
    grating_img = load_grating_image(row, score, diam)
    blank_img   = load_blank_image(row, diam)

    top_img    = grating_img if grat_pos == "top"    else blank_img
    bottom_img = grating_img if grat_pos == "bottom" else blank_img

    # Display pair
    col_gap, col_top, col_gap2, col_bottom, col_gap3 = st.columns([1, 2, 0.5, 2, 1])
    with col_top:
        st.markdown("**Top**")
        st.image(top_img, use_container_width=True)
    with col_bottom:
        st.markdown("**Bottom**")
        st.image(bottom_img, use_container_width=True)

    # Log CS info for examiner (shown small)
    manifest = load_manifest()
    m = manifest[row][score]
    st.caption(
        f"Row {row} · Score {score} · {freq} cpd · "
        f"Michelson contrast: {m['michelson_contrast']:.4f} · "
        f"log CS: {m['log_cs']}"
    )

    # Response buttons
    st.markdown("#### Patient response:")
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    correct_answer = grat_pos  # 'top' or 'bottom'

    def record_response(response: str):
        is_correct = (response == correct_answer)
        st.session_state.test_answers[(row, score)] = {
            "response": response,
            "correct":  is_correct,
            "grat_pos": grat_pos,
        }
        # Track last correct score for this row
        if is_correct:
            st.session_state.test_scores[row] = score_idx  # numeric index (0=S, 1..8)

        # Advance
        next_score = score_idx + 1
        if next_score >= len(SCORES):
            # Move to next row
            st.session_state.test_row_idx  += 1
            st.session_state.test_score_idx = 0
        else:
            st.session_state.test_score_idx = next_score

    with b_col1:
        if st.button("⬆️ Top", use_container_width=True, key=f"btn_top_{row}{score}"):
            record_response("top")
            st.rerun()
    with b_col2:
        if st.button("⬇️ Bottom", use_container_width=True, key=f"btn_bot_{row}{score}"):
            record_response("bottom")
            st.rerun()
    with b_col3:
        if st.button("❌ Neither", use_container_width=True, key=f"btn_nei_{row}{score}"):
            record_response("neither")
            st.rerun()
    with b_col4:
        if st.button("⏭️ Skip Row", use_container_width=True, key=f"btn_skip_{row}{score}", type="secondary"):
            st.session_state.test_row_idx  += 1
            st.session_state.test_score_idx = 0
            st.rerun()


def render_test_results():
    """Show computed scores after test completion."""
    from cs_logic import score_to_log, calc_aulcsf, interpret_aulcsf

    scores_numeric = st.session_state.get("test_scores", {})

    st.success("✅ Test complete!")
    st.markdown("### Results")

    final_scores = {}
    log_vals = []
    for row in ROWS:
        # score_idx: 0=S, 1..8 → we use 1..8 only (S is sample)
        idx = scores_numeric.get(row, 0)
        # idx 0 = only S seen (or nothing) → clinical score 0
        # idx 1..8 → clinical score 1..8
        clinical_score = max(0, idx)
        if clinical_score == 0 and idx > 0:
            clinical_score = idx
        final_scores[row] = clinical_score

        log_v = score_to_log(row, clinical_score)
        log_vals.append(log_v)

    aulcsf = calc_aulcsf(log_vals)
    interp_label, _ = interpret_aulcsf(aulcsf)

    cols = st.columns(4)
    row_names = {"A": "3 cpd", "B": "6 cpd", "C": "12 cpd", "D": "18 cpd"}
    for col, row in zip(cols, ROWS):
        sc = final_scores[row]
        lv = score_to_log(row, sc)
        col.metric(
            label=f"Row {row} · {row_names[row]}",
            value=str(sc) if sc else "0",
            delta=f"logCS {lv:.2f}" if lv else "Not seen"
        )

    if aulcsf:
        badge = {"Normal": "🟢", "Mildly reduced": "🟡",
                 "Moderately reduced": "🟠", "Severely reduced": "🔴"}.get(interp_label, "⚪")
        st.markdown(f"### AULCSF: `{aulcsf:.3f}` {badge} {interp_label}")

    # Store in session for saving to patient record
    st.session_state["last_test_result"] = {
        "scores": final_scores,
        "log_vals": {r: score_to_log(r, final_scores[r]) for r in ROWS},
        "aulcsf": aulcsf,
        "interp": interp_label,
    }

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save to Patient Record", type="primary", use_container_width=True):
            st.session_state["save_test_result"] = True
            st.success("Scores saved. Go to the Record Test tab to confirm and add notes.")
    with col2:
        if st.button("🔄 Restart Test", use_container_width=True):
            for key in ["test_row_idx", "test_score_idx", "test_answers",
                        "test_scores", "test_grating_pos", "test_done"]:
                st.session_state.pop(key, None)
            st.rerun()
