from pathlib import Path

import pandas as pd
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def backend_root() -> Path:
    return BACKEND_ROOT


@pytest.fixture(scope="session")
def sample_frame() -> pd.DataFrame:
    """The bundled 21-month sample dataset."""
    return pd.read_csv(BACKEND_ROOT / "sample_sales.csv")


@pytest.fixture
def sales_frame() -> pd.DataFrame:
    """Small deterministic dataset with known KPI values.

    Sales total 1040, profit 203, 7 distinct orders, 16 units,
    6 distinct months and two line items sharing order O1.
    """
    rows = [
        ("O1", "2026-01-05", "Widget", "Hardware", "North", 2, 100.0, 25.0),
        ("O1", "2026-01-15", "Gadget", "Hardware", "North", 1, 50.0, 10.0),
        ("O2", "2026-02-10", "Widget", "Software", "South", 3, 120.0, 30.0),
        ("O3", "2026-03-05", "Gadget", "Software", "North", 1, 90.0, 18.0),
        ("O4", "2026-04-20", "Widget", "Hardware", "South", 2, 140.0, 35.0),
        ("O5", "2026-05-02", "Gadget", "Hardware", "North", 4, 160.0, 40.0),
        ("O6", "2026-06-18", "Widget", "Software", "South", 1, 180.0, -5.0),
        ("O7", "2026-06-25", "Gadget", "Software", "North", 2, 200.0, 50.0),
    ]

    return pd.DataFrame(rows, columns=[
        "OrderID", "OrderDate", "Product", "Category", "Region",
        "Quantity", "Sales", "Profit",
    ])


@pytest.fixture
def messy_frame() -> pd.DataFrame:
    """Dataset with missing values, invalid dates and a text numeric column."""
    return pd.DataFrame({
        "Order ID": ["1", "2", "3", "4"],
        "Order Date": ["2026-01-01", "not-a-date", "2026-03-01", None],
        "Sales": ["100", "abc", "300", "400"],
        "Region": ["North", None, "South", "North"],
        "Empty": [None, None, None, None],
    })


@pytest.fixture
def no_date_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "OrderID": ["1", "2", "3"],
        "Sales": [10.0, 20.0, 30.0],
        "Category": ["A", "B", "A"],
    })
