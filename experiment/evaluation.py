"""
Script to evaluate Roster Generations for ALL models found in results folder.
UPDATED: Added F1 Score, Jaccard Index, and Hallucination Rate.
"""
import asyncio
import os
import sys
import glob
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from experiment.utils import get_available_years_teams

load_dotenv()
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# ------------------------------------------------------------------------- #
#                          HELPERS                                          #
# ------------------------------------------------------------------------- #

async def get_id_to_name_map(year: int) -> dict:
    """Builds ID->Name map from Team Context"""
    mapping = {}
    try:
        response = supabase.rpc("retrieve_team_context", {"season_year": year}).execute()
        if response.data:
            for row in response.data:
                if row.get('ath_id') and row.get('ath_name'):
                    norm_id = f"ATH_{int(row['ath_id']):05d}"
                    mapping[norm_id] = row['ath_name']
    except Exception:
        pass
    return mapping

async def fetch_ground_truth(year: int, team: str, gender: str) -> set:
    """Returns Set[("Smith, John", "100m")]"""
    entries = set()
    try:
        response = supabase.rpc("retrieve_conference_context", {"season_year": year}).execute()
        if response.data:
            for row in response.data:
                if row["ath_team"] == team and row["ath_gender"] == gender:
                    if row.get('ath_name'):
                        entries.add((row['ath_name'], row["event_type"]))
    except Exception:
        pass
    return entries

def load_results(filepath: str, format_type: str, id_map: dict) -> tuple[set, int]:
    """Returns: (Set of Valid Entries, Count of Hallucinated IDs)"""
    entries = set()
    hallucinations = 0
    
    if not os.path.exists(filepath):
        return None, 0
    
    try:
        df = pd.read_parquet(filepath)
        cols = {c.lower(): c for c in df.columns}

        if format_type == "greedy":
            for event_col in df.columns:
                for raw_id in df[event_col].dropna():
                    try:
                        clean = str(raw_id).replace("ATH_", "").split(".")[0]
                        formatted_id = f"ATH_{int(clean):05d}"
                        real_name = id_map.get(formatted_id)
                        if real_name: 
                            entries.add((real_name, event_col))
                        else:
                            hallucinations += 1
                    except: continue

        elif format_type == "llm":
            name_col = cols.get("athlete name") or cols.get("name")
            event_col = cols.get("event(s)") or cols.get("event")
            
            if name_col and event_col:
                for _, row in df.iterrows():
                    raw_str = str(row[name_col])
                    if "ATH_" in raw_str:
                        raw_id = raw_str.split()[0]
                        real_name = id_map.get(raw_id)
                        
                        if real_name:
                            event_raw = row[event_col]
                            events = event_raw if isinstance(event_raw, list) else [e.strip() for e in str(event_raw).split(',')]
                            for e in events: entries.add((real_name, e))
                        else:
                            hallucinations += 1
                            
    except Exception: pass
    return entries, hallucinations

# ------------------------------------------------------------------------- #
#                          MAIN LOOP                                        #
# ------------------------------------------------------------------------- #

async def run_evaluation():
    base_dir = "experiment/results"
    model_folders = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and "gemini" in d]
    
    print(f"Found {len(model_folders)} models to evaluate.")
    
    combinations = await get_available_years_teams()
    year_maps = {} 

    for model_name in model_folders:
        print(f"\nEvaluating: {model_name}...")
        results = []
        
        for entry in combinations:
            team = entry['school']
            year = int(entry['season_year'])
            
            if year not in year_maps:
                year_maps[year] = await get_id_to_name_map(year)
            
            for gender in ["M", "F"]:
                gt_set = await fetch_ground_truth(year, team, gender)
                if not gt_set: continue

                llm_path = f"{base_dir}/{model_name}/llm_gemini_{team}_{year}_{gender}_results.parquet"
                greedy_path = f"{base_dir}/{model_name}/greedy_{team}_{year}_{gender}_results.parquet"

                pred_set, ghost_count = load_results(llm_path, "llm", year_maps[year])
                
                if pred_set is None: continue

                # --- 1. Basic Counts ---
                tp = len(gt_set.intersection(pred_set))
                fn = len(gt_set.difference(pred_set))
                fp_valid = len(pred_set.difference(gt_set))
                fp_total = fp_valid + ghost_count
                
                total_actual = len(gt_set)
                total_pred = len(pred_set) + ghost_count

                # --- 2. Standard Metrics ---
                recall = tp / total_actual if total_actual > 0 else 0.0
                precision = tp / total_pred if total_pred > 0 else 0.0

                # --- 3. Advanced Metrics ---
                
                # F1 Score
                f1_score = 0.0
                if (precision + recall) > 0:
                    f1_score = 2 * (precision * recall) / (precision + recall)

                # Jaccard Index (Intersection over Union)
                # Union = TP + FP + FN
                union = tp + fp_total + fn
                jaccard = tp / union if union > 0 else 0.0

                # Hallucination Rate
                # % of predictions that were ghosts
                hallucination_rate = ghost_count / total_pred if total_pred > 0 else 0.0

                print(f"{team:<10} {year:<6} {gender:<3} {model_name:<10} F1:{f1_score:.2f} Jaccard:{jaccard:.2f} Ghosts:{hallucination_rate:.0%}")
                
                results.append({
                    "Team": team, 
                    "Year": year, 
                    "Gender": gender, 
                    "Model": model_name,
                    "Recall": recall, 
                    "Precision": precision, 
                    "F1_Score": f1_score,         
                    "Jaccard_Index": jaccard,      
                    "Hallucination_Rate": hallucination_rate, 
                    "TP": tp, 
                    "FN": fn, 
                    "FP": fp_total, 
                    "Ghosts": ghost_count
                })

        if results:
            df_out = pd.DataFrame(results)
            out_path = f"{base_dir}/{model_name}_eval.csv"
            df_out.to_csv(out_path, index=False)
            print(f"Saved: {out_path} ({len(results)} rows)")

if __name__ == "__main__":
    asyncio.run(run_evaluation())