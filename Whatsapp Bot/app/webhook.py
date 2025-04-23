from flask import Blueprint, request, jsonify
import json
import os

webhookBp = Blueprint("webhook", __name__)
CustomersRecord = "app/customers.json"


@webhookBp.route("/webhook", methods=["POST"])
def handle_webhook():
    payload = request.json
    userMessage = payload.get("message", "").strip().lower()

    # Response builder
    def reply(msg):
        return jsonify({"reply": msg})

    # Basic greetings
    if userMessage in ["hi", "Hi", "hello", "Hello", "hey", "Hey"]:
        return reply("Hey! 👋 Need help managing customers? Just tell me what to do!")

    # Get all customers
    if "show all" in userMessage or "list customers" in userMessage:
        if os.path.exists(CustomersRecord):
            with open(CustomersRecord) as f:
                customers = json.load(f)
            if customers:
                names = [c["Name"] for c in customers]
                return reply(f"Here are your customers: {', '.join(names)}")
            else:
                return reply("No customers found.")
        else:
            return reply("Customer database not found.")

    # Search by name
    if "search" in userMessage:
        name = userMessage.replace("search", "").strip()
        if not name:
            return reply("Tell me the name you want to search for.")
        with open(CustomersRecord, "r") as f:
            customers = json.load(f)
        matches = [c for c in customers if name.lower() in c["Name"].lower()]
        if matches:
            return reply(f"Found: {', '.join([c['Name'] for c in matches])}")
        else:
            return reply("No such customer exists.")

    # Stats
    if "stats" in userMessage or "summary" in userMessage:
        with open(CustomersRecord) as f:
            customers = json.load(f)
        total = len(customers)
        avg_age = sum(int(c["Age"]) for c in customers) / total if total else 0
        return reply(f"Total: {total}, Avg Age: {avg_age:.1f}")

    # Default fallback
    return reply(
        "Sorry, I didn't get that. Try saying something like 'List customers', 'Search John', or 'Show stats'."
    )
