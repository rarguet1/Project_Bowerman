import streamlit as st
import pandas as pd
import requests
import json 

# --------------------- URL for the local FastAPI backend -------------------- #
API_URL = "http://127.0.0.1:8000/generate_roster"
DB_URL = "http://127.0.0.1:8000/retrieve_context"

# ---------------------------------------------------------------------------- #
#                                     About                                    #
# ---------------------------------------------------------------------------- #
st.set_page_config(page_title="Project Bowerman MVP", layout="wide")

st.title("🏃‍♂️ Project Bowerman")
st.markdown("Using an LLM to generate optimal athlete entries for track and field meets to maximize team performance.")

st.sidebar.header("About")
st.sidebar.info(
    "This application is an prototype for Project Bowerman. "
    "It demonstrates the core concept of providing athlete data and meet context "
    "to an LLM to generate a justified team roster."
)
st.sidebar.warning("Make sure the backend API is running. See `README.md` for instructions.")

# ---------------------------------------------------------------------------- #
#                                 Input Form                                   #
# ---------------------------------------------------------------------------- #

with st.form("roster_form"):

    st.header("Configuration")
    model_provider = st.selectbox("Select AI Model", ["gemini", "openai", "groq"])

    st.header("Input Form")
    st.subheader("Step 1: Choose Scenario")
    
    year_input = st.selectbox('Year', [2021, 2022, 2023, 2024, 2025])  # Removed 2020 b/c Covid
    season_input = st.selectbox('Season', ['Indoor', 'Outdoor'])
    team_input = st.selectbox('Team', ['UMBC', '...'])
    meet_input = st.selectbox('Meet', ["NCAA Division I Mid-Atlantic Region Cross Country Championships", "2025 America East Cross Country Championships", "2025 IC4A/ECAC XC Championship", "Paul Short Run (College)", "Cantello Invitational", "Mount St. Mary's 5k Duals 2025", "NCAA Division I Outdoor Track & Field Championships", "NCAA Division I East First Round", "2025 Outdoor IC4A/ECAC T&F Championships", "2025 America East Outdoor Track & Field Championship", "Penn Relays", "Virginia Challenge", "2025 Annual Legacy Track & Field Meet", "JMU Invitational", "Duke Invitational", "2025 George Mason Dalton Ebanks Invitational ", "Towson Invitational ", "Maryland Invitational", "UCF Black & Gold Challenge", "2025 America East Indoor Championship", "2025 Darius Dixon Memorial Invitational", "Boston University David Hemery Valentine Invitational", "Penn State National Open", "Dr. Sander Scorcher", "Nittany Lion Challenge", "VCU RAMS Indoor Invitational", "Youree Spence Garcia Meet", "NCAA Division I Mid-Atlantic Region Cross Country Championships", "2024 America East Cross Country Championships", "2024 IC4A/ECAC XC Championship", "Lehigh Paul Short Run (College)", "Harry Groves Spiked Shoe Invitational", "Cantello Invitational", "Mount St. Mary's 5k Duals", "NCAA East First Round", "2024 IC4A/ECAC Outdoor T&F Championships", "2024 America East Outdoor Track & Field Championships", "Penn Relays", "2024 Annual Legacy Track & Field Meet", "Virginia Challenge", "James Madison University Invitational", "Bison Outdoor Classic", "2024 George Mason Ebanks Invitational", "2024 Towson Invitational", "Weems Baskin Invitational 24", "2024 Towson Spring Opener", "America East Indoor Track & Field Championships", "2024 Darius Dixon Memorial Invitational", "Sykes & Sabock Challenge", "Penn State National Open"])
    
    st.subheader("Step 2: Describe the Meet Context and Entry Requests")
    alt_meet_context = st.text_area(
        "Provide the strategic context for the meet.",
        height=150,
        placeholder="Example: Conference Championship. We're in a tight points battle with Towson. We need to maximize sprint points...",
        label_visibility="collapsed"
    )

    st.subheader("Step 3: Generate Roster")
    alt_submitted = st.form_submit_button("Generate Roster")

if alt_submitted:
    athlete_data_string = None

    with st.spinner("Connecting to database... Constructing Meet Context..."):
        try:
            payload = {
                "year": year_input,
                "season": season_input,
                "team": team_input,
                "meet": meet_input,
            }
            
            response = requests.post(DB_URL, json=payload)

            if response.status_code == 200:
                raw_data = response.json()
                
                t_count = len(raw_data.get("team_data", {}))
                c_count = len(raw_data.get("conference_data", {}))
                
                # Empty warning
                if t_count == 0 and c_count == 0:
                    st.warning(f" Database returned 0 records.")
                    st.write(f"Year={year_input}, Season={season_input}")
                    st.stop() 
                else:
                    st.success(f"Team Data: {t_count} schools, Conf Data: {c_count} schools.")

                athlete_data_string = json.dumps(raw_data)
            else:
                try:
                    error_detail = response.json().get('detail')
                except:
                    error_detail = response.text
                st.error(f"Database Error (Status {response.status_code}): {error_detail}")

        except requests.exceptions.ConnectionError:
            st.error(f"Connection Error: Could not connect to DB API at {DB_URL}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

    if athlete_data_string and alt_meet_context:
        with st.spinner("Connecting to API... LLM is reasoning and building the roster..."):
            try:
                # Create the payload to send to the API
                payload = {
                    "meet_context": alt_meet_context, 
                    "athlete_data": athlete_data_string,
                    "provider": model_provider
                }
                
                response = requests.post(API_URL, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    roster_data = data.get("roster")
                    reasoning_text = data.get("reasoning")
                    
                    st.subheader("Coach's Reasoning")
                    st.markdown(reasoning_text)
                    
                    if roster_data:
                        st.divider()

                        if isinstance(roster_data, dict):
                            col1, col2, = st.columns(2)

                            with col1:
                                st.subheader("Suggested Men's Roster")
                                men_list = roster_data.get("men", [])
                                if men_list:
                                    st.dataframe(pd.DataFrame(men_list), width='stretch')
                                else:
                                    st.info("No men's entries generated.")

                            with col2:
                                    st.subheader("Suggested Women's Roster")
                                    women_list = roster_data.get("women", [])
                                    if men_list:
                                        st.dataframe(pd.DataFrame(women_list), width='stretch')
                                    else:
                                        st.info("No men's entries generated.")
                    else:
                        st.subheader("Suggested Roster")
                        st.dataframe(pd.DataFrame(roster_data))
                else:
                    try:
                        api_error_msg = f"Error from API (Status {response.status_code}): {response.json().get('detail')}"
                    except:
                        api_error_msg = f"Error from API (Status {response.status_code}): {response.text}"
                    st.error(api_error_msg)

            except requests.exceptions.ConnectionError:
                st.error(f"Connection Error: Is the backend running at {API_URL}?")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")