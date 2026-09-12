"""
scenario.py
-------------
Injects a second, unrelated disruption between demo "acts" so run_demo.py
can show real adaptation to a NEW problem within one continuous run --
this is what the hackathon brief specifically requires you to demonstrate.
"""

import tools


def trigger_low_stock_event(product_id="P006", new_stock=10):
    """Simulates a sudden stock drop on a product NOT already affected by
    the seeded shipment delay, so this is a genuinely separate event."""
    products = tools.get_products()
    changed = False

    for p in products:
        if p["id"] == product_id:
            old_stock = p["current_stock"]
            p["current_stock"] = new_stock
            changed = True
            print(f"[scenario] {p['name']} stock dropped from {old_stock} to {new_stock} "
                  f"(reorder threshold is {p['reorder_threshold']})")

    if not changed:
        print(f"[scenario] WARNING: product {product_id} not found -- nothing changed.")
        return

    tools.save_products(products)