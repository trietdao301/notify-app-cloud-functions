from dataclasses import dataclass, asdict
from datetime import datetime
from google.cloud import firestore
from typing import Optional, Dict, Any, Union
from enum import Enum

class ChangeType(Enum):
    UPDATED = "updated"
    ADDED = "added"
    REMOVED = "removed"

@dataclass
class Change:
    type: ChangeType
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None

    def to_firestore(self) -> Dict[str, Any]:
        result = {'type': self.type.value}
        if self.old_value is not None:
            result['old_value'] = self.old_value
        if self.new_value is not None:
            result['new_value'] = self.new_value
        return result

    @classmethod
    def from_firestore(cls, data: Dict[str, Any]) -> 'Change':
        return cls(
            type=ChangeType(data['type']),
            old_value=data.get('old_value'),
            new_value=data.get('new_value'),
        )

@dataclass
class PropertyNotification:
    """A notification representing changes to a property.

    Example:
        notification = PropertyNotification(
            propertyId="12345",
            createdAt=int(datetime.now().timestamp() * 1000),
            changes={
                "book": Change(ChangeType.UPDATED, old_value="45", new_value="46"),
                "page": Change(ChangeType.ADDED, new_value="12"),
            },
            userId="user123",
        )
    """
    propertyId: str
    createdAt: int
    changes: Dict[str, Change]
    userId: Optional[str] = None
    isRead: bool = False
    readAt: Optional[int] = None

    _valid_fields = {
        "recordingDate", "lastNameOrCorpName", "firstName", "middleName", "generation",
        "role", "partyType", "grantorOrGrantee", "book", "page", "itemNumber",
        "instrumentTypeCode", "instrumentTypeName", "parcelId", "referenceBook",
        "referencePage", "remark1", "remark2", "instrumentId", "returnCode",
        "numberOfAttempts", "insertTimestamp", "editFlag", "version", "attempts",
    }

    def __post_init__(self):
        self.changes = self._validate_changes(self.changes)

    @classmethod
    def _validate_changes(cls, changes: Dict[str, Change]) -> Dict[str, Change]:
        """Validate changes against valid Property fields."""
        invalid_keys = [key for key in changes.keys() if key not in cls._valid_fields]
        if invalid_keys:
            raise ValueError(f"Invalid field(s) in changes: {', '.join(invalid_keys)}")
        return dict(changes)  # Return a copy to ensure immutability

    def to_firestore(self) -> Dict[str, Any]:
        """Convert to Firestore-compatible dictionary using dataclass fields."""
        base_dict = asdict(self, dict_factory=lambda x: {k: v for k, v in x if v is not None})
        base_dict['changes'] = {key: value.to_firestore() for key, value in self.changes.items()}
        return base_dict

    @classmethod
    def from_firestore(cls, data: Dict[str, Any], doc_id: Optional[str] = None) -> 'PropertyNotification':
        """Create from Firestore data with type conversion."""
        changes_raw = data.get('changes', {}) or {}
        changes = {key: Change.from_firestore(value) for key, value in changes_raw.items()}
        return cls(
            propertyId=data['propertyId'],
            createdAt=cls._parse_timestamp(data['createdAt']),
            changes=changes,
            userId=data.get('userId'),
            isRead=data.get('isRead', False),
            readAt=cls._parse_timestamp(data['readAt']) if data.get('readAt') is not None else None,
        )

    @staticmethod
    def _parse_timestamp(value: Any) -> int:
        if isinstance(value, int):
            return value
        elif isinstance(value, float):
            return round(value)
        elif isinstance(value, firestore.Timestamp):
            return int(value.timestamp() * 1000)
        return int(datetime.now().timestamp() * 1000)