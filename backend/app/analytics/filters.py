
from __future__ import annotations

import pandas as pd

from app.analytics.columns import find_column

DATE_CANDIDATES = (
    "date", "order date", "orderdate", "created at", "timestamp",
    "invoice date", "purchase date",
)
CATEGORY_CANDIDATES = (
    "category", "product category", "sub category", "segment",
    "department",
)
REGION_CANDIDATES = (
    "region", "country", "state", "market", "territory", "zone",
    "province", "area", "location", "city",
)


def _parse_day(value: str, label: str) -> pd.Timestamp:
    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        raise ValueError(
            f"Invalid {label} '{value}'. Use a format such as 2026-01-31."
        )

    return parsed.normalize()


def apply_filters(
    df: pd.DataFrame,
    *,
    date_column: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    category_column: str | None = None,
    category_value: str | None = None,
    region_column: str | None = None,
    region_value: str | None = None,
) -> tuple[pd.DataFrame, dict, list[str]]:
    """Apply optional date/category/region filters to a dataset.

    Returns the filtered frame, a description of the filters that were
    applied, and any non-fatal warnings (for example a filter that matched
    no rows).
    """
    warnings: list[str] = []
    applied: dict = {
        "date_from": None,
        "date_to": None,
        "category_value": None,
        "region_value": None,
    }

    work = df

    if date_from or date_to:
        resolved_date = find_column(df, date_column, DATE_CANDIDATES)

        if resolved_date is None:
            warnings.append(
                "Date filters were ignored: no date column was detected."
            )
        else:
            dates = pd.to_datetime(work[resolved_date], errors="coerce")
            applied["date_column"] = str(resolved_date)

            if date_from:
                start = _parse_day(date_from, "start date")
                applied["date_from"] = start.date().isoformat()
                # NaT comparisons evaluate to False, so rows with
                # unparseable dates are excluded by a date range filter.
                work = work[dates >= start]
                dates = pd.to_datetime(work[resolved_date], errors="coerce")

            if date_to:
                end = _parse_day(date_to, "end date")
                applied["date_to"] = end.date().isoformat()
                work = work[dates <= end]

            if work.empty:
                warnings.append(
                    "No rows match the selected date range."
                )

    if category_value:
        resolved_category = find_column(
            df, category_column, CATEGORY_CANDIDATES
        )

        if resolved_category is None:
            warnings.append(
                "Category filter was ignored: no category column was "
                "detected."
            )
        else:
            applied["category_column"] = str(resolved_category)
            applied["category_value"] = str(category_value)
            values = (
                work[resolved_category]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.casefold()
            )
            work = work[values == str(category_value).strip().casefold()]

            if work.empty:
                warnings.append(
                    f"No rows match category '{category_value}'."
                )

    if region_value:
        resolved_region = find_column(df, region_column, REGION_CANDIDATES)

        if resolved_region is None:
            warnings.append(
                "Region filter was ignored: no region column was detected."
            )
        else:
            applied["region_column"] = str(resolved_region)
            applied["region_value"] = str(region_value)
            values = (
                work[resolved_region]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.casefold()
            )
            work = work[values == str(region_value).strip().casefold()]

            if work.empty:
                warnings.append(
                    f"No rows match region '{region_value}'."
                )

    if len(work) == len(df):
        return df, applied, warnings

    return work.copy(), applied, warnings


def build_facets(
    df: pd.DataFrame,
    *,
    category_column: str | None = None,
    region_column: str | None = None,
    limit: int = 100,
) -> dict:
    """Distinct category/region values used to populate filter controls."""
    facets: dict = {"category": [], "region": []}

    for candidates, key, explicit in (
        (CATEGORY_CANDIDATES, "category", category_column),
        (REGION_CANDIDATES, "region", region_column),
    ):
        column = find_column(df, None if not explicit else explicit, candidates)

        if column is None:
            continue

        values = (
            df[column]
            .dropna()
            .astype(str)
            .str.strip()
        )
        values = values[values != ""]
        facets[key] = sorted(values.unique().tolist())[:limit]

    return facets
