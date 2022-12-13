
import datetime
from typing import Optional, Union, List, Type
from aiolotus.utils import require
from aiolotus.types.options import ReplaceType
from aiolotus.schemas.base import ApiModel, ApiMethod, ID_TYPES


__all__ = [
    'LotusSubscription',
]

class LotusSubscription(ApiModel):
    customer_id: Optional[str] = None
    plan_id: Optional[str] = None
    start_date: Optional[Union[datetime.datetime, str]] = None
    end_date: Optional[Union[datetime.datetime, str]] = None
    auto_renew: Optional[bool] = None
    is_new: Optional[bool] = None
    subscription_id: Optional[str] = None
    status: Optional[str] = None

    turn_off_auto_renew: Optional[bool] = None
    replace_immediately_type: Optional[ReplaceType] = None

    async def validate_params(
        self,
        api_method: ApiMethod,
        items: Optional[List[Type['LotusSubscription']]] = None,
        itemized: bool = False,
        **kwargs
    ) -> None:
        """Validate the message and ensure all required fields are present."""

        if api_method == ApiMethod.CREATE:
            require("customer_id", self.customer_id, ID_TYPES)
            require("plan_id", self.plan_id, ID_TYPES)
            if self.start_date and isinstance(self.start_date, datetime.datetime):
                self.start_date = self.start_date.strftime("%Y-%m-%d")
            if self.end_date and isinstance(self.end_date, datetime.datetime):
                self.end_date = self.end_date.strftime("%Y-%m-%d")
            require("start_date", self.start_date, ID_TYPES)
        
        if api_method == ApiMethod.CANCEL:
            assert (
                self.turn_off_auto_renew is True or self.replace_immediately_type is not None
            ), "Must provide either turn_off_auto_renew or replace_immediately_type"
            if self.turn_off_auto_renew is None:
                self.replace_immediately_type = self.replace_immediately_type.value
            
            if self.turn_off_auto_renew:
                self.auto_renew = False
            else:
                self.status = "ended"
            
        if api_method == ApiMethod.CHANGE:
            require("plan_id", self.plan_id, ID_TYPES)
        
        # if api_method in {ApiMethod.GET, ApiMethod.GET_DETAIL, ApiMethod.CANCEL, ApiMethod.CHANGE}:
        #    require("subscription_id", self.subscription_id, ID_TYPES)
        
        if api_method in {ApiMethod.GET, ApiMethod.GET_DETAIL, ApiMethod.UPDATE, ApiMethod.DELETE, ApiMethod.CHANGE, ApiMethod.CANCEL}:
            require("subscription_id", self.subscription_id, ID_TYPES)
            self.item_id = self.subscription_id
