import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    "Insurance",
    "Subscriptions",
    "Healthcare",
    "Shopping & Retail",
    "Gold & Jewellery",
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

    # ── High-priority overrides of the generic rules below ────────────────────
    # Named food chains are never a travel merchant even inside an airport.
    # Without this, "MCDONALDS -DXB AIRPORT" hit the Travel keyword "AIRPORT"
    # first and was booked as transport rather than a meal.
    ("Food & Dining",          ["MCDONALD", "KFC", "BURGER KING", "SUBWAY SANDWICH",
                                "STARBUCKS", "COSTA COFFEE", "DUNKIN",
                                "BASKIN", "PAPPA ROTI", "TIM HORTON"]),

    # Gold and jewellery are asset purchases, not retail spending — mixing them
    # into Shopping & Retail made that category's trend unreadable. Watches are
    # deliberately NOT here: they get used rather than held, so they stay retail.
    ("Gold & Jewellery",       ["JEWELLER", "JEWELRY", "JEWELLERY", "KALYAN",
                                "DAMAS", "MALABAR GOLD", "JOYALUKKAS",
                                "GOLD SOUQ", "BULLION"]),

    # Recurring subscriptions and memberships, so the total standing commitment
    # is visible in one place. Anthropic/Claude had been overridden into
    # Education and the gym sat in Healthcare, hiding both.
    ("Subscriptions",          ["ANTHROPIC", "CLAUDE.AI", "OPENAI", "CHATGPT",
                                "NETFLIX", "SPOTIFY", "ADOBE", "MICROSOFT",
                                "GITHUB", "DROPBOX", "ICLOUD", "APPLE.COM",
                                "GOOGLE STORAGE", "YOUTUBE PREMIUM",
                                "SHAHID", "OSN", "DISNEY",
                                "FITNESS", "GYM", "HEALTH CLUB",  # memberships
                                ]),

    # Insurance was split across Utilities & Government and Automotive
    # depending on the provider, so no single figure showed what it cost.
    ("Insurance",              ["INSURANCE", "TAKAFUL", "ARABIAFALCON",
                                "ASSURANCE", "INSURE"]),

    ("Food Delivery",          ["TALABAT PRO", "TALABAT", "NOON FOOD",
                                "HUNGERSTATION", "DELIVEROO"]),

    ("Fuel",                   ["OMAN OIL", "SHELL OMAN", "SHELL", "STATION 10",
                                "AL MAHA", "BP TANKSTELLE", "BP LEIKERMOSER",
                                " F.S",           # Omani filling stations, e.g. "QURUM HEIGHTS F.S"
                                ]),

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
                                "CPAP",
                                # FITNESS / GYM moved to Subscriptions — a gym is
                                # a recurring membership, not medical spending.
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
                                "SHARA MILLS",    # dates and grains — a provisions shop, not a restaurant
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
                                "AL RAVI", "AL HAWAS",
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
    # A mid-string gateway prefix ("NAJAFYIA* NAJAFYIA.ORG") isn't caught by
    # _GATEWAY, which only strips a leading one — so these split into two
    # merchants and appeared as two separate rows.
    ("Najafyia",         ["NAJAFYIA"]),
    ("Shara Mills & Dates", ["SHARA MILLS"]),
    ("Claude / Anthropic",  ["ANTHROPIC", "CLAUDE.AI"]),
    ("Qurum Heights F.S",   ["QURUM HEIGHTS"]),
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
    "Gold & Jewellery",   # asset purchases: rare, large
    "Insurance",          # annual premiums, so lumpy rather than monthly
}


def spend_kind(category: str) -> str:
    return "Episodic" if category in EPISODIC_CATS else "Everyday"


def typical_band(totals: pd.Series) -> tuple[float, float]:
    """The 25th-75th percentile range of cycle totals.

    A single mean is a poor reference here — only 5 of 17 cycles land within
    ±15% of it, because spending is a stable base plus occasional travel.
    """
    return float(totals.quantile(0.25)), float(totals.quantile(0.75))


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

# ── Visual system ─────────────────────────────────────────────────────────────
# Categorical hues are assigned in fixed order and never cycled. With 14
# categories that is well past the 8-slot limit, so category identity is carried
# by axis labels and small multiples rather than by hue: ranked bars use ONE
# colour, and only genuine 2-series charts spend a second slot.
# Palette validated against the white chart surface (all-pairs, light mode).

SERIES_1  = "#2a78d6"   # blue   — default single series
SERIES_2  = "#eb6834"   # orange — second series only
ACCENT    = "#256abf"   # darker blue for emphasis
INK       = "#0b0b0b"
INK_2     = "#52514e"
MUTED     = "#898781"
GRID      = "#e1e0d9"
BASELINE  = "#c3c2b7"
BAND_FILL = "#e8e7e1"
UP, DOWN  = "#d03b3b", "#0ca30c"   # polarity, always paired with an arrow + word
FONT      = "system-ui, -apple-system, 'Segoe UI', sans-serif"

# The Plotly toolbar overlays the top-right of every plot on hover, covering
# labels and annotations. Nothing here needs pan/zoom, so it is switched off.
CHART_CFG = {"displayModeBar": False, "displaylogo": False}


def stat_tile(label, value, sub="", tip=""):
    """A stat tile with its sub-line inside the card.

    st.metric can't do this: its only sub-line slot is `delta`, which always
    stamps an ↑/↓ arrow, and these sub-lines are descriptions rather than changes.
    """
    t = f' title="{tip}"' if tip else ""
    st.markdown(
        f'<div{t} style="background:#fcfcfb;border:1px solid rgba(11,11,11,.08);'
        f'border-radius:10px;padding:14px 16px 12px;height:100%">'
        f'<div style="color:{MUTED};font-size:.71rem;text-transform:uppercase;'
        f'letter-spacing:.05em;font-weight:600">{label}</div>'
        f'<div style="color:{INK};font-size:1.5rem;font-weight:600;'
        f'line-height:1.45;margin:3px 0 1px">{value}</div>'
        f'<div style="color:{MUTED};font-size:.79rem">{sub}</div>'
        f'</div>', unsafe_allow_html=True)


def styled(fig, height=280, grid_y=True, legend=False):
    """Apply the shared chart chrome: hairline axes, recessive grid, no frame."""
    fig.update_layout(
        font=dict(family=FONT, size=12, color=INK_2),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(t=8, b=0, l=0, r=8),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0, title="",
                    font=dict(size=11, color=INK_2)),
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=BASELINE,
                        font=dict(family=FONT, size=12, color=INK)),
        bargap=0.28,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showline=True,
                     linecolor=BASELINE, linewidth=1,
                     tickfont=dict(color=MUTED, size=11), title="")
    fig.update_yaxes(showgrid=grid_y, gridcolor=GRID, gridwidth=1,
                     zeroline=False, showline=False,
                     tickfont=dict(color=MUTED, size=11))
    return fig


st.markdown(f"""<style>
  .block-container {{padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1350px;}}
  h1 {{font-size: 1.65rem !important; font-weight: 650 !important;
       letter-spacing: -.02em; margin-bottom: .2rem;}}
  h2 {{font-size: 1.15rem !important; font-weight: 620 !important;
       letter-spacing: -.01em; margin-top: .4rem;}}
  h3 {{font-size: .98rem !important; font-weight: 600 !important;}}
  [data-testid="stMetric"] {{
      background: #fcfcfb; border: 1px solid rgba(11,11,11,.08);
      border-radius: 10px; padding: 14px 16px 12px;
  }}
  [data-testid="stMetricLabel"] p {{
      color: {MUTED} !important; font-size: .72rem !important;
      text-transform: uppercase; letter-spacing: .05em; font-weight: 600;
  }}
  [data-testid="stMetricValue"] {{
      font-size: 1.45rem !important; font-weight: 600 !important; color: {INK};
  }}
  [data-testid="stMetricDelta"] {{font-size: .78rem !important;}}
  button[role="tab"] {{font-weight: 560 !important; font-size: .95rem !important;}}
  [data-testid="stCaptionContainer"] p {{color: {MUTED}; font-size: .8rem;}}
  hr {{margin: 1.6rem 0 1.2rem; border-color: rgba(11,11,11,.07);}}
  [data-testid="stSidebar"] {{border-right: 1px solid rgba(11,11,11,.07);}}
</style>""", unsafe_allow_html=True)

# ── Shared scope ──────────────────────────────────────────────────────────────
expenses["Kind"] = expenses["Category"].apply(spend_kind)

cycle_totals = expenses.groupby("Month")["Amount"].sum()
done_totals  = cycle_totals[COMPLETE_CYCLES] if COMPLETE_CYCLES else cycle_totals
BAND_LO, BAND_HI = typical_band(done_totals) if len(done_totals) else (0.0, 0.0)
TYPICAL = float(done_totals.median()) if len(done_totals) else 0.0

PERIODS = {"Last 3 cycles": 3, "Last 6 cycles": 6, "Last 12 cycles": 12, "All": None}


def period_pick(key):
    """One time control, rendered the same way everywhere it appears."""
    label = st.radio("Period", list(PERIODS), index=1, horizontal=True,
                     label_visibility="collapsed", key=key)
    n = PERIODS[label] or len(COMPLETE_CYCLES)
    n = min(n, len(COMPLETE_CYCLES))
    return COMPLETE_CYCLES[-n:], COMPLETE_CYCLES[max(0, len(COMPLETE_CYCLES) - 2 * n):-n]


def band_chart(totals_series, height=300, label_every=False):
    """Cycle totals as one-colour bars against the shaded normal range.

    The band does the interpretation, so the bars stay a single hue — colouring
    them by size would double-encode the length they already show.
    """
    d = totals_series.reset_index()
    d.columns  = ["Month", "Amount"]
    d["Label"] = d["Month"].apply(cycle_label)
    d["Done"]  = d["Month"].isin(COMPLETE_CYCLES)

    # Direct-label selectively: the extremes and the latest, drawn only from
    # complete cycles — a partial cycle is always the minimum, which would waste
    # a label on an artefact.
    dc   = d[d["Done"]]
    keep = ({dc["Amount"].idxmax(), dc["Amount"].idxmin(), dc.index[-1]}
            if not dc.empty else set())
    d["Tag"] = [f"{v:,.0f}" if (label_every or i in keep) else ""
                for i, v in d["Amount"].items()]

    fig = go.Figure()
    if BAND_HI:
        fig.add_hrect(y0=BAND_LO, y1=BAND_HI, fillcolor=BAND_FILL, opacity=1,
                      line_width=0, layer="below")
    fig.add_trace(go.Bar(
        x=d["Label"], y=d["Amount"],
        marker=dict(color=[SERIES_1 if k else BAND_FILL for k in d["Done"]],
                    cornerradius=4),
        text=d["Tag"], textposition="outside",
        textfont=dict(color=INK_2, size=11),
        customdata=d["Done"].map({True: "complete", False: "partial cycle"}),
        hovertemplate="<b>%{x}</b><br>OMR %{y:,.0f}<br>%{customdata}<extra></extra>",
    ))
    styled(fig, height=height)
    fig.update_yaxes(tickformat=",d", title="OMR",
                     range=[0, d["Amount"].max() * 1.18])
    return fig


t_over, t_cats, t_trends, t_txns, t_setup = st.tabs(
    ["Overview", "Categories", "Trends", "Transactions", "⚙️ Setup"]
)

# ════════════════════════════════════════════════════════════════════════════════
# OVERVIEW — where things stand, and what changed since last time
# ════════════════════════════════════════════════════════════════════════════════
with t_over:
    if not COMPLETE_CYCLES:
        st.warning("Need at least one complete billing cycle.")
    else:
        latest      = COMPLETE_CYCLES[-1]
        latest_tot  = float(cycle_totals[latest])
        latest_data = expenses[expenses["Month"] == latest]
        last6       = COMPLETE_CYCLES[-6:]
        verdict     = ("above normal" if latest_tot > BAND_HI else
                       "below normal" if latest_tot < BAND_LO else "within normal")

        if INPROGRESS:
            el, tot_d = cycle_progress(INPROGRESS)
            st.caption(
                f"{cycle_label(INPROGRESS)} is still open (day {el} of {tot_d}) and is "
                f"excluded everywhere except the transaction list."
            )

        c1, c2, c3 = st.columns(3)
        with c1:
            stat_tile(f"Last complete cycle · {cycle_label(latest)}",
                      f"OMR {latest_tot:,.0f}", verdict)
        with c2:
            stat_tile("Typical cycle", f"OMR {TYPICAL:,.0f}",
                      f"normal range {BAND_LO:,.0f}–{BAND_HI:,.0f}",
                      tip="Median and the middle half (25th–75th percentile) of your "
                          "complete cycles. Your spending is a steady base plus "
                          "occasional travel, so a single average is a poor reference.")
        with c3:
            stat_tile(f"Last {len(last6)} cycles",
                      f"OMR {cycle_totals[last6].sum():,.0f}",
                      f"OMR {cycle_totals[last6].mean():,.0f} per cycle")

        st.divider()

        st.subheader("Spend per cycle")
        st.plotly_chart(band_chart(cycle_totals, height=320),
                        width="stretch", config=CHART_CFG)
        st.caption(f"Shaded band is your normal range, OMR {BAND_LO:,.0f}–{BAND_HI:,.0f}. "
                   "Pale bars are partial cycles, excluded from the band.")

        st.divider()

        # ── Where the money goes ───────────────────────────────────────────────
        left, right = st.columns([3, 2])

        with left:
            st.subheader(f"Where the money goes · last {len(last6)} cycles")
            cat6 = (expenses[expenses["Month"].isin(last6)]
                    .groupby("Category")["Amount"].sum().sort_values() / len(last6))
            share = cat6 / cat6.sum() * 100
            fig_cat = go.Figure(go.Bar(
                x=cat6.values, y=cat6.index, orientation="h",
                marker=dict(color=SERIES_1, cornerradius=4),
                text=[f"OMR {v:,.0f}  ·  {s:.0f}%" for v, s in zip(cat6.values, share.values)],
                textposition="outside", textfont=dict(color=INK_2, size=11),
                hovertemplate="<b>%{y}</b><br>OMR %{x:,.0f} per cycle<extra></extra>",
            ))
            styled(fig_cat, height=max(340, len(cat6) * 30), grid_y=False)
            fig_cat.update_xaxes(showticklabels=False, showline=False,
                                 range=[0, cat6.max() * 1.5])
            st.plotly_chart(fig_cat, width="stretch", config=CHART_CFG)
            st.caption("OMR per cycle, averaged over the period.")

        with right:
            st.subheader("What changed")
            n3 = COMPLETE_CYCLES[-3:]
            p3 = COMPLETE_CYCLES[-6:-3]
            movers = category_movers(expenses, n3, p3, top_n=5)
            if movers.empty:
                st.info("Needs at least 6 complete cycles.")
            else:
                st.caption(f"Last 3 cycles vs the 3 before, OMR per cycle")
                for _, r in movers.iterrows():
                    arrow = "▲" if r["Change"] > 0 else "▼"
                    colr  = UP if r["Change"] > 0 else DOWN
                    st.markdown(
                        f"<div style='padding:9px 0;border-bottom:1px solid rgba(11,11,11,.06)'>"
                        f"<span style='font-weight:600'>{r['Category']}</span><br>"
                        f"<span style='color:{colr};font-weight:600'>{arrow} "
                        f"{r['Change']:+,.0f}</span> "
                        f"<span style='color:{MUTED}'>· now {r['Now']:,.0f} "
                        f"vs {r['Usual']:,.0f}</span>"
                        + (f"<br><span style='color:{MUTED};font-size:.85em'>"
                           f"↳ {r['Driver']} ({r['DriverChange']:+,.0f})</span>"
                           if r["Driver"] != "—" else "")
                        + "</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# CATEGORIES — is each one rising, falling, or just noisy?
# ════════════════════════════════════════════════════════════════════════════════
with t_cats:
    if len(COMPLETE_CYCLES) < 2:
        st.warning("Need at least two complete billing cycles.")
    else:
        period, _ = period_pick("cat_period")
        pdata = expenses[expenses["Month"].isin(period)]
        st.caption(f"{cycle_label(period[0])} – {cycle_label(period[-1])} · "
                   f"{len(period)} complete cycle(s) · OMR {pdata['Amount'].sum():,.0f}")

        grid = (pdata.pivot_table(index="Month", columns="Category",
                                  values="Amount", aggfunc="sum")
                .reindex(period).fillna(0))
        order = grid.mean().sort_values(ascending=False)

        # ── Rising / falling table ─────────────────────────────────────────────
        # A category only counts as moving if the change clears its own
        # volatility AND is materially large. Travel swings by OMR 279 between
        # cycles, so a 50-OMR "rise" there is noise; in Fuel it would be real.
        st.subheader("Rising and falling")
        half = max(1, len(period) // 2)
        rows = []
        for c in order.index:
            s = grid[c]
            now, before = s.iloc[-half:].mean(), s.iloc[:half].mean()
            noise, chg  = s.std(), now - before
            if noise and abs(chg) >= max(15, noise * 0.75):
                trend = "▲ rising" if chg > 0 else "▼ falling"
            else:
                trend = "— steady"
            rows.append({
                # "OMR / cycle" is the whole-period average, so it agrees with
                # both the row order and the share bar. Recent vs Was carries
                # the movement.
                "Category": c, "OMR / cycle": round(float(order[c]), 1),
                "Recent": round(now, 1), "Was": round(before, 1),
                "Change": round(chg, 1), "Trend": trend,
                "Share": float(order[c] / order.sum() * 100),
            })
        tbl = pd.DataFrame(rows)
        st.dataframe(
            tbl, hide_index=True, width="stretch", height=38 + len(tbl) * 35,
            column_config={
                "OMR / cycle": st.column_config.NumberColumn(format="%.0f"),
                "Recent": st.column_config.NumberColumn(
                    f"Last {half}", format="%.0f",
                    help=f"Average over the last {half} cycle(s) of the period"),
                "Was": st.column_config.NumberColumn(
                    f"First {half}", format="%.0f"),
                "Change": st.column_config.NumberColumn(format="%+.0f"),
                "Share": st.column_config.ProgressColumn(
                    "Share of spend", format="%.0f%%", min_value=0,
                    max_value=float(tbl["Share"].max())),
            },
        )
        st.caption(
            f"“Steady” means the change is inside the category's own cycle-to-cycle "
            f"swing — not that nothing moved. Comparing the last {half} cycle(s) "
            f"against the first {half}."
        )

        st.divider()

        # ── Small multiples ────────────────────────────────────────────────────
        # One panel per category on its own y-scale. A shared scale would flatten
        # everything below Groceries into invisibility, and the question here is
        # the SHAPE of each category, not how they compare in size — the per-cycle
        # figure in each panel title carries magnitude.
        st.subheader("Category trends")
        st.caption("Each panel has its own vertical scale, so shapes are comparable "
                   "but heights are not. The figure beside each name is OMR per cycle.")

        cols_n = 4
        cats   = list(order.index)
        rows_n = -(-len(cats) // cols_n)
        fig_sm = make_subplots(
            rows=rows_n, cols=cols_n, shared_xaxes=False,
            subplot_titles=[f"{c}  ·  {order[c]:,.0f}" for c in cats],
            vertical_spacing=0.13, horizontal_spacing=0.06,
        )
        labels = [cycle_label(m) for m in period]
        for i, c in enumerate(cats):
            r, cc = i // cols_n + 1, i % cols_n + 1
            fig_sm.add_trace(go.Bar(
                x=labels, y=grid[c].values,
                marker=dict(color=SERIES_1, cornerradius=2),
                hovertemplate=f"<b>{c}</b><br>%{{x}}<br>OMR %{{y:,.0f}}<extra></extra>",
            ), row=r, col=cc)

        fig_sm.update_layout(
            font=dict(family=FONT, size=11, color=INK_2),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False, bargap=0.3,
            height=165 * rows_n, margin=dict(t=30, b=10, l=0, r=8),
            hoverlabel=dict(bgcolor="#ffffff", bordercolor=BASELINE,
                            font=dict(family=FONT, size=12, color=INK)),
        )
        fig_sm.update_xaxes(showticklabels=False, showgrid=False, zeroline=False,
                            showline=True, linecolor=BASELINE, linewidth=1)
        fig_sm.update_yaxes(showticklabels=False, showgrid=False, zeroline=False,
                            showline=False)
        for a in fig_sm.layout.annotations:
            a.font.size, a.font.color, a.xanchor, a.x = 11, INK_2, "left", a.x - 0.045
        st.plotly_chart(fig_sm, width="stretch", config=CHART_CFG)

        st.divider()

        # ── One category in detail ─────────────────────────────────────────────
        st.subheader("One category in detail")
        sel = st.selectbox("Category", list(order.index), label_visibility="collapsed")
        sdata = pdata[pdata["Category"] == sel]

        d1, d2 = st.columns([3, 2])
        with d1:
            s = grid[sel]
            avg = s.mean()
            fig_one = go.Figure(go.Bar(
                x=labels, y=s.values,
                marker=dict(color=SERIES_1, cornerradius=4),
                text=[f"{v:,.0f}" for v in s.values], textposition="outside",
                textfont=dict(color=INK_2, size=10),
                hovertemplate="<b>%{x}</b><br>OMR %{y:,.0f}<extra></extra>",
            ))
            fig_one.add_hline(y=avg, line_color=MUTED, line_width=1,
                              annotation_text=f"avg {avg:,.0f}",
                              annotation_position="right",
                              annotation_font=dict(color=MUTED, size=10))
            styled(fig_one, height=290)
            fig_one.update_yaxes(tickformat=",d", title="OMR",
                                 range=[0, max(s.max(), avg) * 1.22])
            st.plotly_chart(fig_one, width="stretch", config=CHART_CFG)

        with d2:
            mr = (sdata.groupby("Merchant")["Amount"].sum()
                  .sort_values(ascending=False).head(8).sort_values())
            fig_mr = go.Figure(go.Bar(
                x=mr.values, y=[m[:24] for m in mr.index], orientation="h",
                marker=dict(color=SERIES_1, cornerradius=3),
                text=[f"{v:,.0f}" for v in mr.values], textposition="outside",
                textfont=dict(color=INK_2, size=10),
                hovertemplate="<b>%{y}</b><br>OMR %{x:,.0f}<extra></extra>",
            ))
            styled(fig_mr, height=290, grid_y=False)
            fig_mr.update_xaxes(showticklabels=False, showline=False,
                                range=[0, mr.max() * 1.4])
            st.plotly_chart(fig_mr, width="stretch", config=CHART_CFG)
            st.caption(f"Top merchants · {sdata['Merchant'].nunique()} in total")

        det = sdata[["Transaction Date", "Merchant", "Amount", "Month"]].copy()
        det["Date"]  = det["Transaction Date"].dt.strftime("%d %b %Y")
        det["OMR"]   = det["Amount"].round(0).astype(int)
        det["Cycle"] = det["Month"].apply(cycle_label)
        st.dataframe(det[["Date", "Cycle", "Merchant", "OMR"]]
                     .sort_values("OMR", ascending=False),
                     hide_index=True, width="stretch", height=300)
        st.caption(f"{len(sdata)} transaction(s) · OMR {sdata['Amount'].sum():,.0f}")


# ════════════════════════════════════════════════════════════════════════════════
# TRENDS — the overall shape, and what drives the swings
# ════════════════════════════════════════════════════════════════════════════════
with t_trends:
    if len(COMPLETE_CYCLES) < 3:
        st.warning("Need at least three complete billing cycles.")
    else:
        st.subheader("Everyday base vs episodic spend")
        st.caption(
            "Everyday is food, groceries, fuel and bills; episodic is travel and "
            "large one-off purchases. Measured over your history, everyday runs at "
            "roughly a third the volatility of episodic — so almost every swing in "
            "your monthly total comes from the orange band."
        )
        kd = (expenses[expenses["Month"].isin(COMPLETE_CYCLES)]
              .pivot_table(index="Month", columns="Kind", values="Amount",
                           aggfunc="sum").reindex(COMPLETE_CYCLES).fillna(0))
        klab = [cycle_label(m) for m in COMPLETE_CYCLES]

        fig_k = go.Figure()
        for name, colr in (("Everyday", SERIES_1), ("Episodic", SERIES_2)):
            if name in kd:
                fig_k.add_trace(go.Bar(
                    x=klab, y=kd[name], name=name,
                    marker=dict(color=colr, line=dict(color="#ffffff", width=2)),
                    hovertemplate=f"<b>{name}</b><br>%{{x}}<br>OMR %{{y:,.0f}}<extra></extra>",
                ))
        styled(fig_k, height=330, legend=True)
        fig_k.update_layout(barmode="stack", bargap=0.3)
        fig_k.update_yaxes(tickformat=",d", title="OMR")
        st.plotly_chart(fig_k, width="stretch", config=CHART_CFG)

        s1, s2 = st.columns(2)
        for col, kind in ((s1, "Everyday"), (s2, "Episodic")):
            if kind in kd:
                v = kd[kind]
                with col:
                    stat_tile(f"{kind} · typical cycle", f"OMR {v.median():,.0f}",
                              f"swings between OMR {v.min():,.0f} and {v.max():,.0f}")

        st.divider()

        st.subheader("Total with 3-cycle average")
        # Complete cycles only. A partial bar would add nothing to a trend view
        # and, being first in the series, would also hand the legend swatch its
        # pale colour.
        d = cycle_totals[COMPLETE_CYCLES].reset_index()
        d.columns  = ["Month", "Amount"]
        d["Label"] = d["Month"].apply(cycle_label)
        d["R3"]    = d["Amount"].rolling(3, min_periods=1).mean()

        fig_r = go.Figure()
        fig_r.add_hrect(y0=BAND_LO, y1=BAND_HI, fillcolor=BAND_FILL, opacity=1,
                        line_width=0, layer="below")
        fig_r.add_trace(go.Bar(
            x=d["Label"], y=d["Amount"], name="Cycle total",
            marker=dict(color=SERIES_1, cornerradius=4),
            hovertemplate="<b>%{x}</b><br>OMR %{y:,.0f}<extra></extra>"))
        fig_r.add_trace(go.Scatter(
            x=d["Label"], y=d["R3"], name="3-cycle average", mode="lines",
            line=dict(color=SERIES_2, width=2),
            hovertemplate="3-cycle avg: OMR %{y:,.0f}<extra></extra>"))
        styled(fig_r, height=330, legend=True)
        fig_r.update_yaxes(tickformat=",d", title="OMR")
        st.plotly_chart(fig_r, width="stretch", config=CHART_CFG)
        st.caption("The shaded band is your normal range. Partial cycles are excluded.")

        st.divider()

        # ── Trips: the usual explanation for an episodic spike ─────────────────
        st.subheader("Trips")
        st.caption("Detected from clusters of foreign-currency spend that include a "
                   "flight, hotel or taxi. Cost counts everything charged during the "
                   "window, not just the Travel category.")
        trips = detect_trips(expenses)
        if not trips:
            st.info("No trips detected.")
        else:
            td = pd.DataFrame(trips)
            td["When"] = (td["Start"].dt.strftime("%d %b %Y") + " – "
                          + td["End"].dt.strftime("%d %b %Y"))
            st.dataframe(
                td[["Trip", "When", "Days", "Total", "PerDay", "Txns"]].rename(
                    columns={"Total": "Total OMR", "PerDay": "OMR / day"}),
                hide_index=True, width="stretch", height=38 + len(td) * 35,
                column_config={
                    "Total OMR": st.column_config.NumberColumn(format="%.0f"),
                    "OMR / day": st.column_config.NumberColumn(format="%.0f"),
                })
            st.caption(f"{len(td)} trip(s) · **OMR {td['Total'].sum():,.0f}** total · "
                       f"{td['Total'].sum() / expenses['Amount'].sum() * 100:.0f}% of all spend")

        st.divider()

        # ── Recurring, started, stopped ────────────────────────────────────────
        st.subheader("Merchants you keep paying")
        recent_done = COMPLETE_CYCLES[-6:]
        rd = expenses[expenses["Month"].isin(recent_done) & (expenses["Type"] == "Recurring")]
        if rd.empty:
            st.info("Needs about six complete cycles.")
        else:
            pc  = rd.groupby(["Merchant", "Month"])["Amount"].sum()
            agg = pc.groupby("Merchant").agg(Cycles="count", _m="mean", _s="std").fillna(0)
            agg["OMR / cycle"] = (pc.groupby("Merchant").sum() / len(recent_done)).round(1)
            agg["Amount"] = (agg["_s"] / agg["_m"]).apply(
                lambda cv: "steady" if cv <= 0.40 else "varies")
            agg = (agg[["OMR / cycle", "Cycles", "Amount"]]
                   .sort_values("OMR / cycle", ascending=False).reset_index())
            agg["Cycles"] = agg["Cycles"].astype(int).astype(str) + f"/{len(recent_done)}"
            st.dataframe(agg, hide_index=True, width="stretch",
                         height=38 + len(agg) * 35)
            st.caption(
                f"Seen in at least 4 of the last {len(recent_done)} cycles. Most are "
                "**varies** — groceries and fuel: predictable that you'll spend, not "
                "how much. Only the *steady* rows behave like fixed bills."
            )

        if len(COMPLETE_CYCLES) >= 4:
            recent_w, prior_w = COMPLETE_CYCLES[-3:], COMPLETE_CYCLES[:-3]
            src = expenses[expenses["Month"].isin(COMPLETE_CYCLES)]
            rm  = set(src[src["Month"].isin(recent_w)]["Merchant"])
            pm  = set(src[src["Month"].isin(prior_w)]["Merchant"])
            started = (src[src["Merchant"].isin(rm - pm) & src["Month"].isin(recent_w)]
                       .groupby("Merchant")["Amount"].sum()
                       .sort_values(ascending=False).head(6))
            est = src[src["Month"].isin(prior_w)].groupby("Merchant")["Month"].nunique()
            lap = [m for m in (pm - rm) if est.get(m, 0) >= max(3, len(prior_w) // 3)]
            lapsed = (src[src["Merchant"].isin(lap)].groupby("Merchant")["Amount"].sum()
                      .sort_values(ascending=False).head(6))

            g1, g2 = st.columns(2)
            with g1:
                st.markdown("**Started** — new in the last 3 cycles")
                if started.empty:
                    st.caption("Nothing new.")
                for m, v in started.items():
                    st.markdown(f"<div style='color:{INK_2};font-size:.85rem;padding:2px 0'>"
                                f"{m} · OMR {v:,.0f}</div>", unsafe_allow_html=True)
            with g2:
                st.markdown("**Stopped** — was a habit, now gone")
                if lapsed.empty:
                    st.caption("Nothing stopped.")
                for m, v in lapsed.items():
                    last = src[src["Merchant"] == m]["Month"].max()
                    st.markdown(f"<div style='color:{INK_2};font-size:.85rem;padding:2px 0'>"
                                f"{m} · was OMR {v:,.0f}, last seen {cycle_label(last)}</div>",
                                unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TRANSACTIONS
# ════════════════════════════════════════════════════════════════════════════════
with t_txns:
    q = st.text_input("Search", placeholder="e.g. lulu spar — space or comma separates terms",
                      label_visibility="collapsed")
    found = expenses
    if q:
        terms = [t.strip().upper() for t in q.replace(",", " ").split() if t.strip()]
        hay   = expenses["Description"].str.upper() + " " + expenses["Merchant"].str.upper()
        found = expenses[hay.apply(lambda d: any(t in d for t in terms))]

        if not found.empty:
            fm = found.groupby("Month")["Amount"].sum()
            fig_q = go.Figure(go.Bar(
                x=[cycle_label(m) for m in fm.index], y=fm.values,
                marker=dict(color=SERIES_1, cornerradius=4),
                text=[f"{v:,.0f}" for v in fm.values], textposition="outside",
                textfont=dict(color=INK_2, size=10),
                hovertemplate="<b>%{x}</b><br>OMR %{y:,.0f}<extra></extra>"))
            styled(fig_q, height=270)
            fig_q.update_yaxes(tickformat=",d", title="OMR",
                               range=[0, fm.max() * 1.2])
            st.plotly_chart(fig_q, width="stretch", config=CHART_CFG)
            st.caption(f"Monthly spend matching “{' / '.join(terms)}” · "
                       f"OMR {found['Amount'].sum():,.0f} total")

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
        hide_index=True, width="stretch", key="txn_editor", height=420,
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

    st.divider()

    # ── Bill verification ──────────────────────────────────────────────────────
    st.subheader("Bill verification")
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
        st.dataframe(recon[["Period", "Expenses (OMR)", "Payment (OMR)", "Difference"]],
                     hide_index=True, width="stretch", height=300,
                     column_config={"Difference": st.column_config.NumberColumn(
                         format="%+d", help="Payment − Expenses. Negative is an "
                                            "underpayment, positive a credit.")})


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
                f"Category for {merch}",
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
