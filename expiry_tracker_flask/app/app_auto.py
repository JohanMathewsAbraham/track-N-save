from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
from twilio.rest import Client
from bson import ObjectId
from apscheduler.schedulers.background import BackgroundScheduler
import time

app = Flask(__name__)
app.secret_key = "supersecretkey"  # For flash messages

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["expiry_tracking"]
collection = db["products"]

# Twilio Credentials (Kept for future use)
account_sid = "AC9766c1e1da2a92ec30d34d6aa2e7855f"
auth_token = "846b8c7deb1ccf4ab1ded6600eb7d861"
twilio_whatsapp_number = "whatsapp:+14155238886"
recipient_whatsapp_number = "whatsapp:+918714872773"  # Change to dynamic user input if needed

# Function to send WhatsApp messages (Kept for future use)
def send_whatsapp_alert(message_body):
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        from_=twilio_whatsapp_number,
        body=message_body,
        to=recipient_whatsapp_number
    )
    return message.sid
    
    
def check_and_send_alert():
    today = datetime.today()
    alert_date = today + timedelta(days=2)

    expiring_items = list(collection.find({
        "expiry_date": {"$gte": today, "$lte": alert_date}
    }))

    if expiring_items:
        message_body = "⚠️ Expiry Alert:\n" + "\n".join(
            [f"{item['name']} (Expires on {item['expiry_date'].strftime('%Y-%m-%d')})" for item in expiring_items]
        )
        send_whatsapp_alert(message_body)  # Send WhatsApp alert
        print("✅ WhatsApp alert sent successfully!")
    else:
        print("✅ No expiring products found.")

# Schedule the function to run every day at 8:40 PM with a 2-minute grace period
scheduler = BackgroundScheduler()
scheduler.add_job(
    check_and_send_alert, 
    "cron", 
    hour=22, minute=54, 
    misfire_grace_time=5  # 2 minutes grace period
)
scheduler.start()



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

    products = list(collection.find())
    return render_template("index.html", products=products)

# View and Filter Products
@app.route("/products")
def view_products():
    products = list(collection.find())
    for product in products:
        product["expiry_date"] = product["expiry_date"].strftime("%Y-%m-%d")
    return jsonify(products)

# Remove a Specific Product
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta

@app.route("/remove_product", methods=["POST"])
def remove_product():
    data = request.get_json()
    product_id = data.get("product_id")

    if product_id:
        collection.delete_one({"_id": ObjectId(product_id)})
        return jsonify({"success": True})  # Return JSON response for AJAX

    return jsonify({"success": False})


# Remove Expired Products
@app.route("/remove_expired", methods=["POST"])
def remove_expired():
    today = datetime.today()
    collection.delete_many({"expiry_date": {"$lt": today}})
    flash("Expired products removed successfully!", "success")
    return redirect(url_for("index"))

# Expiry Check Page 
@app.route("/expiry")
def check_expiry():
    today = datetime.today()
    alert_date = today + timedelta(days=2)

    expiring_items = list(collection.find({
        "expiry_date": {"$gte": today, "$lte": alert_date}
    }))

    for item in expiring_items:
        item["expiry_date"] = item["expiry_date"].strftime("%Y-%m-%d")

    # If there are products expiring soon, send a WhatsApp alert
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
    app.run(debug=True, port=5000)
