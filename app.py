from flask import Flask, request, jsonify, make_response
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import ssl
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

# Load environment variables
load_dotenv()
ALLOWED_DOMAIN = os.getenv("ALLOWED_DOMAIN", "https://www.goitaly.com.tr")

app = Flask(__name__)

# Enable CORS for the specific allowed domain
CORS(
    app,
    resources={r"/send-email": {"origins": ALLOWED_DOMAIN}},
    supports_credentials=True,
)

# Initialize Flask-Limiter
limiter = Limiter(get_remote_address, app=app)


@app.route("/send-email", methods=["OPTIONS"])
def send_email_options():
    """
    Explicitly handle preflight requests and return the correct CORS headers.
    """
    if not ALLOWED_DOMAIN:
        return jsonify({"error": "Missing Allowed Domain"}), 500
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", ALLOWED_DOMAIN)
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    response.headers.add("Access-Control-Max-Age", "3600")  # Cache preflight for 1 hour

    return response


@app.route("/send-email", methods=["POST"])
@limiter.limit("5 per minute")
def send_email():
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    host = os.getenv("HOST")

    # Validate Referer or Origin headers
    origin = request.headers.get("Origin")
    if not origin or origin != ALLOWED_DOMAIN:
        return jsonify({"error": "Forbidden"}), 403

    # Check environment variables
    if not sender_email or not sender_password or not host or not ALLOWED_DOMAIN:
        return jsonify({"error": "Missing environment variables"}), 500

    # Get email data from the request
    data = request.get_json()
    recipient = data.get("recipient")
    subject = data.get("subject")
    message = data.get("message")

    # Check for missing fields
    missing_fields = []
    if not subject:
        missing_fields.append("subject")
    if not message:
        missing_fields.append("message")
    if not recipient:
        missing_fields.append("recipient")

    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

    try:
        # Set up the email
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        # Connect to the SMTP server and send the email
        context = ssl.create_default_context()
        context.options |= ssl.OP_LEGACY_SERVER_CONNECT
        server = smtplib.SMTP_SSL(host, 465, context=context)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, msg.as_string())
        server.quit()

        response = jsonify({"message": "Email sent successfully!"})
        response.headers.add("Access-Control-Allow-Origin", ALLOWED_DOMAIN)
        return response, 200
    except Exception as e:
        response = jsonify({"error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", ALLOWED_DOMAIN)
        return response, 500


if __name__ == "__main__":
    app.run(debug=True)
