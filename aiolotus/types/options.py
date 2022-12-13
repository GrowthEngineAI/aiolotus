from enum import Enum

__all__ = [
    "HttpMethod",
    "ApiMethod",
    "PaymentProvider",
    "ExistingCustomerBehavior",
    "PlanDuration",
    "InvoiceStatus",
    "PriceTierType",
    "BatchRoundingType",
    "MetricAggregation",
    "PriceAdjustmentType",
    "MetricType",
    "MetricGranularity",
    "ProrationGranularity",
    "EventType",
    "UsageBillingFrequency",
    "ComponentResetFrequency",
    "FlatFeeBillingType",
    "UsageCalcGranularity",
    "NumericFilterOperators",
    "CategoricalFilterOperators",
    "SubscriptionStatus",
    "PlanVersionStatus",
    "PlanStatus",
    "BacktestKPI",
    "BacktestStatus",
    "ProductStatus",
    "MetricStatus",
    "MakePlanVersionActiveType",
    "ReplaceType",
    "ReplaceImmediatelyType"
]

class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"

class ApiMethod(str, Enum):
    LIST = "LIST"
    CREATE = "CREATE"
    CREATE_BATCH = "CREATE_BATCH"
    
    EVENT = "EVENT"
    TRACK = "TRACK"

    GET = "GET"
    GET_ALL = "GET_ALL"
    GET_DETAIL = "GET_DETAIL"

    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CHANGE = "CHANGE"
    CANCEL = "CANCEL"



class PaymentProvider(str, Enum):
    stripe = "stripe"

class ExistingCustomerBehavior(str, Enum):
    merge = "merge"
    ignore = "ignore"
    overwrite = "overwrite"

class PlanDuration(str, Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"

class InvoiceStatus(str, Enum):
    draft = "draft"
    paid = "paid"
    unpaid = "unpaid"
    void = "void"

class PriceTierType(str, Enum):
    flat = "flat"
    per_unit = "per_unit"
    free = "free"
    tiered = "tiered" # not implemented yet
    fixed = "fixed" # not implemented yet

class BatchRoundingType(str, Enum):
    round_up = "round_up"
    round_down = "round_down"
    round_nearest = "round_nearest"
    no_rounding = "no_rounding"

class MetricAggregation(str, Enum):
    count = "count"
    counter = "count"
    sum = "sum"
    max = "max"
    latest = "latest"
    unique = "unique"
    average = "average"
    
class PriceAdjustmentType(str, Enum):
    percentage = "percentage"
    fixed = "fixed"
    price_override = "price_override"

class MetricType(str, Enum):
    counter = "counter"
    stateful = "stateful"
    rate = "rate"

class MetricGranularity(str, Enum):
    second = "seconds"
    seconds = "seconds"
    minute = "minutes"
    minutes = "minutes"
    hour = "hours"
    hours = "hours"
    day = "days"
    days = "days"
    week = "weeks"
    weeks = "weeks"
    month = "months"
    months = "months"
    quarter = "quarters"
    quarters = "quarters"
    year = "years"
    years = "years"
    all = "total"
    total = "total"


class ProrationGranularity(str, Enum):
    second = "seconds"
    seconds = "seconds"
    minute = "minutes"
    minutes = "minutes"
    hour = "hours"
    hours = "hours"
    day = "days"
    days = "days"
    week = "weeks"
    weeks = "weeks"
    month = "months"
    months = "months"
    quarter = "quarters"
    quarters = "quarters"
    year = "years"
    years = "years"
    all = "total"
    total = "total"


class EventType(str, Enum):
    delta =  "delta"
    total = "total"

class UsageBillingFrequency(str, Enum):
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    end_of_period = "end_of_period"

class ComponentResetFrequency(str, Enum):
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    none = "none"

class FlatFeeBillingType(str, Enum):
    in_arrears = "in_arrears"
    in_advance = "in_advance"
    
class UsageCalcGranularity(str, Enum):
    daily = "daily"
    total = "total"

class NumericFilterOperators(str, Enum):
    gt = "gt"
    gte = "gte"
    lt = "lt"
    lte = "lte"
    eq = "eq"

class CategoricalFilterOperators(str, Enum):
    isin = "isin"
    is_in = "isin"
    isnot = "isnotin"
    is_not = "isnotin"
    isnotin = "isnotin"
    is_not_in = "isnotin"

class SubscriptionStatus(str, Enum):
    active = "active"
    ended = "ended"
    not_started = "not_started"

class PlanVersionStatus(str, Enum):
    active = "active"
    retiring = "retiring"
    grandfathered = "grandfathered"
    archived = "archived"
    inactive = "inactive"

class PlanStatus(str, Enum):
    active = "active"
    archived = "archived"
    experimental = "experimental"

class BacktestKPI(str, Enum):
    total_revenue = "total_revenue"

class BacktestStatus(str, Enum):
    running = "running"
    completed = "completed"
    failed = "failed"

class ProductStatus(str, Enum):
    active = "active"
    archived = "archived"

class MetricStatus(str, Enum):
    active = "active"
    archived = "archived"

class MakePlanVersionActiveType(str, Enum):
    now = "replace_immediately"
    replace_immediately = "replace_immediately"
    on_renewal = "replace_on_active_version_renewal"
    replace_at_end_of_period = "replace_on_active_version_renewal"
    replace_on_active_version_renewal = "replace_on_active_version_renewal"
    grandfather_active = "grandfather_active"
    grandfathered = "grandfather_active"

class ReplaceType(str, Enum):
    bill = "end_current_subscription_and_bill"
    dont_bill = "end_current_subscription_dont_bill"

class ReplaceImmediatelyType(str, Enum):
    bill_now = "end_current_subscription_and_bill"
    dont_bill = "end_current_subscription_dont_bill"
    change_plan = "change_subscription_plan"
    end_current_subscription_and_bill = "end_current_subscription_and_bill"
    end_current_subscription_dont_bill = "end_current_subscription_dont_bill"
    change_subscription_plan = "change_subscription_plan"

