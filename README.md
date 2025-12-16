# Project Bowerman: Streamlit + FastAPI MVP
# 🏃‍♂️ Project Bowerman: Optimal Athlete Entry Predictor
This project explores the reasoning capabilities of large language models to generate strategies for assigning athletes to track events to maximize team performance. It investigates whether language models can perform the required reasoning tasks, such as planning and optimization, using natural language and historic information as input.

This project is structured as follows:
```
├── backend/
│   ├── api.py
│   └── llm_strategy.py
├── data/
│   ├── ingest.py
│   ├── nomalize.py
│   ├── auto_ingest.sh
│   ├── db_scripts/
│   │       ├── ingest.sql
│   │       ├── retrievals.sql
│   │       ├── tables.sql
│   │       └── drop_tables.sql
├── experiment/
|   ├── results/
│   ├── utils.py
│   ├── greedy.py
│   ├── run_llm.py
│   └── evaluation.py
├── frontend/
│   └── app.py
├── images/
├── uv.lock
├── pyproject.toml
├── .gitignore
├── README.md
└── LICENSE
```
### Directory Descriptions
- `frontend/app.py` The Streamlit frontend.
- `backend/` The FastAPI backend (which contains the LLM logic and data api).
- `data/` This directory contains the logic for the database and bulk ingestion
- `experiment/` This directory contains the experiment logic. 
    - To get the results for greedy baseline run `python experiment/greedy.py`. 
    - To run the LLM experiments you can use the example command for gemini-2.0-flash below:
    `LLM_PROVIDER=gemini GEMINI_MODEL=gemini-2.0-flash nohup python -u experiment/run_llm.py > gemini-2.0-flash.log 2>&1 &`
    - To get an evaluation results please run `python experiment/evaluation.py`

You must run both services simultaneously in separate terminal windows for the application to work.

## 1. Installation
This project uses uv for dependency management, as defined in pyproject.toml.
First, ensure you have uv installed. If not, you can install it with:

``pip install uv``

Then, sync the project dependencies:

``uv sync``

## 2. Run the Backend (API)
Open your first terminal window and run the FastAPI server using uv run:

``uv run uvicorn backend.api:app --reload``

- api: This tells uvicorn to look for the ``api.py`` file inside the backend directory (as a Python module).
- app: This refers to the app = FastAPI() object inside ``backend/api.py``.
- --reload: This makes the server automatically restart if you make changes to ``backend/api.py``.

You should see output indicating the server is running, typically at http://127.0.0.1:8000.

## 3. Run the Frontend (Streamlit)
Open a second terminal window. Run the Streamlit app using uv run:

``uv run streamlit run frontend/app.py``

This will automatically open the Streamlit application in your web browser.

## 4. How to Use
- With both services running, open the Streamlit app in your browser.
- Paste your historical athlete data into the "Step 1" text area.
- Type your meet context (e.g., "Conference finals vs Team A") into the chat input at the bottom of the page and press Enter.
- The Streamlit app will send this data to your local FastAPI backend, wait for the response, and then display the results.

## 5. Screenshots
# Data input
Input data is gratiously provided UMBC_f_performances.json.
![alt text](./images/image.png)
# Example context input
![alt text](./images/image-1.png)
# Reasoning output example
![alt text](./images/image-2.png)
# Roster output example
![alt text](./images/image-3.png)