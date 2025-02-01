import boto3
import json
from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from botocore.exceptions import ClientError

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
trips_table_name = "Swift-lift-club-portal-trips"
users_table_name = "Swift-lift-club-portal-users"
trips_table = dynamodb.Table(trips_table_name)
users_table = dynamodb.Table(users_table_name)
print("DynamoDB Table initialized successfully")

def custom_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # Convert Decimal to float
    raise TypeError(f"Type {type(obj)} not serializable")

def generate_trip_date_time():
    """
    Generate the current date and time in Central African Time (UTC+2) in ISO 8601 format.
    Returns:
        str: The current date and time in ISO 8601 format (e.g., "2025-01-25T16:30:00+02:00").
    """
    utc_plus_2 = timezone(timedelta(hours=2))
    now = datetime.now(utc_plus_2)
    return now.isoformat(timespec="seconds")

def get_weekly_trips(passenger_id, target_date):
    """
    Get all trips for a passenger from the specified Monday to the following Friday.

    Args:
        passenger_id (str): The ID of the passenger.
        target_date (str): A Monday date (in ISO 8601 format, e.g., "2025-01-20").
    Returns:
        list: A list of trips for the specified week.
    """
    # Parse the target date
    target_date_obj = datetime.fromisoformat(target_date)

    # Check if the date is a Monday
    if target_date_obj.weekday() != 0:  # 0 = Monday
        raise ValueError(f"target_date {target_date} is not a Monday. Please provide a Monday.")

    # Calculate Friday of the same week
    friday_date_obj = target_date_obj + timedelta(days=4)

    # Format dates to ISO 8601 with UTC+2 timezone
    utc_plus_2 = timezone(timedelta(hours=2))
    start_of_week_iso = target_date_obj.replace(tzinfo=utc_plus_2).strftime("%Y-%m-%dT00:00:00%z")
    end_of_week_iso = friday_date_obj.replace(tzinfo=utc_plus_2).strftime("%Y-%m-%dT23:59:59%z")

    try:
        # Query the table
        response = trips_table.query(
            KeyConditionExpression=Key('passenger_id').eq(passenger_id) & 
                                   Key('trip_date_time').between(start_of_week_iso, end_of_week_iso)
        )
        return response.get('Items', [])

    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    
def get_passenger_name(passenger_id):
    """
    Get passenger name from users table
    """
    try:
        response = users_table.query(
            KeyConditionExpression=Key('passenger_id').eq(passenger_id)
        )
        if response.get('Items') and len(response['Items']) > 0:
            return response['Items'][0]['passenger_name']
        return None
    except Exception as e:
        print(f"Error getting passenger name: {e}")
    return None

def lambda_handler(event, context):
    body = {}
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }
    # print(f"Received event: {json.dumps(event, indent=4, default=custom_serializer)}")

    try:
        print("Processing operation for trips table")

        # Extract operation type
        operation = event.get("queryStringParameters").get("operation")
        if operation not in ["add", "update", "get_weekly_trips"]:
            raise ValueError("Invalid operation. Must be 'add', 'update', or 'get_weekly_trips'.")

        if operation == "add":
            # Extract passenger_id and status
            passenger_id = event.get("queryStringParameters").get("passenger_id")
            status = event.get("queryStringParameters").get("status")
            if not passenger_id or not status:
                raise ValueError("Missing required fields: passenger_id, status.")
            
            # Get passenger name
            passenger_name = get_passenger_name(passenger_id)
            if not passenger_name:
                raise ValueError(f"Passenger with ID {passenger_id} not found in users table")

            # Generate trip_date_time automatically
            trip_date_time = generate_trip_date_time()

            # Add a new record
            response = trips_table.put_item(
                Item={
                    "passenger_id": passenger_id,
                    "trip_date_time": trip_date_time,
                    "status": status,
                    "passenger_name": passenger_name
                }
            )
            body = {
                "message": "Record added successfully",
                "trip_date_time": trip_date_time,
                "response": response
            }

        elif operation == "update":
            # Extract required fields for updates
            passenger_id = event.get("queryStringParameters").get("passenger_id")
            trip_date_time = event.get("queryStringParameters").get("trip_date_time")
            status = event.get("queryStringParameters").get("status")
            if not passenger_id or not trip_date_time or not status:
                raise ValueError("Missing required fields: passenger_id, trip_date_time, status.")

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

        elif operation == "get_weekly_trips":
            # Extract required fields for getting weekly trips
            passenger_id = event.get("queryStringParameters").get("passenger_id")
            target_week = event.get("queryStringParameters").get("target_week")  # Monday's date in ISO 8601 format
            if not passenger_id or not target_week:
                raise ValueError("Missing required fields: passenger_id, target_week.")

            # Fetch weekly trips
            weekly_trips = get_weekly_trips(passenger_id, target_week)
            body = {
                "message": f"Weekly trips for passenger_id: {passenger_id} from {target_week}",
                "weekly_trips": weekly_trips
            }

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