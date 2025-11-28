"""Script to greedily select roster entries"""
from __future__ import annotations

from utils import (
    save_results,
    retrieve_event_performances,
    get_available_years_teams,
    get_all_events
)

def greedy_selector(
        data: dict,
        k: int
) -> list[str]:
    """Provided some data retrieves the top-k athletes
    
    Notes
    -----
    If k > the number of unique athletes it will however many are available 
    """
    def _parse_time(time: str) -> float:
        """Sometimes perf times are ss.ss sometimes they are mm:ss.ss so this helper is needed..."""
        if ":" not in time:
            return float(time)
        else:
            t = time.split(":")
            mins, secs = float(t[0]), float(t[1])
            return mins*60 + secs
    
    candidates = {}

    for row in data:
        name = row['ath_name']
        time= _parse_time(row['event_time'])
        id = f"{row['ath_id']:05d}"

        if name not in candidates or time <= candidates[name][2]:
            candidates[name] = (id, name, time)

    ret = [row[0] for row in sorted(candidates.values(), key=lambda t: t[2])]
    return ret[:k]


async def build_greedy_roster() -> None:
    """Builds greedy rosters and saves to disk"""
    events = [event['event_type'] for event in await get_all_events()]
    combinations = await get_available_years_teams()

    for entry in combinations:
        mens_results = {}
        womens_results = {}
        
        for event in events:
            performances_m, error = await retrieve_event_performances(
                team=entry['school'], 
                year=int(entry['season_year']),
                event=event,
                gender="M"
            )
            if error:
                print(f"RIP, this broke fix it later...{error}")
                
            performances_f, error = await retrieve_event_performances(
                team=entry['school'], 
                year=int(entry['season_year']),
                event=event,
                gender="F"
            )
            if error:
                print(f"RIP, this broke fix it later...{error}")

            mens_results[event] = greedy_selector(data=performances_m, k=6)
            womens_results[event] = greedy_selector(data=performances_f, k=6)
            
        save_results(
            data=mens_results,
            team=entry['school'],
            year=entry['season_year'],
            prefix='greedy',
            gender="M"
        )
        save_results(
            data=womens_results,
            team=entry['school'],
            year=entry['season_year'],
            prefix='greedy',
            gender="F"
        )

if __name__ == "__main__":
    import asyncio
    # Run the main async function
    asyncio.run(build_greedy_roster())