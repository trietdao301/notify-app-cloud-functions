from firebase_admin import firestore
from firebase_admin import messaging, exceptions
from typing import Dict, List, Any
from models.property_notification import PropertyNotification, ChangeType, Change

def sendPushNotifications(
    changes_payload: Dict[str, Change], property_id: str
) -> None:
    """Send Push Notification using FCM"""
    changes_payload = payloadToString(changes_payload)
    sendToFieldSpecificTopics(changes_payload, property_id)
    sendToAllFieldTopic(changes_payload, property_id)


def sendToFieldSpecificTopics(changes_payload: Dict[str, str], property_id: str):
    try:
        changes_payload["propertyId"] = property_id
        for key, value in changes_payload.items():
            if(key == "propertyId"):
                continue
            topic_field_specific = f"property_{property_id}_{key}"
            message_field_specific = messaging.Message(
                data=changes_payload,
                topic=topic_field_specific,
            )
            response = messaging.send(message_field_specific)
            print(
                f"Successfully sent notification to topic {topic_field_specific}: {response}"
            )
    except Exception as e:
        raise e


def sendToAllFieldTopic(changes_payload: Dict[str, str], property_id: str):
    try:
        topic_all_fields = f"property_{property_id}_all"
        message = messaging.Message(
            data=changes_payload,
            topic=topic_all_fields,
        )
        response = messaging.send(message)
        print(f"Successfully sent notification to topic {topic_all_fields}: {response}")
    except Exception as e:
        raise e


def payloadToString(payload: Dict[str, Change]) -> Dict[str, str]:
    dict_payload = {}
    for key, value in payload.items():
        if value.type == ChangeType.REMOVED:
            dict_payload[key] = "Removed"
        elif value.type == ChangeType.ADDED:
            dict_payload[key] = f"New Attribute: {value.new_value}"
        elif value.type == ChangeType.UPDATED:
            dict_payload[key] = (
                f"Updated attribute from {value.old_value} to {value.new_value}"
            )
    return dict_payload
