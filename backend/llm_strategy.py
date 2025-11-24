import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types 
from pydantic import BaseModel, Field
from typing import List

# ---------------------------- Load env variables ---------------------------- #
load_dotenv() 
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

try:
    client = genai.Client()
except Exception as e:
    print(f"Error: Could not initialize Gemini client. {e}")
    client = None

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
#                             Strategy Logic                                   #
# ---------------------------------------------------------------------------- #

async def generate_roster_strategy(
    athlete_data: dict, 
    meet_context: str, 
    provider: str = "gemini"
) -> tuple[dict, str]:
    """
    Dispatcher function to route to the correct LLM provider.
    Returns (roster_dict, reasoning_string)
    """
    if provider == "gemini":
        if client is None: 
            return None, "Error: Gemini client not initialized. Check API key."
        return await _get_gemini_recommendation(athlete_data, meet_context)
    
    elif provider == "placeholder":
        return [], "Placeholder"
    
    else:
        return None, f"Unknown provider: {provider}"

async def _get_gemini_recommendation(athlete_data: dict, meet_context: str) -> (dict, str):
    """
    Generates a roster strategy using Google's Gemini.
    This prompt is now tailored to the "event-first" JSON data.
    """
    response = None
    
    system_instruction_text = f"""
    You are "Coach Bowerman," an expert collegiate track and field strategist. 
    Your task is to create an optimal roster to maximize team points for an
    upcoming meet, based on historical athlete data and the meet's context.

    MEET CONTEXT:
    {meet_context}

    DATA PROVIDED:
    The JSON data below contains two keys:
    1. "team_data": Your team's historical performances. Structure: School -> Gender -> Event -> Athlete -> [Performances].
    2. "conference_data": Top performances from opposing teams in the conference.
    {json.dumps(athlete_data, indent=2)}

    *** YOUR TASK ***
    Analyze the "team_data" to find your best athletes.
    You are acting as the coach for your collegiate track team. Your job is to enter your athletes in events to maximize team points scored.
    Identify the best combination of athletes per and across events based on speed and possible fatigue after multiple events. 
    Consider everyone's season performances including your athletes and opposing athletes in the conference.
    Note that the same athlete may appear in multiple event lists.

    YOUR OUTPUT MUST BE A SINGLE, VALID JSON OBJECT with TWO keys:
    1.  "reasoning": A markdown-formatted string. Explain your strategy for both genders.
    2.  "roster": A JSON Object containing two keys: "men" and "women".
        - "men": A list of objects {{"Athlete Name": "...", "Event(s)": "...", "Notes": "..."}}
        - "women": A list of objects {{"Athlete Name": "...", "Event(s)": "...", "Notes": "..."}}

    *** SCORING/RULES ***
    - Scoring: 10-8-6-5-4-3-2-1
    - Max 4 events per athlete 

    *** STRICT EXAMPLE OF YOUR FINAL OUTPUT ***
    {{
      "reasoning": "**Strategy Analysis:**\\n* Genelle Stephens is a key athlete in both the 200m and 400mh.\\n* We have strong depth in the 400m with McDonald, Stephens, and Sibblies.",
      "roster": {{
        "men": [
           {{"Athlete Name": "LastName1, FirstName1", "Event(s)": "100m", "Notes": "Top seed, expected 10 points."}},
           {{"Athlete Name": "LastName1, FirstName1", "Event(s)": "200m", "Notes": "Top seed, expected 10 points."}}
        ],
        "women": [
           {{"Athlete Name": "LastName2, FirstName2", "Event(s)": "400m", "Notes": "Second best, but entered to prevent fatigue."}},
           {{"Athlete Name": "LastName3, FirstName3", "Event(s)": "200m", "Notes": "Strong second event."}}
        ]
      }}
    }}
    """
    
    user_prompt_content = [
        "Please generate the roster strategy based on the context and data I provided in the system instruction."
    ]

    generation_config = types.GenerateContentConfig(
        system_instruction=system_instruction_text,
        response_mime_type="application/json",
        response_schema=CoachResponse,
    )
    
    try:
        response = await client.aio.models.generate_content(
            model=MODEL_NAME,        
            contents=user_prompt_content,  
            config=generation_config       
        )
        
        data = json.loads(response.text)
        return data.get("roster"), data.get("reasoning")

    except Exception as e:
        error_msg = f"Error calling Gemini API: {e}\n\nRaw Response: {getattr(response, 'text', 'No response')}"
        print(error_msg)
        return None, error_msg