from typing import Optional, Dict, List, Type
from aiolotus.utils import require
from aiolotus.types.options import MetricType, MetricGranularity, MetricAggregation, EventType
from aiolotus.types.filters import Filter, CategoricalFilter, NumericFilter
from aiolotus.schemas.base import ApiModel, ApiMethod, ID_TYPES

__all__ = [
    'LotusMetric',
]

class LotusMetric(ApiModel):
    metric_id: Optional[str] = None
    metric_name: Optional[str] = None
    metric_type: Optional[MetricType] = None
    
    filters: Optional[List[Filter]] = None
    categorical_filters: Optional[List[CategoricalFilter]] = None
    numeric_filters: Optional[List[NumericFilter]] = None
    
    event_name: Optional[str] = None
    event_type: Optional[EventType] = None

    granularity: Optional[MetricGranularity] = None

    billable_aggregation_type: Optional[MetricAggregation] = None
    usage_aggregation_type: Optional[MetricAggregation] = None

    description: Optional[str] = None
    properties: Optional[Dict] = None
    property_name: Optional[str] = None
    is_cost_metric: Optional[bool] = None

    async def validate_metric_type_counter(
        self,
        **kwargs
    ):
        """
        Validate the metric type is counter
        """
        if self.billable_aggregation_type is None:
            self.billable_aggregation_type = MetricAggregation.sum
        if self.usage_aggregation_type is None: self.usage_aggregation_type = MetricAggregation.counter
        if self.granularity is None: self.granularity = MetricGranularity.total
        assert self.usage_aggregation_type in [MetricAggregation.sum, MetricAggregation.counter, MetricAggregation.max, MetricAggregation.unique], "usage_aggregation_type must be one of sum, counter, max, unique"

    async def validate_metric_type_rate(
        self,
        **kwargs
    ):
        """
        Validate the metric type is rate
        """
        if self.billable_aggregation_type is None:
            self.billable_aggregation_type = MetricAggregation.max
        if self.usage_aggregation_type is None: self.usage_aggregation_type = MetricAggregation.counter
        if self.granularity is None: self.granularity = MetricGranularity.days

        assert self.usage_aggregation_type in [MetricAggregation.counter, MetricAggregation.max, MetricAggregation.unique, MetricAggregation.sum], "usage_aggregation_type must be one of counter, max, unique, sum"
        assert self.granularity in [MetricGranularity.days, MetricGranularity.hours, MetricGranularity.minutes], "granularity must be one of days, hours, minutes"

    async def validate_property_name_in_filters(
        self,
        **kwargs
    ):
        """
        Validate the property_name is in filters
        """
        assert self.property_name is not None, "property_name is required for stateful metrics"
        assert self.categorical_filters is not None or self.numeric_filters is not None, "categorical_filters or numeric_filters is required for stateful metrics"
        if self.categorical_filters is not None:
            assert self.property_name in [f.property_name for f in self.categorical_filters], "property_name must be in categorical_filters"
        if self.numeric_filters is not None:
            assert self.property_name in [f.property_name for f in self.numeric_filters], "property_name must be in numeric_filters"

    async def validate_metric_type_stateful(
        self,
        **kwargs
    ):
        """
        Validate the metric type is stateful
        """
        if self.billable_aggregation_type is None: self.billable_aggregation_type = MetricAggregation.sum
        assert self.billable_aggregation_type in [MetricAggregation.sum], "billable_aggregation_type must be one of sum"
        
        if usage_aggregation_type is None: usage_aggregation_type = MetricAggregation.max
        assert usage_aggregation_type in [MetricAggregation.max, MetricAggregation.latest], "usage_aggregation_type must be one of max, latest"
        await self.validate_property_name_in_filters()

        assert self.event_type in [EventType.total, EventType.delta], "event_type must be total or delta"
        if self.granularity is None: self.granularity = MetricGranularity.days
    

    async def validate_params(
        self,
        api_method: ApiMethod,
        items: Optional[List[Type['LotusMetric']]] = None,
        itemized: bool = False,
        **kwargs
    ) -> None:
        """Validate the message and ensure all required fields are present."""

        if self.filters:
            self.numeric_filters, self.categorical_filters = Filter.get_filters(filters=self.filters).values()
            self.filters = None

        if api_method in {ApiMethod.CREATE, ApiMethod.UPDATE}:
            require("metric_name", self.metric_name, str)
            if self.event_name is None: self.event_name = self.metric_name
            if self.properties is None: self.properties = {}
            if self.event_type is None: self.event_type = EventType.total
            if self.metric_type == MetricType.counter:
                await self.validate_metric_type_counter()
            elif self.metric_type == MetricType.rate:
                await self.validate_metric_type_rate()
            elif self.metric_type == MetricType.stateful:
                await self.validate_metric_type_stateful()
        
        if api_method in {ApiMethod.GET, ApiMethod.GET_DETAIL, ApiMethod.UPDATE, ApiMethod.DELETE, ApiMethod.CHANGE}:
            require("metric_id", self.metric_id, ID_TYPES)
            self.item_id = self.metric_id
