import boto3
import json
# from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from botocore.exceptions import ClientError

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
users_table_name = "music-catalogue-users"
songs_table_name = "music-catalogue-table-ops"
trips_table = dynamodb.Table(songs_table_name)
users_table = dynamodb.Table(users_table_name)
print("DynamoDB Table initialized successfully")

def custom_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

    
def get_user_profile(user_id):
    """
    Get user name from users table
    """
    try:
        response = users_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        if response.get('Items') and len(response['Items']) > 0:
            return response['Items'][0]
        return None
    except Exception as e:
        print(f"Error getting user name: {e}")
    return None

def lambda_handler(event, context):
    body = {}
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }
    # Debugging print statement. leave this here
    # print(f"Received event: {json.dumps(event, indent=4, default=custom_serializer)}")

    try:
        print("Processing operation for getting user profile")

        user_id = event.get("queryStringParameters").get("user_id")
        if not user_id:
            raise ValueError("Missing required fields: user_id")
        
        # Get user profile
        user_profile = get_user_profile(user_id)
        if not user_profile:
            raise ValueError(f"user with ID {user_id} not found in users table")

        body = user_profile
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