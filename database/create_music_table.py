import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.client("dynamodb", region_name="us-east-1")

def create_music_table_with_indexes():
    try:
        response = dynamodb.create_table(
            TableName="music",
            AttributeDefinitions=[
                {"AttributeName": "artist", "AttributeType": "S"},   # Partition Key
                {"AttributeName": "title",  "AttributeType": "S"},   # Sort Key
                {"AttributeName": "year",   "AttributeType": "S"},   # For GSI + LSI
                {"AttributeName": "album",  "AttributeType": "S"}    # For GSI
            ],
            KeySchema=[
                {"AttributeName": "artist", "KeyType": "HASH"},
                {"AttributeName": "title",  "KeyType": "RANGE"}
            ],
            
            # ==================== LOCAL SECONDARY INDEX ====================
            LocalSecondaryIndexes=[
                {
                    "IndexName": "music-year-lsi",
                    "KeySchema": [
                        {"AttributeName": "artist", "KeyType": "HASH"},   # Must match table's partition key
                        {"AttributeName": "year",   "KeyType": "RANGE"}   # New sort key
                    ],
                    "Projection": {
                        "ProjectionType": "ALL"   # Include all attributes
                    }
                }
            ],
            
            # ==================== GLOBAL SECONDARY INDEXES ====================
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "music-year-gsi",
                    "KeySchema": [
                        {"AttributeName": "year",   "KeyType": "HASH"},
                        {"AttributeName": "artist", "KeyType": "RANGE"}
                    ],
                    "Projection": {
                        "ProjectionType": "ALL"
                    },
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
                },
                {
                    "IndexName": "music-album-gsi",
                    "KeySchema": [
                        {"AttributeName": "album",  "KeyType": "HASH"},
                        {"AttributeName": "artist", "KeyType": "RANGE"}
                    ],
                    "Projection": {
                        "ProjectionType": "ALL"
                    },
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

        print("Table creation with GSIs and LSI initiated...")
        
        # Wait for table to be ready
        waiter = dynamodb.get_waiter("table_exists")
        waiter.wait(TableName="music")
        
        print("Music table created successfully!")
        print("LSI 'music-year-lsi' created (artist + year)")
        print("GSI 'music-year-gsi' created")
        print("GSI 'music-album-gsi' created")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Table 'music' already exists.")
        else:
            print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    create_music_table_with_indexes()