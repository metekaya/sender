from flask import Flask, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import ssl
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Correctly initialize Flask-Limiter
limiter = Limiter(get_remote_address, app=app)


@app.route("/send-email", methods=["POST"])
@limiter.limit("5 per minute")
def send_email():
    ALLOWED_DOMAIN = os.getenv("ALLOWED_DOMAIN")
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    host = os.getenv("HOST")
    api_key = os.getenv("API_KEY")

    # Check API key
    if api_key != request.headers.get("X-API-KEY"):
        return jsonify({"error": "Unauthorized"}), 401

    # Validate Referer or Origin headers
    referer = request.headers.get("Referer")
    origin = request.headers.get("Origin")
    if not (referer and ALLOWED_DOMAIN in referer) and not (
        origin and ALLOWED_DOMAIN in origin
    ):
        return jsonify({"error": "Forbidden"}), 403

    # Check environment variables
    if not sender_email or not sender_password or not host:
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

        return jsonify({"message": "Email sent successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
