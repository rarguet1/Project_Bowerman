import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types 

# ---------------------------- Load env variables ---------------------------- #
load_dotenv() 
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

try:
    client = genai.Client()
except Exception as e:
    print(f"Error: Could not initialize Gemini client. {e}")
    print("Please make sure 'GEMINI_API_KEY' or 'GOOGLE_API_KEY' is set in your .env file.")
    client = None  

async def generate_roster_strategy(
    athlete_data: dict, 
    meet_context: str, 
    provider: str = "gemini"
) -> (dict, str):
    """
    Dispatcher function to route to the correct LLM provider.
    Returns (roster_dict, reasoning_string)
    """
    if provider == "gemini":
        if client is None: 
            return None, "Error: Gemini client not initialized. Check API key."
        return await _get_gemini_recommendation(athlete_data, meet_context)
    
    elif provider == "placeholder":
        roster, reasoning = _get_placeholder_recommendation()
        return roster, reasoning
    
    else:
        return None, f"Unknown provider: {provider}"

async def _get_gemini_recommendation(athlete_data: dict, meet_context: str) -> (dict, str):
    """
    Generates a roster strategy using Google's Gemini.
    This prompt is now tailored to the "event-first" JSON data.
    """
    response = None
    
    # PROMPT for TFRRS-style data
    system_instruction_text = f"""
    You are "Coach Bowerman," an expert collegiate track and field strategist. 
    Your task is to create an optimal roster to maximize team points for an
    upcoming meet, based on historical athlete data and the meet's context.

    MEET CONTEXT:
    {meet_context}

    ATHLETE DATA:
    The following JSON data provides lists of top performances for your team, organized by EVENT.
    {json.dumps(athlete_data, indent=2)}

    *** YOUR TASK ***
    Analyze the provided athlete JSON data (which is grouped by *event*) and the meet context.
    You are acting as the coach for your collegiate track team. Your job is to enter your athletes in events to maximize team points scored.
    Identify the best combination of athletes per and across events based on speed and possible fatigue after multiple events. 
    Consider everyone's season performances including your athletes and opposing athletes in the conference.
    Note that the same athlete may appear in multiple event lists.
    YOUR OUTPUT MUST BE A SINGLE, VALID JSON OBJECT with TWO keys:

    1.  "reasoning": A markdown-formatted string. Explain your high-level 
        strategy. Justify your decisions, especially for athletes competing in multiple events (max 4).
    2.  "roster": A list of JSON objects. Each object must have keys:
        "Athlete Name", "Event(s)", and "Notes".
        (Use the "text" field from the data for "Athlete Name").

    *** SCORING/RULES ***
    - Scoring: 10-8-6-5-4-3-2-1
    - Max 4 events per athlete 

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
    
    # The user prompt is now just a trigger, since all data is in the system instruction
    user_prompt_content = [
        "Please generate the roster strategy based on the context and data I provided in the system instruction."
    ]

    # This config object requests JSON output
    generation_config = types.GenerateContentConfig(
        system_instruction=system_instruction_text,
        response_mime_type="application/json",
    )
    
    try:
        response = await client.aio.models.generate_content(
            model=MODEL_NAME,        
            contents=user_prompt_content,  
            config=generation_config       
        )
        
        # Parse the JSON response
        data = json.loads(response.text)
        
        # Return the two values
        return data.get("roster"), data.get("reasoning")

    except Exception as e:
        error_msg = f"Error calling Gemini API: {e}\n\nRaw Response: {getattr(response, 'text', 'No response')}"
        print(error_msg)
        return None, error_msg