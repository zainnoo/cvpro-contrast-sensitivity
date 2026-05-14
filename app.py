"""
CV PRO — Contrast Sensitivity Analyser
Streamlit app · VectorVision CSV-1000 protocol
All modules consolidated into one file for reliability.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import datetime
import json
import os
import random
import io
import base64
from PIL import Image

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CV PRO — Contrast Sensitivity Analyser",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
div[data-testid="metric-container"] {
    background: white; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 14px 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
[data-testid="stSidebar"] { background: #1e293b !important; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] *,
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stNumberInput input {
    color: #1e293b !important;
    background-color: #f8fafc !important;
    border-color: #cbd5e1 !important;
}
[data-testid="stSidebar"] ::placeholder {
    color: #64748b !important;
    opacity: 1 !important;
}
.stDownloadButton > button {
    background-color: #0ea5e9 !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 500 !important; width: 100%;
}
.section-hdr {
    font-size: 15px; font-weight: 600; color: #1e293b;
    margin-bottom: 12px; padding-bottom: 6px;
    border-bottom: 2px solid #0ea5e9;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CS LOGIC
# ══════════════════════════════════════════════════════════════════════════════
LOG_CS = {
    "A": {1:1.00,2:1.17,3:1.34,4:1.49,5:1.63,6:1.78,7:1.93,8:2.08},
    "B": {1:1.21,2:1.38,3:1.55,4:1.70,5:1.84,6:1.99,7:2.14,8:2.29},
    "C": {1:0.91,2:1.08,3:1.25,4:1.40,5:1.54,6:1.69,7:1.84,8:1.99},
    "D": {1:0.47,2:0.64,3:0.81,4:0.96,5:1.10,6:1.25,7:1.40,8:1.55},
}
# Official linear CS values → Michelson contrast = 1/CS
LINEAR_CS = {
    "A": [5,  10,  15,  22,  31,  43,  61,  85,  120],  # S,1..8
    "B": [8,  16,  24,  36,  50,  70,  99,  138, 193],
    "C": [4,  8,   12,  18,  25,  35,  50,  70,  99 ],
    "D": [1.5,3,   4.5, 7,   9.5, 13,  18,  25,  36 ],
}
SPATIAL_FREQS = [3, 6, 12, 18]
LOG_SPATIAL_FREQS = [np.log10(f) for f in SPATIAL_FREQS]
ROW_LABELS = ["A","B","C","D"]
ROW_NAMES  = {"A":"3 cpd","B":"6 cpd","C":"12 cpd","D":"18 cpd"}
SCORES_ALL = ["S","1","2","3","4","5","6","7","8"]
CYCLES_IN_MASTER = {"A":5,"B":8,"C":12,"D":16}
FREQS = {"A":3,"B":6,"C":12,"D":18}
MASTER_DPI = 1200  # px diameter of master grating images

AGE_NORMS = {
    "20-55": {"mean":[1.84,2.09,1.76,1.33],"sd":[0.14,0.16,0.17,0.19]},
    "56-75": {"mean":[1.56,1.80,1.50,0.93],"sd":[0.15,0.165,0.15,0.25]},
}

def score_to_log(row, score):
    if not score: return None
    return LOG_CS[row].get(int(score))

def calc_aulcsf(log_vals):
    if all(v is None for v in log_vals): return None
    v = [x if x is not None else 0.0 for x in log_vals]
    area = sum(((v[i]+v[i+1])/2)*(LOG_SPATIAL_FREQS[i+1]-LOG_SPATIAL_FREQS[i])
               for i in range(len(LOG_SPATIAL_FREQS)-1))
    return round(area, 3)

def interpret_aulcsf(val):
    """Thresholds calibrated to VectorVision CSV-1000 age-norm data.
    Normal mean (20-55 yrs) = 1.443; -1SD = 1.317; -2SD = 1.190
    Normal mean (56-75 yrs) = 1.216; -1SD = 1.086
    """
    if val is None: return "Insufficient data","gray"
    if val >= 1.32: return "Normal","green"
    if val >= 1.19: return "Mildly reduced","orange"
    if val >= 1.09: return "Moderately reduced","red"
    return "Severely reduced","darkred"

def get_norm_band(grp):
    n = AGE_NORMS[grp]
    return {
        "upper":[m+s for m,s in zip(n["mean"],n["sd"])],
        "mean": n["mean"],
        "lower":[max(0,m-s) for m,s in zip(n["mean"],n["sd"])],
    }

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN CALIBRATION
# ══════════════════════════════════════════════════════════════════════════════
# Near-vision laptop/tablet presets only (50 cm testing distance)
COMMON_SCREENS = {
    "Samsung Galaxy Book4 Pro 360 (16\")": 212,
    "MacBook Pro 14\" (M-series)": 254,
    "MacBook Pro 16\" (M-series)": 254,
    "MacBook Air 13\" (M-series)": 224,
    "MacBook Air 15\" (M-series)": 224,
    "Dell XPS 13 (2560×1600)": 227,
    "Dell XPS 15 (3456×2160)": 261,
    "HP Spectre x360 14\"": 260,
    "Lenovo ThinkPad X1 Carbon (14\")": 210,
    "Surface Laptop 5 (13.5\")": 201,
    "Surface Pro 9 (13\")": 267,
    "iPad Pro 12.9\" (M-series)": 264,
    "iPad Air 11\" (M3)": 264,
    "Full HD Laptop 15.6\" (1920×1080)": 141,
    "Full HD Laptop 14\" (1920×1080)": 157,
    "2K Laptop 14\" (2560×1600)": 214,
    "Custom (enter DPI)": None,
}

def ppd(dpi, dist_cm):
    """Pixels per degree of visual angle."""
    px_cm = 2.54 / dpi
    return 1.0 / np.degrees(np.arctan(px_cm / dist_cm))

def circle_diam_px(freq_cpd, dpi, dist_cm, cycles):
    """Compute display diameter in pixels for exact visual angle."""
    return max(60, int(round(ppd(dpi, dist_cm) / freq_cpd * cycles)))

def validate_screen(dpi, dist_cm):
    results = {"ppd": round(ppd(dpi, dist_cm), 1), "rows": {}}
    for row in ROW_LABELS:
        freq = FREQS[row]
        cyc  = CYCLES_IN_MASTER[row]
        dp   = circle_diam_px(freq, dpi, dist_cm, cyc)
        ppc  = ppd(dpi, dist_cm) / freq
        ok   = ppc >= 2.0 and dp >= 60
        results["rows"][row] = {"freq":freq,"diam_px":dp,"ppc":round(ppc,1),"ok":ok}
    results["overall_ok"] = all(r["ok"] for r in results["rows"].values())
    return results

# ══════════════════════════════════════════════════════════════════════════════
# GRATING GENERATOR (runs on demand, cached)
# ══════════════════════════════════════════════════════════════════════════════
GRATING_DIR = os.path.join(os.path.dirname(__file__), "gratings_output", "gratings")
BLANK_DIR   = os.path.join(os.path.dirname(__file__), "gratings_output", "blanks")
GRATINGS_AVAILABLE = os.path.isdir(GRATING_DIR)

def linear_to_srgb(L):
    return (np.power(np.clip(L, 0, 1), 1/2.2) * 255).astype(np.uint8)

def make_grating_image(freq_cpd, michelson, diam_px, cycles):
    x = np.linspace(0, cycles * 2 * np.pi, diam_px)
    X = np.tile(x, (diam_px, 1))
    L = 0.5 * (1 + michelson * np.sin(X))
    cy = cx = diam_px // 2
    yy, xx = np.ogrid[:diam_px, :diam_px]
    L[np.sqrt((xx-cx)**2+(yy-cy)**2) > cx-1] = 0.5
    px = linear_to_srgb(L)
    return Image.fromarray(np.stack([px,px,px], axis=-1), mode="RGB")

def make_blank_image(diam_px):
    v = int(linear_to_srgb(np.array([0.5]))[0])
    return Image.new("RGB", (diam_px, diam_px), (v, v, v))

@st.cache_data(show_spinner=False)
def get_grating(row, score_label, diam_px):
    """Load from pre-generated file if available, else generate on-the-fly."""
    if GRATINGS_AVAILABLE:
        path = os.path.join(GRATING_DIR, f"grating_{row}{score_label}.png")
        if os.path.exists(path):
            return Image.open(path).resize((diam_px, diam_px), Image.LANCZOS)
    # Fallback: generate on-the-fly
    idx = SCORES_ALL.index(score_label)
    cs_val = LINEAR_CS[row][idx]
    michelson = 1.0 / cs_val
    return make_grating_image(FREQS[row], michelson, diam_px, CYCLES_IN_MASTER[row])

@st.cache_data(show_spinner=False)
def get_blank(row, diam_px):
    if GRATINGS_AVAILABLE:
        path = os.path.join(BLANK_DIR, f"blank_{row}.png")
        if os.path.exists(path):
            return Image.open(path).resize((diam_px, diam_px), Image.LANCZOS)
    return make_blank_image(diam_px)

# ══════════════════════════════════════════════════════════════════════════════
# PDF REPORT
# ══════════════════════════════════════════════════════════════════════════════
def generate_pdf(patient_name, patient_age, patient_gender, patient_mrn, tests):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable,
                                    Image as RLImage, KeepTogether)
    from reportlab.lib.enums import TA_CENTER

    BLUE = colors.HexColor("#0ea5e9")
    DARK = colors.HexColor("#1e293b")
    LIGHT= colors.HexColor("#f1f5f9")
    MID  = colors.HexColor("#94a3b8")
    GREEN= colors.HexColor("#22c55e")
    YEL  = colors.HexColor("#f59e0b")
    ORG  = colors.HexColor("#f97316")
    RED  = colors.HexColor("#ef4444")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []

    # Header
    story.append(Paragraph("CV PRO",
        ParagraphStyle("h",fontSize=20,textColor=BLUE,fontName="Helvetica-Bold")))
    story.append(Paragraph("Contrast Sensitivity Function Report",
        ParagraphStyle("s",fontSize=9,textColor=MID,fontName="Helvetica",spaceAfter=4)))
    story.append(HRFlowable(width="100%",thickness=1,color=BLUE))
    story.append(Spacer(1,0.4*cm))

    # Patient info
    pt = [[patient_name, f"Age: {patient_age} yrs · {patient_gender.capitalize()}",
           f"MRN: {patient_mrn or '—'}",
           f"Date: {datetime.date.today().strftime('%d %b %Y')}"]]
    pt_t = Table(pt, colWidths=[5*cm,5*cm,4*cm,4*cm])
    pt_t.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),"Helvetica"),
        ("FONTNAME",(0,0),(0,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("BACKGROUND",(0,0),(-1,-1),LIGHT),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
    ]))
    story.append(pt_t)
    story.append(Spacer(1,0.5*cm))

    # Chart
    if tests:
        fig, ax = plt.subplots(figsize=(8,4.2), dpi=140)
        xi = np.arange(4)
        band = get_norm_band("20-55" if patient_age < 56 else "56-75")
        ax.fill_between(xi, band["lower"], band["upper"],
                        color="#22c55e", alpha=0.12, label="Normal range (±1 SD)")
        ax.plot(xi, band["mean"], color="#22c55e", lw=1, ls="--", alpha=0.5)
        pal = ["#0ea5e9","#f97316","#8b5cf6","#10b981"]
        ls_map = {"OD":"-","OS":"--"}
        for i,t in enumerate(tests):
            lv = [t.get(f"log_{r.lower()}") for r in ROW_LABELS]
            px2, py = zip(*[(j,v) for j,v in enumerate(lv) if v is not None]) if any(v is not None for v in lv) else ([],[])
            if py:
                col_i = pal[i % len(pal)]
                ax.plot(list(px2), list(py), color=col_i,
                        ls=ls_map.get(t["eye"],"-"), lw=2.2,
                        marker="o", ms=7, markerfacecolor="white", markeredgewidth=2,
                        label=f"{t['eye']} · {t.get('visit_label') or t['visit_date']}")
        ax.set_xticks(xi); ax.set_xticklabels([f"{f} cpd" for f in SPATIAL_FREQS])
        ax.set_ylim(0,2.6); ax.set_ylabel("Log Contrast Sensitivity")
        ax.set_xlabel("Spatial Frequency (cpd)")
        ax.grid(True,color="#e2e8f0",lw=0.8); ax.spines[["top","right"]].set_visible(False)
        ax.legend(fontsize=8); plt.tight_layout()
        chart_buf = io.BytesIO()
        plt.savefig(chart_buf, format="png", bbox_inches="tight"); plt.close(fig)
        chart_buf.seek(0)
        story.append(KeepTogether([
            Paragraph("Contrast Sensitivity Function Curve",
                ParagraphStyle("sec",fontSize=11,textColor=DARK,fontName="Helvetica-Bold",spaceAfter=6)),
            RLImage(chart_buf, width=16*cm, height=9*cm),
        ]))
        story.append(Spacer(1,0.5*cm))

    # Per-test tables
    story.append(Paragraph("Detailed Scores",
        ParagraphStyle("sec",fontSize=11,textColor=DARK,fontName="Helvetica-Bold",spaceAfter=8)))

    for t in tests:
        aulcsf_val = t.get("aulcsf")
        interp,_ = interpret_aulcsf(aulcsf_val)
        story.append(Paragraph(
            f"<b>{t['eye']}</b> · {t.get('visit_label') or ''} · {t['visit_date']}",
            ParagraphStyle("te",fontSize=10,fontName="Helvetica",spaceAfter=4)))
        hdr = [["Row","Freq","Score","Log CS","Status"]]
        rows_data = []
        for row in ROW_LABELS:
            sc = t.get(f"score_{row.lower()}")
            lv = t.get(f"log_{row.lower()}")
            st2 = ("Good" if lv and lv>=1.70 else
                   "Borderline" if lv and lv>=1.40 else
                   "Reduced" if lv else "Not seen")
            rows_data.append([row, ROW_NAMES[row], str(sc) if sc else "0",
                               f"{lv:.2f}" if lv else "—", st2])
        tbl = Table(hdr+rows_data, colWidths=[1.5*cm,3*cm,3*cm,3*cm,4.5*cm])
        tbl.setStyle(TableStyle([
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTNAME",(0,1),(-1,-1),"Helvetica"),
            ("FONTSIZE",(0,0),(-1,-1),9),
            ("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[LIGHT,colors.white]),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),6),("ALIGN",(2,0),(-1,-1),"CENTER"),
        ]))
        story.append(tbl)
        arow = [[f"AULCSF: {aulcsf_val:.3f}" if aulcsf_val else "AULCSF: —",
                 interp,
                 f"Notes: {t.get('notes') or '—'}"]]
        atbl = Table(arow, colWidths=[4*cm,4*cm,10*cm])
        atbl.setStyle(TableStyle([
            ("FONTNAME",(0,0),(0,0),"Helvetica-Bold"),("FONTNAME",(1,0),(-1,0),"Helvetica"),
            ("FONTSIZE",(0,0),(-1,-1),9),("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#f0f9ff")),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#bae6fd")),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),6),
        ]))
        story.append(atbl)
        story.append(Spacer(1,0.4*cm))

    # Footer
    story.append(HRFlowable(width="100%",thickness=0.5,color=MID))
    story.append(Spacer(1,0.2*cm))
    story.append(Paragraph(
        f"CV PRO · Generated {datetime.datetime.now().strftime('%d %b %Y %H:%M')} · "
        "Log CS: VectorVision CSV-1000 norms · AULCSF: Applegate et al.",
        ParagraphStyle("ft",fontSize=7,textColor=MID,alignment=TA_CENTER)))
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

# ══════════════════════════════════════════════════════════════════════════════
# CIRCULAR IMAGE RENDERER
# ══════════════════════════════════════════════════════════════════════════════
# Maximum on-screen diameter to prevent overflow (caps at 420px per column)
MAX_DISPLAY_PX = 420
MIN_DISPLAY_PX = 80

def pil_to_b64(img: Image.Image, size_px: int) -> str:
    """Resize PIL image to size_px square and return base64-encoded PNG string."""
    img_resized = img.resize((size_px, size_px), Image.LANCZOS)
    buf = io.BytesIO()
    img_resized.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def show_circle(img: Image.Image, label: str, physics_px: int):
    """Render a PIL image as a circle at the physics-correct pixel size (capped to screen)."""
    # Clamp to reasonable screen bounds — preserves proportional size changes
    display_px = int(np.clip(physics_px, MIN_DISPLAY_PX, MAX_DISPLAY_PX))
    b64 = pil_to_b64(img, display_px)
    st.markdown(
        f"""
        <div style="text-align:center; margin-bottom:8px;">
          <div style="font-weight:600; font-size:15px; margin-bottom:6px; color:#1e293b;">{label}</div>
          <img src="data:image/png;base64,{b64}"
               style="width:{display_px}px; height:{display_px}px;
                      border-radius:50%; display:inline-block;
                      box-shadow: 0 2px 8px rgba(0,0,0,0.15);"
               alt="{label}" />
        </div>
        """,
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "patients": {}, "active_patient": None, "tests": {},
        "screen_dpi": 96, "distance_cm": 200,
        "screen_valid": validate_screen(96, 200),
        "test_row_idx": 0, "test_score_idx": 0,
        "test_answers": {}, "test_scores": {},
        "test_grating_pos": {}, "test_done": False,
        "test_started": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 👁️ CV PRO")
    st.caption("Near Vision Contrast Sensitivity")
    st.divider()

    # ── Screen setup (always visible) ─────────────────────────────────────────
    st.markdown("### 🖥️ Screen Setup")
    screen_choice = st.selectbox("Screen type", list(COMMON_SCREENS.keys()), key="screen_choice")
    if screen_choice == "Custom (enter DPI)":
        dpi = st.number_input("DPI / PPI", min_value=60, max_value=600, value=96, step=1)
    else:
        dpi = COMMON_SCREENS[screen_choice]
        st.caption(f"DPI: **{dpi}**")

    dist_cm = st.number_input("Testing distance (cm)", min_value=30, max_value=200,
                               value=50, step=5, key="distance_cm_input")

    val = validate_screen(dpi, dist_cm)
    st.session_state["screen_dpi"] = dpi
    st.session_state["distance_cm"] = dist_cm
    st.session_state["screen_valid"] = val

    if val["overall_ok"]:
        st.success(f"✅ Valid · {val['ppd']} px/°")
    else:
        bad = [r for r,rv in val["rows"].items() if not rv["ok"]]
        st.warning(f"⚠️ Rows {', '.join(bad)} may not render accurately at this distance")

    with st.expander("Circle sizes"):
        for row in ROW_LABELS:
            rv = val["rows"][row]
            icon = "✅" if rv["ok"] else "⚠️"
            st.caption(f"{icon} Row {row} ({rv['freq']}cpd): **{rv['diam_px']}px**")

    st.divider()

    # ── Add patient ───────────────────────────────────────────────────────────
    st.markdown("### Add Patient")
    with st.form("add_patient", clear_on_submit=True):
        p_name   = st.text_input("Full Name *", placeholder="e.g. Ramesh Kumar")
        p_age    = st.number_input("Age *", min_value=1, max_value=120, value=45)
        p_gender = st.selectbox("Gender *", ["Male","Female","Other"])
        p_mrn    = st.text_input("MRN / ID", placeholder="OPH-2026-001")
        if st.form_submit_button("➕ Add Patient", use_container_width=True):
            if p_name.strip():
                key = p_mrn.strip() or p_name.strip()
                st.session_state.patients[key] = {
                    "name":p_name.strip(),"age":int(p_age),
                    "gender":p_gender,"mrn":p_mrn.strip()
                }
                if key not in st.session_state.tests:
                    st.session_state.tests[key] = []
                st.session_state.active_patient = key
                st.success(f"Added {p_name}")

    st.divider()

    # ── Select patient ────────────────────────────────────────────────────────
    st.markdown("### Select Patient")
    if st.session_state.patients:
        keys = list(st.session_state.patients.keys())
        labels = [f"{st.session_state.patients[k]['name']}" for k in keys]
        idx = st.selectbox("Patient", range(len(keys)),
                           format_func=lambda i: labels[i], key="patient_selector")
        st.session_state.active_patient = keys[idx]
    else:
        st.info("No patients yet.")

    st.divider()
    st.caption("VectorVision CSV-1000 protocol · 4 spatial frequencies")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN AREA
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.active_patient:
    st.markdown("## Welcome to CV PRO")
    st.markdown("""
**CV PRO** is a near-vision contrast sensitivity testing tool based on the VectorVision CSV-1000 protocol, designed to run on any modern laptop at **50 cm testing distance**.

**Getting started:**
1. **Select your laptop model** in the sidebar — sets the correct DPI automatically
2. **Set screen brightness to 50%** before starting — critical for accurate results
3. **Add a patient** using the sidebar form
4. Go to **🔬 Live Test** tab to run the sinusoidal grating test
5. Or use **📝 Manual Entry** to type in scores from a physical chart
6. **📈 CS Graph** shows the contrast sensitivity curve with age-norm bands
7. **⬇️ Download PDF** for the full clinical report
    """)
    st.info("👈 Select your laptop model and set screen brightness to 50%, then add a patient to begin.")
    st.stop()

pk = st.session_state.active_patient
patient = st.session_state.patients[pk]
tests_list = st.session_state.tests.get(pk, [])

# Patient header
col_h, col_dl = st.columns([3, 1])
with col_h:
    st.markdown(f"## {patient['name']}")
    st.caption(f"{patient['age']} yrs · {patient['gender']}" +
               (f" · `{patient['mrn']}`" if patient.get('mrn') else ""))
with col_dl:
    if tests_list:
        pdf_bytes = generate_pdf(
            patient["name"], patient["age"],
            patient["gender"], patient.get("mrn",""), tests_list
        )
        st.download_button(
            "⬇️ Download PDF Report", data=pdf_bytes,
            file_name=f"CVPRO_{patient['name'].replace(' ','_')}_{datetime.date.today()}.pdf",
            mime="application/pdf", use_container_width=True,
        )

st.divider()

# Tabs
tab_live, tab_manual, tab_chart, tab_history = st.tabs(
    ["🔬 Live Test", "📝 Manual Entry", "📈 CS Graph", "📋 Test History"]
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB — LIVE TEST
# ══════════════════════════════════════════════════════════════════════════════
with tab_live:
    dpi      = st.session_state["screen_dpi"]
    dist_cm  = st.session_state["distance_cm"]
    scr_val  = st.session_state["screen_valid"]

    st.markdown('<p class="section-hdr">🔬 Live Sinusoidal Grating Test</p>',
                unsafe_allow_html=True)

    # Screen status banner
    if scr_val["overall_ok"]:
        st.success(f"Screen: {dpi} DPI · {dist_cm} cm · {scr_val['ppd']} px/° — All frequencies valid ✅")
    else:
        st.warning(f"⚠️ Screen setup may not render all frequencies accurately. Adjust distance in sidebar.")

    with st.expander("📋 Pre-test checklist — expand before starting"):
        st.markdown("""
| Item | Requirement |
|---|---|
| Testing distance | **50 cm** from laptop screen (near vision protocol) |
| Screen brightness | **50%** — do NOT exceed; higher brightness causes false positives |
| Room lighting | Normal ambient indoor light (no direct glare on screen) |
| Screen angle | Tilt screen so patient sees it straight-on, no reflections |
| Patient correction | Best corrected near vision — reading glasses / contacts on |
| Eye being tested | Occlude other eye with palm or occluder |
| Adaptation | 30 seconds in room light before starting |
| Screen preset | Select your exact laptop model in the sidebar |
        """)

    st.divider()

    # ── Test state machine ────────────────────────────────────────────────────
    if not st.session_state.test_started:
        eye_choice = st.selectbox("Eye to test", ["OD (Right eye)","OS (Left eye)"],
                                  key="live_eye_choice")
        visit_label = st.text_input("Visit label", placeholder="e.g. Pre-op, Post-op 1M",
                                    key="live_visit_label")
        if st.button("▶️ Start Test", type="primary", use_container_width=False):
            st.session_state.test_started    = True
            st.session_state.test_row_idx    = 0
            st.session_state.test_score_idx  = 0
            st.session_state.test_answers    = {}
            st.session_state.test_scores     = {}
            st.session_state.test_done       = False
            st.session_state.test_eye        = eye_choice.split()[0]
            st.session_state.test_visit_label= visit_label
            # Pre-randomise: grating goes to "A" or "B" each position
            # Guarantee no more than 2 consecutive same sides
            pos = {}
            last = None
            run  = 0
            for row in ROW_LABELS:
                for sc in SCORES_ALL:
                    choices = ["A", "B"]
                    if run >= 2:          # force a switch after 2 in a row
                        choices = ["B" if last == "A" else "A"]
                    side = random.choice(choices)
                    pos[(row, sc)] = side
                    run = run + 1 if side == last else 1
                    last = side
            st.session_state.test_grating_pos = pos
            st.rerun()

    elif st.session_state.test_done:
        # ── Results ───────────────────────────────────────────────────────────
        st.success("✅ Test complete!")
        scores_idx = st.session_state.test_scores  # {row: last_correct_idx (0=S)}
        final = {}
        log_vals = []
        for row in ROW_LABELS:
            idx = scores_idx.get(row, 0)
            # idx 0 means only sample (S) seen or nothing → clinical score 0
            # idx ≥1 means scored 1..8
            clinical = idx  # idx directly maps: 0→0, 1→score1 .. 8→score8
            final[row] = clinical
            log_vals.append(score_to_log(row, clinical))

        aulcsf = calc_aulcsf(log_vals)
        interp_label, _ = interpret_aulcsf(aulcsf)

        c1,c2,c3,c4 = st.columns(4)
        badge_map = {"Normal":"🟢","Mildly reduced":"🟡",
                     "Moderately reduced":"🟠","Severely reduced":"🔴"}
        for col, row in zip([c1,c2,c3,c4], ROW_LABELS):
            lv = score_to_log(row, final[row])
            col.metric(f"Row {row} · {ROW_NAMES[row]}",
                       str(final[row]) if final[row] else "0",
                       f"logCS {lv:.2f}" if lv else "Not seen")

        if aulcsf:
            st.markdown(f"### AULCSF: `{aulcsf:.3f}` "
                        f"{badge_map.get(interp_label,'⚪')} {interp_label}")

        col_save, col_restart = st.columns(2)
        with col_save:
            if st.button("💾 Save to Patient Record", type="primary", use_container_width=True):
                test_rec = {
                    "visit_date":  str(datetime.date.today()),
                    "visit_label": st.session_state.get("test_visit_label",""),
                    "eye":         st.session_state.get("test_eye","OD"),
                    "score_a": final["A"],"score_b": final["B"],
                    "score_c": final["C"],"score_d": final["D"],
                    "log_a": score_to_log("A",final["A"]),
                    "log_b": score_to_log("B",final["B"]),
                    "log_c": score_to_log("C",final["C"]),
                    "log_d": score_to_log("D",final["D"]),
                    "aulcsf": aulcsf, "notes": "",
                }
                st.session_state.tests[pk].insert(0, test_rec)
                st.session_state.test_started = False
                st.session_state.test_done    = False
                st.success("Saved! Switch to CS Graph or Test History to view.")
        with col_restart:
            if st.button("🔄 Restart Test", use_container_width=True):
                st.session_state.test_started = False
                st.session_state.test_done    = False
                st.rerun()

    else:
        # ── Show current grating pair ─────────────────────────────────────────
        row_idx   = st.session_state.test_row_idx
        score_idx = st.session_state.test_score_idx

        if row_idx >= len(ROW_LABELS):
            st.session_state.test_done = True
            st.rerun()

        row   = ROW_LABELS[row_idx]
        score = SCORES_ALL[score_idx]
        freq  = FREQS[row]
        diam  = circle_diam_px(freq, dpi, dist_cm, CYCLES_IN_MASTER[row])
        pos   = st.session_state.test_grating_pos.get((row, score), "A")

        # Progress bar
        done = row_idx * 9 + score_idx
        st.progress(done / 36, text=f"Row {row} ({ROW_NAMES[row]}) — Position {score}/8")

        # Load images
        grating_img = get_grating(row, score, diam)
        blank_img   = get_blank(row, diam)

        img_A = grating_img if pos == "A" else blank_img
        img_B = grating_img if pos == "B" else blank_img

        # Display — always side-by-side A | B, grating randomly in A or B
        display_px = int(np.clip(diam, MIN_DISPLAY_PX, MAX_DISPLAY_PX))
        st.markdown("### Which circle has the **stripes**?")
        st.caption(f"Row {row} · {freq} cpd · Position {score} · "
                   f"Michelson contrast: {1/LINEAR_CS[row][score_idx]:.4f} · "
                   f"Circle: {display_px}px ({dist_cm} cm, {dpi} DPI)")

        col_a, col_b = st.columns(2)
        with col_a:
            show_circle(img_A, "A", diam)
        with col_b:
            show_circle(img_B, "B", diam)

        # Response buttons
        st.markdown("#### Patient response:")
        b1, b2, b3, b4 = st.columns(4)

        def record(response):
            correct = response == pos
            st.session_state.test_answers[(row, score)] = {
                "response": response, "correct": correct}
            if correct:
                st.session_state.test_scores[row] = score_idx
            nxt = score_idx + 1
            if nxt >= len(SCORES_ALL):
                st.session_state.test_row_idx  += 1
                st.session_state.test_score_idx = 0
            else:
                st.session_state.test_score_idx = nxt

        with b1:
            if st.button("🅰️  Circle A", use_container_width=True, key=f"a_{row}{score}"):
                record("A"); st.rerun()
        with b2:
            if st.button("🅱️  Circle B", use_container_width=True, key=f"b_{row}{score}"):
                record("B"); st.rerun()
        with b3:
            if st.button("❌ Neither", use_container_width=True, key=f"n_{row}{score}"):
                record("neither"); st.rerun()
        with b4:
            if st.button("⏭️ Next Row", use_container_width=True, key=f"s_{row}{score}"):
                st.session_state.test_row_idx  += 1
                st.session_state.test_score_idx = 0
                st.rerun()

        if score == "S":
            st.info("ℹ️ This is the **sample grating** — the stripes are clearly visible. "
                    "Use this to show the patient what to look for.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB — MANUAL ENTRY
# ══════════════════════════════════════════════════════════════════════════════
with tab_manual:
    st.markdown('<p class="section-hdr">📝 Manual Score Entry</p>', unsafe_allow_html=True)
    with st.form("manual_entry", clear_on_submit=True):
        c1,c2,c3 = st.columns(3)
        with c1: visit_date  = st.date_input("Date", value=datetime.date.today())
        with c2:
            eye = st.selectbox("Eye", ["OD (Right)","OS (Left)"])
            eye_code = eye.split()[0]
        with c3: visit_label = st.text_input("Visit Label", placeholder="Pre-op / Post-op 1M")

        st.markdown("#### Scores — enter last correct position for each row")
        sc1,sc2,sc3,sc4 = st.columns(4)
        scores = {}
        for col, row in zip([sc1,sc2,sc3,sc4], ROW_LABELS):
            with col:
                st.markdown(f"**Row {row}** · {ROW_NAMES[row]}")
                scores[row] = st.selectbox(
                    f"Score {row}", list(range(9)),
                    format_func=lambda x: "0 — not seen" if x==0 else str(x),
                    key=f"m_score_{row}", label_visibility="collapsed")
                lv = score_to_log(row, scores[row])
                if lv: st.caption(f"logCS: **{lv:.2f}**")

        notes = st.text_area("Clinical Notes", placeholder="e.g. NS4 cataract · Post Phaco")

        if st.form_submit_button("✅ Save", use_container_width=True, type="primary"):
            log_vals = [score_to_log(r, scores[r]) for r in ROW_LABELS]
            aulcsf = calc_aulcsf(log_vals)
            rec = {
                "visit_date":str(visit_date),"visit_label":visit_label.strip(),"eye":eye_code,
                "score_a":scores["A"],"score_b":scores["B"],"score_c":scores["C"],"score_d":scores["D"],
                "log_a":log_vals[0],"log_b":log_vals[1],"log_c":log_vals[2],"log_d":log_vals[3],
                "aulcsf":aulcsf,"notes":notes.strip(),
            }
            st.session_state.tests[pk].insert(0, rec)
            interp,_ = interpret_aulcsf(aulcsf)
            st.success(f"Saved · AULCSF: {aulcsf:.3f} — {interp}" if aulcsf else "Saved")

# ══════════════════════════════════════════════════════════════════════════════
# TAB — CS GRAPH
# ══════════════════════════════════════════════════════════════════════════════
with tab_chart:
    st.markdown('<p class="section-hdr">📈 Contrast Sensitivity Function Curve</p>',
                unsafe_allow_html=True)
    if not tests_list:
        st.info("Record at least one test to generate the CSF curve.")
    else:
        t_labels = [f"{t['eye']} · {t.get('visit_label') or 'Visit'} · {t['visit_date']}"
                    for t in tests_list]
        sel = st.multiselect("Select tests to display (max 4)", range(len(tests_list)),
                             default=list(range(min(2, len(tests_list)))),
                             format_func=lambda i: t_labels[i], max_selections=4)

        show_y = st.checkbox("Show 20–55 yr norm band", value=True)
        show_o = st.checkbox("Show 56–75 yr norm band", value=True)

        if sel:
            fig, ax = plt.subplots(figsize=(10,5.5), dpi=130)
            ax.set_facecolor("#f8fafc"); fig.patch.set_facecolor("white")
            xi = np.arange(4)
            if show_y:
                b = get_norm_band("20-55")
                ax.fill_between(xi,b["lower"],b["upper"],color="#22c55e",alpha=0.13,label="Normal 20–55 yrs")
                ax.plot(xi,b["mean"],color="#22c55e",lw=1.2,ls="--",alpha=0.6)
            if show_o:
                b = get_norm_band("56-75")
                ax.fill_between(xi,b["lower"],b["upper"],color="#94a3b8",alpha=0.10,label="Normal 56–75 yrs")
                ax.plot(xi,b["mean"],color="#94a3b8",lw=1.2,ls="--",alpha=0.5)

            pal = ["#0ea5e9","#f97316","#8b5cf6","#10b981"]
            ls_map = {"OD":"-","OS":"--"}
            for i,ti in enumerate(sel):
                t = tests_list[ti]
                lv = [t.get(f"log_{r.lower()}") for r in ROW_LABELS]
                pts = [(j,v) for j,v in enumerate(lv) if v is not None]
                if pts:
                    px2,py = zip(*pts)
                    ax.plot(list(px2),list(py),color=pal[i%4],
                            ls=ls_map.get(t["eye"],"-"),lw=2.5,
                            marker="o",ms=8,markerfacecolor="white",markeredgewidth=2.2,
                            label=f"{t['eye']} — {t.get('visit_label') or 'Visit'} ({t['visit_date']})",zorder=5)
                    for px3,py3 in pts:
                        ax.annotate(f"{py3:.2f}",(px3,py3),
                                    textcoords="offset points",xytext=(0,10),
                                    fontsize=8,color=pal[i%4],ha="center",fontweight="600")

            ax.set_xticks(xi); ax.set_xticklabels([f"{f} cpd" for f in SPATIAL_FREQS],fontsize=11)
            ax.set_ylim(0,2.7); ax.set_yticks([0,.5,1,1.5,2,2.5])
            ax.set_ylabel("Log Contrast Sensitivity",fontsize=11)
            ax.set_xlabel("Spatial Frequency (Cycles per Degree)",fontsize=11)
            ax.grid(True,color="#e2e8f0",lw=0.8,alpha=0.8)
            ax.spines[["top","right"]].set_visible(False)
            ax.legend(fontsize=9,loc="upper right",framealpha=0.95)
            ax.set_title(f"{patient['name']} ({patient['age']} yrs)",fontsize=12,fontweight="600",color="#1e293b")
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            st.markdown("#### AULCSF")
            badge_map = {"Normal":"🟢","Mildly reduced":"🟡",
                         "Moderately reduced":"🟠","Severely reduced":"🔴"}
            cols = st.columns(len(sel))
            for col,ti in zip(cols,sel):
                t = tests_list[ti]
                v = t.get("aulcsf")
                interp,_ = interpret_aulcsf(v)
                col.metric(f"{t['eye']} · {t.get('visit_label') or t['visit_date']}",
                           f"{v:.3f}" if v else "—",
                           f"{badge_map.get(interp,'⚪')} {interp}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB — TEST HISTORY
# ══════════════════════════════════════════════════════════════════════════════
with tab_history:
    st.markdown('<p class="section-hdr">📋 Test History</p>', unsafe_allow_html=True)
    if not tests_list:
        st.info("No tests recorded yet.")
    else:
        rows_data = []
        for t in tests_list:
            interp,_ = interpret_aulcsf(t.get("aulcsf"))
            rows_data.append({
                "Date": t["visit_date"], "Eye": t["eye"],
                "Visit": t.get("visit_label") or "—",
                "A (3cpd)":  f"{t['score_a']} → {t['log_a']:.2f}" if t.get("log_a") else "0",
                "B (6cpd)":  f"{t['score_b']} → {t['log_b']:.2f}" if t.get("log_b") else "0",
                "C (12cpd)": f"{t['score_c']} → {t['log_c']:.2f}" if t.get("log_c") else "0",
                "D (18cpd)": f"{t['score_d']} → {t['log_d']:.2f}" if t.get("log_d") else "0",
                "AULCSF": f"{t['aulcsf']:.3f}" if t.get("aulcsf") is not None else "—",
                "Interpretation": interp,
                "Notes": t.get("notes") or "—",
            })
        df = pd.DataFrame(rows_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv,
                           f"CVPRO_{patient['name'].replace(' ','_')}_tests.csv",
                           "text/csv")
        st.markdown("---")
        del_idx = st.selectbox("Select test to delete", range(len(tests_list)),
                               format_func=lambda i: f"{tests_list[i]['eye']} · "
                               f"{tests_list[i].get('visit_label') or 'Visit'} · "
                               f"{tests_list[i]['visit_date']}")
        if st.button("🗑️ Delete", type="secondary"):
            st.session_state.tests[pk].pop(del_idx)
            st.rerun()

# Footer
st.markdown("---")
st.caption("CV PRO · Log CS: VectorVision CSV-1000 norms · AULCSF: Applegate et al. · For research use")

# v2.6.0 — fix: circle size now responds to distance/DPI changes; range restored to 30-200 cm
