import streamlit as st
import pandas as pd
import requests
import json 

# streamlit run app.py

# --------------------- URL for the local FastAPI backend -------------------- #
API_URL = "http://127.0.0.1:8000/generate_roster"
DB_URL = "http://127.0.0.1:8000/retrieve_context"

# ---------------------------------------------------------------------------- #
#                                     About                                    #
# ---------------------------------------------------------------------------- #
st.set_page_config(page_title="Project Bowerman MVP", layout="wide")

st.title("🏃‍♂️ Project Bowerman")
st.markdown("Using an LLM to generate optimal athlete entries for track and field conferences to maximize team performance.")

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
    st.header("Team Suggestion Form")
    st.subheader("Step 1: Choose Scenario")
    
    year_input = st.selectbox('Year', [2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023])
    season_input = st.selectbox('Season', ['Outdoor'])
    team_input = st.selectbox('Team', ['Albany', 'UMBC', 'NJIT', 'Binghamton', 'Bryant', 'UML', 'UNH', 'Maine', 'Vermont'])
    
    st.subheader("Step 2: Describe the Meet Context and Entry Requests")
    meet_context = st.text_area(
        "Provide the strategic context for the meet.",
        height=150,
        placeholder="Example: Conference Championship. We're in a tight points battle with Towson. We need to maximize sprint points...",
        label_visibility="collapsed"
    )

    st.subheader("Step 3: Generate Roster")
    submitted = st.form_submit_button("Generate Roster", disabled = False)


if submitted:
    athlete_data_string = None
    with st.spinner("Connecting to database... Constructing Meet Context..."):
        try:
            payload = {
                "year": year_input,
                "season": season_input,
                "team": team_input,
            }
            
            response = requests.post(DB_URL, json=payload)

            if response.status_code == 200:
                raw_data = response.json()

                # athlete_data_string = json.dumps(raw_data)
                athlete_data_string = raw_data
            else:
                try:
                    error_detail = response.json().get('detail')
                except:
                    error_detail = response.text
                st.error(f"Database Error (Status {response.status_code}): {error_detail}")

        except requests.exceptions.ConnectionError:
            st.error(f"Connection Error: Could not connect to DB API at {DB_URL}")
        except Exception as e:
            exc_error_msg = f"An unexpected error occurred: {e}"
            st.error(exc_error_msg)
    # ~ print(athlete_data_string)
    if athlete_data_string and meet_context:
        # Spinner while the API call is made
        with st.spinner("Connecting to API... LLM is reasoning and building the roster..."):
            try:
                # Create the payload to send to the API
                payload = {
                    "team": team_input,
                    "meet_context": meet_context, 
                    "athlete_data": athlete_data_string,
                    "provider": model_provider,
                }
                # Make the POST request (non-streaming)
                response = requests.post(API_URL, json = payload)
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