import boto3
import json
from botocore.exceptions import ClientError

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
trips_table_name = "Swift-lift-club-portal-trips"
trips_table = dynamodb.Table(trips_table_name)

def custom_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # Convert Decimal to float
    raise TypeError(f"Type {type(obj)} not serializable")

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

        # Extract record details
        passenger_id = event.get("passenger_id")
        trip_date_time = event.get("trip_date_time")
        status = event.get("status")

        if not passenger_id or not trip_date_time or not status:
            raise ValueError("Missing required fields: passenger_id, trip_date_time, status.")

        if operation == "add":
            # Add a new record
            response = trips_table.put_item(
                Item={
                    "passenger_id": passenger_id,
                    "trip_date_time": trip_date_time,
                    "status": status
                }
            )
            body = {"message": "Record added successfully", "response": response}

        elif operation == "update":
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
