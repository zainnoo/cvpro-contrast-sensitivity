"""
CV PRO — Contrast Sensitivity Analyser
Streamlit app based on the VectorVision CSV-1000 protocol.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import datetime
import json
import os

from cs_logic import (
    score_to_log, calc_aulcsf, interpret_aulcsf,
    ROW_LABELS, ROW_NAMES, SPATIAL_FREQS, get_norm_band, age_group
)
from pdf_report import generate_pdf
from screen_calibration import (
    validate_setup, COMMON_SCREENS, recommended_distance,
    circle_diameter_pixels
)
from test_display import render_calibration_ui, render_test_ui

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CV PRO — Contrast Sensitivity Analyser",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #f8fafc; }
    .stApp > header { background: transparent; }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }

    /* Sidebar */
    [data-testid="stSidebar"] { background: #1e293b !important; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stNumberInput label { color: #94a3b8 !important; }

    /* Score selects */
    div[data-testid="stSelectbox"] > label { font-weight: 600; color: #0ea5e9; }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }
    .stDownloadButton > button {
        background-color: #0ea5e9 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        width: 100%;
    }

    /* Section headers */
    .section-header {
        font-size: 15px;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 12px;
        padding-bottom: 6px;
        border-bottom: 2px solid #0ea5e9;
    }

    /* AULCSF badge */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }

    /* Log value */
    .log-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        color: #0ea5e9;
        font-weight: 600;
    }

    /* Test card */
    .test-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)


# ── Session state initialisation ──────────────────────────────────────────────
def init_state():
    if "patients" not in st.session_state:
        st.session_state.patients = {}   # {mrn_or_name: {...}}
    if "active_patient" not in st.session_state:
        st.session_state.active_patient = None
    if "tests" not in st.session_state:
        st.session_state.tests = {}      # {patient_key: [test_dict, ...]}

init_state()


# ── Sidebar — Patient management ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 👁️ CV PRO")
    st.caption("Contrast Sensitivity Analyser")
    st.divider()

    st.markdown("### Add Patient")
    with st.form("add_patient_form", clear_on_submit=True):
        p_name   = st.text_input("Full Name *", placeholder="e.g. Ramesh Kumar")
        p_age    = st.number_input("Age *", min_value=1, max_value=120, value=45, step=1)
        p_gender = st.selectbox("Gender *", ["Male", "Female", "Other"])
        p_mrn    = st.text_input("MRN / ID", placeholder="e.g. OPH-2026-001")
        add_btn  = st.form_submit_button("➕ Add Patient", use_container_width=True)

        if add_btn:
            if not p_name.strip():
                st.error("Name is required.")
            else:
                key = p_mrn.strip() if p_mrn.strip() else p_name.strip()
                st.session_state.patients[key] = {
                    "name": p_name.strip(), "age": int(p_age),
                    "gender": p_gender, "mrn": p_mrn.strip(),
                }
                if key not in st.session_state.tests:
                    st.session_state.tests[key] = []
                st.session_state.active_patient = key
                st.success(f"Patient **{p_name}** added.")

    st.divider()
    st.markdown("### Select Patient")
    if st.session_state.patients:
        patient_keys = list(st.session_state.patients.keys())
        patient_labels = [
            f"{st.session_state.patients[k]['name']} ({k})"
            for k in patient_keys
        ]
        sel_idx = st.selectbox(
            "Active patient",
            range(len(patient_keys)),
            format_func=lambda i: patient_labels[i],
            key="patient_selector"
        )
        st.session_state.active_patient = patient_keys[sel_idx]
    else:
        st.info("No patients yet. Add one above.")

    st.divider()
    # Screen calibration in sidebar
    render_calibration_ui()
    st.divider()
    st.caption("Protocol: VectorVision CSV-1000 · 85 cd/m² · 4 spatial frequencies")


# ── Main content ──────────────────────────────────────────────────────────────
if not st.session_state.active_patient:
    st.markdown("## Welcome to CV PRO")
    st.markdown("""
    **CV PRO** is a clinical contrast sensitivity scoring tool based on the
    [VectorVision CSV-1000](https://www.vectorvision.com/csv1000-contrast-sensitivity/) protocol.

    **Getting started:**
    1. Add a patient using the sidebar
    2. Record CS test scores (A, B, C, D — scores 1–8)
    3. View the automated CSF curve with age-matched normal ranges
    4. Download a full clinical PDF report

    ---
    *Spatial frequencies tested: 3, 6, 12, 18 cycles per degree*
    """)
    st.stop()

# ── Active patient ────────────────────────────────────────────────────────────
pk = st.session_state.active_patient
patient = st.session_state.patients[pk]
tests_list = st.session_state.tests.get(pk, [])

# Header
col_title, col_actions = st.columns([3, 1])
with col_title:
    st.markdown(f"## {patient['name']}")
    st.caption(f"{patient['age']} yrs · {patient['gender']}" +
               (f" · `{patient['mrn']}`" if patient['mrn'] else ""))

with col_actions:
    if tests_list:
        pdf_bytes = generate_pdf(
            patient_name   = patient["name"],
            patient_age    = patient["age"],
            patient_gender = patient["gender"],
            patient_mrn    = patient.get("mrn", ""),
            tests          = tests_list,
        )
        st.download_button(
            label="⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name=f"CVPRO_{patient['name'].replace(' ','_')}_{datetime.date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_live, tab_record, tab_chart, tab_history = st.tabs(["🔬 Live Test", "📝 Manual Entry", "📈 CS Graph", "📋 Test History"])


# ════════════════════════════════════════════════════════
# TAB 0 — Live Grating Test
# ════════════════════════════════════════════════════════
with tab_live:
    st.markdown('<p class="section-header">Live Sinusoidal Grating Test</p>',
                unsafe_allow_html=True)

    # Check screen calibration
    val = st.session_state.get("screen_valid", {})
    if not val:
        st.info("Configure your screen setup in the sidebar first, then start the test.")
    else:
        screen_ok = val.get("overall_ok", False)
        if not screen_ok:
            st.warning(
                "⚠️ Your current screen/distance setup may not accurately render "
                "high spatial frequencies. Adjust the distance in the sidebar."
            )

        # Luminance guidance
        with st.expander("📋 Pre-test checklist", expanded=False):
            st.markdown("""
            Before testing, ensure:
            - **Room lighting**: ~85 cd/m² (standard office fluorescent lighting)
            - **Screen brightness**: Set to 70–80% for most LCD monitors
            - **Patient correction**: Best corrected vision in the eye being tested
            - **Testing distance**: Patient seated at the configured distance
            - **One eye at a time**: Occlude the other eye
            - **Adaptation**: Allow 30 seconds in room lighting before testing
            """)

        render_test_ui(
            patient_name=patient.get("name", "Patient"),
            patient_age=patient.get("age", 40)
        )


# ════════════════════════════════════════════════════════
# TAB 1 — Manual Score Entry
# ════════════════════════════════════════════════════════
with tab_record:
    st.markdown('<p class="section-header">Record New CS Test</p>', unsafe_allow_html=True)

    with st.form("record_test_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            visit_date  = st.date_input("Visit Date", value=datetime.date.today())
        with c2:
            eye = st.selectbox("Eye", ["OD (Right)", "OS (Left)"])
            eye_code = eye.split()[0]  # 'OD' or 'OS'
        with c3:
            visit_label = st.text_input("Visit Label", placeholder="e.g. Pre-op, Post-op 1M")

        st.markdown("#### CV PRO Scores")
        st.caption("Enter the last correct score (1–8) for each row. Enter 0 if the patient could not see any grating.")

        score_cols = st.columns(4)
        scores = {}
        for i, row in enumerate(ROW_LABELS):
            with score_cols[i]:
                st.markdown(f"**Row {row}**")
                st.caption(ROW_NAMES[row])
                scores[row] = st.selectbox(
                    f"Score {row}",
                    options=list(range(9)),
                    format_func=lambda x: "0 — not seen" if x == 0 else str(x),
                    key=f"score_{row}",
                    label_visibility="collapsed",
                )

        notes = st.text_area("Clinical Notes", placeholder="e.g. Dense NS4 cataract · Post Phaco + Monofocal IOL")

        submitted = st.form_submit_button("✅ Save Test", use_container_width=True, type="primary")

    if submitted:
        log_vals = {row: score_to_log(row, scores[row]) for row in ROW_LABELS}
        aulcsf = calc_aulcsf([log_vals[r] for r in ROW_LABELS])
        interp_label, _ = interpret_aulcsf(aulcsf)

        test_record = {
            "visit_date":  str(visit_date),
            "visit_label": visit_label.strip(),
            "eye":         eye_code,
            "score_a": scores["A"], "score_b": scores["B"],
            "score_c": scores["C"], "score_d": scores["D"],
            "log_a": log_vals["A"], "log_b": log_vals["B"],
            "log_c": log_vals["C"], "log_d": log_vals["D"],
            "aulcsf": aulcsf,
            "notes":  notes.strip(),
        }
        st.session_state.tests[pk].insert(0, test_record)

        # ── Live preview ──
        st.success("Test saved!")
        pc1, pc2, pc3, pc4 = st.columns(4)
        for col, row in zip([pc1, pc2, pc3, pc4], ROW_LABELS):
            lv = log_vals[row]
            sc = scores[row]
            col.metric(
                label=f"Row {row} · {ROW_NAMES[row]}",
                value=f"{lv:.2f}" if lv else "—",
                delta=f"Score {sc}" if sc else "Not seen",
            )

        if aulcsf is not None:
            badge_colors = {
                "Normal": "🟢", "Mildly reduced": "🟡",
                "Moderately reduced": "🟠", "Severely reduced": "🔴"
            }
            badge = badge_colors.get(interp_label, "⚪")
            st.markdown(f"### AULCSF: `{aulcsf:.3f}` {badge} {interp_label}")


# ════════════════════════════════════════════════════════
# TAB 2 — CS Graph
# ════════════════════════════════════════════════════════
with tab_chart:
    st.markdown('<p class="section-header">Contrast Sensitivity Function (CSF) Curve</p>',
                unsafe_allow_html=True)

    if not tests_list:
        st.info("Record at least one test to generate the CSF curve.")
    else:
        # ── Options ──────────────────────────────────────────────────────────
        opt_col1, opt_col2 = st.columns([2, 1])
        with opt_col1:
            test_labels = [
                f"{t['eye']} · {t.get('visit_label') or 'Visit'} · {t['visit_date']}"
                for t in tests_list
            ]
            selected_indices = st.multiselect(
                "Select tests to display (max 4)",
                options=range(len(tests_list)),
                default=list(range(min(2, len(tests_list)))),
                format_func=lambda i: test_labels[i],
                max_selections=4,
            )
        with opt_col2:
            show_older_norm = st.checkbox("Show 56–75 yr norm band", value=True)
            show_younger_norm = st.checkbox("Show 20–55 yr norm band", value=True)

        if not selected_indices:
            st.warning("Select at least one test to plot.")
        else:
            selected_tests = [tests_list[i] for i in selected_indices]

            # ── Build chart ───────────────────────────────────────────────────
            fig, ax = plt.subplots(figsize=(10, 5.5), dpi=130)
            fig.patch.set_facecolor("white")
            ax.set_facecolor("#f8fafc")

            xi = np.arange(len(SPATIAL_FREQS))

            # Norm bands
            if show_younger_norm:
                band_y = get_norm_band("20-55")
                ax.fill_between(xi, band_y["lower"], band_y["upper"],
                                color="#22c55e", alpha=0.13, label="Normal 20–55 yrs (±1 SD)")
                ax.plot(xi, band_y["mean"], color="#22c55e", lw=1.2, ls="--", alpha=0.6)

            if show_older_norm:
                band_o = get_norm_band("56-75")
                ax.fill_between(xi, band_o["lower"], band_o["upper"],
                                color="#94a3b8", alpha=0.10, label="Normal 56–75 yrs (±1 SD)")
                ax.plot(xi, band_o["mean"], color="#94a3b8", lw=1.2, ls="--", alpha=0.5)

            # Patient lines
            palette = ["#0ea5e9", "#f97316", "#8b5cf6", "#10b981"]
            line_styles = {"OD": "-", "OS": "--"}
            for idx, t in enumerate(selected_tests):
                log_vals = [t.get(f"log_{r.lower()}") for r in ROW_LABELS]
                plot_x, plot_y = [], []
                for j, v in enumerate(log_vals):
                    if v is not None:
                        plot_x.append(j)
                        plot_y.append(v)
                if not plot_y:
                    continue
                color = palette[idx % len(palette)]
                ls = line_styles.get(t["eye"], "-")
                label = f"{t['eye']} — {t.get('visit_label') or 'Visit'} ({t['visit_date']})"
                ax.plot(plot_x, plot_y,
                        color=color, ls=ls, lw=2.5,
                        marker="o", ms=8,
                        markerfacecolor="white", markeredgewidth=2.2,
                        label=label, zorder=5)

                # Annotate log values
                for j, (px, py) in enumerate(zip(plot_x, plot_y)):
                    ax.annotate(f"{py:.2f}", (px, py),
                                textcoords="offset points", xytext=(0, 10),
                                fontsize=7.5, color=color, ha="center", fontweight="600")

            ax.set_xticks(xi)
            ax.set_xticklabels([f"{f} cpd" for f in SPATIAL_FREQS], fontsize=11)
            ax.set_ylim(0, 2.7)
            ax.set_yticks([0, 0.5, 1.0, 1.5, 2.0, 2.5])
            ax.set_yticklabels([f"{v:.1f}" for v in [0, 0.5, 1.0, 1.5, 2.0, 2.5]], fontsize=10)
            ax.set_ylabel("Log Contrast Sensitivity", fontsize=11)
            ax.set_xlabel("Spatial Frequency (Cycles per Degree)", fontsize=11)
            ax.grid(True, color="#e2e8f0", linewidth=0.8, alpha=0.8)
            ax.spines[["top", "right"]].set_visible(False)
            ax.legend(fontsize=9, loc="upper right", framealpha=0.95,
                      edgecolor="#e2e8f0", fancybox=True)
            ax.set_title(
                f"CSF Curve — {patient['name']} ({patient['age']} yrs)",
                fontsize=12, fontweight="600", color="#1e293b", pad=12
            )
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            # ── AULCSF summary cards ──────────────────────────────────────────
            st.markdown("#### AULCSF Summary")
            badge_map = {
                "Normal": ("🟢", "#dcfce7"),
                "Mildly reduced": ("🟡", "#fef9c3"),
                "Moderately reduced": ("🟠", "#ffedd5"),
                "Severely reduced": ("🔴", "#fee2e2"),
            }
            aulcsf_cols = st.columns(len(selected_tests))
            for col, t in zip(aulcsf_cols, selected_tests):
                val = t.get("aulcsf")
                label_txt = t.get("visit_label") or t["visit_date"]
                interp_label, _ = interpret_aulcsf(val)
                icon, bg = badge_map.get(interp_label, ("⚪", "#f1f5f9"))
                col.metric(
                    label=f"{t['eye']} · {label_txt}",
                    value=f"{val:.3f}" if val is not None else "—",
                    delta=f"{icon} {interp_label}",
                )


# ════════════════════════════════════════════════════════
# TAB 3 — Test History
# ════════════════════════════════════════════════════════
with tab_history:
    st.markdown('<p class="section-header">Test History</p>', unsafe_allow_html=True)

    if not tests_list:
        st.info("No tests recorded yet.")
    else:
        # Summary table
        rows = []
        for t in tests_list:
            interp_label, _ = interpret_aulcsf(t.get("aulcsf"))
            rows.append({
                "Date":       t["visit_date"],
                "Eye":        t["eye"],
                "Visit":      t.get("visit_label") or "—",
                "A (3cpd)":   f"{t['score_a']} → {t['log_a']:.2f}" if t.get("log_a") else "0",
                "B (6cpd)":   f"{t['score_b']} → {t['log_b']:.2f}" if t.get("log_b") else "0",
                "C (12cpd)":  f"{t['score_c']} → {t['log_c']:.2f}" if t.get("log_c") else "0",
                "D (18cpd)":  f"{t['score_d']} → {t['log_d']:.2f}" if t.get("log_d") else "0",
                "AULCSF":     f"{t['aulcsf']:.3f}" if t.get("aulcsf") is not None else "—",
                "Interpretation": interp_label,
                "Notes":      t.get("notes") or "—",
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # CSV download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download as CSV",
            data=csv,
            file_name=f"CVPRO_{patient['name'].replace(' ','_')}_tests.csv",
            mime="text/csv",
        )

        st.markdown("---")
        st.markdown("#### Delete a Test")
        del_idx = st.selectbox(
            "Select test to delete",
            range(len(tests_list)),
            format_func=lambda i: f"{tests_list[i]['eye']} · {tests_list[i].get('visit_label') or 'Visit'} · {tests_list[i]['visit_date']}"
        )
        if st.button("🗑️ Delete Selected Test", type="secondary"):
            st.session_state.tests[pk].pop(del_idx)
            st.success("Test deleted.")
            st.rerun()


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "CV PRO · Log CS values: [VectorVision CSV-1000 norms](https://www.vectorvision.com/csv1000-norms/) · "
    "AULCSF: Applegate et al. method · "
    "For clinical research use — not a substitute for calibrated hardware."
)
