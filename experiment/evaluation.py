"""
Script to evaluate Roster Generations.
STRATEGY: Name-Based Matching.
"""
import asyncio
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from experiment.utils import get_available_years_teams

load_dotenv()
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# ---------------- CONFIGURATION ---------------- #
TARGET_SUBFOLDER = "gemini-2.0-flash-lite" 
# ----------------------------------------------- #

async def get_id_to_name_map(year: int) -> dict:
    """
    Builds a dictionary mapping { 'ATH_36039': 'Smith, John' }
    derived specifically from the Team Context (what the LLM saw).
    """
    mapping = {}
    try:
        # We use retrieve_team_context because that is the source of the LLM's options
        response = supabase.rpc("retrieve_team_context", {"season_year": year}).execute()
        if response.data:
            for row in response.data:
                if row.get('ath_id') and row.get('ath_name'):
                    norm_id = f"ATH_{int(row['ath_id']):05d}"
                    mapping[norm_id] = row['ath_name']
    except Exception as e:
        print(f"Error building Name Map: {e}")
    return mapping

async def fetch_ground_truth(year: int, team: str, gender: str) -> set:
    """Returns Set[("Smith, John", "100m")] - Using Real Names"""
    entries = set()
    try:
        response = supabase.rpc("retrieve_conference_context", {"season_year": year}).execute()
        if response.data:
            for row in response.data:
                if row["ath_team"] == team and row["ath_gender"] == gender:
                    # Use NAME, not ID
                    if row.get('ath_name'):
                        name = row['ath_name']
                        event = row["event_type"]
                        entries.add((name, event))
    except Exception as e:
        print(f"Error fetching GT: {e}")
    return entries

def load_results(filepath: str, format_type: str, id_map: dict) -> set:
    """Loader that translates IDs -> Names"""
    entries = set()
    if not os.path.exists(filepath): return entries
    
    try:
        df = pd.read_parquet(filepath)
        cols = {c.lower(): c for c in df.columns}

        # --- LOADER FOR GREEDY ---
        if format_type == "greedy":
            for event_col in df.columns:
                for raw_id in df[event_col].dropna():
                    try:
                        clean = str(raw_id).replace("ATH_", "").split(".")[0]
                        formatted_id = f"ATH_{int(clean):05d}"
                        
                        # Translate to Name
                        real_name = id_map.get(formatted_id)
                        if real_name:
                            entries.add((real_name, event_col))
                    except: continue

        # --- LOADER FOR LLM ---
        elif format_type == "llm":
            name_col = cols.get("athlete name") or cols.get("name")
            event_col = cols.get("event(s)") or cols.get("event")
            
            if name_col and event_col:
                for _, row in df.iterrows():
                    raw_str = str(row[name_col])
                    if "ATH_" in raw_str:
                        raw_id = raw_str.split()[0] # "ATH_36039"
                        
                        # Translate to Name
                        real_name = id_map.get(raw_id)
                        if not real_name: 
                            continue # Skip if we can't identify the person
                    else:
                        continue

                    event_raw = row[event_col]
                    events = event_raw if isinstance(event_raw, list) else [e.strip() for e in str(event_raw).split(',')]
                    
                    for e in events:
                        entries.add((real_name, e))
                        
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return entries

async def run_evaluation():
    combinations = await get_available_years_teams()
    
    # Cache maps to prevent spamming DB
    year_maps = {}
    
    results = []
    
    print(f"\nEvaluating against: {TARGET_SUBFOLDER} (NAME MATCHING)")
    print(f"{'Team':<10} {'Year':<6} {'G':<3} {'Model':<10} {'Recall':<6} {'Prec':<6} {'TP/GT'}")
    print("-" * 70)

    for entry in combinations:
        team = entry['school']
        year = int(entry['season_year'])
        
        # Build map for this year if missing
        if year not in year_maps:
            year_maps[year] = await get_id_to_name_map(year)
        
        id_map = year_maps[year]
        
        for gender in ["M", "F"]:
            # 1. Get Ground Truth (NAMES)
            gt_set = await fetch_ground_truth(year, team, gender)
            if not gt_set: continue

            base = "experiment/results"
            paths = [
                ("Greedy", f"{base}/greedy_{team}_{year}_{gender}_results.parquet", "greedy"),
                ("Gemini", f"{base}/{TARGET_SUBFOLDER}/llm_gemini_{team}_{year}_{gender}_results.parquet", "llm")
            ]

            for model, path, fmt in paths:
                # Load Results (Translates IDs -> Names)
                pred_set = load_results(path, fmt, id_map)
                
                if not pred_set: 
                    print("Not found: " + path)
                    continue

                tp = len(gt_set.intersection(pred_set))
                fn = len(gt_set.difference(pred_set))
                fp = len(pred_set.difference(gt_set))
                recall = tp / len(gt_set) if gt_set else 0
                prec = tp / len(pred_set) if pred_set else 0

                print(f"{team:<10} {year:<6} {gender:<3} {model:<10} {recall:.2f}   {prec:.2f}   {tp}/{len(gt_set)}")
                
                results.append({
                    "Team": team, "Year": year, "Gender": gender, "Model": model,
                    "Recall": recall, "Precision": prec, "TP": tp, "FN": fn, "FP": fp, "Total_Actual": len(gt_set), "Total_Pred": len(pred_set)
                })

    if results:
        df_out = pd.DataFrame(results)
        df_out.to_csv(f"experiment/results/{TARGET_SUBFOLDER}_eval.csv", index=False)
        print(f"\n Saved CSV to experiment/results/{TARGET_SUBFOLDER}_eval.csv")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
