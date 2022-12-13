from lazyops.types import BaseModel
from typing import List, Optional
from aiolotus.types.options import (
    PaymentProvider, 
    PriceAdjustmentType,
    PriceTierType,
    BatchRoundingType,
    ProrationGranularity,
    FlatFeeBillingType,
    UsageBillingFrequency,
)


class PlanExternalLink(BaseModel):
    external_plan_id: Optional[str] = None
    source: Optional[PaymentProvider] = None

class PlanPriceAdjustment(BaseModel):
    price_adjustment_amount: int
    price_adjustment_type: Optional[PriceAdjustmentType] = PriceAdjustmentType.percentage    
    price_adjustment_name: Optional[str] = None
    price_adjustment_description: Optional[str] = None
    

class PlanFeature(BaseModel):
    feature_name: str
    feature_description: Optional[str] = None

class PlanPriceTier(BaseModel):
    range_start: int
    range_end: Optional[int] = None
    type: Optional[PriceTierType] = PriceTierType.tiered
    cost_per_batch: Optional[int] = None
    metric_units_per_batch: Optional[int] = None
    batch_rounding_type: Optional[BatchRoundingType] = BatchRoundingType.round_up

class PlanComponent(BaseModel):
    billable_metric_name: str
    tiers: List[PlanPriceTier]
    seperate_by: Optional[List[str]] = None
    proration_granularity: Optional[ProrationGranularity] = ProrationGranularity.minutes


class PlanVersion(BaseModel):
    features: Optional[List[PlanFeature]] = []
    flat_fee_billing_type: Optional[FlatFeeBillingType] = FlatFeeBillingType.in_arrears
    price_adjustment: Optional[PlanPriceAdjustment] = None
    description: Optional[str] = None
    usage_billing_frequency: Optional[UsageBillingFrequency] = UsageBillingFrequency.monthly
    flat_rate: Optional[int] = 0
    transition_to_plan_id: Optional[str] = None
    
