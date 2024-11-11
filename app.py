from flask import Flask, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import ssl

load_dotenv()

app = Flask(__name__)

@app.route("/send-email", methods=["POST"])
def send_email():
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    host = os.getenv("HOST")

    if not sender_email or not sender_password or not host:
        return jsonify({"error": "Missing environment variables"}), 500

    data = request.get_json()
    recipient = data.get("recipient")
    subject = data.get("subject")
    message = data.get("message")

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
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        context = ssl.create_default_context()
        context.options |= ssl.OP_LEGACY_SERVER_CONNECT

        server = smtplib.SMTP_SSL(host, 465, context=context)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, msg.as_string())
        server.quit()

        return jsonify({"message": "Email sent successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

