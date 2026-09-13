"""
demo_static.py
----------------
A standalone, DEPLOYABLE viewer for real AutoChain runs.

This intentionally does NOT import tools.py, graph.py, or ollama --
it only reads demo_logs.json (a copy of real run output) and displays it.
This is what makes it deployable to free hosting like Streamlit Community
Cloud: it needs no local LLM, no LangGraph, nothing beyond streamlit itself.

The full live agent (run_demo.py / app.py in the parent folder) is what
actually reasons in real time and requires Ollama running locally --
see the main README for why that can't be hosted the same way.

Run locally with:
    streamlit run demo_static.py

Deploy by pointing Streamlit Community Cloud at this file specifically
(not app.py), in a repo/folder that only needs streamlit installed.
"""

import json
import os
import streamlit as st

st.set_page_config(page_title="AutoChain — Real Run Results", layout="wide")

st.title("🔗 AutoChain — Real Run Results")
st.caption(
    "This is a read-only viewer of real, previously-executed agent runs. "
    "The full live agent runs locally with a local LLM (no external APIs) — "
    "see the GitHub README to run it yourself with `python run_demo.py`."
)

LOG_PATH = os.path.join(os.path.dirname(__file__), "demo_logs.json")

if not os.path.exists(LOG_PATH):
    st.warning("No run logs found yet. Run `python run_demo.py` locally, then copy "
               "data/demo_logs.json into this folder as demo_logs.json.")
    st.stop()

with open(LOG_PATH, "r") as f:
    logs = json.load(f)

if not logs:
    st.info("The log file is empty -- run the local agent at least once to populate it.")
    st.stop()

st.write(f"Showing **{len(logs)}** real recorded run(s).")

for entry in reversed(logs):
    header = f"{entry.get('label', 'Run')} — {entry.get('status', 'unknown')}"
    if entry.get("timestamp"):
        header += f"  ·  {entry['timestamp']}"

    with st.expander(header, expanded=True):
        st.write("**Decision log:**")
        for line in entry.get("decision_log", []):
            st.write("•", line)

        if entry.get("chosen_plan"):
            st.write("**Chosen plan:**")
            st.json(entry["chosen_plan"])

        if entry.get("justification"):
            st.write("**Justification:**")
            st.write(entry["justification"])