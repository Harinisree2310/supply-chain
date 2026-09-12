"""
graph.py
----------
Wires the node functions into the actual loop shown in our diagram.
This is the file that turns six separate functions into one running agent.
"""

from langgraph.graph import StateGraph, END
from state import AgentState
import agent_nodes as nodes


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("monitor_state", nodes.monitor_state)
    graph.add_node("detect_disruption", nodes.detect_disruption)
    graph.add_node("diagnose_and_retrieve", nodes.diagnose_and_retrieve)
    graph.add_node("optimize", nodes.optimize)
    graph.add_node("decide_and_execute", nodes.decide_and_execute)
    graph.add_node("verify", nodes.verify)

    graph.set_entry_point("monitor_state")
    graph.add_edge("monitor_state", "detect_disruption")

    # if no disruption was found, stop this run (in a live system you'd loop
    # back to monitor_state on a timer instead of ending)
    graph.add_conditional_edges(
        "detect_disruption",
        lambda state: "diagnose_and_retrieve" if state["disruption"] else "end",
        {"diagnose_and_retrieve": "diagnose_and_retrieve", "end": END},
    )

    graph.add_edge("diagnose_and_retrieve", "optimize")
    graph.add_edge("optimize", "decide_and_execute")
    graph.add_edge("decide_and_execute", "verify")

    # the feedback loop: blocked -> retry diagnosis, resolved -> back to monitoring
    graph.add_conditional_edges(
        "verify",
        nodes.route_after_verify,
        {
            "diagnose_and_retrieve": "diagnose_and_retrieve",
            "monitor_state": END,  # END here so one call = one full resolution;
                                    # remove this override to loop continuously
        },
    )

    return graph.compile()


def new_state():
    return {
        "disruption": None,
        "candidate_plans": [],
        "valid_plans": [],
        "chosen_plan": None,
        "justification": "",
        "verification_passed": False,
        "blocked_reasons": [],
        "excluded_vendor_ids": [],
        "decision_log": [],
        "status": "monitoring",
    }