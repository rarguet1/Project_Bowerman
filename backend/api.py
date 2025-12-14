from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from supabase import create_client
from supabase import Client
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# import llm_strategy 
from . import llm_strategy 

# uvicorn api:app --reload

# ---------------------------------------------------------------------------- #
#                                Pydantic Model                                #
# ---------------------------------------------------------------------------- #
class RosterRequest(BaseModel):
    team: str
    meet_context: str
    athlete_data: dict 
    provider: str = "gemini"

class DBRequest(BaseModel):
    year: int
    season: str 
    team: str 
    # ~ meet: str

# ---------------------------------------------------------------------------- #
#                                   Init API                                   #
# ---------------------------------------------------------------------------- #
app = FastAPI(
    title="Project Bowerman API",
    description="API for generating optimal track rosters using LLM logic."
)

# ---------------------------------------------------------------------------- #
#                               Supabase Client                                #
# ---------------------------------------------------------------------------- #
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# ---------------------------------------------------------------------------- #
#                          Backend Logic (Validation)                          #
# ---------------------------------------------------------------------------- #
def process_and_validate_data(athlete_data_text: str) -> tuple[dict, str]:
    """
    Tries to parse the JSON string and validate its basic structure.
    This version validates the new "event-first" data structure.
    """
    try:
        data = json.loads(athlete_data_text) 
        
        # Check if it's a dictionary and not empty
        if not isinstance(data, dict) or not data:
            return None, "Invalid JSON: Data must be a non-empty JSON object (e.g., {'100m': [...]})."
        return data, None
    except json.JSONDecodeError:
        return None, "Invalid input: Data is not valid JSON. Check your pasted data."
    except Exception as e:
        return None, f"An unexpected error occurred during validation: {e}"


def _parse_context(data: list[dict]) -> dict:
    """Helper to parse db team context to format"""
    ret = {}
    for row in data:
        stats = row["event_time"], row['event_wind']#, row['event_date']
        school=row["ath_team"]; gender=row["ath_gender"]; event=row["event_type"]
        name = row['ath_name']; ath_year=row['ath_year']; id = f"ATH_{row['ath_id']:05d}"
        key = f"{name} ({ath_year})"
        
        # adding school/team
        if school not in ret:
            ret[school] = {
                gender: {
                    event : {
                        key : [stats]
                    }
                }
            }

        # adding gender for team
        elif gender not in ret[school]:
            ret[school][gender] = {
                event : {
                    key : [stats]
                }
            }
        
        # adding event for team
        elif event not in ret[school][gender]:
            ret[school][gender][event] = {key: [stats]}

        # adding athlete to event
        elif key not in ret[school][gender][event]:
            ret[school][gender][event][key] = [stats]
        
        else:
            ret[school][gender][event][key].append(stats)
    
    return ret


async def query_db_for_team_context(
        team: str,
        year: int
) -> tuple[dict | None, str | None]:
    """Queries db for team performances for a given year """
    ret={}; error=None
    try:
        response = (
            supabase.rpc(
                "retrieve_team_context",
                {
                    "season_year": year,
                    "team" : team,
                }
            )
            .execute()
        )

        if response.data:
            ret = _parse_context(response.data)

    except Exception as e:
        error = f"ERROR calling RETRIEVE_TEAM_CONTEXT(): {e}"

    return ret, error


async def query_db_for_opponent_context_agg(
        exclude_team: str,
        year: int
) -> tuple[dict | None, str | None]:
    """Queries db for opponent team's context aggregated b"""
    ret={}; error=None
    try:
        response = (
            supabase.rpc(
                "retrieve_opponent_context_agg",
                {
                    "season_year" : year,
                    "exclude_team" : exclude_team
                }
            )
            .execute()
        )

        if response.data:
            ret = _parse_context(response.data)

    except Exception as e:
        error = f"ERROR calling RETRIEVE_OPPONENT_CONTEXT_AGG(): {e}"
    
    return ret, error


async def query_db_for_conference_context(year: int) -> tuple[dict | None, str | None]:
    """Queries db for actual conference entries (ground truth)"""
    ret={}; error=None
    try:
        response = (
            supabase.rpc(
                "retrieve_conference_context",
                {"season_year": year,}
            )
            .execute()
        )

        if response.data:
            for row in response.data:
                school=row["ath_team"]; event=row["event_type"]; gender=row["ath_gender"]
                id = f"ATH_{row['ath_id']:05d}"
                name = row['ath_name']

                # adding school/team
                if school not in ret:
                    ret[school] = {
                        gender : {
                            event : [(name,id)]
                        }
                    }
                
                # adding gender for school
                elif gender not in ret[school]:
                    ret[school][gender] = {event : [(name,id)]}

                # adding event for team
                elif event not in ret[school][gender]:
                    ret[school][gender][event] = [(name,id)]
                
                else:
                    ret[school][gender][event].append((name,id))

    except Exception as e:
        error = f"ERROR calling RETRIEVE_CONFERENCE_CONTEXT(): {e}"
    
    return ret, error

# ---------------------------------------------------------------------------- #
#                                 API Endpoint                                 #
# ---------------------------------------------------------------------------- #
@app.post("/generate_roster")
async def generate_roster_endpoint(request: RosterRequest) -> dict:
    """
    This endpoint receives meet context and athlete data (as a JSON string),
    validates it, and returns a generated roster with reasoning from an LLM.
    """
    # Validate and parse the input data
    # ~ parsed_data, error = process_and_validate_data(request.athlete_data)
    # ~ if error:
        # ~ raise HTTPException(status_code=400, detail=error)
    # ~ print("Data Parsed and Validated, Calling LLM")
    # Call the core logic from the strategy module
    roster, reasoning = await llm_strategy.generate_roster_strategy(
        team = request.team,
        athlete_data = request.athlete_data,
        meet_context = request.meet_context,
        provider=request.provider,
    )
    # Handle errors from the LLM
    if roster is None:
        raise HTTPException(status_code=500, detail=reasoning)
    # Return the successful response as a single JSON object
    return {
        "roster": roster,
        "reasoning": reasoning
    }


@app.post("/retrieve_context")
async def retrieve_context_endpoint(request: DBRequest) -> dict:
    """
    This endpoint receives year, season, meet, and team information and 
    returns the adjusted corresponding json entries 
    """
    
    try:
        # Validate and parse the input data
        year_input = request.year
        # ~ [2020, 2021, 2022, 2023, 2024, 2025]
        season_input = request.season
        # ~ ['Indoor', 'Outdoor'])
        team_input = request.team
        # ~ ['UMBC', '...'])
        # ~ meet_input = request.meet
        # ~ ["NCAA Division I Mid-Atlantic Region Cross Country Championships", "2025 America East Cross Country Championships", "2025 IC4A/ECAC XC Championship", "Paul Short Run (College)", "Cantello Invitational", "Mount St. Mary's 5k Duals 2025", "NCAA Division I Outdoor Track & Field Championships", "NCAA Division I East First Round", "2025 Outdoor IC4A/ECAC T&F Championships", "2025 America East Outdoor Track & Field Championship", "Penn Relays", "Virginia Challenge", "2025 Annual Legacy Track & Field Meet", "JMU Invitational", "Duke Invitational", "2025 George Mason Dalton Ebanks Invitational ", "Towson Invitational ", "Maryland Invitational", "UCF Black & Gold Challenge", "2025 America East Indoor Championship", "2025 Darius Dixon Memorial Invitational", "Boston University David Hemery Valentine Invitational", "Penn State National Open", "Dr. Sander Scorcher", "Nittany Lion Challenge", "VCU RAMS Indoor Invitational", "Youree Spence Garcia Meet", "NCAA Division I Mid-Atlantic Region Cross Country Championships", "2024 America East Cross Country Championships", "2024 IC4A/ECAC XC Championship", "Lehigh Paul Short Run (College)", "Harry Groves Spiked Shoe Invitational", "Cantello Invitational", "Mount St. Mary's 5k Duals", "NCAA East First Round", "2024 IC4A/ECAC Outdoor T&F Championships", "2024 America East Outdoor Track & Field Championships", "Penn Relays", "2024 Annual Legacy Track & Field Meet", "Virginia Challenge", "James Madison University Invitational", "Bison Outdoor Classic", "2024 George Mason Ebanks Invitational", "2024 Towson Invitational", "Weems Baskin Invitational 24", "2024 Towson Spring Opener", "America East Indoor Track & Field Championships", "2024 Darius Dixon Memorial Invitational", "Sykes & Sabock Challenge", "Penn State National Open"])
        error = None
    except Exception as e:
        error = f"An unexpected error occurred during extraction: {e}"
    if error:
        raise HTTPException(status_code = 400, detail = error)
    
    # Build team and meet context from database
    team_data, error = await query_db_for_team_context(team_input, year_input)
    if error:
        raise HTTPException(status_code = 500, detail = error)
    if len(team_data.keys()) == 0:
        raise HTTPException(status_code = 500, detail = "Data for year not found")
    if not (team_input in team_data.keys()):
        raise HTTPException(status_code = 500, detail = "Data for team not found")

    opponent_data, error = await query_db_for_opponent_context_agg(team_input, year_input)
    if error:
        raise HTTPException(status_code = 500, detail = error)
    
    # ~ print("Team Data Got: ")
    # ~ temp = team_data
    # ~ while True:
        # ~ try:
            # ~ print(temp.keys())
            # ~ temp = temp[list(temp.keys())[0]]
        # ~ except:
            # ~ break
            
    # ~ conference_data, error = await query_db_for_conference_context(year_input)    
    # ~ if error:
        # ~ raise HTTPException(status_code = 500, detail = error)
    
    # ~ if len(conference_data.keys()) == 0:
        # ~ raise HTTPException(status_code = 500, detail = "Data for year not found")
    # ~ print("Conf Data Got: ")
    # ~ temp = conference_data
    # ~ while True:
        # ~ try:
            # ~ print(temp.keys())
            # ~ temp = temp[list(temp.keys())[0]]
        # ~ except:
            # ~ break

    
    combined = opponent_data
    combined[team_input] = team_data[team_input]
    # Return the successful response as a single JSON object
    return {
        # ~ "team_data": single_team_data,
        "pre_conference_data": combined
    }
