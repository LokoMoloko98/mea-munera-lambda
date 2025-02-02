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

    
def get_passenger_profile(passenger_id):
    """
    Get passenger name from users table
    """
    try:
        response = users_table.query(
            KeyConditionExpression=Key('passenger_id').eq(passenger_id)
        )
        if response.get('Items') and len(response['Items']) > 0:
            return response['Items'][0]
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
        print("Processing operation for getting user profile")

        passenger_id = event.get("queryStringParameters").get("passenger_id")
        if not passenger_id:
            raise ValueError("Missing required fields: passenger_id")
        
        # Get passenger profile
        passenger_profile = get_passenger_profile(passenger_id)
        if not passenger_profile:
            raise ValueError(f"Passenger with ID {passenger_id} not found in users table")

        body = passenger_profile
        return {
            'statusCode': statusCode,
            'body': json.dumps(body, default=custom_serializer),
            'headers': headers
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