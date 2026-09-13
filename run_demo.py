"""
run_demo.py
-------------
Two-act demo, run entirely in one script execution. Also logs each run's
results to data/demo_logs.json, which powers the deployable static viewer
(demo_static.py) -- so anyone can browse real past runs online without
installing Ollama.

Usage:
    python run_demo.py
"""

import datetime
from graph import build_graph, new_state
import scenario
import tools


def print_result(final_state, label):
    print(f"\n--- {label}: decision log ---")
    for line in final_state["decision_log"]:
        print(" -", line)

    print(f"\n--- {label}: final status: {final_state['status']} ---")
    if final_state.get("chosen_plan"):
        print("Chosen plan:", final_state["chosen_plan"])
    if final_state.get("justification"):
        print("\nJustification:", final_state["justification"].strip())

    tools.append_demo_log({
        "label": label,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "decision_log": final_state["decision_log"],
        "status": final_state["status"],
        "chosen_plan": final_state.get("chosen_plan"),
        "justification": final_state.get("justification", "").strip(),
    })


def main():
    app = build_graph()

    print("=" * 60)
    print("ACT 1: Handling the initial disruption")
    print("=" * 60)
    final1 = app.invoke(new_state())
    print_result(final1, "ACT 1")

    print("\n" + "=" * 60)
    print("Injecting a second, unrelated disruption...")
    print("=" * 60)
    scenario.trigger_low_stock_event(product_id="P006", new_stock=10)

    print("\n" + "=" * 60)
    print("ACT 2: Agent reacts to the new disruption")
    print("=" * 60)
    final2 = app.invoke(new_state())
    print_result(final2, "ACT 2")


if __name__ == "__main__":
    main()