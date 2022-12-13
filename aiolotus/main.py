# Async Lotus Client

# https://github.com/uselotus/lotus-python/tree/main

import datetime

from lazyops.types import classproperty

from aiolotus.types import *
from aiolotus.schemas import *
from aiolotus.client import LotusClient
from typing import Optional, Union, List, Dict, Any, Callable

# Global Wrapper Class for LotusClient

class Lotus:
    apikey: Optional[str] = None
    url: Optional[str] = None
    scheme: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None

    debug_enabled: Optional[bool] = None
    max_queue_size: Optional[int] = None
    on_error: Optional[Callable] = None
    flush_at: Optional[int] = None
    flush_interval: Optional[float] = None
    gzip: Optional[bool] = None
    max_retries: Optional[int] = None
    workers_enabled: Optional[bool] = None
    
    timeout: Optional[int] = None
    apikey_header: Optional[str] = None

    num_workers: Optional[int] = None
    worker_batch_limit_size: Optional[int] = None
    worker_max_msg_size: Optional[int] = None
    ignore_errors: Optional[bool] = None

    _api: Optional[LotusClient] = None

    @classmethod
    def configure(
        cls, 
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
        reset: Optional[bool] = None,
        **kwargs
    ):
        """
        Configure the global Lotus client.
        """
        if apikey is not None: cls.apikey = apikey
        if url is not None: cls.url = url
        if scheme is not None: cls.scheme = scheme
        if host is not None: cls.host = host
        if port is not None: cls.port = port

        if debug_enabled is not None: cls.debug_enabled = debug_enabled
        if max_queue_size is not None: cls.max_queue_size = max_queue_size
        if on_error is not None: cls.on_error = on_error
        if flush_at is not None: cls.flush_at = flush_at
        if flush_interval is not None: cls.flush_interval = flush_interval
        if gzip is not None: cls.gzip = gzip
        if max_retries is not None: cls.max_retries = max_retries
        if workers_enabled is not None: cls.workers_enabled = workers_enabled
        if timeout is not None: cls.timeout = timeout
        if apikey_header is not None: cls.apikey_header = apikey_header
        if num_workers is not None: cls.num_workers = num_workers
        if worker_batch_limit_size is not None: cls.worker_batch_limit_size = worker_batch_limit_size
        if worker_max_msg_size is not None: cls.worker_max_msg_size = worker_max_msg_size
        if ignore_errors is not None: cls.ignore_errors = ignore_errors
        if reset: cls._api = None

        if cls._api is None:
            cls.get_api(**kwargs)


    @classmethod
    def get_api(cls, **kwargs) -> LotusClient:
        if cls._api is None:
            cls._api = LotusClient(
                apikey = cls.apikey,
                url = cls.url,
                scheme = cls.scheme,
                host = cls.host,
                port = cls.port,
                debug_enabled = cls.debug_enabled,
                max_queue_size = cls.max_queue_size,
                on_error = cls.on_error,
                flush_at = cls.flush_at,
                flush_interval = cls.flush_interval,
                gzip = cls.gzip,
                max_retries = cls.max_retries,
                workers_enabled = cls.workers_enabled,
                timeout = cls.timeout,
                apikey_header = cls.apikey_header,
                num_workers = cls.num_workers,
                worker_batch_limit_size = cls.worker_batch_limit_size,
                worker_max_msg_size = cls.worker_max_msg_size,
                ignore_errors = cls.ignore_errors,
                **kwargs
            )
        return cls._api

    @classproperty
    def api(cls) -> LotusClient:
        return cls.get_api()
    

    """
    Events
    """
    @classmethod
    async def track_event(
        cls,
        *args,
        customer_id: Optional[str] = None,
        event_name: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        time_created: Optional[datetime.datetime] = None,
        idempotency_id: Optional[str] = None,
        **kwargs
    ):
        return await cls.get_api(**kwargs).track_event(
            *args,
            customer_id = customer_id,
            event_name = event_name,
            properties = properties,
            time_created = time_created,
            idempotency_id = idempotency_id,
            **kwargs
        )
    

    """
    Customers
    """

    @classmethod
    async def get_all_customers(cls, *args, **kwargs):
        return await cls.get_api(**kwargs).get_all_customers(*args, **kwargs)

    @classmethod
    async def get_customer_detail(cls, *args, customer_id: Optional[str] = None, **kwargs):
        return await cls.get_api(**kwargs).get_customer_detail(
            *args, customer_id = customer_id, **kwargs
        )

    @classmethod
    async def create_customer(
        cls,
        *args,
        customer_name: Optional[str] = None,
        customer_id: Optional[str] = None,
        email: Optional[str] = None,
        payment_provider: Optional[PaymentProvider] = PaymentProvider.stripe,
        payment_provider_id: Optional[str] = None,
        properties: Optional[Dict] = None,
        **kwargs
    ):
        return await cls.get_api(**kwargs).create_customer(
            *args,
            customer_name = customer_name,
            customer_id = customer_id,
            email = email,
            payment_provider = payment_provider,
            payment_provider_id = payment_provider_id,
            properties = properties,
            **kwargs
        )
    
    @classmethod
    async def create_batch_customers(
        cls,
        *args,
        customers: Optional[List[Any]] = None,
        behavior_on_existing: Optional[ExistingCustomerBehavior] = ExistingCustomerBehavior.ignore,
        **kwargs
    ):
        return await cls.get_api(**kwargs).create_batch_customers(
            *args,
            customers = customers,
            behavior_on_existing = behavior_on_existing,
            **kwargs
        )
    
    """
    Subscriptions
    """
    
    @classmethod
    async def create_subscription(
        cls, 
        *args,
        customer_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        start_date: Optional[Union[datetime.datetime, str]] = None,
        end_date: Optional[Union[datetime.datetime, str]] = None,
        auto_renew: Optional[bool] = None,
        is_new: Optional[bool] = None,
        subscription_id: Optional[str] = None,
        status: Optional[str] = None,
        **kwargs
    ):
        return await cls.get_api(**kwargs).create_subscription(
            *args,
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


    @classmethod
    async def cancel_subscription(
        cls,
        *args, 
        subscription_id: Optional[str] = None,
        turn_off_auto_renew: Optional[bool] = None,
        replace_immediately_type: Optional[ReplaceType] = None,
        **kwargs
    ):
        return await cls.get_api(**kwargs).cancel_subscription(
            *args,
            subscription_id = subscription_id,
            turn_off_auto_renew = turn_off_auto_renew,
            replace_immediately_type = replace_immediately_type,
            **kwargs
        )


    @classmethod
    async def get_all_subscriptions(cls, *args, **kwargs):
        return await cls.get_api(**kwargs).get_all_subscriptions(*args, **kwargs)

        
    @classmethod
    async def get_single_subscription(cls, *args, subscription_id: Optional[str] = None, **kwargs):
        return await cls.get_api(**kwargs).get_subscription_detail(
            *args, subscription_id = subscription_id, **kwargs
        )
    
    @classmethod
    async def get_subscription_detail(cls, *args, subscription_id: Optional[str] = None, **kwargs):
        return await cls.get_api(**kwargs).get_subscription_detail(
            *args, subscription_id = subscription_id, **kwargs
        )
    

    
    @classmethod
    async def update_subscription(
        cls,
        subscription_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        start_date: Optional[Union[datetime.datetime, str]] = None,
        end_date: Optional[Union[datetime.datetime, str]] = None,
        auto_renew: Optional[bool] = None,
        is_new: Optional[bool] = None,
        status: Optional[str] = None,
        **kwargs
    ):
        return await cls.get_api(**kwargs).update_subscription(
            subscription_id = subscription_id,
            plan_id = plan_id,
            start_date = start_date,
            end_date = end_date,
            auto_renew = auto_renew,
            is_new = is_new,
            status = status,
            **kwargs
        )
    
    @classmethod
    async def change_subscription_plan(
        cls, 
        *args, 
        subscription_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        replace_immediately_type: Optional[ReplaceType] = None, 
        **kwargs
    ):
        return await cls.get_api(**kwargs).change_subscription_plan(
            *args,
            subscription_id = subscription_id,
            plan_id = plan_id,
            replace_immediately_type = replace_immediately_type,
            **kwargs
        )

    """
    Access
    """

    @classmethod
    async def get_customer_access(
        cls, 
        *args, 
        customer_id: Optional[str] = None,
        event_name: Optional[str] = None,
        feature_name: Optional[str] = None,
        **kwargs
    ):
        return await cls.get_api(**kwargs).get_customer_access(
            *args,
            customer_id = customer_id,
            event_name = event_name,
            feature_name = feature_name,
            **kwargs
        )


    """
    Metrics
    """
    @classmethod
    async def get_all_metrics(cls, *args, **kwargs):
        return await cls.get_api(**kwargs).get_all_metrics(*args, **kwargs)

    @classmethod
    async def get_metric_detail(cls, *args, metric_id: Optional[str] = None, **kwargs):
        return await cls.get_api(**kwargs).get_metric_detail(
            *args, metric_id = metric_id, **kwargs
        )

    @classmethod
    async def create_metric(
        cls,
        *args,
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
        **kwargs
    ):
        return await cls.get_api(**kwargs).create_metric(
            *args,
            metric_id = metric_id,
            metric_name = metric_name,
            filters = filters,
            categorical_filters = categorical_filters,
            numeric_filters = numeric_filters,
            event_name = event_name,
            metric_type = metric_type,
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

    @classmethod
    async def update_metric(
        cls,
        *args,
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
        **kwargs
    ):
        return await cls.get_api(**kwargs).update_metric(
            *args,
            metric_id = metric_id,
            metric_name = metric_name,
            filters = filters,
            categorical_filters = categorical_filters,
            numeric_filters = numeric_filters,
            event_name = event_name,
            metric_type = metric_type,
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

    """
    Plans
    """

    @classmethod
    async def get_all_plans(cls, *args, **kwargs):
        return await cls.get_api(**kwargs).get_all_plans(*args, **kwargs)

    @classmethod
    async def get_plan_detail(cls, *args, plan_id: Optional[str] = None, **kwargs):
        return await cls.get_api(**kwargs).get_plan_detail(
            *args, plan_id = plan_id, **kwargs
        )
    
    @classmethod
    async def create_plan(
        cls,
        *args,
        plan_name: Optional[str] = None,
        plan_duration: Optional[PlanDuration] = None,
        plan_id: Optional[str] = None,
        product_id: Optional[str] = None,
        status: Optional[PlanStatus] = None,
        initial_external_links: Optional[List[PlanExternalLink]] = None,
        initial_version: Optional[PlanVersion] = None,
        parent_plan_id: Optional[str] = None,
        target_customer_id: Optional[str] = None,
        **kwargs
    ):
        return await cls.get_api(**kwargs).create_plan(
            *args,
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

    @classmethod
    async def update_plan(
        cls,
        *args,
        plan_id: Optional[str] = None,
        plan_name: Optional[str] = None,
        plan_duration: Optional[PlanDuration] = None,
        product_id: Optional[str] = None,
        status: Optional[PlanStatus] = None,
        initial_external_links: Optional[List[PlanExternalLink]] = None,
        initial_version: Optional[PlanVersion] = None,
        parent_plan_id: Optional[str] = None,
        target_customer_id: Optional[str] = None,
        **kwargs
    ):
        return await cls.get_api(**kwargs).update_plan(
            *args,
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

    """
    Users
    """

    @classmethod
    async def get_user_detail(
        cls,
        *args,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """
        Get User
        """
        return await cls.get_api(**kwargs).get_user_detail(
            *args,
            user_id = user_id,
            **kwargs
        )
    
    @classmethod
    async def get_all_users(cls, *args, **kwargs):
        """
        Get All Users
        """
        return await cls.get_api(**kwargs).get_all_users(*args, **kwargs)
    
    @classmethod
    async def create_user(
        cls,
        *args,
        email: Optional[str] = None,
        username: Optional[str] = None,
        company_name: Optional[str] = None,
        organization_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Create User
        """
        return await cls.get_api(**kwargs).create_user(
            *args,
            email = email,
            username = username,
            company_name = company_name,
            organization_id = organization_id,
            **kwargs
        )
    
    @classmethod
    async def update_user(
        cls,
        *args,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        username: Optional[str] = None,
        company_name: Optional[str] = None,
        organization_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Update User
        """
        return await cls.get_api(**kwargs).update_user(
            *args,
            user_id = user_id,
            email = email,
            username = username,
            company_name = company_name,
            organization_id = organization_id,
            **kwargs
        )

    @classmethod
    async def delete_user(
        cls,
        *args,
        user_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Delete User
        """
        return await cls.get_api(**kwargs).delete_user(
            *args,
            user_id = user_id,
            **kwargs
        )
    

    """
    Functions
    """

    
    @classmethod
    async def async_flush(cls, **kwargs):
        """Tell the client to flush."""
        return await cls.get_api(**kwargs).async_flush(**kwargs)

    @classmethod
    async def async_join(cls, **kwargs):
        """Block program until the client clears the queue"""
        return cls.get_api(**kwargs).async_join(**kwargs)

    @classmethod
    async def async_shutdown(cls, **kwargs):
        """Flush all messages and cleanly shutdown the client"""
        return await cls.get_api(**kwargs).async_shutdown(**kwargs)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.async_shutdown()
    

    


