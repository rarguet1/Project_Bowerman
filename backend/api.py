from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import time

# ---------------------------------------------------------------------------- #
#                                Pydantic Model                                #
# ---------------------------------------------------------------------------- #
class RosterRequest(BaseModel):
    meet_context: str
    athlete_data: str
# ---------------------------------------------------------------------------- #
#                                   Init API                                   #
# ---------------------------------------------------------------------------- #
app = FastAPI(
    title="Project Bowerman API",
    description="API for generating optimal track rosters using LLM logic."
)
# ---------------------------------------------------------------------------- #
#                          Backend Logic (Placeholder)                         #
# ---------------------------------------------------------------------------- #
def process_and_validate_data(athlete_data_text: str) -> bool:
    """
    Placeholder to process the raw text data.
    """
    if athlete_data_text and len(athlete_data_text) > 5:
        return True
    return False

def generate_roster_logic(athlete_data: str, meet_context: str) -> (dict, str):
    """
    Placeholder for the core LLM call.
    This function takes the processed data and context,
    sends to the LLM, and gets the results.
    """
    # Simulate a delay
    time.sleep(2) 
    
    # Dummy response for MVP
    suggested_roster = {
        'Athlete ID': ['ATH-001', 'ATH-002', 'ATH-001', 'ATH-003'],
        'Event': ['100m Dash', 'Javelin Throw', '4x100m Relay', '1500m Run'],
        'Predicted Points': [10, 8, 6, 5]
    }
    # Convert DataFrame to a dict (JSON serializable)
    roster_dict = pd.DataFrame(suggested_roster).to_dict(orient='records')

    reasoning = """
    **Reasoning for Roster Decisions (from API):**

    1.  **ATH-001 in 100m Dash:** Based on historical times, ATH-001 is the fastest sprinter on the team and is projected to win the event, securing a maximum of 10 points.
    2.  **ATH-002 in Javelin Throw:** This athlete shows strong, consistent performance in Javelin, with a high probability of placing second against the known competitors.
    3.  **ATH-001 in 4x100m Relay:** Placing our top sprinter as the anchor leg in the relay maximizes our chances for a top-three finish, considering the speed of the other teams.
    4.  **ATH-003 in 1500m Run:** While not the top seed, historical data suggests ATH-003 has strong endurance and can likely secure a 4th place finish, adding crucial points.
    """
    return roster_dict, reasoning

# ---------------------------------------------------------------------------- #
#                                 API Endpoint                                 #
# ---------------------------------------------------------------------------- #
@app.post("/generate_roster")
async def generate_roster_endpoint(request: RosterRequest):
    """
    This endpoint receives meet context and athlete data,
    validates it, and returns a generated roster with reasoning.
    """
    # Validate input
    is_valid = process_and_validate_data(request.athlete_data)
    if not is_valid:
        return {"error": "Invalid athlete data. Please provide more data."}, 400

    # Call the core logic
    roster, reasoning = generate_roster_logic(request.athlete_data, request.meet_context)

    # Return the successful response
    return {
        "roster": roster,
        "reasoning": reasoning
    }