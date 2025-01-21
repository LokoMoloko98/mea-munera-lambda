import boto3
import json
import requests

from botocore.exceptions import ClientError
print("Packages have imported successfully")

def lambda_handler(event, context):
    try:
        print("Processing")

        return {
            'statusCode': 200,
            'body': json.dumps('Process completed successfully')
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error occurred during processing')
        }
