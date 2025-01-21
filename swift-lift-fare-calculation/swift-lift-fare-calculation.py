import boto3
import json

from botocore.exceptions import ClientError
print("Packages have imported successfully")

def lambda_handler(event, context):
    try:
        print("Processing")
        print(event)
        print(context)
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
