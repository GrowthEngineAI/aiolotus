
import json
import gzip
import httpx
import backoff
import asyncio
import functools
import aiohttpx
import datetime
from dateutil.tz import tzutc
from io import BytesIO
from concurrent import futures
from lazyops.utils import ObjectEncoder
from typing import Union, Callable, Dict, Optional, Any

from aiolotus.utils.config import settings
from aiolotus.utils.logs import logger
from aiolotus.types.errors import APIError, fatal_exception


__all__ = [
    'async_run',
    'gzip_data',
    'ungzip_data',
    'gzipify',
    'ungzipify',
    'async_request',
    'retryable_async_request',
    'ObjectEncoder'
]

_threadpool: futures.ThreadPoolExecutor = None

def _get_pool():
    global _threadpool
    if _threadpool is None:
        
        _threadpool = futures.ThreadPoolExecutor(max_workers = settings.num_pool_workers or settings.num_workers)
    return _threadpool

async def async_run(sync_func: Callable, *args, **kwargs):
    """
    Runs a Sync Function as an Async Function
    """
    blocking = functools.partial(sync_func, *args, **kwargs)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_get_pool(), blocking)


def gzip_data(
    data: str,
    **kwargs,
):
    buf = BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="w") as gz:
        gz.write(data.encode("utf-8"))
    return buf.getvalue()

def ungzip_data(data: bytes) -> bytes:
    return gzip.decompress(data)

async def gzipify(
    data: str,
    **kwargs,
):
    return await async_run(gzip_data, data, **kwargs)

async def ungzipify(
    data: bytes,
    **kwargs,
):
    return await async_run(ungzip_data, data, **kwargs)


async def async_request(
    client: aiohttpx.Client,
    headers: Dict[str, Any],
    endpoint: Optional[str] = None,
    gzip: Optional[bool] = None,
    timeout: Optional[int] = None,
    ignore_errors: Optional[bool] = None,
    body: Optional[Any] = None,
    method: Optional[str] = 'GET',
) -> httpx.Response:

    """
    Build a request to the API and return the response.
    """
    if body is None: body = {}
    if timeout is None: timeout = settings.timeout
    if gzip is None: gzip = settings.gzip_enabled
    if ignore_errors is None: ignore_errors = settings.ignore_errors

    body["sentAt"] = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=tzutc()).isoformat()
    data = json.dumps(body, cls = ObjectEncoder)
    if gzip: 
        headers["Content-Encoding"] = "gzip"
        #if settings.debug_enabled:
        #    logger.info(f"Headers: {headers}")
        data = await gzipify(data)
    res = await client.async_request(
        method = method,
        url = endpoint,
        headers = headers,
        params = body if method == 'GET' else None,
        data = data if method != 'GET' else None,
        timeout = timeout,
    )
    if res.status_code in [200, 201]:
        if settings.debug_enabled:
            logger.info(f"[{res.status_code}] Made API Call: {method} to {endpoint} successfully.")
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
        return res
    except ValueError as e:
        logger.error(f"failed to parse response: {res.text}")
        if not ignore_errors:
            raise APIError(res.status_code, res.text) from e
        return res


async def retryable_async_request(
    client: aiohttpx.Client,
    headers: Dict[str, Any],
    endpoint: Optional[str] = None,
    gzip: Optional[bool] = None,
    timeout: Optional[int] = None,
    ignore_errors: Optional[bool] = None,
    body: Optional[Dict] = None,
    method: Optional[str] = 'GET',
    retries: Optional[int] = None,
) -> httpx.Response:
    if retries is None: retries = settings.max_retries
    @backoff.on_exception(
        backoff.expo, Exception, max_tries = retries + 1, giveup = fatal_exception
    )
    async def _retryable_async_request():
        return await async_request(
            client = client,
            headers = headers,
            endpoint = endpoint,
            gzip = gzip,
            timeout = timeout,
            ignore_errors = ignore_errors,
            body = body,
            method = method,
        )
    
    return await _retryable_async_request()