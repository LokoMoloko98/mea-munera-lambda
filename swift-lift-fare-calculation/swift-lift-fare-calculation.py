import boto3
import json
from math import ceil
from botocore.exceptions import ClientError
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta

print("Packages have imported successfully")

# Initialize DynamoDB
client = boto3.client('dynamodb')
dynamodb = boto3.resource('dynamodb')
trips_table_name = "Swift-lift-club-portal-trips"
trips_table = dynamodb.Table(trips_table_name)
print("DynamoDB Table initialized successfully")

def custom_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # Convert Decimal to float
    raise TypeError(f"Type {type(obj)} not serializable")

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

    # Format dates to ISO 8601
    start_of_week_iso = target_date_obj.strftime("%Y-%m-%dT00:00:00Z")
    end_of_week_iso = friday_date_obj.strftime("%Y-%m-%dT23:59:59Z")

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


def calculate_fare(total_trips, missed_trips, weekly_fare):
    """
    Calculate the final fare for a passenger based on total trips, missed trips,
    and discount rules.

    Args:
        total_trips (int): The total number of trips in a week.
        missed_trips (int): The number of trips missed by the passenger.
        weekly_fare (float): The standard weekly fare (default: 350).

    Returns:
        dict: A dictionary containing details about the fare calculation.
    """
    if total_trips <= 0:
        raise ValueError("Total trips must be greater than 0.")
    if missed_trips < 0:
        raise ValueError("Missed trips cannot be negative.")
    if missed_trips > total_trips:
        raise ValueError("Missed trips cannot exceed total trips.")

    # Calculate the threshold for discounts (40% of total trips)
    discount_threshold = ceil(total_trips * 0.4)

    # Determine eligible missed trips for discount
    eligible_missed_trips = max(0, missed_trips - discount_threshold)

    # Discount per trip (15% of the weekly fare per missed trip)
    discount_per_trip = weekly_fare * 0.15
    total_discount = eligible_missed_trips * discount_per_trip

    # Calculate the final fare
    final_fare = weekly_fare - total_discount
    final_fare = max(final_fare, 0)  # Ensure fare is not negative

    if total_trips == missed_trips:
        final_fare = 0
        total_discount = 0

    # Return the result as a dictionary
    return {
        "total_trips": total_trips,
        "missed_trips": missed_trips,
        "discount_threshold": discount_threshold,
        "eligible_missed_trips": eligible_missed_trips,
        "discount_per_trip": discount_per_trip,
        "total_discount": total_discount,
        "final_fare": final_fare
    }

def lambda_handler(event, context):
    body = {}
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }
    try:
        print("Processing")
        print(f"Received event: {json.dumps(event, indent=4, default=custom_serializer)}")
        # Extract passenger_id and total trips from the event
        passenger_id = event.get("queryStringParameters").get('passenger_id')
        target_week = event.get("queryStringParameters").get('target_week')
        if not passenger_id or not target_week:
            raise ValueError("passenger_id and target_week must be provided")
        print(f"Calculating fare for Passenger ID: {passenger_id}, for the week beginning on: {target_week}")

        # Fetch trips for the passenger
        weekly_trips = get_weekly_trips(passenger_id, target_week)
        missed_trips_list = [trip for trip in weekly_trips if trip['status'] == 'missed']
        missed_trips = len(missed_trips_list)
        total_trips = 10  # Expected Total trips in a week
        print(f"Total trips for the week beginning on {target_week}: {total_trips}, Missed trips: {missed_trips}")

        # Calculate the final fare
        result = calculate_fare(total_trips=total_trips, missed_trips=missed_trips, weekly_fare=350) # Default weekly fare is 350 for now, will fetch from users DB later
        final_fare = result['final_fare']
        print(f"Final fare calculated: R{final_fare}")

        return {
            'statusCode': statusCode,
            'body': json.dumps(result),
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
