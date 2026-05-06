import boto3

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

table = dynamodb.create_table(
    TableName="subscriptions",
    KeySchema=[
        {"AttributeName": "email", "KeyType": "HASH"},
        {"AttributeName": "title", "KeyType": "RANGE"}
    ],
    AttributeDefinitions=[
        {"AttributeName": "email", "AttributeType": "S"},
        {"AttributeName": "title", "AttributeType": "S"}
    ],
    BillingMode="PAY_PER_REQUEST"
)

table.wait_until_exists()
print("subscriptions table created")