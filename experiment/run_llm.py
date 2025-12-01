"""
Script to run LLM Roster Generation experiments.
STRATEGY: Full Context (No Filtering). Relying on LLM intelligence.
INCLUDES: Resume Logic (Skips already processed teams).
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Add parent directory to path to find 'backend' folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from backend
from backend import llm_strategy
from experiment.utils import save_results, get_available_years_teams

# ---------------------------- Configuration ---------------------------- #
load_dotenv()
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# Determine Provider & Model from Env
PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")

if PROVIDER == "openai":
    current_model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    DELAY_BETWEEN_CALLS = 1 # 1s is polite
    MAX_REQUESTS_PER_RUN = 1000
    
elif PROVIDER == "gemini":
    current_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    HIGH_SPEED_MODELS = ["gemini-2.0-flash", "gemini-2.0_flash-lite", "gemini-2.5-flash-lite", "gemini-2.5-flash"]
    if current_model in HIGH_SPEED_MODELS:
        DELAY_BETWEEN_CALLS = 0
        MAX_REQUESTS_PER_RUN = 1000
    else:
        DELAY_BETWEEN_CALLS = 3
        MAX_REQUESTS_PER_RUN = 100

# Folder Name is just the model name
RESULTS_SUBFOLDER = current_model

# Define High Speed Models
HIGH_SPEED_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash", 
]

# Set Speed/Limits
if current_model in HIGH_SPEED_MODELS:
    print(f"Model {current_model} detected as High Speed / Tier 1.")
    DELAY_BETWEEN_CALLS = 0
    MAX_REQUESTS_PER_RUN = 1000
else:
    print(f"Model {current_model} not in high-speed list. Defaulting to Safe Mode.")
    DELAY_BETWEEN_CALLS = 3     
    MAX_REQUESTS_PER_RUN = 100    

RESULTS_SUBFOLDER = current_model 

MEET_CONTEXT_TEMPLATE = (
    "You are the head track and field coach of {team} and it is time for the "
    "America East Track and Field Conference Championships. Enter your athletes "
    "in each event in a way that maximizes points scored against the rest of "
    "the teams in the conference."
)

# ---------------------------- Data Fetching ---------------------------- #
async def fetch_team_context(year: int) -> dict:
    """
    Fetches context from DB.
    NO FILTERING: Retrieves all available data for the season.
    The LLM must discern its own team from opponents.
    """
    ret = {}
    try:
        # We do NOT pass 'target_team' here, so we get the full dataset
        response = supabase.rpc("retrieve_team_context", {"season_year": year}).execute()
        
        if response.data:
            for row in response.data:
                school = row["ath_team"]
                gender = row["ath_gender"]
                event = row["event_type"]
                stats = row["event_time"], row['event_wind'], row['event_date']
                ath_year = row['ath_year']
                name = f"ATH_{row['ath_id']:05d}"
                
                # Convert tuple key to string for JSON compatibility
                key = f"{name} ({ath_year})" 
                
                if school not in ret: ret[school] = {}
                if gender not in ret[school]: ret[school][gender] = {}
                if event not in ret[school][gender]: ret[school][gender][event] = {}
                
                if key not in ret[school][gender][event]:
                    ret[school][gender][event][key] = [stats]
                else:
                    ret[school][gender][event][key].append(stats)
    except Exception as e:
        print(f"DB Error: {e}")
    return ret

# ---------------------------- Main Loop ---------------------------- #
async def run_llm_experiment(provider="gemini"):
    print(f"Starting Experiment with {provider} using model {current_model}")
    print(f"Settings: Delay={DELAY_BETWEEN_CALLS}s, Max Requests={MAX_REQUESTS_PER_RUN}")
    print(f"Resume Mode: ON (Checking {RESULTS_SUBFOLDER})")
    print(f"Strategy: UNFILTERED (Sending full context to LLM)")
    print("-" * 50)
    
    combinations = await get_available_years_teams()
    if not combinations:
        print("No teams/years found in DB.")
        return

    request_count = 0
    total = len(combinations)

    for i, entry in enumerate(combinations):
        if request_count >= MAX_REQUESTS_PER_RUN:
            print(f"Reached safety limit of {MAX_REQUESTS_PER_RUN} requests. Stopping.")
            break

        team = entry['school']
        year = int(entry['season_year'])
        
        # ---------------- RESUME LOGIC ---------------- #
        # Check if the reasoning file already exists in the model's subfolder
        base_dir = Path(__file__).resolve().parent / "results"
        check_path = base_dir / RESULTS_SUBFOLDER / f"llm_{provider}_{team}_{year}_reasoning.txt"
        
        if check_path.exists():
            print(f"[{i+1}/{total}] Skipping {team} - {year} (Already done)")
            continue
        # ---------------------------------------------- #
        
        print(f"[{i+1}/{total}] Processing: {team} - {year}...", end=" ", flush=True)

        full_team_data = await fetch_team_context(year)
            
        athlete_data_payload = {"pre_conference_data": full_team_data}
        dynamic_meet_context = MEET_CONTEXT_TEMPLATE.format(team=team)

        # Retry Loop
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                roster, reasoning = await llm_strategy.generate_roster_strategy(
                    team=team,
                    athlete_data=athlete_data_payload,
                    meet_context=dynamic_meet_context,
                    provider=provider
                )

                if roster:
                    # Define save directory
                    save_dir = base_dir / RESULTS_SUBFOLDER
                    save_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Normalize keys
                    roster_keys = {k.lower(): v for k, v in roster.items()}

                    # Save Men
                    if "men" in roster_keys:
                        save_results(roster_keys["men"], team, year, f"llm_{provider}", "M", subfolder=RESULTS_SUBFOLDER)
                    # Save Women
                    if "women" in roster_keys:
                        save_results(roster_keys["women"], team, year, f"llm_{provider}", "F", subfolder=RESULTS_SUBFOLDER)
                    
                    # Save Reasoning Text
                    txt_filename = f"llm_{provider}_{team}_{year}_reasoning.txt"
                    with open(save_dir / txt_filename, "w") as f:
                        f.write(reasoning)
                    
                    print("Done")
                    request_count += 1
                    break 
                else:
                    print(f"Failed (No Roster Returned): {reasoning}")
                    break 

            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "resource exhausted" in error_msg:
                    wait_time = 60 * (attempt + 1)
                    print(f"\nHit Rate Limit. Sleeping {wait_time}s before retry {attempt+1}/{max_retries}...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"Error: {e}")
                    break 

        if DELAY_BETWEEN_CALLS > 0:
            await asyncio.sleep(DELAY_BETWEEN_CALLS)

if __name__ == "__main__":
    selected_provider = os.environ.get("LLM_PROVIDER", "gemini")
    asyncio.run(run_llm_experiment(provider=selected_provider))