import os
from flask import Blueprint, request, jsonify
import json, uuid

CustomersRecord = "app/customers.json"
customerBp = Blueprint("customer", __name__)

if not os.path.exists(CustomersRecord) or os.path.getsize(CustomersRecord) == 0:
    customers = []
else:
    with open(CustomersRecord) as f:
        customers = json.load(f)


# INFO: Welcome Message
@customerBp.route("/")
def hello_world():
    return jsonify({"Message": "Hello, World!"})


# INFO: List all Customers
@customerBp.route("/customers", methods=["GET"])
def get_customers():
    return jsonify({"Customers": customers})


# INFO: Get a specific Customer by ID
@customerBp.route("/customers/<id>", methods=["GET"])
def get_customer(id):
    customer = next((c for c in customers if c["Id"] == id), None)
    return jsonify(customer or {"Error": "Customer not found ..."})


# INFO: Search for customers by Name
@customerBp.route("/customers/search", methods=["GET"])
def search_customer():
    firstName = request.args.get("FirstName", "").strip().lower()
    lastName = request.args.get("LastName", "").strip().lower()
    matchMode = request.args.get("mode", "contains").lower()

    if not firstName and not lastName:
        return jsonify({"Error": 'Provide at least "FirstName" or "LastName"'}), 400

    with open(CustomersRecord, "r") as f:
        customers = json.load(f)

    matched = []

    for c in customers:
        full_name = c["Name"].strip().lower()
        name_parts = full_name.split()

        fn_match = ln_match = True

        if firstName:
            fn = name_parts[0] if len(name_parts) > 0 else ""
            if matchMode == "exact":
                fn_match = fn == firstName
            elif matchMode == "startswith":
                fn_match = fn.startswith(firstName)
            else:
                fn_match = firstName in fn

        if lastName:
            ln = name_parts[1] if len(name_parts) > 1 else ""
            if matchMode == "exact":
                ln_match = ln == lastName
            elif matchMode == "startswith":
                ln_match = ln.startswith(lastName)
            else:
                ln_match = lastName in ln

        if fn_match and ln_match:
            matched.append(c)

    if not matched:
        return jsonify({"Message": "No such customer exists..."}), 404

    return jsonify({"Matches": matched}), 200


# INFO: Get Customer by Gender
@customerBp.route("/customers/filter-by-gender", methods=["GET"])
def filter_by_gender():
    gender_query = request.args.get("Gender", "").strip().lower()

    if gender_query not in ["male", "female"]:
        return jsonify({"error": "\"Gender\" must be either 'male' or 'female'"}), 400

    with open(CustomersRecord, "r") as f:
        customers = json.load(f)

    filtered = [c for c in customers if c["Gender"].lower() == gender_query]

    return (
        jsonify(
            {
                "Gender": gender_query.title(),
                "Count": len(filtered),
                "Matches": filtered,
            }
        ),
        200,
    )


# INFO: Update a Customer
@customerBp.route("/customers/<string:customer_id>", methods=["PUT"])
def update_customer(customer_id):
    data = request.json

    if not os.path.exists(CustomersRecord):
        return jsonify({"Error": "Customer data not found ..."}), 404
    with open(CustomersRecord, "r") as f:
        try:
            customers = json.load(f)
        except json.JSONDecodeError:
            return jsonify({"Error": "Corrupted data file."}), 500

    updated = False

    for idx, customer in enumerate(customers):
        if customer.get("Id") == customer_id:
            customers[idx].update(data)
            updated = True
            break

    if not updated:
        return jsonify({"Error": "Customer not found ..."}), 404

    with open(CustomersRecord, "w") as f:
        json.dump(customers, f, indent=2)

    return jsonify({"Status": "Updated", "Id": customer_id}), 200


# INFO: Add a new Customer
@customerBp.route("/customers", methods=["POST"])
def add_customer():
    required_fields = ["Name", "Age", "Gender", "Role"]
    data = request.json

    if not data:
        return jsonify({"Error": "No data sent ..."}), 400

    missing = [field for field in required_fields if field not in data]
    if missing:
        return jsonify({"Error": f"Missing fields: {', '.join(missing)} ..."}), 400

    if os.path.exists(CustomersRecord) and os.path.getsize(CustomersRecord) > 0:
        with open(CustomersRecord, "r") as f:
            customers = json.load(f)
    else:
        customers = []

    newCustomer = {
        "Id": str(uuid.uuid4()),
        "Name": data["Name"],
        "Age": data["Age"],
        "Gender": data["Gender"],
        "Role": data["Role"],
    }

    customers.append(newCustomer)

    with open(CustomersRecord, "w") as f:
        json.dump(customers, f, indent=2)

    return (
        jsonify({"Status": "Added", "Customer": newCustomer}),
        201,
    )


# INFO: Bulk Add Customers
@customerBp.route("/customers/bulk", methods=["POST"])
def add_bulk_customers():
    data = request.json

    if not isinstance(data, list):
        return jsonify({"Error": "Expected a list of customers ..."}), 400

    newCustomers = []
    for entry in data:
        if not all(k in entry for k in ["Name", "Age", "Gender", "Role"]):
            return (
                jsonify(
                    {"Error": "Each customer must have a Name, Age, Gender, and Role"}
                ),
                400,
            )

        customer = {
            "Id": str(uuid.uuid4()),
            "Name": entry["Name"],
            "Age": entry["Age"],
            "Gender": entry["Gender"],
            "Role": entry["Role"],
        }
        newCustomers.append(customer)

    if os.path.exists(CustomersRecord) and os.path.getsize(CustomersRecord) > 0:
        with open(CustomersRecord, "r") as f:
            customers = json.load(f)
    else:
        customers = []

    customers.extend(newCustomers)

    with open(CustomersRecord, "w") as f:
        json.dump(customers, f, indent=2)

    return (
        jsonify(
            {
                "Status": " Customer bulk added",
                "Count": len(newCustomers),
                "Customers": newCustomers,
            }
        ),
        201,
    )


# INFO: Delete a Customer
@customerBp.route("/customers/<string:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    if os.path.exists(CustomersRecord) and os.path.getsize(CustomersRecord) > 0:
        with open(CustomersRecord, "r") as f:
            customers = json.load(f)
    else:
        return jsonify({"Error": "No customer data found ..."}), 404

    updated_customers = [c for c in customers if c["Id"] != customer_id]

    if len(updated_customers) == len(customers):
        return jsonify({"Error": "Customer not found ..."}), 404

    with open(CustomersRecord, "w") as f:
        json.dump(updated_customers, f, indent=2)

    return jsonify({"Status": "Deleted", "Id": customer_id}), 200


# INFO: Botpress Webhook
@customerBp.route("/webhook", methods=["POST"])
def bot_webhook():
    data = request.json
    print("Incoming from Botpress:", data)

    reply = {
        "type": "text",
        "text": "Hey! Got your message: " + data.get("text", "No text found."),
    }

    return jsonify(reply), 200
