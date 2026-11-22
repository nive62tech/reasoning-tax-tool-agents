"""Generates the 60 benchmark tasks (20 per complexity tier) with ground truth
computed directly from the mock database. Deterministic given the seed."""
import json
import random
from collections import defaultdict

from mockdb import MockDB, TIER_DISCOUNT


def build_tasks(db: MockDB, seed: int = 7):
    rng = random.Random(seed)
    tasks = []
    counters = defaultdict(int)

    def pick(cands, n, key=None):
        cands = list(cands)
        rng.shuffle(cands)
        if key is None:
            return cands[:n]
        groups = defaultdict(list)
        for c in cands:
            groups[key(c)].append(c)
        keys, out, i = list(groups), [], 0
        while len(out) < n and any(groups.values()):
            k = keys[i % len(keys)]
            if groups[k]:
                out.append(groups[k].pop())
            i += 1
        return out

    def add(tier, template, prompt, atype, expected, calls):
        counters[tier] += 1
        tasks.append({
            "id": f"t{tier}_{counters[tier]:02d}", "tier": tier, "template": template,
            "prompt": prompt, "answer_type": atype, "expected": expected,
            "reference_calls": calls, "n_ref_calls": len(calls),
            "required_tools": sorted({c[0] for c in calls}),
        })

    oids, cids, pids = list(db.orders), list(db.customers), list(db.products)
    yn = lambda b: "yes" if b else "no"
    first_pid = lambda o: db.orders[o]["items"][0]["product_id"]

    # =========================== TIER 1: single lookup ======================
    for o in rng.sample(oids, 2):
        add(1, "order_status", f"What is the current status of order {o}?", "str",
            db.orders[o]["status"], [("get_order", {"order_id": o})])
    for o in rng.sample(oids, 2):
        add(1, "order_total", f"What is the total amount of order {o}?", "num",
            db.orders[o]["total"], [("get_order", {"order_id": o})])
    for c in rng.sample(cids, 2):
        add(1, "customer_email", f"What is the email address of customer {c}?", "str",
            db.customers[c]["email"], [("get_customer", {"customer_id": c})])
    for p in rng.sample(pids, 2):
        add(1, "product_price", f"What is the catalog price of product {p}?", "num",
            db.products[p]["price"], [("get_product", {"product_id": p})])
    for p in rng.sample(pids, 2):
        add(1, "stock", f"How many units of product {p} are currently in stock?", "num",
            db.inventory[p]["stock"], [("get_inventory", {"product_id": p})])
    for c in rng.sample(cids, 2):
        add(1, "customer_tier", f"Which loyalty tier is customer {c} in?", "str",
            db.customers[c]["tier"], [("get_customer", {"customer_id": c})])
    for c in rng.sample([c for c in cids if db.open_ticket_count(c) >= 1], 2):
        add(1, "open_tickets", f"How many open support tickets does customer {c} have?", "num",
            db.open_ticket_count(c), [("list_tickets", {"customer_id": c, "status": "open"})])
    for c in pick(cids, 2, key=lambda c: db.newsletter[db.customers[c]["email"]]):
        e = db.customers[c]["email"]
        add(1, "newsletter", f"Is {e} subscribed to the newsletter? Answer yes or no.", "bool",
            yn(db.newsletter[e]), [("get_newsletter_status", {"email": e})])
    for t in ["silver", "gold"]:
        add(1, "tier_discount", f"What discount percentage does the {t} loyalty tier receive?", "num",
            TIER_DISCOUNT[t], [("get_tier_discount", {"tier": t})])
    for o in ["O9041", "O9127"]:
        assert o not in db.orders
        add(1, "not_found", f"What is the current status of order {o}?", "str",
            "NOT_FOUND", [("get_order", {"order_id": o})])

    # =========================== TIER 2: two dependent steps =================
    def cust_of(o): return db.customers[db.orders[o]["customer_id"]]

    for t in pick([(o,) for o in oids], 40, key=lambda x: db.newsletter[cust_of(x[0])["email"]])[:2]:
        o = t[0]; c = cust_of(o)
        add(2, "order_newsletter", f"Is the customer who placed order {o} subscribed to the newsletter? Answer yes or no.", "bool",
            yn(db.newsletter[c["email"]]),
            [("get_order", {"order_id": o}), ("get_customer", {"customer_id": c["customer_id"]}),
             ("get_newsletter_status", {"email": c["email"]})])
    for o in rng.sample(oids, 2):
        c = cust_of(o)
        add(2, "order_customer_name", f"What is the full name of the customer who placed order {o}?", "str", c["name"],
            [("get_order", {"order_id": o}), ("get_customer", {"customer_id": c["customer_id"]})])
    for o in rng.sample(oids, 2):
        p = first_pid(o)
        add(2, "order_first_item_name", f"What is the product name of the first line item in order {o}?", "str",
            db.products[p]["name"], [("get_order", {"order_id": o}), ("get_product", {"product_id": p})])
    for c in rng.sample([c for c in cids if db.open_ticket_count(c) >= 1], 2):
        e = db.customers[c]["email"]
        add(2, "email_open_tickets", f"How many open support tickets does the customer with email {e} have?", "num",
            db.open_ticket_count(c),
            [("find_customer_by_email", {"email": e}), ("list_tickets", {"customer_id": c, "status": "open"})])
    for o in rng.sample(oids, 2):
        p = first_pid(o)
        add(2, "order_first_item_stock", f"How many units are currently in stock of the first line item in order {o}?", "num",
            db.inventory[p]["stock"], [("get_order", {"order_id": o}), ("get_inventory", {"product_id": p})])
    for c in pick(cids, 2, key=lambda c: db.customers[c]["tier"]):
        t = db.customers[c]["tier"]
        add(2, "customer_discount", f"What discount percentage applies to customer {c} based on their loyalty tier?", "num",
            TIER_DISCOUNT[t], [("get_customer", {"customer_id": c}), ("get_tier_discount", {"tier": t})])
    for o in rng.sample(oids, 2):
        c = cust_of(o)
        add(2, "order_country", f"Which country is the customer who placed order {o} based in? Use the 2-letter code.", "str",
            c["country"], [("get_order", {"order_id": o}), ("get_customer", {"customer_id": c["customer_id"]})])
    for o in rng.sample(oids, 2):
        p = first_pid(o)
        add(2, "order_first_item_category", f"What product category does the first line item in order {o} belong to?", "str",
            db.products[p]["category"], [("get_order", {"order_id": o}), ("get_product", {"product_id": p})])
    for o in rng.sample([o for o in oids if db.open_ticket_count(db.orders[o]["customer_id"]) >= 1], 2):
        c = db.orders[o]["customer_id"]
        add(2, "order_buyer_tickets", f"How many open support tickets does the customer who placed order {o} have?", "num",
            db.open_ticket_count(c),
            [("get_order", {"order_id": o}), ("list_tickets", {"customer_id": c, "status": "open"})])
    for o in ["O9310", "O9555"]:
        assert o not in db.orders
        add(2, "not_found_chain", f"Is the customer who placed order {o} subscribed to the newsletter? Answer yes or no, or NOT_FOUND if the order does not exist.", "str",
            "NOT_FOUND", [("get_order", {"order_id": o})])

    # =========================== TIER 3: multi-tool chains ===================
    # A) discounted order total
    cands = []
    for o in oids:
        c = cust_of(o)
        pct = TIER_DISCOUNT[c["tier"]]
        if pct > 0:
            cands.append((o, c, pct))
    for o, c, pct in pick(cands, 4, key=lambda x: x[2]):
        ans = round(db.orders[o]["total"] * (1 - pct / 100), 2)
        add(3, "discounted_total", f"Apply the buyer's loyalty-tier discount to the total of order {o}. What is the discounted total, rounded to 2 decimals?", "num",
            ans, [("get_order", {"order_id": o}), ("get_customer", {"customer_id": c["customer_id"]}),
                  ("get_tier_discount", {"tier": c["tier"]})])

    # B) can the order be fulfilled from inventory
    cands = []
    for o in oids:
        its = db.orders[o]["items"]
        if len(its) >= 2:
            ok = all(db.inventory[i["product_id"]]["stock"] >= i["quantity"] for i in its)
            cands.append((o, ok))
    for o, ok in pick(cands, 4, key=lambda x: x[1]):
        its = db.orders[o]["items"]
        add(3, "fulfillable", f"Can order {o} be fully fulfilled from current inventory (every line item's quantity is at most the current stock of that product)? Answer yes or no.", "bool",
            yn(ok), [("get_order", {"order_id": o})] + [("get_inventory", {"product_id": i["product_id"]}) for i in its])

    # C) big orders in a month -> which customers have open tickets
    cands = []
    for (a, b) in [("2026-09-01", "2026-09-30"), ("2026-10-01", "2026-10-31"), ("2026-08-01", "2026-08-31")]:
        for thr in [900, 1000, 1100, 1200, 1300, 1400, 1500]:
            os_ = [o for o in db.orders.values() if a <= o["date"] <= b and o["total"] >= thr]
            cs = sorted({o["customer_id"] for o in os_})
            hits = sorted(c for c in cs if db.open_ticket_count(c) >= 1)
            if 3 <= len(cs) <= 8 and hits:
                cands.append((a, b, thr, cs, hits))
    for a, b, thr, cs, hits in pick(cands, 4):
        add(3, "big_orders_open_tickets",
            f"Consider all orders (any status) dated from {a} to {b} inclusive with a total of at least {thr}. Which of the customers who placed those orders currently have at least one open support ticket? List their customer IDs, comma-separated.",
            "set", hits,
            [("search_orders", {"date_from": a, "date_to": b, "min_total": thr})] +
            [("list_tickets", {"customer_id": c, "status": "open"}) for c in cs])

    # D) lowest-stock product across a customer's non-cancelled orders
    cands = []
    for c in cids:
        os_ = [o for o in db.orders.values() if o["customer_id"] == c and o["status"] != "cancelled"]
        prods = sorted({i["product_id"] for o in os_ for i in o["items"]})
        if len(os_) >= 2 and 3 <= len(prods) <= 7:
            stocks = sorted((db.inventory[p]["stock"], p) for p in prods)
            if stocks[0][0] != stocks[1][0]:
                cands.append((c, os_, prods, stocks[0][1]))
    for c, os_, prods, low in pick(cands, 4):
        add(3, "lowest_stock_across_orders",
            f"Look at all non-cancelled orders placed by customer {c}. Across every line item in those orders, which product ID currently has the lowest stock? Answer with the product ID only.",
            "str", low,
            [("search_orders", {"customer_id": c})] +
            [("get_order", {"order_id": o["order_id"]}) for o in os_] +
            [("get_inventory", {"product_id": p}) for p in prods])

    # E) upgrade eligibility rule
    def eligible(c):
        tier = db.customers[c]["tier"]
        spend = sum(o["total"] for o in db.orders.values() if o["customer_id"] == c and o["status"] != "cancelled")
        opn = db.open_ticket_count(c)
        if tier == "basic":
            return spend > 250 and opn <= 1
        if tier == "silver":
            return spend > 600 and opn == 0
        return False
    cands = [(c, eligible(c)) for c in cids]
    for c, ok in pick(cands, 4, key=lambda x: x[1]):
        add(3, "upgrade_eligibility",
            f"Is customer {c} eligible for a loyalty-tier upgrade right now? Rules: a basic customer needs more than 250 total spend on non-cancelled orders and at most 1 open support ticket; a silver customer needs more than 600 total spend on non-cancelled orders and zero open tickets; a gold customer is already at the top tier and is not eligible. Answer yes or no.",
            "bool", yn(ok),
            [("get_customer", {"customer_id": c}), ("search_orders", {"customer_id": c}),
             ("list_tickets", {"customer_id": c, "status": "open"})])

    return tasks


def get_tasks():
    return build_tasks(MockDB())


if __name__ == "__main__":
    ts = get_tasks()
    with open("tasks.json", "w") as f:
        json.dump(ts, f, indent=1)
    from collections import Counter
    print(len(ts), "tasks;", dict(Counter(t["tier"] for t in ts)))
    print("bool balance:", Counter(t["expected"] for t in ts if t["answer_type"] == "bool"))
