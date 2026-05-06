from flask import Blueprint, request, jsonify, session
from boto3.dynamodb.conditions import Attr
from aws_config import (
    login_table,
    music_table,
    subscription_table,
    s3_client,
    S3_BUCKET_NAME
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ===================== HELPER =====================
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


# ===================== LOGIN =====================
@api_bp.route("/login", methods=["POST"])
def api_login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    try:
        response = login_table.get_item(Key={"email": email})

        if "Item" not in response:
            return jsonify({"success": False, "message": "User not found"}), 404

        user = response["Item"]

        if user["password"] != password:
            return jsonify({"success": False, "message": "Invalid password"}), 401

        session["email"] = email
        session["user_name"] = user["user_name"]

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user_name": user["user_name"]
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ===================== REGISTER =====================
@api_bp.route("/register", methods=["POST"])
def api_register():
    data = request.get_json()

    email = data.get("email")
    user_name = data.get("user_name")
    password = data.get("password")

    try:
        response = login_table.get_item(Key={"email": email})

        if "Item" in response:
            return jsonify({"success": False, "message": "User already exists"}), 409

        login_table.put_item(
            Item={
                "email": email,
                "user_name": user_name,
                "password": password
            }
        )

        return jsonify({
            "success": True,
            "message": "Registration successful"
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ===================== CURRENT USER =====================
@api_bp.route("/me", methods=["GET"])
def api_me():
    if "email" not in session:
        return jsonify({"logged_in": False}), 401

    return jsonify({
        "logged_in": True,
        "email": session["email"],
        "user_name": session["user_name"]
    })


# ===================== MUSIC QUERY =====================
@api_bp.route("/music", methods=["GET"])
def api_music():
    if "email" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    title = request.args.get("title", "").strip()
    year = request.args.get("year", "").strip()
    artist = request.args.get("artist", "").strip()
    album = request.args.get("album", "").strip()

    if not title and not year and not artist and not album:
        return jsonify({
            "success": False,
            "message": "At least one field must be completed.",
            "results": []
        }), 400

    try:
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

        response = music_table.scan(FilterExpression=filter_expression)
        results = response.get("Items", [])

    
        for song in results:
            song["image_url"] = generate_image_url(song.get("image_key"))

        if not results:
            return jsonify({
                "success": False,
                "message": "No result is retrieved. Please query again",
                "results": []
            })

        return jsonify({
            "success": True,
            "message": "Results retrieved",
            "results": results
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ===================== GET SUBSCRIPTIONS =====================
@api_bp.route("/subscriptions", methods=["GET"])
def api_get_subscriptions():
    if "email" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    try:
        response = subscription_table.scan(
            FilterExpression=Attr("email").eq(session["email"])
        )

        subscriptions = response.get("Items", [])

        for song in subscriptions:
            song["image_url"] = generate_image_url(song.get("image_key"))

        return jsonify({
            "success": True,
            "subscriptions": subscriptions
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ===================== SUBSCRIBE =====================
@api_bp.route("/subscriptions", methods=["POST"])
def api_subscribe():
    if "email" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json()

    try:
        subscription_table.put_item(
            Item={
                "email": session["email"],
                "title": data.get("title"),
                "artist": data.get("artist"),
                "year": data.get("year"),
                "album": data.get("album"),
                "image_key": data.get("image_key") 
            }
        )

        return jsonify({
            "success": True,
            "message": "Subscribed successfully"
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ===================== REMOVE SUBSCRIPTION =====================
@api_bp.route("/subscriptions/<title>", methods=["DELETE"])
def api_remove_subscription(title):
    if "email" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    try:
        subscription_table.delete_item(
            Key={
                "email": session["email"],
                "title": title
            }
        )

        return jsonify({
            "success": True,
            "message": "Subscription removed"
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ===================== LOGOUT =====================
@api_bp.route("/logout", methods=["POST"])
def api_logout():
    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    })