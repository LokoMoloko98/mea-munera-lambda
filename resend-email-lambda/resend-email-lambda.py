import boto3
import requests
import json
import os
from jinja2 import Template

# Load Resend API key from environment variable
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

# Define email templates
EMAIL_TEMPLATES = {
    "contact_form": "New message from {{ name }} ({{ email }}):\n\n{{ message }}",
    "passenger_notification": "Dear {{ passenger_name }},\n\nYour trip details have changed:\n\n{{ details }}\n\nThanks!",
}

def send_email(recipient, subject, body):
    """Send an email via Resend API"""
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": "no-reply@yourdomain.com",
        "to": [recipient],
        "subject": subject,
        "text": body,
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def lambda_handler(event, context):
    """Lambda function entry point"""
    try:
        recipient = event["recipient"]
        email_type = event["email_type"]
        data = event["data"]

        # Ensure valid email type
        if email_type not in EMAIL_TEMPLATES:
            return {"statusCode": 400, "body": json.dumps("Invalid email type")}

        # Render the email template
        template = Template(EMAIL_TEMPLATES[email_type])
        email_body = template.render(data)

        # Determine subject based on email type
        subject = "Contact Form Message" if email_type == "contact_form" else "Trip Notification"

        # Send email
        response = send_email(recipient, subject, email_body)

        return {"statusCode": 200, "body": json.dumps(response)}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(str(e))}