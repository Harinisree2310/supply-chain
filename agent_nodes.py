"""
nodes.py
----------
Each function here is one box from our architecture diagram.
Purple boxes (diagnose, decide) call the LLM. Teal boxes (optimize, verify)
are pure deterministic code. Test each function alone with a fake state
dict before wiring them into the graph.
"""

import tools
from llm import ask_llm


def monitor_state(state):
    state["decision_log"].append("Monitoring inventory, shipments, and vendor data...")
    state["status"] = "monitoring"
    return state


def detect_disruption(state):
    disruptions = tools.find_disrupted_shipments()
    if not disruptions:
        state["decision_log"].append("No disruption detected. Staying in monitor mode.")
        state["disruption"] = None
        return state

    # disruptions are already sorted worst-first by tools.find_disrupted_shipments
    chosen = disruptions[0]
    state["disruption"] = chosen
    state["status"] = "handling"

    if len(disruptions) > 1:
        state["decision_log"].append(
            f"{len(disruptions)} disruptions detected. Prioritizing "
            f"{chosen['type']} (urgency {chosen['urgency']}) over {len(disruptions) - 1} other(s)."
        )
    else:
        state["decision_log"].append(
            f"Disruption detected: {chosen['type']} (urgency {chosen['urgency']})"
        )
    return state


def diagnose_and_retrieve(state):
    disruption = state["disruption"]

    if disruption["type"] == "shipment_delay":
        product_id = disruption["shipment"]["product_id"]
    else:  # low_stock
        product_id = disruption["product"]["id"]

    plans = tools.generate_candidate_plans(product_id)

    # exclude vendors that were already ruled out in a previous failed attempt
    excluded = state.get("excluded_vendor_ids", [])
    plans = [p for p in plans if p["vendor_id"] not in excluded]

    state["candidate_plans"] = plans
    state["decision_log"].append(
        f"Retrieved {len(plans)} candidate vendor/route combinations for {product_id}."
    )
    return state


def optimize(state):
    valid = []
    reasons_seen = []

    for plan in state["candidate_plans"]:
        passed, reasons = tools.check_constraints(plan)
        if passed:
            plan["score"] = tools.score_plan(plan)
            valid.append(plan)
        else:
            reasons_seen.extend(reasons)

    valid.sort(key=lambda p: p["score"])
    state["valid_plans"] = valid
    state["decision_log"].append(
        f"{len(valid)} of {len(state['candidate_plans'])} plans satisfy all constraints."
    )
    return state


def decide_and_execute(state):
    if not state["valid_plans"]:
        state["decision_log"].append("No valid plans available -- escalating.")
        state["status"] = "blocked"
        return state

    top_plans = state["valid_plans"][:3]
    chosen = top_plans[0]
    rejected = top_plans[1:]

    def describe(plan):
        return (
            f"Vendor {plan['vendor_name']} via {plan['route_mode']} route -- "
            f"cost ${plan['total_cost_usd']}, delivery {plan['total_days']} days, "
            f"carbon {plan['total_carbon_kg']}kg, reliability {plan['reliability_score']}"
        )

    # ask the LLM to justify the choice AND explain why the alternatives lost --
    # this is what lets you answer "why not vendor B?" with the system's own
    # reasoning instead of improvising an answer live in front of judges.
    # Plans are converted to plain sentences (not raw dicts) because small
    # local models parse readable text far more reliably than code structures,
    # and we tell it the exact count so it can't invent extra "rejected" items.
    if rejected:
        rejected_lines = "\n".join(f"- {describe(p)}" for p in rejected)
        prompt = (
            "A supply chain agent must pick the best recovery plan from ranked candidates.\n\n"
            f"CHOSEN option:\n- {describe(chosen)}\n\n"
            f"There are exactly {len(rejected)} REJECTED alternative(s):\n{rejected_lines}\n\n"
            f"In 3-4 sentences: explain why the chosen option is best, citing its "
            f"actual cost, delivery time, and reliability numbers, then explain why "
            f"each of the {len(rejected)} rejected alternative(s) listed above lost out. "
            f"Do not invent any additional options beyond the ones listed."
        )
    else:
        prompt = (
            f"A supply chain agent chose this recovery plan -- it was the only option "
            f"that satisfied all constraints:\n- {describe(chosen)}\n\n"
            "In 2-3 sentences, explain why this plan is acceptable, referencing its "
            "actual cost, delivery time, and reliability numbers."
        )
    justification = ask_llm(prompt)

    state["chosen_plan"] = chosen
    state["justification"] = justification
    state["decision_log"].append(
        f"Selected vendor {chosen['vendor_name']} via {chosen['route_mode']} route. "
        f"Reasoning: {justification.strip()}"
    )

    # "execute" by genuinely persisting the state change to disk -- this was
    # previously mutating a temporary in-memory copy that got discarded,
    # meaning the same disruption would reappear on every future run.
    products = tools.get_products()
    for p in products:
        if p["id"] == chosen["product_id"]:
            p["current_stock"] += chosen["quantity"]
    tools.save_products(products)

    # if this was a shipment delay, mark that specific shipment resolved
    # so it stops being re-detected as an active disruption
    if state["disruption"]["type"] == "shipment_delay":
        shipments = tools.get_shipments()
        shipment_id = state["disruption"]["shipment"]["id"]
        for s in shipments:
            if s["id"] == shipment_id:
                s["status"] = "resolved"
        tools.save_shipments(shipments)

    return state


def verify(state):
    if state["status"] == "blocked":
        return state

    chosen = state["chosen_plan"]
    passed, reasons = tools.check_constraints(chosen)

    state["verification_passed"] = passed
    state["blocked_reasons"] = reasons

    if passed:
        state["status"] = "resolved"
        tools.record_vendor_outcome(chosen["vendor_id"], "chosen")
        state["decision_log"].append("Verification passed. Plan applied successfully.")
    else:
        state["status"] = "blocked"
        tools.record_vendor_outcome(chosen["vendor_id"], "blocked")
        state.setdefault("excluded_vendor_ids", []).append(chosen["vendor_id"])
        state["decision_log"].append(f"Verification failed: {reasons}. Replanning.")

    return state


def route_after_verify(state):
    """Used by the graph to decide which edge to follow after verify()."""
    if state["status"] == "blocked":
        return "diagnose_and_retrieve"
    return "monitor_state"