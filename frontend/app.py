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
    with st.spinner("Connecting to database... Constructing Meet Context..."):
        try:
            athlete_data_string = None
            
            # Create the payload to send to the API
            payload = {
                "year": year_input,
                "season": season_input,
                "team": team_input,
            }
            
            # Make the POST request (non-streaming)
            response = requests.post(DB_URL, json = payload)

            if response.status_code == 200:
                athlete_data_string = response.json()
            else:
                # Show error from the API
                try:
                    api_error_msg = f"Error from API (Status {response.status_code}): {response.json().get('detail')}"
                except:
                    api_error_msg = f"Error from API (Status {response.status_code}): {response.text}"
                st.error(api_error_msg)

        except requests.exceptions.ConnectionError:
            conn_error_msg = (
                "Connection Error: Could not connect to the backend API. "
                f"Please make sure it is running at {API_URL}"
            )
            st.error(conn_error_msg)
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
                    "athlete_data": athlete_data_string #json.dumps(athlete_data_string)
                }
                # Make the POST request (non-streaming)
                response = requests.post(API_URL, json = payload)
                if response.status_code == 200:
                    data = response.json()
                    roster_data = data.get("roster")
                    reasoning_text = data.get("reasoning")
                    
                    # Display reasoning
                    st.subheader("Coach's Reasoning")
                    st.markdown(reasoning_text)
                    
                    # Display roster
                    if roster_data:
                        st.subheader("Suggested Roster")
                        suggested_roster_df = pd.DataFrame(roster_data)
                        st.dataframe(suggested_roster_df)
                    
                else:
                    # Show error from the API
                    try:
                        api_error_msg = f"Error from API (Status {response.status_code}): {response.json().get('detail')}"
                    except:
                        api_error_msg = f"Error from API (Status {response.status_code}): {response.text}"
                    st.error(api_error_msg)

            except requests.exceptions.ConnectionError:
                conn_error_msg = (
                    "Connection Error: Could not connect to the backend API. "
                    f"Please make sure it is running at {API_URL}"
                )
                st.error(conn_error_msg)
            except Exception as e:
                exc_error_msg = f"An unexpected error occurred: {e}"
                st.error(exc_error_msg)
