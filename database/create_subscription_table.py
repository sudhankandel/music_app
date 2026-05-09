import boto3

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

table = dynamodb.create_table(
    TableName="subscriptions",
    KeySchema=[
        {"AttributeName": "email", "KeyType": "HASH"},
        {"AttributeName": "subscription_id", "KeyType": "RANGE"}
    ],
    AttributeDefinitions=[
        {"AttributeName": "email", "AttributeType": "S"},
        {"AttributeName": "subscription_id", "AttributeType": "S"}
    ],
    BillingMode="PAY_PER_REQUEST"
)

table.wait_until_exists()
print("subscriptions table created")