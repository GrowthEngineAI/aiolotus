import time
import json
import aiohttpx
import asyncio

from typing import Optional, Dict, Any, Callable, List
from aiolotus.utils import (
    logger, 
    settings, 
    retryable_async_request, 
    ObjectEncoder
)

class LotusWorker:
    """Consumes the messages from the client's queue."""

    def __init__(
        self,
        queue: asyncio.Queue,
        client: aiohttpx.Client,
        headers: Dict[str, Any],
        endpoint: str = '/api/track/',
        flush_at: Optional[int] = None,
        on_error: Optional[Callable] = None,
        flush_interval: Optional[float] = None,
        gzip: Optional[bool] = None,
        retries: Optional[int] = None,
        timeout: Optional[int] = None,
        debug_enabled: Optional[bool] = None,
        worker_id: Optional[int] = None,

        batch_size_limit: Optional[int] = None,
        max_msg_size: Optional[int] = None,
        # operation: Any = None, #??
        **kwargs
    ):
        """
        Create a consumer worker for events.
        
        Currently only supports Events API
        """
        self.queue = queue
        self.client = client
        self.headers = headers
        self.endpoint = endpoint
                
        self.flush_at = flush_at if flush_at is not None else settings.worker.flush_at
        self.flush_interval = flush_interval if flush_interval is not None else settings.worker.flush_interval
        self.gzip = gzip if gzip is not None else settings.gzip_enabled
        self.retries = retries if retries is not None else settings.max_retries
        self.timeout = timeout if timeout is not None else settings.timeout
        self.debug_enabled = debug_enabled if debug_enabled is not None else settings.debug_enabled
        self.on_error = on_error
        self.running = True

        self.batch_size_limit = batch_size_limit if batch_size_limit is not None else settings.worker.batch_size_limit
        self.max_msg_size = max_msg_size if max_msg_size is not None else settings.worker.max_msg_size

        self.worker_id = worker_id
        self.log_method = logger.info if self.debug_enabled else logger.debug

    async def run(self):
        """Start the consumer worker."""
        self.log_method(f'Starting Worker [{self.worker_id}]')
        while self.running:
            await self.upload()
        self.log_method(f'Exiting Worker [{self.worker_id}]')
    

    def pause(self):
        """Pause the consumer."""
        self.log_method(f'Pausing Worker [{self.worker_id}]')
        self.running = False


    async def request(self, batch: List[str]):
        """Send a request to the server."""
        
        # self.log_method(f'Worker [{self.worker_id}] Sending Batch: {batch}')
        return await retryable_async_request(
            client = self.client,
            gzip = self.gzip,
            endpoint = self.endpoint,
            headers = self.headers,
            timeout = self.timeout,
            body = {"batch": batch},
            method = 'POST',
            retries = self.retries
        )
    

    async def upload(self):
        """Upload the next batch of items, return whether successful."""
        success = False
        batch = await self.next()
        if len(batch) == 0: return False
        try:
            await self.request(batch)
            success = True
        except Exception as e:
            logger.error(f"Error uploading: {e}")
            success = False
            if self.on_error:
                if asyncio.iscoroutinefunction(self.on_error):
                    await self.on_error(e, batch)
                else:
                    self.on_error(e, batch)
        finally:
            # mark items as acknowledged from queue
            self.log_method(f'Worker [{self.worker_id}] Acknowledging {len(batch)} items')
            for _ in batch:
                self.queue.task_done()
            return success
    
    async def next(self):
        """Return the next batch of items to upload."""
        items = []
        start_time = time.monotonic()
        total_size = 0

        while self.running and len(items) < self.flush_at:
            elapsed = time.monotonic() - start_time
            if elapsed >= self.flush_interval: break
            # if not self.running: break
            
            try:
                item = await self.queue.get()
                item_size = len(json.dumps(item, cls = ObjectEncoder).encode())
                if item_size > self.max_msg_size:
                    logger.error("Item exceeds 32kb limit, dropping. (%s)", str(item))
                    continue
                items.append(item)
                total_size += item_size
                if total_size >= self.batch_size_limit:
                    self.log_method(f'Worker [{self.worker_id}] Batch size limit reached (size {total_size})')
                    break
            
            except asyncio.queues.QueueEmpty:
                break

        return items