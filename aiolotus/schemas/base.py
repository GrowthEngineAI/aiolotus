import json
import httpx
import backoff
import datetime
import asyncio
import numbers
import aiohttpx

from six import string_types
from dateutil.tz import tzutc
from lazyops.types import BaseModel
from lazyops.utils import ObjectEncoder
from typing import List, Optional, Any, Dict, Type
from aiolotus.version import VERSION
from aiolotus.types.options import HttpMethod, ApiMethod
from aiolotus.types.errors import APIError, fatal_exception
from aiolotus.utils.logs import logger
from aiolotus.utils.config import settings
from aiolotus.utils.helpers import (
    stringify_id,
)
from aiolotus.utils.funcs import (
    gzipify,
    ungzipify,
)

__all__ = [
    'string_types',
    'ID_TYPES',
    'ApiModel',
    'BaseOperation',
]

ID_TYPES = (numbers.Number, string_types)

class ApiModel(BaseModel):
    """Base model for API Operations."""
    item_id: Optional[str] = None

    async def validate_params(
        self,
        api_method: ApiMethod,
        items: Optional[List[Type['ApiModel']]] = None,
        itemized: bool = False,
        **kwargs
    ) -> None:
        """Validate the message and ensure all required fields are present."""
        return
    
    async def prepare_list(
        self,
        itemized: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare the body of the LIST request."""
        return self.dict(exclude_none = True)

    async def prepare_create(
        self,
        itemized: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare the body of the CREATE request."""
        return self.dict(exclude_none = True)
    
    async def prepare_create_batch(
        self,
        items: List[Type['ApiModel']],
        itemized: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare the body of the CREATE_BATCH request."""
        data = self.dict(exclude_none = True)
        data['items'] = [item.dict(exclude_none = True) for item in items]
        return data

    async def prepare_event(
        self,
        itemized: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare the body of the EVENT request."""
        return self.dict(exclude_none = True)

    async def prepare_get(
        self,
        itemized: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare the body of the GET request."""
        return self.dict(exclude_none = True)
    
    async def prepare_get_all(
        self,
        itemized: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Prepare the body of the GET_ALL request.
        Routes to LIST method.
        """
        return await self.prepare_list(itemized = itemized, **kwargs)

    async def prepare_get_detail(
        self,
        itemized: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Prepare the body of the GET Detail request.
        Routes to GET method.
        """
        return await self.prepare_get(itemized = itemized, **kwargs)

    async def prepare_update(
        self,
        itemized: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare the body of the UPDATE request."""
        return self.dict(exclude_none = True)
    
    async def prepare_delete(
        self,
        itemized: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare the body of the DELETE request."""
        return self.dict(exclude_none = True)
    
    async def prepare_change(
        self,
        itemized: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Prepare the body of the CHANGE request.
        Routes to UPDATE method.
        """
        return await self.prepare_update(itemized = itemized, **kwargs)
    
    async def prepare_cancel(
        self,
        itemized: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Prepare the body of the CANCEL request.
        Routes to DELETE method.
        """
        return await self.prepare_delete(itemized = itemized, **kwargs)
    
    async def prepare_msg(
        self,
        api_method: ApiMethod,
        itemized: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare the body of the API request."""
        await self.validate_params(api_method = api_method, itemized = itemized, **kwargs)

        if api_method == ApiMethod.LIST:
            return await self.prepare_list(itemized = itemized, **kwargs)
        if api_method == ApiMethod.CREATE:
            return await self.prepare_create(itemized = itemized, **kwargs)
        if api_method == ApiMethod.CREATE_BATCH:
            return await self.prepare_create_batch(itemized = itemized, **kwargs)
        if api_method in {ApiMethod.EVENT, ApiMethod.TRACK}:
            return await self.prepare_event(itemized = itemized, **kwargs)
        if api_method == ApiMethod.GET:
            return await self.prepare_get(itemized = itemized, **kwargs)
        if api_method == ApiMethod.GET_ALL:
            return await self.prepare_get_all(itemized = itemized, **kwargs)
        if api_method == ApiMethod.GET_DETAIL:
            return await self.prepare_get_detail(itemized = itemized, **kwargs)
        if api_method == ApiMethod.UPDATE:
            return await self.prepare_update(itemized = itemized, **kwargs)
        if api_method == ApiMethod.DELETE:
            return await self.prepare_delete(itemized = itemized, **kwargs)
        if api_method == ApiMethod.CHANGE:
            return await self.prepare_change(itemized = itemized, **kwargs)
        if api_method == ApiMethod.CANCEL:
            return await self.prepare_cancel(itemized = itemized, **kwargs)
        raise ValueError(f"[{self.__class__.__name__}] Invalid API method: {api_method}")

    async def prepare_body(
        self,
        api_method: ApiMethod,
        itemized: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare the body of the request."""
        msg = await self.prepare_msg(api_method = api_method, itemized = itemized, **kwargs)
        msg['library'] = 'aiolotus'
        msg['library_version'] = VERSION
        if "idempotency_id" in msg: msg["idempotency_id"] = stringify_id(msg.get("idempotency_id", None))
        if "customer_id" in msg: msg["customer_id"] = stringify_id(msg.get("customer_id", None))
        return msg

class BaseOperation(BaseModel):
    url: str
    name: str
    http_method: HttpMethod
    api_method: ApiMethod
    api_model: Type[ApiModel]
    itemized: bool = False
    
    async def prepare_msg(
        self,
        **kwargs
    ) -> Dict[str, Any]:
        msg = self.api_model(**kwargs)
        return await msg.prepare_body(api_method = self.api_method, itemized = self.itemized)

    async def send(
        self, 
        client: aiohttpx.Client,
        msg: Dict[str, Any],
        headers: Dict[str, Any],
        gzip: Optional[bool] = None,
        timeout: Optional[int] = None,
        ignore_errors: Optional[bool] = None,
        **kwargs
    ) -> httpx.Response:

        # Sends the request
        endpoint_url = self.url
        if msg.get('item_id'): 
            endpoint_url += f"/{msg.get('item_id')}/"
            del msg['item_id']
        
        # request = self.prepare_request(msg, **kwargs)
        if timeout is None: timeout = settings.timeout
        if gzip is None: gzip = settings.gzip_enabled
        if ignore_errors is None: ignore_errors = settings.ignore_errors

        msg["sentAt"] = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=tzutc()).isoformat()
        data = None
        if self.http_method != HttpMethod.GET:
            data = json.dumps(msg, cls = ObjectEncoder)
            if gzip: 
                headers["Content-Encoding"] = "gzip"
                data = await gzipify(data)
        
        res = await client.async_request(
            method = self.http_method.value,
            url = endpoint_url,
            headers = headers,
            params = msg if self.http_method == HttpMethod.GET else None,
            data = data,
            timeout = timeout,
        )
        if res.status_code in [200, 201]:
            if settings.debug_enabled:
                logger.info(f"[{res.status_code}] Made API Call: {self.http_method.value} to {endpoint_url} successfully.")
            return res
        if gzip: 
            try:
                res._content = await ungzipify(res.content)
            except Exception as e:
                logger.error(f"Failed to decompress response: {e}")

        try:
            payload = res.json()
            if settings.debug_enabled:
                logger.info(f"Received response: {payload}")
            if not ignore_errors:
                raise APIError(res.status_code, payload)
            # Return it anyways
            return res
        except ValueError as e:
            logger.error(f"failed to parse response: {res.text}")
            if not ignore_errors:
                raise APIError(res.status_code, res.text) from e
            # Return it anyways
            return res

    async def retryable_send(
        self, 
        client: aiohttpx.Client,
        msg: Dict[str, Any],
        headers: Dict[str, Any],
        gzip: Optional[bool] = None,
        timeout: Optional[int] = None,
        ignore_errors: Optional[bool] = None,
        retries: Optional[int] = None,
        **kwargs
    ) -> httpx.Response:
        if retries is None: retries = settings.max_retries
        @backoff.on_exception(
            backoff.expo, Exception, max_tries = retries + 1, giveup = fatal_exception
        )
        async def _send():
            return await self.send(
                client = client, msg = msg, headers = headers, gzip = gzip, timeout = timeout, ignore_errors = ignore_errors, **kwargs
            )
        
        return await _send()

    async def enqueue(
        self,
        queue: asyncio.Queue,
        msg: Dict[str, Any],
        wait: Optional[bool] = True,
        **kwargs
    ):
        # Enqueues the request
        # returns the future
        try:
            if wait:
                await queue.put(msg)
            else:
                queue.put_nowait(msg)
            return True, msg

        except asyncio.queues.QueueFull:
            logger.error("queue is full")
            return False, msg
    
    async def execute(
        self,
        client: aiohttpx.Client,
        msg: Dict[str, Any],
        headers: Dict[str, Any],
        gzip: Optional[bool] = None,
        timeout: Optional[int] = None,
        ignore_errors: Optional[bool] = None,
        retryable: Optional[bool] = False,
        retries: Optional[int] = None,
        queue: Optional[asyncio.Queue] = None,
        blocking: Optional[bool] = True,
        wait: Optional[bool] = True,
        **kwargs
    ):
        # Executes the request
        # returns the response
        if blocking:
            if retryable:
                res = await self.retryable_send(
                    client = client, msg = msg, headers = headers, gzip = gzip, ignore_errors = ignore_errors, timeout = timeout, retries = retries, **kwargs
                )
            else:
                res = await self.send(
                    client = client, msg = msg, headers = headers, gzip = gzip, ignore_errors = ignore_errors, timeout = timeout, **kwargs
                )
            try:
                return res.json()
            except Exception as e:
                return res.text
        
        return await self.enqueue(
            queue = queue, msg = msg, wait = wait, **kwargs
        )
