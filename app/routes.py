import os
from flask import Blueprint, request, jsonify
import json, uuid
from functools import wraps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CustomersRecord = os.path.join(BASE_DIR, "customers.json")

TOKEN = os.getenv("TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

customerBp = Blueprint("customer", __name__)

if not os.path.exists(CustomersRecord) or os.path.getsize(CustomersRecord) == 0:
    customers = []
else:
    with open(CustomersRecord) as f:
        customers = json.load(f)


# INFO: --- Auth Decorator ---


def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if auth not in [TOKEN, VERIFY_TOKEN]:
            return jsonify({"Error": "Unauthorized access."}), 401
        return f(*args, **kwargs)

    return decorated


# INFO: --- Routes start here ---


@customerBp.route("/")
@require_token
def helloWorld():
    return jsonify({"Message": "Hello, World!"})


@customerBp.route("/customers", methods=["GET"])
@require_token
def getCustomers():
    with open(CustomersRecord, "r") as f:
        customers = json.load(f)
    return jsonify({"Customers": customers})


@customerBp.route("/customers/<id>", methods=["GET"])
@require_token
def getCustomer(id):
    with open(CustomersRecord, "r") as f:
        customers = json.load(f)
    customer = next((c for c in customers if c["Id"] == id), None)
    return jsonify(customer or {"Error": "Customer not found."})


@customerBp.route("/customers/search", methods=["GET"])
@require_token
def searchCustomer():
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
            fn = name_parts[0] if name_parts else ""
            fn_match = (
                fn == firstName
                if matchMode == "exact"
                else (
                    fn.startswith(firstName)
                    if matchMode == "startswith"
                    else firstName in fn
                )
            )

        if lastName:
            ln = name_parts[1] if len(name_parts) > 1 else ""
            ln_match = (
                ln == lastName
                if matchMode == "exact"
                else (
                    ln.startswith(lastName)
                    if matchMode == "startswith"
                    else lastName in ln
                )
            )

        if fn_match and ln_match:
            matched.append(c)

    if not matched:
        return jsonify({"Message": "No such customer exists."}), 404

    return jsonify({"Matches": matched}), 200


@customerBp.route("/customers/filter-by-gender", methods=["GET"])
@require_token
def filterByGender():
    gender_query = request.args.get("Gender", "").strip().lower()

    if gender_query not in ["male", "female"]:
        return jsonify({"Error": "\"Gender\" must be either 'male' or 'female'"}), 400

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


@customerBp.route("/customers/<string:customerId>", methods=["PUT"])
@require_token
def updateCustomer(customerId):
    data = request.json

    if not os.path.exists(CustomersRecord):
        return jsonify({"Error": "Customer data not found."}), 404
    with open(CustomersRecord, "r") as f:
        try:
            customers = json.load(f)
        except json.JSONDecodeError:
            return jsonify({"Error": "Corrupted data file."}), 500

    updated = False
    for idx, customer in enumerate(customers):
        if customer.get("Id") == customerId:
            customers[idx].update(data)
            updated = True
            break

    if not updated:
        return jsonify({"Error": "Customer not found."}), 404

    with open(CustomersRecord, "w") as f:
        json.dump(customers, f, indent=2)

    return jsonify({"Status": "Updated", "Id": customerId}), 200


@customerBp.route("/customers", methods=["POST"])
@require_token
def addCustomer():
    required_fields = ["Name", "Age", "Gender", "Role"]
    data = request.json

    if not data:
        return jsonify({"Error": "No data sent."}), 400

    missing = [field for field in required_fields if field not in data]
    if missing:
        return jsonify({"Error": f"Missing fields: {', '.join(missing)}."}), 400

    if os.path.exists(CustomersRecord) and os.path.getsize(CustomersRecord) > 0:
        with open(CustomersRecord, "r") as f:
            try:
                customers = json.load(f)
            except json.JSONDecodeError:
                customers = []
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

    return jsonify({"Status": "Added", "Customer": newCustomer}), 201


@customerBp.route("/customers/bulk", methods=["POST"])
@require_token
def addBulkCustomers():
    data = request.json

    if not isinstance(data, list):
        return jsonify({"Error": "Expected a list of customers."}), 400

    newCustomers = []
    for entry in data:
        if not all(k in entry for k in ["Name", "Age", "Gender", "Role"]):
            return (
                jsonify({"Error": "Each customer must have Name, Age, Gender, Role."}),
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
        try:
            with open(CustomersRecord, "r") as f:
                customers = json.load(f)
        except json.JSONDecodeError:
            customers = []
    else:
        customers = []

    customers.extend(newCustomers)

    with open(CustomersRecord, "w") as f:
        json.dump(customers, f, indent=2)

    return (
        jsonify(
            {
                "Status": "Customer bulk added",
                "Count": len(newCustomers),
                "Customers": newCustomers,
            }
        ),
        201,
    )


@customerBp.route("/customers/<string:customerId>", methods=["DELETE"])
@require_token
def deleteCustomer(customerId):
    if os.path.exists(CustomersRecord) and os.path.getsize(CustomersRecord) > 0:
        with open(CustomersRecord, "r") as f:
            customers = json.load(f)
    else:
        return jsonify({"Error": "No customer data found."}), 404

    updated_customers = [c for c in customers if c["Id"] != customerId]

    if len(updated_customers) == len(customers):
        return jsonify({"Error": "Customer not found."}), 404

    with open(CustomersRecord, "w") as f:
        json.dump(updated_customers, f, indent=2)

    return jsonify({"Status": "Deleted", "Id": customerId}), 200


# INFO: --- Updated Webhook Handler ---


@customerBp.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403

    elif request.method == "POST":
        data = request.json

        print("Received POST webhook:", data)

        try:
            message_body = data["entry"][0]["changes"][0]["value"]["messages"][0][
                "text"
            ]["body"]
            print("Message received:", message_body)
        except (KeyError, IndexError, TypeError):
            print("No message body found.")

        return "EVENT_RECEIVED", 200
