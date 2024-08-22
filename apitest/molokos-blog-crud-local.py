 
import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

client = boto3.client('dynamodb')
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table('Lokos-Blok-data')
tableName = 'Lokos-Blok-data'


def lambda_handler(event, context):
    print(event)
    body = {}
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }

    try:
        if event['routeKey'] == "DELETE /blogs/{BlogId}":
            table.delete_item(
                Key={'BlogId': event['pathParameters']['BlogId']})
            body = 'Deleted item ' + event['pathParameters']['BlogId']
        elif event['routeKey'] == "GET /blogs/{BlogId}":
            body = table.query(KeyConditionExpression=Key('BlogId').eq(event['pathParameters']['BlogId']))
            print(body)
            body = body["Items"]
            responseBody = [{'BlogId': body['BlogId'], 'BlogTitle': body['BlogTitle'], 'PublishedDate': body['PublishedDate']}]
            body = responseBody
        # elif event['routeKey'] == "GET /items":
        #     body = table.scan()
        #     body = body["Items"]
        #     print("ITEMS----")
        #     print(body)
        #     responseBody = []
        #     for items in body:
        #         responseItems = [
        #             {'price': float(items['price']), 'BlogId': items['BlogId'], 'name': items['name']}]
        #         responseBody.append(responseItems)
        #     body = responseBody
        # elif event['routeKey'] == "PUT /items":
        #     requestJSON = json.loads(event['body'])
        #     table.put_item(
        #         Item={
        #             'BlogId': requestJSON['BlogId'],
        #             'price': Decimal(str(requestJSON['price'])),
        #             'name': requestJSON['name']
        #         })
        #     body = 'Put item ' + requestJSON['BlogId']
    except KeyError:
        statusCode = 400
        body = 'Unsupported route: ' + event['routeKey']
    body = json.dumps(body)
    res = {
        "statusCode": statusCode,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": body
    }
    return res

def main():
    # Simulate an example event
    event = {
        "routeKey": "GET /blogs/02",
        "pathParameters": {"BlogId":"01"},
    }

    # Simulate the context (you can mock this or use an empty one)
    context = {}

    # Call the Lambda handler
    response = lambda_handler(event, context)

    # Print the response
    print("Response:")
    print(json.dumps(response, indent=4))

if __name__ == "__main__":
    main()