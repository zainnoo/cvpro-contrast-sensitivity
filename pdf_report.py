"""
PDF report generator for CV PRO contrast sensitivity results.
Uses ReportLab + matplotlib (embedded chart image).
"""

import io
import datetime
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from cs_logic import (
    score_to_log, calc_aulcsf, interpret_aulcsf,
    LOG_CS, SPATIAL_FREQS, AGE_NORMS, ROW_LABELS, ROW_NAMES,
    get_norm_band, age_group
)


# ── Colour palette ────────────────────────────────────────────────────────────
BLUE   = colors.HexColor("#0ea5e9")
ORANGE = colors.HexColor("#f97316")
DARK   = colors.HexColor("#1e293b")
LIGHT  = colors.HexColor("#f1f5f9")
MID    = colors.HexColor("#94a3b8")
GREEN  = colors.HexColor("#22c55e")
RED    = colors.HexColor("#ef4444")
YELLOW = colors.HexColor("#f59e0b")


def _interp_color(val):
    if val is None: return MID
    if val >= 0.60: return GREEN
    if val >= 0.45: return YELLOW
    if val >= 0.30: return ORANGE
    return RED


def _build_chart(tests: list[dict], patient_age: int) -> io.BytesIO:
    """
    Render the CS curve chart with norm bands using matplotlib.
    Returns a BytesIO PNG buffer.
    """
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#f8fafc")

    xfreqs = [str(f) for f in SPATIAL_FREQS]
    xi = np.arange(len(SPATIAL_FREQS))

    # ── Norm bands ────────────────────────────────────────────────────────────
    grp = age_group(patient_age)
    band = get_norm_band(grp)
    ax.fill_between(xi, band["lower"], band["upper"],
                    color="#22c55e", alpha=0.12, label=f"Normal {grp} yrs")
    ax.plot(xi, band["mean"], color="#22c55e", lw=1, ls="--", alpha=0.5)

    # older band for reference if patient is young
    other_grp = "56-75" if grp == "20-55" else "20-55"
    band2 = get_norm_band(other_grp)
    ax.fill_between(xi, band2["lower"], band2["upper"],
                    color="#94a3b8", alpha=0.07, label=f"Normal {other_grp} yrs")

    # ── Patient curves ────────────────────────────────────────────────────────
    line_styles = {
        "OD": {"color": "#0ea5e9", "ls": "-",  "marker": "o"},
        "OS": {"color": "#f97316", "ls": "--", "marker": "s"},
    }
    plotted_eyes = {}
    for t in tests:
        eye = t["eye"]
        log_vals = [t.get(f"log_{r.lower()}") for r in ROW_LABELS]
        # Only plot where we have values
        plot_x, plot_y = [], []
        for i, v in enumerate(log_vals):
            if v is not None:
                plot_x.append(i)
                plot_y.append(v)
        if not plot_y:
            continue
        style = line_styles.get(eye, line_styles["OD"])
        label = f"{eye} — {t.get('visit_label', t.get('visit_date', ''))}"
        ax.plot(plot_x, plot_y,
                color=style["color"], ls=style["ls"],
                marker=style["marker"], ms=7, lw=2.2,
                markerfacecolor="white", markeredgewidth=2,
                label=label)

    # ── Axes ──────────────────────────────────────────────────────────────────
    ax.set_xticks(xi)
    ax.set_xticklabels([f"{f} cpd" for f in SPATIAL_FREQS], fontsize=10)
    ax.set_ylim(0, 2.6)
    ax.set_yticks([0, 0.5, 1.0, 1.5, 2.0, 2.5])
    ax.set_ylabel("Log Contrast Sensitivity", fontsize=10)
    ax.set_xlabel("Spatial Frequency (Cycles per Degree)", fontsize=10)
    ax.grid(True, color="#e2e8f0", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8, loc="upper right", framealpha=0.9)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_pdf(
    patient_name: str,
    patient_age: int,
    patient_gender: str,
    patient_mrn: str,
    tests: list[dict],
    clinic_name: str = "CV PRO Contrast Sensitivity Clinic",
) -> bytes:
    """
    Generate a full clinical PDF report.
    `tests` is a list of dicts with keys:
        eye, visit_date, visit_label,
        score_a, score_b, score_c, score_d,
        log_a, log_b, log_c, log_d,
        aulcsf, notes
    Returns PDF as bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    header_style = ParagraphStyle(
        "header", fontSize=18, textColor=BLUE,
        fontName="Helvetica-Bold", spaceAfter=2
    )
    sub_style = ParagraphStyle(
        "sub", fontSize=9, textColor=MID,
        fontName="Helvetica", spaceAfter=0
    )
    story.append(Paragraph("CV PRO", header_style))
    story.append(Paragraph("Contrast Sensitivity Function Report", sub_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
    story.append(Spacer(1, 0.4*cm))

    # ── Patient info ──────────────────────────────────────────────────────────
    pt_data = [
        ["Patient Name", patient_name,
         "Report Date", datetime.date.today().strftime("%d %b %Y")],
        ["Age", f"{patient_age} years",
         "Gender", patient_gender.capitalize()],
        ["MRN / ID", patient_mrn or "—",
         "Clinic", clinic_name],
    ]
    pt_table = Table(pt_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 5*cm])
    pt_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), DARK),
        ("TEXTCOLOR", (2, 0), (2, -1), DARK),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.black),
        ("TEXTCOLOR", (3, 0), (3, -1), colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(pt_table)
    story.append(Spacer(1, 0.5*cm))

    # ── CS Chart ─────────────────────────────────────────────────────────────
    if tests:
        chart_buf = _build_chart(tests, patient_age)
        chart_img = RLImage(chart_buf, width=16*cm, height=9*cm)
        story.append(KeepTogether([
            Paragraph("Contrast Sensitivity Function (CSF) Curve",
                      ParagraphStyle("sec", fontSize=11, textColor=DARK,
                                     fontName="Helvetica-Bold", spaceAfter=6)),
            chart_img,
            Spacer(1, 0.15*cm),
            Paragraph(
                "Shaded areas represent normal population ranges (±1 SD). "
                "Blue solid line = OD (right eye). Orange dashed line = OS (left eye).",
                ParagraphStyle("caption", fontSize=8, textColor=MID, spaceAfter=4)
            ),
        ]))
        story.append(Spacer(1, 0.5*cm))

    # ── Test results tables ───────────────────────────────────────────────────
    story.append(Paragraph(
        "Detailed Test Results",
        ParagraphStyle("sec", fontSize=11, textColor=DARK,
                       fontName="Helvetica-Bold", spaceAfter=8)
    ))

    for t in tests:
        eye = t.get("eye", "")
        eye_color = BLUE if eye == "OD" else ORANGE
        visit = t.get("visit_label") or ""
        date  = t.get("visit_date", "")
        aulcsf_val = t.get("aulcsf")
        interp_label, _ = interpret_aulcsf(aulcsf_val)

        # Title row for this test
        story.append(Paragraph(
            f'<font color="#0ea5e9"><b>{eye}</b></font>  '
            f'{"· " + visit if visit else ""}  '
            f'<font color="#94a3b8">({date})</font>',
            ParagraphStyle("testeye", fontSize=10, fontName="Helvetica", spaceAfter=4)
        ))

        # Score/log table
        score_header = ["Row", "Spatial Freq", "Score (1-8)", "Log CS", "Interpretation"]
        score_rows = []
        for row in ROW_LABELS:
            sc = t.get(f"score_{row.lower()}")
            lv = t.get(f"log_{row.lower()}")
            if sc is None or sc == 0:
                interp = "Not seen"
                interp_c = MID
            elif lv is not None:
                if lv >= 1.70:   interp, interp_c = "Good", GREEN
                elif lv >= 1.40: interp, interp_c = "Borderline", YELLOW
                else:            interp, interp_c = "Reduced", RED
            else:
                interp, interp_c = "—", MID
            score_rows.append([
                row, ROW_NAMES[row],
                str(sc) if sc else "0 (not seen)",
                f"{lv:.2f}" if lv is not None else "—",
                interp,
            ])

        score_data = [score_header] + score_rows
        col_widths = [1.5*cm, 3*cm, 3*cm, 3*cm, 4.5*cm]
        score_table = Table(score_data, colWidths=col_widths)
        score_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ]))
        story.append(score_table)

        # AULCSF summary
        aulcsf_color = _interp_color(aulcsf_val)
        aulcsf_row = [[
            "AULCSF",
            f"{aulcsf_val:.3f}" if aulcsf_val is not None else "—",
            interp_label,
            "Notes: " + (t.get("notes") or "—"),
        ]]
        aulcsf_table = Table(aulcsf_row, colWidths=[2*cm, 3*cm, 4*cm, 9*cm])
        aulcsf_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (-1, 0), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
            ("TEXTCOLOR", (0, 0), (0, 0), DARK),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bae6fd")),
        ]))
        story.append(aulcsf_table)
        story.append(Spacer(1, 0.4*cm))

    # ── Interpretation key ────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("AULCSF Interpretation Key",
        ParagraphStyle("key", fontSize=9, fontName="Helvetica-Bold", textColor=DARK, spaceAfter=4)
    ))
    key_data = [
        ["≥ 0.60", "Normal", "0.45 – 0.59", "Mildly reduced",
         "0.30 – 0.44", "Moderately reduced", "< 0.30", "Severely reduced"]
    ]
    key_table = Table(key_data, colWidths=[1.8*cm, 3.5*cm, 2.2*cm, 3.5*cm, 2.2*cm, 4*cm, 1.5*cm, 3.5*cm])
    key_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, 0), "Helvetica-Bold"),
        ("FONTNAME", (4, 0), (4, 0), "Helvetica-Bold"),
        ("FONTNAME", (6, 0), (6, 0), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 0), (1, 0), colors.HexColor("#22c55e")),
        ("TEXTCOLOR", (3, 0), (3, 0), colors.HexColor("#f59e0b")),
        ("TEXTCOLOR", (5, 0), (5, 0), colors.HexColor("#f97316")),
        ("TEXTCOLOR", (7, 0), (7, 0), colors.HexColor("#ef4444")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(key_table)
    story.append(Spacer(1, 0.3*cm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"Generated by CV PRO · {datetime.datetime.now().strftime('%d %b %Y, %H:%M')} · "
        "Log CS values derived from VectorVision CSV-1000 normative data · "
        "AULCSF method: Applegate et al.",
        ParagraphStyle("footer", fontSize=7, textColor=MID, alignment=TA_CENTER)
    ))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
