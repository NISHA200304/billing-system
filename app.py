from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import requests
from config import FIREBASE_WEB_API_KEY
import base64
import json
import os

# ======================
# FLASK INIT
# ======================
app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# ======================
# FIREBASE ADMIN INIT (RENDER SAFE)
# ======================
if not firebase_admin._apps:
    firebase_key_base64 = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

    if not firebase_key_base64:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT env variable not set")

    firebase_key_json = base64.b64decode(firebase_key_base64).decode("utf-8")
    firebase_dict = json.loads(firebase_key_json)

    # 🔥 IMPORTANT FIX (THIS WAS THE BUG)
    firebase_dict["private_key"] = firebase_dict["private_key"].replace("\\n", "\n")

    cred = credentials.Certificate(firebase_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ======================
# LOGIN ROUTE
# ======================
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }

            response = requests.post(url, json=payload, timeout=10)
            data = response.json()

            if "error" in data:
                return render_template("login.html", error="Invalid email or password")

            uid = data["localId"]

            user_doc = db.collection("users").document(uid).get()
            if not user_doc.exists:
                return render_template("login.html", error="User not registered")

            if user_doc.to_dict().get("role") != role:
                return render_template("login.html", error="Invalid role selected")

            session["user_id"] = uid
            session["role"] = role

            return redirect(
                url_for("admin_dashboard") if role == "admin" else url_for("staff_dashboard")
            )

        except Exception as e:
            print("LOGIN ERROR:", e)
            return render_template("login.html", error="Login failed")

    return render_template("login.html")

# ======================
# DASHBOARDS
# ======================
@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("admin_dashboard.html")


@app.route("/staff_dashboard")
def staff_dashboard():
    if session.get("role") != "staff":
        return redirect(url_for("login"))
    return render_template("staff_dashboard.html")

# ======================
# STAFF MANAGEMENT
# ======================
@app.route("/staff_management")
def staff_management():
    return render_template("staff_management.html")


@app.route("/staff/get_all")
def get_all_staff():
    staff_docs = db.collection("staff").stream()
    return jsonify([{"id": doc.id, **doc.to_dict()} for doc in staff_docs])


@app.route("/staff/add", methods=["POST"])
def add_staff():
    staff_id = str(uuid.uuid4())
    db.collection("staff").document(staff_id).set(request.json)
    return jsonify({"status": "success"})


@app.route("/staff/update/<staff_id>", methods=["PUT"])
def update_staff(staff_id):
    db.collection("staff").document(staff_id).update(request.json)
    return jsonify({"status": "success"})


@app.route("/staff/delete/<staff_id>", methods=["DELETE"])
def delete_staff(staff_id):
    db.collection("staff").document(staff_id).delete()
    return jsonify({"status": "success"})

# ======================
# PATIENT MANAGEMENT
# ======================
@app.route("/patient_management")
def patient_management():
    return render_template("patient_management.html")


@app.route("/patient/get_all")
def get_all_patients():
    patients = db.collection("patients").stream()
    return jsonify([{"id": doc.id, **doc.to_dict()} for doc in patients])


@app.route("/patient/add", methods=["POST"])
def add_patient():
    patient_id = str(uuid.uuid4())
    db.collection("patients").document(patient_id).set(request.json)
    return jsonify({"status": "success"})


@app.route("/patient/update/<patient_id>", methods=["PUT"])
def update_patient(patient_id):
    db.collection("patients").document(patient_id).update(request.json)
    return jsonify({"status": "success"})


@app.route("/patient/delete/<patient_id>", methods=["DELETE"])
def delete_patient(patient_id):
    db.collection("patients").document(patient_id).delete()
    return jsonify({"status": "success"})

# ======================
# BILLING
# ======================
@app.route("/billing_structure")
def billing_structure():
    return render_template("billing_structure.html")


@app.route("/billing/get_all")
def get_all_billing():
    billing_docs = db.collection("billing").stream()
    return jsonify([{"id": doc.id, **doc.to_dict()} for doc in billing_docs])


@app.route("/billing/add", methods=["POST"])
def add_billing():
    billing_id = str(uuid.uuid4())
    db.collection("billing").document(billing_id).set(request.json)
    return jsonify({"status": "success"})


@app.route("/billing/update/<billing_id>", methods=["PUT"])
def update_billing(billing_id):
    db.collection("billing").document(billing_id).update(request.json)
    return jsonify({"status": "success"})


@app.route("/billing/delete/<billing_id>", methods=["DELETE"])
def delete_billing(billing_id):
    db.collection("billing").document(billing_id).delete()
    return jsonify({"status": "success"})

# ======================
# LOGOUT
# ======================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ======================
# RUN
# ======================
if __name__ == "__main__":
    app.run(debug=True)




