# Time Series Studio

A PyQt6 desktop application for visualizing, managing, and AI-powered
forecasting of any number of time series — with web import (stocks, forex,
crypto, macro data), local CSV import, multivariate covariate forecasting via
[TimesFM](https://github.com/google-research/timesfm), and a fully
multilingual user interface (English, German, French, Spanish, Hindi,
Mandarin).

---

## Table of Contents

1. [Feature Overview](#feature-overview)
2. [Files in This Project](#files-in-this-project)
3. [Installation](#installation)
4. [Starting the App](#starting-the-app)
5. [Usage](#usage)
6. [Multilingual Support (i18n)](#multilingual-support-i18n)
7. [Forecasting Engine: TimesFM & Fallback](#forecasting-engine-timesfm--fallback)
8. [Project Files (Save/Load)](#project-files-saveload)
9. [CSV Export](#csv-export)
10. [Known Limitations & Performance Notes](#known-limitations--performance-notes)
11. [Troubleshooting](#troubleshooting)
12. [Technical Architecture](#technical-architecture)

---

## Feature Overview

- **Any number of time series** displayed, grouped, and compared simultaneously
- **AI forecasting** with Google TimesFM (v1 / v2.5 / v3.0, automatic version
  and GPU→CPU fallback) — still works without TimesFM via a simple
  statistical heuristic
- **Covariate forecasting:** series marked as "target" are forecast using all
  other (non-target) series as covariates
- **Data import:**
  - Web: Yahoo Finance (stocks/ETFs/indices), FRED (US macro data), CoinGecko (crypto)
  - Local CSV files (any numeric column, automatic date-column detection)
  - 9 built-in earth-science demo series (sunspots, moon cycle, ENSO,
    temperature, CO₂, population, volcanoes, earthquakes, 1749–present)
- **Grouping:** assign any series to any group via a simple dialog, create
  new groups, most-recently-edited group appears first
- **Zoom & pan** over a shared time range across all series
- **Red-hatched gaps** mark missing data points (including gaps in the middle
  of the history, not just at the edges)
- **CSV export** of all series including forecast, side by side, synchronized
  via a shared date column
- **Save/load project** as JSON (complete application state)
- **6 languages**, switchable at runtime, no restart required

---

## Files in This Project

| File                     | Purpose                                                                 |
|---------------------------|------------------------------------------------------------------------|
| `time_series_studio.py`   | Main program (the actual application, executable)                     |
| `i18n.py`                 | Translation module — all UI text in 6 languages, `tr()` function       |
| `README.md`               | This file                                                              |

**Important:** `i18n.py` must be in the same directory as
`time_series_studio.py`, since the main file imports it via
`from i18n import tr, set_language, ...`.

---

## Installation

Requires **Python 3.10+**. The program installs all dependencies
**automatically** on first run (see `ensure_package()` at the top of
`time_series_studio.py`):

```
numpy, pandas, PyQt6, matplotlib, requests, yfinance,
pandas_datareader, torch, timesfm[torch]
```

Optional (only for NVIDIA GPU acceleration; installation may fail without
blocking the program):

```
nvidia-cuda-nvrtc-cu12
```

If you'd rather install the packages yourself beforehand:

```bash
pip install numpy pandas PyQt6 matplotlib requests yfinance pandas_datareader torch "timesfm[torch]"
```

> **Note on TimesFM 3.0:** The 3.0 weights are released under the
> non-commercial `timesfm-non-commercial-license-v1.0` license. For
> production/commercial use, the program automatically falls back to version
> 2.5 if `timesfm3` is unavailable or fails to load.

---

## Starting the App

```bash
python3 time_series_studio.py
```

If, on first launch, no GPU is available or TimesFM isn't installed, the
status bar at the bottom of the window and a one-time notice dialog will
indicate that forecasts are running in **statistical fallback mode** — the
program remains fully functional, but forecast quality is simpler (a moving
average with exponential decay instead of the real AI model).

---

## Usage

| Element                         | Function                                                                 |
|-----------------------------------|---------------------------------------------------------------------------|
| **Forecast days**                | Number of days to forecast into the future                               |
| **+ New group**                  | Creates a new, empty group                                               |
| **Import (Web)**                 | Opens the dialog for Yahoo/FRED/CoinGecko import                         |
| **Import (CSV)**                 | Loads a local CSV file (numeric columns become time series)              |
| **Export (CSV)**                 | Exports all series incl. forecast as one combined CSV file               |
| **Save Project / Load Project**  | Save or restore the complete state as JSON                               |
| **Zoom / Pan view**              | Shared time range across all series                                      |
| **Checkbox per series**          | Marks the series as "target" → forecast using covariates                 |
| **⚙ icon**                       | Assign the series to another/new group                                   |
| **✕ icon**                       | Delete the series                                                        |
| **🔄 icon**                      | Web-imported series only: re-fetch the latest data                       |
| **Language** (dropdown)          | Switch the UI to one of the 6 languages instantly                        |

Hovering over a series name shows a tooltip with all available metadata
(source, symbol, start date, last value, …).

---

## Multilingual Support (i18n)

The program is fully localized via the `i18n.py` module into:

| Code | Language   |
|------|-----------|
| `en` | English (default) |
| `de` | Deutsch |
| `fr` | Français |
| `es` | Español |
| `hi` | हिन्दी |
| `zh` | 中文 (Mandarin) |

The language can be switched **at any time, at runtime**, via the "Language"
dropdown in the top-right of the window — no restart required.

### What exactly gets translated?

**All parts of the user interface ("chrome")** are translated:

- Buttons, labels, tooltips
- All dialog titles and text (group dialog, finance import dialog,
  save/load project dialogs)
- All error, warning, and success messages (`QMessageBox`)
- Status bar (TimesFM status)
- Window title
- The labels of the 9 built-in demo series and their groups
  (sunspots, moon cycle, ENSO, …)
- Metadata keys shown in the tooltip (e.g. "Source" / "Quelle" / "来源")
- Automatically assigned group names (e.g. "Yahoo Finance", "FRED Macro Data")

### Deliberate design decision: what stays unchanged?

Series and group names simultaneously serve as **display text and internal
key** in the program (e.g. as dictionary keys in `self.raw_data`, in
`group_creation_order`, in saved project files). If a runtime language
switch retroactively translated these names, it would:

- break the mapping between series and group,
- make previously saved project files no longer match on reload,
- lose references in `active_targets`, `series_source_configs`, etc.

For this reason: **series/group names that have already been created (the 9
demo series at program start, symbols loaded via web import, column names
imported via CSV, manually assigned group names) keep the language they were
created in.** A later language switch immediately translates the entire UI
around them (buttons, dialogs, tooltips, status bar) — only the already
existing data names themselves stay unchanged (you can always rename/regroup
them manually via the ⚙ icon).

**Practical consequence:** Since the program starts in English by default,
the 9 demo series are named in English. If you'd like them created in a
different language from the start, change the default language in `i18n.py`
before the first launch:

```python
_DEFAULT_LANG = "de"   # instead of "en"
```

### Adding new translations

All text lives centrally in `i18n.py` in the `TRANSLATIONS` dictionary. Each
entry has the form:

```python
"my_new_key": {
    "en": "English text", "de": "Deutscher Text", "fr": "Texte français",
    "es": "Texto español", "hi": "हिन्दी टेक्स्ट", "zh": "中文文本",
},
```

and is used in the code via `tr("my_new_key")`. For placeholders:

```python
tr("update_success_msg", name="AAPL")
# internally uses: "Time series '{name}' was updated successfully!".format(name="AAPL")
```

If a key is accidentally missing from `TRANSLATIONS`, `[[key]]` is displayed
at runtime instead of crashing — missing translations are immediately
visible this way.

---

## Forecasting Engine: TimesFM & Fallback

On startup, the program attempts to initialize TimesFM in this order:

1. **TimesFM 3.0** (`timesfm3` module, version since August 2026) — GPU, then CPU
2. **TimesFM 2.5** (`TimesFM_2p5_200M_torch` / `TimesFm` class) — GPU, then CPU
3. **TimesFM 1.0** (older `TimesFmHparams` API) — GPU, then CPU
4. **Statistical fallback** (moving average with exponential decay), if none
   of the above work

If an inference call fails **after** successful initialization with a
CUDA/JIT error (e.g. `PTX JIT compiler library not found`), TimesFM is
automatically **re-initialized once on CPU** and the computation is retried —
instead of permanently switching to the simple statistical fallback. The
window title and status bar always accurately reflect the method actually in
use (`method_label()`), e.g.:

- `TimesFM v2.5 (GPU)`
- `TimesFM v1 (CPU)`
- `Statistical fallback` / `Statistischer Fallback` / `统计回退方法` …

---

## Project Files (Save/Load)

**Save Project** writes a JSON file with the complete application state:

```json
{
  "forecast_days": 14,
  "zoom_level": 100,
  "scroll_position": 100,
  "active_targets": { "...": true },
  "series_groups": { "...": "..." },
  "group_creation_order": ["..."],
  "series_start_dates": { "...": "YYYY-MM-DD" },
  "series_source_configs": { "...": {"source": "Yahoo", "symbol": "AAPL", "years": 30} },
  "custom_empty_groups": ["..."],
  "metadata": { "...": {"...": "..."} },
  "raw_data": { "...": [1.0, 2.0, null, ...] }
}
```

**Important:** Since series/group names (see above) are not retroactively
re-translated when the language changes, project files are **fully portable
across languages** — a project file created in English loads just as
correctly in German as it does in Chinese. Only the *interface* around it is
then shown in whichever language is currently active.

---

## CSV Export

**Export (CSV)** writes all loaded series (history + forecast) **side by
side** into one file:

- One column per series, MultiIndex header with group and series names
- A shared date column (`Date`/`Datum`/`日期`/…), across which all columns
  are synchronized (missing days in a shorter series show as an empty cell)
- Rows sorted by date descending (most recent date first)
- Column order matches the display order in the UI

---

## Known Limitations & Performance Notes

- The 9 built-in demo series span the period **1749 to today** (roughly
  101,000 days). Preparing these series (`generate_full_series()`) includes a
  day-by-day Python loop to classify `history`/`missing`/`forecast` — with
  such long time ranges, the very first startup or any recalculation can
  noticeably take longer (a few seconds to a couple of minutes, depending on
  hardware). This is existing behavior of the original application logic and
  independent of the multilingual support.
- An automatic CUDA→CPU fallback makes computation slower but keeps it
  working.
- CoinGecko has a public rate limit; very frequent requests may temporarily fail.
- Switching languages immediately translates the interface; series/group
  names already loaded remain unchanged by design (see
  [Multilingual Support](#multilingual-support-i18n)).

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `cudaErrorJitCompilerNotFound` / `PTX JIT compiler library not found` | Automatically handled (CPU re-init). For persistent GPU use, verify that the installed `nvidia-cuda-nvrtc-cu<major>` version matches your installed Torch CUDA version. |
| TimesFM fails to load / warning dialog appears | The program remains usable (statistical fallback). Try `pip install "timesfm[torch]"` again, or check the console output for the exact error. |
| `yfinance`/`pandas_datareader` missing | Installed automatically on startup; alternatively install manually: `pip install yfinance pandas_datareader`. |
| A missing translation shows as `[[key]]` | The corresponding key is missing from the `TRANSLATIONS` dictionary in `i18n.py` — add it (see above). |
| CSV import doesn't detect the date column | The column must be named `date`, `datum`, `time`, `timestamp`, `jahr`, or `year` (case-insensitive); otherwise a daily grid counting back from today is assumed. |

---

## Technical Architecture

- **GUI framework:** PyQt6
- **Plots:** matplotlib (`QtAgg` backend), one compact sparkline-style canvas
  per series (`SingleTimeSeriesCanvas`)
- **Data storage:** `numpy` arrays per series in `self.raw_data`, plus
  metadata dictionaries; preparation/caching via `generate_full_series()` and
  `self.forecast_cache`
- **Forecasting:** the `TimeSeriesModel` class encapsulates TimesFM
  initialization, version/device fallback, and the statistical fallback
- **Internationalization:** central `i18n.py` module with a `tr()` function,
  globally switchable language state, no external i18n libraries required

---

*Built with automated multilingual support (English, German, French,
Spanish, Hindi, Mandarin).*
