import json
import os
from urllib.parse import urlparse

import boto3
import requests
from botocore.exceptions import ClientError


REGION_NAME = "us-east-1"
BUCKET_NAME = "music-artist-images-79"
TABLE_NAME = "music"
S3_FOLDER = "artist-images"


session = boto3.Session(region_name=REGION_NAME)

dynamodb = session.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

s3 = session.client("s3")


def create_bucket_if_not_exists():
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        print(f"S3 bucket already exists: {BUCKET_NAME}")
    except ClientError:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"S3 bucket created: {BUCKET_NAME}")


def get_filename(image_url, artist, album, title):
    filename = os.path.basename(urlparse(image_url).path)

    if not filename:
        filename = f"{artist}_{album}_{title}.jpg"

    filename = filename.replace(" ", "_").replace("/", "_")
    return filename


def upload_image_to_s3(image_url, artist, album, title):
    if not image_url:
        return None

    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        filename = get_filename(image_url, artist, album, title)
        s3_key = f"{S3_FOLDER}/{filename}"

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=response.content,
            ContentType="image/jpeg"
        )

        return s3_key

    except Exception as e:
        print(f"Image upload failed for {artist} - {title}: {e}")
        return None


def clean_song_item(song, image_key):
    item = song.copy()

    artist = item.get("artist", "unknown_artist")
    album = item.get("album", "unknown_album")
    title = item.get("title", "unknown_title")

    # Composite sort key for DynamoDB
    item["album_title"] = f"{album}#{title}"

    # Remove raw/external image URL columns
    item.pop("img_url", None)
    item.pop("image", None)
    item.pop("image_url", None)

    # Store only S3 image key
    item["image_key"] = image_key

    # Remove None values because DynamoDB does not accept None
    item = {key: value for key, value in item.items() if value is not None}

    return item


def load_songs(file_path):
    try:
        create_bucket_if_not_exists()

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        songs_list = data["songs"]

        for song in songs_list:
            try:
                artist = song.get("artist", "unknown_artist")
                album = song.get("album", "unknown_album")
                title = song.get("title", "unknown_title")

                image_url = (
                    song.get("img_url")
                    or song.get("image_url")
                    or song.get("image")
                )

                image_key = upload_image_to_s3(image_url, artist, album, title)

                clean_item = clean_song_item(song, image_key)

                table.put_item(Item=clean_item)

                print(f"Loaded: {artist} - {album} - {title}")

            except Exception as e:
                print(f"Skipped song: {song.get('title')} - Error: {e}")

        print(f"Successfully loaded {len(songs_list)} songs into the music table.")

    except FileNotFoundError:
        print("Error: 2026a2_songs.json not found. Check your file path.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    load_songs("2026a2_songs.json")