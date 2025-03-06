import boto3
import json
from math import ceil
from botocore.exceptions import ClientError
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta

print("Packages have imported successfully")

dynamodb = boto3.resource('dynamodb')
trips_table = dynamodb.Table("Swift-lift-club-portal-trips")
users_table = dynamodb.Table("Swift-lift-club-portal-users")

print("DynamoDB Tables initialized successfully")

def custom_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def get_weekly_trips(passenger_id, target_date):
    target_date_obj = datetime.fromisoformat(target_date)
    if target_date_obj.weekday() != 0:
        raise ValueError(f"target_date {target_date} is not a Monday.")
    
    friday_date_obj = target_date_obj + timedelta(days=4)
    start_of_week_iso = target_date_obj.strftime("%Y-%m-%d")
    end_of_week_iso = friday_date_obj.strftime("%Y-%m-%d")
    
    try:
        response = trips_table.scan(
            FilterExpression=
                Attr('passenger_id').eq(passenger_id) & 
                Attr('trip_date').between(start_of_week_iso, end_of_week_iso)
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def calculate_fare(passenger_type, completed_trips, missed_trips):
    if passenger_type == "long-term":
        weekly_fare = 350
    elif passenger_type == "long-distance":
        weekly_fare = 450
    elif passenger_type == "per-trip":
        return [completed_trips * 35, "N/A"]  # R35 per completed trip
    elif passenger_type == "defunct":
        return 0  # No fare for defunct passengers
    else:
        raise ValueError("Unknown passenger type")
    
    discount_threshold = ceil(10 * 0.4)
    eligible_missed_trips = max(0, missed_trips - discount_threshold)
    discount_per_trip = weekly_fare * 0.15
    total_discount = eligible_missed_trips * discount_per_trip
    final_fare = max(weekly_fare - total_discount, 0)
    
    return [final_fare, total_discount]

def get_passenger_info(passenger_id):
    try:
        response = users_table.query(KeyConditionExpression=Key('passenger_id').eq(passenger_id))
        if response.get('Items'):
            return response['Items'][0]
        return None
    except Exception as e:
        print(f"Error fetching passenger info: {e}")
        return None

def lambda_handler(event, context):
    try:
        passenger_id = event.get("queryStringParameters", {}).get('passenger_id')
        target_week = event.get("queryStringParameters", {}).get('target_week')
        if not passenger_id or not target_week:
            raise ValueError("passenger_id and target_week are required")
        
        passenger_info = get_passenger_info(passenger_id)
        if not passenger_info:
            raise ValueError(f"Passenger with ID {passenger_id} not found")
        
        passenger_type = passenger_info.get("passenger_type", "unknown").lower()
        weekly_trips = get_weekly_trips(passenger_id, target_week)
        
        completed_trips = sum(1 for trip in weekly_trips if trip['status'] == 'completed')
        missed_trips = sum(1 for trip in weekly_trips if trip['status'] == 'missed')
        
        final_fare = calculate_fare(passenger_type, completed_trips, missed_trips)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'passenger_id': passenger_id,
                'week_starting_on': target_week,
                'passenger_name': passenger_info.get('passenger_name', 'Unknown'),
                'passenger_type': passenger_type,
                'trips_completed': completed_trips,
                'trips_missed': missed_trips,
                'total_trips': completed_trips + missed_trips,
                'discount': final_fare[1],
                'final_fare': final_fare[0]
            }, default=custom_serializer),
            'headers': {"Content-Type": "application/json"}
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(str(e)),
            'headers': {"Content-Type": "application/json"}
        }
