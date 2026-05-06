# lambda_function.py

import json
import os
import boto3
from boto3.dynamodb.conditions import Attr
from aws_config import (
    login_table,
    music_table,
    subscription_table,
    s3_client,
    S3_BUCKET_NAME
)


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS"
        },
        "body": json.dumps(body, default=str)
    }


def get_body(event):
    try:
        return json.loads(event.get("body") or "{}")
    except:
        return {}


def generate_image_url(image_key):
    if not image_key:
        return None

    return s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": S3_BUCKET_NAME,
            "Key": image_key
        },
        ExpiresIn=3600
    )


def lambda_handler(event, context):
    method = event.get("httpMethod")
    path = event.get("path")

    if method == "OPTIONS":
        return response(200, {"message": "CORS OK"})

    if path == "/login" and method == "POST":
        return login(event)

    if path == "/register" and method == "POST":
        return register(event)

    if path == "/music" and method == "GET":
        return query_music(event)

    if path == "/subscriptions" and method == "GET":
        return get_subscriptions(event)

    if path == "/subscriptions" and method == "POST":
        return add_subscription(event)

    if path == "/subscriptions" and method == "DELETE":
        return remove_subscription(event)

    return response(404, {
        "success": False,
        "message": "Route not found"
    })


def login(event):
    data = get_body(event)

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return response(400, {
            "success": False,
            "message": "Email and password are required"
        })

    result = login_table.get_item(Key={"email": email})
    user = result.get("Item")

    if not user:
        return response(404, {
            "success": False,
            "message": "User not found"
        })

    if user.get("password") != password:
        return response(401, {
            "success": False,
            "message": "Invalid password"
        })

    return response(200, {
        "success": True,
        "message": "Login successful",
        "email": user.get("email"),
        "user_name": user.get("user_name")
    })


def register(event):
    data = get_body(event)

    email = data.get("email")
    user_name = data.get("user_name")
    password = data.get("password")

    if not email or not user_name or not password:
        return response(400, {
            "success": False,
            "message": "Email, user name, and password are required"
        })

    existing = login_table.get_item(Key={"email": email}).get("Item")

    if existing:
        return response(409, {
            "success": False,
            "message": "User already exists"
        })

    login_table.put_item(
        Item={
            "email": email,
            "user_name": user_name,
            "password": password
        }
    )

    return response(201, {
        "success": True,
        "message": "Registration successful"
    })


def query_music(event):
    params = event.get("queryStringParameters") or {}

    title = params.get("title", "").strip()
    year = params.get("year", "").strip()
    artist = params.get("artist", "").strip()
    album = params.get("album", "").strip()

    if not title and not year and not artist and not album:
        return response(400, {
            "success": False,
            "message": "At least one field must be completed.",
            "results": []
        })

    filter_expression = None

    if title:
        filter_expression = Attr("title").contains(title)

    if year:
        condition = Attr("year").eq(year)
        filter_expression = condition if filter_expression is None else filter_expression & condition

    if artist:
        condition = Attr("artist").contains(artist)
        filter_expression = condition if filter_expression is None else filter_expression & condition

    if album:
        condition = Attr("album").contains(album)
        filter_expression = condition if filter_expression is None else filter_expression & condition

    result = music_table.scan(FilterExpression=filter_expression)
    songs = result.get("Items", [])

    for song in songs:
        song["image_url"] = generate_image_url(song.get("image_key"))

    if not songs:
        return response(200, {
            "success": False,
            "message": "No result is retrieved. Please query again",
            "results": []
        })

    return response(200, {
        "success": True,
        "message": "Results retrieved",
        "results": songs
    })


def get_subscriptions(event):
    params = event.get("queryStringParameters") or {}
    email = params.get("email", "").strip()

    if not email:
        return response(400, {
            "success": False,
            "message": "Email is required"
        })

    result = subscription_table.scan(
        FilterExpression=Attr("email").eq(email)
    )

    subscriptions = result.get("Items", [])

    for song in subscriptions:
        song["image_url"] = generate_image_url(song.get("image_key"))

    return response(200, {
        "success": True,
        "subscriptions": subscriptions
    })


def add_subscription(event):
    data = get_body(event)

    email = data.get("email")
    title = data.get("title")
    artist = data.get("artist")
    year = data.get("year")
    album = data.get("album")
    image_key = data.get("image_key")

    if not email or not title:
        return response(400, {
            "success": False,
            "message": "Email and title are required"
        })

    subscription_table.put_item(
        Item={
            "email": email,
            "title": title,
            "artist": artist,
            "year": year,
            "album": album,
            "image_key": image_key
        }
    )

    return response(201, {
        "success": True,
        "message": "Subscribed successfully"
    })


def remove_subscription(event):
    data = get_body(event)

    email = data.get("email")
    title = data.get("title")

    if not email or not title:
        return response(400, {
            "success": False,
            "message": "Email and title are required"
        })

    subscription_table.delete_item(
        Key={
            "email": email,
            "title": title
        }
    )

    return response(200, {
        "success": True,
        "message": "Subscription removed"
    })