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


with st.form("roster_form)alt"):
    st.header("Alt. Form Structure")
    st.subheader("Step 1: Choose Scenario")
    
    year_input = st.selectbox('Year', [2020, 2021, 2022, 2023, 2024, 2025])
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
    alt_submitted = st.form_submit_button("Generate Roster (Non-Functional)", disabled = True)

with st.form("roster_form"):
    st.header("Step 1: Provide Historical Athlete Data")
    uploaded_file = st.file_uploader(
        "Upload your athlete JSON file.",
        type=["json"],
        label_visibility="collapsed"
    )

    st.header("Step 2: Describe the Meet Context")
    meet_context = st.text_area(
        "Provide the strategic context for the meet.",
        height=150,
        placeholder="Example: Conference Championship. We're in a tight points battle with Towson. We need to maximize sprint points...",
        label_visibility="collapsed"
    )

    st.header("Step 3: Generate Roster")
    submitted = st.form_submit_button("Generate Roster")

if submitted:

    athlete_data_string = None

    if uploaded_file is None:
        st.error("Please upload your JSON athlete data file in Step 1.")
    elif not meet_context or len(meet_context) < 10:
        st.error("Please describe the meet context in Step 2.")
    else:
        try:
            # Read the file's content as a string
            athlete_data_string = uploaded_file.getvalue().decode("utf-8")
        except Exception as e:
            st.error(f"Error reading file: {e}")

    if athlete_data_string and meet_context:
        # Spinner while the API call is made
        with st.spinner("Connecting to API... LLM is reasoning and building the roster..."):
            try:
                # Create the payload to send to the API
                payload = {
                    "meet_context": meet_context, 
                    "athlete_data": athlete_data_string
                }
                
                # Make the POST request (non-streaming)
                response = requests.post(API_URL, json=payload)

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



if alt_submitted:
    with st.spinner("Connecting to database... Constructing Meet Context..."):
        try:
            athlete_data_string = None
            
            # Create the payload to send to the API
            payload = {
                "year": year_input,
                "season": season_input,
                "team": team_input,
                "meet": meet_input,
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
    
    if athlete_data_string and meet_context and False:
        # Spinner while the API call is made
        with st.spinner("Connecting to API... LLM is reasoning and building the roster..."):
            try:
                # Create the payload to send to the API
                payload = {
                    "meet_context": meet_context, 
                    "athlete_data": athlete_data_string
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
