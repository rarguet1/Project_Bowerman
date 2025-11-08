from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from . import llm_strategy 

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
#                          Backend Logic (Validation)                          #
# ---------------------------------------------------------------------------- #
def process_and_validate_data(athlete_data_text: str) -> (dict, str):
    """
    Tries to parse the JSON string and validate its basic structure.
    This version validates the new "event-first" data structure.
    """
    try:
        data = json.loads(athlete_data_text) 
        
        # Check if it's a dictionary and not empty
        if not isinstance(data, dict) or not data:
            return None, "Invalid JSON: Data must be a non-empty JSON object (e.g., {'100m': [...]})."
        
        # Check if at least one key has a list of performances
        if not any(isinstance(v, list) and len(v) > 0 for v in data.values()):
             return None, "Invalid JSON: Data must contain at least one event (e.g., '100m') with a list of performances."
        return data, None
    except json.JSONDecodeError:
        return None, "Invalid input: Data is not valid JSON. Check your pasted data."
    except Exception as e:
        return None, f"An unexpected error occurred during validation: {e}"

# ---------------------------------------------------------------------------- #
#                                 API Endpoint                                 #
# ---------------------------------------------------------------------------- #
@app.post("/generate_roster")
async def generate_roster_endpoint(request: RosterRequest):
    """
    This endpoint receives meet context and athlete data (as a JSON string),
    validates it, and returns a generated roster with reasoning from an LLM.
    """
    # Validate and parse the input data
    parsed_data, error = process_and_validate_data(request.athlete_data)
    if error:
        raise HTTPException(status_code=400, detail=error)

    # Call the core logic from the strategy module
    roster, reasoning = await llm_strategy.generate_roster_strategy(
        athlete_data=parsed_data,
        meet_context=request.meet_context,
        provider="gemini" 
    )

    # Handle errors from the LLM
    if roster is None:
        raise HTTPException(status_code=500, detail=reasoning)

    # Return the successful response as a single JSON object
    return {
        "roster": roster,
        "reasoning": reasoning
    }