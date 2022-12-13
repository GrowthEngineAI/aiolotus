from typing import Optional, Dict, List, Type
from aiolotus.utils import require
from aiolotus.types.options import PaymentProvider, ExistingCustomerBehavior
from aiolotus.schemas.base import ApiModel, ApiMethod, ID_TYPES


__all__ = [
    'LotusCustomer',
]

class LotusCustomer(ApiModel):
    customer_name: Optional[str] = None
    customer_id: Optional[str] = None
    email: Optional[str] = None
    payment_provider: Optional[PaymentProvider] = PaymentProvider.stripe
    payment_provider_id: Optional[str] = None
    properties: Optional[Dict] = {}
    behavior_on_existing: Optional[ExistingCustomerBehavior] = None

    async def validate_params(
        self,
        api_method: ApiMethod,
        items: Optional[List[Type['LotusCustomer']]] = None,
        itemized: bool = False,
        **kwargs
    ) -> None:
        """Validate the message and ensure all required fields are present."""

        if api_method == ApiMethod.CREATE:
            require("customer_id", self.customer_id, ID_TYPES)
            require("email", self.customer_name, ID_TYPES)
        
        if api_method == ApiMethod.CREATE_BATCH:
            require("items", items, list)
            for item in items:
                require("customer_id", item.customer_id, ID_TYPES)
                require("email", item.customer_name, ID_TYPES)
            require("behavior_on_existing", self.behavior_on_existing.value, ID_TYPES)


        if api_method in {ApiMethod.GET, ApiMethod.GET_DETAIL, ApiMethod.UPDATE, ApiMethod.DELETE, ApiMethod.CHANGE, ApiMethod.CANCEL}:
            self.item_id = self.customer_id

