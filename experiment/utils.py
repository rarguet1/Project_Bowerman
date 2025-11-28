"""Helper functions for running experiments"""
from __future__ import annotations

import os
from os import PathLike
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
        gender: str
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

    gender: str
        the gender the roster selections were created for
    
    prefix : str
        helper to specify what type of results generated the roster selections (e.g., greedy, gemini, etc)
    """ 

    # Base results directory
    base_dir = Path(__file__).expanduser().resolve().parent / "results"
    
    # If a subfolder is provided, append it to the path
    if subfolder:
        dest_dir = base_dir / subfolder
    else:
        dest_dir = base_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{prefix}_{team}_{year}_{gender}_results.parquet"
    
    if isinstance(data, dict):
        df_dict = {key: pd.Series(value) for key, value in data.items()}
        pd.DataFrame(df_dict).to_parquet(dest_dir / filename)
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


async def get_all_events() -> list[dict] | None:
    """Retrieves events and events we can run experiments with
    
    Returns
    -------
    output : list[dict] | None
        returns a list of dictionaries retrieved from database with distinct events
    """
    response = supabase.rpc("get_events").execute()
    return response.data if response.data else None


async def retrieve_event_performances(
        team: str,
        year: int,
        event: str,
        gender: str
) -> tuple[list[dict] | None, str | None]:
    """Retrieves event performances for a specified team, year, and gender
    
    Parameters
    ----------
    team : str
        The team/school you wish to pull event performances for

    year : int
        The year you wish to pull event performances for
    
    event : str
        The event (e.g., 100m, 200m, etc.) you wish to pull performances for

    gender : str
        The gender of the athlete performances you wish to pull event performances for
    
    Returns
    -------
    ret, error : tuple[list[dict] | None, str | None]
        On success ret will contain a list of dictionaries of performances for the above specified params \
        the keys for the dictionaries are 'ath_id', 'ath_name', and 'event_time'.
        
        On failure the ret field will be None and error will contain a string with error details.
    """
    ret={}; error=None
    try:
        response = (
            supabase.rpc(
                "retrieve_event_performance",
                {
                    "season_year" : year,
                    "team" : team,
                    "event_type" : event,
                    "ath_gender" : gender
                }
            )
            .execute()
        )
        ret = response.data
    
    except Exception as e:
        error = f"ERROR calling RETRIEVE_EVENT_PERFORMANCE(): {e}"
    
    return ret, error


def load_greedy_results(fp: PathLike) -> dict:
    """Subject to change! Loads greedy results and cleans out null entries
    
    Parameters
    ----------
    fp : PathLike
        filepath to data
    
    Returns
    -------
    ret : dict
        clean dictionary with keys for each event and the athlete id selections for each event
    """
    results = pd.read_parquet(fp).to_dict()
    ret = {}
    
    for event in results:
        ret[event] = {}
        for entry in results[event]:
            if results[event][entry] is not None:
                ret[event][entry] = results[event][entry]

    return ret
