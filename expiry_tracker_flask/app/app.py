from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from datetime import datetime, timedelta
from twilio.rest import Client

app = Flask(__name__)
app.secret_key = "supersecretkey"  # For flash messages

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["expiry_tracking"]
collection = db["products"]

# Twilio Credentials
account_sid = "AC9766c1e1da2a92ec30d34d6aa2e7855f"
auth_token = "846b8c7deb1ccf4ab1ded6600eb7d861"
twilio_whatsapp_number = "whatsapp:+14155238886"
recipient_whatsapp_number = "whatsapp:+918714872773" # Change to dynamic user input if needed

# Function to send WhatsApp alert
def send_whatsapp_alert(message_body):
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        from_=twilio_whatsapp_number,
        body=message_body,
        to=recipient_whatsapp_number
    )
    return message.sid

# Home Page - Add Product
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        mfg_date = request.form["mfg_date"]
        best_before_days = request.form.get("best_before_days")
        expiry_date = request.form.get("expiry_date")

        if not name or not mfg_date:
            flash("Product name and manufacturing date are required!", "danger")
            return redirect(url_for("index"))

        if not expiry_date and best_before_days:
            expiry_date = datetime.strptime(mfg_date, "%Y-%m-%d") + timedelta(days=int(best_before_days))
        elif expiry_date:
            expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d")
        else:
            flash("Provide either Best Before Days or Expiry Date", "danger")
            return redirect(url_for("index"))

        product = {
            "name": name,
            "mfg_date": datetime.strptime(mfg_date, "%Y-%m-%d"),
            "expiry_date": expiry_date
        }
        collection.insert_one(product)
        flash(f"{name} added! Expires on {expiry_date.strftime('%Y-%m-%d')}", "success")

    return render_template("index.html")

# Expiry Check Page + WhatsApp Alert
@app.route("/expiry")
def check_expiry():
    today = datetime.today()
    alert_date = today + timedelta(days=2)

    expiring_items = list(collection.find({
        "expiry_date": {"$gte": today, "$lte": alert_date}
    }))

    # Convert expiry_date to string for display
    for item in expiring_items:
        item["expiry_date"] = item["expiry_date"].strftime("%Y-%m-%d")

    # Send WhatsApp notification if products are expiring
    if expiring_items:
        message_body = "⚠️ Expiry Alert:\n" + "\n".join(
            [f"{item['name']} (Expires on {item['expiry_date']})" for item in expiring_items]
        )
        send_whatsapp_alert(message_body)
        flash("WhatsApp alert sent successfully!", "success")
    else:
        flash("No expiring products found.", "info")

    return render_template("expiry.html", products=expiring_items)

if __name__ == "__main__":
    app.run(debug=True, port=5000)  # Running on port 5000

