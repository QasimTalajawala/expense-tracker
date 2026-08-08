import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import re
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# ── Constants ─────────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).parent
DATA_FILE  = BASE_DIR / "expense_data.csv"
DEMO_FILE  = BASE_DIR / "demo_data.csv"
OVR_FILE   = BASE_DIR / "category_overrides.json"

CATEGORIES = [
    "Groceries",
    "Food & Dining",
    "Food Delivery",
    "Fuel",
    "Telecom",
    "Utilities & Government",
    "Healthcare",
    "Shopping & Retail",
    "Automotive",
    "Travel & Transport",
    "Entertainment",
    "Charity & Donations",
    "Education",
    "Others",
    "Payment",
]

# Priority-ordered: first matching rule wins
RULES = [
    ("Payment",                ["PAYMENT RECEIVED"]),

    ("Food Delivery",          ["TALABAT PRO", "TALABAT", "NOON FOOD",
                                "HUNGERSTATION", "DELIVEROO"]),

    ("Fuel",                   ["OMAN OIL", "SHELL OMAN", "SHELL", "STATION 10",
                                "AL MAHA", "BP TANKSTELLE", "BP LEIKERMOSER"]),

    ("Telecom",                ["OMANTEL", "OOREDOO", "VODAFONE"]),

    ("Utilities & Government", ["NAMA WATER", "KHEDMAH", "ONEIC", "MUNICIPALITY",
                                "OIFC",           # wifi/electricity/water bill portal
                                "ROP EVISA", "ETRAFFIC", "OMPAY",
                                "MOF TAX",        # Ministry of Finance
                                "GULF INSURANCE", "ARABIAFALCON",  # insurance
                                "VFS GCC",        # visa application centre
                                "LAUNDRY", "DRY CLEAN", "DRY CL",  # laundry/dry cleaning
                                "CLEANSHEET",     # THE CLEANSHEET GROUP FZCO
                                ]),

    ("Healthcare",             ["PHARMACY", "MEDICAL COMPLEX", "MEDICAL CENTER",
                                "HOSPITAL", "CLINIC", "HEALTH CENTER", "KIMS",
                                "IHERB",          # health supplements
                                "DENTAL", "CHIRO",
                                "CPAP", "FITNESS", "GYM",
                                ]),

    ("Travel & Transport",     [# Online travel & agencies
                                "MAKEMYTRIP", "BOOKING.COM", "AIRBNB", "EXPEDIA",
                                "HOUSE OF TRAVEL", "OMIO",
                                # Airlines
                                "AIRLINE", "AIRPORT", "ETIHAD", "OMANAIR", "OMAN AIR",
                                "SALAMAIR", "INDIGO AIR",
                                # Taxis & ride-hailing
                                "OTAXI", "UBER", "CAREEM", "DUBAI TAXI",
                                # Hotels & accommodation
                                "HOTEL", "SUITES", "HILTON", "MARRIOTT", "SHERATON", "HYATT",
                                "HOLIDAY INN", "NOVOTEL", "IBIS", "HIEX", "FOUR POINTS",
                                "RADISSON", "ANANTARA", "ALILA", "RITZ CARLTON",
                                "DUSIT", "LEVATIO", "SOLID HOTEL",
                                # Airport lounge & services
                                "MARHABA",
                                # Car rental
                                "EUROPCAR", "HERTZ", "AVIS", "SIXT", "CARS ON BOOKING",
                                # European public transport & ride-hailing
                                "WESTBAHN", "REGIOJET", "DB AUTOMAT", "AIRPORTBUS",
                                "WIENER LINIEN", "OEBB", "LOGMVV", "BOLT.EU",
                                "APLIKA",         # Prague transit app (Operator ICT - Aplika)
                                # Travel extras & parking
                                "GETNOMAD", "PARKPLATZ", "PARKING",
                                # Oman mountain resorts
                                "ALAKHDER", "ALAKHDAR",
                                # Hotel URLs that truncate before "SUITES"
                                "DOWNTOWNSUI",    # https://www.downtownsuites...
                                ]),

    ("Entertainment",          ["MUSCAT FESTIVAL", "CINEMA", "VOX", "REEL", "THEME PARK",
                                "MUSEUM", "ZOO ", "FESTUNG", "WALKTHROUGH", "FUNTAZMO",
                                "NARODNI", "MUSEUMSINSEL", "TAMANI", "PADEL",
                                "RESIDENZ",       # Verwaltung der Residenz M / Shop Residenz München
                                ]),

    ("Charity & Donations",    ["NAJAFYIA", "DONATION", "CHARITY", "ZAKAT"]),

    ("Education",              ["SCHOOL", "UNIVERSITY", "COLLEGE", "TUITION",
                                "TRAINING CENTER"]),

    ("Groceries",              ["LULU",           # covers LULU HYPERMARKET, LULU WEBSTORE, etc.
                                "SPAR", "HYPERMARKET", "CARREFOUR", "SAFEER", "AL FAIR",
                                "SULTAN CENTER", "NESTO", "SUPERMARKET",
                                "LIDL", "NETTO", "ALBERT VAM", "POTRAVINY",
                                "AL EZZ COLD STORE", "COLD STORE", "NAH&FRISCH",
                                "EDEKA", "ALDI",
                                "GEMISCHTWARENHANDEL",  # German general goods store
                                "INVEST FRUI",    # fruit/produce traders (BUSINESS RFED INVEST FRUI)
                                ]),

    ("Shopping & Retail",      ["AMERICAN EAGLE", "PIERRE CARDIN", "H&M", "ZARA", "MARKS",
                                "CENTREPOINT", "ADIDAS", "NIKE", "PLAY PHONE", "JUMBO",
                                "AL WADI DOHA", "RANIM", "PROGRESS CITIES", "MUSCAT TOP",
                                "ALBAKRY", "JIBAL",
                                "IKEA", "DECATHLON", "MATALAN", "SUN & SAND", "TEMU",
                                "AMZN", "AMAZON", "EXTRA", "LAAM", "HYPERMAX", "MANGO",
                                "OLYMPIA", "DANUBE HOME", "THE BABY SHOP",
                                "TISSOT", "KALYAN JEWELLER", "NAMSHI",
                                "DUBAI DUTY FREE",
                                "MANI MART",      # FAST AND QUICK MANI MART
                                "NOONE NATIONAL", # NOONE NATIONAL LLC
                                "KIK",            # KiK Fil (German discount clothing chain)
                                "GIFT MARKET",    # WADI GIFT MARKET / EMIRATES GIFT MARKET
                                "WILLICHHABEN",   # German online retailer
                                "AL WASHEEL",     # AL WASHEEL trading
                                "NOOR SHOPPING",  # NOOR SHOPPING
                                "TELE CENTER",    # M und M Tele Center
                                "ALIF STORE",     # Alif Stores (Omani bookstore/stationery)
                                "HAPPY CENTER",   # small general/retail store
                                "AFAQ",           # Afaq trading (Oman retail)
                                ]),

    ("Automotive",             ["AUTOPOWER", "CAR WASH", "TYRE", "AUTOCARE"]),

    ("Food & Dining",          [# Major chains
                                "MCDONALDS", "KFC", "SUBWAY", "DUNKIN", "STARBUCKS",
                                "BASKIN ROBBINS", "PAPPA ROTI",
                                # Generic food keywords
                                "RESTAURANT", "CAFE", "BURGER", "PIZZA", "SWEETS", "BAKERY",
                                "COFFEE SHOP", "COFFEE", "KITCHEN", "GRILL", "BIRYANI",
                                "BISTRO", "IMBISS", "DOENER", "KEBAB", "FOODCOURT",
                                "TRATTORIA",
                                # Muscat & Oman restaurants/cafes
                                "SOURDOUGH", "REVEAL", "WINDROSE", "BOOM", "FLAMES",
                                "AL RAVI", "AL HAWAS", "SHARA MILLS", "AL SHARA MILLS",
                                "YOGRAT", "YOUGRAT", "BURJ AL DHABI", "MAMOURA",
                                "SIKANDAR", "WHITE STAR", "JAMOCHA",
                                "KALABASH", "BEGUM", "MEAT MOOT", "IMPERIAL KITCHEN",
                                "BABA SALEM", "ALLO BEIRUT", "JUICE WORLD", "JUICE",
                                "FELFELA", "ZAITOOON", "L'ETO", "MS FLUFFY",
                                "TIME OF TEA", "AHLAIN", "KUCU", "LIALI",
                                "KARAK", "MUSCAT CAFE", "ROUND TABLE",
                                "ARYAF", "MISK", "FILLI", "KALDI", "BUBBLE LAB",
                                "KUKU", "ZOBEEZ", "BHAI KADAI", "YUBIL",
                                "R & B - RUWI", "R AND B",
                                # International
                                "STADTKEBAB", "DEAN&DAVID", "EDUSCHO", "PAPA BISTRO",
                                "ANATOLIA", "ISTANBUL IMBISS",
                                "APNA KOLACHI", "AMRITSR",
                                # Generic
                                "TROPICAL",
                                # Additional Oman/international spots
                                "LE PEARL",       # Le Pearl restaurant
                                "CANDY SHOP",     # sweet shop
                                "AM ROTEN STAND", # German food stall
                                "CHILL OUT",      # cafe/restaurant
                                # Vending machines / small food outlets
                                "DELIKOMAT",      # Czech vending machine
                                "BADRALSAMAA",    # Omani food stall / small restaurant
                                "FRIENDS",        # small cafe/restaurant
                                ]),
]

# ── Immaterial-Others threshold ───────────────────────────────────────────────
# If total unclassified spend is BELOW this amount, suppress the warning banner.
OTHERS_WARN_OMR = 150  # warn only if total unclassified spend exceeds this

COLORS    = px.colors.qualitative.Pastel
CHART_CFG = {"displayModeBar": True, "displaylogo": False,
             "modeBarButtonsToRemove": ["lasso2d", "select2d"]}

# Travel sub-category rules: (SubCategory, [keywords]) — priority-ordered, first match wins
TRAVEL_SUBCATS = [
    ("Hotels & Accommodation",  [# Chain brands
                                  "MARRIOTT", "HILTON", "HYATT", "SHERATON", "RITZ CARLTON",
                                  "IBIS", "NOVOTEL", "RADISSON", "HOLIDAY INN", "HIEX",
                                  "FOUR POINTS", "ANANTARA", "ALILA", "DUSIT",
                                  # Local / boutique
                                  "LEVATIO", "SOLID HOTEL", "ALAKHDER", "ALAKHDAR",
                                  # Generic
                                  "HOTEL", "HOSTEL", "RESORT", "SUITES", "GUESTHOUSE",
                                  # Booking platforms that book accommodation
                                  "AIRBNB",
                                  ]),
    ("Flights & Rail",          [# Oman
                                  "OMANAIR", "OMAN AIR", "SALAMAIR",
                                  # Gulf / Middle East
                                  "ETIHAD", "FLYDUBAI", "EMIRATES", "QATAR AIR",
                                  "INDIGO AIR",
                                  # European rail & coaches
                                  "WESTBAHN", "REGIOJET", "DB AUTOMAT", "OEBB",
                                  # Generic
                                  "AIRLINE", "AIRWAYS", "AIRPORT BUS", "AIRPORTBUS",
                                  "EUROSTAR", "FLIXBUS",
                                  ]),
    ("Online Booking",          [# Multi-modal / rail booking
                                  "OMIO", "HOUSE OF TRAVEL",
                                  # Accommodation platforms
                                  "BOOKING.COM", "EXPEDIA", "AGODA", "HOTELS.COM",
                                  "TRIVAGO", "KAYAK", "SKYSCANNER", "MAKEMYTRIP",
                                  ]),
    ("Taxis & Ride-hailing",    ["UBER", "CAREEM", "OTAXI", "DUBAI TAXI",
                                  "TAXI", "LYFT", "BOLT.EU", "GRAB", "CAB"]),
    ("Car Rental",              ["EUROPCAR", "HERTZ", "AVIS", "SIXT",
                                  "CARS ON BOOKING", "CAR RENTAL", "RENT A CAR"]),
    ("Public Transport",        ["WIENER LINIEN", "LOGMVV", "APLIKA",
                                  "METRO", "SUBWAY", "TRAM", "OYSTER", "TFL",
                                  "S-BAHN", "U-BAHN"]),
    ("Airport & Parking",       ["MARHABA", "AIRPORT", "TERMINAL", "LOUNGE",
                                  "DUTY FREE", "PARKING", "PARKPLATZ"]),
    ("Travel Services",         ["GETNOMAD",        # travel eSIM / connectivity
                                  "NOMAD", "ESIM"]),
]

# ── Merchant normalisation ────────────────────────────────────────────────────
# Bank descriptions fragment the same merchant across many strings — petrol
# stations carry site numbers, online merchants carry order refs, gateways add
# prefixes.  These rules collapse them to one display name.  This is a *display
# and aggregation* layer only: `Description` is left untouched so category
# overrides (which key on the raw string) keep working.

_GATEWAY    = re.compile(r"^(TAP\*|SQ ?\*|PAYPAL ?\*|PP\*|SP ?\*|WWW\.|HTTPS?://)", re.I)
_STATION    = re.compile(r"^\d{3,5}\s+")            # "5399 OMAN OIL RUWI VALLEY"
_LONGDIGIT  = re.compile(r"\s*[*#]?\d{6,}\s*$")     # "ETIHAD AIRW 6072412242702"
_REFSUFFIX  = re.compile(r"\*[A-Za-z0-9]{5,}$")     # "Amazon.ca*NA6RE42O2"
_CORPSUFFIX = re.compile(
    r"\s+(L\.?L\.?C\.?|LTD\.?|LIMITED|CO\.?|INC\.?|EST\.?|TRAD(?:ING)?"
    r"|ENTERPRISES?|COMPANY|GROUP|FZCO|FZE|W\.?L\.?L\.?|S\.?A\.?O\.?C\.?)$",
    re.I,
)

# Checked against the raw description before any cleanup — first match wins.
MERCHANT_ALIASES = [
    ("Lulu Hypermarket", ["LULU HYPERMARKET", "LULU MUSCAT HYPERMARKET"]),
    ("Lulu Webstore",    ["LULU WEBSTORE"]),
    ("Lulu Pharmacy",    ["LULU PHARMACY"]),
    ("Oman Oil",         ["OMAN OIL"]),
    ("Shell Oman",       ["SHELL OMAN", "SHELL "]),
    ("Station 10",       ["STATION 10"]),
    ("Talabat",          ["TALABAT"]),
    ("Amazon",           ["AMAZON", "AMZN"]),
    ("Spar",             ["SPAR"]),
    ("Carrefour",        ["CARREFOUR"]),
    ("MakeMyTrip",       ["MAKEMYTRIP"]),
    ("Booking.com",      ["BOOKING.COM"]),
    ("Airbnb",           ["AIRBNB"]),
    ("Etihad Airways",   ["ETIHAD"]),
    ("Oman Air",         ["OMANAIR", "OMAN AIR"]),
    ("SalamAir",         ["SALAMAIR"]),
    ("Careem",           ["CAREEM"]),
    ("Uber",             ["UBER"]),
    ("Otaxi",            ["OTAXI"]),
    ("Omantel",          ["OMANTEL"]),
    ("Khedmah",          ["KHEDMAH"]),
    ("Nama Water",       ["NAMA WATER"]),
    ("OIFC",             ["OIFC"]),
    ("Muscat Pharmacy",  ["MUSCAT PHARMACY"]),
    ("KIMS Oman",        ["KIMS"]),
    ("Horizon Fitness",  ["HORIZON FITNESS"]),
    ("Kalyan Jewellers", ["KALYAN"]),
    ("British Council",  ["BRITISH COUNCIL"]),
    ("McDonald's",       ["MCDONALD"]),
    ("Starbucks",        ["STARBUCKS"]),
    ("IKEA",             ["IKEA"]),
    ("Temu",             ["TEMU"]),
    ("Namshi",           ["NAMSHI"]),
    ("Centrepoint",      ["CENTREPOINT"]),
]


def merchant_name(desc: str) -> str:
    """Collapse a raw bank description to a canonical, readable merchant name."""
    raw_u = str(desc).upper()
    for canon, keywords in MERCHANT_ALIASES:
        if any(kw in raw_u for kw in keywords):
            return canon

    s = _GATEWAY.sub("", str(desc).strip())
    s = _STATION.sub("", s)
    s = _LONGDIGIT.sub("", s)
    s = _REFSUFFIX.sub("", s).strip()

    prev = None
    while prev != s:                      # strip stacked suffixes: "X TRADING LLC"
        prev = s
        s = _CORPSUFFIX.sub("", s).strip()

    return s.title() if s.isupper() else s

# ── Parser ────────────────────────────────────────────────────────────────────

def parse_bm_statement(file) -> pd.DataFrame:
    try:
        raw = pd.read_excel(file, header=None, engine="xlrd")
    except Exception:
        raw = pd.read_excel(file, header=None)

    header_row = next(
        (i for i, row in raw.iterrows()
         if any("Transaction Date" in str(v) for v in row.values)),
        None,
    )
    if header_row is None:
        return pd.DataFrame()

    hdr = raw.iloc[header_row]
    c = {}
    for idx, val in hdr.items():
        s = str(val).strip()
        if "Transaction Date" in s:       c["date"]    = idx
        elif "Description" in s:          c["desc"]    = idx
        elif "Merchant Location" in s:    c["city"]    = idx
        elif "Merchant Country" in s:     c["country"] = idx
        elif "Transaction Currency" in s: c["ccy"]     = idx
        elif "Transaction Amount" in s:   c["amt"]     = idx
        elif "Amount in Card" in s:       c["omr"]     = idx

    if not {"date", "desc", "omr"}.issubset(c):
        return pd.DataFrame()

    d = raw.iloc[header_row + 1:].copy()

    df = pd.DataFrame({
        "Transaction Date": pd.to_datetime(d[c["date"]], dayfirst=True, errors="coerce"),
        "Description":      d[c["desc"]].astype(str).str.strip().str.rstrip(">").str.strip(),
        "City":             d[c["city"]].values    if "city"    in c else "",
        "Country":          d[c["country"]].values if "country" in c else "",
        "TXN Currency":     d[c["ccy"]].values     if "ccy"     in c else "",
        "TXN Amount":       d[c["amt"]].values     if "amt"     in c else "",
        "OMR Amount":       pd.to_numeric(d[c["omr"]], errors="coerce"),
    })

    df = df[
        df["Description"].notna()
        & ~df["Description"].isin(["nan", ""])
        & df["Transaction Date"].notna()
        & df["OMR Amount"].notna()
    ].reset_index(drop=True)

    return df

# ── Classifier ────────────────────────────────────────────────────────────────

def classify(desc: str) -> str:
    u = desc.upper()
    for cat, keywords in RULES:
        if any(kw in u for kw in keywords):
            return cat
    return "Others"


def travel_subcat(desc: str) -> str:
    """Sub-classify a Travel & Transport transaction into a finer bucket."""
    u = desc.upper()
    for subcat, keywords in TRAVEL_SUBCATS:
        if any(kw in u for kw in keywords):
            return subcat
    return "Other Travel"


def apply_overrides(df: pd.DataFrame, overrides: dict) -> pd.DataFrame:
    df = df.copy()
    df["Category"] = df["Description"].apply(classify)
    for desc, cat in overrides.items():
        df.loc[df["Description"] == desc, "Category"] = cat
    return df

# ── Persistence ───────────────────────────────────────────────────────────────

def load_overrides() -> dict:
    return json.loads(OVR_FILE.read_text()) if OVR_FILE.exists() else {}


def save_overrides(overrides: dict):
    OVR_FILE.write_text(json.dumps(overrides, indent=2))


def load_data() -> tuple[pd.DataFrame, bool]:
    """Returns (dataframe, is_demo).  Falls back to demo_data.csv when no real data exists."""
    if DATA_FILE.exists() and DATA_FILE.stat().st_size > 0:
        return pd.read_csv(DATA_FILE, parse_dates=["Transaction Date"]), False
    if DEMO_FILE.exists():
        return pd.read_csv(DEMO_FILE, parse_dates=["Transaction Date"]), True
    return pd.DataFrame(), False


def save_data(df: pd.DataFrame):
    df.to_csv(DATA_FILE, index=False)


def ingest(files) -> int:
    parsed = [parse_bm_statement(f) for f in files]
    parsed = [df for df in parsed if not df.empty]
    if not parsed:
        return 0

    new = pd.concat(parsed, ignore_index=True)
    existing, _ = load_data()

    if not existing.empty:
        combined = pd.concat([existing, new], ignore_index=True)
        key = (
            combined["Transaction Date"].astype(str) + "|"
            + combined["Description"] + "|"
            + combined["OMR Amount"].astype(str)
        )
        combined = combined[~key.duplicated(keep="first")].reset_index(drop=True)
        added = len(combined) - len(existing)
    else:
        combined = new
        added = len(new)

    save_data(combined)
    return max(added, 0)


def delete_rows(keys_to_remove: list):
    raw, _ = load_data()
    raw_key = (
        raw["Transaction Date"].astype(str) + "|"
        + raw["Description"] + "|"
        + raw["OMR Amount"].astype(str)
    )
    kept = raw[~raw_key.isin(keys_to_remove)].reset_index(drop=True)
    save_data(kept)


def row_key(df: pd.DataFrame) -> pd.Series:
    return (
        df["Transaction Date"].astype(str) + "|"
        + df["Description"] + "|"
        + df["OMR Amount"].astype(str)
    )

# ── Billing cycle helpers ─────────────────────────────────────────────────────

def billing_cycle_month(date) -> str:
    """Map a transaction date to its billing cycle (3rd → 2nd).
    Returns 'YYYY-MM' of the cycle's start month.
    e.g. 1 Jan or 2 Jan  → previous December cycle ('YYYY-12')
         3 Jan onwards    → January cycle ('YYYY-01')
    """
    if pd.isna(date):
        return ""
    if date.day >= 3:
        return date.strftime("%Y-%m")
    prev = date - pd.DateOffset(months=1)
    return prev.strftime("%Y-%m")


def cycle_label(ym: str) -> str:
    """'2026-01'  →  'Jan 2026'  (the start month of the billing cycle)"""
    y, m = int(ym[:4]), int(ym[5:7])
    return pd.Timestamp(y, m, 1).strftime("%b %Y")


def cycle_dates(ym: str) -> str:
    """'2026-01'  →  '3 Jan – 2 Feb 2026'  (full date range for tooltips)"""
    y, m  = int(ym[:4]), int(ym[5:7])
    end_m = m % 12 + 1
    end_y = y + (1 if m == 12 else 0)
    return (
        f"3 {pd.Timestamp(y, m, 1).strftime('%b')}"
        f" – 2 {pd.Timestamp(end_y, end_m, 1).strftime('%b %Y')}"
    )


def cycle_end(ym: str) -> pd.Timestamp:
    """Return the last day of the billing cycle (2nd of next month)."""
    y, m  = int(ym[:4]), int(ym[5:7])
    end_m = m % 12 + 1
    end_y = y + (1 if m == 12 else 0)
    return pd.Timestamp(end_y, end_m, 2)


def cycle_start(ym: str) -> pd.Timestamp:
    """Return the first day of the billing cycle (3rd of the month)."""
    return pd.Timestamp(int(ym[:4]), int(ym[5:7]), 3)


def split_cycles(all_cycles, data_start, today=None):
    """Separate cycles into (complete, partial).

    A cycle is only comparable if it is fully covered on BOTH sides:
      • it has already ended (cycle_end <= today), and
      • the data reaches back to its start (cycle_start >= first transaction).

    Without this, the in-progress cycle looks like a spending collapse and the
    first stub cycle drags every average down.
    """
    today = today or pd.Timestamp.today().normalize()
    complete, partial = [], []
    for ym in sorted(all_cycles):
        incomplete = cycle_start(ym) < data_start or cycle_end(ym) > today
        (partial if incomplete else complete).append(ym)
    return complete, partial


def cycle_progress(ym: str, today=None) -> tuple[int, int]:
    """Return (days_elapsed, days_total) for an in-progress cycle."""
    today = today or pd.Timestamp.today().normalize()
    start, end = cycle_start(ym), cycle_end(ym)
    total   = (end - start).days + 1
    elapsed = min(max((today - start).days + 1, 1), total)
    return elapsed, total


def recurring_merchants(df, cycles, window=6, min_hits=4) -> set:
    """Merchants seen in at least `min_hits` of the last `window` complete cycles.

    Deliberately scoped to recent cycles so lapsed commitments drop out and
    newly-started ones are picked up quickly.
    """
    recent = cycles[-window:]
    if len(recent) < min_hits:
        return set()
    hits = df[df["Month"].isin(recent)].groupby("Merchant")["Month"].nunique()
    return set(hits[hits >= min_hits].index)


def category_movers(df, cur_cycle, base_cycles, top_n=3) -> pd.DataFrame:
    """Categories that moved most vs the average of `base_cycles`.

    Each row names the single merchant that drove the change, which is the
    question a category-level delta always leaves unanswered.
    """
    if not base_cycles:
        return pd.DataFrame()

    cur  = df[df["Month"] == cur_cycle].groupby("Category")["Amount"].sum()
    base = df[df["Month"].isin(base_cycles)].groupby("Category")["Amount"].sum() / len(base_cycles)

    mv = pd.DataFrame({"Now": cur, "Usual": base}).fillna(0)
    mv["Change"] = mv["Now"] - mv["Usual"]
    mv = mv.reindex(mv["Change"].abs().sort_values(ascending=False).index).head(top_n)

    drivers = []
    for cat in mv.index:
        c = df[(df["Month"] == cur_cycle) & (df["Category"] == cat)].groupby("Merchant")["Amount"].sum()
        b = (df[df["Month"].isin(base_cycles) & (df["Category"] == cat)]
             .groupby("Merchant")["Amount"].sum() / len(base_cycles))
        idx = c.index.union(b.index)
        d   = c.reindex(idx).fillna(0) - b.reindex(idx).fillna(0)
        if d.empty:
            drivers.append(("—", 0.0))
        else:
            top = d.reindex(d.abs().sort_values(ascending=False).index).head(1)
            drivers.append((top.index[0], float(top.iloc[0])))

    mv["Driver"]        = [d[0] for d in drivers]
    mv["DriverChange"]  = [d[1] for d in drivers]
    return mv.reset_index().rename(columns={"index": "Category"})

# ── Chart helpers ─────────────────────────────────────────────────────────────

def hbar(df, x_col, y_col, color_col=None, title=None, height=320):
    """Horizontal bar sorted ascending (largest at top), text labels outside."""
    df = df.sort_values(x_col, ascending=True)
    df["_label"] = df[x_col].round(0).astype(int).apply(lambda v: f"OMR {v:,}")
    pct = df[x_col] / df[x_col].sum() * 100

    fig = px.bar(
        df, x=x_col, y=y_col, orientation="h",
        color=color_col if color_col else y_col,
        color_discrete_sequence=COLORS,
        text="_label",
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>OMR %{x:,.0f}<extra></extra>",
    )
    fig.update_layout(
        showlegend=bool(color_col and color_col != y_col),
        xaxis=dict(showticklabels=False, title="",
                   range=[0, df[x_col].max() * 1.35]),  # headroom for outside text
        yaxis_title="",
        margin=dict(t=30 if title else 10, b=0, r=10),
        height=height,
        title=title,
    )
    return fig

# ── App ───────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="BM Expense Tracker", page_icon="💳", layout="wide")
st.title("💳 Bank Muscat Expense Tracker")

overrides = load_overrides()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Statements")
    uploaded = st.file_uploader(
        "Upload XLS/XLSX",
        type=["xls", "xlsx"],
        accept_multiple_files=True,
        help="Bank Muscat portal → My Transactions → Export to Excel",
    )
    if uploaded:
        with st.spinner("Importing…"):
            n = ingest(uploaded)
        if n > 0:
            st.success(f"{n} new transaction(s) added")
        else:
            st.info("No new transactions (already imported)")
        st.rerun()

    raw, _is_demo_sidebar = load_data()
    if not raw.empty:
        st.divider()
        st.caption(f"{len(raw)} total transactions stored")
        if not _is_demo_sidebar:
            if st.button("Clear All Data", type="secondary"):
                DATA_FILE.unlink(missing_ok=True)
                OVR_FILE.unlink(missing_ok=True)
                st.rerun()

# ── Gate ──────────────────────────────────────────────────────────────────────
raw, is_demo = load_data()
if raw.empty:
    st.info("⬆️  Upload a Bank Muscat credit card statement XLS to get started.")
    st.stop()

if is_demo:
    st.info(
        "👋 **Demo mode** — you're viewing sample data so you can explore the app. "
        "Upload your own Bank Muscat XLS statement in the sidebar to see your real numbers.",
        icon="📊",
    )

df = apply_overrides(raw, overrides)

expenses = df[df["OMR Amount"] < 0].copy()
expenses["Amount"]   = expenses["OMR Amount"].abs()
expenses["Month"]    = expenses["Transaction Date"].apply(billing_cycle_month)
expenses["Year"]     = expenses["Month"].str[:4]
expenses["Merchant"] = expenses["Description"].apply(merchant_name)

# ── Cycle completeness ────────────────────────────────────────────────────────
# Averages, trends and "vs usual" comparisons must only ever use complete
# cycles.  The in-progress cycle is reported separately as a run-rate.
DATA_START = expenses["Transaction Date"].min()
COMPLETE_CYCLES, PARTIAL_CYCLES = split_cycles(expenses["Month"].unique(), DATA_START)
ALL_CYCLES     = sorted(expenses["Month"].unique())
INPROGRESS     = ALL_CYCLES[-1] if ALL_CYCLES and ALL_CYCLES[-1] in PARTIAL_CYCLES else None
RECURRING      = recurring_merchants(expenses, COMPLETE_CYCLES)
expenses["Type"] = expenses["Merchant"].apply(
    lambda m: "Recurring" if m in RECURRING else "One-off"
)

# Payment transactions for bill verification
payments = df[df["OMR Amount"] > 0].copy()
payments["Amount"] = payments["OMR Amount"]  # positive = payment received

# ── Sidebar Filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    all_months = sorted(expenses["Month"].unique())
    cycle_labels_map = {
        ym: cycle_label(ym) + (" (in progress)" if ym == INPROGRESS else "")
        for ym in all_months
    }
    sel_months = st.multiselect(
        "Billing Cycle", all_months, default=all_months,
        format_func=lambda ym: cycle_labels_map.get(ym, ym),
    )

    all_cats = [c for c in CATEGORIES if c in expenses["Category"].unique() and c != "Payment"]
    sel_cats = st.multiselect("Category", all_cats, default=all_cats)

flt = expenses[
    expenses["Month"].isin(sel_months) & expenses["Category"].isin(sel_cats)
].copy()

# ── Tabs ──────────────────────────────────────────────────────────────────────
t_overview, t_monthly, t_trends, t_travel, t_txns, t_reclassify = st.tabs(
    ["Overview", "Monthly Deep-Dive", "Trends", "Travel Analysis", "Transactions", "Reclassify"]
)

# ════════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ════════════════════════════════════════════════════════════════════════════════
with t_overview:
    if flt.empty:
        st.warning("No transactions for the selected filters.")
    else:
        # ── Cycle scope ────────────────────────────────────────────────────────
        # Everything comparative uses COMPLETE cycles only.  The in-progress
        # cycle is reported separately as a run-rate so a 6-day-old cycle never
        # masquerades as a spending collapse.
        cycle_list     = sorted(flt["Month"].unique())
        monthly_totals = flt.groupby("Month")["Amount"].sum()
        done_cycles    = [c for c in cycle_list if c in COMPLETE_CYCLES]
        live_cycle     = INPROGRESS if INPROGRESS in cycle_list else None

        if not done_cycles:
            st.warning(
                "No complete billing cycles in the current filter — "
                "every number below would be based on a partial cycle."
            )
            done_cycles = cycle_list          # degrade gracefully rather than crash

        cycle_avg    = monthly_totals[done_cycles].mean()
        latest_cycle = done_cycles[-1]
        latest_total = monthly_totals[latest_cycle]
        latest_data  = flt[flt["Month"] == latest_cycle]
        base_cycles  = done_cycles[-4:-1]      # the 3 cycles before the latest
        base_avg     = monthly_totals[base_cycles].mean() if base_cycles else None

        # Others warning — only shown when total unclassified spend is material
        others_amt = flt[flt["Category"] == "Others"]["Amount"].sum()
        n_others   = int((flt["Category"] == "Others").sum())
        if others_amt > OTHERS_WARN_OMR:
            st.warning(
                f"OMR {others_amt:,.0f} unclassified across {n_others} transaction(s) — "
                f"fix in **Reclassify** tab."
            )

        # ── In-progress cycle: run-rate, not a total ───────────────────────────
        if live_cycle:
            elapsed, total_days = cycle_progress(live_cycle)
            spent_so_far = monthly_totals.get(live_cycle, 0)
            run_rate     = spent_so_far / elapsed * total_days
            pace         = run_rate - cycle_avg
            verdict      = "above" if pace > 0 else "below"
            st.info(
                f"**{cycle_label(live_cycle)} is still open** — day {elapsed} of {total_days}. "
                f"OMR {spent_so_far:,.0f} spent so far, tracking toward "
                f"**~OMR {run_rate:,.0f}** by {cycle_dates(live_cycle).split('–')[1].strip()} "
                f"— OMR {abs(pace):,.0f} {verdict} your usual OMR {cycle_avg:,.0f}. "
                f"Excluded from every figure below.",
                icon="⏳",
            )

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 1 — LAST COMPLETE CYCLE
        # ══════════════════════════════════════════════════════════════════════
        st.subheader(f"Last Complete Cycle — {cycle_label(latest_cycle)}")
        st.caption(cycle_dates(latest_cycle))

        # ── 4 KPI cards ────────────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            # Compared against the 3-cycle average, not the previous cycle:
            # cycle-to-cycle swing is ~50% here, so "vs last month" is mostly noise.
            delta_vs_base = (
                f"{((latest_total - base_avg) / base_avg * 100):+.0f}% vs 3-cycle avg"
                if base_avg else None
            )
            st.metric("Total Spend", f"OMR {latest_total:,.0f}",
                      delta=delta_vs_base, delta_color="inverse")
            if base_avg:
                st.caption(f"3-cycle avg: OMR {base_avg:,.0f}")

        with c2:
            st.metric("Typical Cycle", f"OMR {cycle_avg:,.0f}",
                      help=f"Mean of {len(done_cycles)} complete billing cycles "
                           f"(partial cycles excluded)")
            st.caption(f"Median OMR {monthly_totals[done_cycles].median():,.0f} "
                       f"· {len(done_cycles)} cycles")

        with c3:
            # Recurring baseline — the part of a cycle that is already committed
            recent_done   = done_cycles[-6:]
            recent_data   = flt[flt["Month"].isin(recent_done)]
            recent_total  = recent_data["Amount"].sum()
            rec_total     = recent_data[recent_data["Type"] == "Recurring"]["Amount"].sum()
            rec_per_cyc   = rec_total / len(recent_done)
            rec_pct       = (rec_total / recent_total * 100) if recent_total else 0
            # Both halves must come from the same window, or they won't add up
            # to the cycle average the user sees next to them.
            disc_per_cyc  = (recent_total - rec_total) / len(recent_done)
            st.metric("Recurring Baseline", f"OMR {rec_per_cyc:,.0f}",
                      f"{rec_pct:.0f}% of spend", delta_color="off",
                      help=f"Merchants you pay in most cycles — the part of your "
                           f"spend that is committed before you decide anything. "
                           f"Measured over the last {len(recent_done)} complete cycles.")
            st.caption(f"Discretionary: OMR {disc_per_cyc:,.0f}/cycle")

        with c4:
            cat_totals  = latest_data.groupby("Category")["Amount"].sum()
            top_cat     = cat_totals.idxmax()
            top_cat_pct = cat_totals.max() / cat_totals.sum() * 100
            # Amount as the headline — category names are too long to survive
            # Streamlit's metric truncation ("Shopping & Retail" → "Shopping …")
            st.metric("Top Category", f"OMR {cat_totals.max():,.0f}",
                      f"{top_cat}  ·  {top_cat_pct:.0f}%", delta_color="off")

        # ── What changed, and who drove it ─────────────────────────────────────
        movers = category_movers(flt, latest_cycle, base_cycles)
        if not movers.empty:
            st.markdown("**What moved vs your usual**")
            mcols = st.columns(len(movers))
            for col, (_, r) in zip(mcols, movers.iterrows()):
                # The delta string must start with the signed number — Streamlit
                # reads that sign to pick the arrow direction and the colour.
                col.metric(
                    r["Category"], f"OMR {r['Now']:,.0f}",
                    f"{r['Change']:+,.0f} vs usual {r['Usual']:,.0f}",
                    delta_color="inverse",
                )
                col.caption(
                    f"↳ {r['Driver']} ({r['DriverChange']:+,.0f})"
                    if r["Driver"] != "—" else ""
                )

        st.divider()

        # ── Category breakdown (latest cycle) + Top transactions ───────────────
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown("**Spend by Category**")
            cat_df = (
                latest_data.groupby("Category")["Amount"].sum()
                .reset_index().sort_values("Amount", ascending=False)
            )
            cat_df["Pct"]    = (cat_df["Amount"] / cat_df["Amount"].sum() * 100).round(1)
            cat_df["_label"] = cat_df.apply(
                lambda r: f"OMR {int(round(r['Amount'])):,}  ({r['Pct']:.0f}%)", axis=1
            )
            cat_df = cat_df.sort_values("Amount", ascending=False)

            fig_cat = px.bar(
                cat_df, x="Amount", y="Category", orientation="h",
                color="Category", color_discrete_sequence=COLORS,
                text="_label", custom_data=["Pct"],
            )
            fig_cat.update_traces(
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>OMR %{x:,.0f}  (%{customdata[0]}%)<extra></extra>",
            )
            fig_cat.update_layout(
                showlegend=False,
                xaxis=dict(showticklabels=False, title="",
                           range=[0, cat_df["Amount"].max() * 1.45]),
                yaxis_title="",
                # Top margin keeps the largest bar's label clear of the
                # Plotly toolbar, which overlays the chart's top-right on hover.
                margin=dict(t=28, b=0, r=10),
                height=max(300, len(cat_df) * 36),
            )
            st.plotly_chart(fig_cat, width="stretch", config=CHART_CFG)

        with col_right:
            st.markdown("**Top Transactions**")
            top_txns = (
                latest_data.nlargest(12, "Amount")
                [["Transaction Date", "Merchant", "Amount", "Category"]].copy()
            )
            top_txns["Transaction Date"] = top_txns["Transaction Date"].dt.strftime("%d %b")
            top_txns["Amount"]           = top_txns["Amount"].round(0).astype(int)
            top_txns = top_txns.rename(columns={
                "Transaction Date": "Date", "Amount": "OMR",
            })
            st.dataframe(top_txns, hide_index=True, width="stretch",
                         height=max(280, len(cat_df) * 36))

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 2 — WHAT'S COMMITTED
        # ══════════════════════════════════════════════════════════════════════
        st.divider()
        st.subheader("Committed vs Discretionary")
        st.caption(
            f"Based on the last {len(recent_done)} complete cycles. **Recurring** = "
            f"merchants you pay in at least 4 of the last 6 cycles."
        )

        rec_col, list_col = st.columns([2, 3])

        with rec_col:
            split = (
                recent_data.groupby("Type")["Amount"].sum()
                .reindex(["Recurring", "One-off"]).fillna(0) / len(recent_done)
            )
            fig_split = go.Figure(go.Bar(
                x=split.values, y=split.index, orientation="h",
                marker_color=["#80cbc4", "#c5cae9"],
                text=[f"OMR {v:,.0f}/cycle" for v in split.values],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>OMR %{x:,.0f} per cycle<extra></extra>",
            ))
            fig_split.update_layout(
                xaxis=dict(showticklabels=False, title="",
                           range=[0, split.max() * 1.5]),
                yaxis_title="", margin=dict(t=10, b=0, r=10),
                height=170, showlegend=False,
            )
            st.plotly_chart(fig_split, width="stretch", config=CHART_CFG)
            st.caption(
                f"About **OMR {rec_per_cyc:,.0f}** of a typical cycle is spoken for "
                f"before you make a single choice."
            )

        with list_col:
            rec_rows = recent_data[recent_data["Type"] == "Recurring"]
            if rec_rows.empty:
                st.info("No recurring merchants detected yet — needs ~6 complete cycles.")
            else:
                per_cyc = rec_rows.groupby(["Merchant", "Month"])["Amount"].sum()
                agg     = per_cyc.groupby("Merchant").agg(
                    Cycles="count", _mean="mean", _std="std"
                ).fillna(0)
                agg["Per Cycle"] = (per_cyc.groupby("Merchant").sum()
                                    / len(recent_done)).round(1)
                agg["Pattern"] = (agg["_std"] / agg["_mean"]).apply(
                    lambda cv: "steady" if cv <= 0.40 else "variable"
                )
                agg = (agg[["Per Cycle", "Cycles", "Pattern"]]
                       .sort_values("Per Cycle", ascending=False)
                       .reset_index())
                agg["Cycles"] = agg["Cycles"].astype(int).astype(str) + f"/{len(recent_done)}"
                agg = agg.rename(columns={"Per Cycle": "OMR / cycle"})
                st.dataframe(agg, hide_index=True, width="stretch", height=280)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 3 — SPENDING HISTORY
        # ══════════════════════════════════════════════════════════════════════
        st.divider()
        st.subheader("Spending History")

        monthly = monthly_totals.reset_index()
        monthly.columns     = ["Month", "Amount"]
        monthly["Label"]    = monthly["Month"].apply(cycle_label)
        monthly["Complete"] = monthly["Month"].isin(COMPLETE_CYCLES)
        monthly["AmtText"]  = monthly.apply(
            lambda r: f"OMR {int(round(r['Amount'])):,}" + ("" if r["Complete"] else " so far"),
            axis=1,
        )

        # Partial cycles are drawn hollow — present for context, but visibly
        # not comparable to the complete cycles around them.
        bar_colors = [
            ("#ef9a9a" if amt > cycle_avg else "#90caf9") if done else "#e0e0e0"
            for amt, done in zip(monthly["Amount"], monthly["Complete"])
        ]
        bar_lines = ["#bdbdbd" if not done else "rgba(0,0,0,0)" for done in monthly["Complete"]]
        y_max     = monthly["Amount"].max() * 1.22

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=monthly["Label"], y=monthly["Amount"],
            marker=dict(color=bar_colors,
                        line=dict(color=bar_lines, width=1.5)),
            text=monthly["AmtText"], textposition="outside",
            name="Cycle spend",
            customdata=monthly["Complete"].map({True: "complete", False: "partial cycle"}),
            hovertemplate="<b>%{x}</b><br>OMR %{y:,.0f}<br><i>%{customdata}</i><extra></extra>",
        ))
        fig_trend.add_hline(
            y=cycle_avg,
            line_dash="dot", line_color="#555", line_width=2,
            annotation_text=f"Avg  OMR {cycle_avg:,.0f}",
            annotation_position="top left",
            annotation_font_color="#555",
        )
        fig_trend.update_layout(
            xaxis_title="", yaxis_title="OMR",
            yaxis=dict(tickformat=",d", range=[0, y_max]),
            showlegend=False,
            margin=dict(t=20, b=0), height=320,
        )
        st.plotly_chart(fig_trend, width="stretch", config=CHART_CFG)
        st.caption(
            "🔴 Above average  🔵 Below average  ⬜ Partial cycle — excluded from "
            "the average and every comparison"
        )


# ════════════════════════════════════════════════════════════════════════════════
# MONTHLY DEEP-DIVE
# ════════════════════════════════════════════════════════════════════════════════
with t_monthly:
    if flt.empty:
        st.warning("No data.")
    else:
        month_options = sorted(flt["Month"].unique(), reverse=True)
        # Land on the most recent COMPLETE cycle, not the in-progress one —
        # otherwise the tab opens on a partial total and a meaningless delta.
        _default_i = next(
            (i for i, ym in enumerate(month_options) if ym in COMPLETE_CYCLES), 0
        )
        sel_month = st.selectbox(
            "Select Billing Cycle", month_options, index=_default_i,
            format_func=lambda ym: cycle_labels_map.get(ym, ym),
        )
        st.caption(f"Cycle period: **{cycle_dates(sel_month)}**")
        m_data = flt[flt["Month"] == sel_month]

        if sel_month not in COMPLETE_CYCLES:
            if sel_month == INPROGRESS:
                el, tot = cycle_progress(sel_month)
                st.info(
                    f"This cycle is still open — day {el} of {tot}. Totals below are "
                    f"partial, so comparisons against full cycles will look low.",
                    icon="⏳",
                )
            else:
                st.info(
                    "Your data doesn't cover the start of this cycle, so the totals "
                    "below are incomplete.",
                    icon="⏳",
                )

        # Previous billing cycle for deltas
        idx = month_options.index(sel_month)
        prev_month = month_options[idx + 1] if idx + 1 < len(month_options) else None
        prev_data  = flt[flt["Month"] == prev_month] if prev_month else pd.DataFrame()

        total_curr = m_data["Amount"].sum()
        total_prev = prev_data["Amount"].sum() if not prev_data.empty else None
        prev_label = cycle_label(prev_month) if prev_month else ""
        pct_delta  = f"{((total_curr - total_prev) / total_prev * 100):+.0f}% vs {prev_label}" if total_prev else None

        ca, cb, cc, cd = st.columns(4)
        ca.metric("Total Spend",     f"OMR {total_curr:,.0f}",
                  delta=pct_delta, delta_color="inverse")
        cb.metric("Transactions",    len(m_data),
                  delta=f"{len(m_data) - len(prev_data):+d} vs prev" if not prev_data.empty else None)
        cc.metric("Avg Transaction", f"OMR {m_data['Amount'].mean():,.0f}")
        cd.metric("Largest Item",    f"OMR {m_data['Amount'].max():,.0f}")

        st.divider()
        col1, col2 = st.columns([3, 2])

        with col1:
            st.subheader("Category Breakdown")
            cat_m = m_data.groupby("Category")["Amount"].sum().reset_index()
            st.plotly_chart(
                hbar(cat_m, "Amount", "Category", height=280),
                width="stretch", config=CHART_CFG,
            )

            st.subheader("Cumulative Spend Through Month")
            cumul = (
                m_data.sort_values("Transaction Date")
                .assign(Cumulative=lambda d: d["Amount"].cumsum())
            )
            fig_cumul = px.line(
                cumul, x="Transaction Date", y="Cumulative",
                markers=True, color_discrete_sequence=["#4a90d9"],
                custom_data=["Description", "Amount"],
            )
            fig_cumul.update_traces(
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "OMR %{customdata[1]:,.0f}<br>"
                    "Running total: OMR %{y:,.0f}<extra></extra>"
                ),
            )
            fig_cumul.update_layout(
                xaxis_title="", yaxis_title="Cumulative OMR",
                yaxis=dict(tickformat=",d"), margin=dict(t=10, b=0), height=240,
            )
            st.plotly_chart(fig_cumul, width="stretch", config=CHART_CFG)

        with col2:
            st.subheader("Top 10 Transactions")
            top10 = (
                m_data.nlargest(10, "Amount")
                [["Transaction Date", "Description", "Amount", "Category"]].copy()
            )
            top10["Transaction Date"] = top10["Transaction Date"].dt.strftime("%d %b")
            top10["Amount"] = top10["Amount"].round(0).astype(int)
            top10 = top10.rename(columns={"Amount": "OMR", "Transaction Date": "Date"})
            st.dataframe(top10, hide_index=True, width="stretch", height=280)

            if not prev_data.empty:
                st.subheader(f"Change vs {cycle_label(prev_month)}")
                curr_cat = m_data.groupby("Category")["Amount"].sum()
                prev_cat = prev_data.groupby("Category")["Amount"].sum()
                cmp = (
                    pd.DataFrame({"curr": curr_cat, "prev": prev_cat})
                    .fillna(0)
                    .assign(Change=lambda d: d["curr"] - d["prev"])
                    .reset_index()
                    .sort_values("Change", ascending=False)
                )
                cmp["_label"] = cmp["Change"].apply(
                    lambda v: f"{'+' if v >= 0 else ''}OMR {int(round(v)):,}"
                )

                # Name the merchant behind each category move — a category delta
                # on its own never says who caused it.
                drivers = category_movers(flt, sel_month, [prev_month], top_n=len(cmp))
                driver_map = dict(zip(drivers["Category"], drivers["Driver"])) if not drivers.empty else {}
                cmp["Driver"] = cmp["Category"].map(driver_map).fillna("—")

                fig_cmp = px.bar(
                    cmp, x="Category", y="Change",
                    color="Change",
                    color_continuous_scale=["#ef5350", "#ffcc80", "#66bb6a"],
                    color_continuous_midpoint=0,
                    text="_label", custom_data=["Driver"],
                )
                fig_cmp.update_traces(
                    textposition="outside",
                    hovertemplate=(
                        "<b>%{x}</b><br>Change: OMR %{y:,.0f}"
                        "<br>Driven by: %{customdata[0]}<extra></extra>"
                    ),
                )
                _cmp_abs = cmp["Change"].abs().max() if not cmp.empty else 1
                fig_cmp.update_layout(
                    xaxis_title="", yaxis_title="OMR",
                    yaxis=dict(tickformat=",d",
                               range=[-_cmp_abs * 1.35, _cmp_abs * 1.35]),
                    coloraxis_showscale=False,
                    xaxis=dict(tickangle=-40),
                    margin=dict(t=10, b=80), height=320,
                )
                st.plotly_chart(fig_cmp, width="stretch", config=CHART_CFG)

        st.subheader("All Transactions This Cycle")
        show_m = m_data[["Transaction Date", "Description", "City", "Amount", "Category"]].copy()
        show_m["Transaction Date"] = show_m["Transaction Date"].dt.strftime("%d %b %Y")
        show_m["Amount"] = show_m["Amount"].round(0).astype(int)
        show_m = (
            show_m.rename(columns={"Amount": "OMR Amount"})
            .sort_values("OMR Amount", ascending=False)
        )
        st.dataframe(show_m, hide_index=True, width="stretch")

        # ── Bill Verification ───────────────────────────────────────────────────
        st.divider()
        st.subheader("Bill Verification")
        st.caption(
            "Your payment for this cycle should equal the **Cycle Total** above. "
            "Payments are typically posted in the following cycle."
        )

        # Build per-cycle reconciliation table
        cycle_totals = (
            expenses.groupby("Month")["Amount"].sum()
            .reset_index().rename(columns={"Month": "Cycle", "Amount": "Expenses (OMR)"})
            .sort_values("Cycle", ascending=False)
        )
        cycle_totals["Period"] = cycle_totals["Cycle"].apply(cycle_label)
        cycle_totals["Expenses (OMR)"] = cycle_totals["Expenses (OMR)"].round(0).astype(int)

        # Match each payment to the cycle whose end date is just before the payment
        def payment_cycle(pay_date):
            """Find which billing cycle this payment most likely settles."""
            for ym in sorted(cycle_totals["Cycle"].tolist(), reverse=True):
                if pay_date >= cycle_end(ym):
                    return ym
            return None

        if not payments.empty:
            pay_summary = (
                payments[["Transaction Date", "Amount"]]
                .copy()
                .sort_values("Transaction Date", ascending=False)
            )
            pay_summary["Settles Cycle"] = pay_summary["Transaction Date"].apply(payment_cycle)
            pay_by_cycle = (
                pay_summary.groupby("Settles Cycle")["Amount"]
                .sum().reset_index()
                .rename(columns={"Settles Cycle": "Cycle", "Amount": "Payment (OMR)"})
            )
            pay_by_cycle["Payment (OMR)"] = pay_by_cycle["Payment (OMR)"].round(0).astype(int)

            recon = cycle_totals.merge(pay_by_cycle, on="Cycle", how="left")
            recon["Payment (OMR)"] = recon["Payment (OMR)"].fillna(0).astype(int)
            recon["Difference"] = recon["Payment (OMR)"] - recon["Expenses (OMR)"]
            recon = recon[["Period", "Expenses (OMR)", "Payment (OMR)", "Difference"]]

            st.dataframe(
                recon.style.map(
                    lambda v: "color: green" if v == 0 else ("color: red" if isinstance(v, (int, float)) and v != 0 else ""),
                    subset=["Difference"],
                ),
                hide_index=True, width="stretch",
            )
            st.caption(
                "Difference = Payment − Expenses. "
                "Zero means the payment exactly matched the bill. "
                "Negative means underpayment, positive means overpayment or credit."
            )
        else:
            st.info("No payment transactions found in the data yet.")


# ════════════════════════════════════════════════════════════════════════════════
# TRENDS
# ════════════════════════════════════════════════════════════════════════════════
with t_trends:
    if flt.empty:
        st.warning("No data.")
    elif len(flt["Month"].unique()) < 2:
        st.info("Upload at least 2 months of data to see trends.")
    else:
        trend_cat = flt.groupby(["Month", "Category"])["Amount"].sum().reset_index()
        trend_cat["Label"] = trend_cat["Month"].apply(cycle_label)

        # ── Section 1: Category Deep Dive (select + drill-down) ────────────────
        st.subheader("Category Deep Dive")
        cat_options = sorted(flt["Category"].unique())
        sel_cat = st.selectbox("Select category to explore", cat_options, key="trends_cat")

        cat_data    = flt[flt["Category"] == sel_cat]
        cat_monthly = cat_data.groupby("Month")["Amount"].sum().reset_index()
        cat_monthly["Label"]    = cat_monthly["Month"].apply(cycle_label)
        cat_monthly["Complete"] = cat_monthly["Month"].isin(COMPLETE_CYCLES)
        cat_monthly["AmtText"]  = cat_monthly["Amount"].round(0).astype(int).apply(lambda v: f"OMR {v:,}")

        # Average over complete cycles only — a partial cycle would drag it down
        _done = cat_monthly[cat_monthly["Complete"]]
        cat_avg = _done["Amount"].mean() if not _done.empty else cat_monthly["Amount"].mean()

        fig_cat_trend = go.Figure()
        fig_cat_trend.add_trace(go.Bar(
            x=cat_monthly["Label"], y=cat_monthly["Amount"],
            text=cat_monthly["AmtText"], textposition="outside",
            marker=dict(
                color=["#90caf9" if c else "#e0e0e0" for c in cat_monthly["Complete"]],
                line=dict(color=["rgba(0,0,0,0)" if c else "#bdbdbd"
                                 for c in cat_monthly["Complete"]], width=1.5),
            ),
            customdata=cat_monthly["Complete"].map({True: "complete", False: "partial cycle"}),
            hovertemplate="<b>%{x}</b><br>OMR %{y:,.0f}<br><i>%{customdata}</i><extra></extra>",
        ))
        fig_cat_trend.add_hline(
            y=cat_avg, line_dash="dot", line_color="#555", line_width=1.5,
            annotation_text=f"Avg  OMR {cat_avg:,.0f}",
            annotation_position="top left", annotation_font_color="#555",
        )
        fig_cat_trend.update_layout(
            xaxis_title="", yaxis_title="OMR",
            yaxis=dict(tickformat=",d",
                       range=[0, cat_monthly["Amount"].max() * 1.22]),
            showlegend=False,
            margin=dict(t=20, b=0), height=280,
        )
        st.plotly_chart(fig_cat_trend, width="stretch", config=CHART_CFG)

        # Drill-down: pick one or more billing cycles → see every transaction
        st.subheader(f"Transaction Breakdown — {sel_cat}")
        drill_cycles = sorted(cat_monthly["Month"].tolist(), reverse=True)
        drill_labels_map = {ym: cycle_label(ym) for ym in drill_cycles}
        sel_drill = st.multiselect(
            "Select billing cycle(s)",
            drill_cycles,
            default=[drill_cycles[0]] if drill_cycles else [],
            format_func=lambda ym: drill_labels_map.get(ym, ym),
            key="trends_drill",
        )

        if not sel_drill:
            st.info("Select at least one billing cycle above.")
        else:
            drill_src  = cat_data[cat_data["Month"].isin(sel_drill)]
            drill_txns = drill_src[
                ["Transaction Date", "Month", "Merchant", "Description", "City", "Amount"]
            ].copy()
            drill_txns["Date"]  = drill_txns["Transaction Date"].dt.strftime("%d %b %Y")
            drill_txns["OMR"]   = drill_txns["Amount"].round(0).astype(int)
            drill_txns["Cycle"] = drill_txns["Month"].apply(cycle_label)
            drill_txns = drill_txns[["Date", "Cycle", "Merchant", "Description", "City", "OMR"]]
            drill_txns = drill_txns.sort_values("OMR", ascending=False)

            col_tbl, col_chart = st.columns([3, 2])
            with col_tbl:
                total_drill = drill_txns["OMR"].sum()
                st.caption(
                    f"{len(drill_txns)} transaction(s) · OMR {total_drill:,} total · "
                    f"{drill_txns['Merchant'].nunique()} merchant(s)"
                )
                st.dataframe(drill_txns, hide_index=True, width="stretch")
            with col_chart:
                # Grouped by normalised merchant, so the same shop doesn't get
                # split across several slices by its bank description variants.
                merch = (
                    drill_src.groupby("Merchant")["Amount"].sum()
                    .round(0).astype(int).reset_index()
                    .sort_values("Amount", ascending=False)
                )
                if len(merch) > 1:
                    fig_pie = px.pie(
                        merch, values="Amount", names="Merchant",
                        color_discrete_sequence=COLORS, hole=0.35,
                    )
                    fig_pie.update_traces(
                        textinfo="percent", textposition="inside",
                        hovertemplate="<b>%{label}</b><br>OMR %{value:,}<br>%{percent}<extra></extra>",
                    )
                    fig_pie.update_layout(showlegend=True, margin=dict(t=10, b=0), height=260)
                    st.plotly_chart(fig_pie, width="stretch", config=CHART_CFG)

        st.divider()

        # ── Section 2: Merchants ───────────────────────────────────────────────
        st.subheader("Merchants")
        st.caption(
            "Bank descriptions are collapsed to one name per merchant — petrol "
            "stations, order references and gateway prefixes are stripped."
        )

        done_flt = [c for c in sorted(flt["Month"].unique()) if c in COMPLETE_CYCLES]
        m_src    = flt[flt["Month"].isin(done_flt)] if done_flt else flt
        n_cyc    = max(len(done_flt), 1)

        col_top, col_chg = st.columns([3, 2])

        with col_top:
            st.markdown("**Where the money actually goes**")
            lead = m_src.groupby("Merchant").agg(
                Total=("Amount", "sum"),
                Txns=("Amount", "count"),
                Cycles=("Month", "nunique"),
            ).sort_values("Total", ascending=False).head(15).reset_index()
            lead["Per Cycle"] = (lead["Total"] / n_cyc).round(1)
            lead["Total"]     = lead["Total"].round(0).astype(int)
            lead["Seen in"]   = lead["Cycles"].astype(str) + f"/{n_cyc}"
            lead = lead[["Merchant", "Total", "Per Cycle", "Txns", "Seen in"]]
            lead = lead.rename(columns={"Total": "Total OMR", "Per Cycle": "OMR / cycle"})
            st.dataframe(lead, hide_index=True, width="stretch", height=380)

        with col_chg:
            # New vs lapsed: a merchant that quietly stops billing you (or quietly
            # starts) is invisible in any category-level view.
            st.markdown("**Started & stopped**")
            if len(done_flt) < 4:
                st.info("Needs at least 4 complete cycles.")
            else:
                recent_w = done_flt[-3:]
                prior_w  = done_flt[:-3]
                recent_m = set(m_src[m_src["Month"].isin(recent_w)]["Merchant"])
                prior_m  = set(m_src[m_src["Month"].isin(prior_w)]["Merchant"])

                started = m_src[
                    m_src["Merchant"].isin(recent_m - prior_m)
                    & m_src["Month"].isin(recent_w)
                ].groupby("Merchant")["Amount"].sum().sort_values(ascending=False).head(6)

                # Only flag a lapse for merchants that were an established habit
                established = (
                    m_src[m_src["Month"].isin(prior_w)]
                    .groupby("Merchant")["Month"].nunique()
                )
                lapsed_names = [
                    m for m in (prior_m - recent_m)
                    if established.get(m, 0) >= max(3, len(prior_w) // 3)
                ]
                lapsed = (
                    m_src[m_src["Merchant"].isin(lapsed_names)]
                    .groupby("Merchant")["Amount"].sum()
                    .sort_values(ascending=False).head(6)
                )

                st.caption(f"Comparing last 3 cycles vs the {len(prior_w)} before")
                if not started.empty:
                    st.markdown("🆕 **New**")
                    for m, v in started.items():
                        st.markdown(f"<small>{m} — OMR {v:,.0f}</small>",
                                    unsafe_allow_html=True)
                if not lapsed.empty:
                    st.markdown("🛑 **Stopped**")
                    for m, v in lapsed.items():
                        last_seen = m_src[m_src["Merchant"] == m]["Month"].max()
                        st.markdown(
                            f"<small>{m} — was OMR {v:,.0f}, last seen "
                            f"{cycle_label(last_seen)}</small>",
                            unsafe_allow_html=True,
                        )
                if started.empty and lapsed.empty:
                    st.info("No merchants started or stopped recently.")

        st.divider()

        # ── Section 3: Monthly total + 3-cycle rolling average ─────────────────
        col_a, col_b = st.columns([3, 2])

        with col_a:
            st.subheader("All Categories — Monthly Total & 3-Cycle Rolling Avg")
            monthly = flt.groupby("Month")["Amount"].sum().reset_index()
            monthly["Label"]    = monthly["Month"].apply(cycle_label)
            monthly["Complete"] = monthly["Month"].isin(COMPLETE_CYCLES)

            # The rolling average is computed over complete cycles only and left
            # blank on partial ones — otherwise a half-finished cycle drags the
            # trend line into a fake decline.
            _series = monthly["Amount"].where(monthly["Complete"])
            monthly["Rolling3"] = (
                _series.rolling(3, min_periods=1).mean().where(monthly["Complete"])
            )

            fig_roll = go.Figure()
            fig_roll.add_trace(go.Bar(
                x=monthly["Label"], y=monthly["Amount"],
                name="Monthly Total",
                marker=dict(
                    color=["#90caf9" if c else "#e0e0e0" for c in monthly["Complete"]],
                    line=dict(color=["rgba(0,0,0,0)" if c else "#bdbdbd"
                                     for c in monthly["Complete"]], width=1.5),
                ),
                customdata=monthly["Complete"].map({True: "complete", False: "partial cycle"}),
                hovertemplate="<b>%{x}</b><br>OMR %{y:,.0f}<br><i>%{customdata}</i><extra></extra>",
            ))
            fig_roll.add_trace(go.Scatter(
                x=monthly["Label"], y=monthly["Rolling3"],
                mode="lines+markers", name="3-Cycle Avg",
                line=dict(color="#e65100", width=2), marker=dict(size=6),
                connectgaps=False,
                hovertemplate="3-Cycle Avg: OMR %{y:,.0f}<extra></extra>",
            ))
            fig_roll.update_layout(
                xaxis_title="", yaxis_title="OMR",
                yaxis=dict(tickformat=",d"), legend_title="",
                margin=dict(t=10, b=0), height=300,
            )
            st.plotly_chart(fig_roll, width="stretch", config=CHART_CFG)

        with col_b:
            st.subheader("Cycle Totals")
            monthly_show = monthly[["Label", "Amount", "Rolling3", "Complete"]].copy()
            monthly_show["Amount"]   = monthly_show["Amount"].round(0).astype(int)
            monthly_show["Rolling3"] = monthly_show["Rolling3"].apply(
                lambda v: "—" if pd.isna(v) else f"{v:,.0f}"
            )
            monthly_show["Label"]    = monthly_show.apply(
                lambda r: r["Label"] if r["Complete"] else f"{r['Label']} (partial)", axis=1
            )
            monthly_show = monthly_show.drop(columns=["Complete"]).rename(
                columns={"Label": "Cycle", "Amount": "Total (OMR)", "Rolling3": "3-Cycle Avg"}
            ).iloc[::-1].reset_index(drop=True)
            st.dataframe(monthly_show, hide_index=True, width="stretch", height=300)

        st.divider()

        # ── Section 4: Category mix (% stacked) ────────────────────────────────
        st.subheader("Category Mix Over Time (% of Monthly Spend)")
        # Partial cycles are dropped entirely here: in a proportional view a
        # cycle with two transactions reads as "100% Groceries", which is noise
        # rather than a shift in habits.
        trend_cat_done = trend_cat[trend_cat["Month"].isin(COMPLETE_CYCLES)]
        if trend_cat_done.empty:
            st.info("No complete billing cycles in the current filter.")
        else:
            st.caption("Complete billing cycles only.")

            # Pre-compute % so hovertemplate can show the correct normalised value
            trend_cat_pct = trend_cat_done.copy()
            month_totals  = trend_cat_pct.groupby("Month")["Amount"].transform("sum")
            trend_cat_pct["Pct"] = (trend_cat_pct["Amount"] / month_totals * 100).round(1)
            fig_pct = px.bar(
                trend_cat_pct, x="Label", y="Amount", color="Category",
                color_discrete_sequence=COLORS,
                custom_data=["Pct"],
            )
            fig_pct.update_traces(
                hovertemplate="<b>%{fullData.name}</b><br>%{x}<br>%{customdata[0]:.1f}%<extra></extra>",
            )
            fig_pct.update_layout(
                barnorm="percent",
                xaxis_title="", yaxis_title="% of Spend",
                legend_title="", margin=dict(t=10, b=0), height=320,
            )
            st.plotly_chart(fig_pct, width="stretch", config=CHART_CFG)

        # ── Section 5: Year-over-Year (only if multiple years) ─────────────────
        years = sorted(flt["Year"].unique())
        if len(years) > 1:
            st.divider()
            st.subheader("Year-over-Year Summary")
            yoy_cat = flt.groupby(["Year", "Category"])["Amount"].sum().reset_index()
            fig_yoy = px.bar(
                yoy_cat, x="Category", y="Amount", color="Year",
                barmode="group", color_discrete_sequence=["#42a5f5", "#ef5350", "#66bb6a"],
            )
            fig_yoy.update_traces(
                hovertemplate="<b>%{x}</b><br>%{fullData.name}<br>OMR %{y:,.0f}<extra></extra>",
            )
            fig_yoy.update_layout(
                xaxis_title="", yaxis_title="OMR",
                yaxis=dict(tickformat=",d",
                           range=[0, yoy_cat["Amount"].max() * 1.12]),
                legend_title="Year",
                xaxis=dict(tickangle=-30),
                margin=dict(t=10, b=80), height=380,
            )
            st.plotly_chart(fig_yoy, width="stretch", config=CHART_CFG)

            # Summary table
            yoy_total = flt.groupby("Year")["Amount"].agg(
                Total="sum", Transactions="count", Avg_Month=lambda x: x.sum() / flt.loc[x.index, "Month"].nunique()
            ).reset_index()
            yoy_total["Total"] = yoy_total["Total"].round(0).astype(int)
            yoy_total["Avg_Month"] = yoy_total["Avg_Month"].round(0).astype(int)
            yoy_total.columns = ["Year", "Total Spend (OMR)", "Transactions", "Avg/Month (OMR)"]
            st.dataframe(yoy_total, hide_index=True, width="stretch")


# ════════════════════════════════════════════════════════════════════════════════
# TRAVEL ANALYSIS
# ════════════════════════════════════════════════════════════════════════════════
with t_travel:
    travel_cat = "Travel & Transport"

    # Cycles that contain any Travel & Transport spend (using full expenses, not flt)
    travel_cycles = sorted(
        expenses[expenses["Category"] == travel_cat]["Month"].unique()
    )

    if not travel_cycles:
        st.info("No Travel & Transport transactions found. "
                "Upload more statements or check the Reclassify tab.")
    else:
        # Default to most recent travel cycle
        default_idx = len(travel_cycles) - 1
        sel_travel_cycle = st.selectbox(
            "Select billing cycle",
            travel_cycles,
            index=default_idx,
            format_func=lambda ym: f"{cycle_label(ym)}  ({cycle_dates(ym)})",
            key="travel_cycle_sel",
        )

        # All expenses for selected cycle (unfiltered by sidebar category — we want full picture)
        cycle_all = expenses[expenses["Month"] == sel_travel_cycle].copy()
        cycle_travel = cycle_all[cycle_all["Category"] == travel_cat].copy()
        cycle_other  = cycle_all[cycle_all["Category"] != travel_cat]

        total_cycle   = cycle_all["Amount"].sum()
        total_travel  = cycle_travel["Amount"].sum()
        total_other   = cycle_other["Amount"].sum()

        # ── KPI row ────────────────────────────────────────────────────────────
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Cycle Spend",      f"OMR {total_cycle:,.0f}")
        k2.metric("Travel & Transport",     f"OMR {total_travel:,.0f}",
                  f"{total_travel / total_cycle * 100:.0f}% of cycle" if total_cycle else None)
        k3.metric("All Other Categories",   f"OMR {total_other:,.0f}")
        k4.metric("Travel Transactions",    f"{len(cycle_travel)}")

        st.divider()

        # ── Two columns: full category breakdown + travel sub-categories ───────
        col_a, col_b = st.columns([1, 1])

        with col_a:
            st.subheader("Full Spend by Category")
            cat_breakdown = (
                cycle_all.groupby("Category")["Amount"].sum()
                .reset_index().sort_values("Amount", ascending=True)
            )
            cat_breakdown["_label"] = (
                cat_breakdown["Amount"].round(0).astype(int).apply(lambda v: f"OMR {v:,}")
            )
            # Highlight travel category
            cat_breakdown["_color"] = cat_breakdown["Category"].apply(
                lambda c: "#ef9a9a" if c == travel_cat else "#90caf9"
            )
            fig_cat = go.Figure(go.Bar(
                x=cat_breakdown["Amount"],
                y=cat_breakdown["Category"],
                orientation="h",
                marker_color=cat_breakdown["_color"],
                text=cat_breakdown["_label"],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>OMR %{x:,.0f}<extra></extra>",
            ))
            fig_cat.update_layout(
                xaxis_title="", yaxis_title="",
                xaxis=dict(showticklabels=False,
                           range=[0, cat_breakdown["Amount"].max() * 1.35]),
                margin=dict(t=10, b=0, r=10), height=320,
                showlegend=False,
            )
            st.plotly_chart(fig_cat, width="stretch", config=CHART_CFG)
            st.caption(f"🔴 Travel & Transport  🔵 Other categories")

        with col_b:
            st.subheader("Travel Breakdown")
            if cycle_travel.empty:
                st.info("No Travel & Transport spend in this cycle.")
            else:
                cycle_travel = cycle_travel.copy()
                cycle_travel["SubCategory"] = cycle_travel["Description"].apply(travel_subcat)
                sub_df = (
                    cycle_travel.groupby("SubCategory")["Amount"].sum()
                    .reset_index().sort_values("Amount", ascending=True)
                )
                sub_df["_label"] = (
                    sub_df["Amount"].round(0).astype(int).apply(lambda v: f"OMR {v:,}")
                )
                fig_sub = go.Figure(go.Bar(
                    x=sub_df["Amount"],
                    y=sub_df["SubCategory"],
                    orientation="h",
                    marker_color="#80cbc4",
                    text=sub_df["_label"],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>OMR %{x:,.0f}<extra></extra>",
                ))
                fig_sub.update_layout(
                    xaxis_title="", yaxis_title="",
                    xaxis=dict(showticklabels=False,
                               range=[0, sub_df["Amount"].max() * 1.35]),
                    margin=dict(t=10, b=0, r=10), height=320,
                    showlegend=False,
                )
                st.plotly_chart(fig_sub, width="stretch", config=CHART_CFG)

        st.divider()

        # ── Full transaction table for the cycle ───────────────────────────────
        st.subheader(f"All Transactions — {cycle_label(sel_travel_cycle)}")

        # Add sub-category column for travel rows
        display_travel = cycle_all.copy()
        display_travel["SubCategory"] = display_travel.apply(
            lambda r: travel_subcat(r["Description"]) if r["Category"] == travel_cat else "—",
            axis=1,
        )
        display_travel = display_travel[
            ["Transaction Date", "Description", "City", "Country",
             "Amount", "Category", "SubCategory"]
        ].sort_values("Amount", ascending=False).copy()
        display_travel["Amount"] = display_travel["Amount"].round(0).astype(int)
        display_travel["Transaction Date"] = display_travel["Transaction Date"].dt.strftime("%d %b %Y")
        display_travel = display_travel.rename(columns={"Amount": "OMR Amount"})
        st.dataframe(display_travel, hide_index=True, width="stretch")


# ════════════════════════════════════════════════════════════════════════════════
# TRANSACTIONS
# ════════════════════════════════════════════════════════════════════════════════
with t_txns:
    search = st.text_input("Search merchant", placeholder="e.g. LULU SPAR  or  LULU, SPAR  (space or comma separates terms)")
    show_flt = flt
    if search:
        # Split on commas or whitespace; match any term (OR logic)
        terms = [t.strip().upper() for t in search.replace(",", " ").split() if t.strip()]
        desc_upper = flt["Description"].str.upper()
        mask = desc_upper.apply(lambda d: any(t in d for t in terms))
        show_flt = flt[mask]

    st.caption(f"{len(show_flt)} transaction(s)")

    # Month-on-month chart when a search filter is active
    if search and not show_flt.empty:
        srch_monthly = (
            show_flt.groupby("Month")["Amount"].sum().reset_index()
        )
        srch_monthly["Label"]   = srch_monthly["Month"].apply(cycle_label)
        srch_monthly["AmtText"] = srch_monthly["Amount"].round(0).astype(int).apply(lambda v: f"OMR {v:,}")
        srch_avg = srch_monthly["Amount"].mean()

        fig_srch = go.Figure()
        fig_srch.add_trace(go.Bar(
            x=srch_monthly["Label"], y=srch_monthly["Amount"],
            text=srch_monthly["AmtText"], textposition="outside",
            marker_color="#90caf9",
            hovertemplate="<b>%{x}</b><br>OMR %{y:,.0f}<extra></extra>",
            name="Spend",
        ))
        fig_srch.add_hline(
            y=srch_avg, line_dash="dot", line_color="#555", line_width=1.5,
            annotation_text=f"Avg  OMR {srch_avg:,.0f}",
            annotation_position="top left", annotation_font_color="#555",
        )
        fig_srch.update_layout(
            title=f'Monthly spend — {" / ".join(terms)}',
            xaxis_title="", yaxis_title="OMR",
            yaxis=dict(tickformat=",d",
                       range=[0, srch_monthly["Amount"].max() * 1.25]),
            showlegend=False,
            margin=dict(t=50, b=0), height=270,
        )
        st.plotly_chart(fig_srch, width="stretch", config=CHART_CFG)

    show = show_flt[["Transaction Date", "Description", "City", "Country",
                      "TXN Currency", "TXN Amount", "Amount", "Category"]].copy()
    show["_key"] = row_key(show_flt).values
    show = show.sort_values("Transaction Date", ascending=False).reset_index(drop=True)
    show.insert(0, "Delete", False)
    show["Amount"] = show["Amount"].round(0).astype(int)
    show = show.rename(columns={"Amount": "OMR Amount"})
    show["Transaction Date"] = show["Transaction Date"].dt.strftime("%d %b %Y")

    edited = st.data_editor(
        show.drop(columns=["_key"]),
        column_config={
            "Delete": st.column_config.CheckboxColumn(
                "🗑️", help="Check rows to delete, then click Delete"
            ),
        },
        disabled=[c for c in show.columns if c not in ["Delete", "_key"]],
        hide_index=True,
        width="stretch",
        key="txn_editor",
    )

    n_sel = int(edited["Delete"].sum())
    col_del, col_exp = st.columns([2, 5])

    with col_del:
        if st.button(
            f"Delete {n_sel} transaction{'s' if n_sel != 1 else ''}",
            type="primary",
            disabled=(n_sel == 0),
        ):
            keys_to_remove = show.loc[edited["Delete"].values, "_key"].tolist()
            delete_rows(keys_to_remove)
            st.success(f"Deleted {n_sel} transaction(s).")
            st.rerun()

    with col_exp:
        export = show.drop(columns=["_key", "Delete"])
        st.download_button("Export CSV", export.to_csv(index=False), "expenses.csv", "text/csv")


# ════════════════════════════════════════════════════════════════════════════════
# RECLASSIFY
# ════════════════════════════════════════════════════════════════════════════════
with t_reclassify:
    st.caption(
        "Override the auto-classification for any merchant. "
        "Saved changes apply to all past and future transactions from that merchant."
    )

    summary = (
        expenses.groupby(["Description", "Category"])["Amount"]
        .agg(Total="sum", Count="count").reset_index()
        .sort_values("Total", ascending=False)
    )

    # ── Others summary banner ──────────────────────────────────────────────────
    others_summary = summary[summary["Category"] == "Others"]
    total_others_omr = others_summary["Total"].sum()
    n_others_merch   = len(others_summary)
    if n_others_merch > 0:
        if total_others_omr <= OTHERS_WARN_OMR:
            st.success(
                f"✅ Others total is OMR {total_others_omr:,.0f} across "
                f"{n_others_merch} merchant(s) — immaterial, no action needed."
            )
        else:
            st.warning(
                f"OMR {total_others_omr:,.0f} unclassified across "
                f"{n_others_merch} merchant(s) — consider classifying below."
            )
    else:
        st.success("✅ All merchants classified — nothing in Others.")

    # ── Controls ───────────────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3 = st.columns([3, 3, 2])
    show_others_only = ctrl1.checkbox("Show only 'Others' merchants", value=True)
    min_omr = ctrl2.slider(
        "Hide items below OMR", min_value=0, max_value=50, value=5,
        help="Others merchants below this total are hidden — they're immaterial",
    )
    if ctrl3.button("Reset all overrides", type="secondary"):
        save_overrides({})
        st.success("All manual overrides cleared.")
        st.rerun()

    others_first = pd.concat([
        summary[summary["Category"] == "Others"],
        summary[summary["Category"] != "Others"],
    ])

    if show_others_only:
        others_first = others_first[others_first["Category"] == "Others"]

    # Apply the minimum-amount filter only to Others rows
    others_first = others_first[
        (others_first["Category"] != "Others") |
        (others_first["Total"] >= min_omr)
    ]

    if others_first.empty:
        st.info(f"No merchants to show (all Others items are below OMR {min_omr}).")
    else:
        pending = {}
        for _, row in others_first.iterrows():
            desc    = row["Description"]
            current = overrides.get(desc, row["Category"])
            c1, c2, c3 = st.columns([4, 3, 2])
            c1.text(desc[:55])
            sel = c2.selectbox(
                "",
                CATEGORIES,
                index=CATEGORIES.index(current) if current in CATEGORIES else 0,
                key=f"r_{desc}",
                label_visibility="collapsed",
            )
            c3.caption(f"OMR {round(row['Total']):,}  ·  {int(row['Count'])} txns")
            if sel != current:
                pending[desc] = sel

        st.divider()
        if st.button("Save Overrides", type="primary", disabled=not pending):
            overrides.update(pending)
            save_overrides(overrides)
            st.success(f"Saved {len(pending)} override(s).")
            st.rerun()
