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


# ── Everyday vs episodic ──────────────────────────────────────────────────────
# Measured on 17 cycles of real data: the everyday half runs at OMR ~480/cycle
# with CV 0.33, while the episodic half swings between OMR 61 and 990 (CV 0.62).
# Nearly all cycle-to-cycle variance comes from the episodic side, so the two
# are worth separating rather than averaging together.
EPISODIC_CATS = {
    "Travel & Transport", "Shopping & Retail",
    "Education", "Healthcare", "Charity & Donations",
}


def spend_kind(category: str) -> str:
    return "Episodic" if category in EPISODIC_CATS else "Everyday"


def typical_band(totals: pd.Series) -> tuple[float, float]:
    """The 25th-75th percentile range of cycle totals.

    A single mean is a poor reference here — only 5 of 17 cycles land within
    ±15% of it, because spending is a stable base plus occasional travel.
    """
    return float(totals.quantile(0.25)), float(totals.quantile(0.75))


def pace_curve(df, cycles) -> dict:
    """Cumulative OMR normally spent by each day of a cycle.

    Returns {day: (p25, median, p75)}.  Compares against where you actually
    were by this day in past cycles, rather than projecting the current cycle
    forward — by day 14 real cycles range from 23% to 65% complete, so a
    point projection implies precision that does not exist.
    """
    if not cycles:
        return {}
    by_day = {}
    for ym in cycles:
        d, start = df[df["Month"] == ym], cycle_start(ym)
        for day in range(1, 32):
            cut = start + pd.Timedelta(days=day)
            by_day.setdefault(day, []).append(
                d[d["Transaction Date"] < cut]["Amount"].sum()
            )
    return {
        day: (float(pd.Series(v).quantile(0.25)),
              float(pd.Series(v).median()),
              float(pd.Series(v).quantile(0.75)))
        for day, v in by_day.items()
    }


def detect_trips(df, gap_days=5, min_txns=3) -> list:
    """Group foreign-country spend into trips.

    A trip is the natural unit for episodic spend, and it cuts across
    categories — meals and shopping abroad belong to the trip, not to
    Food & Dining.  Domestic-currency online purchases from foreign merchants
    would create phantom trips, so only rows with a real merchant country and
    a non-OMR currency count toward detection.
    """
    f = df[
        df["Country"].notna()
        & ~df["Country"].astype(str).str.upper().isin(["-NIL-", "NAN", "", "OMAN"])
        & (df["TXN Currency"] != "OMR")
    ].sort_values("Transaction Date")
    if f.empty:
        return []

    trips, cur = [], None
    for _, r in f.iterrows():
        if cur and (r["Transaction Date"] - cur["end"]).days <= gap_days:
            cur["end"] = r["Transaction Date"]
            cur["rows"].append(r)
        else:
            if cur:
                trips.append(cur)
            cur = {"start": r["Transaction Date"], "end": r["Transaction Date"], "rows": [r]}
    if cur:
        trips.append(cur)

    out = []
    for t in trips:
        if len(t["rows"]) < min_txns:
            continue
        # Full cost = everything charged in the window, whatever its category
        window = df[(df["Transaction Date"] >= t["start"] - pd.Timedelta(days=1))
                    & (df["Transaction Date"] <= t["end"] + pd.Timedelta(days=1))]

        # A real trip involves getting somewhere. Without a flight, hotel or
        # taxi in the window this is a run of foreign-billed online purchases
        # — SaaS subscriptions and overseas web orders bill from the US and
        # would otherwise show up as phantom trips.
        if not (window["Category"] == "Travel & Transport").any():
            continue

        # Name only countries you actually spent time in. A single Amazon.ca
        # order placed mid-trip should not make Canada a destination.
        rows  = pd.DataFrame(t["rows"])
        by_c  = rows.groupby("Country").agg(n=("Amount", "size"), amt=("Amount", "sum"))
        real  = by_c[by_c["n"] >= 2].sort_values("amt", ascending=False)
        if real.empty:
            real = by_c.sort_values("amt", ascending=False).head(1)
        names = [str(c).title() for c in real.index[:3]]
        label = " · ".join(names)
        if len(real) > 3:
            label += f" +{len(real) - 3}"

        days = (t["end"] - t["start"]).days + 1
        out.append({
            "Trip": label,
            "Start": t["start"], "End": t["end"], "Days": days,
            "Total": float(window["Amount"].sum()),
            "PerDay": float(window["Amount"].sum()) / days,
            "Txns": len(window),
        })
    return sorted(out, key=lambda x: x["Start"], reverse=True)


def category_movers(df, cur_cycle, base_cycles, top_n=3) -> pd.DataFrame:
    """Categories that moved most vs the average of `base_cycles`.

    Each row names the single merchant that drove the change, which is the
    question a category-level delta always leaves unanswered.
    """
    cur_cycles = [cur_cycle] if isinstance(cur_cycle, str) else list(cur_cycle)
    if not base_cycles or not cur_cycles:
        return pd.DataFrame()

    # Both sides are expressed per-cycle so periods of different length compare
    n_cur, n_base = len(cur_cycles), len(base_cycles)
    cur  = df[df["Month"].isin(cur_cycles)].groupby("Category")["Amount"].sum() / n_cur
    base = df[df["Month"].isin(base_cycles)].groupby("Category")["Amount"].sum() / n_base

    mv = pd.DataFrame({"Now": cur, "Usual": base}).fillna(0)
    mv["Change"] = mv["Now"] - mv["Usual"]
    mv = mv.reindex(mv["Change"].abs().sort_values(ascending=False).index).head(top_n)

    drivers = []
    for cat in mv.index:
        c = (df[df["Month"].isin(cur_cycles) & (df["Category"] == cat)]
             .groupby("Merchant")["Amount"].sum() / n_cur)
        b = (df[df["Month"].isin(base_cycles) & (df["Category"] == cat)]
             .groupby("Merchant")["Amount"].sum() / n_base)
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


# ── Shared scope ──────────────────────────────────────────────────────────────
# No sidebar filters: each tab owns its own time scope.  Two competing time
# controls (a global cycle multiselect plus a per-tab selector) was the main
# reason it was never clear which period a number referred to.

expenses["Kind"] = expenses["Category"].apply(spend_kind)

cycle_labels_map = {
    ym: cycle_label(ym) + (" · in progress" if ym == INPROGRESS else "")
    for ym in ALL_CYCLES
}
cycle_totals = expenses.groupby("Month")["Amount"].sum()
done_totals  = cycle_totals[COMPLETE_CYCLES] if COMPLETE_CYCLES else cycle_totals
BAND_LO, BAND_HI = typical_band(done_totals) if len(done_totals) else (0.0, 0.0)
TYPICAL = float(done_totals.median()) if len(done_totals) else 0.0
PACE    = pace_curve(expenses, COMPLETE_CYCLES)

BLUE, RED, GREY, TEAL, SAND = "#90caf9", "#ef9a9a", "#e0e0e0", "#80cbc4", "#c5cae9"

t_now, t_explain, t_review, t_setup = st.tabs(
    ["Now", "Explain", "Review", "⚙️ Setup"]
)

# ════════════════════════════════════════════════════════════════════════════════
# NOW — the every-open screen.  One question: am I on track this cycle?
# ════════════════════════════════════════════════════════════════════════════════
with t_now:
    if not COMPLETE_CYCLES:
        st.warning("Need at least one complete billing cycle before this means anything.")
    else:
        focus      = INPROGRESS or COMPLETE_CYCLES[-1]
        focus_data = expenses[expenses["Month"] == focus]
        spent      = float(focus_data["Amount"].sum())
        live       = focus == INPROGRESS

        if live:
            elapsed, total_days = cycle_progress(focus)
            p25, usual, p75 = PACE.get(elapsed, (0.0, 0.0, 0.0))
            st.subheader(f"{cycle_label(focus)} · day {elapsed} of {total_days}")
        else:
            elapsed = total_days = None
            p25, usual, p75 = BAND_LO, TYPICAL, BAND_HI
            st.subheader(f"{cycle_label(focus)} · complete")
        st.caption(cycle_dates(focus))

        # ── Three numbers, and only three ──────────────────────────────────────
        c1, c2, c3 = st.columns(3)

        with c1:
            gap  = spent - usual
            st.metric("Spent so far" if live else "Total spend", f"OMR {spent:,.0f}",
                      f"{gap:+,.0f} vs usual" if usual else None,
                      delta_color="inverse")

        with c2:
            st.metric("Usually by now" if live else "Typical cycle",
                      f"OMR {usual:,.0f}",
                      help="Median of the same point in every complete cycle")
            st.caption(f"Normal range OMR {p25:,.0f}–{p75:,.0f}")

        with c3:
            # For a live cycle, judge the PROJECTION, not the raw total — six
            # days of spending is below the full-cycle band by definition.
            # Projection scales by how far off the usual pace you are, rather
            # than extrapolating linearly.
            projected = (spent / usual * TYPICAL) if (live and usual) else spent
            verdict = ("below normal" if projected < BAND_LO else
                       "above normal" if projected > BAND_HI else "within normal")
            st.metric("Full-cycle range", f"OMR {BAND_LO:,.0f}–{BAND_HI:,.0f}",
                      help="Middle half of your complete cycles (25th–75th percentile). "
                           "Only 5 of 17 cycles land near the mean, so a single "
                           "average is a misleading reference.")
            st.caption(f"At this pace ≈ OMR {projected:,.0f} — {verdict}" if live
                       else f"This cycle is {verdict}")

        # ── Pace bar ───────────────────────────────────────────────────────────
        fig_pace = go.Figure()
        fig_pace.add_trace(go.Bar(
            x=[spent], y=[""], orientation="h", width=0.45,
            marker_color=RED if spent > (p75 or spent) else TEAL,
            hovertemplate=f"Spent: OMR {spent:,.0f}<extra></extra>",
        ))
        # Annotations sit below the axis — the Plotly toolbar overlays the
        # top-right of the plot on hover and would cover them.
        if usual:
            fig_pace.add_vline(x=usual, line_dash="dot", line_color="#555", line_width=2,
                               annotation_text="usual by now" if live else "typical",
                               annotation_position="bottom", annotation_font_color="#555")
        fig_pace.add_vrect(x0=BAND_LO, x1=BAND_HI, fillcolor="#b0bec5", opacity=0.18,
                           line_width=0, layer="below",
                           annotation_text="normal full-cycle range",
                           annotation_position="bottom", annotation_font_color="#78909c")
        fig_pace.update_layout(
            xaxis=dict(title="", tickformat=",d",
                       range=[0, max(spent, BAND_HI, usual) * 1.12]),
            yaxis=dict(showticklabels=False),
            showlegend=False, height=150, margin=dict(t=10, b=55, l=0, r=10),
        )
        st.plotly_chart(fig_pace, width="stretch", config=CHART_CFG)

        # ── Everyday vs episodic ───────────────────────────────────────────────
        kind_now = focus_data.groupby("Kind")["Amount"].sum()
        k1, k2 = st.columns(2)
        for col, kind, note in (
            (k1, "Everyday", "food, groceries, fuel, bills"),
            (k2, "Episodic", "travel and big one-off purchases"),
        ):
            with col:
                got = float(kind_now.get(kind, 0.0))
                # Compare like with like: on a live cycle the benchmark is where
                # this kind of spend normally stands by this same day, not the
                # full-cycle figure.
                sub = expenses[expenses["Kind"] == kind]
                if live:
                    ref = pace_curve(sub, COMPLETE_CYCLES).get(elapsed, (0, 0, 0))[1]
                    lbl = "vs usual by now"
                else:
                    ref = float(sub[sub["Month"].isin(COMPLETE_CYCLES)]
                                .groupby("Month")["Amount"].sum().median())
                    lbl = "vs typical cycle"
                col.metric(f"{kind} so far" if live else kind, f"OMR {got:,.0f}",
                           f"{got - ref:+,.0f} {lbl}" if ref else None,
                           delta_color="inverse")
                col.caption(note)

        st.divider()

        # ── The items that actually explain the cycle ──────────────────────────
        # Top 8 covers a median 59% of a cycle; the 12-36 transactions under
        # OMR 5 together account for only 4-11%.
        st.markdown("**Biggest items this cycle**")
        big = focus_data.nlargest(8, "Amount")[
            ["Transaction Date", "Merchant", "Amount", "Category"]
        ].copy()
        if big.empty:
            st.info("No transactions in this cycle yet.")
        else:
            big["Transaction Date"] = big["Transaction Date"].dt.strftime("%d %b")
            big["Amount"] = big["Amount"].round(0).astype(int)
            covered = big["Amount"].sum() / spent * 100 if spent else 0
            st.dataframe(
                big.rename(columns={"Transaction Date": "Date", "Amount": "OMR"}),
                hide_index=True, width="stretch",
                height=38 + len(big) * 35,     # size to content, no filler rows
            )
            st.caption(f"These {len(big)} cover {covered:.0f}% of the cycle "
                       f"({len(focus_data)} transactions in total)")

        st.divider()

        # ── History with the normal band drawn in ──────────────────────────────
        st.markdown("**Recent cycles**")
        hist = cycle_totals.tail(13).reset_index()
        hist.columns  = ["Month", "Amount"]
        hist["Label"] = hist["Month"].apply(cycle_label)
        hist["Done"]  = hist["Month"].isin(COMPLETE_CYCLES)

        fig_h = go.Figure()
        fig_h.add_hrect(y0=BAND_LO, y1=BAND_HI, fillcolor="#b0bec5", opacity=0.18,
                        line_width=0, layer="below",
                        annotation_text="normal range", annotation_position="top left",
                        annotation_font_color="#78909c")
        fig_h.add_trace(go.Bar(
            x=hist["Label"], y=hist["Amount"],
            marker=dict(
                color=[(RED if a > BAND_HI else TEAL if a >= BAND_LO else BLUE)
                       if d else GREY for a, d in zip(hist["Amount"], hist["Done"])],
                line=dict(color=["rgba(0,0,0,0)" if d else "#bdbdbd" for d in hist["Done"]],
                          width=1.5),
            ),
            text=hist["Amount"].round(0).astype(int).apply(lambda v: f"{v:,}"),
            textposition="outside",
            customdata=hist["Done"].map({True: "complete", False: "partial"}),
            hovertemplate="<b>%{x}</b><br>OMR %{y:,.0f}<br><i>%{customdata}</i><extra></extra>",
        ))
        fig_h.update_layout(
            xaxis_title="", yaxis_title="OMR",
            yaxis=dict(tickformat=",d", range=[0, hist["Amount"].max() * 1.25]),
            showlegend=False, height=300, margin=dict(t=30, b=0),
        )
        st.plotly_chart(fig_h, width="stretch", config=CHART_CFG)
        st.caption("🔴 above normal   🟢 within normal   🔵 below normal   ⬜ partial cycle")


# ════════════════════════════════════════════════════════════════════════════════
# EXPLAIN — one question: where did the money go, and what changed?
# ════════════════════════════════════════════════════════════════════════════════
with t_explain:
    if not COMPLETE_CYCLES:
        st.warning("Need at least one complete billing cycle.")
    else:
        SCOPES = {"Last 3 cycles": 3, "Last 6 cycles": 6,
                  "Last 12 cycles": 12, "All": len(COMPLETE_CYCLES)}
        pick = st.radio("Period", list(SCOPES) + ["One cycle…"],
                        horizontal=True, label_visibility="collapsed")

        if pick == "One cycle…":
            sel = st.selectbox("Billing cycle", list(reversed(COMPLETE_CYCLES)),
                               format_func=lambda ym: cycle_labels_map.get(ym, ym))
            period, base = [sel], []
            i = COMPLETE_CYCLES.index(sel)
            base = COMPLETE_CYCLES[max(0, i - 3):i]
        else:
            n = min(SCOPES[pick], len(COMPLETE_CYCLES))
            period = COMPLETE_CYCLES[-n:]
            base   = COMPLETE_CYCLES[max(0, len(COMPLETE_CYCLES) - 2 * n):-n]

        data  = expenses[expenses["Month"].isin(period)]
        total = float(data["Amount"].sum())
        st.caption(
            f"{cycle_label(period[0])} – {cycle_label(period[-1])} · "
            f"{len(period)} cycle(s) · OMR {total:,.0f} total · "
            f"OMR {total / len(period):,.0f} per cycle · complete cycles only"
        )

        # ── What changed, and who caused it ────────────────────────────────────
        movers = category_movers(expenses, period, base, top_n=3)
        if not movers.empty:
            st.markdown(f"**What moved** — vs the previous {len(base)} cycle(s)")
            mc = st.columns(len(movers))
            for col, (_, r) in zip(mc, movers.iterrows()):
                col.metric(r["Category"], f"OMR {r['Now']:,.0f}/cycle",
                           f"{r['Change']:+,.0f} vs usual {r['Usual']:,.0f}",
                           delta_color="inverse")
                if r["Driver"] != "—":
                    col.caption(f"↳ {r['Driver']} ({r['DriverChange']:+,.0f})")
            st.divider()

        # ── Where it went ──────────────────────────────────────────────────────
        left, right = st.columns([1, 1])

        with left:
            st.markdown("**By category**")
            cat = (data.groupby("Category")["Amount"].sum()
                   .reset_index().sort_values("Amount", ascending=False))
            cat["Pct"] = (cat["Amount"] / cat["Amount"].sum() * 100).round(0)
            cat["_l"]  = cat.apply(
                lambda r: f"OMR {int(round(r['Amount'])):,}  ({r['Pct']:.0f}%)", axis=1)
            # `cat` is already sorted descending, and Plotly lays categorical
            # rows out top-down, so the largest bar lands at the top.
            fig_c = px.bar(cat, x="Amount", y="Category", orientation="h",
                           color="Category", color_discrete_sequence=COLORS,
                           text="_l", custom_data=["Pct"])
            fig_c.update_traces(
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>OMR %{x:,.0f} (%{customdata[0]}%)<extra></extra>")
            fig_c.update_layout(
                showlegend=False, yaxis_title="",
                xaxis=dict(showticklabels=False, title="",
                           range=[0, cat["Amount"].max() * 1.45]),
                margin=dict(t=28, b=0, r=10), height=max(320, len(cat) * 34),
            )
            st.plotly_chart(fig_c, width="stretch", config=CHART_CFG)

        with right:
            st.markdown("**By merchant**")
            mer = data.groupby("Merchant").agg(
                Total=("Amount", "sum"), Txns=("Amount", "count"),
                Cycles=("Month", "nunique"),
            ).sort_values("Total", ascending=False).head(15).reset_index()
            mer["Per cycle"] = (mer["Total"] / len(period)).round(1)
            mer["Total"]     = mer["Total"].round(0).astype(int)
            mer["Seen in"]   = mer["Cycles"].astype(str) + f"/{len(period)}"
            st.dataframe(
                mer[["Merchant", "Total", "Per cycle", "Txns", "Seen in"]]
                   .rename(columns={"Total": "Total OMR", "Per cycle": "OMR / cycle"}),
                hide_index=True, width="stretch", height=max(320, len(cat) * 34),
            )

        st.divider()

        # ── Drill into one category ────────────────────────────────────────────
        st.markdown("**Drill into a category**")
        cats = cat["Category"].tolist()
        dcat = st.selectbox("Category", cats, label_visibility="collapsed")
        dd   = data[data["Category"] == dcat]

        d1, d2 = st.columns([2, 3])
        with d1:
            dm = (dd.groupby("Merchant")["Amount"].sum()
                  .round(0).astype(int).reset_index()
                  .sort_values("Amount", ascending=False))
            if len(dm) > 1:
                fig_p = px.pie(dm.head(10), values="Amount", names="Merchant",
                               color_discrete_sequence=COLORS, hole=0.4)
                fig_p.update_traces(
                    textinfo="percent", textposition="inside",
                    hovertemplate="<b>%{label}</b><br>OMR %{value:,}<br>%{percent}<extra></extra>")
                fig_p.update_layout(margin=dict(t=10, b=0), height=300,
                                    legend=dict(font=dict(size=10)))
                st.plotly_chart(fig_p, width="stretch", config=CHART_CFG)
            else:
                st.info("Only one merchant in this category.")
        with d2:
            dt = dd[["Transaction Date", "Merchant", "Amount", "Month"]].copy()
            dt["Date"]  = dt["Transaction Date"].dt.strftime("%d %b %Y")
            dt["OMR"]   = dt["Amount"].round(0).astype(int)
            dt["Cycle"] = dt["Month"].apply(cycle_label)
            st.dataframe(dt[["Date", "Cycle", "Merchant", "OMR"]]
                         .sort_values("OMR", ascending=False),
                         hide_index=True, width="stretch", height=300)
            st.caption(f"{len(dd)} transaction(s) · OMR {dd['Amount'].sum():,.0f}")

        st.divider()

        # ── Find a transaction ─────────────────────────────────────────────────
        st.markdown("**Find a transaction**")
        q = st.text_input("Search", placeholder="e.g. lulu spar — space or comma separates terms",
                          label_visibility="collapsed")
        found = data
        if q:
            terms = [t.strip().upper() for t in q.replace(",", " ").split() if t.strip()]
            hay   = (data["Description"].str.upper() + " " + data["Merchant"].str.upper())
            found = data[hay.apply(lambda d: any(t in d for t in terms))]

            if not found.empty:
                fm = found.groupby("Month")["Amount"].sum().reset_index()
                fm["Label"] = fm["Month"].apply(cycle_label)
                fig_f = go.Figure(go.Bar(
                    x=fm["Label"], y=fm["Amount"], marker_color=TEAL,
                    text=fm["Amount"].round(0).astype(int).apply(lambda v: f"{v:,}"),
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>OMR %{y:,.0f}<extra></extra>"))
                fig_f.update_layout(
                    title=f'Monthly spend — {" / ".join(terms)}',
                    xaxis_title="", yaxis_title="OMR",
                    yaxis=dict(tickformat=",d", range=[0, fm["Amount"].max() * 1.25]),
                    showlegend=False, height=260, margin=dict(t=50, b=0))
                st.plotly_chart(fig_f, width="stretch", config=CHART_CFG)

        show = found[["Transaction Date", "Merchant", "Description", "City",
                      "TXN Currency", "TXN Amount", "Amount", "Category"]].copy()
        show["_key"] = row_key(found).values
        show = show.sort_values("Transaction Date", ascending=False).reset_index(drop=True)
        show.insert(0, "Delete", False)
        show["Amount"] = show["Amount"].round(0).astype(int)
        show = show.rename(columns={"Amount": "OMR"})
        show["Transaction Date"] = show["Transaction Date"].dt.strftime("%d %b %Y")

        edited = st.data_editor(
            show.drop(columns=["_key"]),
            column_config={"Delete": st.column_config.CheckboxColumn(
                "🗑️", help="Check rows to delete, then click Delete")},
            disabled=[c for c in show.columns if c not in ["Delete", "_key"]],
            hide_index=True, width="stretch", key="txn_editor",
        )
        st.caption(f"{len(show)} transaction(s)")

        n_sel = int(edited["Delete"].sum())
        b1, b2 = st.columns([2, 5])
        with b1:
            if st.button(f"Delete {n_sel} transaction{'s' if n_sel != 1 else ''}",
                         type="primary", disabled=(n_sel == 0)):
                delete_rows(show.loc[edited["Delete"].values, "_key"].tolist())
                st.success(f"Deleted {n_sel} transaction(s).")
                st.rerun()
        with b2:
            st.download_button("Export CSV",
                               show.drop(columns=["_key", "Delete"]).to_csv(index=False),
                               "expenses.csv", "text/csv")


# ════════════════════════════════════════════════════════════════════════════════
# REVIEW — the few-times-a-year work
# ════════════════════════════════════════════════════════════════════════════════
with t_review:
    # ── Trips ──────────────────────────────────────────────────────────────────
    st.subheader("Trips")
    st.caption(
        "Detected from clusters of foreign-currency spend. Cost counts **everything** "
        "charged during the trip window, not just the Travel category — meals and "
        "shopping abroad belong to the trip."
    )
    trips = detect_trips(expenses)
    if not trips:
        st.info("No trips detected.")
    else:
        td = pd.DataFrame(trips)
        td["When"]    = (td["Start"].dt.strftime("%d %b %Y") + " – "
                         + td["End"].dt.strftime("%d %b %Y"))
        td["Cost"]    = td["Total"].round(0).astype(int)
        td["Per day"] = td["PerDay"].round(0).astype(int)

        tl, tr = st.columns([3, 2])
        with tl:
            st.dataframe(td[["Trip", "When", "Days", "Cost", "Per day", "Txns"]]
                         .rename(columns={"Cost": "Total OMR", "Per day": "OMR / day"}),
                         hide_index=True, width="stretch",
                         height=38 + len(td) * 35)
        with tr:
            # Chart is dated-only on the axis; full destinations live in the
            # table beside it, so long country lists cannot squeeze the bars.
            fig_t = go.Figure(go.Bar(
                x=td["Total"][::-1], y=td["Start"].dt.strftime("%b %Y")[::-1],
                orientation="h", marker_color=TEAL,
                customdata=td["Trip"][::-1],
                text=td["Cost"][::-1].apply(lambda v: f"OMR {v:,}"), textposition="outside",
                hovertemplate="<b>%{customdata}</b><br>%{y}<br>OMR %{x:,.0f}<extra></extra>"))
            fig_t.update_layout(
                xaxis=dict(showticklabels=False, title="",
                           range=[0, td["Total"].max() * 1.45]),
                yaxis=dict(title="", type="category"),
                height=58 + len(td) * 35, margin=dict(t=30, b=0, r=10),
                showlegend=False)
            st.plotly_chart(fig_t, width="stretch", config=CHART_CFG)
        st.caption(f"Total across {len(td)} trip(s): **OMR {td['Total'].sum():,.0f}** "
                   f"— {td['Total'].sum() / expenses['Amount'].sum() * 100:.0f}% of all spend.")

    st.divider()

    # ── Bill verification ──────────────────────────────────────────────────────
    st.subheader("Bill Verification")
    st.caption("Each cycle's expenses against the payment that settled it. "
               "Payments post in the following cycle.")

    ct = (expenses.groupby("Month")["Amount"].sum().reset_index()
          .rename(columns={"Month": "Cycle", "Amount": "Expenses (OMR)"})
          .sort_values("Cycle", ascending=False))
    ct["Period"] = ct["Cycle"].apply(cycle_label)
    ct["Expenses (OMR)"] = ct["Expenses (OMR)"].round(0).astype(int)

    if payments.empty:
        st.info("No payment transactions found yet.")
    else:
        def payment_cycle(pay_date):
            for ym in sorted(ct["Cycle"].tolist(), reverse=True):
                if pay_date >= cycle_end(ym):
                    return ym
            return None

        ps = payments[["Transaction Date", "Amount"]].copy()
        ps["Settles"] = ps["Transaction Date"].apply(payment_cycle)
        pb = (ps.groupby("Settles")["Amount"].sum().reset_index()
              .rename(columns={"Settles": "Cycle", "Amount": "Payment (OMR)"}))
        pb["Payment (OMR)"] = pb["Payment (OMR)"].round(0).astype(int)

        recon = ct.merge(pb, on="Cycle", how="left")
        recon["Payment (OMR)"] = recon["Payment (OMR)"].fillna(0).astype(int)
        recon["Difference"]    = recon["Payment (OMR)"] - recon["Expenses (OMR)"]
        recon = recon[["Period", "Expenses (OMR)", "Payment (OMR)", "Difference"]]

        st.dataframe(
            recon.style.map(
                lambda v: "color: green" if v == 0 else
                          ("color: red" if isinstance(v, (int, float)) and v != 0 else ""),
                subset=["Difference"]),
            hide_index=True, width="stretch", height=300,
        )
        st.caption("Difference = Payment − Expenses. Negative means underpayment, "
                   "positive means overpayment or credit.")

    st.divider()

    # ── Recurring merchants ────────────────────────────────────────────────────
    st.subheader("Recurring Merchants")
    recent_done = COMPLETE_CYCLES[-6:]
    rd = expenses[expenses["Month"].isin(recent_done) & (expenses["Type"] == "Recurring")]
    if rd.empty or not recent_done:
        st.info("Needs about six complete cycles before this is meaningful.")
    else:
        pc  = rd.groupby(["Merchant", "Month"])["Amount"].sum()
        agg = pc.groupby("Merchant").agg(Cycles="count", _m="mean", _s="std").fillna(0)
        agg["Per cycle"] = (pc.groupby("Merchant").sum() / len(recent_done)).round(1)
        agg["Pattern"]   = (agg["_s"] / agg["_m"]).apply(
            lambda cv: "steady" if cv <= 0.40 else "variable")
        agg = (agg[["Per cycle", "Cycles", "Pattern"]]
               .sort_values("Per cycle", ascending=False).reset_index())
        agg["Cycles"] = agg["Cycles"].astype(int).astype(str) + f"/{len(recent_done)}"
        st.dataframe(agg.rename(columns={"Per cycle": "OMR / cycle"}),
                     hide_index=True, width="stretch", height=280)
        st.caption(
            f"OMR {agg['OMR / cycle'].sum() if 'OMR / cycle' in agg else 0:,.0f} — "
            "seen in at least 4 of the last 6 cycles. Note most of these are "
            "**variable** (groceries, fuel): predictable that you'll spend, not how much."
        )

    st.divider()

    # ── Started & stopped ──────────────────────────────────────────────────────
    st.subheader("Started & Stopped")
    if len(COMPLETE_CYCLES) < 4:
        st.info("Needs at least four complete cycles.")
    else:
        recent_w, prior_w = COMPLETE_CYCLES[-3:], COMPLETE_CYCLES[:-3]
        src = expenses[expenses["Month"].isin(COMPLETE_CYCLES)]
        recent_m = set(src[src["Month"].isin(recent_w)]["Merchant"])
        prior_m  = set(src[src["Month"].isin(prior_w)]["Merchant"])

        started = (src[src["Merchant"].isin(recent_m - prior_m) & src["Month"].isin(recent_w)]
                   .groupby("Merchant")["Amount"].sum().sort_values(ascending=False).head(8))
        established = src[src["Month"].isin(prior_w)].groupby("Merchant")["Month"].nunique()
        lapsed_names = [m for m in (prior_m - recent_m)
                        if established.get(m, 0) >= max(3, len(prior_w) // 3)]
        lapsed = (src[src["Merchant"].isin(lapsed_names)].groupby("Merchant")["Amount"].sum()
                  .sort_values(ascending=False).head(8))

        s1, s2 = st.columns(2)
        with s1:
            st.markdown("🆕 **Started** — new in the last 3 cycles")
            if started.empty:
                st.caption("Nothing new.")
            for m, v in started.items():
                st.markdown(f"<small>{m} — OMR {v:,.0f}</small>", unsafe_allow_html=True)
        with s2:
            st.markdown("🛑 **Stopped** — was a habit, now gone")
            if lapsed.empty:
                st.caption("Nothing stopped.")
            for m, v in lapsed.items():
                last = src[src["Merchant"] == m]["Month"].max()
                st.markdown(f"<small>{m} — was OMR {v:,.0f}, last seen "
                            f"{cycle_label(last)}</small>", unsafe_allow_html=True)

    st.divider()

    # ── Full history ───────────────────────────────────────────────────────────
    st.subheader("Full History")
    fh = cycle_totals.reset_index()
    fh.columns  = ["Month", "Amount"]
    fh["Label"] = fh["Month"].apply(cycle_label)
    fh["Done"]  = fh["Month"].isin(COMPLETE_CYCLES)
    fh["R3"]    = (fh["Amount"].where(fh["Done"]).rolling(3, min_periods=1)
                   .mean().where(fh["Done"]))

    fig_fh = go.Figure()
    fig_fh.add_hrect(y0=BAND_LO, y1=BAND_HI, fillcolor="#b0bec5", opacity=0.18,
                     line_width=0, layer="below")
    fig_fh.add_trace(go.Bar(
        x=fh["Label"], y=fh["Amount"], name="Cycle total",
        marker=dict(color=[BLUE if d else GREY for d in fh["Done"]],
                    line=dict(color=["rgba(0,0,0,0)" if d else "#bdbdbd" for d in fh["Done"]],
                              width=1.5)),
        hovertemplate="<b>%{x}</b><br>OMR %{y:,.0f}<extra></extra>"))
    fig_fh.add_trace(go.Scatter(
        x=fh["Label"], y=fh["R3"], mode="lines+markers", name="3-cycle avg",
        line=dict(color="#e65100", width=2), marker=dict(size=5), connectgaps=False,
        hovertemplate="3-cycle avg: OMR %{y:,.0f}<extra></extra>"))
    fig_fh.update_layout(
        xaxis_title="", yaxis_title="OMR", yaxis=dict(tickformat=",d"),
        legend_title="", height=340, margin=dict(t=10, b=0))
    st.plotly_chart(fig_fh, width="stretch", config=CHART_CFG)
    st.caption("Shaded band is your normal range. Grey bars are partial cycles, "
               "excluded from the band and the rolling average.")


# ════════════════════════════════════════════════════════════════════════════════
# SETUP — configuration, not analysis
# ════════════════════════════════════════════════════════════════════════════════
with t_setup:
    st.caption(
        "Override the auto-classification for any merchant. "
        "Saved changes apply to all past and future transactions from that merchant."
    )

    # One row per canonical merchant, not per raw bank string.  The overrides
    # file keys on the raw `Description` (and `apply_overrides` matches on it),
    # so keep the merchant → descriptions map: a single choice below is written
    # out as one override entry per variant.  Built from `expenses` only, so a
    # payment row is never recategorised by a merchant edit.
    merch_descs = (
        expenses.groupby("Merchant")["Description"]
        .apply(lambda s: sorted(s.unique()))
        .to_dict()
    )

    per_cat = (
        expenses.groupby(["Merchant", "Category"])["Amount"]
        .agg(Total="sum", Count="count").reset_index()
    )

    # A merchant's variants can carry different categories — either because the
    # keyword rules split them, or because an older per-description override
    # covered only some.  Show the dominant one (most transactions, ties broken
    # by spend then name so it is stable) and flag the merchant as mixed.
    dominant = (
        per_cat.sort_values(["Count", "Total", "Category"],
                            ascending=[False, False, True])
        .drop_duplicates("Merchant").set_index("Merchant")["Category"]
    )
    others_omr = (
        per_cat[per_cat["Category"] == "Others"].groupby("Merchant")["Total"].sum()
    )

    summary = per_cat.groupby("Merchant").agg(
        Total=("Total", "sum"), Count=("Count", "sum"), NCats=("Category", "size"),
    ).reset_index()
    summary["Category"] = summary["Merchant"].map(dominant)
    summary["Mixed"]    = summary["NCats"] > 1
    summary["Others"]   = summary["Merchant"].map(others_omr).fillna(0.0)

    # ── Others summary banner ──────────────────────────────────────────────────
    others_summary = summary[summary["Others"] > 0]
    total_others_omr = others_summary["Others"].sum()
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

    # Anything with unclassified spend first — including a merchant only partly
    # in Others — then everything else by size.
    others_first = pd.concat([
        summary[summary["Others"] > 0].sort_values("Others", ascending=False),
        summary[summary["Others"] == 0].sort_values("Total", ascending=False),
    ])

    if show_others_only:
        others_first = others_first[others_first["Others"] > 0]

    # Apply the minimum-amount filter to the unclassified portion only
    others_first = others_first[
        (others_first["Others"] == 0) | (others_first["Others"] >= min_omr)
    ]

    if others_first.empty:
        st.info(f"No merchants to show (all Others items are below OMR {min_omr}).")
    else:
        pending = {}          # raw Description → category, the overrides file format
        touched = 0           # merchants the user actually changed
        for _, row in others_first.iterrows():
            merch    = row["Merchant"]
            variants = merch_descs.get(merch, [])
            current  = row["Category"]

            c1, c2, c3 = st.columns([4, 3, 2])
            c1.text(merch[:55])

            note = []
            if len(variants) > 1:
                note.append(f"{len(variants)} bank descriptions")
            if row["Mixed"]:
                mix = per_cat[per_cat["Merchant"] == merch].sort_values(
                    "Count", ascending=False)["Category"].tolist()
                note.append("⚠️ mixed: " + ", ".join(mix))
            if note:
                c1.caption("  ·  ".join(note))

            sel = c2.selectbox(
                "",
                CATEGORIES,
                index=CATEGORIES.index(current) if current in CATEGORIES else 0,
                key=f"r_{merch}",
                label_visibility="collapsed",
            )

            # Picking a new category already rewrites every variant.  The
            # checkbox only exists so a mixed merchant can be unified onto the
            # category it already shows.
            unify = row["Mixed"] and c1.checkbox(
                "Apply to all variants", key=f"u_{merch}"
            )

            c3.caption(f"OMR {round(row['Total']):,}  ·  {int(row['Count'])} txns")
            if 0 < row["Others"] < row["Total"]:
                c3.caption(f"OMR {round(row['Others']):,} unclassified")

            if sel != current or unify:
                touched += 1
                for d in variants:            # one entry per raw description
                    pending[d] = sel

        st.divider()
        if st.button("Save Overrides", type="primary", disabled=not pending):
            overrides.update(pending)
            save_overrides(overrides)
            st.success(
                f"Saved {touched} merchant change(s) "
                f"across {len(pending)} bank description(s)."
            )
            st.rerun()
