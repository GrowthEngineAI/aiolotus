from lazyops.types import BaseModel
from typing import List, Optional, Any, Union, Dict
from aiolotus.types.options import NumericFilterOperators, CategoricalFilterOperators

__all__ = [
    "Filter",
    "NumericFilter",
    "CategoricalFilter",
]

class NumericFilter(BaseModel):
    property_name: str
    operator: NumericFilterOperators
    comparison_value: Union[float, int]

class CategoricalFilter(BaseModel):
    property_name: str
    operator: CategoricalFilterOperators
    comparison_value: List[Any]

class Filter(BaseModel):
    property_name: str
    operator: Union[NumericFilterOperators, CategoricalFilterOperators, str]
    comparison_value: Union[float, int, List[Any]]

    def get_filter(self):
        if self.operator in NumericFilterOperators:
            return NumericFilter(
                property_name=self.property_name,
                operator=self.operator,
                comparison_value=self.comparison_value
            )
        elif self.operator in CategoricalFilterOperators:
            return CategoricalFilter(
                property_name=self.property_name,
                operator=self.operator,
                comparison_value=self.comparison_value
            )
        else:
            raise ValueError(f"Operator {self.operator} not supported")
    
    @classmethod
    def get_filters(cls, filters: Optional[List[Union[NumericFilter, CategoricalFilter, 'Filter']]] = None) -> Dict[str, List[Union[NumericFilter, CategoricalFilter]]]:
        # sourcery skip: avoid-builtin-shadow
        result = {
            "numeric_filters": [],
            "categorical_filters": []
        }
        if not filters: return result
        for filter in filters:
            if isinstance(filter, Filter):
                filter = filter.get_filter()
            if isinstance(filter, NumericFilter):
                result["numeric_filters"].append(filter)
            elif isinstance(filter, CategoricalFilter):
                result["categorical_filters"].append(filter)
        return result

