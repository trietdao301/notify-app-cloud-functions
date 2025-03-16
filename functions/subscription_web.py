from firebase_admin import messaging
import logging
from firebase_functions import https_fn
from flask import jsonify, request, Response

@https_fn.on_request()
def subscribeToTopic(req: https_fn.Request) -> Response:
    # Handle CORS preflight request
    if req.method == "OPTIONS":
        return Response(
            status=204,
            headers={
                "Access-Control-Allow-Origin": "*",  # Allow all origins
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Max-Age": "3600",
            },
        )

    # Add CORS headers to the response
    response_headers = {
        "Access-Control-Allow-Origin": "*",  # Allow all origins
    }

    try:
        # Log the request headers for debugging
        logging.info(f"Request headers: {req.headers}")

        # Parse the JSON body
        data = req.get_json(silent=True) or {}
        if not data:
            raise ValueError("Request body must be JSON")

        fcm_token = data.get("fcmToken")
        topic = data.get("topic")

        # Validate input
        if not isinstance(fcm_token, str) or not fcm_token:
            raise ValueError("fcmToken must be a non-empty string")
        if not isinstance(topic, str) or not topic:
            raise ValueError("topic must be a non-empty string")

        response = messaging.subscribe_to_topic(fcm_token, topic)
        logging.info(f"Subscribed {fcm_token} to topic {topic}")

        return jsonify({
            "success": True,
            "message": f"Subscribed {fcm_token} to {topic}",
            "response": str(response)
        }), 200, response_headers

    except ValueError as ve:
        logging.error(f"Invalid request: {str(ve)}")
        return jsonify({"error": str(ve)}), 400, response_headers
    except Exception as e:
        logging.error(f"Error subscribing to topic: {str(e)}")
        return jsonify({"error": "Failed to subscribe to topic"}), 500, response_headers
    

@https_fn.on_request()
def unsubscribeFromTopic(req: https_fn.Request) -> Response:
    # Handle CORS preflight request
    if req.method == "OPTIONS":
        return Response(
            status=204,
            headers={
                "Access-Control-Allow-Origin": "*",  # Allow all origins
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Max-Age": "3600",
            },
        )

    # Add CORS headers to the response
    response_headers = {
        "Access-Control-Allow-Origin": "*",  # Allow all origins
    }

    try:
        # Log the request headers for debugging
        logging.info(f"Request headers: {req.headers}")

        # Parse the JSON body
        data = req.get_json(silent=True) or {}
        if not data:
            raise ValueError("Request body must be JSON")

        fcm_token = data.get("fcmToken")
        topic = data.get("topic")

        # Validate input
        if not isinstance(fcm_token, str) or not fcm_token:
            raise ValueError("fcmToken must be a non-empty string")
        if not isinstance(topic, str) or not topic:
            raise ValueError("topic must be a non-empty string")

        response = messaging.unsubscribe_from_topic(fcm_token, topic)
        logging.info(f"Unsubscribed {fcm_token} to topic {topic}")

        return jsonify({
            "success": True,
            "message": f"Unsubscribed {fcm_token} to {topic}",
            "response": str(response)
        }), 200, response_headers

    except ValueError as ve:
        logging.error(f"Invalid request: {str(ve)}")
        return jsonify({"error": str(ve)}), 400, response_headers
    except Exception as e:
        logging.error(f"Error unsubscribing to topic: {str(e)}")
        return jsonify({"error": "Failed to unsubscribe to topic"}), 500, response_headers