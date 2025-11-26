"""Script to greedily select roster entries"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client
from supabase import Client

from utils import save_results
from utils import get_available_years_teams

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

async def retrieve_event_performances(
        team: str,
        year: int,
        event: str
) -> tuple[dict | None, str | None]:
    """asdf"""
    ret={}; error=None
    try:
        response = (
            supabase.rpc(
                "retrieve_event_performance",
                {
                    "season_year" : year,
                    "team" : team,
                    "event_class" : event,
                }
            )
            .execute()
        )
        ret = response.data
    
    except Exception as e:
        error = f"ERROR calling RETRIEVE_EVENT_PERFORMANCE(): {e}"
    
    return ret, error

def greedy_selector() -> None:
    pass