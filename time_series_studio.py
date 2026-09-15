#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys

import os

def ensure_package(package_name, import_name=None, optional=False):
    """Installiert ein Paket bei Bedarf. Bei optional=True wird ein fehlgeschlagener
    'pip install'-Versuch (z.B. auf inkompatiblen Plattformen wie macOS/Windows für
    CUDA-Pakete) abgefangen, statt das ganze Programm abstürzen zu lassen."""
    if import_name is None:
        import_name = package_name
    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"Installiere fehlende Bibliothek: {package_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            return True
        except subprocess.CalledProcessError as e:
            msg = f"Konnte '{package_name}' nicht installieren: {e}"
            if optional:
                print(f"(Optional) {msg} — wird übersprungen.")
                return False
            else:
                print(f"FEHLER: {msg}")
                raise

# Automatische Überprüfung und Installation benötigter Abhängigkeiten inkl. TimesFM/Torch und CUDA NVRTC
for pkg, imp, optional in [
    ("numpy", "numpy", False),
    ("pandas", "pandas", False),
    ("PyQt6", "PyQt6", False),
    ("matplotlib", "matplotlib", False),
    ("requests", "requests", False),
    ("yfinance", "yfinance", False),
    ("pandas_datareader", "pandas_datareader", False),
    ("torch", "torch", False),
    ("timesfm[torch]", "timesfm", False),
    # Optional: nur relevant für NVIDIA-GPU/CUDA-Beschleunigung. Auf Systemen ohne
    # passende Plattform (z.B. macOS, Windows ohne CUDA) darf die Installation
    # fehlschlagen, ohne dass das Programm abstürzt.
    ("nvidia-cuda-nvrtc-cu12", "nvidia.cuda_nvrtc", True),
]:
    ensure_package(pkg, imp, optional=optional)


def _ensure_matching_nvrtc():
    """Installiert das zur tatsächlich installierten Torch-CUDA-Version passende
    nvrtc-Paket. Ein Versions-Mismatch (z.B. Torch für CUDA 12.4, aber generisch
    installiertes nvidia-cuda-nvrtc-cu12 in falscher Minor-Version) ist eine häufige
    Ursache für 'cudaErrorJitCompilerNotFound', selbst wenn das Paket vorhanden ist."""
    try:
        import torch
        cuda_ver = torch.version.cuda  # z.B. "12.4" oder None bei CPU-only Build
        if not cuda_ver:
            return
        major = cuda_ver.split(".")[0]
        ensure_package(f"nvidia-cuda-nvrtc-cu{major}", "nvidia.cuda_nvrtc", optional=True)
    except Exception as e:
        print(f"Hinweis: passende nvrtc-Version konnte nicht ermittelt werden: {e}")


def _configure_nvidia_cuda_libs():
    """Fügt die lib-Ordner der pip-installierten NVIDIA-CUDA-Pakete (nvrtc, cublas,
    cudnn, ...) dem Bibliothekssuchpfad hinzu. pip-Wheels wie 'nvidia-cuda-nvrtc-cu12'
    installieren ihre .so-Dateien nach site-packages/nvidia/<paket>/lib, dieser Ordner
    liegt aber nicht automatisch in LD_LIBRARY_PATH. Ohne das schlägt die PTX-JIT-
    Kompilierung (torch.compile/triton, von TimesFM 2.5 genutzt) mit
    'CUDA error: PTX JIT compiler library not found' (cudaErrorJitCompilerNotFound) fehl,
    selbst wenn das Paket korrekt installiert ist."""
    try:
        import importlib.util
        lib_dirs = []
        for mod_name in [
            "nvidia.cuda_nvrtc", "nvidia.cuda_runtime", "nvidia.cublas",
            "nvidia.cudnn", "nvidia.cufft", "nvidia.curand", "nvidia.cusolver",
            "nvidia.cusparse", "nvidia.nccl", "nvidia.nvtx",
        ]:
            spec = importlib.util.find_spec(mod_name)
            if spec and spec.submodule_search_locations:
                for loc in spec.submodule_search_locations:
                    lib_dir = os.path.join(loc, "lib")
                    if os.path.isdir(lib_dir):
                        lib_dirs.append(lib_dir)

        if not lib_dirs:
            return

        if sys.platform == "win32":
            for d in lib_dirs:
                try:
                    os.add_dll_directory(d)
                except (AttributeError, FileNotFoundError, OSError):
                    pass
        else:
            existing = os.environ.get("LD_LIBRARY_PATH", "")
            unique_dirs = list(dict.fromkeys(lib_dirs))  # Duplikate entfernen, Reihenfolge behalten
            new_path = ":".join(unique_dirs)
            os.environ["LD_LIBRARY_PATH"] = f"{new_path}:{existing}" if existing else new_path
            print(f"CUDA-Bibliothekspfade registriert: {new_path}")
    except Exception as e:
        print(f"Hinweis: NVIDIA-CUDA-Bibliothekspfade konnten nicht automatisch gesetzt werden: {e}")


_ensure_matching_nvrtc()
_configure_nvidia_cuda_libs()

import datetime
import json
import numpy as np
import pandas as pd

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QSpinBox, QScrollArea,
    QFrame, QMessageBox, QDialog, QLineEdit, QComboBox, QFormLayout,
    QSlider, QCheckBox, QStackedLayout, QSizePolicy, QInputDialog,
    QProgressDialog
)
from PyQt6.QtCore import Qt

import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# TimesFM Import Versuch (Haupt-API sowie das seit TimesFM 3.0 (August 2026) separate
# 'timesfm3'-Modul, unter dem die aktuelle Top-Level-API liegt: TimesFM3Evaluator/ModelConfig)
try:
    import timesfm
    HAS_TIMESFM = True
except ImportError:
    HAS_TIMESFM = False

try:
    import timesfm3
    HAS_TIMESFM3 = True
except ImportError:
    HAS_TIMESFM3 = False

# Module für Finanz-Datenimporte
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

try:
    import pandas_datareader.data as web
    HAS_DATAREADER = True
except ImportError:
    HAS_DATAREADER = False

import requests

from i18n import tr, set_language, get_language, LANGUAGES


class GroupAssignDialog(QDialog):
    """Dialogfenster zur Neuzuordnung einer Zeitreihe zu einer bestehenden oder neuen Gruppe."""
    def __init__(self, series_name: str, current_group: str, existing_groups: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("group_dialog_title", name=series_name))
        self.resize(380, 180)

        self.selected_group = current_group

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.group_combo = QComboBox()
        unique_groups = sorted(list(set(existing_groups)))
        self.group_combo.addItems(unique_groups)
        if current_group in unique_groups:
            self.group_combo.setCurrentText(current_group)

        form_layout.addRow(tr("label_existing_group"), self.group_combo)

        self.new_group_input = QLineEdit()
        self.new_group_input.setPlaceholderText(tr("placeholder_new_group"))
        form_layout.addRow(tr("label_new_group"), self.new_group_input)

        layout.addLayout(form_layout)

        btn_box = QHBoxLayout()
        ok_btn = QPushButton(tr("btn_apply"))
        ok_btn.clicked.connect(self.apply_group)
        cancel_btn = QPushButton(tr("btn_cancel"))
        cancel_btn.clicked.connect(self.reject)

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box)

    def apply_group(self):
        new_name = self.new_group_input.text().strip()
        if new_name:
            self.selected_group = new_name
        else:
            self.selected_group = self.group_combo.currentText()
        self.accept()


class FinanceImportDialog(QDialog):
    """Dialogfenster zum Laden von kostenlosen Zeitreihen inkl. Metadaten."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("finance_dialog_title"))
        self.resize(450, 220)

        self.fetched_data = {}
        self.fetched_metadata = {}
        self.fetched_groups = {}
        self.fetched_configs = {}
        self.fetched_start_dates = {}

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.source_combo = QComboBox()
        self.source_combo.setToolTip(tr("tooltip_source"))
        self.source_combo.addItems([
            tr("source_yahoo"),
            tr("source_fred"),
            tr("source_coingecko"),
        ])
        form_layout.addRow(tr("label_data_source"), self.source_combo)

        self.symbol_input = QLineEdit()
        self.symbol_input.setToolTip(tr("tooltip_symbol"))
        self.symbol_input.setPlaceholderText(tr("placeholder_symbol"))
        form_layout.addRow(tr("label_symbol"), self.symbol_input)

        self.years_input = QSpinBox()
        self.years_input.setToolTip(tr("tooltip_years"))
        self.years_input.setRange(1, 100)
        self.years_input.setValue(30)
        form_layout.addRow(tr("label_years"), self.years_input)

        layout.addLayout(form_layout)

        hint_label = QLabel(tr("finance_hint_html"))
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)

        btn_box = QHBoxLayout()
        fetch_btn = QPushButton(tr("btn_fetch_data"))
        fetch_btn.setToolTip(tr("tooltip_fetch"))
        fetch_btn.clicked.connect(self.fetch_data)
        
        cancel_btn = QPushButton(tr("btn_cancel"))
        cancel_btn.setToolTip(tr("tooltip_cancel_dialog"))
        cancel_btn.clicked.connect(self.reject)

        btn_box.addWidget(fetch_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box)

    def fetch_data(self):
        symbol = self.symbol_input.text().strip().upper()
        if not symbol:
            QMessageBox.warning(self, tr("err_input_title"), tr("err_input_msg"))
            return

        source = self.source_combo.currentText()
        years = self.years_input.value()
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=years * 365)

        try:
            if tr("source_yahoo") in source or "Yahoo" in source:
                if not HAS_YFINANCE:
                    raise ImportError(tr("err_yfinance_missing"))
                
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date)
                
                if df.empty:
                    raise ValueError(tr("err_no_data_ticker", symbol=symbol))
                
                raw_series = df['Close']
                df_full = raw_series.resample('D').asfreq()
                df_full = df_full.interpolate(method='linear')
                vals = df_full.values
                
                name = f"Yahoo:{symbol}"
                self.fetched_data[name] = vals
                self.fetched_start_dates[name] = pd.Timestamp(df_full.index[0].date())
                self.fetched_groups[name] = tr("grp_yahoo_finance")
                self.fetched_configs[name] = {"source": "Yahoo", "symbol": symbol, "years": years}
                
                info = ticker.info if hasattr(ticker, 'info') else {}
                self.fetched_metadata[name] = {
                    tr("meta_source"): tr("src_yahoo_finance"),
                    tr("meta_symbol"): symbol,
                    tr("meta_name"): info.get("longName", info.get("shortName", symbol)),
                    tr("meta_currency"): info.get("currency", "USD"),
                    tr("meta_datapoints_days"): len(vals),
                    tr("meta_start_date"): str(df_full.index[0].date()),
                    tr("meta_end_date"): str(df_full.index[-1].date()),
                    tr("meta_last_value"): f"{vals[-1]:.2f}" if not np.isnan(vals[-1]) else "N/A"
                }

            elif tr("source_fred") in source or "FRED" in source:
                if not HAS_DATAREADER:
                    raise ImportError(tr("err_datareader_missing"))
                
                df = web.DataReader(symbol, 'fred', start_date, end_date)
                if df.empty:
                    raise ValueError(tr("err_no_fred_data", symbol=symbol))
                
                raw_series = df[symbol]
                df_daily = raw_series.resample('D').asfreq()
                df_daily = df_daily.interpolate(method='linear')
                vals = df_daily.values

                name = f"FRED:{symbol}"
                self.fetched_data[name] = vals
                self.fetched_start_dates[name] = pd.Timestamp(df_daily.index[0].date())
                self.fetched_groups[name] = tr("grp_fred_macro")
                self.fetched_configs[name] = {"source": "FRED", "symbol": symbol, "years": years}
                
                self.fetched_metadata[name] = {
                    tr("meta_source"): tr("src_fred_daily"),
                    tr("meta_symbol"): symbol,
                    tr("meta_datapoints_days"): len(vals),
                    tr("meta_start_date"): str(df_daily.index[0].date()),
                    tr("meta_end_date"): str(df_daily.index[-1].date()),
                    tr("meta_last_value"): f"{vals[-1]:.4f}" if not np.isnan(vals[-1]) else "N/A"
                }

            elif tr("source_coingecko") in source or "CoinGecko" in source:
                coin_id = symbol.lower()
                url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={years*365}"
                res = requests.get(url, timeout=10)
                res.raise_for_status()
                data = res.json()
                
                prices = data.get("prices", [])
                if not prices:
                    raise ValueError(tr("err_no_crypto_data", coin_id=coin_id))
                
                timestamps = [p[0] for p in prices]
                prices_vals = [p[1] for p in prices]
                s = pd.Series(prices_vals, index=pd.to_datetime(timestamps, unit='ms')).sort_index()
                df_daily = s.resample('D').asfreq()
                df_daily = df_daily.interpolate(method='linear')
                vals = df_daily.values

                name = f"Crypto:{symbol}"
                self.fetched_data[name] = vals
                self.fetched_start_dates[name] = pd.Timestamp(df_daily.index[0].date())
                self.fetched_groups[name] = tr("grp_coingecko_crypto")
                self.fetched_configs[name] = {"source": "CoinGecko", "symbol": coin_id, "years": years}
                
                self.fetched_metadata[name] = {
                    tr("meta_source"): tr("src_coingecko_daily"),
                    tr("meta_coin_id"): coin_id,
                    tr("meta_datapoints_days"): len(vals),
                    tr("meta_last_price"): f"${vals[-1]:,.2f}" if not np.isnan(vals[-1]) else "N/A"
                }

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, tr("err_fetch_title"), tr("err_fetch_msg", e=e))


class TimeSeriesModel:
    """Verwaltung von TimesFM Forecasting inkl. Versions-Fallback (v3.0/v2.5 -> v1) und GPU/CPU-Strategie."""
    def __init__(self):
        self.tfm = None
        self.api_version = None
        self.device_used = None
        self._cuda_downgrade_attempted = False
        self.init_timesfm()

    def init_timesfm(self, force_cpu: bool = False):
        if not HAS_TIMESFM and not HAS_TIMESFM3:
            return

        devices = ["cpu"] if force_cpu else ["cuda", "cpu"]

        # 0. Versuch: TimesFM 3.0 (aktuelle Hauptversion seit August 2026), eigenes
        # Modul 'timesfm3' mit komplett neuer API (TimesFM3Evaluator/ModelConfig,
        # .predict_batch(...) statt .forecast(...)). Achtung: Die 3.0-Gewichte stehen
        # unter der nicht-kommerziellen Lizenz 'timesfm-non-commercial-license-v1.0' -
        # für produktiven/kommerziellen Einsatz ggf. bei Version 2.5 bleiben.
        if HAS_TIMESFM3:
            for device_target in devices:
                try:
                    import torch
                    if device_target == "cuda" and not torch.cuda.is_available():
                        continue

                    config = timesfm3.ModelConfig(
                        checkpoint_path="google/timesfm-3.0-pytorch",
                        per_core_batch_size=32,
                        device=device_target,
                    )
                    self.tfm = timesfm3.TimesFM3Evaluator(config)
                    self.api_version = "v3.0"
                    self.device_used = device_target
                    print(f"TimesFM (v3.0) erfolgreich initialisiert (Device: {device_target}).")
                    return
                except Exception as e:
                    print(f"TimesFM v3.0 Init mit Device '{device_target}' fehlgeschlagen: {e}")
                    self.tfm = None

        if not HAS_TIMESFM:
            return

        # 1. Versuch: Ältere/archivierte TimesFM API (v2.5) mit korrektem ForecastConfig Compile
        for device_target in devices:
            try:
                import torch
                torch.set_float32_matmul_precision("high")
                
                if device_target == "cuda" and not torch.cuda.is_available():
                    continue

                if hasattr(timesfm, 'TimesFM_2p5_200M_torch'):
                    self.tfm = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
                        "google/timesfm-2.5-200m-pytorch"
                    )
                elif hasattr(timesfm, 'TimesFm'):
                    self.tfm = timesfm.TimesFm(checkpoint=timesfm.TimesFmCheckpoint(huggingface_repo_id="google/timesfm-2.5-200m-pytorch"))

                if self.tfm is not None:
                    if hasattr(self.tfm, 'compile'):
                        if hasattr(timesfm, 'ForecastConfig'):
                            self.tfm.compile(timesfm.ForecastConfig(max_context=1024, max_horizon=365))
                        else:
                            self.tfm.compile(backend=device_target)
                    self.api_version = "v2.5"
                    self.device_used = device_target
                    print(f"TimesFM (v2.5) erfolgreich initialisiert und kompiliert (Device: {device_target}).")
                    return
            except Exception as e:
                print(f"TimesFM v2.5 Init mit Device '{device_target}' fehlgeschlagen: {e}")

        # 2. Versuch (Failback): Ältere TimesFM v1 API mit TimesFmHparams
        backends = ["cpu"] if force_cpu else ["gpu", "cpu"]
        for backend in backends:
            try:
                if backend == "gpu":
                    import torch
                    if not torch.cuda.is_available():
                        continue

                hparams = timesfm.TimesFmHparams(
                    backend=backend,
                    per_core_batch_size=32,
                    horizon_len=128,
                )
                # Hinweis: "google/timesfm-1.0-200m" (ohne Suffix) ist das JAX/PAX-
                # Checkpoint. Da wir hier mit torch.cuda arbeiten und ein PyTorch-
                # Backend voraussetzen, muss das PyTorch-Checkpoint verwendet werden.
                checkpoint = timesfm.TimesFmCheckpoint(
                    huggingface_repo_id="google/timesfm-1.0-200m-pytorch"
                )
                
                if hasattr(timesfm, 'TimesFm'):
                    self.tfm = timesfm.TimesFm(hparams=hparams, checkpoint=checkpoint)
                elif hasattr(timesfm, 'TimesFM'):
                    self.tfm = timesfm.TimesFM(hparams=hparams, checkpoint=checkpoint)

                if self.tfm is not None:
                    self.api_version = "v1"
                    self.device_used = "cuda" if backend == "gpu" else "cpu"
                    print(f"TimesFM (v1 Fallback) erfolgreich mit Backend '{backend}' initialisiert.")
                    return
            except Exception as e:
                print(f"TimesFM v1 Fallback mit Backend '{backend}' fehlgeschlagen: {e}")
                self.tfm = None

    def _is_cuda_error(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        return "cuda" in msg or "nvrtc" in msg or "jit compiler" in msg or "ptx" in msg

    def _downgrade_to_cpu_and_retry(self) -> bool:
        """Wird aufgerufen, wenn eine Inferenz mit einem CUDA/JIT-Fehler (z.B.
        'PTX JIT compiler library not found') fehlschlägt, obwohl die Initialisierung
        selbst erfolgreich war (der Fehler tritt oft erst beim ersten echten Forward-Pass
        auf, da CUDA-Kernel lazy kompiliert werden). Statt dauerhaft in die simple
        statistische Heuristik zu fallen, wird TimesFM einmalig neu und diesmal
        ausschließlich auf der CPU initialisiert - langsamer, aber weiterhin das
        echte Modell. Gibt True zurück, wenn danach ein Modell verfügbar ist."""
        if self._cuda_downgrade_attempted:
            return self.tfm is not None
        self._cuda_downgrade_attempted = True
        print("CUDA/JIT-Fehler erkannt — initialisiere TimesFM neu, diesmal nur auf der CPU...")
        self.tfm = None
        self.api_version = None
        self.init_timesfm(force_cpu=True)
        return self.tfm is not None

    def method_label(self) -> str:
        """Menschlich lesbare Bezeichnung der aktuell tatsächlich verwendeten
        Prognose-Methode, z.B. 'TimesFM v2.5 (GPU)' oder 'Statistischer Fallback'."""
        if self.tfm is None:
            return tr("method_statistical_fallback")
        device_label = "GPU" if self.device_used == "cuda" else "CPU"
        return f"TimesFM {self.api_version} ({device_label})"

    def _clean_and_interpolate_series(self, values: np.ndarray) -> np.ndarray:
        if len(values) == 0:
            return values
        s = pd.Series(values)
        return s.interpolate(method='linear').bfill().ffill().values

    def forecast_univariate(self, values: np.ndarray, forecast_horizon: int) -> np.ndarray:
        clean_vals = self._clean_and_interpolate_series(values)
        n = len(clean_vals)
        if n == 0 or np.all(np.isnan(clean_vals)):
            return np.zeros(forecast_horizon)

        if self.tfm is not None:
            try:
                if self.api_version == "v3.0":
                    # TimesFM 3.0: forecaster.predict_batch(contexts, horizon=..., ...)
                    # gibt eine Liste von Ergebnisobjekten mit .forecast (Shape (horizon,))
                    outputs = list(self.tfm.predict_batch(
                        [clean_vals], horizon=forecast_horizon, return_quantiles=False
                    ))
                    if len(outputs) > 0:
                        return np.array(outputs[0].forecast[:forecast_horizon])
                elif self.api_version == "v2.5":
                    point_forecast, _ = self.tfm.forecast(horizon=forecast_horizon, inputs=[clean_vals])
                    if len(point_forecast) > 0:
                        step_forecast = point_forecast[0]
                        return np.array(step_forecast[:forecast_horizon])
                else:
                    # v1 Fallback: horizon_len des Modells ist fix (siehe TimesFmHparams),
                    # daher iterativ in Blöcken vorhersagen, bis forecast_horizon erreicht ist.
                    curr_history = clean_vals.copy()
                    predictions = []
                    remaining = forecast_horizon
                    while remaining > 0:
                        point_forecast, _ = self.tfm.forecast([curr_history], freq=[0])
                        step_forecast = point_forecast[0]
                        take = min(remaining, len(step_forecast))
                        predictions.extend(step_forecast[:take])
                        curr_history = np.append(curr_history, step_forecast[:take])
                        remaining -= take
                    return np.array(predictions[:forecast_horizon])
            except Exception as e:
                print(f"TimesFM Ausführungsfehler: {e}")
                if self.device_used == "cuda" and self._is_cuda_error(e):
                    if self._downgrade_to_cpu_and_retry():
                        return self.forecast_univariate(values, forecast_horizon)

        # Statistischer Fallback falls Modell fehlschlägt
        detrended = clean_vals - np.mean(clean_vals)
        last_val = clean_vals[-1]
        lookback = min(n, 30)
        mean_val = np.mean(clean_vals[-lookback:])
        decay = np.exp(-np.linspace(0, 1.5, forecast_horizon))
        return last_val * decay + mean_val * (1 - decay)

    def forecast_with_covariates(self, target_values: np.ndarray, covariate_extended_list: list, forecast_horizon: int) -> np.ndarray:
        clean_target = self._clean_and_interpolate_series(target_values)
        if len(clean_target) == 0:
            return np.zeros(forecast_horizon)

        base_forecast = self.forecast_univariate(clean_target, forecast_horizon)

        if covariate_extended_list:
            cov_influences = np.zeros(forecast_horizon)
            t_steps = np.arange(1, forecast_horizon + 1)
            damped_trend = 1.0 - np.exp(-t_steps / 30.0)

            for cov_ext in covariate_extended_list:
                clean_cov = self._clean_and_interpolate_series(cov_ext)
                if len(clean_cov) > 5 and len(clean_target) > 5:
                    min_len = min(len(clean_target), len(clean_cov))
                    y_diff = np.diff(clean_target[-min_len:])
                    x_diff = np.diff(clean_cov[-min_len:])
                    
                    var_x = np.var(x_diff)
                    if var_x > 1e-8:
                        beta = np.cov(x_diff, y_diff)[0, 1] / var_x
                        cov_trend = np.mean(x_diff[-10:]) if len(x_diff) >= 10 else 0
                        cov_influences += beta * cov_trend * damped_trend * 10.0

            return base_forecast + cov_influences
        else:
            return base_forecast


class SingleTimeSeriesCanvas(FigureCanvas):
    """Plot Canvas für EINE einzelne Zeitreihe mit rot schraffierten fehlenden Daten
    (nicht nur führende, sondern auch innere Lücken - siehe 'was_missing' in
    generate_full_series)."""
    def __init__(self, df: pd.DataFrame, parent=None):
        fig = Figure(figsize=(8, 0.78), dpi=100)
        fig.patch.set_alpha(0.0)

        super().__init__(fig)
        self.setParent(parent)

        self.setFixedHeight(78)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.ax = fig.add_subplot(111)
        self.ax.patch.set_alpha(0.0)

        self.df = df
        
        fig.subplots_adjust(left=0.01, right=0.99, top=0.90, bottom=0.38)

        self.ax.yaxis.set_visible(False)
        self.ax.spines['left'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['bottom'].set_alpha(0.4)

        valid_vals = df['value'].dropna()
        if not valid_vals.empty:
            val_min = valid_vals.min()
            val_max = valid_vals.max()
        else:
            val_min, val_max = 0.0, 1.0

        rng = (val_max - val_min) if (val_max != val_min and not np.isnan(val_max - val_min)) else 1.0

        def scale_val(v):
            return ((v - val_min) / rng) * 0.8 + 0.1

        hist_df = df[df['type'] == 'history']
        forecast_df = df[df['type'] == 'forecast']

        today = pd.Timestamp(datetime.date.today())
        # 'was_missing' hält den ursprünglichen NaN-Status vor der linearen
        # Interpolation fest (siehe generate_full_series) - nur so werden auch innere,
        # später glattgezogene Lücken korrekt rot schraffiert und nicht nur Lücken am
        # Rand der Serie. Fallback auf value.isna() für den unwahrscheinlichen Fall,
        # dass 'was_missing' fehlt (z.B. älterer Cache-Eintrag).
        if 'was_missing' in df.columns:
            was_missing = df['was_missing'].fillna(True).astype(bool)
        else:
            was_missing = df['value'].isna()
        # Keine Einschränkung auf "<= today" mehr: was_missing ist für jeden Tag, den
        # der Forecast tatsächlich gefüllt hat, bereits korrekt auf False gesetzt
        # (siehe generate_full_series) - unabhängig vom Datum. Würde man hier
        # zusätzlich auf "<= today" filtern, blieben Tage OHNE Forecast-Abdeckung
        # (z.B. falls ein Modell weniger Werte liefert als angefordert) in der
        # Zukunft unschraffiert und damit als leere, nicht als fehlend erkennbare
        # Lücke stehen.
        hist_nan_mask = was_missing
        if hist_nan_mask.any():
            nan_indices = np.where(hist_nan_mask.values)[0]
            splits = np.where(np.diff(nan_indices) > 1)[0] + 1
            chunks = np.split(nan_indices, splits)
            for chunk in chunks:
                start_dt = df.index[chunk[0]]
                # +1 Tag ans Ende: axvspan zeichnet ein halboffenes Intervall
                # [start, end). Ohne den Zuschlag würde bei mehrtägigen Lücken der
                # letzte fehlende Tag optisch nicht seine volle Breite bekommen
                # (nur beim vorherigen Sonderfall für 1-Tages-Lücken war das korrigiert).
                end_dt = df.index[chunk[-1]] + pd.Timedelta(days=1)
                self.ax.axvspan(
                    start_dt, end_dt,
                    facecolor='red', alpha=0.25, hatch='//', edgecolor='red', linewidth=0
                )

        if not hist_df.empty:
            h_vals = hist_df['value'].dropna()
            if len(h_vals) > 0:
                med_val = np.median(h_vals)
                q25_val = np.percentile(h_vals, 25)
                q75_val = np.percentile(h_vals, 75)

                x_s, x_e = df.index[0], df.index[-1]
                self.ax.hlines(scale_val(med_val), x_s, x_e, color='#2ca02c', linestyle='-', linewidth=0.9, alpha=0.7)
                self.ax.hlines(scale_val(q25_val), x_s, x_e, color='#2ca02c', linestyle='--', linewidth=0.8, alpha=0.6)
                self.ax.hlines(scale_val(q75_val), x_s, x_e, color='#2ca02c', linestyle='--', linewidth=0.8, alpha=0.6)

            self.ax.plot(hist_df.index, scale_val(hist_df['value']), color='#1f77b4', linewidth=1.2)

        if not forecast_df.empty:
            if not hist_df.empty and not hist_df['value'].empty:
                last_valid_hist = hist_df['value'].dropna()
                if not last_valid_hist.empty:
                    connect_x = [last_valid_hist.index[-1], forecast_df.index[0]]
                    connect_y = [scale_val(last_valid_hist.iloc[-1]), scale_val(forecast_df['value'].iloc[0])]
                    self.ax.plot(connect_x, connect_y, color='#ff7f0e', linestyle='--', linewidth=1.2)

            self.ax.plot(forecast_df.index, scale_val(forecast_df['value']), color='#ff7f0e', linestyle='--', linewidth=1.2)

        # Bereich VOR bzw. NACH dem eigentlichen Datenzeitraum dieser Serie ebenfalls
        # rot schraffieren. Notwendig, weil beim Zoomen/Scrollen (apply_zoom_and_scroll)
        # ein GEMEINSAMER Zeitbereich über ALLE Serien hinweg gesetzt wird (siehe
        # get_global_date_range: min_d = früheste Startdatum unter allen Serien).
        # Serien mit "jüngerer" (kürzerer) Historie als andere Serien in der Gruppe
        # zeigten den fehlenden älteren Zeitraum bisher als leere, unschraffierte
        # Fläche, weil für diese Daten in df.index schlicht keine Zeilen existieren.
        # axvspan wird unabhängig vom aktuell sichtbaren xlim in Datenkoordinaten
        # gezeichnet und von matplotlib automatisch auf die jeweilige Ansicht geclippt,
        # daher genügt ein einmalig hier gesetzter, großzügig weit reichender Bereich.
        # Feste Datums-Konstanten (z.B. Jahr 1900) sind hier ungeeignet: Diese App
        # lädt u.a. Erdwissenschafts-Zeitreihen (Sonnenflecken, Temperatur, CO2,
        # Bevölkerung), die bereits 1749 beginnen (siehe
        # load_all_comprehensive_earth_science_data). Der gemeinsame Zoom-Bereich
        # (get_global_date_range: frühestes Startdatum über ALLE Serien) reicht dann
        # ebenfalls bis 1749 zurück. Kürzere Serien (z.B. Finanzdaten) hatten den
        # Bereich VOR ihrer eigenen Historie bis 1900 zurück nur bis zu einer
        # willkürlichen festen Grenze schraffiert - alles davor (1749-1900) blieb
        # unschraffiert. Statt einer geratenen festen Grenze werden daher die von
        # pandas selbst garantiert darstellbaren äußersten Zeitstempel verwendet -
        # das deckt jeden möglichen Datenbereich ab, unabhängig davon, wie weit
        # zukünftige Datenquellen zurück- oder vorausreichen.
        FAR_PAST = pd.Timestamp.min
        FAR_FUTURE = pd.Timestamp.max
        if df.index[0] > FAR_PAST:
            self.ax.axvspan(
                FAR_PAST, df.index[0],
                facecolor='red', alpha=0.25, hatch='//', edgecolor='red', linewidth=0
            )
        if df.index[-1] < FAR_FUTURE:
            # +1 Tag: der letzte Eintrag in df.index (df.index[-1]) ist selbst noch
            # ein echter (ggf. prognostizierter) Datenpunkt und soll nicht vom
            # "danach"-Bereich überdeckt werden - sonst wird der letzte Forecast-Tag
            # fälschlich rot schraffiert. Gleiche [Tag, Tag+1)-Konvention wie beim
            # Lücken-Hatching weiter oben.
            self.ax.axvspan(
                df.index[-1] + pd.Timedelta(days=1), FAR_FUTURE,
                facecolor='red', alpha=0.25, hatch='//', edgecolor='red', linewidth=0
            )

        self.min_date = df.index[0]
        self.max_date = df.index[-1]
        
        self.ax.set_xlim(self.min_date, self.max_date)
        self.ax.set_ylim(-0.05, 1.05)
        self.ax.tick_params(axis='x', which='major', labelsize=8, pad=3)

    def set_x_bounds(self, start_date, end_date):
        self.ax.set_xlim(start_date, end_date)
        self.draw_idle()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title_base"))
        self.resize(1200, 780)

        self.ts_model = TimeSeriesModel()
        self._update_window_title()
        self._show_timesfm_status()
        self.raw_data = {}
        self.metadata = {}
        self.active_targets = {}
        self.series_groups = {}
        self.series_start_dates = {}
        self.series_source_configs = {}
        self.custom_empty_groups = set()
        self.group_creation_order = []
        self.forecast_days = 14
        self.canvases = []
        self.forecast_cache = {}

        self.init_ui()
        self.load_all_comprehensive_earth_science_data()

    def _update_window_title(self):
        """Zeigt im Fenstertitel die tatsächlich verwendete Prognose-Methode an
        (z.B. 'TimesFM v2.5 (GPU)', 'TimesFM v1 (CPU)' oder 'Statistischer Fallback'),
        statt der statischen Beschriftung 'TimesFM - GPU/CPU Fallback'."""
        self.setWindowTitle(tr("app_title_with_method", method=self.ts_model.method_label()))

    def _show_timesfm_status(self):
        """Zeigt sichtbar in der GUI an, ob TimesFM erfolgreich geladen wurde oder ob
        das Programm im statistischen Fallback läuft - vorher war das nur per print()
        in der Konsole sichtbar und ging leicht unbemerkt unter. Aktualisiert die
        Statuszeile bei jedem Aufruf (z.B. auch nach einem automatischen CUDA->CPU-
        Fallback), zeigt die Warn-Dialogbox aber nur einmal an, statt bei jedem
        render_all_series() erneut aufzupoppen."""
        bar = self.statusBar()
        if self.ts_model.tfm is not None:
            bar.setStyleSheet("background-color: #d4edda; color: #155724;")
            device_label = "GPU" if self.ts_model.device_used == "cuda" else "CPU"
            bar.showMessage(
                tr("status_timesfm_ok", version=self.ts_model.api_version, device=device_label)
            )
        else:
            bar.setStyleSheet("background-color: #f8d7da; color: #721c24;")
            bar.showMessage(tr("status_timesfm_fail"))
            if not getattr(self, "_timesfm_warning_shown", False):
                self._timesfm_warning_shown = True
                QMessageBox.warning(
                    self,
                    tr("warn_timesfm_title"),
                    tr("warn_timesfm_msg")
                )

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- HEADER ---
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        header_layout = QHBoxLayout(header_frame)

        self.title_label = QLabel(tr("header_title"))
        title_label = self.title_label
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.horizon_label = QLabel(tr("label_forecast_days"))
        horizon_label = self.horizon_label
        self.horizon_spinbox = QSpinBox()
        self.horizon_spinbox.setToolTip(tr("tooltip_forecast_days"))
        self.horizon_spinbox.setRange(1, 365)
        self.horizon_spinbox.setValue(self.forecast_days)
        # Ohne dies feuert valueChanged bei jedem einzelnen getippten Zeichen
        # (z.B. bei "100": erst 1, dann 10, dann 100 -> 3 Neuberechnungen). Mit
        # keyboardTracking(False) wird valueChanged nur noch ausgelöst, wenn die
        # Eingabe abgeschlossen ist (Enter/Tab/Fokusverlust) oder die Pfeiltasten/
        # das Mausrad benutzt werden.
        self.horizon_spinbox.setKeyboardTracking(False)
        self.horizon_spinbox.valueChanged.connect(self.update_forecast_horizon)
        
        header_layout.addWidget(horizon_label)
        header_layout.addWidget(self.horizon_spinbox)

        self.add_group_btn = QPushButton(tr("btn_new_group"))
        add_group_btn = self.add_group_btn
        add_group_btn.setToolTip(tr("tooltip_new_group"))
        add_group_btn.clicked.connect(self.create_new_group)
        header_layout.addWidget(add_group_btn)

        self.import_fin_btn = QPushButton(tr("btn_import_web"))
        import_fin_btn = self.import_fin_btn
        import_fin_btn.setToolTip(tr("tooltip_import_web"))
        import_fin_btn.clicked.connect(self.import_finance)
        header_layout.addWidget(import_fin_btn)

        self.import_csv_btn = QPushButton(tr("btn_import_csv"))
        import_csv_btn = self.import_csv_btn
        import_csv_btn.setToolTip(tr("tooltip_import_csv"))
        import_csv_btn.clicked.connect(self.import_csv)
        header_layout.addWidget(import_csv_btn)

        self.export_btn = QPushButton(tr("btn_export_csv"))
        export_btn = self.export_btn
        export_btn.setToolTip(tr("tooltip_export_csv"))
        export_btn.clicked.connect(self.export_series_with_forecast)
        header_layout.addWidget(export_btn)

        self.save_btn = QPushButton(tr("btn_save_project"))
        save_btn = self.save_btn
        save_btn.clicked.connect(self.save_project)
        header_layout.addWidget(save_btn)

        self.load_btn = QPushButton(tr("btn_load_project"))
        load_btn = self.load_btn
        load_btn.clicked.connect(self.load_project)
        header_layout.addWidget(load_btn)

        # --- SPRACHUMSCHALTER ---
        # Übersetzt sofort die gesamte Bedienoberfläche (Buttons, Labels,
        # Tooltips, Dialoge, Statuszeile, Gruppenbeschriftungen). Bereits
        # geladene Zeitreihen-/Gruppennamen sind Nutzdaten und behalten die
        # Sprache bei, in der sie erzeugt wurden (siehe README.md).
        self.lang_label = QLabel(tr("label_language"))
        header_layout.addWidget(self.lang_label)

        self.lang_combo = QComboBox()
        self._lang_codes = list(LANGUAGES.keys())
        for code in self._lang_codes:
            self.lang_combo.addItem(LANGUAGES[code], userData=code)
        self.lang_combo.setCurrentIndex(self._lang_codes.index(get_language()))
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        header_layout.addWidget(self.lang_combo)

        main_layout.addWidget(header_frame)

        # --- ZOOM & SCROLL SLIDER BAR ---
        slider_frame = QFrame()
        slider_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 4px;")
        slider_layout = QHBoxLayout(slider_frame)
        slider_layout.setContentsMargins(10, 5, 10, 5)

        self.zoom_label = QLabel(tr("label_zoom"))
        slider_layout.addWidget(self.zoom_label)
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(1, 100)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.apply_zoom_and_scroll)
        slider_layout.addWidget(self.zoom_slider)

        self.pan_label = QLabel(tr("label_pan"))
        slider_layout.addWidget(self.pan_label)
        self.scroll_slider = QSlider(Qt.Orientation.Horizontal)
        self.scroll_slider.setRange(0, 100)
        self.scroll_slider.setValue(100)
        self.scroll_slider.valueChanged.connect(self.apply_zoom_and_scroll)
        slider_layout.addWidget(self.scroll_slider)

        self.reset_zoom_btn = QPushButton(tr("btn_zoom_reset"))
        reset_zoom_btn = self.reset_zoom_btn
        reset_zoom_btn.setMaximumWidth(50)
        reset_zoom_btn.clicked.connect(self.reset_zoom)
        slider_layout.addWidget(reset_zoom_btn)

        self.zoom_data_btn = QPushButton(tr("btn_zoom_to_data"))
        zoom_data_btn = self.zoom_data_btn
        zoom_data_btn.clicked.connect(self.zoom_to_available_data)
        slider_layout.addWidget(zoom_data_btn)

        main_layout.addWidget(slider_frame)

        # --- SCROLL BEREICH ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.scroll_content = QWidget()
        self.rows_layout = QVBoxLayout(self.scroll_content)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.rows_layout.setContentsMargins(5, 5, 5, 5)
        self.rows_layout.setSpacing(10)

        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

    def on_language_changed(self, index: int):
        """Wird aufgerufen, wenn der Nutzer im Sprach-Dropdown eine andere
        Sprache wählt. Setzt die globale Sprache und aktualisiert sofort alle
        statischen Oberflächen-Texte (retranslate_ui) sowie die Statuszeile,
        den Fenstertitel und die dynamisch gerenderten Gruppen-Überschriften."""
        code = self._lang_codes[index]
        set_language(code)
        self.retranslate_ui()

    def retranslate_ui(self):
        """Aktualisiert alle dauerhaft angelegten Widgets (Buttons, Labels,
        Tooltips) auf die aktuell aktive Sprache. Dynamisch erzeugte Inhalte
        (Zeitreihen-Zeilen, Gruppen-Boxen) werden über render_all_series()
        neu aufgebaut, wodurch z.B. die Gruppen-Überschrift
        '<b>Gruppe: ...</b> (<n> Zeitreihen)' ebenfalls neu übersetzt wird."""
        self.title_label.setText(tr("header_title"))
        self.horizon_label.setText(tr("label_forecast_days"))
        self.horizon_spinbox.setToolTip(tr("tooltip_forecast_days"))
        self.add_group_btn.setText(tr("btn_new_group"))
        self.add_group_btn.setToolTip(tr("tooltip_new_group"))
        self.import_fin_btn.setText(tr("btn_import_web"))
        self.import_fin_btn.setToolTip(tr("tooltip_import_web"))
        self.import_csv_btn.setText(tr("btn_import_csv"))
        self.import_csv_btn.setToolTip(tr("tooltip_import_csv"))
        self.export_btn.setText(tr("btn_export_csv"))
        self.export_btn.setToolTip(tr("tooltip_export_csv"))
        self.save_btn.setText(tr("btn_save_project"))
        self.load_btn.setText(tr("btn_load_project"))
        self.lang_label.setText(tr("label_language"))
        self.zoom_label.setText(tr("label_zoom"))
        self.pan_label.setText(tr("label_pan"))
        self.reset_zoom_btn.setText(tr("btn_zoom_reset"))
        self.zoom_data_btn.setText(tr("btn_zoom_to_data"))

        self._update_window_title()
        self._show_timesfm_status()
        if self.raw_data:
            self.render_all_series(reset_view=False)

    def create_new_group(self):
        group_name, ok = QInputDialog.getText(
            self, tr("new_group_dialog_title"), tr("new_group_dialog_label")
        )
        if ok and group_name.strip():
            grp = group_name.strip()
            self.custom_empty_groups.add(grp)
            if grp in self.group_creation_order:
                self.group_creation_order.remove(grp)
            self.group_creation_order.insert(0, grp)
            self.render_all_series(reset_view=False)

    def reassign_series_group(self, name: str):
        existing_groups = list(set(list(self.series_groups.values()) + list(self.custom_empty_groups)))
        if not existing_groups:
            existing_groups = [tr("grp_general")]

        curr_grp = self.series_groups.get(name, tr("grp_general"))
        dialog = GroupAssignDialog(name, curr_grp, existing_groups, self)
        
        if dialog.exec():
            new_grp = dialog.selected_group
            self.series_groups[name] = new_grp
            if new_grp in self.custom_empty_groups:
                self.custom_empty_groups.remove(new_grp)
            if new_grp in self.group_creation_order:
                self.group_creation_order.remove(new_grp)
            self.group_creation_order.insert(0, new_grp)
            self.render_all_series(reset_view=False)

    def update_series_data(self, name: str):
        config = self.series_source_configs.get(name, None)
        if not config:
            return

        source = config.get("source")
        symbol = config.get("symbol")
        years = config.get("years", 30)
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=years * 365)

        try:
            if source == "Yahoo":
                if not HAS_YFINANCE:
                    raise ImportError(tr("err_yfinance_not_installed"))
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date)
                if df.empty:
                    raise ValueError(tr("err_no_current_data"))
                raw_series = df['Close']
                df_full = raw_series.resample('D').asfreq()
                df_full = df_full.interpolate(method='linear')
                vals = df_full.values

                self.raw_data[name] = vals
                self.series_start_dates[name] = pd.Timestamp(df_full.index[0].date())
                
                info = ticker.info if hasattr(ticker, 'info') else {}
                self.metadata[name] = {
                    tr("meta_source"): tr("src_yahoo_finance_updated"),
                    tr("meta_symbol"): symbol,
                    tr("meta_name"): info.get("longName", info.get("shortName", symbol)),
                    tr("meta_currency"): info.get("currency", "USD"),
                    tr("meta_datapoints"): len(vals),
                    tr("meta_last_value"): f"{vals[-1]:.2f}" if not np.isnan(vals[-1]) else "N/A"
                }

            elif source == "FRED":
                if not HAS_DATAREADER:
                    raise ImportError(tr("err_datareader_not_installed"))
                df = web.DataReader(symbol, 'fred', start_date, end_date)
                if df.empty:
                    raise ValueError(tr("err_no_fred_data_generic"))
                raw_series = df[symbol]
                df_daily = raw_series.resample('D').asfreq()
                df_daily = df_daily.interpolate(method='linear')
                vals = df_daily.values

                self.raw_data[name] = vals
                self.series_start_dates[name] = pd.Timestamp(df_daily.index[0].date())
                
                self.metadata[name] = {
                    tr("meta_source"): tr("src_fred_updated"),
                    tr("meta_symbol"): symbol,
                    tr("meta_datapoints"): len(vals),
                    tr("meta_last_value"): f"{vals[-1]:.4f}" if not np.isnan(vals[-1]) else "N/A"
                }

            elif source == "CoinGecko":
                url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days={years*365}"
                res = requests.get(url, timeout=10)
                res.raise_for_status()
                data = res.json()
                prices = data.get("prices", [])
                if not prices:
                    raise ValueError(tr("err_no_crypto_data_generic"))
                timestamps = [p[0] for p in prices]
                prices_vals = [p[1] for p in prices]
                s = pd.Series(prices_vals, index=pd.to_datetime(timestamps, unit='ms')).sort_index()
                df_daily = s.resample('D').asfreq()
                df_daily = df_daily.interpolate(method='linear')
                vals = df_daily.values

                self.raw_data[name] = vals
                self.series_start_dates[name] = pd.Timestamp(df_daily.index[0].date())
                
                self.metadata[name] = {
                    tr("meta_source"): tr("src_coingecko_updated"),
                    tr("meta_coin_id"): symbol,
                    tr("meta_datapoints"): len(vals),
                    tr("meta_last_price"): f"${vals[-1]:,.2f}" if not np.isnan(vals[-1]) else "N/A"
                }

            self.forecast_cache.clear()
            self.render_all_series(reset_view=False)
            QMessageBox.information(self, tr("success_title"), tr("update_success_msg", name=name))

        except Exception as e:
            QMessageBox.critical(self, tr("update_error_title"), tr("update_error_msg", e=e))

    def load_all_comprehensive_earth_science_data(self):
        start_date = pd.Timestamp("1749-01-01")
        today = pd.Timestamp(datetime.date.today())
        daily_index = pd.date_range(start=start_date, end=today, freq='D')
        t = np.arange(len(daily_index))
        years_float = 1749 + t / 365.25

        # 1. Sonnenflecken
        years_range = np.arange(1749, today.year + 1)
        ty = years_range - 1749
        cycle_11 = np.sin(2 * np.pi * ty / 11.0 - 1.2)
        cycle_harmonic = 0.3 * np.sin(4 * np.pi * ty / 11.0)
        gleissberg = 0.5 * np.sin(2 * np.pi * ty / 90.0) + 1.2
        annual_sunspots = (cycle_11 + cycle_harmonic + 1.2)**2 * 45.0 * gleissberg + np.random.normal(0, 2, len(years_range))
        annual_sunspots = np.clip(annual_sunspots, 0, None)
        df_ann = pd.DataFrame({'value': annual_sunspots}, index=pd.to_datetime(years_range, format='%Y'))
        df_sun = df_ann.reindex(pd.to_datetime(years_range, format='%Y').union(daily_index)).sort_index()
        df_sun['value'] = df_sun['value'].interpolate(method='linear')
        sun_vals = df_sun.loc[daily_index]['value'].values

        s_name = tr("series_sunspots")
        self.raw_data[s_name] = sun_vals
        self.series_start_dates[s_name] = start_date
        self.active_targets[s_name] = False
        self.series_groups[s_name] = tr("grp_astronomy_solar")
        self.metadata[s_name] = {tr("meta_source"): tr("meta_silso"), tr("meta_datapoints"): len(sun_vals)}

        # 2. Mondzyklus
        moon_vals = np.sin(2 * np.pi * t / 29.53059) * 50 + 50
        m_name = tr("series_moon_cycle")
        self.raw_data[m_name] = moon_vals
        self.series_start_dates[m_name] = start_date
        self.active_targets[m_name] = False
        self.series_groups[m_name] = tr("grp_astronomy_solar")
        self.metadata[m_name] = {tr("meta_source"): tr("meta_astro_model"), tr("meta_datapoints"): len(moon_vals)}

        # 3. El Niño / ENSO
        enso_vals = 2.5 * np.sin(2 * np.pi * t / 1460.0) + 1.2 * np.sin(2 * np.pi * t / 2190.0) + np.random.normal(0, 0.4, len(t))
        e_name = tr("series_enso")
        self.raw_data[e_name] = enso_vals
        self.series_start_dates[e_name] = start_date
        self.active_targets[e_name] = False
        self.series_groups[e_name] = tr("grp_climate_atmosphere")
        self.metadata[e_name] = {tr("meta_source"): tr("meta_enso_model"), tr("meta_datapoints"): len(enso_vals)}

        # 4. Oberflächentemperatur-Anomalie (°C)
        base_temp = -0.3 + 0.002 * (years_float - 1749) + 0.7 * (1.0 / (1.0 + np.exp(-0.04 * (years_float - 1970))))
        temp_vals = base_temp + 0.12 * np.sin(2 * np.pi * t / (365.25 * 11.0)) + np.random.normal(0, 0.04, len(t))
        t_name = tr("series_temp_anomaly")
        self.raw_data[t_name] = temp_vals
        self.series_start_dates[t_name] = start_date
        self.active_targets[t_name] = False
        self.series_groups[t_name] = tr("grp_climate_atmosphere")
        self.metadata[t_name] = {tr("meta_source"): tr("meta_temp_reconstruction"), tr("meta_datapoints"): len(temp_vals)}

        # 5. CO₂-Gehalt (ppm)
        co2_vals = 280.0 * np.exp(0.0018 * (years_float - 1749)) + 2.5 * np.sin(2 * np.pi * t / 365.25) + np.random.normal(0, 0.3, len(t))
        co2_name = tr("series_co2")
        self.raw_data[co2_name] = co2_vals
        self.series_start_dates[co2_name] = start_date
        self.active_targets[co2_name] = False
        self.series_groups[co2_name] = tr("grp_climate_atmosphere")
        self.metadata[co2_name] = {tr("meta_source"): tr("meta_co2_reconstruction"), tr("meta_datapoints"): len(co2_vals)}

        # 6. Bevölkerungsanzahl (Milliarden)
        pop_vals = 0.79 * np.exp(0.009 * (years_float - 1750))
        p_name = tr("series_population")
        self.raw_data[p_name] = pop_vals
        self.series_start_dates[p_name] = start_date
        self.active_targets[p_name] = False
        self.series_groups[p_name] = tr("grp_demographics_society")
        self.metadata[p_name] = {tr("meta_source"): tr("meta_un_demographic"), tr("meta_datapoints"): len(pop_vals)}

        # 7. Vulkanausbrüche
        volcano_vals = np.zeros(len(t))
        np.random.seed(123)
        spike_indices = np.random.choice(t, size=20)
        for idx in spike_indices:
            if idx < len(t) - 150:
                dur = np.random.randint(45, 180)
                amp = np.random.uniform(3.0, 9.0)
                volcano_vals[idx:idx+dur] += amp * np.exp(-np.linspace(0, 3, dur))
        v_name = tr("series_volcano")
        self.raw_data[v_name] = volcano_vals
        self.series_start_dates[v_name] = start_date
        self.active_targets[v_name] = False
        self.series_groups[v_name] = tr("grp_geophysics_nature")
        self.metadata[v_name] = {tr("meta_source"): tr("meta_volcano_catalog"), tr("meta_datapoints"): len(volcano_vals)}

        # 8. Erdbeben
        np.random.seed(456)
        earthquake_vals = np.random.exponential(scale=1.2, size=len(t))
        eq_spikes = np.random.choice(t, size=40)
        for idx in eq_spikes:
            if idx < len(t) - 50:
                dur = np.random.randint(5, 25)
                amp = np.random.uniform(8.0, 25.0)
                earthquake_vals[idx:idx+dur] += amp * np.exp(-np.linspace(0, 2.5, dur))
        eq_name = tr("series_earthquake")
        self.raw_data[eq_name] = earthquake_vals
        self.series_start_dates[eq_name] = start_date
        self.active_targets[eq_name] = False
        self.series_groups[eq_name] = tr("grp_geophysics_nature")
        self.metadata[eq_name] = {tr("meta_source"): tr("meta_seismic_index"), tr("meta_datapoints"): len(earthquake_vals)}

        self.group_creation_order = [
            tr("grp_geophysics_nature"), tr("grp_climate_atmosphere"),
            tr("grp_demographics_society"), tr("grp_astronomy_solar"),
        ]

    def delete_series(self, name: str):
        if name in self.raw_data:
            del self.raw_data[name]
        if name in self.metadata:
            del self.metadata[name]
        if name in self.active_targets:
            del self.active_targets[name]
        if name in self.series_groups:
            del self.series_groups[name]
        if name in self.series_start_dates:
            del self.series_start_dates[name]
        if name in self.series_source_configs:
            del self.series_source_configs[name]
        self.forecast_cache.clear()
        self.render_all_series(reset_view=False)

    def on_checkbox_changed(self, name, state):
        self.active_targets[name] = (state == Qt.CheckState.Checked.value or state == 2)
        self.forecast_cache.clear()
        self.render_all_series(reset_view=False)

    def on_group_checkbox_changed(self, group_series_names, state):
        check_bool = (state == Qt.CheckState.Checked.value or state == 2)
        for s_name in group_series_names:
            self.active_targets[s_name] = check_bool
        self.forecast_cache.clear()
        self.render_all_series(reset_view=False)

    def get_global_date_range(self):
        today = pd.Timestamp(datetime.date.today())
        if not self.raw_data:
            return today, today + pd.Timedelta(days=self.forecast_days)
        
        min_d = today
        for name, vals in self.raw_data.items():
            s_start = self.get_series_start_date(name, vals)
            if s_start < min_d:
                min_d = s_start
                
        max_d = today + pd.Timedelta(days=self.forecast_days)
        return min_d, max_d

    def apply_zoom_and_scroll(self):
        if not self.canvases:
            return

        min_d, max_d = self.get_global_date_range()
        total_days = (max_d - min_d).days

        zoom_pct = self.zoom_slider.value() / 100.0
        visible_days = max(7, int(total_days * zoom_pct))

        pos_pct = self.scroll_slider.value() / 100.0
        max_start_offset = total_days - visible_days
        start_offset = int(max_start_offset * pos_pct)

        new_start = min_d + pd.Timedelta(days=start_offset)
        new_end = new_start + pd.Timedelta(days=visible_days)

        for cv in self.canvases:
            cv.set_x_bounds(new_start, new_end)

    def reset_zoom(self):
        self.zoom_slider.setValue(100)
        self.scroll_slider.setValue(100)

    def zoom_to_available_data(self):
        if not self.canvases or not self.raw_data:
            return

        min_hist_date, max_date = self.get_global_date_range()
        today = pd.Timestamp(datetime.date.today())
        
        for name in self.raw_data.keys():
            s_start = self.series_start_dates.get(name, today - pd.Timedelta(days=len(self.raw_data[name])))
            if s_start < min_hist_date:
                min_hist_date = s_start

        global_min, global_max = self.get_global_date_range()
        total_span = (global_max - global_min).days
        avail_span = (max_date - min_hist_date).days

        if total_span > 0:
            zoom_val = max(1, min(100, int((avail_span / total_span) * 100)))
            self.zoom_slider.setValue(zoom_val)
            self.scroll_slider.setValue(100)

    def update_forecast_horizon(self):
        self.forecast_days = self.horizon_spinbox.value()
        self.forecast_cache.clear()
        self.render_all_series(reset_view=False)

    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("csv_dialog_title"), "", tr("csv_filter")
        )
        if file_path:
            try:
                df = pd.read_csv(file_path)
                filename = os.path.basename(file_path)
                
                date_col = None
                for col in df.columns:
                    if col.lower() in ['date', 'datum', 'time', 'timestamp', 'jahr', 'year']:
                        date_col = col
                        break

                today = pd.Timestamp(datetime.date.today())
                if date_col:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                    df = df.dropna(subset=[date_col]).sort_values(by=date_col)
                    df.set_index(date_col, inplace=True)
                    df = df.resample('D').asfreq()
                    for col in df.select_dtypes(include=[np.number]).columns:
                        df[col] = df[col].interpolate(method='linear')
                    start_date = pd.Timestamp(df.index[0].date())
                else:
                    start_date = today - pd.Timedelta(days=len(df))
                    df.index = pd.date_range(start=start_date, periods=len(df), freq='D')

                numeric_cols = df.select_dtypes(include=[np.number]).columns
                
                group_name = f"{tr('src_local_csv')}: {filename}"
                if group_name in self.group_creation_order:
                    self.group_creation_order.remove(group_name)
                self.group_creation_order.insert(0, group_name)

                for col in numeric_cols:
                    series_name = f"{filename} - {col}"
                    vals = df[col].values
                    self.raw_data[series_name] = vals
                    self.series_start_dates[series_name] = start_date
                    self.active_targets[series_name] = False
                    self.series_groups[series_name] = group_name
                    self.metadata[series_name] = {
                        tr("meta_source"): tr("src_local_csv"),
                        tr("meta_filename"): filename,
                        tr("meta_column"): col,
                        tr("meta_datapoints"): len(vals),
                        tr("meta_start_date"): str(start_date.date()),
                        tr("meta_min_value"): f"{np.nanmin(vals):.2f}" if len(vals) > 0 and not np.all(np.isnan(vals)) else "N/A",
                        tr("meta_max_value"): f"{np.nanmax(vals):.2f}" if len(vals) > 0 and not np.all(np.isnan(vals)) else "N/A"
                    }

                self.forecast_cache.clear()
                self.render_all_series(reset_view=False)
            except Exception as e:
                QMessageBox.critical(self, tr("err_generic_title"), tr("err_csv_load_msg", e=e))

    def import_finance(self):
        dialog = FinanceImportDialog(self)
        if dialog.exec():
            for name, vals in dialog.fetched_data.items():
                self.raw_data[name] = vals
                self.active_targets[name] = False
                grp = dialog.fetched_groups.get(name, tr("grp_finance_data"))
                self.series_groups[name] = grp
                
                if grp in self.group_creation_order:
                    self.group_creation_order.remove(grp)
                self.group_creation_order.insert(0, grp)

                if name in dialog.fetched_start_dates:
                    self.series_start_dates[name] = dialog.fetched_start_dates[name]
                if name in dialog.fetched_configs:
                    self.series_source_configs[name] = dialog.fetched_configs[name]

            for name, meta in dialog.fetched_metadata.items():
                self.metadata[name] = meta

            self.forecast_cache.clear()
            self.render_all_series(reset_view=False)

    def get_series_start_date(self, name: str, raw_values: np.ndarray) -> pd.Timestamp:
        today = pd.Timestamp(datetime.date.today())
        if name in self.series_start_dates:
            return self.series_start_dates[name]
        return today - pd.Timedelta(days=len(raw_values))

    def generate_full_series(self, target_name: str, raw_values: np.ndarray, covariate_extended_list: list) -> pd.DataFrame:
        is_target = self.active_targets.get(target_name, False)
        val_sum = float(np.nansum(raw_values)) if len(raw_values) > 0 else 0.0
        nan_count = int(np.isnan(raw_values).sum())
        cache_key = f"{target_name}_{len(raw_values)}_{val_sum:.4f}_{nan_count}_{self.forecast_days}_{is_target}"

        if cache_key in self.forecast_cache:
            return self.forecast_cache[cache_key]

        today = pd.Timestamp(datetime.date.today())
        s_start = self.get_series_start_date(target_name, raw_values)
        end_date = today + pd.Timedelta(days=self.forecast_days)

        full_index = pd.date_range(start=s_start, end=end_date, freq='D')
        df = pd.DataFrame(index=full_index)
        df['value'] = np.nan
        df['type'] = 'missing'
        # Standardmäßig gilt jeder Punkt als "fehlend", bis unten für tatsächlich
        # gelieferte Rohdaten das Gegenteil festgestellt wird.
        df['was_missing'] = True

        n_vals = len(raw_values)
        if n_vals > 0:
            assign_len = min(n_vals, len(full_index))
            assigned_vals = raw_values[:assign_len]
            
            temp_series = pd.Series(assigned_vals, index=full_index[:assign_len])

            # WICHTIG: Den NaN-Status VOR der Interpolation sichern. interpolate()
            # füllt innere Lücken (zwischen zwei echten Werten) glatt auf, sodass sie
            # in 'value' danach nicht mehr als fehlend erkennbar sind - nur Lücken am
            # Rand (vor dem ersten bzw. nach dem letzten echten Wert) blieben bisher
            # NaN. Dadurch wurden gerade die häufigsten Datenlücken (mitten in der
            # Zeitreihe) nie rot schraffiert. 'was_missing' hält den echten,
            # ursprünglichen Lückenstatus unabhängig von der Interpolation fest.
            df.loc[full_index[:assign_len], 'was_missing'] = temp_series.isna().values

            # limit_area='inside' ist entscheidend: pandas' interpolate() würde
            # standardmäßig nicht nur innere Lücken füllen, sondern nachlaufende
            # NaN-Lücken (fehlende neueste Tage, z.B. bei veralteter Datenquelle)
            # lautlos mit dem letzten bekannten Wert flach fortschreiben
            # (Extrapolation statt Interpolation!). Das hätte last_valid_index()
            # unten dazu gebracht, eine künstlich verlängerte Position statt des
            # echten letzten Datenpunkts zu finden - und dadurch den Forecast-Anker
            # sowie die Rot-Schraffur-Grenze systematisch nach rechts verschoben.
            interpolated_series = temp_series.interpolate(method='linear', limit_area='inside')
            
            df.loc[full_index[:assign_len], 'value'] = interpolated_series.values
            
            for i in range(assign_len):
                dt = full_index[i]
                if dt <= today:
                    val = df.iloc[i]['value']
                    if pd.isna(val):
                        df.iloc[i, df.columns.get_loc('type')] = 'missing'
                    else:
                        df.iloc[i, df.columns.get_loc('type')] = 'history'

            clean_raw = interpolated_series.dropna().values
            if len(clean_raw) > 0:
                last_valid_ts = interpolated_series.last_valid_index()
                last_valid_loc = (
                    df.index.get_loc(last_valid_ts) if last_valid_ts is not None else (assign_len - 1)
                )

                if today in df.index:
                    today_loc = df.index.get_loc(today)
                else:
                    today_loc = len(df) - self.forecast_days - 1

                # Falls die Rohdaten nicht bis "heute" reichen (z.B. verzögerte/
                # veraltete Datenquelle), wurde diese Lücke bisher als "fehlend" rot
                # schraffiert und dann unvermittelt vom Forecast gefolgt - das ergab
                # den störenden roten Bereich zwischen letztem historischen
                # Datenpunkt und Forecast-Beginn. Jetzt wird dieser "Nachhol"-
                # Zeitraum nahtlos mitprognostiziert: Der Forecast startet direkt
                # nach dem letzten echten (bzw. interpolierten) Datenpunkt und
                # deckt sowohl die Tage bis heute als auch die gewünschten
                # self.forecast_days Tage in die Zukunft ab.
                catchup_days = max(0, today_loc - last_valid_loc)
                forecast_horizon_total = catchup_days + self.forecast_days

                if is_target:
                    forecast_vals = self.ts_model.forecast_with_covariates(
                        clean_raw, covariate_extended_list, forecast_horizon_total
                    )
                else:
                    forecast_vals = self.ts_model.forecast_univariate(
                        clean_raw, forecast_horizon_total
                    )

                forecast_start_idx = last_valid_loc + 1
                forecast_end_idx = min(len(df), forecast_start_idx + len(forecast_vals))
                f_len = forecast_end_idx - forecast_start_idx
                
                df.iloc[forecast_start_idx:forecast_end_idx, df.columns.get_loc('value')] = forecast_vals[:f_len]
                df.iloc[forecast_start_idx:forecast_end_idx, df.columns.get_loc('type')] = 'forecast'
                # Dieser Bereich trägt jetzt eine (prognostizierte) Werteschätzung
                # statt einer echten Lücke und darf daher nicht mehr rot schraffiert
                # werden (sonst würde die rote Schraffur die orange Forecast-Linie
                # überlagern).
                df.iloc[forecast_start_idx:forecast_end_idx, df.columns.get_loc('was_missing')] = False

        self.forecast_cache[cache_key] = df
        return df

    def _get_sorted_group_structure(self):
        """Liefert (sorted_groups, grouped_structure) in exakt der Reihenfolge, in der
        Gruppen/Zeitreihen auch in der Oberfläche angezeigt werden (oberste Gruppe
        zuerst, darin die Zeitreihen in Einfüge-Reihenfolge von raw_data). Wird sowohl
        vom Rendern als auch vom Export genutzt, damit beide konsistent bleiben."""
        unordered_groups = set(self.custom_empty_groups)
        for name in self.raw_data.keys():
            unordered_groups.add(self.series_groups.get(name, "Allgemein"))

        sorted_groups = []
        for g in self.group_creation_order:
            if g in unordered_groups:
                sorted_groups.append(g)
                unordered_groups.remove(g)
        for g in sorted(list(unordered_groups)):
            sorted_groups.append(g)

        grouped_structure = {g: [] for g in sorted_groups}
        for name in self.raw_data.keys():
            grp = self.series_groups.get(name, "Allgemein")
            grouped_structure[grp].append(name)

        return sorted_groups, grouped_structure

    def render_all_series(self, reset_view=False):
        self.setUpdatesEnabled(False)
        try:
            total_items = len(self.raw_data)
            progress = QProgressDialog(tr("progress_computing"), tr("btn_cancel"), 0, max(1, total_items), self)
            progress.setWindowTitle(tr("progress_title"))
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(200)
            progress.setValue(0)

            for cv in self.canvases:
                if hasattr(cv, 'figure') and cv.figure:
                    plt.close(cv.figure)

            while self.rows_layout.count():
                child = self.rows_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            self.canvases.clear()

            sorted_groups, grouped_structure = self._get_sorted_group_structure()

            covariate_extended_list = []
            for name, vals in self.raw_data.items():
                if not self.active_targets.get(name, False):
                    clean_v = vals[~np.isnan(vals)]
                    if len(clean_v) > 0:
                        ext_fc = self.ts_model.forecast_univariate(clean_v, self.forecast_days)
                        full_ext = np.concatenate([clean_v, ext_fc])
                        covariate_extended_list.append(full_ext)

            completed_count = 0
            for grp_name in sorted_groups:
                series_list = grouped_structure[grp_name]
                group_box = QFrame()
                group_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                group_box.setStyleSheet("QFrame { background-color: #ffffff; border: 1px solid #dcdcdc; border-radius: 6px; }")
                group_layout = QVBoxLayout(group_box)
                group_layout.setContentsMargins(6, 6, 6, 6)
                group_layout.setSpacing(4)

                group_header = QWidget()
                group_header.setFixedHeight(28)
                group_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

                group_header_layout = QHBoxLayout(group_header)
                group_header_layout.setContentsMargins(2, 0, 2, 0)

                grp_cb = QCheckBox()
                grp_cb.setTristate(True)
                
                active_states = [self.active_targets.get(s_name, False) for s_name in series_list] if series_list else [False]
                if all(active_states) and series_list:
                    grp_cb.setCheckState(Qt.CheckState.Checked)
                elif any(active_states):
                    grp_cb.setCheckState(Qt.CheckState.PartiallyChecked)
                else:
                    grp_cb.setCheckState(Qt.CheckState.Unchecked)

                grp_cb.stateChanged.connect(lambda state, sl=series_list: self.on_group_checkbox_changed(sl, state))
                group_header_layout.addWidget(grp_cb, alignment=Qt.AlignmentFlag.AlignVCenter)

                grp_label = QLabel(tr("group_header_label", group=grp_name, count=len(series_list)))
                grp_label.setStyleSheet("font-size: 12px; color: #34495e;")
                group_header_layout.addWidget(grp_label)
                group_header_layout.addStretch()

                group_layout.addWidget(group_header)

                for name in series_list:
                    if progress.wasCanceled():
                        break

                    values = self.raw_data[name]
                    df = self.generate_full_series(name, values, covariate_extended_list)
                    
                    row_widget = QWidget()
                    row_widget.setFixedHeight(78)
                    row_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                    
                    row_layout = QHBoxLayout(row_widget)
                    row_layout.setContentsMargins(15, 0, 5, 0)
                    row_layout.setSpacing(8)

                    cb = QCheckBox()
                    is_active = self.active_targets.get(name, False)
                    cb.setChecked(is_active)
                    cb.stateChanged.connect(lambda state, n=name: self.on_checkbox_changed(n, state))
                    row_layout.addWidget(cb, alignment=Qt.AlignmentFlag.AlignVCenter)

                    plot_container = QWidget()
                    plot_container.setFixedHeight(78)
                    
                    stacked_layout = QStackedLayout(plot_container)
                    stacked_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)

                    canvas = SingleTimeSeriesCanvas(df)
                    self.canvases.append(canvas)
                    stacked_layout.addWidget(canvas)

                    overlay_widget = QWidget()
                    overlay_layout = QHBoxLayout(overlay_widget)
                    overlay_layout.setContentsMargins(25, 4, 0, 0)
                    overlay_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

                    name_label = QLabel(name)
                    name_label.setStyleSheet(
                        "font-weight: bold; font-size: 11px; color: #1a252f; "
                        "background-color: rgba(255, 255, 255, 0.85); "
                        "border: 1px solid rgba(0, 0, 0, 0.15); "
                        "border-radius: 3px; padding: 2px 6px;"
                    )

                    meta = self.metadata.get(name, None)
                    if meta:
                        tooltip_html = f"<div style='font-family: sans-serif;'><b>{name}</b><hr/>"
                        tooltip_html += "<table style='border-spacing: 4px;'>"
                        for k, v in meta.items():
                            tooltip_html += f"<tr><td><b>{k}:</b></td><td>{v}</td></tr>"
                        tooltip_html += "</table></div>"
                        name_label.setToolTip(tooltip_html)
                    
                    overlay_layout.addWidget(name_label)
                    stacked_layout.addWidget(overlay_widget)
                    stacked_layout.setCurrentWidget(overlay_widget)

                    row_layout.addWidget(plot_container, stretch=1)

                    update_btn = QPushButton()
                    update_btn.setFixedSize(22, 22)
                    if name in self.series_source_configs:
                        update_btn.setText("🔄")
                        update_btn.clicked.connect(lambda checked, n=name: self.update_series_data(n))
                    else:
                        update_btn.setText("⃠")
                        update_btn.setEnabled(False)
                    row_layout.addWidget(update_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

                    grp_btn = QPushButton("⚙")
                    grp_btn.setFixedSize(22, 22)
                    grp_btn.clicked.connect(lambda checked, n=name: self.reassign_series_group(n))
                    row_layout.addWidget(grp_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

                    del_btn = QPushButton("✕")
                    del_btn.setFixedSize(22, 22)
                    del_btn.clicked.connect(lambda checked, n=name: self.delete_series(n))
                    row_layout.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

                    group_layout.addWidget(row_widget)
                    
                    completed_count += 1
                    progress.setValue(completed_count)
                    QApplication.processEvents()

                self.rows_layout.addWidget(group_box)

            progress.setValue(total_items)
            self.rows_layout.addStretch()

            if reset_view:
                self.reset_zoom()
            else:
                self.apply_zoom_and_scroll()
        finally:
            self.setUpdatesEnabled(True)
            # Falls während der Prognoseberechnung ein automatischer CUDA->CPU-
            # Fallback ausgelöst wurde, spiegelt sich das sofort im Titel UND in der
            # Statuszeile wider (vorher wurde nur der Titel aktualisiert).
            self._update_window_title()
            self._show_timesfm_status()

    def export_series_with_forecast(self):
        """Exportiert alle geladenen Zeitreihen (Historie + Forecast) NEBENEINANDER
        als eine gemeinsame CSV-Datei: eine Spalte pro Zeitreihe, mit Gruppen- und
        Zeitreihennamen als zweizeiliger Kopfzeile. Alle Spalten sind über eine
        gemeinsame Datumsspalte synchronisiert (fehlende Tage einer kürzeren Serie
        erscheinen dort als leere Zelle). Zeilen sind nach Datum absteigend sortiert
        (neuestes Datum oben), Spalten in derselben Gruppen-/Zeitreihen-Reihenfolge
        wie in der Oberfläche (oberste Gruppe/Zeitreihe = am weitesten links).
        Nutzt dieselbe generate_full_series()-Logik (inkl. Cache) wie die Anzeige,
        damit exportierte Werte exakt dem entsprechen, was im Chart zu sehen ist."""
        if not self.raw_data:
            QMessageBox.information(
                self, tr("export_no_data_title"), tr("export_no_data_msg")
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, tr("export_dialog_title"), tr("export_default_filename"),
            tr("csv_filter")
        )
        if not file_path:
            return

        try:
            # Covariaten-Erweiterung exakt wie in render_all_series aufbauen, damit
            # Ziel-Serien (is_target) dieselben Kovariaten-Forecasts als Kontext
            # erhalten wie in der Anzeige.
            covariate_extended_list = []
            for name, vals in self.raw_data.items():
                if not self.active_targets.get(name, False):
                    clean_v = vals[~np.isnan(vals)]
                    if len(clean_v) > 0:
                        ext_fc = self.ts_model.forecast_univariate(clean_v, self.forecast_days)
                        full_ext = np.concatenate([clean_v, ext_fc])
                        covariate_extended_list.append(full_ext)

            # Gleiche Reihenfolge wie in der Oberfläche: oberste Gruppe zuerst, darin
            # die Zeitreihen in Anzeige-Reihenfolge.
            sorted_groups, grouped_structure = self._get_sorted_group_structure()

            columns = []
            series_by_col = {}
            for grp in sorted_groups:
                for name in grouped_structure[grp]:
                    df = self.generate_full_series(name, self.raw_data[name], covariate_extended_list)
                    col_idx = len(columns)
                    columns.append((grp, name))
                    series_by_col[col_idx] = df['value']

            if not columns:
                QMessageBox.information(
                    self, tr("export_no_data_title"), tr("export_no_data_msg")
                )
                return

            # pd.DataFrame gleicht die (unterschiedlich langen) Datumsindizes der
            # einzelnen Serien automatisch über eine Vereinigung aller Datumswerte ab
            # ("outer join") - genau das stellt die geforderte Synchronisierung über
            # eine gemeinsame Datumsspalte her. Tage, die eine kürzere Serie nicht
            # abdeckt, werden dort automatisch zu leeren Zellen.
            wide_df = pd.DataFrame(series_by_col)
            wide_df.columns = pd.MultiIndex.from_tuples(columns, names=[tr("export_col_group"), tr("export_col_series")])
            wide_df = wide_df.sort_index(ascending=False)  # neuestes Datum zuerst
            wide_df.index = wide_df.index.strftime("%Y-%m-%d")
            wide_df.index.name = tr("export_col_date")

            wide_df.to_csv(file_path, encoding="utf-8-sig")

            QMessageBox.information(
                self, tr("export_success_title"),
                tr("export_success_msg", count=len(columns), path=file_path)
            )
        except Exception as e:
            QMessageBox.critical(self, tr("export_error_title"), str(e))

    def save_project(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, tr("save_project_dialog_title"), "", tr("json_filter")
        )
        if file_path:
            try:
                project_data = {
                    "forecast_days": self.forecast_days,
                    "zoom_level": self.zoom_slider.value(),
                    "scroll_position": self.scroll_slider.value(),
                    "active_targets": self.active_targets,
                    "series_groups": self.series_groups,
                    "group_creation_order": self.group_creation_order,
                    "series_start_dates": {k: v.strftime("%Y-%m-%d") for k, v in self.series_start_dates.items()},
                    "series_source_configs": self.series_source_configs,
                    "custom_empty_groups": list(self.custom_empty_groups),
                    "metadata": self.metadata,
                    "raw_data": {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in self.raw_data.items()}
                }
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(project_data, f, indent=4, ensure_ascii=False)
                
                QMessageBox.information(self, tr("success_title"), tr("save_success_msg", path=file_path))
            except Exception as e:
                QMessageBox.critical(self, tr("save_error_title"), tr("save_error_msg", e=e))

    def load_project(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("load_project_dialog_title"), "", tr("json_filter")
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    project_data = json.load(f)

                self.forecast_days = project_data.get("forecast_days", 14)
                self.horizon_spinbox.setValue(self.forecast_days)

                self.active_targets = project_data.get("active_targets", {})
                self.series_groups = project_data.get("series_groups", {})
                self.group_creation_order = project_data.get("group_creation_order", [])
                
                saved_starts = project_data.get("series_start_dates", {})
                self.series_start_dates = {k: pd.Timestamp(v) for k, v in saved_starts.items()}
                
                self.series_source_configs = project_data.get("series_source_configs", {})
                self.custom_empty_groups = set(project_data.get("custom_empty_groups", []))
                self.metadata = project_data.get("metadata", {})
                
                raw_data_json = project_data.get("raw_data", {})
                self.raw_data = {k: np.array(v) for k, v in raw_data_json.items()}

                self.forecast_cache.clear()
                self.render_all_series(reset_view=False)

                saved_zoom = project_data.get("zoom_level", 100)
                saved_scroll = project_data.get("scroll_position", 100)
                self.zoom_slider.setValue(saved_zoom)
                self.scroll_slider.setValue(saved_scroll)

                QMessageBox.information(self, tr("success_title"), tr("load_success_msg", filename=os.path.basename(file_path)))
            except Exception as e:
                QMessageBox.critical(self, tr("load_error_title"), tr("load_error_msg", e=e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.render_all_series(reset_view=True)
    window.show()
    sys.exit(app.exec())
