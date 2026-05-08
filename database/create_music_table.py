import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.client("dynamodb", region_name="us-east-1")

def create_music_table_with_indexes():
    try:
        response = dynamodb.create_table(
            TableName="music",

            AttributeDefinitions=[
                {"AttributeName": "artist", "AttributeType": "S"},       # PK
                {"AttributeName": "album_title", "AttributeType": "S"},  # SK = album#title
                {"AttributeName": "year", "AttributeType": "S"},
                {"AttributeName": "album", "AttributeType": "S"}
            ],

            KeySchema=[
                {"AttributeName": "artist", "KeyType": "HASH"},
                {"AttributeName": "album_title", "KeyType": "RANGE"}
            ],

            # LSI: useful for querying songs by same artist ordered/filter by year
            LocalSecondaryIndexes=[
                {
                    "IndexName": "artist-year-lsi",
                    "KeySchema": [
                        {"AttributeName": "artist", "KeyType": "HASH"},
                        {"AttributeName": "year", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"}
                }
            ],

            # GSIs: useful for searching across all artists
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "year-artist-gsi",
                    "KeySchema": [
                        {"AttributeName": "year", "KeyType": "HASH"},
                        {"AttributeName": "artist", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
                },
                {
                    "IndexName": "album-artist-gsi",
                    "KeySchema": [
                        {"AttributeName": "album", "KeyType": "HASH"},
                        {"AttributeName": "artist", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
                }
            ],

            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        )

        print("Table creation started...")

        waiter = dynamodb.get_waiter("table_exists")
        waiter.wait(TableName="music")

        print("Music table created successfully!")
        print("Primary key: artist + album_title")
        print("LSI created: artist-year-lsi")
        print("GSI created: year-artist-gsi")
        print("GSI created: album-artist-gsi")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("Table 'music' already exists.")
        else:
            print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    create_music_table_with_indexes()