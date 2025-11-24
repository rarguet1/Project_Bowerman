import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import AsyncOpenAI # NEW IMPORT
from pydantic import BaseModel, Field
from typing import List

# ---------------------------- Load env variables ---------------------------- #
load_dotenv() 
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# Initialize Gemini
try:
    gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
except Exception:
    gemini_client = None

# Initialize OpenAI
try:
    openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except Exception:
    openai_client = None

# ---------------------------------------------------------------------------- #
#                           Strict Output Schemas                              #
# ---------------------------------------------------------------------------- #
class AthleteEntry(BaseModel):
    name: str = Field(alias="Athlete Name", description="Name of the athlete")
    events: str = Field(alias="Event(s)", description="The specific event(s) entered")
    notes: str = Field(alias="Notes", description="Brief strategic note")

class RosterSplit(BaseModel):
    men: List[AthleteEntry]
    women: List[AthleteEntry]

class CoachResponse(BaseModel):
    reasoning: str = Field(description="Markdown formatted strategic reasoning")
    roster: RosterSplit

# ---------------------------------------------------------------------------- #
#                             Shared Prompt Logic                              #
# ---------------------------------------------------------------------------- #
def _build_system_prompt(meet_context: str, athlete_data: dict) -> str:
    return f"""
    You are "Coach Bowerman," an expert collegiate track and field strategist. 
    Your task is to create an optimal roster to maximize team points for an
    upcoming meet.

    MEET CONTEXT:
    {meet_context}

    DATA PROVIDED:
    The JSON data below contains two keys:
    1. "team_data": Your team's historical performances.
    2. "conference_data": Top performances from opposing teams.

    {json.dumps(athlete_data, indent=2)}

    *** YOUR TASK ***
    Analyze the "team_data" to find your best athletes. Compare them against the "conference_data".
    IMPORTANT: You must create separate strategies for the MEN'S team and the WOMEN'S team.
    
    Identify the best combination of athletes per and across events based on speed and possible fatigue. 
    Max 4 events per athlete.
    """

# ---------------------------------------------------------------------------- #
#                             Strategy Dispatcher                              #
# ---------------------------------------------------------------------------- #
async def generate_roster_strategy(
    athlete_data: dict, 
    meet_context: str, 
    provider: str = "gemini"
) -> tuple[dict, str]:
    
    if provider == "gemini":
        if not gemini_client: return None, "Error: Gemini Key missing."
        return await _get_gemini_recommendation(athlete_data, meet_context)
    
    elif provider == "openai":
        if not openai_client: return None, "Error: OpenAI Key missing."
        return await _get_openai_recommendation(athlete_data, meet_context)
    
    else:
        return None, f"Unknown provider: {provider}"

# ---------------------------------------------------------------------------- #
#                             Gemini Implementation                            #
# ---------------------------------------------------------------------------- #
async def _get_gemini_recommendation(athlete_data: dict, meet_context: str) -> tuple[dict, str]:
    system_instruction_text = _build_system_prompt(meet_context, athlete_data)
    
    generation_config = types.GenerateContentConfig(
        system_instruction=system_instruction_text,
        response_mime_type="application/json",
        response_schema=CoachResponse 
    )
    
    try:
        response = await gemini_client.aio.models.generate_content(
            model=GEMINI_MODEL,        
            contents=["Generate roster strategy."],  
            config=generation_config       
        )
        data = json.loads(response.text)
        return data.get("roster"), data.get("reasoning")

    except Exception as e:
        return None, f"Gemini Error: {e}"

# ---------------------------------------------------------------------------- #
#                             OpenAI Implementation                            #
# ---------------------------------------------------------------------------- #
async def _get_openai_recommendation(athlete_data: dict, meet_context: str) -> tuple[dict, str]:
    system_text = _build_system_prompt(meet_context, athlete_data)

    try:
        completion = await openai_client.beta.chat.completions.parse(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_text},
                {"role": "user", "content": "Generate roster strategy."},
            ],
            response_format=CoachResponse, # Enforce Schema
        )
        
        # Extract the parsed Pydantic object
        result: CoachResponse = completion.choices[0].message.parsed
        
        # Convert back to dict format for the frontend
        # .model_dump(by_alias=True) ensures "Athlete Name" keeps its space
        roster_dict = result.roster.model_dump(by_alias=True) 
        
        return roster_dict, result.reasoning

    except Exception as e:
        return None, f"OpenAI Error: {e}"