import boto3

REGION_NAME = "us-east-1"
S3_BUCKET_NAME = "music-artist-images-79"

dynamodb = boto3.resource("dynamodb", region_name=REGION_NAME)
s3_client = boto3.client("s3", region_name=REGION_NAME)

login_table = dynamodb.Table("login")
music_table = dynamodb.Table("music")
subscription_table = dynamodb.Table("subscriptions")