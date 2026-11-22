"""Deterministic mock store database + tool implementations.

Every tool is pure and deterministic, so each task has a verifiable ground truth
and results never depend on live data.
"""
import json
import random
from datetime import date, timedelta

FIRST = ["Aarav", "Maya", "Liam", "Sofia", "Noah", "Isha", "Ethan", "Zara", "Lucas", "Anika"]
LAST = ["Nair", "Patel", "Schmidt", "Garcia", "Tanaka", "Silva", "Brown", "Rossi", "Khan", "Dubois"]
COUNTRIES = ["IN", "US", "DE", "UK", "FR", "JP", "BR"]
TIERS = ["basic", "silver", "gold"]
TIER_DISCOUNT = {"basic": 0, "silver": 5, "gold": 10}

CATALOG = {
    "audio": ["Headphones", "Speaker", "Microphone", "Soundbar", "Earbuds", "Turntable", "Amplifier", "DAC"],
    "kitchen": ["Blender", "Kettle", "Toaster", "Air Fryer", "Rice Cooker", "Grinder", "Mixer", "Juicer"],
    "fitness": ["Yoga Mat", "Dumbbells", "Jump Rope", "Kettlebell", "Resistance Bands", "Foam Roller", "Treadmill Mat", "Pull-up Bar"],
    "office": ["Desk Lamp", "Monitor Stand", "Keyboard", "Mouse", "Notebook", "Webcam", "Chair Cushion", "Docking Station"],
    "toys": ["Puzzle", "Robot Kit", "Board Game", "Drone", "Building Blocks", "Plush Bear", "RC Car", "Science Kit"],
}
WAREHOUSES = ["Kochi", "Pune", "Austin", "Berlin"]


class MockDB:
    def __init__(self, seed=42):
        rng = random.Random(seed)
        self.customers, self.products, self.inventory = {}, {}, {}
        self.orders, self.tickets, self.newsletter = {}, [], {}

        for i in range(1, 31):
            a = (i - 1) % 10
            b = ((i - 1) // 10 + 3 * a) % 10
            first, last = FIRST[a], LAST[b]
            cid = f"C{i:03d}"
            email = f"{first.lower()}.{last.lower()}@example.com"
            self.customers[cid] = {
                "customer_id": cid, "name": f"{first} {last}", "email": email,
                "tier": rng.choice(TIERS), "country": rng.choice(COUNTRIES),
            }
            self.newsletter[email] = rng.random() < 0.5

        prices, n = set(), 101
        for cat, nouns in CATALOG.items():
            for noun in nouns:
                price = round(rng.uniform(8, 300), 2)
                while price in prices:
                    price = round(rng.uniform(8, 300), 2)
                prices.add(price)
                pid = f"P{n}"
                self.products[pid] = {"product_id": pid, "name": noun, "category": cat, "price": price}
                n += 1
        low = set(rng.sample(list(self.products), 8))
        used_stock = set()
        for pid in self.products:
            s = rng.randint(0, 3) if pid in low else rng.randint(8, 150)
            while s in used_stock and pid not in low:
                s = rng.randint(8, 150)
            used_stock.add(s)
            self.inventory[pid] = {"product_id": pid, "stock": s, "warehouse": rng.choice(WAREHOUSES)}

        start, span = date(2026, 8, 1), (date(2026, 11, 15) - date(2026, 8, 1)).days
        for k in range(120):
            oid = f"O{1001 + k}"
            items = []
            for pid in rng.sample(list(self.products), rng.choice([1, 2, 2, 3])):
                items.append({"product_id": pid, "quantity": rng.randint(1, 4),
                              "unit_price": self.products[pid]["price"]})
            total = round(sum(it["quantity"] * it["unit_price"] for it in items), 2)
            self.orders[oid] = {
                "order_id": oid, "customer_id": rng.choice(list(self.customers)),
                "date": (start + timedelta(days=rng.randint(0, span))).isoformat(),
                "status": rng.choices(["delivered", "shipped", "pending", "cancelled"], [45, 20, 20, 15])[0],
                "items": items, "total": total,
            }

        for k in range(45):
            self.tickets.append({
                "ticket_id": f"T{5001 + k}", "customer_id": rng.choice(list(self.customers)),
                "status": rng.choice(["open", "closed"]), "priority": rng.choice(["low", "medium", "high"]),
            })

    # ------------------------------------------------------------------ tools
    def get_order(self, order_id):
        o = self.orders.get(str(order_id).upper())
        return o if o else {"error": f"Order {order_id} not found"}

    def get_customer(self, customer_id):
        c = self.customers.get(str(customer_id).upper())
        return c if c else {"error": f"Customer {customer_id} not found"}

    def find_customer_by_email(self, email):
        for c in self.customers.values():
            if c["email"].lower() == str(email).lower():
                return c
        return {"error": f"No customer with email {email}"}

    def search_orders(self, customer_id=None, status=None, min_total=None, date_from=None, date_to=None):
        out = []
        for o in self.orders.values():
            if customer_id and o["customer_id"] != str(customer_id).upper():
                continue
            if status and o["status"] != status:
                continue
            if min_total is not None and o["total"] < float(min_total):
                continue
            if date_from and o["date"] < date_from:
                continue
            if date_to and o["date"] > date_to:
                continue
            out.append({"order_id": o["order_id"], "customer_id": o["customer_id"],
                        "date": o["date"], "status": o["status"], "total": o["total"]})
        out.sort(key=lambda x: (x["date"], x["order_id"]))
        return {"count": len(out), "orders": out[:50]}

    def get_product(self, product_id):
        p = self.products.get(str(product_id).upper())
        return p if p else {"error": f"Product {product_id} not found"}

    def get_inventory(self, product_id):
        i = self.inventory.get(str(product_id).upper())
        return i if i else {"error": f"Product {product_id} not found"}

    def list_tickets(self, customer_id, status=None):
        cid = str(customer_id).upper()
        if cid not in self.customers:
            return {"error": f"Customer {customer_id} not found"}
        t = [x for x in self.tickets if x["customer_id"] == cid and (not status or x["status"] == status)]
        return {"count": len(t), "tickets": t}

    def get_newsletter_status(self, email):
        key = next((e for e in self.newsletter if e.lower() == str(email).lower()), None)
        if key is None:
            return {"error": f"Email {email} not found"}
        return {"email": key, "subscribed": self.newsletter[key]}

    def get_tier_discount(self, tier):
        t = str(tier).lower()
        if t not in TIER_DISCOUNT:
            return {"error": f"Unknown tier {tier}"}
        return {"tier": t, "discount_percent": TIER_DISCOUNT[t]}

    # ---- ground-truth helpers used by the task generator (not exposed as tools)
    def open_ticket_count(self, cid):
        return sum(1 for t in self.tickets if t["customer_id"] == cid and t["status"] == "open")


def _s(props, req=None):
    return {"type": "object", "properties": props, "required": req or list(props)}


TOOL_SCHEMAS = [
    {"name": "get_order", "description": "Get full details of one order (customer, date, status, line items, total) by order ID like 'O1001'.",
     "input_schema": _s({"order_id": {"type": "string"}})},
    {"name": "get_customer", "description": "Get a customer record (name, email, loyalty tier, country) by customer ID like 'C007'.",
     "input_schema": _s({"customer_id": {"type": "string"}})},
    {"name": "find_customer_by_email", "description": "Find a customer record by exact email address.",
     "input_schema": _s({"email": {"type": "string"}})},
    {"name": "search_orders", "description": "Search orders. All filters optional and combined with AND. Returns order summaries (id, customer, date, status, total) sorted by date. min_total means total >= min_total. Dates are inclusive ISO strings (YYYY-MM-DD).",
     "input_schema": _s({"customer_id": {"type": "string"}, "status": {"type": "string", "enum": ["pending", "shipped", "delivered", "cancelled"]},
                         "min_total": {"type": "number"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}}, req=[])},
    {"name": "get_product", "description": "Get catalog details (name, category, price) for a product ID like 'P105'.",
     "input_schema": _s({"product_id": {"type": "string"}})},
    {"name": "get_inventory", "description": "Get current stock level and warehouse for a product ID.",
     "input_schema": _s({"product_id": {"type": "string"}})},
    {"name": "list_tickets", "description": "List support tickets for a customer ID, optionally filtered by status ('open' or 'closed'). Includes a count.",
     "input_schema": _s({"customer_id": {"type": "string"}, "status": {"type": "string", "enum": ["open", "closed"]}}, req=["customer_id"])},
    {"name": "get_newsletter_status", "description": "Check whether an email address is subscribed to the newsletter.",
     "input_schema": _s({"email": {"type": "string"}})},
    {"name": "get_tier_discount", "description": "Get the discount percentage granted to a loyalty tier ('basic', 'silver', 'gold').",
     "input_schema": _s({"tier": {"type": "string"}})},
]

_TOOL_FUNCS = {s["name"]: s["name"] for s in TOOL_SCHEMAS}


def execute_tool(db, name, args):
    """Returns (result_dict, is_error)."""
    if name not in _TOOL_FUNCS:
        return {"error": f"Unknown tool {name}"}, True
    try:
        res = getattr(db, name)(**(args or {}))
    except TypeError as e:
        res = {"error": f"Invalid arguments: {e}"}
    return res, ("error" in res)
