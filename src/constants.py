from __future__ import annotations

DEFAULT_RANDOM_STATE = 42
DEFAULT_PROFIT_MARGIN = 0.30

DEFAULT_FORECAST_HORIZONS = (30, 60, 90, 180, 365)
DEFAULT_TOP_N_SERIES = 5
DEFAULT_MIN_HISTORY_DAYS = 180
DEFAULT_TEST_SIZE = 30

SEASON_MAP = {
    12: "Winter",
    1: "Winter",
    2: "Winter",
    3: "Spring",
    4: "Spring",
    5: "Spring",
    6: "Summer",
    7: "Summer",
    8: "Summer",
    9: "Autumn",
    10: "Autumn",
    11: "Autumn",
}
SEASON_CODE = {"Winter": 0, "Spring": 1, "Summer": 2, "Autumn": 3}

PRODUCT_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Lighting": ("light", "lamp", "candlestick", "lantern"),
    "Decor": ("frame", "glass", "ornament", "decor", "tree"),
    "Accessories": ("bag", "wallet", "purse", "holder"),
    "Homeware": ("box", "storage", "jar", "cup", "plate"),
    "Stationery": ("card", "paper", "stationery"),
}
DEFAULT_PRODUCT_CATEGORY = "Other"

HOLIDAY_MONTH_DAY_PAIRS = {
    (1, 1),
    (12, 24),
    (12, 25),
    (12, 26),
    (12, 31),
}

RAW_DATA_FILENAMES = (
    "Online_Retail_II.xlsx",
    "online_retail_II.xlsx",
    "online_retail_ii.xlsx",
)
