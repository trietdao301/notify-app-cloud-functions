from models.property_notification import PropertyNotification, ChangeType, Change
from typing import Dict, List, Any
from firebase_admin import firestore
from datetime import datetime, timezone

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


