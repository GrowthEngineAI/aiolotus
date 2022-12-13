import uuid
import datetime
from dateutil.tz import tzutc
from typing import Optional, Dict, Any, List, Type
from aiolotus.utils import require
from aiolotus.schemas.base import ApiModel, ApiMethod, ID_TYPES, string_types

__all__ = [
    'LotusEvent',
]

class LotusEvent(ApiModel):
    customer_id: Optional[str] = None
    event_name: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    time_created: Optional[datetime.datetime] = None
    idempotency_id: Optional[str] = None

    async def validate_params(
        self,
        api_method: ApiMethod,
        items: Optional[List[Type['LotusEvent']]] = None,
        itemized: bool = False,
        **kwargs
    ) -> None:
        """Validate the message and ensure all required fields are present."""

        if api_method not in {ApiMethod.EVENT, ApiMethod.TRACK}:
            return
        
        if self.properties is None: self.properties = {}
        if self.idempotency_id is None:
            self.idempotency_id = str(uuid.uuid4())
        if self.time_created is None:
            self.time_created = datetime.datetime.now(tzutc())
        if isinstance(self.time_created, datetime.datetime):
            self.time_created = self.time_created.isoformat()

        require("customer_id", self.customer_id, ID_TYPES)
        require("idempotency_id", self.idempotency_id, ID_TYPES)
        require("properties", self.properties, dict)
        require("event_name", self.event_name, string_types)
        require("time_created", self.time_created, string_types)

