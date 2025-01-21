import boto3
import json
from math import ceil
from botocore.exceptions import ClientError

print("Packages have imported successfully")

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')

# DynamoDB table name
TRIPS_TABLE = "Swift-lift-club-portal-trips"

def lambda_handler(event, context):
    body = {}
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }
    try:
        print("Processing")
        print(event)

        # Extract passenger_id and total trips from the event
        passenger_id = event.get('passenger_id')
        total_trips = event.get('total_trips')
        if not passenger_id or not total_trips:
            raise ValueError("passenger_id and total_trips must be provided")

        # Fetch missed trips for the passenger
        trips_table = dynamodb.Table(TRIPS_TABLE)
        response = trips_table.get_item(Key={"passenger_id": passenger_id})
        if 'Item' not in response:
            raise ValueError("Passenger data not found")

        missed_trips = response['Item'].get('missed_trips', 0)
        print(f"Total trips: {total_trips}, Missed trips: {missed_trips}")

        # Calculate the discount threshold
        discount_threshold = ceil(total_trips * 0.4)

        # Calculate eligible missed trips for discount
        eligible_missed_trips = max(0, missed_trips - discount_threshold)
        discount_per_trip = 0.15 * 350  # 15% of R350
        total_discount = eligible_missed_trips * discount_per_trip

        # Calculate the final fare
        final_fare = 350 - total_discount
        final_fare = max(final_fare, 0)  # Ensure fare is not negative

        print(f"Final fare calculated: R{final_fare}")

        body = {
            "passenger_id": passenger_id,
            "total_trips": total_trips,
            "missed_trips": missed_trips,
            "discount_threshold": discount_threshold,
            "eligible_missed_trips": eligible_missed_trips,
            "total_discount": total_discount,
            "final_fare": final_fare
        }

        return {
            'statusCode': statusCode,
            'body': json.dumps(body),
            'headers': headers
        }

    except ValueError as ve:
        print(f"Value error occurred: {ve}")
        return {
            'statusCode': 400,
            'body': json.dumps(str(ve)),
            'headers': headers
        }

    except ClientError as ce:
        print(f"Client error occurred: {ce}")
        return {
            'statusCode': 500,
            'body': json.dumps("Error accessing DynamoDB"),
            'headers': headers
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error occurred during processing'),
            'headers': headers
        }
