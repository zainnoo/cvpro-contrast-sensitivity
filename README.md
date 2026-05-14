# 👁️ CV PRO — Contrast Sensitivity Analyser

A clinical spatial contrast sensitivity scoring and reporting tool built with Streamlit, based on the **VectorVision CSV-1000** protocol.

## Features

- **Patient registry** — add patients with age, gender, MRN
- **Score entry** — record CV PRO scores (1–8) for all 4 spatial frequencies: 3, 6, 12, 18 cpd (rows A, B, C, D)
- **Auto log CS conversion** — scores are automatically converted to log contrast sensitivity using official VectorVision norms
- **CSF curve** — interactive chart with age-matched normal population bands (20–55 yrs and 56–75 yrs)
- **AULCSF** — automatic Area Under Log Contrast Sensitivity Function calculation (Applegate et al. method)
- **PDF report** — downloadable clinical report with CS curve chart, per-row scores, log CS values, AULCSF and interpretation
- **CSV export** — download test history as spreadsheet

## Log CS Lookup Table

Based on the official [VectorVision CSV-1000 normative data](https://www.vectorvision.com/csv1000-norms/):

| Score | Row A (3 cpd) | Row B (6 cpd) | Row C (12 cpd) | Row D (18 cpd) |
|-------|--------------|--------------|----------------|----------------|
| 1     | 1.00         | 1.21         | 0.91           | 0.47           |
| 2     | 1.17         | 1.38         | 1.08           | 0.64           |
| 3     | 1.34         | 1.55         | 1.25           | 0.81           |
| 4     | 1.49         | 1.70         | 1.40           | 0.96           |
| 5     | 1.63         | 1.84         | 1.54           | 1.10           |
| 6     | 1.78         | 1.99         | 1.69           | 1.25           |
| 7     | 1.93         | 2.14         | 1.84           | 1.40           |
| 8     | 2.08         | 2.29         | 1.99           | 1.55           |

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud

1. Fork or clone this repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Set **Main file path** to `app.py`
5. Click **Deploy**

## Testing Protocol

- Room lighting: **85 cd/m²**
- Testing distance: **2 metres** (on 15-inch monitor)
- 4 charts shown: A (3 cpd), B (6 cpd), C (12 cpd), D (18 cpd)
- Scoring: Last correct response from 1–8 is the score

## AULCSF Interpretation

| Value    | Interpretation      |
|----------|---------------------|
| ≥ 0.60   | Normal              |
| 0.45–0.59 | Mildly reduced     |
| 0.30–0.44 | Moderately reduced |
| < 0.30   | Severely reduced    |

AULCSF calculated by trapezoidal integration of fitted log CS units between log₁₀(3) = 0.477 and log₁₀(18) = 1.255 (Applegate et al.).

## Disclaimer

CV PRO is designed for clinical research and educational use. It is not a substitute for hardware-calibrated contrast sensitivity testing with a certified instrument.

---

*Developed by Dr Zain Khatib · Ophthalmologist · [VectorVision CSV-1000 protocol](https://www.vectorvision.com)*
