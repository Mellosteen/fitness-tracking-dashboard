from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from src.auth import get_authed_client


TABLE_NAME = "daily_entries"


def _records_to_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    if not frame.empty and "entry_date" in frame:
        frame["entry_date"] = pd.to_datetime(frame["entry_date"]).dt.date
    return frame


def fetch_all_entries() -> pd.DataFrame:
    response = (
        get_authed_client()
        .table(TABLE_NAME)
        .select("*")
        .order("entry_date")
        .execute()
    )
    return _records_to_frame(response.data or [])


def fetch_user_entries(user_id: str) -> pd.DataFrame:
    response = (
        get_authed_client()
        .table(TABLE_NAME)
        .select("*")
        .eq("user_id", user_id)
        .order("entry_date")
        .execute()
    )
    return _records_to_frame(response.data or [])


def fetch_entry_for_date(user_id: str, entry_date: date) -> dict[str, Any] | None:
    response = (
        get_authed_client()
        .table(TABLE_NAME)
        .select("*")
        .eq("user_id", user_id)
        .eq("entry_date", entry_date.isoformat())
        .limit(1)
        .execute()
    )
    records = response.data or []
    return records[0] if records else None


def upsert_daily_entry(values: dict[str, Any]) -> None:
    get_authed_client().table(TABLE_NAME).upsert(
        values,
        on_conflict="user_id,entry_date",
    ).execute()
