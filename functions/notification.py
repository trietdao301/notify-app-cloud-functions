import copy
from firebase_admin import messaging, exceptions
from firebase_functions.firestore_fn import (
    on_document_updated,
    Event,
    DocumentSnapshot,
)
from firebase_admin import firestore
from datetime import datetime, timezone
from typing import Dict, List, Any
from models.property_notification import Change, ChangeType, PropertyNotification


@on_document_updated(document="properties/{propertyId}")
def sendNotificationToTopic(event: Event[DocumentSnapshot]) -> None:
    """
    Purpose:

    1. Sends a push notification to relevant FCM topics based on the property ID
    and notification preference (propertyField).
    2. Creates an in-app notification entry in "property_notification" collection.

    Triggered by:
    1. Changes in "properties" collection.

    Note:
    1. Topic name format is   ***property_{propertyId}_{propertyField}***
    2. If user chooses to subscribe to all fields, then topic format:
    property_{propertyId}_all

    Example: property_property1_deed, property_property2_all.
    """
    property_id = event.params["propertyId"]
    data = event.data

    new_property_data = data.after.to_dict()
    old_property_data = data.before.to_dict()
    if new_property_data == old_property_data:
        print(f"Property {property_id} is unchanged. No notification is sent.")
        return
    payload = buildNotificationChangePayload(
        new_object=new_property_data,
        old_object=old_property_data,
        property_id=property_id,
    )

    try:
        payload_copy = copy.deepcopy(payload)
        sendPushNotifications(payload, property_id)
        createInAppNotifications(payload_copy, property_id)

    except Exception as e:
        print(f"Error: {e}")


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


def sendPushNotifications(
    changes_payload: Dict[str, Change], property_id: str
) -> None:
    """Send Push Notification using FCM"""
    changes_payload = payloadToString(changes_payload)
    sendToFieldSpecificTopics(changes_payload, property_id)
    sendToAllFieldTopic(changes_payload, property_id)


def ChangeAndPreferenceUnion(
    changes_payload: Dict[str, Change], preferences: List[str]
) -> Dict[str, Change]:
    if changes_payload is None:
        raise Exception(
            "Unexpected error: changing payload is None, when a change is detected"
        )
    if preferences is None:
        raise Exception("alertPreference is None while isSubscribed is True")
    result: Dict[str, Change] = {}
    for key, value in changes_payload.items():
        if key in preferences:
            result.update({key: value})
    return result


def createInAppNotifications(
    change_payload: Dict[str, Change], property_id: str
) -> None:
    """
    Add new notification documents to property_notification collection in firestore.
    The number of user subscribes to this propperty = The number of notification created.
    """
    db = firestore.client()
    subscriptions_of_this_property = (
        db.collection("subscriptions")
        .where("propertyId", "==", property_id)
        .where("isSubscribed", "==", True)
        .stream()
    )

    dt = datetime.now(timezone.utc)
    current_time_in_milliseconds = int(dt.timestamp() * 1000)
    for sub in subscriptions_of_this_property:
        sub_data = sub.to_dict()
        matched_changes: Dict[str, Change] = ChangeAndPreferenceUnion(
            change_payload, sub_data.get("alertPreferences")
        )
        if(len(matched_changes) == 0):
            continue
        notification = PropertyNotification(
            propertyId=property_id,
            createdAt=current_time_in_milliseconds,
            changes=matched_changes,
            userId=sub_data.get("userId"),
            isRead=False,
            readAt=None,
        )
        try:
            db.collection("property_notifications").add(notification.to_firestore())
        except Exception as e:
            raise e


def buildNotificationChangePayload(
    new_object: Dict[str, Any], old_object: Dict[str, Any], property_id: str
) -> Dict[str, Change]:
    """Take two property objects and return their differences.

    Args:
        new_object (Dict[str, Any]): Updated property object.
        old_object (Dict[str, Any]): Original property object.

    Returns:
        Dict[str, Change]

    Example:
    {"book": Change(ChangeType.UPDATED, old_value, new_value),
    "deed" : Change(ChangeType.ADDED, None, new_value)}
    """
    if property_id != new_object.get("documentId") or new_object.get(
        "documentId"
    ) != old_object.get("documentId"):
        raise Exception("Property IDs don't match")

    changes_payload: Dict[str, Change] = {}

    if new_object != old_object:
        # Check for new or updated attributes
        for new_key, new_value in new_object.items():
            is_new_field = (old_object.get(new_key) is None) and (new_value is not None)
            if is_new_field:
                change = Change(
                    type=ChangeType.ADDED, old_value=None, new_value=new_value
                )
                data_to_add = {new_key: change}
                changes_payload.update(data_to_add)
                continue
            is_updating_field = new_value != old_object.get(new_key)
            if is_updating_field:
                old_value = old_object.get(new_key)
                change = Change(
                    type=ChangeType.UPDATED, old_value=old_value, new_value=new_value
                )
                data_to_add = {new_key: change}
                changes_payload.update(data_to_add)
               

        # Check for removed attributes
        is_removing_field = changes_payload == {}
        if is_removing_field:
            removed_keys = old_object.keys() - new_object.keys()
            for key in removed_keys:
                change = Change(
                    type=ChangeType.REMOVED,
                    old_value=old_object.get(key),
                    new_value=None,
                )
                data_to_add = {key: change}
                changes_payload.update(data_to_add)
               
    return changes_payload


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
