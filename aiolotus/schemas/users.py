from typing import Optional, List, Type
from aiolotus.utils import require
from aiolotus.schemas.base import ApiModel, ApiMethod, ID_TYPES, string_types

__all__ = [
    'LotusUser',
]


class LotusUser(ApiModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    company_name: Optional[str] = None
    organization_id: Optional[str] = None

    async def validate_params(
        self,
        api_method: ApiMethod,
        items: Optional[List[Type['LotusUser']]] = None,
        itemized: bool = False,
        **kwargs
    ) -> None:
        """Validate the message and ensure all required fields are present."""
        if api_method in {ApiMethod.CREATE}:
            require("email", self.email, string_types)
            require("username", self.username, string_types)
            require("company_name", self.company_name, string_types)
            require("organization_id", self.organization_id, ID_TYPES)
        
        if api_method in {ApiMethod.GET, ApiMethod.GET_DETAIL, ApiMethod.UPDATE, ApiMethod.DELETE, ApiMethod.CHANGE}:
            require("user_id", self.user_id, ID_TYPES)
            self.item_id = self.user_id
