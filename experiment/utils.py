"""Helper functions for running experiments"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client
from supabase import Client

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def save_results(
        data: dict | pd.DataFrame,
        team: str,
        year: str,
        prefix: str,
) -> None:
    """Writes roster selections to results/ directory
    
    Parameters
    ----------
    data : dict | DataFrame
        your data you would like to write to disk (this will be saved as a parquet)
    
    team : str
        the team the roster selections were created for 
    
    year : str
        the year the roster selections were created for
    
    prefix : 
        helper to specify what type of results generated the roster selections (e.g., greedy, gemini, etc)
    """ 
    dest_dir = Path(__file__).expanduser().resolve().parent / "results"
    dest_dir.mkdir(exist_ok=True)
    filename = f"{prefix}_{team}_{year}_results.parquet"
    
    if isinstance(data, dict):
        pd.DataFrame(data).to_parquet(dest_dir / filename)
    else:
        data.to_parquet(dest_dir / filename)

async def get_available_years_teams() -> list[dict] | None:
    """Retrieves teams and years we can run the experiments with
    
    Returns
    -------
    output : list[dict] | None
        returns a list of dictionaries retrieved from database for available teams and years \
        the keys are "season_year" for years and "school" for the school
    
    Notes
    -----
    This is an asynchronous function so await me!
    """
    response = supabase.rpc("get_teams_years").execute()
    return response.data if response.data else None

