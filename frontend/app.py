import streamlit as st
import pandas as pd
import requests


# ---------------------------------------------------------------------------- #
#                                 Stream Lit UI                                #
# ---------------------------------------------------------------------------- #

# --------------------- URL for the local FastAPI backend -------------------- #
API_URL = "http://127.0.0.1:8000/generate_roster"

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
#                                Main Data Input                               #
# ---------------------------------------------------------------------------- #
st.header("Step 1: Provide Historical Athlete Data")
athlete_data = st.text_area(
    "Paste historical performance data for your team (e.g., from TFRRS).",
    height=200,
    placeholder="Example: ATH-001, 100m, 10.54s\nATH-002, Javelin, 65.2m\n...",
    label_visibility="collapsed"
)
# ---------------------------------------------------------------------------- #
#                          Chat Interface (No History)                         #
# ---------------------------------------------------------------------------- #
st.header("Step 2: Generate Roster via Chat")

# ---------------- Chat Input ---------------- #
query = st.chat_input(placeholder="Describe the meet context (e.g., 'Conference finals vs Team A')")

if query:
    # Display the user's query
    with st.chat_message("user"):
        st.markdown(query)

    # Basic frontend validation
    if not athlete_data or len(athlete_data) < 6:
        error_msg = "Please paste your historical athlete data in the text area above before generating a roster."
        # Display the error in an assistant message
        with st.chat_message("assistant"):
            st.error(error_msg)
    else:
        # Display a spinner while API is called
        with st.chat_message("assistant"):
            with st.spinner("Connecting to API... LLM is reasoning and building the roster..."):
                try:
                    # Create the payload to send to the API
                    payload = {
                        "meet_context": query,  # The chat query is the meet context
                        "athlete_data": athlete_data
                    }
                    
                    # Make the POST request
                    response = requests.post(API_URL, json=payload)

                    if response.status_code == 200:
                        # --- 4. Display Outputs ---
                        data = response.json()
                        roster_data = data.get("roster")
                        reasoning_text = data.get("reasoning")
                        
                        # Display reasoning and roster
                        st.markdown(reasoning_text)
                        if roster_data:
                            suggested_roster_df = pd.DataFrame(roster_data)
                            st.dataframe(suggested_roster_df)
                        
                    else:
                        # Show error from the API
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

# To run this app:
# 1. Make sure the API is running (see api.py)
# 2. Run in your terminal: streamlit run app.py

