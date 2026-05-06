import boto3

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Your table name
table = dynamodb.Table('login')

# Base student ID (change this to yours)
base_id = "s4147504"

for i in range(10):
    email = f"{base_id[:-1]}{i}@student.rmit.edu.au"
    username = f"sudhankandel{i}"
    password = f"{i}{(i+1)%10}{(i+2)%10}{(i+3)%10}{(i+4)%10}{(i+5)%10}"

    table.put_item(
        Item={
            'email': email,
            'user_name': username,
            'password': password
        }
    )

    print(f"Inserted: {email}")

print("All 10 records inserted successfully!")