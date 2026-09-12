"""
tools.py
----------
These are the DETERMINISTIC functions: plain Python, no AI involved.
The agent calls these to read data and do math. None of these should
ever call the LLM -- keep the "reasoning" and "doing math" layers separate.
"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _load(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r") as f:
        return json.load(f)


def _save(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_products():
    return _load("products.json")


def save_products(products):
    """Writes product data back to disk. Used by scenario.py to inject
    a fresh disruption between demo acts, and by decide_and_execute if
    you choose to persist stock changes (see the NOTE in nodes.py)."""
    _save("products.json", products)


def get_vendors():
    return _load("vendors.json")


def get_routes():
    return _load("routes.json")


def get_shipments():
    return _load("shipments.json")


def save_shipments(shipments):
    """Writes shipment data back to disk -- needed so a resolved shipment
    delay doesn't get re-detected as the same disruption on the next run."""
    _save("shipments.json", shipments)


def get_constraints():
    return _load("constraints.json")


def get_product_by_id(product_id):
    for p in get_products():
        if p["id"] == product_id:
            return p
    return None


def get_vendors_for_product(product_id):
    """Return every vendor that supplies a given product, with that
    vendor's price/capacity info for just that product attached."""
    result = []
    for vendor in get_vendors():
        for entry in vendor["products_supplied"]:
            if entry["product_id"] == product_id:
                result.append({
                    "vendor_id": vendor["id"],
                    "vendor_name": vendor["name"],
                    "location": vendor["location"],
                    "reliability_score": vendor["reliability_score"],
                    "avg_lead_time_days": vendor["avg_lead_time_days"],
                    "carbon_index_per_unit": vendor["carbon_index_per_unit"],
                    "unit_price": entry["unit_price"],
                    "min_order_qty": entry["min_order_qty"],
                    "max_capacity_per_week": entry["max_capacity_per_week"],
                })
    return result


def get_routes_from_location(location):
    return [r for r in get_routes() if r["from_location"] == location]


def find_disrupted_shipments():
    """A 'disruption' in this dataset is any shipment marked delayed,
    or any product whose stock has fallen below its reorder threshold.
    Each disruption gets an 'urgency' score so the caller can prioritize
    the worst problem first instead of picking whichever appears first."""
    disruptions = []

    for s in get_shipments():
        if s["status"] == "delayed":
            # a delayed shipment is already actively causing problems --
            # treat it as high urgency by default, slightly higher if it
            # also affects a product that's already low on stock
            product = get_product_by_id(s["product_id"])
            urgency = 0.85
            if product and product["current_stock"] < product["reorder_threshold"]:
                urgency = 0.95
            disruptions.append({"type": "shipment_delay", "shipment": s, "urgency": round(urgency, 3)})

    for p in get_products():
        if p["current_stock"] < p["reorder_threshold"]:
            # the further below threshold, the more urgent -- a product at
            # 0 stock scores higher than one just barely under the line
            shortfall_ratio = 1 - (p["current_stock"] / p["reorder_threshold"])
            disruptions.append({"type": "low_stock", "product": p, "urgency": round(shortfall_ratio, 3)})

    disruptions.sort(key=lambda d: d["urgency"], reverse=True)
    return disruptions


def build_candidate_plan(product_id, vendor_option, route):
    """Combine a vendor option + a route into one concrete plan with
    computed totals. Quantity defaults to the vendor's minimum order qty."""
    qty = vendor_option["min_order_qty"]
    total_cost = round(qty * (vendor_option["unit_price"] + route["cost_per_unit"]), 2)
    total_carbon = round(qty * (vendor_option["carbon_index_per_unit"] + route["carbon_per_unit"]), 2)
    total_days = vendor_option["avg_lead_time_days"] + route["transit_days"]

    return {
        "product_id": product_id,
        "vendor_id": vendor_option["vendor_id"],
        "vendor_name": vendor_option["vendor_name"],
        "route_id": route["id"],
        "route_mode": route["mode"],
        "quantity": qty,
        "total_cost_usd": total_cost,
        "total_carbon_kg": total_carbon,
        "total_days": total_days,
        "reliability_score": vendor_option["reliability_score"],
    }


def generate_candidate_plans(product_id):
    """For a given product, build one candidate plan per (vendor, route)
    combination available from that vendor's location. This is the
    'diagnose & retrieve options' step's main data-gathering work."""
    plans = []
    for vendor_option in get_vendors_for_product(product_id):
        routes = get_routes_from_location(vendor_option["location"])
        for route in routes:
            plans.append(build_candidate_plan(product_id, vendor_option, route))
    return plans


def check_constraints(plan):
    """Deterministic pass/fail check against constraints.json.
    Returns (True, []) if the plan passes, or (False, [reasons]) if not."""
    c = get_constraints()
    reasons = []

    if plan["total_days"] > c["sla_delivery_days"]:
        reasons.append(f"delivery takes {plan['total_days']}d, SLA is {c['sla_delivery_days']}d")
    if plan["total_cost_usd"] > c["max_budget_per_order_usd"]:
        reasons.append(f"cost ${plan['total_cost_usd']} exceeds budget ${c['max_budget_per_order_usd']}")
    if plan["total_carbon_kg"] > c["max_carbon_per_order_kg"]:
        reasons.append(f"carbon {plan['total_carbon_kg']}kg exceeds cap {c['max_carbon_per_order_kg']}kg")
    if plan["reliability_score"] < c["min_acceptable_reliability_score"]:
        reasons.append(f"vendor reliability {plan['reliability_score']} below minimum {c['min_acceptable_reliability_score']}")

    return (len(reasons) == 0, reasons)


def get_track_record():
    return _load("vendor_track_record.json")


def save_track_record(record):
    path = os.path.join(DATA_DIR, "vendor_track_record.json")
    with open(path, "w") as f:
        json.dump(record, f, indent=2)


def record_vendor_outcome(vendor_id, outcome):
    """outcome is 'blocked' or 'chosen'. Persists across separate runs of
    run_demo.py, so a vendor that failed verification last time still
    carries a small penalty the next time a disruption is being solved."""
    record = get_track_record()
    entry = record["vendors"].setdefault(vendor_id, {"blocked_count": 0, "chosen_count": 0})
    entry[f"{outcome}_count"] = entry.get(f"{outcome}_count", 0) + 1
    save_track_record(record)


def score_plan(plan):
    """Simple weighted score for ranking valid plans -- lower is better.
    Normalizes cost/carbon/days roughly, rewards higher reliability, and
    applies a small penalty for vendors with a history of blocked plans
    (this is the persistent-memory piece -- it looks outside this single
    run at what happened across past disruptions)."""
    cost_score = plan["total_cost_usd"] / 1000
    carbon_score = plan["total_carbon_kg"] / 500
    time_score = plan["total_days"] / 20
    reliability_penalty = (1 - plan["reliability_score"]) * 5

    record = get_track_record()
    history = record["vendors"].get(plan["vendor_id"], {"blocked_count": 0, "chosen_count": 0})
    history_penalty = history.get("blocked_count", 0) * 0.3

    return round(cost_score + carbon_score + time_score + reliability_penalty + history_penalty, 3)