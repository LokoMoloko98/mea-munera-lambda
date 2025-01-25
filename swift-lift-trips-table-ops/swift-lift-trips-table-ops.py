import boto3
import json
from botocore.exceptions import ClientError
from datetime import datetime
import pytz  # For timezone conversion

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
trips_table_name = "Swift-lift-club-portal-trips"
trips_table = dynamodb.Table(trips_table_name)

def generate_trip_date_time():
    """
    Generate the current date and time in Central African Time (UTC+2) in ISO 8601 format.
    Returns:
        str: The current date and time in ISO 8601 format (e.g., "2025-01-25T16:30:00+02:00").
    """
    cat_tz = pytz.timezone("Africa/Johannesburg")  # Central African Time
    return datetime.now(cat_tz).strftime("%Y-%m-%dT%H:%M:%S%z")

def lambda_handler(event, context):
    body = {}
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }

    try:
        print("Processing operation for trips table")

        # Extract operation type (add/update)
        operation = event.get("operation")
        if operation not in ["add", "update"]:
            raise ValueError("Invalid operation. Must be 'add' or 'update'.")

        # Extract passenger_id and status
        passenger_id = event.get("passenger_id")
        status = event.get("status")

        if not passenger_id or not status:
            raise ValueError("Missing required fields: passenger_id, status.")

        if operation == "add":
            # Generate trip_date_time automatically in Central African Time
            trip_date_time = generate_trip_date_time()

            # Add a new record
            response = trips_table.put_item(
                Item={
                    "passenger_id": passenger_id,
                    "trip_date_time": trip_date_time,
                    "status": status
                }
            )
            body = {
                "message": "Record added successfully",
                "trip_date_time": trip_date_time,
                "response": response
            }

        elif operation == "update":
            # Extract trip_date_time for updates
            trip_date_time = event.get("trip_date_time")
            if not trip_date_time:
                raise ValueError("trip_date_time must be provided for update operations.")

            # Update an existing record
            response = trips_table.update_item(
                Key={
                    "passenger_id": passenger_id,
                    "trip_date_time": trip_date_time
                },
                UpdateExpression="SET #st = :status",
                ExpressionAttributeNames={
                    "#st": "status"
                },
                ExpressionAttributeValues={
                    ":status": status
                },
                ReturnValues="UPDATED_NEW"
            )
            body = {"message": "Record updated successfully", "response": response}

    except ValueError as ve:
        print(f"Value error: {ve}")
        statusCode = 400
        body = {"error": str(ve)}

    except ClientError as ce:
        print(f"Client error: {ce}")
        statusCode = 500
        body = {"error": "DynamoDB error occurred"}

    except Exception as e:
        print(f"An error occurred: {e}")
        statusCode = 500
        body = {"error": "Internal server error"}

    return {
        "statusCode": statusCode,
        "body": json.dumps(body),
        "headers": headers
    }
