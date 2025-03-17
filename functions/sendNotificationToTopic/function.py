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
from sendNotificationToTopic.helpers.buildNotification import buildNotificationChangePayload
from sendNotificationToTopic.helpers.createInAppNotification import createInAppNotifications
from sendNotificationToTopic.helpers.sendPushNotification import sendPushNotifications



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