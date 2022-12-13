from typing import Optional, Dict, List, Type
from aiolotus.utils import require
from aiolotus.types.options import PlanDuration, PlanStatus
from aiolotus.types.plans import (
    PlanExternalLink,
    PlanVersion
)
from aiolotus.schemas.base import ApiModel, ApiMethod, ID_TYPES

__all__ = [
    'LotusPlan',
]

class LotusPlan(ApiModel):
    plan_name: Optional[str] = None
    plan_duration: Optional[PlanDuration] = None
    plan_id: Optional[str] = None
    product_id: Optional[str] = None

    status: Optional[PlanStatus] = None
    initial_external_links: Optional[List[PlanExternalLink]] = None
    initial_version: Optional[PlanVersion] = None
    parent_plan_id: Optional[str] = None
    target_customer_id: Optional[str] = None

    async def validate_params(
        self,
        api_method: ApiMethod,
        items: Optional[List[Type['LotusPlan']]] = None,
        itemized: bool = False,
        **kwargs
    ) -> None:
        """Validate the message and ensure all required fields are present."""

        if api_method in {ApiMethod.CREATE, ApiMethod.UPDATE} and self.plan_duration is None: 
            self.plan_duration = PlanDuration.monthly
        
        if api_method in {ApiMethod.CREATE}:
            if self.initial_version is None: self.initial_version = PlanVersion()
            require("plan_name", self.plan_name, str)
        
        if api_method in {ApiMethod.GET, ApiMethod.GET_DETAIL, ApiMethod.UPDATE, ApiMethod.DELETE, ApiMethod.CHANGE}:
            require("plan_id", self.plan_id, ID_TYPES)
            self.item_id = self.plan_id