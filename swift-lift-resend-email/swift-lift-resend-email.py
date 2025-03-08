import requests
import json
import os
from jinja2 import Template
from decimal import Decimal

# Load Resend API key from environment variable
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

def custom_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # Convert Decimal to float
    raise TypeError(f"Type {type(obj)} not serializable")

# Define email templates
EMAIL_TEMPLATES = {
    "contact_form": "New message from {{ name }}\n\nEmail: {{ email }}\n\nCell Number {{ contact_number }}:\n\nMessage: {{ message }}",
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
        "from": "swift-lift-club@no-reply.moloko-mokubedi.co.za",
        "to": [recipient],
        "subject": subject,
        "text": body,
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def lambda_handler(event, context):
    """Lambda function entry point"""
    print(f"Received event: {json.dumps(event, indent=4, default=custom_serializer)}")
    try:
        body = json.loads(event.get("body", "{}")) 
        email_type = body.get("email_type")
        data = body.get("data", {})

        # Ensure valid email type
        if email_type not in EMAIL_TEMPLATES:
            return {"statusCode": 400, "body": json.dumps("Invalid email type")}

        # Render the email template
        template = Template(EMAIL_TEMPLATES[email_type])
        email_body = template.render(data)

        # Determine subject based on email type
        subject =""
        if email_type == "contact_form":
            subject = "Swift Lift Club Interest..."
            recipient = "communication@moloko-mokubedi.co.za"
        elif email_type == "Trip Notification":
            subject = "Trip Notification"

        # Send email
        response = send_email(recipient, subject, email_body)

        return {"statusCode": 200, "body": json.dumps(response, indent=4, default=custom_serializer)}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(str(e))}