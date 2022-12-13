import asyncio
import datetime
import aiohttpx
import functools

from typing import Optional, Dict, Any, Callable, List, Union
from lazyops.utils import is_coro_func, timer
from aiolotus.utils import logger, settings
from aiolotus.utils.helpers import full_name
from aiolotus.worker import LotusWorker
from aiolotus.operations import APIOperation
from aiolotus.types import *
from aiolotus.schemas import *



class LotusClient:
    """Create a new Lotus client."""
    def __init__(
        self,
        apikey: Optional[str] = None,
        url: Optional[str] = None,
        scheme: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        debug_enabled: Optional[bool] = None,
        max_queue_size: Optional[int] = None,
        on_error: Optional[Callable] = None,
        flush_at: Optional[int] = None,
        flush_interval: Optional[float] = None,
        gzip: Optional[bool] = None,
        max_retries: Optional[int] = None,
        workers_enabled: Optional[bool] = None,

        timeout: Optional[int] = None,
        apikey_header: Optional[str] = None,

        num_workers: Optional[int] = None,
        worker_batch_limit_size: Optional[int] = None,
        worker_max_msg_size: Optional[int] = None,
        ignore_errors: Optional[bool] = None,
        **kwargs
    ):

        self.apikey = apikey if apikey is not None else settings.apikey
        self.api_url = settings.get_api_url(host = host, port = port, scheme = scheme, url = url)
        
        self.debug_enabled = debug_enabled if debug_enabled is not None else settings.debug_enabled
        self.max_queue_size = max_queue_size if max_queue_size is not None else settings.worker.max_queue_size
        
        self.flush_at = flush_at if flush_at is not None else settings.worker.flush_at
        self.flush_interval = flush_interval if flush_interval is not None else settings.worker.flush_interval
        self.gzip = gzip if gzip is not None else settings.gzip_enabled
        self.max_retries = max_retries if max_retries is not None else settings.max_retries

        self.workers_enabled = workers_enabled if workers_enabled is not None else settings.worker.enabled
        # self.sync_mode = sync_mode if sync_mode is not None else settings.lotus.sync_enabled
        self.timeout = timeout if timeout is not None else settings.timeout
        # self.threads = threads if threads is not None else settings.lotus.threads
        self.num_workers = num_workers if num_workers is not None else settings.num_workers
        self.ignore_errors = ignore_errors if ignore_errors is not None else settings.ignore_errors

        self.on_error = on_error

        self.queue: asyncio.Queue = None
        self.headers = settings.get_headers(apikey = self.apikey, apikey_header = apikey_header)
        # self.loop = asyncio.get_running_loop()
        self.log_method = logger.info if self.debug_enabled else logger.debug

        self.client = aiohttpx.Client(
            base_url = self.api_url,
            timeout = self.timeout,
        )
        self.tasks: List[asyncio.Task] = []
        self.workers: List[LotusWorker] = []
        self.workers_started: bool = False
        self.worker_kwargs: Dict[str, Any] = kwargs or {}
        self.worker_batch_limit_size = worker_batch_limit_size
        self.worker_max_msg_size = worker_max_msg_size
        #if self.workers_enabled:
        #    self.initialize_workers(batch_limit_size = worker_batch_limit_size, max_msg_size = worker_max_msg_size, **kwargs)
        #    # self.start_workers(**kwargs)
        logger.info(f"Lotus client initialized: {self.client.base_url}: Debug Enabled: {self.debug_enabled}")

    def initialize_workers(
        self, 
        batch_limit_size: Optional[int] = None,
        max_msg_size: Optional[int] = None,
        **kwargs
    ):
        if self.workers: 
            logger.error('Workers already initialized')
            return
        if not self.queue:
            
            self.queue = asyncio.Queue(maxsize = self.max_queue_size)
        self.log_method(f'Starting {self.num_workers} Lotus Workers')
        batch_limit_size = batch_limit_size if batch_limit_size is not None else self.worker_batch_limit_size
        max_msg_size = max_msg_size if max_msg_size is not None else self.worker_max_msg_size

        for n in range(self.num_workers):
            worker = LotusWorker(
                queue = self.queue,
                client = self.client,
                headers = self.headers,
                on_error = self.on_error,
                flush_at = self.flush_at,
                flush_interval = self.flush_interval,
                gzip = self.gzip,
                retries = self.max_retries,
                timeout = self.timeout,
                debug_enabled = self.debug_enabled,
                worker_id = n,
                batch_limit_size = batch_limit_size,
                max_msg_size = max_msg_size,
                **self.worker_kwargs,
                **kwargs
            )
            self.workers.append(worker)
    
    async def async_initialize_workers(
        self, 
        batch_limit_size: Optional[int] = None,
        max_msg_size: Optional[int] = None,
        **kwargs
    ):
        self.initialize_workers(
            batch_limit_size = batch_limit_size,
            max_msg_size = max_msg_size,
            **kwargs
        )

    def start_workers(self, **kwargs):
        if self.tasks:
            logger.error('Worker Tasks already started')
            return
        self.tasks = [
            asyncio.create_task(worker.run()) for worker in self.workers
        ]

    async def async_start_workers(self, **kwargs):
        self.start_workers(**kwargs)

    def create_workers(self, **kwargs):
        if self.workers_started: return
        self.initialize_workers(**kwargs)
        self.start_workers(**kwargs)
        self.workers_started = True
    
    async def async_create_workers(self, **kwargs):
        if self.workers_started: return
        await self.async_initialize_workers(**kwargs)
        await self.async_start_workers(**kwargs)
        self.workers_started = True

    """
    Track Event
    """
    def track_event(
        self,
        customer_id: Optional[str] = None,
        event_name: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        time_created: Optional[datetime.datetime] = None,
        idempotency_id: Optional[str] = None,
        blocking: Optional[bool] = False,
        **kwargs
    ):
        """
        Track an event for a customer
        """
        if self.workers_enabled and not self.workers_started:
            logger.info('Workers not started, creating workers')
            self.create_workers()

        msg = APIOperation.track_event.prepare_msg(
            customer_id = customer_id,
            event_name = event_name,
            properties = properties,
            time_created = time_created,
            idempotency_id = idempotency_id,
            blocking = blocking,
            **kwargs
        )
        return APIOperation.track_event.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_track_event(
        self,
        customer_id: Optional[str] = None,
        event_name: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        time_created: Optional[datetime.datetime] = None,
        idempotency_id: Optional[str] = None,
        blocking: Optional[bool] = False,
        **kwargs
    ):
        """
        Track an event for a customer
        """
        if self.workers_enabled and not self.workers_started:
            logger.info('Workers not started, creating workers')
            await self.async_create_workers()

        msg = await APIOperation.track_event.async_prepare_msg(
            customer_id = customer_id,
            event_name = event_name,
            properties = properties,
            time_created = time_created,
            idempotency_id = idempotency_id,
            blocking = blocking,
            **kwargs
        )
        return await APIOperation.track_event.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    """
    Customers
    """
    
    def get_all_customers(
        self, 
        blocking: Optional[bool] = True, 
        **kwargs
    ):
        """
        Retrieve All Customers
        """
        msg = APIOperation.get_all_customers.prepare_msg(
            **kwargs
        )
        return APIOperation.get_all_customers.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )

    async def async_get_all_customers(
        self, 
        blocking: Optional[bool] = True, 
        **kwargs
    ):
        """
        Retrieve All Customers
        """
        msg = await APIOperation.get_all_customers.async_prepare_msg(
            **kwargs
        )
        return await APIOperation.get_all_customers.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def get_customer(
        self, 
        customer_id: Optional[str] = None, 
        blocking: Optional[bool] = True, 
        **kwargs
    ):
        """
        Retrieve a Customer by ID
        """
        msg = APIOperation.get_customer_detail.prepare_msg(
            customer_id = customer_id,
            **kwargs
        )
        return APIOperation.get_customer_detail.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_get_customer(
        self, 
        customer_id: Optional[str] = None, 
        blocking: Optional[bool] = True, 
        **kwargs
    ):
        """
        Retrieve a Customer by ID
        """
        msg = await APIOperation.get_customer_detail.async_prepare_msg(
            customer_id = customer_id,
            **kwargs
        )
        return await APIOperation.get_customer_detail.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )

    def get_customer_detail(
        self, 
        customer_id: Optional[str] = None, 
        blocking: Optional[bool] = True, 
        **kwargs
    ):
        """
        Retrieve a Customer by ID
        """
        msg = APIOperation.get_customer_detail.prepare_msg(
            customer_id = customer_id,
            **kwargs
        )
        return APIOperation.get_customer_detail.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            **kwargs
        )


    async def async_get_customer_detail(
        self, 
        customer_id: Optional[str] = None, 
        blocking: Optional[bool] = True, 
        **kwargs
    ):
        """
        Retrieve a Customer by ID
        """
        msg = await APIOperation.get_customer_detail.async_prepare_msg(
            customer_id = customer_id,
            **kwargs
        )
        return await APIOperation.get_customer_detail.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            **kwargs
        )

    def create_customer(
        self,
        customer_name: Optional[str] = None,
        customer_id: Optional[str] = None,
        email: Optional[str] = None,
        payment_provider: Optional[PaymentProvider] = PaymentProvider.stripe,
        payment_provider_id: Optional[str] = None,
        properties: Optional[Dict] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Create a Customer
        """
        msg = APIOperation.create_customer.prepare_msg(
            customer_name = customer_name,
            customer_id = customer_id,
            email = email,
            payment_provider = payment_provider,
            payment_provider_id = payment_provider_id,
            properties = properties,
            **kwargs
        )
        return APIOperation.create_customer.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    

    async def async_create_customer(
        self,
        customer_name: Optional[str] = None,
        customer_id: Optional[str] = None,
        email: Optional[str] = None,
        payment_provider: Optional[PaymentProvider] = PaymentProvider.stripe,
        payment_provider_id: Optional[str] = None,
        properties: Optional[Dict] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Create a Customer
        """
        msg = await APIOperation.create_customer.async_prepare_msg(
            customer_name = customer_name,
            customer_id = customer_id,
            email = email,
            payment_provider = payment_provider,
            payment_provider_id = payment_provider_id,
            properties = properties,
            **kwargs
        )
        return await APIOperation.create_customer.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def create_batch_customers(
        self,
        customers: Optional[List[Union[LotusCustomer, Any]]] = None,
        behavior_on_existing: Optional[ExistingCustomerBehavior] = ExistingCustomerBehavior.ignore,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Create a Batch of Customers
        """
        customers = [c if isinstance(c, LotusCustomer) else LotusCustomer(**c) for c in customers]
        msg = APIOperation.create_batch_customers.prepare_msg(
            customers = customers,
            behavior_on_existing = behavior_on_existing,
        )
        return APIOperation.create_batch_customers.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
        )
    
    async def async_create_batch_customers(
        self,
        customers: Optional[List[Union[LotusCustomer, Any]]] = None,
        behavior_on_existing: Optional[ExistingCustomerBehavior] = ExistingCustomerBehavior.ignore,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Create a Batch of Customers
        """
        customers = [c if isinstance(c, LotusCustomer) else LotusCustomer(**c) for c in customers]
        msg = await APIOperation.create_batch_customers.async_prepare_msg(
            customers = customers,
            behavior_on_existing = behavior_on_existing,
        )
        return await APIOperation.create_batch_customers.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
        )
    
    # async def update_customer(
    #     self,
    #     customer_id: Optional[str] = None,
    #     customer_name: Optional[str] = None,
    #     email: Optional[str] = None,
    #     payment_provider: Optional[PaymentProvider] = PaymentProvider.stripe,
    #     payment_provider_id: Optional[str] = None,
    #     properties: Optional[Dict] = None,
    #     blocking: Optional[bool] = True,
    #     **kwargs
    # ):
    #     msg = await APIOperation.update_customer.prepare_msg(
    #         customer_id = customer_id,
    #         customer_name = customer_name,
    #         email = email,
    #         payment_provider = payment_provider,
    #         payment_provider_id = payment_provider_id,
    #         properties = properties,
    #         **kwargs
    #     )
    #     return await APIOperation.update_customer.execute(
    #         client = self.client, 
    #         msg = msg,
    #         headers = self.headers,
    #         timeout = self.timeout,
    #         blocking = blocking,
    #         queue = self.queue,
    #         **kwargs
    #     )

    def delete_customer(
        self,
        customer_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Delete a Customer by ID
        """
        msg = APIOperation.delete_customer.prepare_msg(
            customer_id = customer_id,
            **kwargs
        )
        return APIOperation.delete_customer.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_delete_customer(
        self,
        customer_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Delete a Customer by ID
        """
        msg = await APIOperation.delete_customer.async_prepare_msg(
            customer_id = customer_id,
            **kwargs
        )
        return await APIOperation.delete_customer.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    """
    Subscriptions
    """

    def get_all_subscriptions(
        self,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get All Subscriptions
        """
        msg = APIOperation.get_all_subscriptions.prepare_msg(
            **kwargs
        )
        return APIOperation.get_all_subscriptions.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_get_all_subscriptions(
        self,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get All Subscriptions
        """
        msg = await APIOperation.get_all_subscriptions.async_prepare_msg(
            **kwargs
        )
        return await APIOperation.get_all_subscriptions.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )

    async def async_create_subscription(
        self,
        customer_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        start_date: Optional[Union[datetime.datetime, str]] = None,
        end_date: Optional[Union[datetime.datetime, str]] = None,
        auto_renew: Optional[bool] = None,
        is_new: Optional[bool] = None,
        subscription_id: Optional[str] = None,
        status: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Create a Subscription
        """
        msg = await APIOperation.create_subscription.async_prepare_msg(
            customer_id = customer_id,
            plan_id = plan_id,
            start_date = start_date,
            end_date = end_date,
            auto_renew = auto_renew,
            is_new = is_new,
            subscription_id = subscription_id,
            status = status,
            **kwargs
        )
        return await APIOperation.create_subscription.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def create_subscription(
        self,
        customer_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        start_date: Optional[Union[datetime.datetime, str]] = None,
        end_date: Optional[Union[datetime.datetime, str]] = None,
        auto_renew: Optional[bool] = None,
        is_new: Optional[bool] = None,
        subscription_id: Optional[str] = None,
        status: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Create a Subscription
        """
        msg = APIOperation.create_subscription.prepare_msg(
            customer_id = customer_id,
            plan_id = plan_id,
            start_date = start_date,
            end_date = end_date,
            auto_renew = auto_renew,
            is_new = is_new,
            subscription_id = subscription_id,
            status = status,
            **kwargs
        )
        return APIOperation.create_subscription.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    
    async def async_cancel_subscription(
        self,
        subscription_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Cancel a Subscription
        """
        msg = await APIOperation.cancel_subscription.async_prepare_msg(
            subscription_id = subscription_id,
            **kwargs
        )
        return await APIOperation.cancel_subscription.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def cancel_subscription(
        self,
        subscription_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Cancel a Subscription
        """
        msg = APIOperation.cancel_subscription.prepare_msg(
            subscription_id = subscription_id,
            **kwargs
        )
        return APIOperation.cancel_subscription.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_get_subscription_detail(
        self,
        subscription_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get Subscription Detail
        """
        msg = await APIOperation.get_subscription_detail.async_prepare_msg(
            subscription_id = subscription_id,
            **kwargs
        )
        return await APIOperation.get_subscription_detail.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def get_subscription_detail(
        self,
        subscription_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get Subscription Detail
        """
        msg = APIOperation.get_subscription_detail.prepare_msg(
            subscription_id = subscription_id,
            **kwargs
        )
        return APIOperation.get_subscription_detail.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_update_subscription(
        self,
        subscription_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        start_date: Optional[Union[datetime.datetime, str]] = None,
        end_date: Optional[Union[datetime.datetime, str]] = None,
        auto_renew: Optional[bool] = None,
        is_new: Optional[bool] = None,
        status: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Update a Subscription
        """
        msg = await APIOperation.update_subscription.async_prepare_msg(
            subscription_id = subscription_id,
            plan_id = plan_id,
            start_date = start_date,
            end_date = end_date,
            auto_renew = auto_renew,
            is_new = is_new,
            status = status,
            **kwargs
        )
        return await APIOperation.update_subscription.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def update_subscription(
        self,
        subscription_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        start_date: Optional[Union[datetime.datetime, str]] = None,
        end_date: Optional[Union[datetime.datetime, str]] = None,
        auto_renew: Optional[bool] = None,
        is_new: Optional[bool] = None,
        status: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Update a Subscription
        """
        msg = APIOperation.update_subscription.prepare_msg(
            subscription_id = subscription_id,
            plan_id = plan_id,
            start_date = start_date,
            end_date = end_date,
            auto_renew = auto_renew,
            is_new = is_new,
            status = status,
            **kwargs
        )
        return APIOperation.update_subscription.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    
    async def async_change_subscription_plan(
        self,
        subscription_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Change Subscription Plan
        """
        msg = await APIOperation.change_subscription_plan.async_prepare_msg(
            subscription_id = subscription_id,
            plan_id = plan_id,
            **kwargs
        )
        return await APIOperation.change_subscription_plan.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def change_subscription_plan(
        self,
        subscription_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Change Subscription Plan
        """
        msg = APIOperation.change_subscription_plan.prepare_msg(
            subscription_id = subscription_id,
            plan_id = plan_id,
            **kwargs
        )
        return APIOperation.change_subscription_plan.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )

    """
    Metrics
    """
    async def async_get_all_metrics(
        self,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get All Metrics
        """
        msg = await APIOperation.get_all_metrics.async_prepare_msg(
            **kwargs
        )
        return await APIOperation.get_all_metrics.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def get_all_metrics(
        self,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get All Metrics
        """
        msg = APIOperation.get_all_metrics.prepare_msg(
            **kwargs
        )
        return APIOperation.get_all_metrics.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )

    async def async_get_metric_detail(
        self,
        metric_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get Metric Detail
        """
        msg = await APIOperation.get_metric_detail.async_prepare_msg(
            metric_id = metric_id,
            **kwargs
        )
        return await APIOperation.get_metric_detail.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def get_metric_detail(
        self,
        metric_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get Metric Detail
        """
        msg = APIOperation.get_metric_detail.prepare_msg(
            metric_id = metric_id,
            **kwargs
        )
        return APIOperation.get_metric_detail.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_get_metric(
        self,
        metric_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get Metric
        """
        msg = await APIOperation.get_metric_detail.async_prepare_msg(
            metric_id = metric_id,
            **kwargs
        )
        return await APIOperation.get_metric_detail.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def get_metric(
        self,
        metric_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get Metric
        """
        msg = APIOperation.get_metric_detail.prepare_msg(
            metric_id = metric_id,
            **kwargs
        )
        return APIOperation.get_metric_detail.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_create_metric(
        self,
        metric_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        filters: Optional[List[Filter]] = None,
        categorical_filters: Optional[List[CategoricalFilter]] = None,
        numeric_filters: Optional[List[NumericFilter]] = None,
        event_name: Optional[str] = None,
        event_type: Optional[EventType] = None,
        granularity: Optional[MetricGranularity] = None,
        billable_aggregation_type: Optional[MetricAggregation] = None,
        usage_aggregation_type: Optional[MetricAggregation] = None,
        description: Optional[str] = None,
        properties: Optional[Dict] = None,
        property_name: Optional[str] = None,
        is_cost_metric: Optional[bool] = None,
        blocking: Optional[bool] = True,
        **kwargs,
    ):
        """
        Create Metric
        """
        msg = await APIOperation.create_metric.async_prepare_msg(
            metric_id = metric_id,
            metric_name = metric_name,
            metric_type = metric_type,
            filters = filters,
            categorical_filters = categorical_filters,
            numeric_filters = numeric_filters,
            event_name = event_name,
            event_type = event_type,
            granularity = granularity,
            billable_aggregation_type = billable_aggregation_type,
            usage_aggregation_type = usage_aggregation_type,
            description = description,
            properties = properties,
            property_name = property_name,
            is_cost_metric = is_cost_metric,
            **kwargs
        )
        return await APIOperation.create_metric.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def create_metric(
        self,
        metric_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        filters: Optional[List[Filter]] = None,
        categorical_filters: Optional[List[CategoricalFilter]] = None,
        numeric_filters: Optional[List[NumericFilter]] = None,
        event_name: Optional[str] = None,
        event_type: Optional[EventType] = None,
        granularity: Optional[MetricGranularity] = None,
        billable_aggregation_type: Optional[MetricAggregation] = None,
        usage_aggregation_type: Optional[MetricAggregation] = None,
        description: Optional[str] = None,
        properties: Optional[Dict] = None,
        property_name: Optional[str] = None,
        is_cost_metric: Optional[bool] = None,
        blocking: Optional[bool] = True,
        **kwargs,
    ):
        """
        Create Metric
        """
        msg = APIOperation.create_metric.prepare_msg(
            metric_id = metric_id,
            metric_name = metric_name,
            metric_type = metric_type,
            filters = filters,
            categorical_filters = categorical_filters,
            numeric_filters = numeric_filters,
            event_name = event_name,
            event_type = event_type,
            granularity = granularity,
            billable_aggregation_type = billable_aggregation_type,
            usage_aggregation_type = usage_aggregation_type,
            description = description,
            properties = properties,
            property_name = property_name,
            is_cost_metric = is_cost_metric,
            **kwargs
        )
        return APIOperation.create_metric.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )

    
    async def async_update_metric(
        self,
        metric_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        filters: Optional[List[Filter]] = None,
        categorical_filters: Optional[List[CategoricalFilter]] = None,
        numeric_filters: Optional[List[NumericFilter]] = None,
        event_name: Optional[str] = None,
        event_type: Optional[EventType] = None,
        granularity: Optional[MetricGranularity] = None,
        billable_aggregation_type: Optional[MetricAggregation] = None,
        usage_aggregation_type: Optional[MetricAggregation] = None,
        description: Optional[str] = None,
        properties: Optional[Dict] = None,
        property_name: Optional[str] = None,
        is_cost_metric: Optional[bool] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Update Metric
        """
        msg = await APIOperation.update_metric.async_prepare_msg(
            metric_id = metric_id,
            metric_name = metric_name,
            metric_type = metric_type,
            filters = filters,
            categorical_filters = categorical_filters,
            numeric_filters = numeric_filters,
            event_name = event_name,
            event_type = event_type,
            granularity = granularity,
            billable_aggregation_type = billable_aggregation_type,
            usage_aggregation_type = usage_aggregation_type,
            description = description,
            properties = properties,
            property_name = property_name,
            is_cost_metric = is_cost_metric,
            **kwargs
        )
        return await APIOperation.update_metric.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def update_metric(
        self,
        metric_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        filters: Optional[List[Filter]] = None,
        categorical_filters: Optional[List[CategoricalFilter]] = None,
        numeric_filters: Optional[List[NumericFilter]] = None,
        event_name: Optional[str] = None,
        event_type: Optional[EventType] = None,
        granularity: Optional[MetricGranularity] = None,
        billable_aggregation_type: Optional[MetricAggregation] = None,
        usage_aggregation_type: Optional[MetricAggregation] = None,
        description: Optional[str] = None,
        properties: Optional[Dict] = None,
        property_name: Optional[str] = None,
        is_cost_metric: Optional[bool] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Update Metric
        """
        msg = APIOperation.update_metric.prepare_msg(
            metric_id = metric_id,
            metric_name = metric_name,
            metric_type = metric_type,
            filters = filters,
            categorical_filters = categorical_filters,
            numeric_filters = numeric_filters,
            event_name = event_name,
            event_type = event_type,
            granularity = granularity,
            billable_aggregation_type = billable_aggregation_type,
            usage_aggregation_type = usage_aggregation_type,
            description = description,
            properties = properties,
            property_name = property_name,
            is_cost_metric = is_cost_metric,
            **kwargs
        )
        return APIOperation.update_metric.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    

    """
    Plans
    """

    async def async_get_all_plans(
        self,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get All Plans
        """
        msg = await APIOperation.get_all_plans.async_prepare_msg(
            **kwargs
        )
        return await APIOperation.get_all_plans.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def get_all_plans(
        self,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get All Plans
        """
        msg = APIOperation.get_all_plans.prepare_msg(
            **kwargs
        )
        return APIOperation.get_all_plans.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )

    async def async_get_plan_detail(
        self,
        plan_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get Plan Detail
        """
        msg = await APIOperation.get_plan_detail.async_prepare_msg(
            plan_id = plan_id,
            **kwargs
        )
        return await APIOperation.get_plan_detail.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def get_plan_detail(
        self,
        plan_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get Plan Detail
        """
        msg = APIOperation.get_plan_detail.prepare_msg(
            plan_id = plan_id,
            **kwargs
        )
        return APIOperation.get_plan_detail.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_create_plan(
        self,
        plan_name: Optional[str] = None,
        plan_duration: Optional[PlanDuration] = None,
        plan_id: Optional[str] = None,
        product_id: Optional[str] = None,
        status: Optional[PlanStatus] = None,
        initial_external_links: Optional[List[PlanExternalLink]] = None,
        initial_version: Optional[PlanVersion] = None,
        parent_plan_id: Optional[str] = None,
        target_customer_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Create Plan
        """
        msg = await APIOperation.create_plan.async_prepare_msg(
            plan_name = plan_name,
            plan_duration = plan_duration,
            plan_id = plan_id,
            product_id = product_id,
            status = status,
            initial_external_links = initial_external_links,
            initial_version = initial_version,
            parent_plan_id = parent_plan_id,
            target_customer_id = target_customer_id,
            **kwargs
        )
        return await APIOperation.create_plan.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def create_plan(
        self,
        plan_name: Optional[str] = None,
        plan_duration: Optional[PlanDuration] = None,
        plan_id: Optional[str] = None,
        product_id: Optional[str] = None,
        status: Optional[PlanStatus] = None,
        initial_external_links: Optional[List[PlanExternalLink]] = None,
        initial_version: Optional[PlanVersion] = None,
        parent_plan_id: Optional[str] = None,
        target_customer_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Create Plan
        """
        msg = APIOperation.create_plan.prepare_msg(
            plan_name = plan_name,
            plan_duration = plan_duration,
            plan_id = plan_id,
            product_id = product_id,
            status = status,
            initial_external_links = initial_external_links,
            initial_version = initial_version,
            parent_plan_id = parent_plan_id,
            target_customer_id = target_customer_id,
            **kwargs
        )
        return APIOperation.create_plan.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_update_plan(
        self,
        plan_id: Optional[str] = None,
        plan_name: Optional[str] = None,
        plan_duration: Optional[PlanDuration] = None,
        product_id: Optional[str] = None,
        status: Optional[PlanStatus] = None,
        initial_external_links: Optional[List[PlanExternalLink]] = None,
        initial_version: Optional[PlanVersion] = None,
        parent_plan_id: Optional[str] = None,
        target_customer_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Update Plan
        """
        msg = await APIOperation.update_plan.async_prepare_msg(
            plan_id = plan_id,
            plan_name = plan_name,
            plan_duration = plan_duration,
            product_id = product_id,
            status = status,
            initial_external_links = initial_external_links,
            initial_version = initial_version,
            parent_plan_id = parent_plan_id,
            target_customer_id = target_customer_id,
            **kwargs
        )
        return await APIOperation.update_plan.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def update_plan(
        self,
        plan_id: Optional[str] = None,
        plan_name: Optional[str] = None,
        plan_duration: Optional[PlanDuration] = None,
        product_id: Optional[str] = None,
        status: Optional[PlanStatus] = None,
        initial_external_links: Optional[List[PlanExternalLink]] = None,
        initial_version: Optional[PlanVersion] = None,
        parent_plan_id: Optional[str] = None,
        target_customer_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Update Plan
        """
        msg = APIOperation.update_plan.prepare_msg(
            plan_id = plan_id,
            plan_name = plan_name,
            plan_duration = plan_duration,
            product_id = product_id,
            status = status,
            initial_external_links = initial_external_links,
            initial_version = initial_version,
            parent_plan_id = parent_plan_id,
            target_customer_id = target_customer_id,
            **kwargs
        )
        return APIOperation.update_plan.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    # async def async_delete_plan(
    #     self,
    #     plan_id: Optional[str] = None,
    #     blocking: Optional[bool] = True,
    #     **kwargs
    # ):
    #     """
    #     Delete Plan
    #     """
    #     msg = await APIOperation.delete_plan.prepare_msg(
    #         plan_id = plan_id,
    #         **kwargs
    #     )
    #     return await APIOperation.delete_plan.execute(
    #         client = self.client, 
    #         msg = msg,
    #         headers = self.headers,
    #         timeout = self.timeout,
    #         blocking = blocking,
    #         queue = self.queue,
    #         **kwargs
    #     )

    """
    Users
    """
    async def async_get_user_detail(
        self,
        user_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get User
        """
        msg = await APIOperation.get_user_detail.async_prepare_msg(
            user_id = user_id,
            **kwargs
        )
        return await APIOperation.get_user_detail.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def get_user_detail(
        self,
        user_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get User
        """
        msg = APIOperation.get_user_detail.prepare_msg(
            user_id = user_id,
            **kwargs
        )
        return APIOperation.get_user_detail.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_get_all_users(
        self,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get All Users
        """
        msg = await APIOperation.get_all_users.async_prepare_msg(
            **kwargs
        )
        return await APIOperation.get_all_users.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def get_all_users(
        self,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Get All Users
        """
        msg = APIOperation.get_all_users.prepare_msg(
            **kwargs
        )
        return APIOperation.get_all_users.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_create_user(
        self,
        email: Optional[str] = None,
        username: Optional[str] = None,
        company_name: Optional[str] = None,
        organization_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Create User
        """
        msg = await APIOperation.create_user.async_prepare_msg(
            email = email,
            username = username,
            company_name = company_name,
            organization_id = organization_id,
            **kwargs
        )
        return await APIOperation.create_user.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def create_user(
        self,
        email: Optional[str] = None,
        username: Optional[str] = None,
        company_name: Optional[str] = None,
        organization_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Create User
        """
        msg = APIOperation.create_user.prepare_msg(
            email = email,
            username = username,
            company_name = company_name,
            organization_id = organization_id,
            **kwargs
        )
        return APIOperation.create_user.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_update_user(
        self,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        username: Optional[str] = None,
        company_name: Optional[str] = None,
        organization_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Update User
        """
        msg = await APIOperation.update_user.async_prepare_msg(
            user_id = user_id,
            email = email,
            username = username,
            company_name = company_name,
            organization_id = organization_id,
            **kwargs
        )
        return await APIOperation.update_user.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def update_user(
        self,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        username: Optional[str] = None,
        company_name: Optional[str] = None,
        organization_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Update User
        """
        msg = APIOperation.update_user.prepare_msg(
            user_id = user_id,
            email = email,
            username = username,
            company_name = company_name,
            organization_id = organization_id,
            **kwargs
        )
        return APIOperation.update_user.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    async def async_delete_user(
        self,
        user_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Delete User
        """
        msg = await APIOperation.delete_user.async_prepare_msg(
            user_id = user_id,
            **kwargs
        )
        return await APIOperation.delete_user.async_execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    def delete_user(
        self,
        user_id: Optional[str] = None,
        blocking: Optional[bool] = True,
        **kwargs
    ):
        """
        Delete User
        """
        msg = APIOperation.delete_user.prepare_msg(
            user_id = user_id,
            **kwargs
        )
        return APIOperation.delete_user.execute(
            client = self.client, 
            msg = msg,
            headers = self.headers,
            timeout = self.timeout,
            blocking = blocking,
            queue = self.queue,
            ignore_errors = self.ignore_errors,
            **kwargs
        )
    
    """
    Function Decorators
    """
    def on_event(
        self,
        customer_id: Optional[Union[str, Callable]] = None,
        event_name: Optional[Union[str, Callable]] = None,
        properties: Optional[Union[Dict, Callable]] = None,
        time_created: Optional[datetime.datetime] = None,
        idempotency_id: Optional[str] = None,
        exclude_properties: Optional[List[str]] = None,
        exclude_on: Optional[Callable] = None,
        extra_properties: Optional[Dict] = None,
        extra_properties_func: Optional[Callable] = None,
        include_duration: Optional[bool] = False,
        include_results: Optional[bool] = True,
        blocking: Optional[bool] = False,
        **kwargs,
    ):
        """
        Lotus Event Decorator to log events to the Lotus API.
        Most params are either _str_ or _Callable_ which will pass the function's arguments 
        and expects a _str_ to be returned. If required parameters are not provided, the 
        event logging will not occur.

        Example:

        >>> @lotus.on_event(customer_id = get_customer_id)
        ... def my_func(headers: Dict, params: Dict):
        ...     ...

        >>> @lotus.on_event(customer_id="1234")
        ... async def async_run_func():
        ...     ...

        >>> @lotus.on_event(customer_id="1234", event_name="my_event")
        ... def run_func():
        ...     ...

        :param customer_id: The customer_id to log the event to. (required)
        :param event_name: The type of event to log. Defaults to the function name.
        :param properties: A dictionary of parameters to log with the event. Defaults 
        to the function's arguments.
        :param time_created: The time the event occurred. Defaults to the current time.
        :param idempotency_id: A unique id to prevent duplicate events. Defaults to a unique uuid.

        :param exclude_properties: A list of properties to exclude from the event.
        :param exclude_on: A function that takes validates whether this event should be logged.

        :param extra_properties: A dictionary of extra properties to add to the event.
        :param extra_properties_func: A function that takes the function's arguments and returns
        a dictionary of extra properties to add to the event.
        
        :param include_duration: Whether to include the duration of the function in the event.
        :param blocking: Whether to block the function until the event is logged.

        """
        wrapper_kwargs = kwargs or {}
        def decorator(func):
            if is_coro_func(func):
                @functools.wraps(func)
                async def wrapper(*args, **kwargs):

                    # validate exclude_on
                    if exclude_on is not None:
                        if is_coro_func(exclude_on) and await exclude_on(*args, **kwargs, **wrapper_kwargs):
                            return await func(*args, **kwargs)
                        elif exclude_on(*args, **kwargs):
                            return await func(*args, **kwargs)

                    # validate customer_id
                    if customer_id is None:
                        logger.error("customer_id is required for event logging.")
                        return await func(*args, **kwargs)
                    
                    _customer_id = customer_id
                    if callable(customer_id):
                        if is_coro_func(customer_id):
                            _customer_id = await customer_id(*args, **kwargs, **wrapper_kwargs)
                        else:
                            _customer_id = customer_id(*args, **kwargs, **wrapper_kwargs)
                    
                    # validate event_name
                    if event_name is None:
                        _event_id = full_name(func)
                    elif callable(event_name):
                        if is_coro_func(event_name):
                            _event_id = await event_name(*args, **kwargs, **wrapper_kwargs)
                        else:
                            _event_id = event_name(*args, **kwargs, **wrapper_kwargs)
                    
                    
                    # validate/handle properties
                    event_properties = {}
                    if properties is not None:
                        if callable(properties):
                            if is_coro_func(properties):
                                event_properties = await properties(*args, **kwargs, **wrapper_kwargs)
                            else:
                                event_properties = properties(*args, **kwargs, **wrapper_kwargs)
                        else:
                            event_properties = properties
                    
                    if extra_properties:
                        event_properties.update(extra_properties)
                    
                    if extra_properties_func:
                        if is_coro_func(extra_properties_func):
                            event_properties.update(await extra_properties_func(*args, **kwargs, **wrapper_kwargs))
                        else:
                            event_properties.update(extra_properties_func(*args, **kwargs, **wrapper_kwargs))
                    
                    if exclude_properties:
                        for prop in exclude_properties:
                            event_properties.pop(prop, None)
                    
                    duration_s = timer() if include_duration else None
                    result = await func(*args, **kwargs)
                    if include_duration: event_properties['duration_s'] = timer(duration_s)
                    if include_results: event_properties['results'] = result
                    
                    await self.async_track_event(
                        customer_id = _customer_id,
                        event_name = _event_id,
                        properties = event_properties,
                        time_created = time_created,
                        idempotency_id = idempotency_id,
                        blocking = blocking,
                        **kwargs,
                    )
                    return result
                    
            
            else:
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    # validate exclude_on
                    if exclude_on is not None and exclude_on(*args, **kwargs, **wrapper_kwargs):
                        return func(*args, **kwargs)

                    # validate customer_id
                    if customer_id is None:
                        logger.error("customer_id is required for event logging.")
                        return func(*args, **kwargs)
                    
                    _customer_id = customer_id
                    if callable(customer_id):
                        _customer_id = customer_id(*args, **kwargs, **wrapper_kwargs)
                    
                    # validate event_name
                    if event_name is None:
                        _event_id = full_name(func)
                    elif callable(event_name):
                        _event_id = event_name(*args, **kwargs, **wrapper_kwargs)
                    
                    
                    # validate/handle properties
                    event_properties = {}
                    if properties is not None:
                        if callable(properties):
                            event_properties = properties(*args, **kwargs, **wrapper_kwargs)
                        else:
                            event_properties = properties
                    
                    if extra_properties:
                        event_properties.update(extra_properties)
                    
                    if extra_properties_func:
                        event_properties.update(extra_properties_func(*args, **kwargs, **wrapper_kwargs))
                    
                    if exclude_properties:
                        for prop in exclude_properties:
                            event_properties.pop(prop, None)
                    
                    duration_s = timer() if include_duration else None
                    result = func(*args, **kwargs)
                    
                    if include_duration: event_properties['duration_s'] = timer(duration_s)
                    if include_results: event_properties['results'] = result
                    
                    self.track_event(
                        customer_id = _customer_id,
                        event_name = _event_id,
                        properties = event_properties,
                        time_created = time_created,
                        idempotency_id = idempotency_id,
                        blocking = blocking,
                        **kwargs,
                    )
                    return result
                
            return wrapper
        return decorator



    """
    Context Management
    """
    
    
    async def async_flush(self):
        """Forces a flush from the internal queue to the server"""
        if self.workers_started:
            self.log_method(f"Flushing {self.queue.qsize()} items.")
            
            await self.queue.join()
            self.log_method(f"Successfully flushed about {self.queue.qsize()} items.")
            self.workers = []
    
    async def async_join(self):
        """Forces a flush from the internal queue to the server"""
        # Cancel our worker tasks.
        if self.workers_started:
            for worker in self.workers:
                worker.pause()
            
            for task in self.tasks:
                task.cancel()
            
            # Wait until all worker tasks are cancelled.
            await asyncio.gather(*self.tasks, return_exceptions=True)
            self.log_method(f"successfully joined all {len(self.tasks)} tasks.")
            self.tasks = []
            self.workers_started = False
            
    
    async def async_shutdown(self):
        """Flushes the queue and ends the consumer thread"""
        await self.async_flush()
        await self.async_join()
        self.log_method("Shutdown complete")
    
    def __enter__(self):
        return self

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.async_shutdown()
    
    def __exit__(self, exc_type, exc_value, traceback):
        return