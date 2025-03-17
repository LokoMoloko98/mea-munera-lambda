import boto3
from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
from botocore.exceptions import BotoCoreError, ClientError
from decimal import Decimal
import json

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

def get_trips_by_date(trip_date, table_name):
    """
    Queries the DynamoDB table for all trips on a given date.
    
    :param trip_date: The trip date in 'YYYY-MM-DD' format.
    :param table_name: The name of the DynamoDB table.
    :return: A list of trips matching the given date.
    """
    try:
        response = dynamodb.scan(
            TableName=table_name,
            FilterExpression="trip_date = :date",
            ExpressionAttributeValues={":date": {"S": trip_date}}
        )

        trips = response.get("Items", [])
        
        return trips

    except (BotoCoreError, ClientError) as e:
        print(f"Error querying DynamoDB: {e}")
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
    print(f"Received event: {json.dumps(event, indent=4, default=custom_serializer)}")

    try:
        print("Processing operation for trips table")

        # Extract operation type
        operation = event.get("queryStringParameters").get("operation")
        if operation not in ["get_trips_by_date"]:
            raise ValueError("Invalid operation. Must be 'get_trips_by_date'.")
        
        elif operation == "get_trips_by_date":
            # Extract required fields for getting weekly trips
            trip_date = event.get("queryStringParameters").get("trip_date")
            if not trip_date:
                raise ValueError("Missing required fields: trip_date.")
        
            # Fetch weekly trips
            trips_by_date_trips = get_trips_by_date(trip_date, trips_table_name)
            body = {
                "message": f"Trips for day {trip_date}",
                "trips_by_date_trips": trips_by_date_trips
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