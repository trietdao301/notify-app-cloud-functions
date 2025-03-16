
from typing import Dict, List, Any
from models.property_notification import Change, ChangeType


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