import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import AsyncOpenAI # NEW IMPORT
from pydantic import BaseModel, Field
from typing import List
from groq import AsyncGroq

# ---------------------------- Load env variables ---------------------------- #
load_dotenv() 
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.2-70b-versatile")

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

# Initialize Groq
try:
    groq_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
except Exception:
    groq_client = None
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
#                             Strategy Dispatcher                              #
# ---------------------------------------------------------------------------- #
async def generate_roster_strategy(
    team: str,
    athlete_data: dict, 
    meet_context: str, 
    provider: str = "gemini",
) -> tuple[dict, str]:
    
    if provider == "gemini":
        if not gemini_client: return None, "Error: Gemini Key missing."
        return await _get_gemini_recommendation(team, athlete_data, meet_context)
    
    elif provider == "openai":
        if not openai_client: return None, "Error: OpenAI Key missing."
        return await _get_openai_recommendation(team, athlete_data, meet_context)
    
    elif provider == "groq": 
        if not groq_client: return None, "Error: Groq Key missing."
        return await _get_groq_recommendation(team, athlete_data, meet_context)
    
    else:
        return None, f"Unknown provider: {provider}"


def _build_system_prompt(team: str, athlete_data: dict, meet_context: str) -> tuple[dict, str]:
    """
    Generates a roster strategy using Google's Gemini.
    This prompt is now tailored to the "event-first" JSON data.
    """    
    conference_data = athlete_data["pre_conference_data"]
    team_context = conference_data.pop(team)
    
    # PROMPT for TFRRS-style data
    return f"""
    You are "Coach Bowerman," an expert collegiate track and field strategist. 
    Your task is to recommend an optimal competition roster to maximize team points for the
    season end conference meet based on historical athlete data for that season so far and the meet's context.

    MEET CONTEXT:
    {meet_context}
    
    TEAM NAME: {team}
    The following JSON data provides lists of all performances for your team.
    {json.dumps(team_context, indent=2)}
    
    CONFERENCE DATA:
    The following JSON data provides lists of all performances for all opponent teams in the conference meet, organized by SCHOOL, GENDER and then EVENT.
    Each EVENT entry contains [TIME, WINDSPEED, PERFORMANCE DATE]
    All athletes that are not in your specified school are competitors.
    {json.dumps(conference_data, indent=2)}

    MEET SCHEDULE:
    OUTDOOR AMERICA EAST TRACK AND FIELD CHAMPIONSHIPS
    SCHEDULE OF EVENTS
    DAY 1

    1:00 p.m 		Women's 1500 Meter 			        Trials
    1:30 p.m. 		Men's 1500 Meter 			        Trials
    2:00 p.m.		Women's 100 Meter Hurdles	        Trials
    2:10 p.m.	  	Men's 110 Meter Hurdles		        Trials
    2:25 p.m. 		Women's 400 Meter 			        Trials
    2:35 p.m. 		Men's 400 Meter		 		        Trials
    2:45 p.m. 		Women's 800 Meter 			        Trials
    2:55 p.m. 		Men's 800 Meter 			        Trials
    3:05 p.m.		Women's 100 Meter 			        Trials
    3:15 p.m.		Men's 100 Meter				        Trials
    3:35 p.m.		Women's 400 Meter Hurdles	        Trials
    3:50 p.m.		Men's 400 Meter Hurdles	            Trials
    4:10 p.m.		Women's 3000 Meter Steeplechase	    Finals
    4:30 p.m.	 	Men's 3000 Meter Steeplechase		Finals
    4:45 p.m.		Women's 200 Meter 			        Trials
    4:55 p.m.		Men's 200 Meter				        Trials
    5:05 p.m.		Women's 10,000 Meter			    Finals
    5:50 p.m.		Men's 10,000 Meter				    Finals


    DAY 2
    11:30 a.m.		Women's 1500 Meter			    Final
    11:45 a.m.		Men's   1500 Meter				Final
    12:00 p.m.		Women's 400 Meter				Final
    12:05 p.m.		Men's	400 Meter				Final
    12:15 p.m.		Women's 100 Meter Hurdles		Final
    12:25 p.m.		Men's	100 Meter Hurdles		Final
    12:35 p.m.		Women's 800 Meter				Final
    12:45 p.m.		Men's	800 Meter				Final
    12:55 p.m.		Women's 100 Meter				Final
    1:00 p.m.		Men's	100 Meter				Final
    1:10 p.m.		Women's 400 Meter Hurdles		Final
    1:20 p.m.		Men's   400 Meter Hurdles		Final
    1:30 p.m.		Women's 200 Meter				Final
    1:35 p.m.		Men's	200 Meter				Final
    1:45 p.m.		Women's 5000 Meter			    Final
    2:05 p.m.		Men's	5000 Meter				Final



    *** YOUR TASK ***
    Analyze the provided athlete JSON data and the meet context.
    You are acting as the coach for your collegiate track team. Your job is to enter your athletes in events to maximize cumulative team points scored.
    Do not consider relays such as the 4x100m or the 4x400m or the 4x800m in your analysis.
    Identify the best combination of athletes per and across events based on speed, possible fatigue after multiple events, and the age and experience level of each athlete(an older athlete may be better equipped to run multiple events as opposed to a younger athlete). 
    Athletes are limited to 4 events during a meet but commonly run multiple events.
    Explicitly consider everyone's season performances including your athletes and opposing athletes in the conference and how they may perform against each other.
    Note that the same athlete may appear in multiple event lists.
    You are able to enter as many athletes in an event as you want but consider that there are costs involved with transporting and housing athletes at the conference meet, so athletes that are extremely unlikely to score points should be left at home.
    YOUR OUTPUT MUST BE A SINGLE, VALID JSON OBJECT with TWO keys:

    1.  "reasoning": A markdown-formatted string. Explain your high-level 
        strategy using conference marks and rankings. Justify your decisions, especially for athletes competing in multiple events (maximum of 4 events per athlete).
    2.  "roster": A list of JSON objects. Each object must have keys:
        "Athlete Name", "Event(s)", and "Notes".
        (Use the "text" field from the data for "Athlete Name").

    *** SCORING/RULES ***
    - Scoring by event placement: 10-8-6-5-4-3-2-1
    
    *** STRICT EXAMPLE OF YOUR FINAL OUTPUT ***
    {{
      "reasoning": "**Strategy Analysis:**\n* Genelle Stephens is a key athlete in both the 200m and 400mh.\n* We have strong depth in the 400m with McDonald, Stephens, and Sibblies.",
      "roster": [
        {{"Athlete Name": "LastName1, FirstName1", "Event(s)": "100m", "Notes": "Top seed, expected 10 points."}},
        {{"Athlete Name": "LastName1, FirstName1", "Event(s)": "200m", "Notes": "Top seed, expected 10 points."}},
        {{"Athlete Name": "LastName2, FirstName2", "Event(s)": "400m", "Notes": "Second best, but entered to prevent fatigue for FirstName1"}},
        {{"Athlete Name": "LastName3, FirstName3", "Event(s)": "200m", "Notes": "Strong second event."}}
      ]
    }}
    """
    
# ---------------------------------------------------------------------------- #
#                             Gemini Implementation                            #
# ---------------------------------------------------------------------------- #
async def _get_gemini_recommendation(team: str, athlete_data: dict, meet_context: str) -> tuple[dict, str]:
    system_instruction_text = _build_system_prompt(team, athlete_data, meet_context)
    
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
async def _get_openai_recommendation(team: str, athlete_data: dict, meet_context: str) -> tuple[dict, str]:
    system_text = _build_system_prompt(team, athlete_data, meet_context)

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
        roster_dict = result.roster.model_dump(by_alias=True) 
        
        return roster_dict, result.reasoning

    except Exception as e:
        return None, f"OpenAI Error: {e}"
    
async def _get_groq_recommendation(team: str, athlete_data: dict, meet_context: str) -> tuple[dict, str]:
    # Build the prompt
    system_text = _build_system_prompt(team, athlete_data, meet_context)
    
    # Llama-3 follows this specific instruction well for JSON
    system_text += "\n\nIMPORTANT: Output ONLY valid JSON matching the schema. No explanations before or after."

    try:
        chat_completion = await groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_text
                },
                {
                    "role": "user",
                    "content": "Generate the roster strategy JSON.",
                }
            ],
            model=GROQ_MODEL,
            
            response_format={"type": "json_object"}, 
            
            temperature=0.1,
        )
        
        # Parse the response
        raw_content = chat_completion.choices[0].message.content
        data = json.loads(raw_content)
        
        return data.get("roster"), data.get("reasoning")

    except Exception as e:
        return None, f"Groq Error: {e}"
