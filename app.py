"""
app.py
--------
Minimal Streamlit dashboard. Run with:
    streamlit run app.py

This wraps the exact same graph.py / run_demo.py logic in clickable buttons
instead of a terminal script -- no new agent logic lives here.
"""

import streamlit as st
import pandas as pd

from graph import build_graph, new_state
import tools
import scenario

st.set_page_config(page_title="Supply Chain Recovery Agent", layout="wide")
st.title("🔗 Autonomous Supply Chain Recovery Agent")
st.caption("Runs entirely locally — no external APIs, no internet dependency.")

# Build the graph once and keep it across reruns (Streamlit reruns the whole
# script on every button click, so this avoids rebuilding it every time)
if "app" not in st.session_state:
    st.session_state.app = build_graph()
if "history" not in st.session_state:
    st.session_state.history = []  # list of (label, final_state) tuples


def run_agent(label):
    final_state = st.session_state.app.invoke(new_state())
    st.session_state.history.append((label, final_state))


col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Current state")
    products_df = pd.DataFrame(tools.get_products())
    products_df["below_threshold"] = products_df["current_stock"] < products_df["reorder_threshold"]
    st.dataframe(
        products_df[["id", "name", "current_stock", "reorder_threshold", "below_threshold"]],
        use_container_width=True,
        hide_index=True,
    )

    shipments_df = pd.DataFrame(tools.get_shipments())
    st.write("Shipments")
    st.dataframe(shipments_df[["id", "product_id", "status"]], use_container_width=True, hide_index=True)

with col2:
    st.subheader("Controls")

    if st.button("▶ Run agent (resolve current top disruption)", type="primary"):
        run_agent(f"Run {len(st.session_state.history) + 1}")

    st.divider()
    st.write("Inject a new disruption to test adaptation:")
    product_options = {p["id"]: p["name"] for p in tools.get_products()}
    selected_product = st.selectbox("Product", options=list(product_options.keys()),
                                     format_func=lambda pid: f"{pid} — {product_options[pid]}")
    new_stock_value = st.number_input("New stock level", min_value=0, value=10)

    if st.button("⚠ Inject disruption"):
        scenario.trigger_low_stock_event(product_id=selected_product, new_stock=new_stock_value)
        st.success(f"Stock for {product_options[selected_product]} set to {new_stock_value}")

st.divider()
st.subheader("Run history")

if not st.session_state.history:
    st.info("No runs yet — click 'Run agent' to resolve the current top disruption.")

for label, final_state in reversed(st.session_state.history):
    with st.expander(f"{label} — status: {final_state['status']}", expanded=True):
        for line in final_state["decision_log"]:
            st.write("•", line)

        if final_state.get("chosen_plan"):
            st.write("**Chosen plan:**")
            st.json(final_state["chosen_plan"])

        if final_state.get("justification"):
            st.write("**Justification:**")
            st.write(final_state["justification"].strip())