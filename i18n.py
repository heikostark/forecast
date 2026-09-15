#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
i18n.py — Zentrales Übersetzungsmodul für Time Series Studio.

Enthält alle sichtbaren Oberflächen-Texte (Buttons, Labels, Tooltips, Dialoge,
Fehlermeldungen, Statusmeldungen) in sechs Sprachen:
    de (Deutsch), en (English), fr (Français), es (Español),
    hi (हिन्दी), zh (中文)

Verwendung:
    from i18n import tr, set_language, get_language, LANGUAGES

    set_language("en")
    label = QLabel(tr("btn_import_web"))
    msg   = tr("err_no_data_ticker", symbol="AAPL")

Design-Entscheidung (siehe README.md, Abschnitt "Mehrsprachigkeit"):
Diese Datei übersetzt die BEDIENOBERFLÄCHE (Chrome): Menüs, Buttons, Tooltips,
Dialogtitel/-texte, Meldungen sowie die Beschriftungen der mitgelieferten
Demo-Zeitreihen. Vom Nutzer selbst vergebene Namen (eigene Gruppennamen,
CSV-Spaltennamen, Ticker-Symbole) werden bewusst NICHT automatisch übersetzt,
da sie als interne Schlüssel (Dictionary-Keys, Projektdateien) verwendet
werden und eine Übersetzung zur Laufzeit Referenzen brechen würde.
"""

LANGUAGES = {
    "de": "Deutsch",
    "en": "English",
    "fr": "Français",
    "es": "Español",
    "hi": "हिन्दी",
    "zh": "中文",
}

_DEFAULT_LANG = "en"
_current_lang = _DEFAULT_LANG


def set_language(code: str) -> None:
    """Setzt die aktive Sprache global. Fällt auf Deutsch zurück, falls der
    Code unbekannt ist."""
    global _current_lang
    _current_lang = code if code in LANGUAGES else _DEFAULT_LANG


def get_language() -> str:
    return _current_lang


def tr(key: str, **kwargs) -> str:
    """Liefert den übersetzten String für 'key' in der aktuell aktiven Sprache.
    Unbekannte Keys werden als '[[key]]' zurückgegeben (statt eines Absturzes),
    damit fehlende Übersetzungen im laufenden Betrieb sofort auffallen.
    kwargs werden per str.format() eingesetzt (z.B. tr("greet", name="Anna"))."""
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return f"[[{key}]]"
    text = entry.get(_current_lang) or entry.get(_DEFAULT_LANG) or f"[[{key}]]"
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


# ---------------------------------------------------------------------------
# Übersetzungstabelle
# ---------------------------------------------------------------------------
TRANSLATIONS = {

    # --- Allgemeine Buttons / Aktionen -------------------------------------
    "btn_apply": {
        "de": "Übernehmen", "en": "Apply", "fr": "Appliquer", "es": "Aplicar",
        "hi": "लागू करें", "zh": "应用",
    },
    "btn_cancel": {
        "de": "Abbrechen", "en": "Cancel", "fr": "Annuler", "es": "Cancelar",
        "hi": "रद्द करें", "zh": "取消",
    },
    "btn_ok": {
        "de": "OK", "en": "OK", "fr": "OK", "es": "OK", "hi": "ठीक है", "zh": "确定",
    },

    # --- Hauptfenster --------------------------------------------------------
    "app_title_base": {
        "de": "Time Series Studio", "en": "Time Series Studio",
        "fr": "Time Series Studio", "es": "Time Series Studio",
        "hi": "टाइम सीरीज़ स्टूडियो", "zh": "时间序列工作室",
    },
    "app_title_with_method": {
        "de": "Time Series Studio — {method}",
        "en": "Time Series Studio — {method}",
        "fr": "Time Series Studio — {method}",
        "es": "Time Series Studio — {method}",
        "hi": "टाइम सीरीज़ स्टूडियो — {method}",
        "zh": "时间序列工作室 — {method}",
    },
    "header_title": {
        "de": "TimesFM Time Series Studio",
        "en": "TimesFM Time Series Studio",
        "fr": "TimesFM Time Series Studio",
        "es": "TimesFM Time Series Studio",
        "hi": "TimesFM टाइम सीरीज़ स्टूडियो",
        "zh": "TimesFM 时间序列工作室",
    },
    "label_forecast_days": {
        "de": "Prognose-Tage:", "en": "Forecast days:", "fr": "Jours de prévision :",
        "es": "Días de pronóstico:", "hi": "पूर्वानुमान दिन:", "zh": "预测天数:",
    },
    "tooltip_forecast_days": {
        "de": "Anzahl der Tage, die für die Zukunft vorausgesagt werden sollen.",
        "en": "Number of days to forecast into the future.",
        "fr": "Nombre de jours à prévoir dans le futur.",
        "es": "Número de días a pronosticar hacia el futuro.",
        "hi": "भविष्य के लिए पूर्वानुमानित किए जाने वाले दिनों की संख्या।",
        "zh": "要预测未来的天数。",
    },
    "btn_new_group": {
        "de": "+ Neue Gruppe", "en": "+ New group", "fr": "+ Nouveau groupe",
        "es": "+ Nuevo grupo", "hi": "+ नया समूह", "zh": "+ 新建分组",
    },
    "tooltip_new_group": {
        "de": "Erstellt eine neue leere Gruppe.",
        "en": "Creates a new empty group.",
        "fr": "Crée un nouveau groupe vide.",
        "es": "Crea un nuevo grupo vacío.",
        "hi": "एक नया खाली समूह बनाता है।",
        "zh": "创建一个新的空分组。",
    },
    "btn_import_web": {
        "de": "Import (Web)", "en": "Import (Web)", "fr": "Importer (Web)",
        "es": "Importar (Web)", "hi": "आयात (वेब)", "zh": "导入(网络)",
    },
    "tooltip_import_web": {
        "de": "Aktien, Devisen, Kryptowährungen oder Makrodaten abrufen.",
        "en": "Fetch stocks, forex, cryptocurrencies or macro data.",
        "fr": "Récupérer des actions, devises, cryptomonnaies ou données macro.",
        "es": "Obtener acciones, divisas, criptomonedas o datos macro.",
        "hi": "शेयर, मुद्रा, क्रिप्टोकरेंसी या मैक्रो डेटा प्राप्त करें।",
        "zh": "获取股票、外汇、加密货币或宏观数据。",
    },
    "btn_import_csv": {
        "de": "Import (CSV)", "en": "Import (CSV)", "fr": "Importer (CSV)",
        "es": "Importar (CSV)", "hi": "आयात (CSV)", "zh": "导入(CSV)",
    },
    "tooltip_import_csv": {
        "de": "Lokale CSV-Datei mit Zeitreihen-Spalten laden.",
        "en": "Load a local CSV file with time series columns.",
        "fr": "Charger un fichier CSV local avec des colonnes de séries temporelles.",
        "es": "Cargar un archivo CSV local con columnas de series temporales.",
        "hi": "टाइम सीरीज़ कॉलम वाली स्थानीय CSV फ़ाइल लोड करें।",
        "zh": "加载包含时间序列列的本地 CSV 文件。",
    },
    "btn_export_csv": {
        "de": "Export (CSV)", "en": "Export (CSV)", "fr": "Exporter (CSV)",
        "es": "Exportar (CSV)", "hi": "निर्यात (CSV)", "zh": "导出(CSV)",
    },
    "tooltip_export_csv": {
        "de": "Alle Zeitreihen inkl. Historie, Forecast und Lücken-Kennzeichnung als CSV exportieren.",
        "en": "Export all time series incl. history, forecast and gap markers as CSV.",
        "fr": "Exporter toutes les séries temporelles (historique, prévision, lacunes) en CSV.",
        "es": "Exportar todas las series temporales (historial, pronóstico y huecos) como CSV.",
        "hi": "इतिहास, पूर्वानुमान और अंतराल चिह्नों सहित सभी टाइम सीरीज़ को CSV के रूप में निर्यात करें।",
        "zh": "将所有时间序列(含历史、预测和缺口标记)导出为 CSV。",
    },
    "btn_save_project": {
        "de": "Projekt Speichern", "en": "Save Project", "fr": "Enregistrer le projet",
        "es": "Guardar proyecto", "hi": "प्रोजेक्ट सहेजें", "zh": "保存项目",
    },
    "btn_load_project": {
        "de": "Projekt Laden", "en": "Load Project", "fr": "Charger le projet",
        "es": "Cargar proyecto", "hi": "प्रोजेक्ट लोड करें", "zh": "加载项目",
    },
    "label_zoom": {
        "de": "<b>Zoom:</b>", "en": "<b>Zoom:</b>", "fr": "<b>Zoom :</b>",
        "es": "<b>Zoom:</b>", "hi": "<b>ज़ूम:</b>", "zh": "<b>缩放:</b>",
    },
    "label_pan": {
        "de": "<b>Ausschnitt verschieben:</b>", "en": "<b>Pan view:</b>",
        "fr": "<b>Déplacer la vue :</b>", "es": "<b>Desplazar vista:</b>",
        "hi": "<b>दृश्य खिसकाएँ:</b>", "zh": "<b>平移视图:</b>",
    },
    "btn_zoom_reset": {
        "de": "100%", "en": "100%", "fr": "100%", "es": "100%", "hi": "100%", "zh": "100%",
    },
    "btn_zoom_to_data": {
        "de": "Auf vorhandene Daten zoomen", "en": "Zoom to available data",
        "fr": "Zoomer sur les données disponibles", "es": "Ajustar a los datos disponibles",
        "hi": "उपलब्ध डेटा पर ज़ूम करें", "zh": "缩放至可用数据",
    },
    "label_language": {
        "de": "Sprache:", "en": "Language:", "fr": "Langue :", "es": "Idioma:",
        "hi": "भाषा:", "zh": "语言:",
    },

    # --- Gruppen-Dialog (Neuzuordnung) --------------------------------------
    "group_dialog_title": {
        "de": "Gruppe ändern für '{name}'", "en": "Change group for '{name}'",
        "fr": "Changer le groupe de « {name} »", "es": "Cambiar grupo de «{name}»",
        "hi": "'{name}' के लिए समूह बदलें", "zh": "更改“{name}”的分组",
    },
    "label_existing_group": {
        "de": "Bestehende Gruppe:", "en": "Existing group:", "fr": "Groupe existant :",
        "es": "Grupo existente:", "hi": "मौजूदा समूह:", "zh": "现有分组:",
    },
    "label_new_group": {
        "de": "Oder Neue Gruppe:", "en": "Or new group:", "fr": "Ou nouveau groupe :",
        "es": "O nuevo grupo:", "hi": "या नया समूह:", "zh": "或新建分组:",
    },
    "placeholder_new_group": {
        "de": "Name der neuen Gruppe eingeben...", "en": "Enter name of new group...",
        "fr": "Saisir le nom du nouveau groupe...", "es": "Introduce el nombre del nuevo grupo...",
        "hi": "नए समूह का नाम दर्ज करें...", "zh": "输入新分组名称…",
    },
    "new_group_dialog_title": {
        "de": "Neue Gruppe erstellen", "en": "Create new group", "fr": "Créer un nouveau groupe",
        "es": "Crear nuevo grupo", "hi": "नया समूह बनाएँ", "zh": "创建新分组",
    },
    "new_group_dialog_label": {
        "de": "Name der neuen Gruppe:", "en": "Name of the new group:",
        "fr": "Nom du nouveau groupe :", "es": "Nombre del nuevo grupo:",
        "hi": "नए समूह का नाम:", "zh": "新分组名称:",
    },

    # --- Finanz-Import-Dialog -------------------------------------------------
    "finance_dialog_title": {
        "de": "Finanz- & Makro-Zeitreihen Importieren", "en": "Import Financial & Macro Time Series",
        "fr": "Importer des séries financières et macroéconomiques",
        "es": "Importar series financieras y macroeconómicas",
        "hi": "वित्तीय और मैक्रो टाइम सीरीज़ आयात करें", "zh": "导入金融与宏观时间序列",
    },
    "tooltip_source": {
        "de": "Wähle die externe Datenquelle für den Import aus.",
        "en": "Choose the external data source for the import.",
        "fr": "Choisissez la source de données externe pour l'import.",
        "es": "Elige la fuente de datos externa para la importación.",
        "hi": "आयात के लिए बाहरी डेटा स्रोत चुनें।",
        "zh": "为导入选择外部数据源。",
    },
    "source_yahoo": {
        "de": "Yahoo Finance (Aktien, ETFs, Indizes)",
        "en": "Yahoo Finance (Stocks, ETFs, Indices)",
        "fr": "Yahoo Finance (Actions, ETF, Indices)",
        "es": "Yahoo Finance (Acciones, ETF, Índices)",
        "hi": "Yahoo Finance (शेयर, ETF, सूचकांक)",
        "zh": "雅虎财经(股票、ETF、指数)",
    },
    "source_fred": {
        "de": "FRED - US Federal Reserve (Makrodaten, Zinsen, BIP)",
        "en": "FRED - US Federal Reserve (Macro data, rates, GDP)",
        "fr": "FRED - Réserve fédérale américaine (Données macro, taux, PIB)",
        "es": "FRED - Reserva Federal de EE. UU. (Datos macro, tasas, PIB)",
        "hi": "FRED - अमेरिकी फ़ेडरल रिज़र्व (मैक्रो डेटा, दरें, GDP)",
        "zh": "FRED - 美国联邦储备(宏观数据、利率、GDP)",
    },
    "source_coingecko": {
        "de": "CoinGecko (Kryptowährungen - z.B. bitcoin, ethereum)",
        "en": "CoinGecko (Cryptocurrencies - e.g. bitcoin, ethereum)",
        "fr": "CoinGecko (Cryptomonnaies - ex. bitcoin, ethereum)",
        "es": "CoinGecko (Criptomonedas - p. ej. bitcoin, ethereum)",
        "hi": "CoinGecko (क्रिप्टोकरेंसी - जैसे bitcoin, ethereum)",
        "zh": "CoinGecko(加密货币,如 bitcoin、ethereum)",
    },
    "label_data_source": {
        "de": "Datenquelle:", "en": "Data source:", "fr": "Source de données :",
        "es": "Fuente de datos:", "hi": "डेटा स्रोत:", "zh": "数据源:",
    },
    "tooltip_symbol": {
        "de": "Gib das Ticker-Symbol ein (z.B. AAPL, ^GDAXI, GDP oder bitcoin).",
        "en": "Enter the ticker symbol (e.g. AAPL, ^GDAXI, GDP or bitcoin).",
        "fr": "Saisissez le symbole (ex. AAPL, ^GDAXI, GDP ou bitcoin).",
        "es": "Introduce el símbolo (p. ej. AAPL, ^GDAXI, GDP o bitcoin).",
        "hi": "टिकर प्रतीक दर्ज करें (जैसे AAPL, ^GDAXI, GDP या bitcoin)।",
        "zh": "输入代码(例如 AAPL、^GDAXI、GDP 或 bitcoin)。",
    },
    "placeholder_symbol": {
        "de": "z.B. AAPL, MSFT, ^GDAXI, BTC-USD, GDP",
        "en": "e.g. AAPL, MSFT, ^GDAXI, BTC-USD, GDP",
        "fr": "ex. AAPL, MSFT, ^GDAXI, BTC-USD, GDP",
        "es": "p. ej. AAPL, MSFT, ^GDAXI, BTC-USD, GDP",
        "hi": "जैसे AAPL, MSFT, ^GDAXI, BTC-USD, GDP",
        "zh": "例如 AAPL、MSFT、^GDAXI、BTC-USD、GDP",
    },
    "label_symbol": {
        "de": "Ticker / Symbol:", "en": "Ticker / Symbol:", "fr": "Symbole / Ticker :",
        "es": "Símbolo / Ticker:", "hi": "टिकर / प्रतीक:", "zh": "代码 / Ticker:",
    },
    "tooltip_years": {
        "de": "Anzahl der historischen Jahre, die geladen werden sollen.",
        "en": "Number of historical years to load.",
        "fr": "Nombre d'années historiques à charger.",
        "es": "Número de años históricos a cargar.",
        "hi": "लोड किए जाने वाले ऐतिहासिक वर्षों की संख्या।",
        "zh": "要加载的历史年数。",
    },
    "label_years": {
        "de": "Verlauf (Jahre):", "en": "History (years):", "fr": "Historique (années) :",
        "es": "Historial (años):", "hi": "इतिहास (वर्ष):", "zh": "历史范围(年):",
    },
    "finance_hint_html": {
        "de": ("<small><i>Tipps:<br>"
               "• Yahoo: 'AAPL' (Apple), '^GDAXI' (DAX), 'EURUSD=X' (Forex)<br>"
               "• FRED: 'GDP' (BIP US - wird auf Tagesbasis interpoliert), 'UNRATE' (Arbeitslosigkeit)</i></small>"),
        "en": ("<small><i>Tips:<br>"
               "• Yahoo: 'AAPL' (Apple), '^GDAXI' (DAX), 'EURUSD=X' (Forex)<br>"
               "• FRED: 'GDP' (US GDP - interpolated to daily), 'UNRATE' (unemployment)</i></small>"),
        "fr": ("<small><i>Astuces :<br>"
               "• Yahoo : 'AAPL' (Apple), '^GDAXI' (DAX), 'EURUSD=X' (Forex)<br>"
               "• FRED : 'GDP' (PIB US - interpolé quotidiennement), 'UNRATE' (chômage)</i></small>"),
        "es": ("<small><i>Consejos:<br>"
               "• Yahoo: 'AAPL' (Apple), '^GDAXI' (DAX), 'EURUSD=X' (Forex)<br>"
               "• FRED: 'GDP' (PIB de EE. UU. - interpolado a diario), 'UNRATE' (desempleo)</i></small>"),
        "hi": ("<small><i>सुझाव:<br>"
               "• Yahoo: 'AAPL' (Apple), '^GDAXI' (DAX), 'EURUSD=X' (Forex)<br>"
               "• FRED: 'GDP' (US GDP - दैनिक आधार पर प्रक्षेपित), 'UNRATE' (बेरोज़गारी)</i></small>"),
        "zh": ("<small><i>提示:<br>"
               "• 雅虎: 'AAPL'(苹果)、'^GDAXI'(DAX指数)、'EURUSD=X'(外汇)<br>"
               "• FRED: 'GDP'(美国GDP,按日插值)、'UNRATE'(失业率)</i></small>"),
    },
    "btn_fetch_data": {
        "de": "Daten Laden", "en": "Fetch Data", "fr": "Charger les données",
        "es": "Cargar datos", "hi": "डेटा लोड करें", "zh": "获取数据",
    },
    "tooltip_fetch": {
        "de": "Startet den Abruf der Daten aus der gewählten Quelle.",
        "en": "Starts fetching data from the selected source.",
        "fr": "Démarre la récupération des données depuis la source sélectionnée.",
        "es": "Inicia la obtención de datos desde la fuente seleccionada.",
        "hi": "चयनित स्रोत से डेटा प्राप्त करना शुरू करता है।",
        "zh": "开始从所选数据源获取数据。",
    },
    "tooltip_cancel_dialog": {
        "de": "Schließt den Dialog ohne Daten zu importieren.",
        "en": "Closes the dialog without importing data.",
        "fr": "Ferme la boîte de dialogue sans importer de données.",
        "es": "Cierra el diálogo sin importar datos.",
        "hi": "बिना डेटा आयात किए संवाद बंद करता है।",
        "zh": "关闭对话框而不导入数据。",
    },

    # --- Fehler-/Erfolgsmeldungen (Finanzimport) --------------------------
    "err_input_title": {
        "de": "Eingabefehler", "en": "Input Error", "fr": "Erreur de saisie",
        "es": "Error de entrada", "hi": "इनपुट त्रुटि", "zh": "输入错误",
    },
    "err_input_msg": {
        "de": "Bitte gib ein Symbol/Ticker ein.", "en": "Please enter a symbol/ticker.",
        "fr": "Veuillez saisir un symbole/ticker.", "es": "Introduce un símbolo/ticker.",
        "hi": "कृपया एक प्रतीक/टिकर दर्ज करें।", "zh": "请输入代码。",
    },
    "err_yfinance_missing": {
        "de": "Bitte installiere 'yfinance': pip install yfinance",
        "en": "Please install 'yfinance': pip install yfinance",
        "fr": "Veuillez installer 'yfinance' : pip install yfinance",
        "es": "Instala 'yfinance': pip install yfinance",
        "hi": "कृपया 'yfinance' इंस्टॉल करें: pip install yfinance",
        "zh": "请安装 'yfinance': pip install yfinance",
    },
    "err_no_data_ticker": {
        "de": "Keine Daten für Ticker '{symbol}' gefunden.",
        "en": "No data found for ticker '{symbol}'.",
        "fr": "Aucune donnée trouvée pour le ticker « {symbol} ».",
        "es": "No se encontraron datos para el ticker «{symbol}».",
        "hi": "टिकर '{symbol}' के लिए कोई डेटा नहीं मिला।",
        "zh": "未找到代码“{symbol}”的数据。",
    },
    "err_datareader_missing": {
        "de": "Bitte installiere 'pandas_datareader': pip install pandas_datareader",
        "en": "Please install 'pandas_datareader': pip install pandas_datareader",
        "fr": "Veuillez installer 'pandas_datareader' : pip install pandas_datareader",
        "es": "Instala 'pandas_datareader': pip install pandas_datareader",
        "hi": "कृपया 'pandas_datareader' इंस्टॉल करें: pip install pandas_datareader",
        "zh": "请安装 'pandas_datareader': pip install pandas_datareader",
    },
    "err_no_fred_data": {
        "de": "Keine FRED-Daten für Symbol '{symbol}' gefunden.",
        "en": "No FRED data found for symbol '{symbol}'.",
        "fr": "Aucune donnée FRED trouvée pour le symbole « {symbol} ».",
        "es": "No se encontraron datos de FRED para el símbolo «{symbol}».",
        "hi": "प्रतीक '{symbol}' के लिए कोई FRED डेटा नहीं मिला।",
        "zh": "未找到符号“{symbol}”的 FRED 数据。",
    },
    "err_no_crypto_data": {
        "de": "Keine Krypto-Daten für ID '{coin_id}' gefunden.",
        "en": "No crypto data found for ID '{coin_id}'.",
        "fr": "Aucune donnée crypto trouvée pour l'ID « {coin_id} ».",
        "es": "No se encontraron datos cripto para el ID «{coin_id}».",
        "hi": "ID '{coin_id}' के लिए कोई क्रिप्टो डेटा नहीं मिला।",
        "zh": "未找到 ID“{coin_id}”的加密货币数据。",
    },
    "err_fetch_title": {
        "de": "Fehler beim Datenabruf", "en": "Data Fetch Error", "fr": "Erreur de récupération",
        "es": "Error al obtener datos", "hi": "डेटा प्राप्ति त्रुटि", "zh": "数据获取错误",
    },
    "err_fetch_msg": {
        "de": "Konnte Daten nicht laden:\n{e}", "en": "Could not load data:\n{e}",
        "fr": "Impossible de charger les données :\n{e}",
        "es": "No se pudieron cargar los datos:\n{e}",
        "hi": "डेटा लोड नहीं किया जा सका:\n{e}", "zh": "无法加载数据:\n{e}",
    },

    # --- TimesFM Status ------------------------------------------------------
    "method_statistical_fallback": {
        "de": "Statistischer Fallback", "en": "Statistical fallback",
        "fr": "Repli statistique", "es": "Alternativa estadística",
        "hi": "सांख्यिकीय फ़ॉलबैक", "zh": "统计回退方法",
    },
    "status_timesfm_ok": {
        "de": "✓ TimesFM ({version}, {device}) erfolgreich geladen — Prognosen nutzen das KI-Modell.",
        "en": "✓ TimesFM ({version}, {device}) loaded successfully — forecasts use the AI model.",
        "fr": "✓ TimesFM ({version}, {device}) chargé avec succès — les prévisions utilisent le modèle IA.",
        "es": "✓ TimesFM ({version}, {device}) cargado correctamente — los pronósticos usan el modelo de IA.",
        "hi": "✓ TimesFM ({version}, {device}) सफलतापूर्वक लोड हुआ — पूर्वानुमान AI मॉडल का उपयोग करते हैं।",
        "zh": "✓ TimesFM({version}, {device})加载成功 — 预测将使用 AI 模型。",
    },
    "status_timesfm_fail": {
        "de": "⚠ TimesFM konnte nicht geladen werden — Prognosen laufen im statistischen Fallback-Modus (Details siehe Konsole).",
        "en": "⚠ TimesFM could not be loaded — forecasts run in statistical fallback mode (see console for details).",
        "fr": "⚠ Impossible de charger TimesFM — les prévisions utilisent le mode de repli statistique (détails dans la console).",
        "es": "⚠ No se pudo cargar TimesFM — los pronósticos usan el modo de alternativa estadística (ver detalles en consola).",
        "hi": "⚠ TimesFM लोड नहीं हो सका — पूर्वानुमान सांख्यिकीय फ़ॉलबैक मोड में चल रहे हैं (विवरण के लिए कंसोल देखें)।",
        "zh": "⚠ 无法加载 TimesFM — 预测将以统计回退模式运行(详情请查看控制台)。",
    },
    "warn_timesfm_title": {
        "de": "TimesFM nicht verfügbar", "en": "TimesFM unavailable", "fr": "TimesFM indisponible",
        "es": "TimesFM no disponible", "hi": "TimesFM उपलब्ध नहीं है", "zh": "TimesFM 不可用",
    },
    "warn_timesfm_msg": {
        "de": ("Das TimesFM-Modell konnte nicht initialisiert werden.\n\n"
               "Das Programm funktioniert weiterhin, nutzt für Prognosen aber nur "
               "eine einfache statistische Heuristik statt des KI-Modells.\n\n"
               "Details zur Ursache stehen in der Konsolenausgabe."),
        "en": ("The TimesFM model could not be initialized.\n\n"
               "The program continues to work, but forecasts use a simple "
               "statistical heuristic instead of the AI model.\n\n"
               "Details on the cause are in the console output."),
        "fr": ("Le modèle TimesFM n'a pas pu être initialisé.\n\n"
               "Le programme continue de fonctionner, mais les prévisions utilisent "
               "une simple heuristique statistique au lieu du modèle IA.\n\n"
               "Les détails de la cause figurent dans la sortie console."),
        "es": ("No se pudo inicializar el modelo TimesFM.\n\n"
               "El programa sigue funcionando, pero los pronósticos usan una "
               "sencilla heurística estadística en lugar del modelo de IA.\n\n"
               "Los detalles de la causa están en la salida de consola."),
        "hi": ("TimesFM मॉडल को प्रारंभ नहीं किया जा सका।\n\n"
               "प्रोग्राम काम करना जारी रखता है, लेकिन पूर्वानुमानों के लिए AI मॉडल "
               "के बजाय एक सरल सांख्यिकीय हेयुरिस्टिक का उपयोग करता है।\n\n"
               "कारण का विवरण कंसोल आउटपुट में है।"),
        "zh": ("无法初始化 TimesFM 模型。\n\n"
               "程序将继续运行,但预测将使用简单的统计启发式方法,而非 AI 模型。\n\n"
               "详细原因请查看控制台输出。"),
    },

    # --- CSV Import ------------------------------------------------------------
    "csv_dialog_title": {
        "de": "CSV-Datei öffnen", "en": "Open CSV File", "fr": "Ouvrir un fichier CSV",
        "es": "Abrir archivo CSV", "hi": "CSV फ़ाइल खोलें", "zh": "打开 CSV 文件",
    },
    "csv_filter": {
        "de": "CSV Dateien (*.csv);;Alle Dateien (*)",
        "en": "CSV files (*.csv);;All files (*)",
        "fr": "Fichiers CSV (*.csv);;Tous les fichiers (*)",
        "es": "Archivos CSV (*.csv);;Todos los archivos (*)",
        "hi": "CSV फ़ाइलें (*.csv);;सभी फ़ाइलें (*)",
        "zh": "CSV 文件 (*.csv);;所有文件 (*)",
    },
    "err_generic_title": {
        "de": "Fehler", "en": "Error", "fr": "Erreur", "es": "Error", "hi": "त्रुटि", "zh": "错误",
    },
    "err_csv_load_msg": {
        "de": "Datei konnte nicht geladen werden:\n{e}",
        "en": "File could not be loaded:\n{e}",
        "fr": "Impossible de charger le fichier :\n{e}",
        "es": "No se pudo cargar el archivo:\n{e}",
        "hi": "फ़ाइल लोड नहीं की जा सकी:\n{e}",
        "zh": "无法加载文件:\n{e}",
    },

    # --- Aktualisieren einzelner Serien ---------------------------------------
    "err_yfinance_not_installed": {
        "de": "yfinance ist nicht installiert.", "en": "yfinance is not installed.",
        "fr": "yfinance n'est pas installé.", "es": "yfinance no está instalado.",
        "hi": "yfinance इंस्टॉल नहीं है।", "zh": "未安装 yfinance。",
    },
    "err_no_current_data": {
        "de": "Keine aktuellen Daten empfangen.", "en": "No current data received.",
        "fr": "Aucune donnée actuelle reçue.", "es": "No se recibieron datos actuales.",
        "hi": "कोई वर्तमान डेटा प्राप्त नहीं हुआ।", "zh": "未接收到最新数据。",
    },
    "err_datareader_not_installed": {
        "de": "pandas_datareader ist nicht installiert.", "en": "pandas_datareader is not installed.",
        "fr": "pandas_datareader n'est pas installé.", "es": "pandas_datareader no está instalado.",
        "hi": "pandas_datareader इंस्टॉल नहीं है।", "zh": "未安装 pandas_datareader。",
    },
    "err_no_fred_data_generic": {
        "de": "Keine FRED-Daten empfangen.", "en": "No FRED data received.",
        "fr": "Aucune donnée FRED reçue.", "es": "No se recibieron datos de FRED.",
        "hi": "कोई FRED डेटा प्राप्त नहीं हुआ।", "zh": "未接收到 FRED 数据。",
    },
    "err_no_crypto_data_generic": {
        "de": "Keine Krypto-Daten empfangen.", "en": "No crypto data received.",
        "fr": "Aucune donnée crypto reçue.", "es": "No se recibieron datos cripto.",
        "hi": "कोई क्रिप्टो डेटा प्राप्त नहीं हुआ।", "zh": "未接收到加密货币数据。",
    },
    "success_title": {
        "de": "Erfolg", "en": "Success", "fr": "Succès", "es": "Éxito",
        "hi": "सफलता", "zh": "成功",
    },
    "update_success_msg": {
        "de": "Zeitreihe '{name}' wurde erfolgreich aktualisiert!",
        "en": "Time series '{name}' was updated successfully!",
        "fr": "La série temporelle « {name} » a été mise à jour avec succès !",
        "es": "¡La serie temporal «{name}» se actualizó correctamente!",
        "hi": "टाइम सीरीज़ '{name}' सफलतापूर्वक अपडेट हो गई!",
        "zh": "时间序列“{name}”已成功更新!",
    },
    "update_error_title": {
        "de": "Aktualisierungsfehler", "en": "Update Error", "fr": "Erreur de mise à jour",
        "es": "Error de actualización", "hi": "अद्यतन त्रुटि", "zh": "更新错误",
    },
    "update_error_msg": {
        "de": "Konnte Daten nicht abrufen:\n{e}", "en": "Could not fetch data:\n{e}",
        "fr": "Impossible de récupérer les données :\n{e}",
        "es": "No se pudieron obtener los datos:\n{e}",
        "hi": "डेटा प्राप्त नहीं किया जा सका:\n{e}", "zh": "无法获取数据:\n{e}",
    },

    # --- Fortschritt / Rendering -------------------------------------------
    "progress_computing": {
        "de": "Berechne Zeitreihen & Prognosen...", "en": "Computing time series & forecasts...",
        "fr": "Calcul des séries temporelles et prévisions...",
        "es": "Calculando series temporales y pronósticos...",
        "hi": "टाइम सीरीज़ और पूर्वानुमान की गणना हो रही है...", "zh": "正在计算时间序列与预测…",
    },
    "progress_title": {
        "de": "Bitte warten", "en": "Please wait", "fr": "Veuillez patienter",
        "es": "Espere por favor", "hi": "कृपया प्रतीक्षा करें", "zh": "请稍候",
    },
    "group_header_label": {
        "de": "<b>Gruppe: {group}</b> <small>({count} Zeitreihen)</small>",
        "en": "<b>Group: {group}</b> <small>({count} series)</small>",
        "fr": "<b>Groupe : {group}</b> <small>({count} séries)</small>",
        "es": "<b>Grupo: {group}</b> <small>({count} series)</small>",
        "hi": "<b>समूह: {group}</b> <small>({count} सीरीज़)</small>",
        "zh": "<b>分组: {group}</b> <small>(共 {count} 条序列)</small>",
    },

    # --- Export --------------------------------------------------------------
    "export_no_data_title": {
        "de": "Kein Export möglich", "en": "Export not possible", "fr": "Export impossible",
        "es": "No es posible exportar", "hi": "निर्यात संभव नहीं", "zh": "无法导出",
    },
    "export_no_data_msg": {
        "de": "Es sind keine Zeitreihen geladen.", "en": "No time series are loaded.",
        "fr": "Aucune série temporelle n'est chargée.", "es": "No hay series temporales cargadas.",
        "hi": "कोई टाइम सीरीज़ लोड नहीं है।", "zh": "未加载任何时间序列。",
    },
    "export_dialog_title": {
        "de": "Zeitreihen mit Forecast exportieren", "en": "Export time series with forecast",
        "fr": "Exporter les séries temporelles avec prévision",
        "es": "Exportar series temporales con pronóstico",
        "hi": "पूर्वानुमान सहित टाइम सीरीज़ निर्यात करें", "zh": "导出带预测的时间序列",
    },
    "export_default_filename": {
        "de": "zeitreihen_export.csv", "en": "timeseries_export.csv",
        "fr": "series_temporelles_export.csv", "es": "series_temporales_exportacion.csv",
        "hi": "timeseries_export.csv", "zh": "时间序列导出.csv",
    },
    "export_success_title": {
        "de": "Export erfolgreich", "en": "Export successful", "fr": "Export réussi",
        "es": "Exportación exitosa", "hi": "निर्यात सफल", "zh": "导出成功",
    },
    "export_success_msg": {
        "de": ("{count} Zeitreihen (inkl. Forecast) wurden nebeneinander, "
               "synchronisiert über eine gemeinsame Datumsspalte, nach\n'{path}'\nexportiert."),
        "en": ("{count} time series (incl. forecast) were exported side by side, "
               "synchronized via a shared date column, to\n'{path}'."),
        "fr": ("{count} séries temporelles (avec prévision) ont été exportées côte à côte, "
               "synchronisées via une colonne de date commune, vers\n« {path} »."),
        "es": ("Se exportaron {count} series temporales (con pronóstico) una junto a otra, "
               "sincronizadas mediante una columna de fecha común, a\n«{path}»."),
        "hi": ("{count} टाइम सीरीज़ (पूर्वानुमान सहित) को एक साझा तिथि कॉलम के माध्यम से "
               "समन्वयित करके, एक साथ\n'{path}'\nमें निर्यात किया गया।"),
        "zh": ("已将 {count} 条时间序列(含预测)并排导出,并通过统一的日期列同步,"
               "保存至\n'{path}'。"),
    },
    "export_error_title": {
        "de": "Fehler beim Export", "en": "Export Error", "fr": "Erreur d'exportation",
        "es": "Error de exportación", "hi": "निर्यात त्रुटि", "zh": "导出错误",
    },
    "export_col_date": {
        "de": "Datum", "en": "Date", "fr": "Date", "es": "Fecha", "hi": "तिथि", "zh": "日期",
    },
    "export_col_group": {
        "de": "Gruppe", "en": "Group", "fr": "Groupe", "es": "Grupo", "hi": "समूह", "zh": "分组",
    },
    "export_col_series": {
        "de": "Zeitreihe", "en": "Series", "fr": "Série", "es": "Serie", "hi": "सीरीज़", "zh": "序列",
    },

    # --- Projekt speichern/laden -----------------------------------------------
    "save_project_dialog_title": {
        "de": "Projekt Speichern", "en": "Save Project", "fr": "Enregistrer le projet",
        "es": "Guardar proyecto", "hi": "प्रोजेक्ट सहेजें", "zh": "保存项目",
    },
    "json_filter": {
        "de": "JSON Dateien (*.json);;Alle Dateien (*)",
        "en": "JSON files (*.json);;All files (*)",
        "fr": "Fichiers JSON (*.json);;Tous les fichiers (*)",
        "es": "Archivos JSON (*.json);;Todos los archivos (*)",
        "hi": "JSON फ़ाइलें (*.json);;सभी फ़ाइलें (*)",
        "zh": "JSON 文件 (*.json);;所有文件 (*)",
    },
    "save_success_msg": {
        "de": "Projekt erfolgreich gespeichert unter:\n{path}",
        "en": "Project saved successfully to:\n{path}",
        "fr": "Projet enregistré avec succès dans :\n{path}",
        "es": "Proyecto guardado correctamente en:\n{path}",
        "hi": "प्रोजेक्ट सफलतापूर्वक यहाँ सहेजा गया:\n{path}",
        "zh": "项目已成功保存至:\n{path}",
    },
    "save_error_title": {
        "de": "Fehler beim Speichern", "en": "Save Error", "fr": "Erreur d'enregistrement",
        "es": "Error al guardar", "hi": "सहेजने में त्रुटि", "zh": "保存错误",
    },
    "save_error_msg": {
        "de": "Projekt konnte nicht gespeichert werden:\n{e}",
        "en": "Project could not be saved:\n{e}",
        "fr": "Le projet n'a pas pu être enregistré :\n{e}",
        "es": "No se pudo guardar el proyecto:\n{e}",
        "hi": "प्रोजेक्ट सहेजा नहीं जा सका:\n{e}",
        "zh": "无法保存项目:\n{e}",
    },
    "load_project_dialog_title": {
        "de": "Projekt Laden", "en": "Load Project", "fr": "Charger le projet",
        "es": "Cargar proyecto", "hi": "प्रोजेक्ट लोड करें", "zh": "加载项目",
    },
    "load_success_msg": {
        "de": "Projekt '{filename}' wurde erfolgreich geladen!",
        "en": "Project '{filename}' was loaded successfully!",
        "fr": "Le projet « {filename} » a été chargé avec succès !",
        "es": "¡El proyecto «{filename}» se cargó correctamente!",
        "hi": "प्रोजेक्ट '{filename}' सफलतापूर्वक लोड हो गया!",
        "zh": "项目“{filename}”已成功加载!",
    },
    "load_error_title": {
        "de": "Fehler beim Laden", "en": "Load Error", "fr": "Erreur de chargement",
        "es": "Error al cargar", "hi": "लोड करने में त्रुटि", "zh": "加载错误",
    },
    "load_error_msg": {
        "de": "Projektdatei konnte nicht geladen werden:\n{e}",
        "en": "Project file could not be loaded:\n{e}",
        "fr": "Le fichier projet n'a pas pu être chargé :\n{e}",
        "es": "No se pudo cargar el archivo de proyecto:\n{e}",
        "hi": "प्रोजेक्ट फ़ाइल लोड नहीं की जा सकी:\n{e}",
        "zh": "无法加载项目文件:\n{e}",
    },

    # --- Metadaten-Schlüssel (Tooltip-Tabelle) -----------------------------
    "meta_source": {
        "de": "Quelle", "en": "Source", "fr": "Source", "es": "Fuente", "hi": "स्रोत", "zh": "来源",
    },
    "meta_symbol": {
        "de": "Symbol", "en": "Symbol", "fr": "Symbole", "es": "Símbolo", "hi": "प्रतीक", "zh": "代码",
    },
    "meta_name": {
        "de": "Name", "en": "Name", "fr": "Nom", "es": "Nombre", "hi": "नाम", "zh": "名称",
    },
    "meta_currency": {
        "de": "Währung", "en": "Currency", "fr": "Devise", "es": "Moneda", "hi": "मुद्रा", "zh": "货币",
    },
    "meta_datapoints_days": {
        "de": "Datenpunkte (Tage)", "en": "Data points (days)", "fr": "Points de données (jours)",
        "es": "Puntos de datos (días)", "hi": "डेटा बिंदु (दिन)", "zh": "数据点(天)",
    },
    "meta_datapoints": {
        "de": "Datenpunkte", "en": "Data points", "fr": "Points de données",
        "es": "Puntos de datos", "hi": "डेटा बिंदु", "zh": "数据点",
    },
    "meta_start_date": {
        "de": "Startdatum", "en": "Start date", "fr": "Date de début", "es": "Fecha de inicio",
        "hi": "आरंभ तिथि", "zh": "开始日期",
    },
    "meta_end_date": {
        "de": "Enddatum", "en": "End date", "fr": "Date de fin", "es": "Fecha de fin",
        "hi": "समाप्ति तिथि", "zh": "结束日期",
    },
    "meta_last_value": {
        "de": "Letzter Wert", "en": "Last value", "fr": "Dernière valeur", "es": "Último valor",
        "hi": "अंतिम मूल्य", "zh": "最新值",
    },
    "meta_coin_id": {
        "de": "Coin ID", "en": "Coin ID", "fr": "ID de la crypto", "es": "ID de la moneda",
        "hi": "कॉइन ID", "zh": "币种 ID",
    },
    "meta_last_price": {
        "de": "Letzter Preis", "en": "Last price", "fr": "Dernier prix", "es": "Último precio",
        "hi": "अंतिम मूल्य", "zh": "最新价格",
    },
    "meta_filename": {
        "de": "Dateiname", "en": "Filename", "fr": "Nom du fichier", "es": "Nombre de archivo",
        "hi": "फ़ाइल नाम", "zh": "文件名",
    },
    "meta_column": {
        "de": "Spalte", "en": "Column", "fr": "Colonne", "es": "Columna", "hi": "कॉलम", "zh": "列",
    },
    "meta_min_value": {
        "de": "Min Wert", "en": "Min value", "fr": "Valeur min", "es": "Valor mín.",
        "hi": "न्यूनतम मूल्य", "zh": "最小值",
    },
    "meta_max_value": {
        "de": "Max Wert", "en": "Max value", "fr": "Valeur max", "es": "Valor máx.",
        "hi": "अधिकतम मूल्य", "zh": "最大值",
    },

    # --- Quellen-Bezeichnungen (in Metadaten-Werten) -----------------------
    "src_yahoo_finance": {
        "de": "Yahoo Finance", "en": "Yahoo Finance", "fr": "Yahoo Finance",
        "es": "Yahoo Finance", "hi": "Yahoo Finance", "zh": "雅虎财经",
    },
    "src_yahoo_finance_updated": {
        "de": "Yahoo Finance (Aktualisiert)", "en": "Yahoo Finance (Updated)",
        "fr": "Yahoo Finance (Mis à jour)", "es": "Yahoo Finance (Actualizado)",
        "hi": "Yahoo Finance (अद्यतन)", "zh": "雅虎财经(已更新)",
    },
    "src_fred_daily": {
        "de": "FRED (Tages-interpoliert)", "en": "FRED (Daily-interpolated)",
        "fr": "FRED (Interpolé quotidien)", "es": "FRED (Interpolado diario)",
        "hi": "FRED (दैनिक-प्रक्षेपित)", "zh": "FRED(按日插值)",
    },
    "src_fred_updated": {
        "de": "FRED (Aktualisiert)", "en": "FRED (Updated)", "fr": "FRED (Mis à jour)",
        "es": "FRED (Actualizado)", "hi": "FRED (अद्यतन)", "zh": "FRED(已更新)",
    },
    "src_coingecko_daily": {
        "de": "CoinGecko API (Tages-interpoliert)", "en": "CoinGecko API (Daily-interpolated)",
        "fr": "API CoinGecko (Interpolé quotidien)", "es": "API CoinGecko (Interpolado diario)",
        "hi": "CoinGecko API (दैनिक-प्रक्षेपित)", "zh": "CoinGecko API(按日插值)",
    },
    "src_coingecko_updated": {
        "de": "CoinGecko API (Aktualisiert)", "en": "CoinGecko API (Updated)",
        "fr": "API CoinGecko (Mis à jour)", "es": "API CoinGecko (Actualizado)",
        "hi": "CoinGecko API (अद्यतन)", "zh": "CoinGecko API(已更新)",
    },
    "src_local_csv": {
        "de": "Lokale CSV", "en": "Local CSV", "fr": "CSV local", "es": "CSV local",
        "hi": "स्थानीय CSV", "zh": "本地 CSV",
    },

    # --- Gruppen-Namen (automatisch vergeben) -------------------------------
    "grp_yahoo_finance": {
        "de": "Yahoo Finance", "en": "Yahoo Finance", "fr": "Yahoo Finance",
        "es": "Yahoo Finance", "hi": "Yahoo Finance", "zh": "雅虎财经",
    },
    "grp_fred_macro": {
        "de": "FRED Makrodaten", "en": "FRED Macro Data", "fr": "Données macro FRED",
        "es": "Datos macro FRED", "hi": "FRED मैक्रो डेटा", "zh": "FRED 宏观数据",
    },
    "grp_coingecko_crypto": {
        "de": "CoinGecko Krypto", "en": "CoinGecko Crypto", "fr": "Crypto CoinGecko",
        "es": "Cripto CoinGecko", "hi": "CoinGecko क्रिप्टो", "zh": "CoinGecko 加密货币",
    },
    "grp_finance_data": {
        "de": "Finanzdaten", "en": "Financial Data", "fr": "Données financières",
        "es": "Datos financieros", "hi": "वित्तीय डेटा", "zh": "金融数据",
    },
    "grp_general": {
        "de": "Allgemein", "en": "General", "fr": "Général", "es": "General",
        "hi": "सामान्य", "zh": "常规",
    },

    # --- Demo-Zeitreihen (Erdwissenschaften) --------------------------------
    "grp_astronomy_solar": {
        "de": "Astronomie & Solar", "en": "Astronomy & Solar", "fr": "Astronomie et Soleil",
        "es": "Astronomía y Solar", "hi": "खगोल विज्ञान और सौर", "zh": "天文与太阳",
    },
    "grp_climate_atmosphere": {
        "de": "Klima & Atmosphäre", "en": "Climate & Atmosphere", "fr": "Climat et Atmosphère",
        "es": "Clima y Atmósfera", "hi": "जलवायु और वायुमंडल", "zh": "气候与大气",
    },
    "grp_demographics_society": {
        "de": "Demografie & Gesellschaft", "en": "Demographics & Society",
        "fr": "Démographie et Société", "es": "Demografía y Sociedad",
        "hi": "जनसांख्यिकी और समाज", "zh": "人口与社会",
    },
    "grp_geophysics_nature": {
        "de": "Geophysik & Natur", "en": "Geophysics & Nature", "fr": "Géophysique et Nature",
        "es": "Geofísica y Naturaleza", "hi": "भूभौतिकी और प्रकृति", "zh": "地球物理与自然",
    },
    "series_sunspots": {
        "de": "Sonnenflecken (Interpoliert 1749-2026)",
        "en": "Sunspots (Interpolated 1749-2026)",
        "fr": "Taches solaires (Interpolé 1749-2026)",
        "es": "Manchas solares (Interpolado 1749-2026)",
        "hi": "सनस्पॉट (प्रक्षेपित 1749-2026)",
        "zh": "太阳黑子(插值 1749-2026)",
    },
    "series_moon_cycle": {
        "de": "Mondzyklus (Synodische Phase)", "en": "Moon cycle (Synodic phase)",
        "fr": "Cycle lunaire (Phase synodique)", "es": "Ciclo lunar (Fase sinódica)",
        "hi": "चंद्र चक्र (सिनोडिक चरण)", "zh": "月相周期(朔望相位)",
    },
    "series_enso": {
        "de": "El Niño / ENSO Index (Klima)", "en": "El Niño / ENSO Index (Climate)",
        "fr": "Indice El Niño / ENSO (Climat)", "es": "Índice El Niño / ENSO (Clima)",
        "hi": "एल नीनो / ENSO सूचकांक (जलवायु)", "zh": "厄尔尼诺 / ENSO 指数(气候)",
    },
    "series_temp_anomaly": {
        "de": "Oberflächentemperatur-Anomalie (°C)", "en": "Surface Temperature Anomaly (°C)",
        "fr": "Anomalie de température de surface (°C)",
        "es": "Anomalía de temperatura superficial (°C)",
        "hi": "सतह तापमान विसंगति (°C)", "zh": "地表温度异常(°C)",
    },
    "series_co2": {
        "de": "CO₂-Gehalt der Atmosphäre (ppm)", "en": "Atmospheric CO₂ level (ppm)",
        "fr": "Taux de CO₂ atmosphérique (ppm)", "es": "Nivel de CO₂ atmosférico (ppm)",
        "hi": "वायुमंडलीय CO₂ स्तर (ppm)", "zh": "大气 CO₂ 浓度(ppm)",
    },
    "series_population": {
        "de": "Globale Bevölkerungsanzahl (Milliarden)", "en": "Global population (billions)",
        "fr": "Population mondiale (milliards)", "es": "Población mundial (miles de millones)",
        "hi": "वैश्विक जनसंख्या (अरब)", "zh": "全球人口(十亿)",
    },
    "series_volcano": {
        "de": "Vulkanausbrüche / Aerosol-Index", "en": "Volcanic eruptions / Aerosol index",
        "fr": "Éruptions volcaniques / Indice d'aérosols",
        "es": "Erupciones volcánicas / Índice de aerosoles",
        "hi": "ज्वालामुखी विस्फोट / एरोसोल सूचकांक", "zh": "火山喷发 / 气溶胶指数",
    },
    "series_earthquake": {
        "de": "Seismische Aktivität / Erdbeben (Energie-Index)",
        "en": "Seismic activity / Earthquakes (Energy index)",
        "fr": "Activité sismique / Séismes (Indice d'énergie)",
        "es": "Actividad sísmica / Terremotos (Índice de energía)",
        "hi": "भूकंपीय गतिविधि / भूकंप (ऊर्जा सूचकांक)", "zh": "地震活动 / 地震(能量指数)",
    },
    "meta_silso": {
        "de": "SILSO / Linear interpoliert", "en": "SILSO / Linearly interpolated",
        "fr": "SILSO / Interpolation linéaire", "es": "SILSO / Interpolación lineal",
        "hi": "SILSO / रैखिक प्रक्षेपित", "zh": "SILSO / 线性插值",
    },
    "meta_astro_model": {
        "de": "Astronomisches Modell (29.53 Tage)", "en": "Astronomical model (29.53 days)",
        "fr": "Modèle astronomique (29,53 jours)", "es": "Modelo astronómico (29,53 días)",
        "hi": "खगोलीय मॉडल (29.53 दिन)", "zh": "天文模型(29.53 天)",
    },
    "meta_enso_model": {
        "de": "ENSO Ozean-Modell", "en": "ENSO ocean model", "fr": "Modèle océanique ENSO",
        "es": "Modelo oceánico ENSO", "hi": "ENSO महासागर मॉडल", "zh": "ENSO 海洋模型",
    },
    "meta_temp_reconstruction": {
        "de": "Historische Temperatur-Rekonstruktion", "en": "Historical temperature reconstruction",
        "fr": "Reconstruction historique de la température",
        "es": "Reconstrucción histórica de temperatura",
        "hi": "ऐतिहासिक तापमान पुनर्निर्माण", "zh": "历史温度重建",
    },
    "meta_co2_reconstruction": {
        "de": "Eiskern- & Mauna Loa Rekonstruktion", "en": "Ice core & Mauna Loa reconstruction",
        "fr": "Reconstruction carottes de glace et Mauna Loa",
        "es": "Reconstrucción de núcleos de hielo y Mauna Loa",
        "hi": "आइस कोर और माउना लोआ पुनर्निर्माण", "zh": "冰芯与莫纳罗亚重建",
    },
    "meta_un_demographic": {
        "de": "Demografische UN-Modellierung", "en": "UN demographic modeling",
        "fr": "Modélisation démographique de l'ONU", "es": "Modelado demográfico de la ONU",
        "hi": "UN जनसांख्यिकीय मॉडलिंग", "zh": "联合国人口建模",
    },
    "meta_volcano_catalog": {
        "de": "Historischer Vulkankatalog", "en": "Historical volcano catalog",
        "fr": "Catalogue historique des volcans", "es": "Catálogo histórico de volcanes",
        "hi": "ऐतिहासिक ज्वालामुखी सूची", "zh": "历史火山目录",
    },
    "meta_seismic_index": {
        "de": "Seismologischer Energie-Release Index", "en": "Seismological energy-release index",
        "fr": "Indice sismologique de libération d'énergie",
        "es": "Índice sismológico de liberación de energía",
        "hi": "भूकंपीय ऊर्जा-मुक्ति सूचकांक", "zh": "地震能量释放指数",
    },
}
